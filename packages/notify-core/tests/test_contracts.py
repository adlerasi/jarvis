"""
Contract tests for Notification Service (notify-core) library.

Tests use real subprocess calls for desktop notification backends (where
available) and temp files for log handlers.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


# ── Helpers ────────────────────────────────────────────────────────────

def _desktop_available() -> bool:
    """Check if at least one desktop notification backend is available."""
    # Linux notify-send
    try:
        subprocess.run(["which", "notify-send"], capture_output=True, timeout=3)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    # Check platform
    import platform
    if platform.system() == "Windows":
        return True  # PowerShell BurntToast may work
    if platform.system() == "Darwin":
        return True  # osascript works on macOS
    return False


# ── Contract: Desktop Notification ─────────────────────────────────────

class DesktopNotifyContract(unittest.TestCase):
    """notify() must deliver a desktop notification."""

    def test_notify_basic(self):
        """notify(title, message) returns True on success."""
        from notify_core import notify
        result = notify("Test", "This is a test notification")
        self.assertIsInstance(result, bool)

    def test_notify_with_priority(self):
        """notify() accepts optional priority parameter."""
        from notify_core import notify
        for prio in ("low", "normal", "critical"):
            result = notify("Test", f"Priority {prio}", priority=prio)
            self.assertIsInstance(result, bool)

    def test_notify_returns_bool(self):
        """notify() always returns a bool."""
        from notify_core import notify
        result = notify("Test", "Hello")
        self.assertIn(result, (True, False))


# ── Contract: NotificationBus ──────────────────────────────────────────

class NotificationBusContract(unittest.TestCase):
    """NotificationBus publish/subscribe pattern."""

    def setUp(self):
        from notify_core import NotificationBus
        self.bus = NotificationBus()
        self._received: list[dict] = []

    def _handler(self, event: dict):
        self._received.append(event)

    def test_subscribe_returns_token(self):
        token = self.bus.subscribe("test.event", self._handler)
        self.assertIsNotNone(token)

    def test_publish_calls_handler(self):
        self.bus.subscribe("test.event", self._handler)
        self.bus.publish("test.event", {"msg": "hello"})
        self.assertEqual(len(self._received), 1)
        self.assertEqual(self._received[0]["msg"], "hello")

    def test_unsubscribe_stops_handler(self):
        token = self.bus.subscribe("test.event", self._handler)
        self.bus.unsubscribe(token)
        self.bus.publish("test.event", {"msg": "hello"})
        self.assertEqual(len(self._received), 0)

    def test_multiple_subscribers_all_called(self):
        received2: list = []
        def handler2(e): received2.append(e)
        self.bus.subscribe("test.event", self._handler)
        self.bus.subscribe("test.event", handler2)
        self.bus.publish("test.event", {"x": 1})
        self.assertEqual(len(self._received), 1)
        self.assertEqual(len(received2), 1)

    def test_different_events_dont_cross(self):
        self.bus.subscribe("event.a", self._handler)
        self.bus.publish("event.b", {"msg": "no"})
        self.assertEqual(len(self._received), 0)

    def test_subscribe_wildcard(self):
        """Subscribing to '*' receives all events."""
        from notify_core import NotificationBus
        bus = NotificationBus()
        received: list = []
        bus.subscribe("*", lambda e: received.append(e))
        bus.publish("any.event", {"val": 1})
        bus.publish("other.event", {"val": 2})
        self.assertEqual(len(received), 2)

    def test_publish_without_subscribers_does_not_crash(self):
        self.bus.publish("lonely.event", {"data": 1})  # should not raise


# ── Contract: VoiceHandler ─────────────────────────────────────────────

class VoiceHandlerContract(unittest.TestCase):
    """VoiceHandler speaks via injected callable."""

    def test_voice_handler_calls_speak(self):
        from notify_core import VoiceHandler
        captured: list[str] = []
        def speak(text: str): captured.append(text)
        handler = VoiceHandler(speak=speak)
        handler({"title": "Test", "message": "Hello", "priority": "normal"})
        self.assertGreater(len(captured), 0)
        self.assertIn("Hello", captured[0])

    def test_voice_handler_no_speak_does_not_crash(self):
        from notify_core import VoiceHandler
        handler = VoiceHandler(speak=None)
        handler({"title": "Test", "message": "Hello", "priority": "normal"})  # no crash

    def test_voice_handler_includes_title(self):
        from notify_core import VoiceHandler
        captured: list[str] = []
        def speak(text: str): captured.append(text)
        handler = VoiceHandler(speak=speak)
        handler({"title": "Warning", "message": "Low battery", "priority": "critical"})
        self.assertIn("Warning", captured[0])


# ── Contract: LogHandler ───────────────────────────────────────────────

class LogHandlerContract(unittest.TestCase):
    """LogHandler writes timestamped entries."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="notify_ctr_"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_log_handler_writes_to_file(self):
        from notify_core import LogHandler
        logfile = self._tmp / "notifications.log"
        handler = LogHandler(file_path=str(logfile))
        handler({"title": "Test", "message": "Hello", "priority": "normal"})
        content = logfile.read_text(encoding="utf-8")
        self.assertIn("Test", content)
        self.assertIn("Hello", content)

    def test_log_handler_stdout(self):
        from notify_core import LogHandler
        handler = LogHandler(file_path=None)  # stdout
        handler({"title": "Stdout", "message": "Test", "priority": "low"})  # no crash

    def test_log_handler_timestamp_format(self):
        from notify_core import LogHandler
        logfile = self._tmp / "ts.log"
        handler = LogHandler(file_path=str(logfile))
        handler({"title": "TS", "message": "test", "priority": "normal"})
        content = logfile.read_text(encoding="utf-8")
        # Should contain a timestamp-like prefix (digits or ISO date)
        import re
        self.assertTrue(re.search(r"\d{4}-\d{2}-\d{2}", content) or re.search(r"\d+", content.split(" ")[0]))


# ── Contract: Notification Integration ─────────────────────────────────

class IntegrationContract(unittest.TestCase):
    """End-to-end: bus + handler(s) work together."""

    def test_bus_with_log_handler(self):
        from notify_core import NotificationBus, LogHandler
        bus = NotificationBus()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            logpath = f.name
        handler = LogHandler(file_path=logpath)
        bus.subscribe("*", handler)
        bus.publish("test.event", {"title": "E2E", "message": "Works", "priority": "normal"})
        time.sleep(0.1)  # Let async writes settle
        content = Path(logpath).read_text(encoding="utf-8")
        self.assertIn("E2E", content)
        Path(logpath).unlink(missing_ok=True)

    def test_bus_with_voice_handler(self):
        from notify_core import NotificationBus, VoiceHandler
        bus = NotificationBus()
        captured: list[str] = []
        handler = VoiceHandler(speak=lambda t: captured.append(t))
        bus.subscribe("*", handler)
        bus.publish("alert", {"title": "Alert", "message": "Battery low", "priority": "critical"})
        self.assertGreater(len(captured), 0)


# ── Contract: CLI Interface ────────────────────────────────────────────

class CLIContract(unittest.TestCase):
    """CLI: stdin/stdout/--json per Principle VI."""

    def test_cli_send(self):
        """`notify-core send Title Message` exits 0."""
        result = subprocess.run(
            [sys.executable, "-m", "notify_core", "send", "CLI Test", "Hello from CLI"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_cli_send_json(self):
        """`notify-core send T M --json` returns JSON."""
        result = subprocess.run(
            [sys.executable, "-m", "notify_core", "send", "Test", "Body", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIn("status", data)

    def test_cli_unknown_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "notify_core", "bogus"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
