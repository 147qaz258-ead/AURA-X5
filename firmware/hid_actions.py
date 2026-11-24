"""USB Boot Keyboard HID 8-byte report builder for /dev/hidg0 on RDK X5."""
from typing import Dict, List

MOD_LCTRL = 0x01
MOD_LSHIFT = 0x02
MOD_LALT = 0x04
MOD_LGUI = 0x08  # Windows / Super key

KEY_CODES: Dict[str, int] = {
    "a": 0x04, "b": 0x05, "c": 0x06, "d": 0x07, "e": 0x08, "f": 0x09,
    "g": 0x0A, "h": 0x0B, "i": 0x0C, "j": 0x0D, "k": 0x0E, "l": 0x0F,
    "m": 0x10, "n": 0x11, "o": 0x12, "p": 0x13, "q": 0x14, "r": 0x15,
    "s": 0x16, "t": 0x17, "u": 0x18, "v": 0x19, "w": 0x1A, "x": 0x1B,
    "y": 0x1C, "z": 0x1D,
    "enter": 0x28, "esc": 0x29, "tab": 0x2B, "space": 0x2C,
}


def key_report(modifier: int, key_name: str) -> bytes:
    code = KEY_CODES[key_name.lower()]
    return bytes([modifier & 0xFF, 0x00, code, 0, 0, 0, 0, 0])


def release_report() -> bytes:
    return b"\x00" * 8


def macro_ctrl_s() -> List[Dict]:
    return [{"report": list(key_report(MOD_LCTRL, "s"))}]


def macro_win_l() -> List[Dict]:
    return [{"report": list(key_report(MOD_LGUI, "l"))}]
