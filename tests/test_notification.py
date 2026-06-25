"""
Tests for core/notification.py and core/_native_notify.py.
"""
from __future__ import annotations

import sys
from unittest import TestCase
from unittest.mock import MagicMock, patch


class TestNotify(TestCase):
    """core.notification.notify() — JARVIS desktop notification adapter."""

    def test_prefixes_title_with_jarvis(self):
        """notify() should prefix title with 'JARVIS — '."""
        with patch("core.notification._notify_core") as mock_core:
            from core.notification import notify
            notify("Test", "message")
            mock_core.assert_called_once_with("JARVIS — Test", "message", priority="normal")

    def test_empty_title_defaults_to_jarvis(self):
        """notify() with empty title should use just 'JARVIS'."""
        with patch("core.notification._notify_core") as mock_core:
            from core.notification import notify
            notify("", "message")
            mock_core.assert_called_once_with("JARVIS", "message", priority="normal")

    def test_forwards_priority(self):
        """notify() should forward priority parameter."""
        with patch("core.notification._notify_core") as mock_core:
            from core.notification import notify
            notify("Alert", "msg", priority="critical")
            mock_core.assert_called_once_with("JARVIS — Alert", "msg", priority="critical")

    def test_fallback_to_stderr_on_failure(self):
        """notify() should print to stderr when desktop notification fails."""
        with patch("core.notification._notify_core", return_value=False):
            from core.notification import notify
            result = notify("Test", "msg")
            self.assertFalse(result)


class TestNativeNotify(TestCase):
    """core._native_notify.notify() — cross-platform desktop notification."""

    @patch("core._native_notify.platform.system", return_value="Linux")
    @patch("core._native_notify.subprocess.run")
    def test_linux_notify_send(self, mock_run: MagicMock, mock_system: MagicMock):
        """Linux should call notify-send with urgency."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "notify-send")
        self.assertIn("normal", args)

    @patch("core._native_notify.platform.system", return_value="Linux")
    @patch("core._native_notify.subprocess.run", side_effect=FileNotFoundError)
    def test_linux_notify_send_missing(self, mock_run: MagicMock, mock_system: MagicMock):
        """Linux should return False when notify-send is missing."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertFalse(result)

    @patch("core._native_notify.platform.system", return_value="Darwin")
    @patch("core._native_notify.subprocess.run")
    def test_darwin_osascript(self, mock_run: MagicMock, mock_system: MagicMock):
        """macOS should call osascript."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertTrue(result)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "osascript")

    @patch("core._native_notify.platform.system", return_value="Darwin")
    @patch("core._native_notify.subprocess.run", side_effect=FileNotFoundError)
    def test_darwin_osascript_missing(self, mock_run: MagicMock, mock_system: MagicMock):
        """macOS should return False when osascript is missing."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertFalse(result)

    @patch("core._native_notify.platform.system", return_value="Windows")
    @patch("core._native_notify.subprocess.run")
    def test_windows_powershell(self, mock_run: MagicMock, mock_system: MagicMock):
        """Windows should call PowerShell ToastNotification."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertTrue(result)
        args = mock_run.call_args[0][0]
        self.assertEqual(args[0], "powershell")

    @patch("core._native_notify.platform.system", return_value="Windows")
    @patch("core._native_notify.subprocess.run", side_effect=FileNotFoundError)
    def test_windows_missing(self, mock_run: MagicMock, mock_system: MagicMock):
        """Windows should return False when PowerShell is missing."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertFalse(result)

    @patch("core._native_notify.platform.system", return_value="UnknownOS")
    def test_unknown_platform(self, mock_system: MagicMock):
        """Unknown platform should fall back and return False."""
        from core._native_notify import notify
        result = notify("JARVIS", "Hello")
        self.assertFalse(result)

    def test_stderr_fallback_message(self):
        """Unknown platform should print fallback to stderr."""
        from core._native_notify import notify
        with patch("sys.stderr") as mock_stderr:
            with patch("core._native_notify.platform.system", return_value="UnknownOS"):
                notify("JARVIS", "Hello")
            mock_stderr.write.assert_called()
