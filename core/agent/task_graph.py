"""Task graph data model — ActionType, Status, TaskNode, TaskGraph."""
from __future__ import annotations

import json
import time
from collections import deque
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    TOOL = "tool"
    SHELL = "shell"
    INPUT = "input"
    OBSERVE = "observe"
    WAIT = "wait"
    APPROVAL_WAIT = "approval_wait"
    LLM_REASON = "llm_reason"


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskNode:
    """A single atomic step in a task graph."""

    def __init__(
        self,
        step_id: str,
        description: str,
        action_type: ActionType | str = ActionType.TOOL,
        tool_name: str = "",
        params: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        status: Status | str = Status.PENDING,
        max_retries: int = 2,
        retry_count: int = 0,
        confidence: float | None = None,
        observation_before: str = "",
        observation_after: str = "",
        result: str = "",
        reflection: str = "",
        started_at: float | None = None,
        completed_at: float | None = None,
    ):
        self.step_id = step_id
        self.description = description
        self.action_type = ActionType(action_type) if isinstance(action_type, str) else action_type
        self.tool_name = tool_name
        self.params = params or {}
        self.dependencies = dependencies or []
        self.status = Status(status) if isinstance(status, str) else status
        self.max_retries = max_retries
        self.retry_count = retry_count
        self.confidence = confidence
        self.observation_before = observation_before
        self.observation_after = observation_after
        self.result = result
        self.reflection = reflection
        self.started_at = started_at
        self.completed_at = completed_at

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step_id": self.step_id,
            "description": self.description,
            "action_type": self.action_type.value,
            "tool_name": self.tool_name,
            "params": dict(self.params),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "confidence": self.confidence,
            "observation_before": self.observation_before,
            "observation_after": self.observation_after,
            "result": self.result,
            "reflection": self.reflection,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }
        return {k: v for k, v in d.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskNode:
        return cls(**{k: v for k, v in data.items() if v is not None})

    def is_terminal(self) -> bool:
        return self.status in (Status.SUCCESS, Status.FAILED, Status.SKIPPED, Status.CANCELLED)


class TaskGraph:
    """Directed acyclic graph of steps."""

    def __init__(
        self,
        graph_id: str = "",
        goal_id: str = "",
        nodes: dict[str, TaskNode] | None = None,
        edges: list[tuple[str, str]] | None = None,
    ):
        self.graph_id = graph_id or f"graph_{int(time.time())}"
        self.goal_id = goal_id
        self.nodes: dict[str, TaskNode] = nodes or {}
        self.edges: list[tuple[str, str]] = edges or []
        self.created_at: float = time.time()
        self.version: int = 1

    def add_node(self, node: TaskNode):
        self.nodes[node.step_id] = node

    def add_edge(self, from_id: str, to_id: str):
        if from_id in self.nodes and to_id in self.nodes:
            if (from_id, to_id) not in self.edges:
                self.edges.append((from_id, to_id))

    def has_cycle(self) -> bool:
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)
            for f, t in self.edges:
                if f == node_id:
                    if t not in visited:
                        if _dfs(t):
                            return True
                    elif t in rec_stack:
                        return True
            rec_stack.discard(node_id)
            return False

        for nid in self.nodes:
            if nid not in visited:
                if _dfs(nid):
                    return True
        return False

    def get_execution_order(self) -> list[TaskNode]:
        """Return nodes in topological order (Kahn's algorithm)."""
        in_degree: dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: dict[str, list[str]] = {nid: [] for nid in self.nodes}
        for f, t in self.edges:
            if f in adj and t in in_degree:
                adj[f].append(t)
                in_degree[t] = in_degree.get(t, 0) + 1

        queue: deque[str] = deque()
        for nid, deg in in_degree.items():
            if deg == 0:
                queue.append(nid)

        result: list[TaskNode] = []
        while queue:
            nid = queue.popleft()
            result.append(self.nodes[nid])
            for neighbor in adj.get(nid, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        remaining = [n for n in self.nodes if n not in {r.step_id for r in result}]
        for nid in remaining:
            result.append(self.nodes[nid])
        return result

    def failed_nodes(self) -> list[TaskNode]:
        return [n for n in self.nodes.values() if n.status == Status.FAILED]

    def remaining_nodes(self) -> list[TaskNode]:
        return [n for n in self.nodes.values() if not n.is_terminal()]

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "goal_id": self.goal_id,
            "nodes": {sid: node.to_dict() for sid, node in self.nodes.items()},
            "edges": [(f, t) for f, t in self.edges],
            "created_at": self.created_at,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskGraph:
        g = cls(
            graph_id=data.get("graph_id", ""),
            goal_id=data.get("goal_id", ""),
            edges=[(e[0], e[1]) for e in data.get("edges", [])],
        )
        for sid, ndata in data.get("nodes", {}).items():
            g.nodes[sid] = TaskNode.from_dict(ndata)
        g.created_at = data.get("created_at", time.time())
        g.version = data.get("version", 1)
        return g

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> TaskGraph:
        return cls.from_dict(json.loads(text))
