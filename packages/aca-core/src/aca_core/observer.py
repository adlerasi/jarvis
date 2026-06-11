"""
Observer — Desktop state capture for ACA
Adler ASİ tarafından yapılmıştır

Standalone library version: screen capture is injected via ``capture_screen``
callable.  Process list and active window title are captured with psutil /
subprocess.
"""
from __future__ import annotations

import platform
import time
import traceback
from typing import Any, Callable


class Observer:
    """Captures desktop state: screen text, active window, running processes.

    ``capture_screen`` is an optional callable ``() → str`` that performs the
    actual screen/text capture.  When omitted the library falls back to a
    placeholder message so the class remains usable without GUI dependencies.
    """

    def __init__(self, capture_screen: Callable[[], str] | None = None):
        self._capture_screen = capture_screen
        self._last_capture: dict[str, Any] = {}

    def capture(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "timestamp": time.time(),
            "screen_text": self._do_capture_screen(),
            "active_window_title": self._capture_active_window_title(),
            "running_processes": self._capture_running_processes(),
            "recent_files": [],
        }
        self._last_capture = state
        return state

    def _do_capture_screen(self) -> str:
        if self._capture_screen is not None:
            try:
                return self._capture_screen()
            except Exception:
                traceback.print_exc()
                return "Ekran analizi basarisiz."
        return "aca-core: screen capture not configured."

    def _capture_active_window_title(self) -> str:
        system = platform.system()
        try:
            if system == "Windows":
                return self._active_window_windows()
            elif system == "Linux":
                return self._active_window_linux()
            elif system == "Darwin":
                return self._active_window_macos()
            else:
                return f"Bilinmeyen platform: {system}"
        except Exception:
            traceback.print_exc()
            return ""

    def _active_window_windows(self) -> str:
        try:
            import subprocess as sp
            result = sp.run(
                ["powershell", "-Command",
                 "(Get-Process | Where-Object { $_.MainWindowTitle -ne '' } | "
                 "Select-Object -First 1 -ExpandProperty MainWindowTitle)"],
                capture_output=True, text=True, timeout=5
            )
            title = result.stdout.strip()
            return title if title else "Bilinmeyen Pencere"
        except Exception:
            return ""

    def _active_window_linux(self) -> str:
        try:
            import subprocess as sp
            try:
                result = sp.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True, text=True, timeout=3
                )
                if result.returncode == 0:
                    return result.stdout.strip() or "Bilinmeyen Pencere"
            except FileNotFoundError:
                pass

            result = sp.run(
                ["wmctrl", "-a", ":ACTIVE:", "-l"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(None, 3)
                    return parts[-1] if len(parts) >= 4 else "Bilinmeyen Pencere"
            return "Bilinmeyen Pencere"
        except Exception:
            return ""

    def _active_window_macos(self) -> str:
        try:
            import subprocess as sp
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = sp.run(
                ["osascript", "-e", script],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() or "Bilinmeyen Pencere"
        except Exception:
            return ""

    def _capture_running_processes(self) -> list[dict[str, Any]]:
        try:
            import psutil
            processes: list[dict[str, Any]] = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = proc.info
                    processes.append({
                        "pid": info["pid"],
                        "name": info["name"],
                        "cpu": info["cpu_percent"] or 0.0,
                        "memory": info["memory_percent"] or 0.0,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            processes.sort(key=lambda p: p["cpu"], reverse=True)
            return processes[:10]
        except ImportError:
            return []
        except Exception:
            traceback.print_exc()
            return []

    def last_capture(self) -> dict[str, Any]:
        return self._last_capture
