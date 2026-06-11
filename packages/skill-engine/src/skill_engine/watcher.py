from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable


class Watcher:
    """Filesystem watcher that polls a skills directory for changes.

    Detects:
    - New skill directories appearing
    - Skill directories being removed
    - Skill files (or their SKILL.md / triggers.json) being modified

    Fires callbacks with (event_type: str, skill_id_or_folder: str).
    Event types: "loaded", "reloaded", "disabled", "reload_failed"
    """

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
        self._snapshot: dict[str, float] = {}  # folder_name -> last known mtime

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
        """Record current folder set and file mtimes."""
        snap: dict[str, float] = {}
        if self._skills_dir.exists():
            for child in self._skills_dir.iterdir():
                if child.is_dir():
                    mtime = self._folder_max_mtime(child)
                    snap[child.name] = mtime
        self._snapshot = snap

    @staticmethod
    def _folder_max_mtime(folder: Path) -> float:
        """Return the latest mtime among the skill files in *folder*."""
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
                pass  # Don't crash the watcher thread
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
            mtime = self._folder_max_mtime(child)
            current_snapshot[child.name] = mtime

        known = set(self._snapshot.keys())

        # New folders
        for folder in current_folders - known:
            if self._on_change:
                self._on_change("loaded", folder)

        # Removed folders
        for folder in known - current_folders:
            if self._on_change:
                self._on_change("disabled", folder)

        # Modified folders
        for folder in current_folders & known:
            if current_snapshot.get(folder, 0) > self._snapshot.get(folder, 0):
                if self._on_change:
                    self._on_change("reloaded", folder)

        self._snapshot = current_snapshot
