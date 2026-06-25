"""LazyLoader — deferred initialization for expensive resources.

Usage:
    loader = LazyLoader()
    model = loader.get("whisper", lambda: WhisperModel("base", device="cpu"))
    # or use the decorator for property-style access:
    @loader.lazy
    def stt():
        return WhisperModel("base", device="cpu")
    # stt() called only on first access
"""

from __future__ import annotations

import threading
from typing import Any, Callable


class LazyLoader:
    """Thread-safe deferred resource initializer.

    Stores factory functions and calls them once on first access,
    caching the result.  Each unique key is created at most once.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict[str, Any] = {}

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """Return the cached resource for *key*, creating it if needed."""
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        with self._lock:
            if key not in self._cache:
                self._cache[key] = factory()
            return self._cache[key]

    def clear(self, key: str | None = None) -> None:
        """Remove a single resource or clear all."""
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    @property
    def loaded_keys(self) -> set[str]:
        """Set of keys that have been initialized."""
        return set(self._cache.keys())
