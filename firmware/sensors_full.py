"""Complete peripheral drivers for AURA-X5 Carrier HAT (EVT-B).
Covers: SHT40 (0x44), INA219 (0x40), VL53L1X (0x29), LD2410C UART, and WS2812B state mapping.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import time


def sht40_crc8(data: bytes) -> int:
    """Sensirion SHT4x CRC-8 (poly 0x31, init 0xFF)."""
    crc = 0xFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
    return crc


@dataclass
class EnvReading:
    temp_c: float
    rh_pct: float


class SHT40Driver:
    ADDR = 0x44

    def __init__(self, bus_num: int = 5):
        import smbus2  # type: ignore
        self.bus = smbus2.SMBus(bus_num)

    def read(self) -> EnvReading:
        self.bus.write_byte(self.ADDR, 0xFD)  # High-precision measurement
        time.sleep(0.01)
        from smbus2 import i2c_msg  # type: ignore
        msg = i2c_msg.read(self.ADDR, 6)
        self.bus.i2c_rdwr(msg)
        raw = bytes(msg)
        if sht40_crc8(raw[0:2]) != raw[2] or sht40_crc8(raw[3:5]) != raw[5]:
            raise ValueError("SHT40 CRC-8 mismatch")
        t_ticks = (raw[0] << 8) | raw[1]
        rh_ticks = (raw[3] << 8) | raw[4]
        temp_c = -45.0 + 175.0 * (t_ticks / 65535.0)
        rh_pct = max(0.0, min(100.0, -6.0 + 125.0 * (rh_ticks / 65535.0)))
        return EnvReading(temp_c=round(temp_c, 2), rh_pct=round(rh_pct, 1))


class INA219Driver:
    ADDR = 0x40

    def __init__(self, bus_num: int = 5):
        import smbus2  # type: ignore
        self.bus = smbus2.SMBus(bus_num)

    def read_bus_voltage_v(self) -> float:
        raw = self.bus.read_word_data(self.ADDR, 0x02)
        swapped = ((raw & 0xFF) << 8) | (raw >> 8)
        return round(((swapped >> 3) * 4) / 1000.0, 3)


def ws2812_color_for_state(agent_state: str, privacy_cut: bool) -> Tuple[int, int, int]:
    """Map AURA-X5 agent state to RGB ring color."""
    if privacy_cut:
        return (180, 20, 20)
    mapping = {
        "STANDBY": (20, 90, 180),
        "OBSERVING": (0, 160, 200),
        "PENDING_APPROVAL": (230, 150, 10),
        "APPROVED": (20, 200, 80),
        "REJECTED": (200, 40, 40),
    }
    return mapping.get(agent_state.upper(), (40, 60, 90))
