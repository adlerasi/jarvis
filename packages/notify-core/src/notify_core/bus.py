"""
NotificationBus — typed publish/subscribe event bus.
"""
from __future__ import annotations

import uuid
from typing import Any, Callable

Handler = Callable[[dict[str, Any]], None]
Token = str


class NotificationBus:
    """Lightweight pub/sub bus for notification events.

    Usage:
        bus = NotificationBus()
        token = bus.subscribe("event.type", handler)
        bus.publish("event.type", {"title": "...", "message": "..."})
        bus.unsubscribe(token)
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, list[tuple[Token, Handler]]] = {}
        self._tokens: dict[Token, tuple[str, Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> Token:
        """Subscribe to an event type.  Use "*" to receive all events.

        Returns a token that can be passed to unsubscribe().
        """
        token: Token = uuid.uuid4().hex[:12]
        self._subscriptions.setdefault(event_type, []).append((token, handler))
        self._tokens[token] = (event_type, handler)
        return token

    def unsubscribe(self, token: Token) -> None:
        """Remove a subscription by its token."""
        meta = self._tokens.pop(token, None)
        if meta is None:
            return
        event_type = meta[0]
        subs = self._subscriptions.get(event_type, [])
        self._subscriptions[event_type] = [
            (t, h) for t, h in subs if t != token
        ]

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event to all matching subscribers."""
        # Exact match subscribers
        for _, handler in self._subscriptions.get(event_type, []):
            handler(data)
        # Wildcard subscribers
        for _, handler in self._subscriptions.get("*", []):
            handler(data)
