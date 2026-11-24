"""Stage 3 Continuous Concurrent BPU Benchmark for AURA-X5 on D-Robotics RDK X5.

Runs two concurrent workloads for >=30 seconds (default 35s):
  - Workload 1 (BPU): Continuous real-time inference via hbm_runtime (Bayes 10-TOPS BPU).
  - Workload 2 (CPU/UI/Sensor): Concurrent 20 Hz UI state rendering + hardware telemetry polling.

Strict No-Mock Policy: fails fast with non-zero exit if hbm_runtime or model file is absent.
"""
import argparse
import json
from pathlib import Path
import sys
import threading
import time
from typing import Dict, List, Optional, Tuple
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "firmware"))
sys.path.insert(0, str(ROOT / "ros2_ws" / "src" / "aura_x5_ros"))

DEFAULT_MODEL = "/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin"


def _read_proc_stat() -> Optional[Tuple[int, int]]:
    stat_file = Path("/proc/stat")
    if not stat_file.exists():
        return None
    first = stat_file.read_text(encoding="utf-8").splitlines()[0].split()
    vals = [int(x) for x in first[1:8]]
    idle = vals[3] + vals[4]
    total = sum(vals)
    return total, idle


def _read_soc_temp_c() -> Optional[float]:
    thermal_root = Path("/sys/class/thermal")
    if not thermal_root.exists():
        return None
    temps = []
    for zone in sorted(thermal_root.glob("thermal_zone*/temp")):
        try:
            v = int(zone.read_text(encoding="utf-8").strip())
            if 0 < v < 150000:
                temps.append(v / 1000.0)
        except (OSError, ValueError):
            continue
    return round(max(temps), 1) if temps else None


def summarize_benchmark(
    model_name: str,
    runtime_desc: str,
    input_shape: List[int],
    latencies_ms: List[float],
    elapsed_sec: float,
    concurrent_cycles: int,
    cpu_samples_pct: List[float],
    temp_samples_c: List[float],
) -> Dict:
    """Aggregate raw benchmark samples into Stage 3 evidence dictionary."""
    if not latencies_ms or elapsed_sec <= 0:
        raise ValueError("Benchmark produced zero inference samples.")
    arr = np.asarray(latencies_ms, dtype=np.float64)
    return {
        "model_name": model_name,
        "runtime": runtime_desc,
        "input_shape": list(input_shape),
        "duration_sec": round(elapsed_sec, 2),
        "total_inferences": len(latencies_ms),
        "fps": round(len(latencies_ms) / elapsed_sec, 2),
        "latency_avg_ms": round(float(arr.mean()), 2),
        "latency_p95_ms": round(float(np.percentile(arr, 95)), 2),
        "latency_max_ms": round(float(arr.max()), 2),
        "concurrent_workload": "UI state render + hardware telemetry poll (20 Hz target)",
        "concurrent_cycles": int(concurrent_cycles),
        "concurrent_hz": round(concurrent_cycles / elapsed_sec, 2),
        "cpu_avg_pct": round(float(np.mean(cpu_samples_pct)), 1) if cpu_samples_pct else None,
        "soc_temp_start_c": temp_samples_c[0] if temp_samples_c else None,
        "soc_temp_max_c": max(temp_samples_c) if temp_samples_c else None,
    }


def format_markdown_row(summary: Dict) -> str:
    shape_str = "x".join(str(d) for d in summary["input_shape"])
    cpu_str = f"CPU {summary['cpu_avg_pct']}% + Bayes BPU active" if summary["cpu_avg_pct"] is not None else "Bayes BPU active"
    temp_str = (
        f"{summary['soc_temp_start_c']}C -> max {summary['soc_temp_max_c']}C ({summary['duration_sec']}s)"
        if summary["soc_temp_max_c"] is not None
        else f"N/A ({summary['duration_sec']}s)"
    )
    return (
        f"| `{summary['model_name']}` ({summary['runtime']}) | `{shape_str}` | "
        f"{summary['latency_avg_ms']} ms / P95 {summary['latency_p95_ms']} ms | "
        f"{summary['fps']} FPS | {summary['concurrent_workload']} ({summary['concurrent_hz']} Hz) | "
        f"{cpu_str} | {temp_str} |"
    )


def run_live_benchmark(model_path: Path, duration_sec: float) -> Dict:
    from bpu_vision import RDKX5BPUService  # type: ignore
    from display_ui import UIState, render_ui_image  # type: ignore
    from sensor_hub import probe_connected_hardware  # type: ignore

    bpu = RDKX5BPUService(model_path)
    tensor = np.random.randint(0, 255, size=bpu.input_shape, dtype=np.uint8)
    tensor = np.ascontiguousarray(tensor)

    stop_ev = threading.Event()
    concurrent_count = [0]
    cpu_samples: List[float] = []
    temp_samples: List[float] = []

    def workload_2():
        state = UIState(
            active_page="AGENT",
            connected_pc=True,
            privacy_mic_on=False,
            user_present=True,
            bpu_load_pct=50,
            proposal_title="Stage 3 Concurrent Soak",
            proposal_summary="Running continuous BPU inference + UI/sensor loop.",
            evidence_frame_id="bench-live",
            status_banner="BENCHMARKING",
        )
        while not stop_ev.is_set():
            render_ui_image(state)
            probe_connected_hardware()
            concurrent_count[0] += 1
            time.sleep(0.05)

    def sampler():
        prev = _read_proc_stat()
        t0 = _read_soc_temp_c()
        if t0 is not None:
            temp_samples.append(t0)
        while not stop_ev.is_set():
            time.sleep(1.0)
            cur = _read_proc_stat()
            if prev and cur and (cur[0] - prev[0]) > 0:
                dt = cur[0] - prev[0]
                di = cur[1] - prev[1]
                cpu_samples.append(round((1.0 - di / dt) * 100.0, 1))
            prev = cur
            tc = _read_soc_temp_c()
            if tc is not None:
                temp_samples.append(tc)

    t_w2 = threading.Thread(target=workload_2, daemon=True)
    t_samp = threading.Thread(target=sampler, daemon=True)
    t_w2.start()
    t_samp.start()

    latencies: List[float] = []
    t_start = time.perf_counter()
    try:
        while (time.perf_counter() - t_start) < duration_sec:
            res = bpu.infer_chw_uint8(tensor)
            latencies.append(res.latency_ms)
    finally:
        stop_ev.set()
        t_w2.join(timeout=2.0)
        t_samp.join(timeout=2.0)

    elapsed = time.perf_counter() - t_start
    return summarize_benchmark(
        model_name=bpu.model_name,
        runtime_desc="hbm_runtime / Bayes 10-TOPS BPU",
        input_shape=list(bpu.input_shape),
        latencies_ms=latencies,
        elapsed_sec=elapsed,
        concurrent_cycles=concurrent_count[0],
        cpu_samples_pct=cpu_samples,
        temp_samples_c=temp_samples,
    )


def main():
    parser = argparse.ArgumentParser(description="Run Stage 3 continuous concurrent BPU benchmark on RDK X5.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Path to compiled RDK X5 .bin/.hbm model")
    parser.add_argument("--duration", type=float, default=35.0, help="Continuous test duration in seconds (>=30s)")
    parser.add_argument("--out", default="", help="Optional output JSON path")
    args = parser.parse_args()

    summary = run_live_benchmark(Path(args.model), args.duration)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print("\nMarkdown Table Row:")
    print(format_markdown_row(summary))

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nSaved benchmark evidence to {out_path}")


if __name__ == "__main__":
    main()
