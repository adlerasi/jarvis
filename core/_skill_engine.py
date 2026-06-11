"""
Local SkillEngine — skill loading/routing/hot-reload, replaces skill-engine package.
"""
from __future__ import annotations

import importlib.util
import inspect
import sys
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


# ── Exceptions ──────────────────────────────────────────────────────────

class SkillEngineError(Exception):
    """Base exception for all skill-engine errors."""

class SkillLoadError(SkillEngineError):
    """Raised when a skill module cannot be loaded."""

class SkillNotFoundError(SkillEngineError):
    """Raised when a skill ID does not exist."""


# ── SkillInfo ───────────────────────────────────────────────────────────

@dataclass
class SkillInfo:
    skill_id: str
    name: str
    version: str
    folder: str
    module_path: Path
    md_path: Path | None = None
    triggers_path: Path | None = None
    route_func: Callable[[str], str | None] | None = None
    on_load_func: Callable[[str], None] | None = None
    on_unload_func: Callable[[str], None] | None = None
    on_error_func: Callable[[str, Exception], None] | None = None
    loaded_at: datetime = field(default_factory=datetime.now)
    last_modified: float = 0.0
    load_count: int = 0
    error_count: int = 0
    last_error: str | None = None
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "version": self.version,
            "folder": self.folder,
            "loaded_at": self.loaded_at.isoformat(),
            "last_modified": self.last_modified,
            "load_count": self.load_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "is_active": self.is_active,
        }


# ── Loader functions ────────────────────────────────────────────────────

def _infer_skill_id(folder_name: str, module: Any) -> str:
    return str(getattr(module, "SKILL_ID", None) or folder_name)

def _infer_skill_name(folder_name: str, module: Any) -> str:
    return str(getattr(module, "SKILL_NAME", None) or folder_name)

def _infer_skill_version(module: Any) -> str:
    return str(getattr(module, "SKILL_VERSION", "0.0.0"))

def _find_route_function(module: Any, folder_name: str) -> Any:
    expected = f"route_{folder_name}_request"
    func = getattr(module, expected, None)
    if func is not None:
        return func
    for attr_name in dir(module):
        if attr_name.startswith("route_") and attr_name.endswith("_request"):
            return getattr(module, attr_name)
    return None

def _find_lifecycle_hooks(module: Any) -> dict[str, Any]:
    hooks: dict[str, Any] = {}
    for name in ("on_load", "on_unload", "on_error"):
        fn = getattr(module, name, None)
        if fn is not None and callable(fn):
            hooks[name] = fn
    return hooks

def _validate_route_signature(route_func: Any, folder_name: str) -> None:
    try:
        sig = inspect.signature(route_func)
        params = list(sig.parameters.values())
        if len(params) != 1:
            raise SkillLoadError(
                f"{folder_name}: route function must accept exactly 1 argument, got {len(params)}"
            )
        ret = sig.return_annotation
        if ret is not inspect.Parameter.empty:
            if isinstance(ret, str):
                ret_str = ret
            elif hasattr(ret, "__origin__"):
                ret_str = str(ret)
            else:
                ret_str = ret.__name__ if hasattr(ret, "__name__") else str(ret)
            allowed = ("str", "str | None", "Optional[str]", "Union[str, None]", "NoneType")
            if ret_str not in allowed:
                raise SkillLoadError(
                    f"{folder_name}: route function return must be str | None, got {ret}"
                )
    except SkillLoadError:
        raise
    except Exception as e:
        raise SkillLoadError(f"{folder_name}: cannot inspect route function: {e}") from e

