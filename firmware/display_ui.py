"""AURA-X5 3.5inch (480x320) Multi-Page Embodied UI Renderer.
Pages:
  - AGENT: Proactive suggestion card + [APPROVE] / [REJECT]
  - HOME:  Embodied AURA-X5 avatar + live status overview
  - SENSORS: Real I2C/UART/HID/Privacy hardware telemetry grid
"""
from dataclasses import dataclass
from typing import Optional
from PIL import Image, ImageDraw, ImageFont


WIDTH = 480
HEIGHT = 320

# Top navigation tabs
TAB_AGENT = (140, 8, 224, 38)
TAB_HOME = (232, 8, 304, 38)
TAB_SENSORS = (312, 8, 404, 38)

BTN_APPROVE = (20, 242, 230, 304)
BTN_REJECT = (250, 242, 460, 304)
CARD_REGION = (16, 54, 464, 230)


@dataclass
class UIState:
    active_page: str = "AGENT"  # "AGENT" | "HOME" | "SENSORS"
    connected_pc: bool = False
    privacy_mic_on: bool = False
    user_present: bool = True
    bpu_load_pct: int = 0
    proposal_title: str = "AURA-X5 Standby"
    proposal_summary: str = "Observing desktop context via RDK X5 10-TOPS BPU..."
    evidence_frame_id: str = "-"
    status_banner: str = "READY"
    sensors_summary: str = "RADAR:NC | I2C:NC | HID:NC"
    radar_status: str = "ttyS1: READY"
    i2c_status: str = "VL53L1X/SHT40/INA219: NOT ATTACHED"
    audio_status: str = "INMP441/MAX98357A: PRIVACY CUT"
    hid_status: str = "USB-C HID (/dev/hidg0): STANDBY"


