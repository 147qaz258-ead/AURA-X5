# Stage 3 — Benchmarks, Calibration, Safety & Recovery Manual

> **Official Requirement:** [`stages/stage3-launch.md`](https://github.com/D-Robotics/Robotics-Dream-Keeper-Challenge-Winter/blob/main/stages/stage3-launch.md)  
> **Benchmark Runner:** [`scripts/benchmark_bpu_concurrent.py`](../scripts/benchmark_bpu_concurrent.py)  
> **Honesty Policy:** No fabricated numbers. Entries marked `PENDING_ON_RDK_X5` will be populated directly from JSON logs generated on live RDK X5 hardware during Stage 3 testing.

---

## 1. BPU Continuous & Concurrent Workload Benchmark Table

### Reproduction Command (On Live RDK X5)
```bash
python3 scripts/benchmark_bpu_concurrent.py \
  --model /app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin \
  --duration 35 \
  --out docs/evidence/stage3/bpu_benchmark.json
```

### Measured Performance Summary

| Model & Runtime | Input Resolution | End-to-End Latency (Avg / P95) | Throughput (FPS / Hz) | Concurrent Workload #2 | CPU / BPU Utilization | SoC Temp & Test Duration | Evidence File |
|---|---|---|---|---|---|---|---|
| `mobilenetv2_224x224_nv12.bin` (`hbm_runtime 1.24.5` / HBRT `3.15.55.0`) | `1×3×224×224` (`uint8`) | `PENDING_ON_RDK_X5` | `PENDING_ON_RDK_X5` | Concurrent UI state render + GPIO/sensor telemetry loop (`20 Hz`) | `PENDING_ON_RDK_X5` | `PENDING_ON_RDK_X5` (Target: `≥35 s`, `<75 °C`) | `docs/evidence/stage3/bpu_benchmark.json` |
| *Optional Stage 3 Upgrade:* `yolov8s` / `ppocrv5` `.bin`/`.hbm` (`hbm_runtime`) | `1×3×640×640` | `PENDING_ON_RDK_X5` | `PENDING_ON_RDK_X5` | ROS 2 multi-node topic publish + HDMI 60 FPS WebSocket broadcast | `PENDING_ON_RDK_X5` | `PENDING_ON_RDK_X5` | `docs/evidence/stage3/bpu_yolo_benchmark.json` |

### Already-Verified Host & Pre-Build Quantitative Baselines (Real Measurements)

| Subsystem | Test Condition | Measured Result | Verification Artifact |
|---|---|---|---|
| Host Screen Capture (`dsh-see-now 0.2.2` / `ddagrab`) | 20 min continuous (`1200.1 s`), 12 FPS target | **12.00 FPS**, **0.00% drop** (`14,394` frames), stop latency **26 ms**, post-stop frames **0** | `docs/reports/M1_acceptance.md` (companion workspace) |
| High-DPI Desktop OCR Tiling Study | Controlled 90-line 4K matrix (`10px–32px`) | Whole-screen `640×640` = **26%** vs `640×640` tiled (`stride=512`) = **77%–79%** (baseline lower bound) | `docs/reports/M2_ocr_resolution_probe.md` |
| Custom Carrier PCB (`aura_x5_hat` EVT-B) | KiCad 9.0.7 automated DRC | **32 parts, 36 nets, 3995 tracks, 69 vias, 0 DRC errors, 0 unconnected** | [`electronics/validation.json`](../electronics/validation.json) |
| 3D Enclosure Printability | CadQuery 2.8.0 mesh audit | **3/3 STL parts watertight** (`base_shell` 72.77 cm³, `front_console_flat` 19.32 cm³, `encoder_knob` 5.99 cm³) | [`mechanical/fit_check.json`](../mechanical/fit_check.json) |

---

## 2. Calibration Procedures

1. **3.5" XPT2046 Resistive Touch Calibration (V1 Build)**:
   - Landscape `480×320` (`ILI9486 MADCTL=0x28`) uses swapped X/Y and inverted X mapping (`hal_devices.py` lines 108–109, raw span `200..3850`, pressure threshold `z_threshold=60`).
   - Run `python3 scripts/test_bitbang_xpt.py` and tap the four screen corners (`APPROVE` and `REJECT` zones) to verify coordinate accuracy within `±5 px`.
2. **HLK-LD2410C 24 GHz mmWave Presence Radar Calibration**:
   - Mount on front console facing seated user (`0.4 m – 1.5 m` desk range).
   - Verify valid 23-byte `F4 F3 F2 F1 ... F8 F7 F6 F5` frames at `256000 baud` on `/dev/ttyS1` (`>= 5 Hz`) and confirm stationary desk detection without false triggers from behind-monitor walls.
3. **Host Screen Change Threshold Calibration**:
   - Default `ScreenChangeDetector(diff_threshold=0.02)` filters cursor blinks and clock ticks while firing reliably on IDE edits, browser switches, or modal pop-ups.

---

## 3. Safety Architecture, Actuator Limits & Emergency Stop

AURA-X5 can inject real OS-level keyboard/mouse events via `/dev/hidg0` and `/dev/hidg1`, and drives a 5V active cooling fan. Accordingly, four hard safety invariants are enforced:

1. **Non-Bypassable Physical Approval Gate (`firmware/agent_core.py`)**:
   - `SafetyGatedAgentCore.approve_current(physical_source)` accepts **only** verified local physical inputs (`ec11_press`, `xpt2046_touch`, `hdmi_local_confirm`). Any remote or software API call raises `PermissionError`.
2. **Hardware Emergency Kill-Switch (`GPIO Pin 7`)**:
   - Pressing the Kill-Switch immediately sets `kill_latched = True`, transitions all pending/approved proposals to `ABORTED_BY_KILL_SWITCH`, and writes an 8-byte all-zero HID release packet (`0x00 * 8`) to `/dev/hidg0` so no modifier key (`Ctrl`, `Win`, `Alt`) can ever remain stuck.
   - Mid-macro check runs before every single HID key packet (`agent_core.py` lines 95–96).
3. **Hardware Privacy Sovereignty (`DPDT Switch` → `V_PRIVACY_3V3`)**:
   - Physically disconnects the 3.3V power rail to the microphone/camera header (`J6`) regardless of software state, while reporting rail status on `GPIO Pin 29` (`privacy_sense_pin`) and illuminating/extinguishing the hardware red LED (`D2`).
4. **Actuator & Thermal Limits**:
   - HID keystroke interval bounded to `20 ms` per packet with mandatory trailing all-zero release packet.
   - Proposal expiry TTL (`120 s`) prevents accidental execution of stale queued suggestions.
   - Fan PWM (`GPIO Pin 32`, `25 kHz`) ramps up automatically if SoC temperature exceeds `60 °C`, with warning banner at `75 °C`.

---

## 4. Known Limitations & Failure Recovery

| Known Limitation | Impact | Failure Recovery Procedure |
|---|---|---|
| `hbm_runtime` only runs on RDK X5 ARM64 Linux (not on Windows x64 dev PC) | Unit tests on PC test contract/logic only; BPU inference must be benchmarked on RDK X5 | Always execute `scripts/benchmark_bpu_concurrent.py` directly on RDK X5 via SSH |
| USB-C OTG Gadget requires a data-capable cable connected to the OTG port | Charge-only cables fail to enumerate `ecm.usb0` / `/dev/hidg0` | Verify `ls /sys/class/udc` and `/dev/hidg0`; re-run `sudo bash firmware/usb_gadget_setup.sh` or fall back to LAN WebSocket (`192.168.128.10:8765`) |
| Kill-Switch intentionally latches after activation | Subsequent approvals raise `RuntimeError` until explicitly cleared | Confirm host desktop state is safe, then call `ros2 service call /aura/reset_kill_latch std_srvs/srv/Trigger` (or restart `aura_safety_gate_node`) |
| Single-frame `224×224` MobileNetV2 cannot read fine 12px Chinese desktop text | Limits fine-grained OCR on dense code screens without tiling | Use active-window title + `640×640` ROI tiling pipeline for Stage 3 PP-OCRv5 / YOLOv8 extension |
