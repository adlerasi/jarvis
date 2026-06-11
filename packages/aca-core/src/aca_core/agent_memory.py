"""
Agent Memory — Persistence for goals, sessions, and workflow templates
Adler ASİ tarafından yapılmıştır

Standalone library version: storage paths are configurable via constructor.
"""
from __future__ import annotations

import json
import os
import time
import traceback
import unicodedata
from pathlib import Path
from typing import Any


class AgentMemory:
    """Persistent storage for agent goals, sessions, and workflow templates.

    Storage paths are configurable via ``base_path`` (default: current dir +
    ``memory/agent/``).  Use an absolute path when embedding in an application.
    """

    def __init__(self, base_path: str | Path | None = None):
        self._base = Path(base_path).resolve() if base_path else Path.cwd() / "memory" / "agent"
        self._goals_dir = self._base / "goals"
        self._sessions_dir = self._base / "sessions"
        self._templates_dir = self._base / "templates"
        self._index_file = self._base / "index.json"
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in (self._goals_dir, self._sessions_dir, self._templates_dir):
            d.mkdir(parents=True, exist_ok=True)
        if not self._index_file.exists():
            self._index_file.write_text("{}", encoding="utf-8")

    def _read_index(self) -> dict[str, Any]:
        try:
            if self._index_file.exists():
                return json.loads(self._index_file.read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
        return {}

    def _write_index(self, data: dict[str, Any]):
        try:
            self._index_file.parent.mkdir(parents=True, exist_ok=True)
            self._index_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            traceback.print_exc()

    def save_goal(self, goal_id: str, goal_data: dict[str, Any]) -> bool:
        try:
            path = self._goals_dir / f"{goal_id}.json"
            path.write_text(
                json.dumps(goal_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            index = self._read_index()
            if "goals" not in index:
                index["goals"] = {}
            index["goals"][goal_id] = {
                "text": goal_data.get("text", ""),
                "status": goal_data.get("status", "pending"),
                "updated_at": time.time(),
            }
            self._write_index(index)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def load_goal(self, goal_id: str) -> dict[str, Any] | None:
        try:
            path = self._goals_dir / f"{goal_id}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
        return None

    def list_goals(self, limit: int = 10) -> list[dict[str, Any]]:
        index = self._read_index()
        goals = index.get("goals", {})
        sorted_goals = sorted(
            goals.items(),
            key=lambda x: x[1].get("updated_at", 0),
            reverse=True,
        )
        result = []
        for gid, gdata in sorted_goals[:limit]:
            result.append({"goal_id": gid, **gdata})
        return result

    def save_session(self, session_id: str, session_data: dict[str, Any]) -> bool:
        try:
            path = self._sessions_dir / f"{session_id}.json"
            path.write_text(
                json.dumps(session_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            index = self._read_index()
            if "sessions" not in index:
                index["sessions"] = {}
            index["sessions"][session_id] = {
                "goal_id": session_data.get("goal_id", ""),
                "status": session_data.get("status", ""),
                "updated_at": time.time(),
            }
            self._write_index(index)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def load_session(self, session_id: str) -> dict[str, Any] | None:
        try:
            path = self._sessions_dir / f"{session_id}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
        return None

    def save_template(self, template_id: str, template_data: dict[str, Any]) -> bool:
        try:
            path = self._templates_dir / f"{template_id}.json"
            path.write_text(
                json.dumps(template_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            index = self._read_index()
            if "templates" not in index:
                index["templates"] = {}
            index["templates"][template_id] = {
                "intent": template_data.get("intent", ""),
                "keywords": template_data.get("keywords", []),
                "step_count": len(template_data.get("steps", [])),
                "updated_at": time.time(),
            }
            self._write_index(index)
            return True
        except Exception:
            traceback.print_exc()
            return False

    def load_template(self, template_id: str) -> dict[str, Any] | None:
        try:
            path = self._templates_dir / f"{template_id}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            traceback.print_exc()
        return None

    def find_templates(self, intent_text: str) -> list[dict[str, Any]]:
        normalized = self._normalize_goal_text(intent_text)
        tokens = set(normalized.split())

        index = self._read_index()
        templates_index = index.get("templates", {})
        scored: list[tuple[float, str]] = []

        for tid, tmeta in templates_index.items():
            keywords = set(tmeta.get("keywords", []))
            if not keywords:
                continue
            overlap = len(tokens & keywords)
            score = overlap / max(len(keywords), 1)
            if score > 0:
                scored.append((score, tid))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, tid in scored[:5]:
            tpl = self.load_template(tid)
            if tpl:
                tpl["template_id"] = tid
                tpl["match_score"] = score
                results.append(tpl)
        return results

    def save_current_goal(self, goal_id: str | None):
        try:
            index = self._read_index()
            if goal_id is None:
                index.pop("current_goal", None)
            else:
                index["current_goal"] = goal_id
            self._write_index(index)
        except Exception:
            traceback.print_exc()

    def load_current_goal(self) -> str | None:
        try:
            index = self._read_index()
            return index.get("current_goal")
        except Exception:
            traceback.print_exc()
            return None

    @staticmethod
    def _normalize_goal_text(text: str) -> str:
        text = (text or "").strip().casefold()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.replace("ı", "i")

        stopwords = {
            "ve", "bir", "bu", "şu", "o", "ile", "için", "olarak",
            "olan", "gereken", "olan", "daha", "en", "çok", "az",
            "the", "a", "an", "is", "are", "was", "were", "to",
            "for", "with", "on", "at", "in", "of", "by", "from",
            "that", "this", "these", "those", "it", "its", "be",
        }
        words = [w for w in text.split() if w not in stopwords and len(w) > 1]
        return " ".join(words)

    @staticmethod
    def compute_similarity(a: str, b: str) -> float:
        norm_a = AgentMemory._normalize_goal_text(a)
        norm_b = AgentMemory._normalize_goal_text(b)

        tokens_a = set(norm_a.split())
        tokens_b = set(norm_b.split())

        if not tokens_a or not tokens_b:
            return 0.0

        overlap = len(tokens_a & tokens_b)
        total = len(tokens_a | tokens_b)
        return overlap / max(total, 1)
