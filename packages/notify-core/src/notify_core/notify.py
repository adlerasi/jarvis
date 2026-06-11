"""
Desktop notification — cross-platform via subprocess.
"""
from __future__ import annotations

import logging
import platform
import subprocess
import sys

logger = logging.getLogger(__name__)

_PRIORITY_MAP = {
    "low": "low",
    "normal": "normal",
    "critical": "critical",
}


def _notify_linux(title: str, message: str, priority: str) -> bool:
    """Send desktop notification via notify-send (Linux)."""
    urgency = _PRIORITY_MAP.get(priority, "normal")
    try:
        subprocess.run(
            ["notify-send", "-u", urgency, title, message],
            capture_output=True, timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("notify-send not available")
        return False


def _notify_darwin(title: str, message: str) -> bool:
    """Send desktop notification via osascript (macOS)."""
    try:
        script = f'display notification "{message}" with title "{title}"'
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("osascript not available")
        return False


def _notify_windows(title: str, message: str) -> bool:
    """Send desktop notification via PowerShell (Windows)."""
    ps_script = (
        f'[Windows.UI.Notifications.ToastNotificationManager,'
        f' Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;'
        f'$template = [Windows.UI.Notifications.ToastNotificationManager]'
        f'::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);'
        f'$textNodes = $template.GetElementsByTagName("text");'
        f'$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null;'
        f'$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null;'
        f'$toast = [Windows.UI.Notifications.ToastNotification]::new($template);'
        f'[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier().Show($toast);'
    )
    try:
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=10,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return _notify_windows_fallback(title, message)


def _notify_windows_fallback(title: str, message: str) -> bool:
    """Fallback: BurntToast-like popup via .NET MessageBox."""
    try:
        ps_fallback = (
            f'Add-Type -AssemblyName System.Windows.Forms;'
            f'[System.Windows.Forms.MessageBox]::Show("{message}", "{title}")'
        )
        subprocess.run(
            ["powershell", "-Command", ps_fallback],
            capture_output=True, timeout=10,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def notify(title: str, message: str, priority: str = "normal") -> bool:
    """Display a desktop notification.

    Uses native notification mechanisms:
    - Linux:  notify-send
    - macOS:  osascript
    - Windows: PowerShell ToastNotification

    Falls back to stderr logging if no desktop backend is available.

    Args:
        title: Notification title.
        message: Notification body.
        priority: One of "low", "normal", "critical".

    Returns:
        True if delivered via desktop backend, False if fell back.
    """
    system = platform.system()
    ok: bool = False

    if system == "Linux":
        ok = _notify_linux(title, message, priority)
    elif system == "Darwin":
        ok = _notify_darwin(title, message)
    elif system == "Windows":
        ok = _notify_windows(title, message)

    if not ok:
        # Fallback: print to stderr so it's visible in terminal/CI
        print(f"[{priority.upper()}] {title}: {message}", file=sys.stderr)

    return ok
