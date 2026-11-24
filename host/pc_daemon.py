"""AURA-X5 PC Host Proactive Observer Daemon.
Captures screen changes (pixel diff + SHA-256) and streams context over USB-C RNDIS (10.55.0.1:8765).
"""
from dataclasses import dataclass
import hashlib
import json
import time
from typing import Optional
import numpy as np


@dataclass
class FrameEvent:
    frame_id: str
    timestamp: float
    sha256: str
    diff_ratio: float
    width: int
    height: int


class ScreenChangeDetector:
    """Computes normalized pixel diff ratio to filter idle frames before sending to RDK X5 BPU."""

    def __init__(self, diff_threshold: float = 0.015):
        self.diff_threshold = diff_threshold
        self._prev_gray: Optional[np.ndarray] = None
        self._seq = 0

    def process_frame(self, rgb_frame: np.ndarray) -> Optional[FrameEvent]:
        gray = rgb_frame.mean(axis=2).astype(np.uint8)
        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            diff_ratio = 1.0
        else:
            changed = np.abs(gray.astype(np.int16) - self._prev_gray.astype(np.int16)) > 12
            diff_ratio = float(changed.mean())

        if diff_ratio < self.diff_threshold:
            return None

        self._prev_gray = gray
        self._seq += 1
        digest = hashlib.sha256(rgb_frame.tobytes()).hexdigest()
        return FrameEvent(
            frame_id=f"frame-{self._seq:06d}",
            timestamp=time.time(),
            sha256=digest,
            diff_ratio=round(diff_ratio, 4),
            width=int(rgb_frame.shape[1]),
            height=int(rgb_frame.shape[0]),
        )


def build_proposal_payload(event: FrameEvent, title: str, summary: str) -> str:
    return json.dumps({
        "type": "proactive_proposal",
        "evidence_frame_id": event.frame_id,
        "sha256": event.sha256,
        "diff_ratio": event.diff_ratio,
        "title": title,
        "summary": summary,
    }, ensure_ascii=False)
