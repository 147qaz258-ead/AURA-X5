"""Shared ROS 2 topic/service contracts, payload helpers, and time-sync utilities for AURA-X5.
Pure Python so it can be unit-tested on host PCs as well as imported by rclpy nodes on RDK X5.
"""
from dataclasses import dataclass
from pathlib import Path
import json
import sys
import time
from typing import Any, Dict, Optional

# Canonical ROS 2 topic and service names (must match docs/ARCHITECTURE.md)
TOPIC_DESKTOP_FRAME = "/aura/desktop_frame"
TOPIC_PERCEPTION_RESULT = "/aura/perception_result"
TOPIC_BPU_METRICS = "/aura/bpu_metrics"
TOPIC_HARDWARE_TELEMETRY = "/aura/hardware_telemetry"
TOPIC_RADAR_PRESENCE = "/aura/radar_presence"
TOPIC_PRIVACY_STATE = "/aura/privacy_state"
TOPIC_KILL_SWITCH = "/aura/kill_switch"
TOPIC_PHYSICAL_INPUT = "/aura/physical_input"
TOPIC_ACTION_PROPOSAL = "/aura/action_proposal"
TOPIC_HID_COMMAND = "/aura/hid_command"
TOPIC_UI_STATE = "/aura/ui_state"
TOPIC_DECISION_EVENT = "/aura/decision_event"
SERVICE_RESET_KILL_LATCH = "/aura/reset_kill_latch"

VALID_PHYSICAL_APPROVAL_SOURCES = frozenset({
    "ec11_press",
    "xpt2046_touch",
    "hdmi_local_confirm",
})


def resolve_firmware_path() -> Optional[Path]:
    """Locate aura_x5/firmware in either the source workspace or /opt/aura_x5."""
    here = Path(__file__).resolve()
    candidates = [
        here.parents[4] / "firmware",  # aura_x5/ros2_ws/src/aura_x5_ros/aura_x5_ros/contracts.py
        Path("/opt/aura_x5"),
        Path("/opt/aura_x5/firmware"),
    ]
    for path in candidates:
        if (path / "agent_core.py").exists():
            return path
    return None


def ensure_firmware_on_path() -> Path:
    fw = resolve_firmware_path()
    if fw is None:
        raise FileNotFoundError("Cannot locate AURA-X5 firmware directory (expected agent_core.py).")
    fw_str = str(fw)
    if fw_str not in sys.path:
        sys.path.insert(0, fw_str)
    return fw


def now_ns() -> int:
    return time.time_ns()


def encode_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def decode_json(raw: str) -> Dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("ROS 2 JSON envelope must decode to a JSON object")
    return data


def read_soc_temp_c() -> Optional[float]:
    """Read Linux thermal_zone SoC temperature on RDK X5 (returns None if unavailable)."""
    thermal_root = Path("/sys/class/thermal")
    if not thermal_root.exists():
        return None
    temps = []
    for zone in sorted(thermal_root.glob("thermal_zone*/temp")):
        try:
            milli_c = int(zone.read_text(encoding="utf-8").strip())
            if 0 < milli_c < 150000:
                temps.append(milli_c / 1000.0)
        except (OSError, ValueError):
            continue
    return round(max(temps), 1) if temps else None


@dataclass
class SyncStatus:
    in_sync: bool
    skew_ms: float
    stale: bool


def evaluate_sensor_sync(
    primary_ts_ns: int,
    secondary_ts_ns: int,
    max_skew_ms: float = 500.0,
    now_timestamp_ns: Optional[int] = None,
    max_age_sec: float = 120.0,
) -> SyncStatus:
    """Evaluate timestamp alignment and freshness across multi-sensor ROS 2 streams."""
    ref_now = now_timestamp_ns if now_timestamp_ns is not None else now_ns()
    skew_ms = abs(primary_ts_ns - secondary_ts_ns) / 1_000_000.0
    age_sec = max(0.0, (ref_now - primary_ts_ns) / 1_000_000_000.0)
    stale = age_sec > max_age_sec
    return SyncStatus(in_sync=(skew_ms <= max_skew_ms and not stale), skew_ms=round(skew_ms, 2), stale=stale)
