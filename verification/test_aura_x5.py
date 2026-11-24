"""AURA-X5 End-to-End Verification Suite (Contract, Firmware Logic, Host Diff, CAD Fit)."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from firmware.hal_devices import parse_ld2410c_frame
from firmware.agent_core import ActionProposal, ProposalState, SafetyGatedAgentCore
from firmware.sensors_full import sht40_crc8, ws2812_color_for_state
from firmware.display_ui import hit_test_touch
from firmware.hid_actions import macro_ctrl_s, macro_win_l, release_report
from host.pc_daemon import ScreenChangeDetector, FrameEvent
from host.proactive_engine import ProactiveAgentEngine


class TestAuraX5System(unittest.TestCase):
    def test_interfaces_contract_present_and_conflict_free(self):
        cfg = json.loads((ROOT / "interfaces.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["project"], "AURA-X5")
        self.assertEqual(cfg["display_module"]["resolution"], {"width": 480, "height": 320})
        # Verify zero 40-pin conflicts across all subsystems
        used_pins = {}
        pin_map = cfg["pin_map_40pin"]
        for group_name, group in pin_map.items():
            for k, v in group.items():
                if k.endswith("_pin") and isinstance(v, int):
                    self.assertNotIn(v, used_pins, f"Pin {v} conflict between {group_name}.{k} and {used_pins.get(v)}")
                    used_pins[v] = f"{group_name}.{k}"

    def test_ld2410c_radar_frame_parser(self):
        # Construct valid 23-byte HLK-LD2410C normal frame
        body = bytearray(13)
        body[0] = 0x02  # normal data
        body[1] = 0xAA  # head
        body[2] = 0x03  # moving + stationary
        struct.pack_into("<H", body, 3, 85)   # moving dist 85cm
        body[5] = 90                           # moving energy
        struct.pack_into("<H", body, 6, 80)   # static dist 80cm
        body[8] = 95                           # static energy
        struct.pack_into("<H", body, 9, 82)   # detect dist 82cm
        frame = b"\xf4\xf3\xf2\xf1" + struct.pack("<H", len(body)) + bytes(body) + b"\x55\x00\xf8\xf7\xf6\xf5"
        reading = parse_ld2410c_frame(frame)
        self.assertIsNotNone(reading)
        self.assertTrue(reading.user_present)
        self.assertEqual(reading.moving_dist_cm, 85)
        self.assertEqual(reading.static_dist_cm, 80)

    def test_safety_gated_hid_approval_and_kill_switch(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            hid_path = tf.name
        core = SafetyGatedAgentCore(hid_kb_path=hid_path)
        prop = ActionProposal(
            proposal_id="p1",
            title="Auto-format log",
            summary="Press Ctrl+S",
            hid_actions=[{"report": [0x01, 0, 0x16, 0, 0, 0, 0, 0]}],
            evidence_frame_id="frame-000001",
        )
        core.submit_proposal(prop)
        # Software/non-physical approval must be rejected
        with self.assertRaises(PermissionError):
            core.approve_current("remote_api")
        # Physical touch approval succeeds and writes 8-byte HID report + release
        executed = core.approve_current("xpt2046_touch")
        self.assertEqual(executed.state, ProposalState.EXECUTED)
        raw = Path(hid_path).read_bytes()
        self.assertEqual(len(raw), 16)
        self.assertEqual(raw[:8], bytes([0x01, 0, 0x16, 0, 0, 0, 0, 0]))
        self.assertEqual(raw[8:], b"\x00" * 8)

        # Kill-Switch aborts pending proposals and latches
        prop2 = ActionProposal("p2", "Next", "Test", [], "frame-000002")
        core.submit_proposal(prop2)
        aborted = core.trigger_kill_switch()
        self.assertEqual(aborted, 1)
        self.assertEqual(prop2.state, ProposalState.ABORTED_BY_KILL_SWITCH)
        with self.assertRaises(RuntimeError):
            core.approve_current("ec11_press")

    def test_pc_screen_change_detector(self):
        det = ScreenChangeDetector(diff_threshold=0.05)
        f1 = np.zeros((100, 100, 3), dtype=np.uint8)
        ev1 = det.process_frame(f1)
        self.assertIsNotNone(ev1)
        # Identical frame should be filtered out
        self.assertIsNone(det.process_frame(f1.copy()))
        # Significant change (>5%) should trigger
        f2 = f1.copy()
        f2[:20, :50] = 255
        ev2 = det.process_frame(f2)
        self.assertIsNotNone(ev2)
        self.assertGreater(ev2.diff_ratio, 0.05)

    def test_mechanical_stls_watertight(self):
        fit = json.loads((ROOT / "mechanical" / "fit_check.json").read_text(encoding="utf-8"))
        for part_name in ("base_shell", "front_console_flat", "encoder_knob"):
            self.assertTrue(fit[part_name]["watertight"], f"{part_name} is not watertight")

    def test_sensors_crc_and_ws2812_mapping(self):
        # Sensirion SHT4x datasheet example: 0xBE 0xEF -> CRC 0x92
        self.assertEqual(sht40_crc8(b"\xBE\xEF"), 0x92)
        self.assertEqual(ws2812_color_for_state("STANDBY", privacy_cut=True), (180, 20, 20))
        self.assertEqual(ws2812_color_for_state("APPROVED", privacy_cut=False), (20, 200, 80))

    def test_multipage_touch_and_proactive_engine(self):
        self.assertEqual(hit_test_touch(260, 20, "AGENT"), "page_HOME")
        self.assertEqual(hit_test_touch(340, 20, "HOME"), "page_SENSORS")
        self.assertEqual(hit_test_touch(120, 270, "AGENT"), "approve")
        with tempfile.TemporaryDirectory() as td:
            eng = ProactiveAgentEngine(log_path=Path(td) / "events.jsonl")
            ev = FrameEvent("frame-000001", 100.0, "abc12345", 0.12, 1920, 1080)
            prop = eng.evaluate_context(ev, "Visual Studio Code")
            self.assertEqual(prop.action_type, "hid_ctrl_s")
            res = eng.handle_physical_decision("approve", prop.proposal_id)
            self.assertTrue(res["verified"])

    def test_hid_macro_reports(self):
        ctrl_s = macro_ctrl_s()
        self.assertEqual(bytes(ctrl_s[0]["report"]), bytes([0x01, 0x00, 0x16, 0, 0, 0, 0, 0]))
        win_l = macro_win_l()
        self.assertEqual(bytes(win_l[0]["report"]), bytes([0x08, 0x00, 0x0F, 0, 0, 0, 0, 0]))
        self.assertEqual(release_report(), b"\x00" * 8)

    def test_hdmi_v2_ui_offline_self_contained(self):
        html = (ROOT / "ui_web" / "index.html").read_text(encoding="utf-8")
        self.assertIn("auraCanvas", html)
        self.assertIn("ws://${host}:8765", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)
        import firmware.hdmi_server as hs  # noqa: F401
        self.assertEqual(hs.state_dict["status_banner"], "STANDBY")

    def test_ros2_contracts_and_sensor_sync(self):
        sys.path.insert(0, str(ROOT / "ros2_ws" / "src" / "aura_x5_ros"))
        from aura_x5_ros.contracts import (
            SERVICE_RESET_KILL_LATCH,
            TOPIC_BPU_METRICS,
            TOPIC_HID_COMMAND,
            TOPIC_KILL_SWITCH,
            TOPIC_PERCEPTION_RESULT,
            evaluate_sensor_sync,
            resolve_firmware_path,
        )
        self.assertEqual(TOPIC_PERCEPTION_RESULT, "/aura/perception_result")
        self.assertEqual(TOPIC_BPU_METRICS, "/aura/bpu_metrics")
        self.assertEqual(TOPIC_KILL_SWITCH, "/aura/kill_switch")
        self.assertEqual(TOPIC_HID_COMMAND, "/aura/hid_command")
        self.assertEqual(SERVICE_RESET_KILL_LATCH, "/aura/reset_kill_latch")
        self.assertIsNotNone(resolve_firmware_path())

        now = 1_700_000_000_000_000_000
        ok_sync = evaluate_sensor_sync(now - 50_000_000, now - 100_000_000, max_skew_ms=500.0, now_timestamp_ns=now)
        self.assertTrue(ok_sync.in_sync)
        self.assertFalse(ok_sync.stale)
        bad_sync = evaluate_sensor_sync(now - 100_000_000, now - 900_000_000, max_skew_ms=500.0, now_timestamp_ns=now)
        self.assertFalse(bad_sync.in_sync)

    def test_kill_latch_reset_and_hdmi_confirm(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            hid_path = tf.name
        core = SafetyGatedAgentCore(hid_kb_path=hid_path)
        core.trigger_kill_switch()
        self.assertTrue(core.kill_latched)
        core.reset_kill_latch()
        self.assertFalse(core.kill_latched)
        prop = ActionProposal("p3", "HDMI Confirm", "Save", [{"report": [0x01, 0, 0x16, 0, 0, 0, 0, 0]}], "f-3")
        core.submit_proposal(prop)
        done = core.approve_current("hdmi_local_confirm")
        self.assertEqual(done.state, ProposalState.EXECUTED)

    def test_concurrent_bpu_benchmark_summary_and_markdown(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import benchmark_bpu_concurrent as bench
        summary = bench.summarize_benchmark(
            model_name="mobilenetv2_224x224_nv12",
            runtime_desc="hbm_runtime",
            input_shape=[1, 3, 224, 224],
            latencies_ms=[10.0, 12.0, 11.0, 15.0],
            elapsed_sec=2.0,
            concurrent_cycles=40,
            cpu_samples_pct=[28.0, 32.0],
            temp_samples_c=[46.0, 51.5],
        )
        self.assertEqual(summary["fps"], 2.0)
        self.assertEqual(summary["soc_temp_max_c"], 51.5)
        row = bench.format_markdown_row(summary)
        self.assertIn("mobilenetv2_224x224_nv12", row)
        self.assertIn("2.0 FPS", row)

    def test_no_hardcoded_ssh_passwords_in_scripts(self):
        for py_file in (ROOT / "scripts").glob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            self.assertNotIn('"root", "root"', content, f"Hardcoded password found in {py_file.name}")

    def test_winter_challenge_deliverables_present(self):
        required = [
            "README.md",
            "LICENSE",
            "ROADMAP.md",
            "models/README.md",
            "docs/STAGE1_IGNITE.md",
            "docs/PROPOSAL.md",
            "docs/ARCHITECTURE.md",
            "docs/ENGINEERING_PLAN.md",
            "docs/BENCHMARKS_AND_SAFETY.md",
            "docs/ADVOCATOR_CONTENT_PLAN.md",
            "showcase_pr/ParticipantName-Project-AURA-X5.md",
            "ros2_ws/src/aura_x5_ros/package.xml",
            "ros2_ws/src/aura_x5_ros/setup.py",
            "ros2_ws/src/aura_x5_ros/launch/aura_x5.launch.py",
            "ros2_ws/src/aura_x5_ros/config/aura_x5_params.yaml",
        ]
        for rel in required:
            self.assertTrue((ROOT / rel).exists(), f"Missing challenge deliverable: {rel}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
