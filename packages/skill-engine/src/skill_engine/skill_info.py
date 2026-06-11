from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


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
