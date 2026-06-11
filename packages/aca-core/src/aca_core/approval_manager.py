"""
Approval Manager — Risk classification and human approval flow
Adler ASİ tarafından yapılmıştır
"""
from __future__ import annotations

import time
from dataclasses import dataclass
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
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """A human approval request for a potentially risky action."""
    request_id: str
    step_id: str
    goal_text: str
    tool_name: str
    params: dict[str, Any]
    risk_level: RiskLevel
    description: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = 0.0
    responded_at: float | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "step_id": self.step_id,
            "goal_text": self.goal_text,
            "tool_name": self.tool_name,
            "params": self.params,
            "risk_level": self.risk_level.value,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at,
            "responded_at": self.responded_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ApprovalRequest:
        data = dict(data)
        data["risk_level"] = RiskLevel(data["risk_level"])
        data["status"] = ApprovalStatus(data["status"])
        return cls(**data)


_HIGH_RISK_TOOLS: dict[str, str] = {
    "kill_process": "Surec sonlandirma",
    "cleanup_folder": "Dosya temizleme",
    "cleanup_recycle_bin": "Geri donusum kutusu temizligi",
    "control_service": "Servis kontrolu",
}

_MEDIUM_RISK_TOOLS: dict[str, str] = {
    "shell_run": "Shell komutu",
    "browser_control": "Tarayici kontrolu",
    "set_process_priority": "Surec onceligi degistirme",
}

_WRITE_SHELL_PREFIXES = (
    "rm ", "mv ", "cp ", "dd ", "mkfs", "format ",
    "del ", "erase ", "rmdir ", "rd ", "remove-item",
    ">", ">>", "| ",
)


class ApprovalManager:
    """Manages risk classification and human approval for ACA actions.

    High-risk actions ALWAYS require approval.
    Medium-risk actions require approval only in approval mode.
    Low-risk actions execute freely.
    """

    def __init__(self):
        self._pending_requests: dict[str, ApprovalRequest] = {}
        self._approval_timeout = 120

    def classify_action(self, tool_name: str, params: dict[str, Any]) -> RiskLevel:
        """Classify a tool action's risk level."""
        if tool_name in _HIGH_RISK_TOOLS:
            return RiskLevel.HIGH

        if tool_name == "shell_run":
            command = (params.get("command", "") or "").strip().lower()
            if command.startswith(_WRITE_SHELL_PREFIXES):
                return RiskLevel.HIGH

        if tool_name in _MEDIUM_RISK_TOOLS:
            if tool_name == "browser_control":
                action = (params.get("action", "") or "").lower()
                if action in ("download", "save"):
                    return RiskLevel.MEDIUM
                return RiskLevel.LOW
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def is_high_risk(self, tool_name: str) -> bool:
        return tool_name in _HIGH_RISK_TOOLS

    def request_approval(self, step_id: str, goal_text: str,
                          tool_name: str, params: dict[str, Any],
                          risk_level: RiskLevel,
                          description: str = "") -> ApprovalRequest:
        request_id = f"apr_{int(time.time())}_{step_id}"
        req = ApprovalRequest(
            request_id=request_id,
            step_id=step_id,
            goal_text=goal_text,
            tool_name=tool_name,
            params=dict(params),
            risk_level=risk_level,
            description=description or f"{tool_name}: {params}",
        )
        self._pending_requests[request_id] = req
        return req

    def respond_to_approval(self, request_id: str, approved: bool) -> bool:
        req = self._pending_requests.get(request_id)
        if req is None or req.status != ApprovalStatus.PENDING:
            return False

        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
        req.responded_at = time.time()

        if approved:
            self._pending_requests.pop(request_id, None)
        return True

    def get_pending_request(self, request_id: str) -> ApprovalRequest | None:
        return self._pending_requests.get(request_id)

    def get_all_pending(self) -> list[ApprovalRequest]:
        return [
            req for req in self._pending_requests.values()
            if req.status == ApprovalStatus.PENDING
        ]

    def has_pending(self) -> bool:
        return any(
            req.status == ApprovalStatus.PENDING
            for req in self._pending_requests.values()
        )

    def expire_old_requests(self, max_age: float = 120.0):
        now = time.time()
        to_expire: list[str] = []
        for rid, req in self._pending_requests.items():
            if req.status == ApprovalStatus.PENDING and (now - req.created_at) > max_age:
                req.status = ApprovalStatus.EXPIRED
                to_expire.append(rid)
        for rid in to_expire:
            self._pending_requests.pop(rid, None)

    def get_request_details(self, request_id: str) -> str:
        req = self._pending_requests.get(request_id)
        if req is None:
            return "Onay talebi bulunamadi."
        return (
            f"[ONAY GEREKIYOR] Seviye: {req.risk_level.value}\n"
            f"Arac: {req.tool_name}\n"
            f"Parametreler: {req.params}\n"
            f"Hedef: {req.goal_text}\n"
            f"Adim: {req.step_id}\n"
            f"Aciklama: {req.description}"
        )
