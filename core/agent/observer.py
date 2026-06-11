"""FR-001: Desktop state observation via analyze_screen()"""
from __future__ import annotations

import platform
import subprocess
import time
import traceback
from typing import Any, Callable


class Observer:
    """Captures desktop state using actions/screen_vision.analyze_screen()."""

    def __init__(self, capture_screen: Callable[[], str] | None = None):
        self._capture_screen = capture_screen

    def capture(self) -> dict[str, Any]:
        screen = self._capture_screen() if self._capture_screen else "(no screen)"
        return {
            "timestamp": time.time(),
            "screen_text": screen,
            "active_window_title": self._active_window(),
            "running_processes": self._processes(),
        }

    def _active_window(self) -> str:
        s = platform.system()
        try:
            if s == "Windows":
                r = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-Process | Where-Object MainWindowTitle -ne '' | Select-Object -First 1 -ExpandProperty MainWindowTitle)"],
                    capture_output=True, text=True, timeout=5)
                return r.stdout.strip() or "?"
            elif s == "Linux":
                r = subprocess.run(["xdotool", "getactivewindow", "getwindowname"],
                                   capture_output=True, text=True, timeout=3)
                return r.stdout.strip() or "?"
            elif s == "Darwin":
                r = subprocess.run(
                    ["osascript", "-e",
                     'tell app "System Events" to get name of first application process whose frontmost is true'],
                    capture_output=True, text=True, timeout=5)
                return r.stdout.strip() or "?"
        except Exception:
            traceback.print_exc()
        return "?"

    def _processes(self) -> list[dict[str, Any]]:
        try:
            import psutil
            seen: set[str] = set()
            out = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    n = (info["name"] or "").lower()
                    if n not in seen:
                        seen.add(n)
                        out.append({"pid": info["pid"], "name": info["name"],
                                    "cpu": info["cpu_percent"] or 0.0,
                                    "memory": info["memory_percent"] or 0.0})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            out.sort(key=lambda x: x["cpu"], reverse=True)
            return out[:15]
        except ImportError:
            return []
        except Exception:
            traceback.print_exc()
            return []
