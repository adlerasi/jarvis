"""
aca-core — Autonomous Computer Agent standalone library
"""
from aca_core.task_graph import ActionType, Status, TaskGraph, TaskNode
from aca_core.observer import Observer
from aca_core.planner import Planner
from aca_core.executor import Executor
from aca_core.reflection import Reflection, ReflectionResult
from aca_core.approval_manager import (
    ApprovalManager, ApprovalRequest, ApprovalStatus, RiskLevel,
)
from aca_core.agent_memory import AgentMemory

__all__ = [
    "ActionType", "Status", "TaskGraph", "TaskNode",
    "Observer", "Planner", "Executor", "Reflection", "ReflectionResult",
    "ApprovalManager", "ApprovalRequest", "ApprovalStatus", "RiskLevel",
    "AgentMemory",
]
