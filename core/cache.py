"""LRU Cache — thread-safe, TTL-aware, with hit/miss tracking.

Usage:
    cache = LRUCache(maxsize=128, ttl=300)
    cache.set("key", value)
    val = cache.get("key")          # None if missing or expired
    val = cache.get_or_set("key", lambda: expensive(), ttl=60)
    print(cache.stats)              # {"hits": 5, "misses": 2, "size": 3}
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional


class LRUCache:
    """Thread-safe LRU cache with optional per-key TTL."""

    def __init__(self, maxsize: int = 128, ttl: Optional[float] = None):
        self._maxsize = max(maxsize, 1)
        self._default_ttl = ttl
        self._lock = threading.Lock()
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._expiry: dict[str, float] = {}
        self._hits = 0
        self._misses = 0

    # ── Public API ────────────────────────────────────────────

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            val = self._cache.get(key)
            if val is None:
                self._misses += 1
                return default
            if self._is_expired(key):
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
                self._misses += 1
                return default
            self._cache.move_to_end(key)
            self._hits += 1
            return val

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expiry = None
        ttl_val = ttl if ttl is not None else self._default_ttl
        if ttl_val is not None:
            expiry = time.time() + ttl_val
        with self._lock:
            self._cache[key] = value
            if expiry is not None:
                self._expiry[key] = expiry
            self._cache.move_to_end(key)
            self._evict_if_needed()

    def get_or_set(
        self, key: str, factory: Callable[[], Any],
        ttl: Optional[float] = None
    ) -> Any:
        existing = self.get(key)
        if existing is not None:
            return existing
        value = factory()
        self.set(key, value, ttl=ttl)
        return value

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()
            self._expiry.clear()
            self._hits = 0
            self._misses = 0

    def remove(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)

    @property
    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._cache),
                "maxsize": self._maxsize,
            }

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    # ── Internal ──────────────────────────────────────────────

    def _is_expired(self, key: str) -> bool:
        exp = self._expiry.get(key)
        if exp is None:
            return False
        return time.time() > exp

    def _evict_if_needed(self) -> None:
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)
