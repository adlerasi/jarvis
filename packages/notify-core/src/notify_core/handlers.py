"""
Notification handlers: Voice, Log.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional


class VoiceHandler:
    """Handler that speaks notifications via an injected TTS callable.

    Args:
        speak: Optional callable accepting a single string.  When None
            the handler silently skips.
    """

    def __init__(self, speak: Optional[Callable[[str], None]] = None) -> None:
        self._speak = speak

    def __call__(self, event: dict[str, Any]) -> None:
        if self._speak is None:
            return
        title = event.get("title", "")
        message = event.get("message", "")
        text = f"{title}: {message}" if title else message
        self._speak(text)


class LogHandler:
    """Handler that writes notifications to a file or stdout.

    Args:
        file_path: Path to log file.  None writes to stdout.
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        self._file_path = file_path
        self._handle: Any = None  # keep open if file

    def __call__(self, event: dict[str, Any]) -> None:
        title = event.get("title", "")
        message = event.get("message", "")
        priority = event.get("priority", "normal")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{priority.upper()}] {title}: {message}\n"

        if self._file_path is not None:
            Path(self._file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._file_path, "a", encoding="utf-8") as f:
                f.write(line)
        else:
            sys.stdout.write(line)
            sys.stdout.flush()
