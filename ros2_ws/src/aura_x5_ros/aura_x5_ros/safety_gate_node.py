"""ROS 2 Hardware Safety Gate Node (/aura_safety_gate_node) for AURA-X5 on RDK X5.
Enforces physical-only approval, proposal TTL expiration, and Kill-Switch latching.
"""
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String
from std_srvs.srv import Trigger

from aura_x5_ros.contracts import (
    SERVICE_RESET_KILL_LATCH,
    TOPIC_ACTION_PROPOSAL,
    TOPIC_DECISION_EVENT,
    TOPIC_HID_COMMAND,
    TOPIC_KILL_SWITCH,
    TOPIC_PERCEPTION_RESULT,
    TOPIC_PHYSICAL_INPUT,
    TOPIC_RADAR_PRESENCE,
    TOPIC_UI_STATE,
    VALID_PHYSICAL_APPROVAL_SOURCES,
    decode_json,
    encode_json,
    ensure_firmware_on_path,
)

ensure_firmware_on_path()
from agent_core import ActionProposal, ProposalState, SafetyGatedAgentCore  # type: ignore


class AuraSafetyGateNode(Node):
    def __init__(self):
        super().__init__("aura_safety_gate_node")
        self.declare_parameter("proposal_ttl_sec", 120.0)
        self.declare_parameter("hid_keyboard_device", "/dev/hidg0")

        hid_path = self.get_parameter("hid_keyboard_device").get_parameter_value().string_value
        self.core = SafetyGatedAgentCore(hid_kb_path=hid_path)
        self.ttl_sec = float(self.get_parameter("proposal_ttl_sec").value)

        self.latest_bpu_ms = None
        self.user_present = None
        self.status_banner = "STANDBY"

        self.pub_hid = self.create_publisher(String, TOPIC_HID_COMMAND, 10)
        self.pub_ui = self.create_publisher(String, TOPIC_UI_STATE, 5)
        self.pub_decision = self.create_publisher(String, TOPIC_DECISION_EVENT, 10)

        self.create_subscription(String, TOPIC_ACTION_PROPOSAL, self._on_proposal, 10)
        self.create_subscription(String, TOPIC_PHYSICAL_INPUT, self._on_physical_input, 10)
        self.create_subscription(Bool, TOPIC_KILL_SWITCH, self._on_kill_switch, 10)
        self.create_subscription(String, TOPIC_PERCEPTION_RESULT, self._on_perception, 5)
        self.create_subscription(String, TOPIC_RADAR_PRESENCE, self._on_radar, 5)

        self.create_service(Trigger, SERVICE_RESET_KILL_LATCH, self._on_reset_kill_latch)
        self.create_timer(0.2, self._publish_ui_state)

    def _on_perception(self, msg: String):
        data = decode_json(msg.data)
        self.latest_bpu_ms = data.get("latency_ms")

    def _on_radar(self, msg: String):
        data = decode_json(msg.data)
        if data.get("connected"):
            self.user_present = data.get("user_present")

    def _on_proposal(self, msg: String):
        data = decode_json(msg.data)
        prop = ActionProposal(
            proposal_id=str(data.get("proposal_id") or data.get("evidence_frame_id") or int(time.time())),
            title=str(data.get("title", "Proactive Suggestion")),
            summary=str(data.get("summary", "")),
            hid_actions=list(data.get("hid_actions", [])),
            evidence_frame_id=str(data.get("evidence_frame_id", "-")),
        )
        self.core.submit_proposal(prop)
        self.status_banner = "PENDING APPROVAL"
        self._publish_ui_state()

    def _on_kill_switch(self, msg: Bool):
        if not msg.data:
            return
        aborted = self.core.trigger_kill_switch()
        self.status_banner = "KILL-SWITCH LATCHED"
        self.get_logger().warn(f"Hardware Kill-Switch engaged! Aborted {aborted} proposal(s).")
        self.pub_hid.publish(String(data=encode_json({
            "ts_ns": self.get_clock().now().nanoseconds,
            "command": "release_all",
        })))
        self._publish_ui_state()

    def _on_reset_kill_latch(self, _request, response):
        self.core.reset_kill_latch()
        self.status_banner = "STANDBY"
        response.success = True
        response.message = "Kill-Switch latch cleared explicitly."
        self.get_logger().info(response.message)
        self._publish_ui_state()
        return response

    def _expire_stale_proposals(self):
        now = time.time()
        for prop in self.core.queue:
            if prop.state == ProposalState.PENDING_APPROVAL and (now - prop.created_at) > self.ttl_sec:
                prop.state = ProposalState.REJECTED

    def _on_physical_input(self, msg: String):
        self._expire_stale_proposals()
        data = decode_json(msg.data)
        source = str(data.get("source", ""))
        decision = str(data.get("decision", ""))

        if decision == "rotate":
            delta = int(data.get("delta", 1))
            self.core.rotate_selection(delta)
            self._publish_ui_state()
            return

        if decision == "reject":
            prop = self.core.reject_current()
            self.status_banner = "REJECTED"
            self.pub_decision.publish(String(data=encode_json({
                "ts_ns": self.get_clock().now().nanoseconds,
                "decision": "reject",
                "source": source,
                "proposal_id": prop.proposal_id if prop else None,
            })))
            self._publish_ui_state()
            return

        if decision == "approve":
            if source not in VALID_PHYSICAL_APPROVAL_SOURCES:
                self.get_logger().error(f"Blocked unauthorized approval source: {source}")
                return
            if self.core.kill_latched:
                self.status_banner = "KILL-SWITCH LATCHED"
                self.get_logger().warn("Cannot approve while Kill-Switch is latched.")
                self._publish_ui_state()
                return
            prop = self.core.current_proposal()
            if prop is None:
                return
            prop.state = ProposalState.APPROVED
            self.status_banner = "APPROVED"
            if prop.hid_actions:
                self.pub_hid.publish(String(data=encode_json({
                    "ts_ns": self.get_clock().now().nanoseconds,
                    "command": "execute_macro",
                    "proposal_id": prop.proposal_id,
                    "hid_actions": prop.hid_actions,
                })))
            prop.state = ProposalState.EXECUTED
            self.pub_decision.publish(String(data=encode_json({
                "ts_ns": self.get_clock().now().nanoseconds,
                "decision": "approve",
                "source": source,
                "proposal_id": prop.proposal_id,
            })))
            self._publish_ui_state()

    def _publish_ui_state(self):
        self._expire_stale_proposals()
        cur = self.core.current_proposal()
        payload = {
            "ts_ns": self.get_clock().now().nanoseconds,
            "type": "ui_state",
            "proposal_title": cur.title if cur else "AURA-X5 ROS 2 Ready",
            "proposal_summary": cur.summary if cur else "Observing desktop context & BPU stream. Waiting for physical confirmation.",
            "evidence_frame_id": cur.evidence_frame_id if cur else "idle",
            "status_banner": self.status_banner,
            "kill_latched": self.core.kill_latched,
            "bpu_ms": self.latest_bpu_ms,
            "user_present": self.user_present,
        }
        self.pub_ui.publish(String(data=encode_json(payload)))


def main(args=None):
    rclpy.init(args=args)
    node = AuraSafetyGateNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
