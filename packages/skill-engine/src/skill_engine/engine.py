from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from skill_engine.exceptions import SkillLoadError
from skill_engine.loader import load_skill_from_path
from skill_engine.skill_info import SkillInfo
from skill_engine.watcher import Watcher


class SkillEngine:
    """Skill loading, hot-reload, routing, and lifecycle manager.

    Usage::

        engine = SkillEngine(skills_dir="skills/")
        engine.route("merhaba")         # -> "Merhaba!" or None
        engine.list_skills()            # -> ["greeter-v1", ...]
        engine.get_skill_info("greeter-v1")  # -> SkillInfo
    """

    # Class-level set to support _reset_instance() for testing
    _instances: list[SkillEngine] = []

    def __init__(
        self,
        skills_dir: str | Path = "skills",
        auto_reload: bool = False,
        reload_interval: float = 3.0,
    ):
        self._skills_dir = Path(skills_dir)
        self._auto_reload = auto_reload
        self._reload_interval = reload_interval

        # Internal state
        self._skills: dict[str, SkillInfo] = {}
        self._routers: dict[str, Any] = {}
        self._folder_map: dict[str, str] = {}

        # Watcher
        self._watcher: Watcher | None = None

        # Register instance for testing
        SkillEngine._instances.append(self)

        # Initial load
        self._load_all()

        # Start watcher if requested
        if auto_reload:
            self._start_watcher()

    # ── Public API ──────────────────────────────────────────────────

    def route(self, user_text: str) -> str | None:
        """Route *user_text* through all active skills.

        Returns the first non-None result, or None if no skill matched.
        """
        for skill_id, info in list(self._skills.items()):
            if not info.is_active or info.route_func is None:
                continue
            try:
                result = info.route_func(user_text)
                if result is not None:
                    return result
            except Exception as e:
                info.error_count += 1
                info.last_error = str(e)
                self._call_on_error(info, e)
        return None

    def list_skills(self) -> list[str]:
        """Return IDs of all active (loaded and enabled) skills."""
        return [sid for sid, info in self._skills.items() if info.is_active]

    def get_skill_info(self, skill_id: str) -> SkillInfo | None:
        """Return SkillInfo for *skill_id*, or None if unknown."""
        return self._skills.get(skill_id)

    def get_stats(self) -> dict[str, Any]:
        """Return summary statistics."""
        active = sum(1 for info in self._skills.values() if info.is_active)
        failed = sum(1 for info in self._skills.values() if not info.is_active)
        total_errors = sum(info.error_count for info in self._skills.values())
        return {
            "total": len(self._skills),
            "active": active,
            "failed": failed,
            "errors": total_errors,
        }

    def disable_skill(self, skill_id: str) -> bool:
        """Remove *skill_id* from routing, mark inactive.

        Returns True on success, False if skill_id not found.
        """
        info = self._skills.get(skill_id)
        if info is None:
            return False
        info.is_active = False
        info.route_func = None
        self._routers.pop(skill_id, None)
        self._call_on_unload(info)
        return True

    def enable_skill(self, skill_id: str) -> bool:
        """Re-enable a disabled skill by reloading it from disk.

        Returns True on success, False if not found or reload fails.
        """
        info = self._skills.get(skill_id)
        if info is None:
            return False
        folder_path = self._skills_dir / info.folder
        try:
            new_info = load_skill_from_path(folder_path, info.folder)
            new_info.is_active = True
            new_info.load_count = info.load_count + 1
            self._skills[skill_id] = new_info
            self._routers[skill_id] = new_info.route_func
            self._folder_map[info.folder] = skill_id
            self._call_on_load(new_info)
            return True
        except SkillLoadError:
            return False

    def reload_skill(self, skill_id: str) -> bool:
        """Reload a single skill from disk.

        Returns True on success, False if not found.
        """
        info = self._skills.get(skill_id)
        if info is None:
            return False
        folder_path = self._skills_dir / info.folder
        return self._reload_from_folder(folder_path, info.folder, skill_id)

    def reload_all(self):
        """Reload all currently loaded skills from disk."""
        for skill_id in list(self._skills.keys()):
            self.reload_skill(skill_id)

    def stop_watcher(self):
        """Stop the hot-reload watcher thread if running."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    # ── Internal: loading ──────────────────────────────────────────

    def _load_all(self):
        """Load all skill folders under *skills_dir*."""
        if not self._skills_dir.exists():
            return
        for child in sorted(self._skills_dir.iterdir()):
            if child.is_dir():
                try:
                    self._load_folder(child)
                except SkillLoadError:
                    pass  # Individual skill failures don't crash the engine

    def _load_folder(self, folder_path: Path) -> str | None:
        """Load a single skill folder.

        Returns the skill_id on success, None on failure.
        """
        folder_name = folder_path.name
        # If folder was previously loaded under a different ID, disable it first
        if folder_name in self._folder_map:
            old_id = self._folder_map[folder_name]
            if old_id in self._skills:
                self._skills[old_id].is_active = False

        try:
            info = load_skill_from_path(folder_path, folder_name)
        except SkillLoadError:
            # Register as failed skill so it appears in stats
            self._register_failed(folder_name, folder_path)
            return None

        # Store
        self._skills[info.skill_id] = info
        self._routers[info.skill_id] = info.route_func
        self._folder_map[folder_name] = info.skill_id
        self._call_on_load(info)
        return info.skill_id

    def _reload_from_folder(self, folder_path: Path, folder_name: str, skill_id: str) -> bool:
        """Reload a skill, preserving its skill_id."""
        try:
            new_info = load_skill_from_path(folder_path, folder_name)
        except SkillLoadError:
            return False

        old_info = self._skills.get(skill_id)
        new_info.load_count = (old_info.load_count + 1) if old_info else 1
        new_info.is_active = True

        # If SKILL_ID changed in the module, re-register
        if new_info.skill_id != skill_id:
            self._folder_map.pop(folder_name, None)
            self._skills.pop(skill_id, None)
            self._routers.pop(skill_id, None)

        self._skills[new_info.skill_id] = new_info
        self._routers[new_info.skill_id] = new_info.route_func
        self._folder_map[folder_name] = new_info.skill_id
        self._call_on_load(new_info)
        return True

    def _register_failed(self, folder_name: str, folder_path: Path):
        """Register a placeholder for a skill that failed to load."""
        info = SkillInfo(
            skill_id=f"failed-{folder_name}",
            name=folder_name,
            version="0.0.0",
            folder=folder_name,
            module_path=folder_path,
            last_error="Load failed",
            is_active=False,
        )
        self._skills[info.skill_id] = info
        self._folder_map[folder_name] = info.skill_id

    # ── Internal: lifecycle hooks ──────────────────────────────────

    def _call_on_load(self, info: SkillInfo):
        if info.on_load_func is not None:
            try:
                info.on_load_func(info.skill_id)
            except Exception:
                traceback.print_exc()

    def _call_on_unload(self, info: SkillInfo):
        if info.on_unload_func is not None:
            try:
                info.on_unload_func(info.skill_id)
            except Exception:
                traceback.print_exc()

    def _call_on_error(self, info: SkillInfo, exc: Exception):
        if info.on_error_func is not None:
            try:
                info.on_error_func(info.skill_id, exc)
            except Exception:
                traceback.print_exc()

    # ── Internal: watcher ──────────────────────────────────────────

    def _start_watcher(self):
        def _on_change(event: str, folder: str):
            folder_path = self._skills_dir / folder
            if event == "loaded":
                self._load_folder(folder_path)
            elif event == "reloaded":
                skill_id = self._folder_map.get(folder)
                if skill_id:
                    self._reload_from_folder(folder_path, folder, skill_id)
                else:
                    self._load_folder(folder_path)
            elif event == "disabled":
                skill_id = self._folder_map.get(folder)
                if skill_id:
                    self.disable_skill(skill_id)
                    self._folder_map.pop(folder, None)

        self._watcher = Watcher(
            skills_dir=self._skills_dir,
            interval=self._reload_interval,
            on_change=_on_change,
        )
        self._watcher.start()

    # ── Testing support ────────────────────────────────────────────

    @classmethod
    def _reset_instance(cls):
        """Stop and clear all tracked instances. Used in tests."""
        for eng in cls._instances:
            eng.stop_watcher()
        cls._instances.clear()