def _load_skill_from_path(folder_path: Path, folder_name: str, force_reload: bool = False) -> SkillInfo:
    """Load a single skill from its folder path. Returns SkillInfo. Raises SkillLoadError."""
    skill_file = folder_path / f"{folder_name}_skill.py"
    if not skill_file.exists():
        py_files = list(folder_path.glob("*.py"))
        if not py_files:
            raise SkillLoadError(f"{folder_name}: no .py file found in {folder_path}")
        skill_file = py_files[0]

    module_name = f"_skill_import_{folder_name}"
    if module_name in sys.modules:
        del sys.modules[module_name]

    if not force_reload:
        resolved_file = skill_file.resolve()
        for existing_mod in list(sys.modules.values()):
            if getattr(existing_mod, "__file__", None) and Path(existing_mod.__file__).resolve() == resolved_file:
                module = existing_mod
                sys.modules[module_name] = module
                route_func = _find_route_function(module, folder_name)
                if route_func is None:
                    raise SkillLoadError(
                        f"{folder_name}: no route_{folder_name}_request function found in {skill_file.name}"
                    )
                _validate_route_signature(route_func, folder_name)
                skill_id = _infer_skill_id(folder_name, module)
                skill_name = _infer_skill_name(folder_name, module)
                skill_version = _infer_skill_version(module)
                hooks = _find_lifecycle_hooks(module)
                md_path = folder_path / "SKILL.md"
                triggers_path = folder_path / "triggers.json"
                return SkillInfo(
                    skill_id=skill_id, name=skill_name, version=skill_version,
                    folder=folder_name, module_path=skill_file,
                    md_path=md_path if md_path.exists() else None,
                    triggers_path=triggers_path if triggers_path.exists() else None,
                    route_func=route_func,
                    on_load_func=hooks.get("on_load"),
                    on_unload_func=hooks.get("on_unload"),
                    on_error_func=hooks.get("on_error"),
                    last_modified=skill_file.stat().st_mtime, load_count=1,
                )

    try:
        spec = importlib.util.spec_from_file_location(module_name, str(skill_file))
        if spec is None:
            raise SkillLoadError(f"{folder_name}: importlib returned no spec for {skill_file}")
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise SkillLoadError(f"{folder_name}: importlib returned no loader for {skill_file}")
        spec.loader.exec_module(module)
        sys.modules[module_name] = module
    except SyntaxError as e:
        raise SkillLoadError(f"{folder_name}: syntax error in {skill_file.name}: {e}") from e
    except Exception as e:
        raise SkillLoadError(f"{folder_name}: failed to load {skill_file.name}: {e}") from e

    route_func = _find_route_function(module, folder_name)
    if route_func is None:
        raise SkillLoadError(
            f"{folder_name}: no route_{folder_name}_request function found in {skill_file.name}"
        )
    _validate_route_signature(route_func, folder_name)

    skill_id = _infer_skill_id(folder_name, module)
    skill_name = _infer_skill_name(folder_name, module)
    skill_version = _infer_skill_version(module)
    hooks = _find_lifecycle_hooks(module)

    md_path = folder_path / "SKILL.md"
    triggers_path = folder_path / "triggers.json"

    return SkillInfo(
        skill_id=skill_id,
        name=skill_name,
        version=skill_version,
        folder=folder_name,
        module_path=skill_file,
        md_path=md_path if md_path.exists() else None,
        triggers_path=triggers_path if triggers_path.exists() else None,
        route_func=route_func,
        on_load_func=hooks.get("on_load"),
        on_unload_func=hooks.get("on_unload"),
        on_error_func=hooks.get("on_error"),
        last_modified=skill_file.stat().st_mtime,
        load_count=1,
    )


# ── Watcher ─────────────────────────────────────────────────────────────

class _Watcher:
    """Filesystem watcher for skill hot-reload."""

    def __init__(
        self,
        skills_dir: str | Path,
        interval: float = 3.0,
        on_change: Callable[[str, str], None] | None = None,
    ):
        self._skills_dir = Path(skills_dir)
        self._interval = interval
        self._on_change = on_change
        self._thread: threading.Thread | None = None
        self._running = False
        self._snapshot: dict[str, float] = {}

    def start(self):
        if self._running:
            return
        self._running = True
        self._take_snapshot()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SkillWatcher")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3.0)
            self._thread = None

    def _take_snapshot(self):
        snap: dict[str, float] = {}
        if self._skills_dir.exists():
            for child in self._skills_dir.iterdir():
                if child.is_dir():
                    snap[child.name] = self._folder_max_mtime(child)
        self._snapshot = snap

    @staticmethod
    def _folder_max_mtime(folder: Path) -> float:
        latest = 0.0
        for pattern in ("*.py", "SKILL.md", "triggers.json"):
            for f in folder.glob(pattern):
                try:
                    mtime = f.stat().st_mtime
                    if mtime > latest:
                        latest = mtime
                except OSError:
                    pass
        return latest

    def _loop(self):
        while self._running:
            try:
                self._check()
            except Exception:
                import traceback
                traceback.print_exc()
            time.sleep(self._interval)

    def _check(self):
        if not self._skills_dir.exists():
            return
        current_folders: set[str] = set()
        current_snapshot: dict[str, float] = {}
        for child in self._skills_dir.iterdir():
            if not child.is_dir():
                continue
            current_folders.add(child.name)
            current_snapshot[child.name] = self._folder_max_mtime(child)
        known = set(self._snapshot.keys())
        for folder in current_folders - known:
            if self._on_change:
                self._on_change("loaded", folder)
        for folder in known - current_folders:
            if self._on_change:
                self._on_change("disabled", folder)
        for folder in current_folders & known:
            if current_snapshot.get(folder, 0) > self._snapshot.get(folder, 0):
                if self._on_change:
                    self._on_change("reloaded", folder)
        self._snapshot = current_snapshot


# ── SkillEngine ─────────────────────────────────────────────────────────

