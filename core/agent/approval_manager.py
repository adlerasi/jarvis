"""Approval Manager — Risk-based human approval for ACA actions."""
from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"


class ApprovalRequest:
    """A single approval request for a high/medium risk action."""

    def __init__(
        self,
        step_id: str,
        goal_text: str,
        tool_name: str,
        params: dict[str, Any],
        risk_level: RiskLevel,
        description: str = "",
    ):
        self.request_id: str = str(uuid.uuid4())[:8]
        self.step_id: str = step_id
        self.goal_text: str = goal_text
        self.tool_name: str = tool_name
        self.params: dict[str, Any] = dict(params)
        self.risk_level: RiskLevel = risk_level
        self.description: str = description
        self.status: ApprovalStatus = ApprovalStatus.PENDING
        self.requested_at: float = time.time()
        self.responded_at: float | None = None
        self.response_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "step_id": self.step_id,
            "goal_text": self.goal_text,
            "tool_name": self.tool_name,
            "params": dict(self.params),
            "risk_level": self.risk_level.value,
            "description": self.description,
            "status": self.status.value,
            "requested_at": self.requested_at,
            "responded_at": self.responded_at,
            "response_notes": self.response_notes,
        }


HIGH_RISK_TOOLS: set[str] = {
    "kill_process", "cleanup_folder", "control_service",
    "shell_run",
}

MEDIUM_RISK_TOOLS: set[str] = {
    "browser_control", "list_processes",
    "find_large_files", "find_duplicate_files",
    "get_folder_summary", "get_network_summary",
    "list_net_connections", "ping_host",
    "add_cron_job", "list_cron_jobs", "remove_cron_job",
    "list_services",
}


class ApprovalManager:
    """Manages approval requests for high/medium risk actions."""

    def __init__(self):
        self._requests: dict[str, ApprovalRequest] = {}
        self._approval_timeout: float = 120.0

    def classify_action(self, tool_name: str, params: dict[str, Any] | None = None) -> RiskLevel:
        if tool_name in HIGH_RISK_TOOLS:
            return RiskLevel.HIGH
        if tool_name in MEDIUM_RISK_TOOLS:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def request_approval(
        self,
        step_id: str,
        goal_text: str,
        tool_name: str,
        params: dict[str, Any],
        risk_level: RiskLevel,
        description: str = "",
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            step_id=step_id,
            goal_text=goal_text,
            tool_name=tool_name,
            params=params,
            risk_level=risk_level,
            description=description,
        )
        self._requests[req.request_id] = req
        return req

    def respond_to_approval(self, request_id: str, approved: bool) -> bool:
        req = self._requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return False
        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
        req.responded_at = time.time()
        return True

    def get_pending(self, request_id: str) -> ApprovalRequest | None:
        req = self._requests.get(request_id)
        if req and req.status == ApprovalStatus.PENDING:
            return req
        return None

    def get_all_pending(self) -> list[ApprovalRequest]:
        return [r for r in self._requests.values() if r.status == ApprovalStatus.PENDING]

    def get_history(self) -> list[dict[str, Any]]:
        return [r.to_dict() for r in self._requests.values()]

    def cleanup_expired(self):
        now = time.time()
        expired = [
            rid for rid, req in self._requests.items()
            if req.status == ApprovalStatus.PENDING
            and (now - req.requested_at) > self._approval_timeout
        ]
        for rid in expired:
            self._requests[rid].status = ApprovalStatus.DENIED
            self._requests[rid].responded_at = now
            self._requests[rid].response_notes = "Sure asimi"
