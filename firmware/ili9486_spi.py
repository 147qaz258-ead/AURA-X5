"""MPI3501 16-bit shift-register ILI9486 driver on RDK X5 (verified GPIO waveform + C fast pusher)."""
import ctypes
from pathlib import Path
import time
import numpy as np
import Hobot.GPIO as GPIO


class ILI9486ShiftSPI:
    WIDTH = 480
    HEIGHT = 320
    PIN_DC = 18
    PIN_MOSI = 19
    PIN_RST = 22
    PIN_SCLK = 23
    PIN_CS = 24

    # Verified RDK X5 sysfs GPIO indices for BOARD 19, 23, 24, 18
    SYSFS_MOSI = 398
    SYSFS_SCLK = 395
    SYSFS_CS = 394
    SYSFS_DC = 402

    def __init__(self, spi_bus: int = 1, spi_dev: int = 0, max_hz: int = 12_000_000):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        for p, init in (
            (self.PIN_MOSI, GPIO.LOW),
            (self.PIN_SCLK, GPIO.LOW),
            (self.PIN_CS, GPIO.HIGH),
            (self.PIN_DC, GPIO.LOW),
            (self.PIN_RST, GPIO.HIGH),
        ):
            GPIO.setup(p, GPIO.OUT, initial=init)

        so_path = Path(__file__).with_name("ili9486_fast.so")
        self._lib = ctypes.CDLL(str(so_path)) if so_path.exists() else None
        if self._lib:
            self._lib.lcd_gpio_open.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            self._lib.lcd_gpio_open.restype = ctypes.c_int
            self._lib.push_rgb565_gpio.argtypes = [ctypes.c_void_p, ctypes.c_int]
            self._lib.push_rgb565_gpio.restype = ctypes.c_int
            if self._lib.lcd_gpio_open(self.SYSFS_MOSI, self.SYSFS_SCLK, self.SYSFS_CS, self.SYSFS_DC) != 0:
                raise OSError("Failed to open sysfs GPIO FDs in ili9486_fast.so")

        self._init_display()

    def _write16(self, val: int) -> None:
        GPIO.output(self.PIN_CS, GPIO.LOW)
        for i in range(15, -1, -1):
            GPIO.output(self.PIN_MOSI, (val >> i) & 1)
            GPIO.output(self.PIN_SCLK, GPIO.HIGH)
            GPIO.output(self.PIN_SCLK, GPIO.LOW)
        GPIO.output(self.PIN_CS, GPIO.HIGH)

    def _cmd(self, c: int) -> None:
        GPIO.output(self.PIN_DC, GPIO.LOW)
        self._write16(c & 0xFF)

    def _data(self, *vals: int) -> None:
        GPIO.output(self.PIN_DC, GPIO.HIGH)
        for d in vals:
            self._write16(d & 0xFF)

    def _reset(self) -> None:
        GPIO.output(self.PIN_RST, GPIO.HIGH); time.sleep(0.05)
        GPIO.output(self.PIN_RST, GPIO.LOW);  time.sleep(0.10)
        GPIO.output(self.PIN_RST, GPIO.HIGH); time.sleep(0.15)

    def _init_display(self) -> None:
        self._reset()
        self._cmd(0xB0); self._data(0x00)
        self._cmd(0x11); time.sleep(0.15)
        self._cmd(0x3A); self._data(0x55)
        self._cmd(0xC2); self._data(0x44)
        self._cmd(0xC5); self._data(0x00, 0x00, 0x00, 0x00)
        self._cmd(0xE0); self._data(0x0F, 0x1F, 0x1C, 0x0C, 0x0F, 0x08, 0x48, 0x98, 0x37, 0x0A, 0x13, 0x04, 0x11, 0x0D, 0x00)
        self._cmd(0xE1); self._data(0x0F, 0x32, 0x2E, 0x0B, 0x0D, 0x05, 0x47, 0x75, 0x37, 0x06, 0x10, 0x03, 0x24, 0x20, 0x00)
        self._cmd(0x36); self._data(0x28)
        self._cmd(0x29); time.sleep(0.10)

    def set_window(self, x0: int, y0: int, x1: int, y1: int) -> None:
        self._cmd(0x2A); self._data(x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF)
        self._cmd(0x2B); self._data(y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF)
        self._cmd(0x2C)

    def push_rgb888(self, rgb_img, region=None) -> None:
        """Push full 480x320 image or a dirty sub-region (x0, y0, x1, y1) for fast partial refresh."""
        if region is None:
            x0, y0, x1, y1 = 0, 0, self.WIDTH - 1, self.HEIGHT - 1
            crop = rgb_img
        else:
            x0, y0, x1, y1 = region
            crop = rgb_img.crop((x0, y0, x1 + 1, y1 + 1))

        arr = np.asarray(crop, dtype=np.uint16)
        r = (arr[:, :, 0] >> 3) << 11
        g = (arr[:, :, 1] >> 2) << 5
        b = arr[:, :, 2] >> 3
        rgb565 = np.ascontiguousarray((r | g | b).astype("<u2"))
        self.set_window(x0, y0, x1, y1)
        GPIO.output(self.PIN_DC, GPIO.HIGH)
        num_pixels = (x1 - x0 + 1) * (y1 - y0 + 1)
        if self._lib:
            rc = self._lib.push_rgb565_gpio(rgb565.ctypes.data, num_pixels)
            if rc != 0:
                raise OSError("push_rgb565_gpio failed")
        else:
            for px in rgb565.ravel():
                self._write16(int(px))

    def close(self) -> None:
        if self._lib:
            self._lib.lcd_gpio_close()
        GPIO.cleanup([self.PIN_MOSI, self.PIN_SCLK, self.PIN_CS, self.PIN_DC, self.PIN_RST])
