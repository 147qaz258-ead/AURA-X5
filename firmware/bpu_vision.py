"""D-Robotics RDK X5 10 TOPS BPU Inference Service for AURA-X5.
Verified on RDK X5 Linux 6.1.83 (hbm_runtime 1.24.5 / HBRT 3.15.55.0).
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
import time
import numpy as np


class BPUUnavailableError(RuntimeError):
    """Raised when hbm_runtime or compiled .bin/.hbm model is unavailable."""


@dataclass
class BPUInferenceResult:
    model_name: str
    latency_ms: float
    top_class_idx: int
    top_score: float
    outputs: List[Dict[str, Any]]
    bpu_core: str = "Bayes-10TOPS-INT8"


class RDKX5BPUService:
    """Loads .bin/.hbm models onto RDK X5 Bayes BPU via hbm_runtime."""

    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise BPUUnavailableError(f"BPU model not found: {self.model_path}")
        try:
            import hbm_runtime  # type: ignore
            self.rt = hbm_runtime.HB_HBMRuntime(str(self.model_path))
            self.model_name = self.rt.model_names[0]
            self.input_name = self.rt.input_names[self.model_name][0]
            self.input_shape = tuple(self.rt.input_shapes[self.model_name][self.input_name])
        except Exception as exc:
            raise BPUUnavailableError(f"hbm_runtime unavailable: {exc}") from exc

    def infer_chw_uint8(self, tensor_nchw: np.ndarray) -> BPUInferenceResult:
        t0 = time.perf_counter()
        out_map = self.rt.run({self.input_name: tensor_nchw})[self.model_name]
        dt_ms = (time.perf_counter() - t0) * 1000.0
        first_out = next(iter(out_map.values())).ravel()
        top_idx = int(np.argmax(first_out))
        top_score = float(first_out[top_idx])
        return BPUInferenceResult(
            model_name=self.model_name,
            latency_ms=round(dt_ms, 2),
            top_class_idx=top_idx,
            top_score=round(top_score, 4),
            outputs=[{k: list(v.shape) for k, v in out_map.items()}],
        )
