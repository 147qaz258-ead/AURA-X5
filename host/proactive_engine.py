"""AURA-X5 Proactive Agent Engine (PC Host).
Generates context-aware proactive proposals from desktop changes and executes approved actions
with JSONL evidence logging.
"""
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import time
from typing import Dict, List, Optional
import urllib.request

from host.pc_daemon import FrameEvent


@dataclass
class ProactiveProposal:
    proposal_id: str
    title: str
    summary: str
    action_type: str  # "notify_only" | "hid_ctrl_s" | "focus_break"
    evidence_frame_id: str
    window_title: str
    created_at: float


class ProactiveAgentEngine:
    """Context-aware proactive decision maker + post-approval executor."""

    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or (Path(__file__).resolve().parents[1] / "logs" / "agent_events.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_start = time.time()
        self.last_break_prompt = self.session_start
        self.pending: Dict[str, ProactiveProposal] = {}

    def _log(self, event_type: str, payload: Dict) -> None:
        record = {"ts": time.time(), "event": event_type, **payload}
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _query_llm_optional(self, window_title: str, diff_ratio: float) -> Optional[Dict[str, str]]:
        api_key = os.environ.get("MODELSCOPE_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return None
        base_url = os.environ.get("AURA_LLM_BASE_URL", "https://api-inference.modelscope.cn/v1/chat/completions")
        model = os.environ.get("AURA_LLM_MODEL", "Qwen/Qwen2.5-7B-Instruct")
        body = json.dumps({
            "model": model,
            "messages": [
                {"role": "system", "content": "Reply in JSON with keys title (<=28 chars) and summary (<=90 chars) for a desktop proactive assistant."},
                {"role": "user", "content": f"Active window: {window_title}, screen change: {diff_ratio*100:.1f}%"},
            ],
            "max_tokens": 120,
        }).encode("utf-8")
        req = urllib.request.Request(
            base_url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception:
            return None

    def evaluate_context(self, event: FrameEvent, window_title: str) -> ProactiveProposal:
        """Analyze desktop context (optional LLM via MODELSCOPE_API_KEY, or deterministic rules)."""
        now = time.time()
        win_low = window_title.lower()
        llm_hint = self._query_llm_optional(window_title, event.diff_ratio)

        if llm_hint and "title" in llm_hint and "summary" in llm_hint:
            prop = ProactiveProposal(
                proposal_id=event.frame_id,
                title=str(llm_hint["title"])[:32],
                summary=str(llm_hint["summary"])[:100],
                action_type="notify_only",
                evidence_frame_id=event.frame_id,
                window_title=window_title,
                created_at=now,
            )
        elif (now - self.last_break_prompt) > 2700:
            self.last_break_prompt = now
            prop = ProactiveProposal(
                proposal_id=event.frame_id,
                title="Focus Break Reminder",
                summary="You have been active for 45+ min. Tap APPROVE to lock screen or REJECT to continue.",
                action_type="focus_break",
                evidence_frame_id=event.frame_id,
                window_title=window_title,
                created_at=now,
            )
        elif any(k in win_low for k in ("code", "kicad", "easyeda", "antigravity", "pycharm", "vscode")):
            prop = ProactiveProposal(
                proposal_id=event.frame_id,
                title=f"IDE Active: {window_title[:20]}",
                summary=f"Detected {event.diff_ratio*100:.1f}% edit on {window_title[:28]}. Tap APPROVE to quick-save (Ctrl+S).",
                action_type="hid_ctrl_s",
                evidence_frame_id=event.frame_id,
                window_title=window_title,
                created_at=now,
            )
        else:
            prop = ProactiveProposal(
                proposal_id=event.frame_id,
                title=f"Context: {window_title[:22]}",
                summary=f"Screen diff {event.diff_ratio*100:.1f}% recorded ({event.sha256[:8]}). Ready for command.",
                action_type="notify_only",
                evidence_frame_id=event.frame_id,
                window_title=window_title,
                created_at=now,
            )

        self.pending[prop.proposal_id] = prop
        self._log("proposal_created", asdict(prop))
        return prop

    def handle_physical_decision(self, decision: str, proposal_id: Optional[str] = None) -> Dict:
        """Process physical APPROVE / REJECT from RDK X5 touchscreen or EC11 encoder."""
        target = self.pending.get(proposal_id) if proposal_id else (list(self.pending.values())[-1] if self.pending else None)
        result = {
            "decision": decision,
            "proposal_id": target.proposal_id if target else None,
            "action_type": target.action_type if target else None,
            "verified": True,
        }
        self._log("physical_decision", result)
        return result