class SkillEngine:
    """Skill loading, hot-reload, routing, and lifecycle manager."""

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
        self._skills: dict[str, SkillInfo] = {}
        self._routers: dict[str, Any] = {}
        self._folder_map: dict[str, str] = {}
        self._watcher: _Watcher | None = None
        self._lock = threading.Lock()

        SkillEngine._instances.append(self)
        self._load_all()
        if auto_reload:
            self._start_watcher()

    def route(self, user_text: str) -> str | None:
        with self._lock:
            snapshot = dict(self._skills)
        for skill_id, info in list(snapshot.items()):
            if not info.is_active or info.route_func is None:
                continue
            try:
                result = info.route_func(user_text)
                if result is not None:
                    return result
            except Exception as e:
                with self._lock:
                    fresh = self._skills.get(skill_id)
                    if fresh is not None:
                        fresh.error_count += 1
                        fresh.last_error = str(e)
                self._call_on_error(info, e)
        return None

    def list_skills(self) -> list[str]:
        with self._lock:
            return [sid for sid, info in self._skills.items() if info.is_active]

    def get_skill_info(self, skill_id: str) -> SkillInfo | None:
        with self._lock:
            return self._skills.get(skill_id)

    def get_stats(self) -> dict[str, Any]:
        with self._lock:
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
        with self._lock:
            info = self._skills.get(skill_id)
            if info is None:
                return False
            info.is_active = False
            info.route_func = None
            self._routers.pop(skill_id, None)
        self._call_on_unload(info)
        return True

    def enable_skill(self, skill_id: str) -> bool:
        with self._lock:
            info = self._skills.get(skill_id)
            if info is None:
                return False
            folder_path = self._skills_dir / info.folder
        try:
            new_info = _load_skill_from_path(folder_path, info.folder, force_reload=True)
        except SkillLoadError:
            return False
        new_info.is_active = True
        with self._lock:
            old = self._skills.get(skill_id)
            new_info.load_count = (old.load_count + 1) if old else 1
            self._skills[skill_id] = new_info
            self._routers[skill_id] = new_info.route_func
            self._folder_map[info.folder] = skill_id
        self._call_on_load(new_info)
        return True

    def reload_skill(self, skill_id: str) -> bool:
        with self._lock:
            info = self._skills.get(skill_id)
            if info is None:
                return False
            folder_path = self._skills_dir / info.folder
            folder_name = info.folder
        return self._reload_from_folder(folder_path, folder_name, skill_id)

    def reload_all(self):
        with self._lock:
            keys = list(self._skills.keys())
        for skill_id in keys:
            self.reload_skill(skill_id)

    def stop_watcher(self):
        if self._watcher:
            self._watcher.stop()
            self._watcher = None

    def _load_all(self):
        if not self._skills_dir.exists():
            return
        for child in sorted(self._skills_dir.iterdir()):
            if child.is_dir():
                try:
                    self._load_folder(child)
                except SkillLoadError:
                    pass

    def _load_folder(self, folder_path: Path) -> str | None:
        folder_name = folder_path.name
        with self._lock:
            old_id = self._folder_map.get(folder_name)
            if old_id and old_id in self._skills:
                self._skills[old_id].is_active = False
        try:
            info = _load_skill_from_path(folder_path, folder_name)
        except SkillLoadError:
            self._register_failed(folder_name, folder_path)
            return None
        with self._lock:
            self._skills[info.skill_id] = info
            self._routers[info.skill_id] = info.route_func
            self._folder_map[folder_name] = info.skill_id
        self._call_on_load(info)
        return info.skill_id

    def _reload_from_folder(
        self, folder_path: Path, folder_name: str, skill_id: str,
    ) -> bool:
        try:
            new_info = _load_skill_from_path(folder_path, folder_name, force_reload=True)
        except SkillLoadError:
            return False
        new_info.is_active = True
        with self._lock:
            old_info = self._skills.get(skill_id)
            new_info.load_count = (old_info.load_count + 1) if old_info else 1
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
        info = SkillInfo(
            skill_id=f"failed-{folder_name}",
            name=folder_name,
            version="0.0.0",
            folder=folder_name,
            module_path=folder_path,
            last_error="Load failed",
            is_active=False,
        )
        with self._lock:
            self._skills[info.skill_id] = info
            self._folder_map[folder_name] = info.skill_id

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

    def _start_watcher(self):
        def _on_change(event: str, folder: str):
            folder_path = self._skills_dir / folder
            if event == "loaded":
                self._load_folder(folder_path)
            elif event == "reloaded":
                with self._lock:
                    skill_id = self._folder_map.get(folder)
                if skill_id:
                    self._reload_from_folder(folder_path, folder, skill_id)
                else:
                    self._load_folder(folder_path)
            elif event == "disabled":
                with self._lock:
                    skill_id = self._folder_map.get(folder)
                if skill_id:
                    self.disable_skill(skill_id)
                    with self._lock:
                        self._folder_map.pop(folder, None)
        self._watcher = _Watcher(
            skills_dir=self._skills_dir,
            interval=self._reload_interval,
            on_change=_on_change,
        )
        self._watcher.start()

    @classmethod
    def _reset_instance(cls):
        for eng in cls._instances:
            eng.stop_watcher()
        cls._instances.clear()
