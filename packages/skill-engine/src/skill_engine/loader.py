from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from typing import Any

from skill_engine.exceptions import SkillLoadError
from skill_engine.skill_info import SkillInfo


def infer_skill_id_from_folder(folder_name: str, module: Any) -> str:
    """Return SKILL_ID from module, falling back to folder_name."""
    return str(getattr(module, "SKILL_ID", None) or folder_name)


def infer_skill_name(folder_name: str, module: Any) -> str:
    """Return SKILL_NAME from module, falling back to folder_name."""
    return str(getattr(module, "SKILL_NAME", None) or folder_name)


def infer_skill_version(module: Any) -> str:
    """Return SKILL_VERSION from module, defaulting to 0.0.0."""
    return str(getattr(module, "SKILL_VERSION", "0.0.0"))


def find_route_function(module: Any, folder_name: str) -> Any:
    """Find route_{folder_name}_request or any route_*_request function."""
    # Preferred: route_{folder}_request
    expected = f"route_{folder_name}_request"
    func = getattr(module, expected, None)
    if func is not None:
        return func
    # Fallback: any function matching route_*_request
    for attr_name in dir(module):
        if attr_name.startswith("route_") and attr_name.endswith("_request"):
            return getattr(module, attr_name)
    return None


def find_lifecycle_hooks(module: Any) -> dict[str, Any]:
    """Return optional lifecycle hook references from the skill module."""
    hooks: dict[str, Any] = {}
    for name in ("on_load", "on_unload", "on_error"):
        fn = getattr(module, name, None)
        if fn is not None and callable(fn):
            hooks[name] = fn
    return hooks


def validate_route_signature(route_func: Any, folder_name: str) -> None:
    """Check route function accepts exactly (str) -> str | None."""
    try:
        sig = inspect.signature(route_func)
        params = list(sig.parameters.values())
        if len(params) != 1:
            raise SkillLoadError(
                f"{folder_name}: route function must accept exactly 1 argument (user_text), "
                f"got {len(params)}"
            )
        # Check return annotation if present
        ret = sig.return_annotation
        if ret is not inspect.Parameter.empty:
            # Support both runtime types and string annotations (from __future__ import annotations)
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


def load_skill_from_path(folder_path: Path, folder_name: str) -> SkillInfo:
    """Load a single skill from its folder path.

    Returns a populated SkillInfo on success.
    Raises SkillLoadError on failure.
    """
    skill_file = folder_path / f"{folder_name}_skill.py"
    if not skill_file.exists():
        # Try any .py file in the folder
        py_files = list(folder_path.glob("*.py"))
        if not py_files:
            raise SkillLoadError(f"{folder_name}: no .py file found in {folder_path}")
        skill_file = py_files[0]

    module_name = f"_skill_import_{folder_name}"

    # Clean old module if present (supports hot-reload)
    if module_name in sys.modules:
        del sys.modules[module_name]

    try:
        spec = importlib.util.spec_from_file_location(module_name, str(skill_file))
        if spec is None:
            raise SkillLoadError(f"{folder_name}: importlib returned no spec for {skill_file}")
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise SkillLoadError(f"{folder_name}: importlib returned no loader for {skill_file}")
        spec.loader.exec_module(module)
    except SyntaxError as e:
        raise SkillLoadError(f"{folder_name}: syntax error in {skill_file.name}: {e}") from e
    except Exception as e:
        raise SkillLoadError(f"{folder_name}: failed to load {skill_file.name}: {e}") from e

    # Validate route function
    route_func = find_route_function(module, folder_name)
    if route_func is None:
        raise SkillLoadError(
            f"{folder_name}: no route_{folder_name}_request function found in {skill_file.name}"
        )
    validate_route_signature(route_func, folder_name)

    # Extract metadata
    skill_id = infer_skill_id_from_folder(folder_name, module)
    skill_name = infer_skill_name(folder_name, module)
    skill_version = infer_skill_version(module)

    # Lifecycle hooks
    hooks = find_lifecycle_hooks(module)

    # Extra file paths for change detection
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