def _load_font(size: int):
    for path in (
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_ui_image(state: UIState) -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), (11, 15, 25))
    draw = ImageDraw.Draw(img)
    f_hdr = _load_font(18)
    f_title = _load_font(20)
    f_body = _load_font(15)
    f_small = _load_font(12)

    # Top header bar + embodied ring + 3 page tabs
    draw.rectangle([0, 0, WIDTH, 46], fill=(18, 24, 38))
    draw.line([(0, 46), (WIDTH, 46)], fill=(40, 52, 78), width=1)

    ring_col = (56, 189, 248) if state.connected_pc else (148, 163, 184)
    if "APPROVED" in state.status_banner:
        ring_col = (34, 197, 94)
    elif "REJECTED" in state.status_banner:
        ring_col = (239, 68, 68)

    draw.ellipse([10, 9, 38, 37], outline=ring_col, width=3)
    draw.ellipse([18, 17, 30, 29], fill=ring_col)
    draw.text((44, 13), "AURA", fill=(241, 245, 249), font=f_hdr)

    for label, box in (("AGENT", TAB_AGENT), ("HOME", TAB_HOME), ("SENS", TAB_SENSORS)):
        key = "SENSORS" if label == "SENS" else label
        active = state.active_page == key
        fill = (37, 99, 235) if active else (30, 41, 59)
        draw.rounded_rectangle(list(box), radius=8, fill=fill)
        draw.text((box[0] + 12, box[1] + 8), label, fill=(255, 255, 255), font=f_small)

    # Rightmost link dot
    pc_col = (16, 185, 129) if state.connected_pc else (239, 68, 68)
    draw.rounded_rectangle([412, 10, 470, 36], radius=10, fill=pc_col)
    draw.text((422, 15), "LINK" if state.connected_pc else "WAIT", fill=(255, 255, 255), font=f_small)

    if state.active_page == "HOME":
        # Embodied Persona Avatar Page
        draw.rounded_rectangle([16, 56, 464, 302], radius=14, fill=(18, 25, 40), outline=(56, 72, 104), width=2)
        draw.ellipse([175, 82, 305, 212], outline=ring_col, width=5)
        # Dual expressive digital eyes
        draw.rounded_rectangle([206, 128, 226, 164], radius=8, fill=(224, 242, 254))
        draw.rounded_rectangle([254, 128, 274, 164], radius=8, fill=(224, 242, 254))
        draw.text((135, 228), "AURA-X5 EMBODIED CORE", fill=(148, 163, 184), font=f_hdr)
        draw.text((112, 260), f"BPU: 10 TOPS  |  {state.sensors_summary}", fill=(100, 116, 139), font=f_small)
        return img

    if state.active_page == "SENSORS":
        # Real Hardware Telemetry Page
        draw.rounded_rectangle([16, 56, 464, 302], radius=12, fill=(18, 25, 40), outline=(56, 72, 104), width=2)
        draw.text((30, 68), "HARDWARE BUS TELEMETRY", fill=(125, 211, 252), font=f_hdr)
        rows = [
            ("mmWave Radar", state.radar_status),
            ("I2C Sensors", state.i2c_status),
            ("I2S Audio/Priv", state.audio_status),
            ("USB-C Gadget", state.hid_status),
        ]
        for idx, (k, v) in enumerate(rows):
            y = 108 + idx * 46
            draw.rounded_rectangle([28, y, 452, y + 36], radius=8, fill=(26, 35, 54))
            draw.text((40, y + 9), f"{k}:", fill=(148, 163, 184), font=f_small)
            draw.text((160, y + 9), v[:34], fill=(226, 232, 240), font=f_small)
        return img

    # Default Page: AGENT Proposal & Approval
    card_border = (56, 72, 104)
    banner_col = (56, 189, 248)
    if "APPROVED" in state.status_banner:
        card_border = (34, 197, 94)
        banner_col = (74, 222, 128)
    elif "REJECTED" in state.status_banner:
        card_border = (239, 68, 68)
        banner_col = (248, 113, 113)

    draw.rounded_rectangle(list(CARD_REGION), radius=12, fill=(20, 27, 42), outline=card_border, width=3)
    draw.text((30, 66), state.proposal_title[:34], fill=(125, 211, 252), font=f_title)
    draw.text((30, 102), state.proposal_summary[:50], fill=(226, 232, 240), font=f_body)
    draw.text((30, 126), state.proposal_summary[50:100], fill=(203, 213, 225), font=f_body)

    draw.line([(30, 158), (450, 158)], fill=(38, 49, 72), width=1)
    draw.text((30, 168), state.status_banner, fill=banner_col, font=f_hdr)
    draw.text(
        (30, 198),
        f"Frame: {state.evidence_frame_id}  |  BPU: {state.bpu_load_pct}%  |  {state.sensors_summary}",
        fill=(148, 163, 184),
        font=f_small,
    )

    draw.rounded_rectangle(list(BTN_APPROVE), radius=12, fill=(21, 128, 61), outline=(74, 222, 128), width=2)
    draw.text((76, 261), "APPROVE", fill=(255, 255, 255), font=f_title)

    draw.rounded_rectangle(list(BTN_REJECT), radius=12, fill=(185, 28, 28), outline=(248, 113, 113), width=2)
    draw.text((314, 261), "REJECT", fill=(255, 255, 255), font=f_title)
    return img


def hit_test_touch(x: int, y: int, active_page: str = "AGENT") -> Optional[str]:
    if TAB_AGENT[0] <= x <= TAB_AGENT[2] and TAB_AGENT[1] <= y <= TAB_AGENT[3]:
        return "page_AGENT"
    if TAB_HOME[0] <= x <= TAB_HOME[2] and TAB_HOME[1] <= y <= TAB_HOME[3]:
        return "page_HOME"
    if TAB_SENSORS[0] <= x <= TAB_SENSORS[2] and TAB_SENSORS[1] <= y <= TAB_SENSORS[3]:
        return "page_SENSORS"
    if active_page == "AGENT":
        if BTN_APPROVE[0] <= x <= BTN_APPROVE[2] and BTN_APPROVE[1] <= y <= BTN_APPROVE[3]:
            return "approve"
        if BTN_REJECT[0] <= x <= BTN_REJECT[2] and BTN_REJECT[1] <= y <= BTN_REJECT[3]:
            return "reject"
    return None
