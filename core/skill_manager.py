"""
JARVIS Skill Manager v4 — local SkillEngine implementation.
"""
from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any, Callable, Optional

from core._skill_engine import SkillEngine, SkillInfo as _EngineSkillInfo

BASE_DIR = Path(__file__).resolve().parent.parent
SKILLS_DIR = BASE_DIR / "skills"


# ── Re-export SkillInfo with JARVIS-compatible API ──────────────────


class SkillInfo:
    """Wrapper around skill_engine's SkillInfo.

    Preserves JARVIS's public API surface (fields + to_dict).
    Delegates to the engine's SkillInfo internally.
    """

    def __init__(self, _engine_info: _EngineSkillInfo | None = None, **kwargs) -> None:
        if _engine_info is not None:
            self._info = _engine_info
        else:
            # For direct instantiation (tests use this)
            from datetime import datetime
            self._info = _EngineSkillInfo(
                skill_id=kwargs.get("skill_id", ""),
                name=kwargs.get("name", ""),
                version=kwargs.get("version", "0.0.0"),
                folder=kwargs.get("folder", ""),
                module_path=kwargs.get("module_path", Path()),
                md_path=kwargs.get("md_path"),
                triggers_path=kwargs.get("triggers_path"),
                route_func=kwargs.get("route_func"),
                loaded_at=kwargs.get("loaded_at", datetime.now()),
                last_modified=kwargs.get("last_modified", 0.0),
                load_count=kwargs.get("load_count", 0),
                error_count=kwargs.get("error_count", 0),
                last_error=kwargs.get("last_error"),
                is_active=kwargs.get("is_active", True),
            )

    @property
    def skill_id(self) -> str:
        return self._info.skill_id

    @skill_id.setter
    def skill_id(self, val: str) -> None:
        self._info.skill_id = val

    @property
    def name(self) -> str:
        return self._info.name

    @name.setter
    def name(self, val: str) -> None:
        self._info.name = val

    @property
    def version(self) -> str:
        return self._info.version

    @version.setter
    def version(self, val: str) -> None:
        self._info.version = val

    @property
    def folder(self) -> str:
        return self._info.folder

    @folder.setter
    def folder(self, val: str) -> None:
        self._info.folder = val

    @property
    def module_path(self) -> Path:
        return self._info.module_path

    @module_path.setter
    def module_path(self, val: Path) -> None:
        self._info.module_path = val

    @property
    def md_path(self) -> Path | None:
        return self._info.md_path

    @md_path.setter
    def md_path(self, val: Path | None) -> None:
        self._info.md_path = val

    @property
    def triggers_path(self) -> Path | None:
        return self._info.triggers_path

    @triggers_path.setter
    def triggers_path(self, val: Path | None) -> None:
        self._info.triggers_path = val

    @property
    def route_func(self) -> Callable[[str], str | None] | None:
        return self._info.route_func

    @route_func.setter
    def route_func(self, val: Callable[[str], str | None] | None) -> None:
        self._info.route_func = val

    @property
    def loaded_at(self) -> Any:
        return self._info.loaded_at

    @loaded_at.setter
    def loaded_at(self, val: Any) -> None:
        self._info.loaded_at = val

    @property
    def last_modified(self) -> float:
        return self._info.last_modified

    @last_modified.setter
    def last_modified(self, val: float) -> None:
        self._info.last_modified = val

    @property
    def load_count(self) -> int:
        return self._info.load_count

    @load_count.setter
    def load_count(self, val: int) -> None:
        self._info.load_count = val

    @property
    def error_count(self) -> int:
        return self._info.error_count

    @error_count.setter
    def error_count(self, val: int) -> None:
        self._info.error_count = val

    @property
    def last_error(self) -> str | None:
        return self._info.last_error

    @last_error.setter
    def last_error(self, val: str | None) -> None:
        self._info.last_error = val

    @property
    def is_active(self) -> bool:
        return self._info.is_active

    @is_active.setter
    def is_active(self, val: bool) -> None:
        self._info.is_active = val

    def to_dict(self) -> dict[str, Any]:
        return self._info.to_dict()


# ── SkillManager — SkillEngine wrapper ──────────────────────────────


class SkillManager:
    """Hot-reload destekli skill yöneticisi (skill-engine library)."""

    def __init__(self, auto_reload: bool = True, reload_interval: float = 3.0) -> None:
        self._callbacks: list[Callable[..., Any]] = []
        self._running = auto_reload  # for watcher test compatibility
        self._engine = SkillEngine(
            skills_dir=str(SKILLS_DIR),
            auto_reload=auto_reload,
            reload_interval=reload_interval,
        )

    # ── Public API ───────────────────────────────────────────────────

    def route(self, user_text: str) -> str | None:
        return self._engine.route(user_text)

    def list_skills(self) -> list[str]:
        return self._engine.list_skills()

    def get_skill_count(self) -> int:
        return len(self._engine.list_skills())

    def get_skill_info(self, skill_id: str) -> SkillInfo | None:
        info = self._engine.get_skill_info(skill_id)
        if info is None:
            return None
        return SkillInfo(_engine_info=info)

    def list_all_skills(self) -> list[dict[str, Any]]:
        return [info.to_dict() for info in self._engine._skills.values()]

    def get_stats(self) -> dict[str, Any]:
        s = self._engine.get_stats()
        return {
            "total_skills": s["total"],
            "active": s["active"],
            "failed": s["failed"],
            "total_errors": s["errors"],
            "auto_reload": self._engine._auto_reload,
            "reload_interval": self._engine._reload_interval,
        }

    def disable_skill(self, skill_id: str) -> bool:
        ok = self._engine.disable_skill(skill_id)
        if ok:
            self._notify_callbacks("disabled", skill_id)
        return ok

    def enable_skill(self, skill_id: str) -> bool:
        return self._engine.enable_skill(skill_id)

    def reload_skill(self, skill_id: str) -> bool:
        ok = self._engine.reload_skill(skill_id)
        if ok:
            self._notify_callbacks("reloaded", skill_id)
        else:
            self._notify_callbacks("reload_failed", skill_id)
        return ok

    def reload_all(self) -> None:
        self._engine.reload_all()

    def stop_watcher(self) -> None:
        self._running = False
        self._engine.stop_watcher()

    @property
    def _skills(self) -> dict[str, Any]:
        """Expose internal _skills dict for list_all_skills access."""
        return self._engine._skills

    # ── Callback Sistemi ─────────────────────────────────────────────

    def on_reload(self, callback: Callable[..., Any]) -> None:
        self._callbacks.append(callback)

    def _notify_callbacks(self, event: str, skill_id: str) -> None:
        for cb in self._callbacks:
            try:
                cb(event, skill_id)
            except Exception:
                traceback.print_exc()


# ── Singleton ──────────────────────────────────────────────────────
_skill_manager = None


def get_skill_manager(auto_reload: bool = True, reload_interval: float = 3.0) -> SkillManager:
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager(auto_reload=auto_reload, reload_interval=reload_interval)
    return _skill_manager


def reload_skill_manager() -> SkillManager:
    global _skill_manager
    if _skill_manager:
        _skill_manager.stop_watcher()
        _skill_manager = None
    return get_skill_manager()
