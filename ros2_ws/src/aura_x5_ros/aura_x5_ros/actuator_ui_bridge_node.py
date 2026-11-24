"""ROS 2 Actuator & HDMI/PC UI Bridge Node (/aura_actuator_ui_bridge_node) for AURA-X5.
Bridges host PC WebSocket + 60 FPS HDMI kiosk web UI with ROS 2 topics, executes gated
USB-C HID keyboard reports on /dev/hidg0, and tracks thermal metrics.
"""
import asyncio
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
import websockets

from aura_x5_ros.contracts import (
    TOPIC_ACTION_PROPOSAL,
    TOPIC_BPU_METRICS,
    TOPIC_DECISION_EVENT,
    TOPIC_DESKTOP_FRAME,
    TOPIC_HARDWARE_TELEMETRY,
    TOPIC_HID_COMMAND,
    TOPIC_PHYSICAL_INPUT,
    TOPIC_PRIVACY_STATE,
    TOPIC_UI_STATE,
    decode_json,
    encode_json,
    ensure_firmware_on_path,
)

fw_path = ensure_firmware_on_path()
from hid_actions import release_report  # type: ignore


class AuraActuatorUIBridgeNode(Node):
    def __init__(self):
        super().__init__("aura_actuator_ui_bridge_node")
        self.declare_parameter("http_ui_port", 8080)
        self.declare_parameter("ws_port", 8765)
        self.declare_parameter("hid_keyboard_device", "/dev/hidg0")

        self.http_port = int(self.get_parameter("http_ui_port").value)
        self.ws_port = int(self.get_parameter("ws_port").value)
        self.hid_path = self.get_parameter("hid_keyboard_device").get_parameter_value().string_value

        self.pub_frame = self.create_publisher(String, TOPIC_DESKTOP_FRAME, 2)
        self.pub_proposal = self.create_publisher(String, TOPIC_ACTION_PROPOSAL, 10)
        self.pub_input = self.create_publisher(String, TOPIC_PHYSICAL_INPUT, 10)

        self.create_subscription(String, TOPIC_HID_COMMAND, self._on_hid_command, 10)
        self.create_subscription(String, TOPIC_UI_STATE, self._on_ui_state, 5)
        self.create_subscription(String, TOPIC_BPU_METRICS, self._on_bpu_metrics, 5)
        self.create_subscription(String, TOPIC_HARDWARE_TELEMETRY, self._on_telemetry, 5)
        self.create_subscription(String, TOPIC_DECISION_EVENT, self._on_decision, 10)
        self.create_subscription(Bool, TOPIC_PRIVACY_STATE, self._on_privacy, 5)

        self._ws_clients = set()
        self._ws_loop = None
        self._latest_state = {
            "type": "ui_state",
            "connected_pc": False,
            "proposal_title": "AURA-X5 ROS 2 Bridge Ready",
            "proposal_summary": "Waiting for PC observer & RDK X5 BPU stream.",
            "evidence_frame_id": "idle",
            "status_banner": "STANDBY",
            "bpu_ms": None,
            "bpu_fps": 0.0,
            "soc_temp_c": None,
            "privacy_mic_on": None,
        }

        self._start_http_server()
        self._start_ws_thread()

    def _start_http_server(self):
        ui_dir = fw_path.parent / "ui_web"
        if not ui_dir.exists():
            self.get_logger().warn(f"ui_web directory not found at {ui_dir}; HTTP UI disabled.")
            return
        handler = partial(SimpleHTTPRequestHandler, directory=str(ui_dir))
        self._http_srv = ThreadingHTTPServer(("0.0.0.0", self.http_port), handler)
        threading.Thread(target=self._http_srv.serve_forever, daemon=True).start()
        self.get_logger().info(f"HDMI 60 FPS Web UI served at http://127.0.0.1:{self.http_port}")

    def _start_ws_thread(self):
        def _runner():
            self._ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._ws_loop)
            self._ws_loop.run_until_complete(self._ws_main())

        threading.Thread(target=_runner, daemon=True).start()

    async def _ws_main(self):
        async with websockets.serve(self._ws_handler, "0.0.0.0", self.ws_port):
            self.get_logger().info(f"WebSocket bridge listening on ws://0.0.0.0:{self.ws_port}")
            await asyncio.Future()

    async def _ws_handler(self, websocket):
        self._ws_clients.add(websocket)
        self._latest_state["connected_pc"] = True
        await websocket.send(encode_json(self._latest_state))
        try:
            async for raw in websocket:
                data = decode_json(raw)
                mtype = data.get("type")
                if mtype == "proactive_proposal":
                    if data.get("thumb_b64"):
                        self.pub_frame.publish(String(data=encode_json({
                            "ts_ns": self.get_clock().now().nanoseconds,
                            "frame_id": data.get("evidence_frame_id", "frame"),
                            "thumb_b64": data["thumb_b64"],
                        })))
                    self.pub_proposal.publish(String(data=encode_json(data)))
                elif mtype == "ui_decision":
                    self.pub_input.publish(String(data=encode_json({
                        "ts_ns": self.get_clock().now().nanoseconds,
                        "source": "hdmi_local_confirm",
                        "decision": data.get("decision", "reject"),
                    })))
        finally:
            self._ws_clients.discard(websocket)
            self._latest_state["connected_pc"] = len(self._ws_clients) > 0

    def _broadcast_ws(self, payload: dict):
        if self._ws_loop is None or not self._ws_clients:
            return
        raw = encode_json(payload)

        async def _send_all():
            await asyncio.gather(*(c.send(raw) for c in list(self._ws_clients)), return_exceptions=True)

        asyncio.run_coroutine_threadsafe(_send_all(), self._ws_loop)

    def _on_ui_state(self, msg: String):
        self._latest_state.update(decode_json(msg.data))
        self._broadcast_ws(self._latest_state)

    def _on_bpu_metrics(self, msg: String):
        data = decode_json(msg.data)
        self._latest_state["bpu_fps"] = data.get("fps")
        self._latest_state["bpu_ms"] = data.get("avg_ms")
        self._latest_state["soc_temp_c"] = data.get("soc_temp_c")
        self._broadcast_ws(self._latest_state)

    def _on_telemetry(self, msg: String):
        self._latest_state["telemetry"] = decode_json(msg.data)

    def _on_privacy(self, msg: Bool):
        self._latest_state["privacy_mic_on"] = bool(msg.data)
        self._broadcast_ws(self._latest_state)

    def _on_decision(self, msg: String):
        data = decode_json(msg.data)
        self._broadcast_ws({"type": "decision", "decision": data.get("decision")})

    def _write_hid_release(self):
        try:
            with open(self.hid_path, "wb") as f:
                f.write(release_report())
                f.flush()
        except OSError:
            pass

    def _on_hid_command(self, msg: String):
        data = decode_json(msg.data)
        cmd = data.get("command")
        if cmd == "release_all":
            self._write_hid_release()
            return
        if cmd == "execute_macro":
            actions = data.get("hid_actions", [])
            try:
                with open(self.hid_path, "wb") as f:
                    for act in actions:
                        report = bytes(act.get("report", [0] * 8))
                        if len(report) != 8:
                            raise ValueError("HID boot keyboard report must be 8 bytes")
                        f.write(report)
                        f.flush()
                        time.sleep(0.02)
                    f.write(release_report())
                    f.flush()
            except OSError as exc:
                self.get_logger().warn(f"USB HID device unavailable ({self.hid_path}): {exc}")


def main(args=None):
    rclpy.init(args=args)
    node = AuraActuatorUIBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._write_hid_release()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
