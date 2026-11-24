"""AURA-X5 Embodied Agent Core & Safety-Gated HID Gateway (runs on RDK X5).
Enforces physical approval (EC11 press or 3.5" XPT2046 touch) and Kill-Switch abort.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import time


class ProposalState(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    ABORTED_BY_KILL_SWITCH = "aborted_by_kill_switch"


@dataclass
class ActionProposal:
    proposal_id: str
    title: str
    summary: str
    hid_actions: List[Dict]
    evidence_frame_id: str
    created_at: float = field(default_factory=time.time)
    state: ProposalState = ProposalState.PENDING_APPROVAL


class SafetyGatedAgentCore:
    """Manages proactive proposals and enforces hardware-only HID execution gates."""

    def __init__(self, hid_kb_path: str = "/dev/hidg0"):
        self.hid_kb_path = hid_kb_path
        self.queue: List[ActionProposal] = []
        self.active_index: int = 0
        self.kill_latched: bool = False

    def submit_proposal(self, proposal: ActionProposal) -> None:
        self.queue.append(proposal)

    def current_proposal(self) -> Optional[ActionProposal]:
        pending = [p for p in self.queue if p.state == ProposalState.PENDING_APPROVAL]
        if not pending:
            return None
        return pending[self.active_index % len(pending)]

    def rotate_selection(self, delta: int) -> Optional[ActionProposal]:
        pending = [p for p in self.queue if p.state == ProposalState.PENDING_APPROVAL]
        if not pending:
            return None
        self.active_index = (self.active_index + delta) % len(pending)
        return pending[self.active_index]

    def trigger_kill_switch(self) -> int:
        """Hardware Kill-Switch: aborts all pending proposals and releases HID keys."""
        self.kill_latched = True
        aborted = 0
        for p in self.queue:
            if p.state in (ProposalState.PENDING_APPROVAL, ProposalState.APPROVED):
                p.state = ProposalState.ABORTED_BY_KILL_SWITCH
                aborted += 1
        self._release_all_hid_keys()
        return aborted

    def reset_kill_latch(self) -> None:
        """Explicit operator recovery after verifying host safety."""
        self.kill_latched = False

    def approve_current(self, physical_source: str) -> Optional[ActionProposal]:
        if physical_source not in ("ec11_press", "xpt2046_touch", "hdmi_local_confirm"):
            raise PermissionError(f"Invalid approval source: {physical_source}")
        if self.kill_latched:
            raise RuntimeError("Kill-Switch latched; clear latch before approving new actions.")
        prop = self.current_proposal()
        if prop is None:
            return None
        prop.state = ProposalState.APPROVED
        self._execute_hid_actions(prop)
        prop.state = ProposalState.EXECUTED
        return prop

    def reject_current(self) -> Optional[ActionProposal]:
        prop = self.current_proposal()
        if prop is None:
            return None
        prop.state = ProposalState.REJECTED
        return prop

    def _release_all_hid_keys(self) -> None:
        try:
            with open(self.hid_kb_path, "wb") as f:
                f.write(b"\x00" * 8)
        except OSError:
            pass

    def _execute_hid_actions(self, prop: ActionProposal) -> None:
        with open(self.hid_kb_path, "wb") as f:
            for act in prop.hid_actions:
                if self.kill_latched:
                    raise RuntimeError("Aborted mid-macro by Kill-Switch")
                report = bytes(act.get("report", [0] * 8))
                if len(report) != 8:
                    raise ValueError("HID boot keyboard report must be 8 bytes")
                f.write(report)
                f.flush()
                time.sleep(0.02)
            f.write(b"\x00" * 8)
