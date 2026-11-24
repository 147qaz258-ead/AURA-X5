"""AURA-X5 V2 HDMI Edition: 60 FPS Web UI Server + WebSocket + BPU + Solderless GPIO Controls.
Serves aura_x5/ui_web/index.html on http://127.0.0.1:8080 and WebSocket on ws://0.0.0.0:8765.
"""
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys
import threading
import time
import websockets

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "firmware"))
from agent_core import ActionProposal, SafetyGatedAgentCore
from sensor_hub import probe_connected_hardware

UI_DIR = ROOT / "ui_web"
CLIENTS = set()
core = SafetyGatedAgentCore()

state_dict = {
    "type": "ui_state",
    "connected_pc": False,
    "proposal_title": "AURA-X5 V2 HDMI 就绪",
    "proposal_summary": "等待 PC 端主动上下文连接。支持 EC11 旋钮 / Kill-Switch / 键盘 Enter & Esc 审批。",
    "evidence_frame_id": "idle",
    "status_banner": "STANDBY",
    "bpu_ms": None,
}


def start_http_server(port: int = 8080):
    handler = partial(SimpleHTTPRequestHandler, directory=str(UI_DIR))
    srv = ThreadingHTTPServer(("0.0.0.0", port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


async def broadcast_state():
    if not CLIENTS:
        return
    payload = json.dumps(state_dict, ensure_ascii=False)
    await asyncio.gather(*(c.send(payload) for c in list(CLIENTS)), return_exceptions=True)


async def ws_handler(websocket):
    CLIENTS.add(websocket)
    await websocket.send(json.dumps(state_dict, ensure_ascii=False))
    try:
        async for raw in websocket:
            data = json.loads(raw)
            mtype = data.get("type")
            if mtype == "proactive_proposal":
                state_dict["connected_pc"] = True
                state_dict["proposal_title"] = data.get("title", "Proactive Suggestion")
                state_dict["proposal_summary"] = data.get("summary", "")
                state_dict["evidence_frame_id"] = data.get("evidence_frame_id", "-")
                state_dict["status_banner"] = "PENDING APPROVAL"
                prop = ActionProposal(
                    proposal_id=state_dict["evidence_frame_id"],
                    title=state_dict["proposal_title"],
                    summary=state_dict["proposal_summary"],
                    hid_actions=data.get("hid_actions", []),
                    evidence_frame_id=state_dict["evidence_frame_id"],
                )
                core.submit_proposal(prop)
                await broadcast_state()
            elif mtype == "ui_decision":
                dec = data.get("decision")
                state_dict["status_banner"] = "APPROVED" if dec == "approve" else "REJECTED"
                await broadcast_state()
                await broadcast_decision(dec)
    finally:
        CLIENTS.discard(websocket)


async def broadcast_decision(decision: str):
    payload = json.dumps({"type": "decision", "decision": decision})
    await asyncio.gather(*(c.send(payload) for c in list(CLIENTS)), return_exceptions=True)


async def main():
    start_http_server(8080)
    print(f"AURA-X5 V2 HDMI UI: http://127.0.0.1:8080 | WS: ws://0.0.0.0:8765")
    async with websockets.serve(ws_handler, "0.0.0.0", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
