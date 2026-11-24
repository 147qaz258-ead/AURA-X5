"""AURA-X5 PC Host Live Agent: Streams Windows screen diffs + 224x224 thumb to RDK X5 BPU."""
import asyncio
import base64
import ctypes
import io
import json
import os
from pathlib import Path
import sys
import numpy as np
from PIL import ImageGrab
import websockets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from host.pc_daemon import ScreenChangeDetector
from host.proactive_engine import ProactiveAgentEngine

RDK_WS_URL = os.environ.get("AURA_RDK_WS", "ws://192.168.128.10:8765")


def get_active_window_title() -> str:
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value or "Desktop"
    except Exception:
        return "Desktop"


async def main():
    detector = ScreenChangeDetector(diff_threshold=0.02)
    engine = ProactiveAgentEngine()
    print(f"Connecting to AURA-X5 RDK X5 at {RDK_WS_URL}...")
    async with websockets.connect(RDK_WS_URL) as ws:
        print("Connected to RDK X5! Observing Windows desktop changes...")

        async def recv_events():
            async for msg in ws:
                data = json.loads(msg)
                if data.get("type") == "decision":
                    res = engine.handle_physical_decision(data["decision"])
                    print(f"[RDK X5 HARDWARE DECISION] {res}")
                else:
                    print(f"[RDK X5 BPU ACK] {data}")

        recv_task = asyncio.create_task(recv_events())
        try:
            while True:
                shot = ImageGrab.grab().resize((224, 224))
                ev = detector.process_frame(np.asarray(shot))
                if ev is not None:
                    win = get_active_window_title()
                    prop = engine.evaluate_context(ev, win)
                    buf = io.BytesIO()
                    shot.save(buf, format="JPEG", quality=70)
                    payload = json.dumps({
                        "type": "proactive_proposal",
                        "evidence_frame_id": prop.evidence_frame_id,
                        "diff_ratio": ev.diff_ratio,
                        "title": prop.title,
                        "summary": prop.summary,
                        "thumb_b64": base64.b64encode(buf.getvalue()).decode("ascii"),
                    }, ensure_ascii=False)
                    await ws.send(payload)
                    print(f"[PC -> RDK BPU] Sent {prop.proposal_id} ({win[:28]})")
                await asyncio.sleep(1.5)
        finally:
            recv_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
