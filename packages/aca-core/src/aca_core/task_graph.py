"""
Task Graph — DAG data structure for ACA plans
Adler ASİ tarafından yapılmıştır
"""
from __future__ import annotations

import enum
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any


class ActionType(str, enum.Enum):
    """Types of actions an ACA step can perform."""
    TOOL = "tool"
    SHELL = "shell"
    INPUT = "input"
    OBSERVE = "observe"
    WAIT = "wait"


class Status(str, enum.Enum):
    """Execution status of a task node."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class TaskNode:
    """A single step in a task graph plan."""
    step_id: str
    description: str
    action_type: ActionType
    tool_name: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: Status = Status.PENDING
    retry_count: int = 0
    max_retries: int = 2
    confidence: float = 0.0
    observation_before: dict[str, Any] | None = None
    observation_after: dict[str, Any] | None = None
    result: str = ""
    reflection: str = ""
    created_at: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["action_type"] = self.action_type.value
        d["status"] = self.status.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskNode:
        data = dict(data)
        data["action_type"] = ActionType(data["action_type"])
        data["status"] = Status(data["status"])
        return cls(**data)


class TaskGraph:
    """Directed Acyclic Graph of TaskNodes representing a plan."""

    def __init__(self, graph_id: str = "", goal_id: str = ""):
        self.graph_id: str = graph_id or f"g_{int(time.time())}"
        self.goal_id: str = goal_id
        self.nodes: dict[str, TaskNode] = {}
        self.edges: list[tuple[str, str]] = []

    def add_node(self, node: TaskNode) -> None:
        self.nodes[node.step_id] = node

    def add_edge(self, from_step: str, to_step: str) -> None:
        if from_step not in self.nodes or to_step not in self.nodes:
            raise ValueError(f"Cannot add edge: {from_step} or {to_step} not in graph")
        self.edges.append((from_step, to_step))

    def get_execution_order(self) -> list[TaskNode]:
        in_degree: dict[str, int] = {sid: 0 for sid in self.nodes}
        adjacency: dict[str, list[str]] = {sid: [] for sid in self.nodes}

        for from_step, to_step in self.edges:
            if to_step in in_degree:
                in_degree[to_step] += 1
            if from_step in adjacency:
                adjacency[from_step].append(to_step)

        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        ordered: list[TaskNode] = []

        while queue:
            sid = queue.pop(0)
            ordered.append(self.nodes[sid])
            for neighbor in adjacency.get(sid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered) != len(self.nodes):
            raise ValueError(f"Cycle detected in task graph ({len(ordered)}/{len(self.nodes)} nodes)")

        return ordered

    def has_cycle(self) -> bool:
        try:
            self.get_execution_order()
            return False
        except ValueError:
            return True

    def get_node(self, step_id: str) -> TaskNode | None:
        return self.nodes.get(step_id)

    def get_roots(self) -> list[TaskNode]:
        has_incoming = {to for _, to in self.edges}
        return [n for sid, n in self.nodes.items() if sid not in has_incoming]

    def get_leaves(self) -> list[TaskNode]:
        has_outgoing = {fr for fr, _ in self.edges}
        return [n for sid, n in self.nodes.items() if sid not in has_outgoing]

    def remaining_nodes(self) -> list[TaskNode]:
        return [n for n in self.nodes.values() if n.status in (Status.PENDING, Status.IN_PROGRESS)]

    def failed_nodes(self) -> list[TaskNode]:
        return [n for n in self.nodes.values() if n.status == Status.FAILED]

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "goal_id": self.goal_id,
            "nodes": {sid: node.to_dict() for sid, node in self.nodes.items()},
            "edges": list(self.edges),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraph:
        g = cls(graph_id=data.get("graph_id", ""), goal_id=data.get("goal_id", ""))
        for sid, node_data in data.get("nodes", {}).items():
            g.nodes[sid] = TaskNode.from_dict(node_data)
        g.edges = [(a, b) for a, b in data.get("edges", [])]
        return g

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> TaskGraph:
        return cls.from_dict(json.loads(text))
