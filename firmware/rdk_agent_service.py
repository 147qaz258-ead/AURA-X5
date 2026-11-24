"""AURA-X5 Live RDK X5 Service: Real 10-TOPS BPU + 3.5" Multi-Page Touch UI + WebSocket Server."""
import asyncio
import base64
import io
import json
import sys
import threading
import time
import numpy as np
from PIL import Image
import websockets

sys.path.insert(0, "/opt/aura_x5")
from ili9486_spi import ILI9486ShiftSPI
from display_ui import UIState, render_ui_image, hit_test_touch, CARD_REGION
from hal_devices import XPT2046Touch
from agent_core import ActionProposal, SafetyGatedAgentCore
from sensor_hub import probe_connected_hardware
from bpu_vision import RDKX5BPUService, BPUUnavailableError

DEFAULT_BPU_MODEL = "/app/multimedia_samples/sunrise_camera/Platform/x5/model_zoom/mobilenetv2_224x224_nv12.bin"

CLIENTS = set()
spi_lock = threading.Lock()
touch = XPT2046Touch()
lcd = ILI9486ShiftSPI()
core = SafetyGatedAgentCore()
hw_tel = probe_connected_hardware()

try:
    bpu = RDKX5BPUService(DEFAULT_BPU_MODEL)
    BPU_READY = True
except BPUUnavailableError as exc:
    bpu = None
    BPU_READY = False
    print(f"[BPU] Unavailable: {exc}")

ui_state = UIState(
    active_page="AGENT",
    connected_pc=False,
    privacy_mic_on=False,
    user_present=True,
    bpu_load_pct=0,
    proposal_title="AURA-X5 Ready",
    proposal_summary="BPU 10-TOPS online. Observing desktop context over USB-C...",
    evidence_frame_id="idle",
    status_banner="STANDBY",
    sensors_summary=f"BPU:{'ON' if BPU_READY else 'NC'} | RADAR:{'ON' if hw_tel.uart_radar_ld2410c else 'NC'}",
    hid_status=f"USB-C HID (/dev/hidg0): {'READY' if hw_tel.hid_keyboard_ready else 'NOT_CONFIGURED'}",
)


def refresh_screen(region=None):
    img = render_ui_image(ui_state)
    with spi_lock:
        lcd.push_rgb888(img, region=region)


async def broadcast(msg: dict):
    if not CLIENTS:
        return
    payload = json.dumps(msg, ensure_ascii=False)
    await asyncio.gather(*(c.send(payload) for c in list(CLIENTS)), return_exceptions=True)


def run_bpu_on_b64_thumb(b64_jpg: str):
    if not bpu:
        return None
    raw = base64.b64decode(b64_jpg)
    img = Image.open(io.BytesIO(raw)).convert("RGB").resize((224, 224))
    arr = np.asarray(img, dtype=np.uint8).transpose(2, 0, 1)[None, ...]  # [1, 3, 224, 224]
    return bpu.infer_chw_uint8(np.ascontiguousarray(arr))


async def ws_handler(websocket):
    CLIENTS.add(websocket)
    ui_state.connected_pc = True
    ui_state.status_banner = "PC LINKED"
    refresh_screen()
    try:
        async for raw in websocket:
            data = json.loads(raw)
            if data.get("type") == "proactive_proposal":
                bpu_ms = None
                if data.get("thumb_b64") and BPU_READY:
                    res = run_bpu_on_b64_thumb(data["thumb_b64"])
                    if res:
                        bpu_ms = res.latency_ms
                        ui_state.bpu_load_pct = max(1, min(100, int(bpu_ms)))
                prop = ActionProposal(
                    proposal_id=data.get("evidence_frame_id", str(int(time.time()))),
                    title=data.get("title", "Proactive Suggestion"),
                    summary=data.get("summary", ""),
                    hid_actions=data.get("hid_actions", []),
                    evidence_frame_id=data.get("evidence_frame_id", "-"),
                )
                core.submit_proposal(prop)
                ui_state.proposal_title = prop.title
                ui_state.proposal_summary = prop.summary
                ui_state.evidence_frame_id = f"{prop.evidence_frame_id} ({bpu_ms}ms)" if bpu_ms else prop.evidence_frame_id
                ui_state.status_banner = "TAP APPROVE/REJECT"
                refresh_screen(region=CARD_REGION if ui_state.active_page == "AGENT" else None)
                await websocket.send(json.dumps({"type": "bpu_ack", "frame_id": prop.proposal_id, "bpu_ms": bpu_ms}))
    finally:
        CLIENTS.discard(websocket)
        ui_state.connected_pc = len(CLIENTS) > 0
        refresh_screen()


async def touch_loop():
    last_tap = 0.0
    while True:
        with spi_lock:
            raw = touch.read_raw()
            pt = touch.read_point()
        if raw[2] > 40:
            print(f"[TOUCH] raw={raw} mapped={pt}")
        if pt and (time.time() - last_tap) > 0.6:
            last_tap = time.time()
            action = hit_test_touch(pt[0], pt[1], ui_state.active_page)
            if action and action.startswith("page_"):
                ui_state.active_page = action.split("_", 1)[1]
                refresh_screen()
            elif action == "approve":
                ui_state.status_banner = "APPROVED BY TOUCH"
                refresh_screen(region=CARD_REGION)
                await broadcast({"type": "decision", "decision": "approve", "point": pt})
            elif action == "reject":
                core.reject_current()
                ui_state.status_banner = "REJECTED BY TOUCH"
                refresh_screen(region=CARD_REGION)
                await broadcast({"type": "decision", "decision": "reject", "point": pt})
        await asyncio.sleep(0.05)


async def main():
    refresh_screen()
    async with websockets.serve(ws_handler, "0.0.0.0", 8765):
        print(f"AURA-X5 RDK Service listening on ws://0.0.0.0:8765 (BPU_READY={BPU_READY})")
        await touch_loop()


if __name__ == "__main__":
    asyncio.run(main())
