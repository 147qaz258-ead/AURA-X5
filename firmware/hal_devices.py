"""Hardware Abstraction Layer (HAL) for AURA-X5 on D-Robotics RDK X5.
Strictly aligned with aura_x5/interfaces.json.
No fake/mock sensor data: raises HardwareUnavailableError when physical buses are absent.
"""
from dataclasses import dataclass
from typing import Optional, Tuple
import struct
import time


class HardwareUnavailableError(RuntimeError):
    """Raised when a required RDK X5 hardware bus or library is not present."""


@dataclass
class RadarReading:
    target_state: int  # 0=none, 1=moving, 2=stationary, 3=both
    moving_dist_cm: int
    moving_energy: int
    static_dist_cm: int
    static_energy: int
    detect_dist_cm: int

    @property
    def user_present(self) -> bool:
        return self.target_state != 0


def parse_ld2410c_frame(frame: bytes) -> Optional[RadarReading]:
    """Parse HLK-LD2410C 24GHz mmWave radar basic data frame (header F4 F3 F2 F1, tail F8 F7 F6 F5)."""
    if len(frame) < 23:
        return None
    if frame[0:4] != b"\xf4\xf3\xf2\xf1" or frame[-4:] != b"\xf8\xf7\xf6\xf5":
        return None
    # Intra-frame: [4:6]=len, [6]=0x02 (normal), [7]=0xAA (head), [8]=target_state
    if frame[6] != 0x02 or frame[7] != 0xAA:
        return None
    target_state = frame[8]
    moving_dist, = struct.unpack_from("<H", frame, 9)
    moving_energy = frame[11]
    static_dist, = struct.unpack_from("<H", frame, 12)
    static_energy = frame[14]
    detect_dist, = struct.unpack_from("<H", frame, 15)
    return RadarReading(
        target_state=target_state,
        moving_dist_cm=moving_dist,
        moving_energy=moving_energy,
        static_dist_cm=static_dist,
        static_energy=static_energy,
        detect_dist_cm=detect_dist,
    )


class XPT2046Touch:
    """4-wire resistive touch controller over GPIO bit-bang (Pins 19/21/23/26/11) on RDK X5."""
    PIN_IRQ = 11
    PIN_MOSI = 19
    PIN_MISO = 21
    PIN_SCLK = 23
    PIN_CS = 26

    def __init__(self, spi_bus: int = 1, spi_dev: int = 1, width: int = 480, height: int = 320):
        self.width = width
        self.height = height
        try:
            import Hobot.GPIO as GPIO  # type: ignore
            self.GPIO = GPIO
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.PIN_MOSI, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.PIN_SCLK, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(self.PIN_CS, GPIO.OUT, initial=GPIO.HIGH)
            GPIO.setup(self.PIN_MISO, GPIO.IN)
            GPIO.setup(self.PIN_IRQ, GPIO.IN)
        except Exception as exc:
            raise HardwareUnavailableError(f"XPT2046 GPIO unavailable: {exc}") from exc

    def _xfer(self, cmd: int) -> int:
        G = self.GPIO
        G.output(self.PIN_CS, G.LOW)
        for i in range(7, -1, -1):
            G.output(self.PIN_MOSI, (cmd >> i) & 1)
            G.output(self.PIN_SCLK, G.HIGH)
            G.output(self.PIN_SCLK, G.LOW)
        val = 0
        for _ in range(16):
            G.output(self.PIN_SCLK, G.HIGH)
            bit = G.input(self.PIN_MISO)
            G.output(self.PIN_SCLK, G.LOW)
            val = (val << 1) | bit
        G.output(self.PIN_CS, G.HIGH)
        return val >> 3

    def is_touched(self) -> bool:
        return self.GPIO.input(self.PIN_IRQ) == 0

    def read_raw(self) -> Tuple[int, int, int]:
        x = self._xfer(0xD0)
        y = self._xfer(0x90)
        z1 = self._xfer(0xB0)
        return x, y, z1

    def read_point(self, z_threshold: int = 60) -> Optional[Tuple[int, int]]:
        x_raw, y_raw, z = self.read_raw()
        if z < z_threshold or x_raw in (0, 4095) or y_raw in (0, 4095):
            return None
        # Landscape 480x320 (ILI9486 MADCTL=0x28): X/Y swapped and X inverted
        px = self.width - 1 - max(0, min(self.width - 1, int((y_raw - 200) * self.width / 3650)))
        py = max(0, min(self.height - 1, int((x_raw - 200) * self.height / 3650)))
        return px, py


class PrivacyAndControls:
    """Manages RDK X5 40-Pin GPIO controls: Privacy Sense, Kill-Switch, EC11, Fan PWM."""
    PIN_KILL_SW = 7
    PIN_EC11_A = 13
    PIN_EC11_B = 15
    PIN_EC11_SW = 16
    PIN_PRIVACY_SENSE = 29
    PIN_BUZZER_PWM = 31
    PIN_FAN_PWM = 32

    def __init__(self):
        try:
            import Hobot.GPIO as GPIO  # type: ignore
            self.GPIO = GPIO
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.PIN_KILL_SW, GPIO.IN)
            GPIO.setup(self.PIN_EC11_A, GPIO.IN)
            GPIO.setup(self.PIN_EC11_B, GPIO.IN)
            GPIO.setup(self.PIN_EC11_SW, GPIO.IN)
            GPIO.setup(self.PIN_PRIVACY_SENSE, GPIO.IN)
            self.fan_pwm = GPIO.PWM(self.PIN_FAN_PWM, 25000)
            self.fan_pwm.start(40)
        except Exception as exc:
            raise HardwareUnavailableError(f"Hobot.GPIO unavailable (not running on RDK X5?): {exc}") from exc

    def is_privacy_power_on(self) -> bool:
        """True if DPDT hardware privacy switch is ON (mic/cam powered), False if physically cut."""
        return bool(self.GPIO.input(self.PIN_PRIVACY_SENSE))

    def is_kill_pressed(self) -> bool:
        return self.GPIO.input(self.PIN_KILL_SW) == 0

    def set_fan_duty(self, pct: int) -> None:
        self.fan_pwm.ChangeDutyCycle(max(0, min(100, int(pct))))
