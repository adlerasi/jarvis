"""
JARVIS desktop notification adapter — local cross-platform implementation.
"""
from __future__ import annotations

from core._native_notify import notify as _notify_core


def notify(
    title: str,
    message: str,
    priority: str = "normal",
) -> bool:
    """Send a JARVIS-branded desktop notification.

    Args:
        title:   Notification title (e.g. "JARVIS").
        message: Notification body.
        priority: "low", "normal", or "critical".

    Returns:
        True if delivered as desktop notification, False if fell back to stderr.
    """
    display_title = f"JARVIS — {title}" if title else "JARVIS"
    return _notify_core(display_title, message, priority=priority)
