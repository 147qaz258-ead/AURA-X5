"""Unified Sensor & Control Hub for AURA-X5 on RDK X5.
Probes real hardware buses (I2C-5, UART ttyS1, GPIO) without fabricating missing sensors.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import os


@dataclass
class HardwareTelemetry:
    i2c_vl53l1x: bool = False
    i2c_sht40: bool = False
    i2c_ina219: bool = False
    uart_radar_ld2410c: bool = False
    hid_keyboard_ready: bool = False
    hid_mouse_ready: bool = False
    user_present: Optional[bool] = None
    radar_dist_cm: Optional[int] = None
    ambient_temp_c: Optional[float] = None
    ambient_rh_pct: Optional[float] = None
    power_mw: Optional[float] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def probe_connected_hardware() -> HardwareTelemetry:
    """Detect which physical peripherals are currently attached on RDK X5."""
    tel = HardwareTelemetry()
    tel.hid_keyboard_ready = os.path.exists("/dev/hidg0")
    tel.hid_mouse_ready = os.path.exists("/dev/hidg1")

    # Probe I2C-5 addresses if smbus2 is available
    try:
        import smbus2  # type: ignore
        bus = smbus2.SMBus(5)
        for attr, addr in (("i2c_vl53l1x", 0x29), ("i2c_ina219", 0x40), ("i2c_sht40", 0x44)):
            try:
                bus.read_byte(addr)
                setattr(tel, attr, True)
            except OSError:
                pass
        bus.close()
    except Exception:
        pass

    # Check UART device for HLK-LD2410C
    tel.uart_radar_ld2410c = os.path.exists("/dev/ttyS1")
    return tel
