from __future__ import annotations

import json
import re
import traceback
import unicodedata
from pathlib import Path
from typing import Any


class MemoryStore:
    """JSON-backed key-value store with deep merge, search, and formatting.

    Persists data to a JSON file. Thread-safe only at the file level
    (atomic write via ``write_text``).
    """

    def __init__(self, file_path: str | Path):
        self._file = Path(file_path)
        self._data: dict[str, Any] = {}
        self._load()

    @property
    def data(self) -> dict:
        """Return the underlying data dict (read-only view)."""
        return self._data

    # ── Public API ──────────────────────────────────────────────────

    def get(self, key: str) -> Any | None:
        """Get a value by dot-separated *key*.

        Examples::

            store.get("name")         # top-level
            store.get("user.name")    # nested
        """
        parts = key.split(".")
        cur = self._data
        for i, part in enumerate(parts):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur

    def set(self, key: str, value: Any) -> None:
        """Set *value* at dot-separated *key*, overwriting existing."""
        parts = key.split(".")
        cur = self._data
        for part in parts[:-1]:
            if part not in cur or not isinstance(cur[part], dict):
                cur[part] = {}
            cur = cur[part]
        cur[parts[-1]] = value
        self._save()

    def merge(self, key: str, value: dict[str, Any]) -> None:
        """Deep-merge *value* into the dict at dot-separated *key*.

        Nested dictionaries are merged recursively. Non-dict values at
        *key* are overwritten.
        """
        existing = self.get(key)
        if isinstance(existing, dict):
            merged = self._deep_merge(existing, value)
        else:
            merged = value
        self.set(key, merged)

    def search(self, text: str) -> list[dict[str, Any]]:
        """Search all stored data by normalized text matching.

        Returns a list of ``{"category", "key", "value"}`` dicts for
        every matching entry.
        """
        needle = self._normalize(text)
        if not needle:
            return []
        results: list[dict[str, Any]] = []
        self._search_dict(self._data, [], needle, results)
        return results

    def delete(
        self,
        category: str | None = None,
        key: str | None = None,
        match_text: str | None = None,
    ) -> str:
        """Delete entries by exact path or text match.

        Args:
            category: Top-level key name.
            key: Second-level key name (requires *category*).
            match_text: Text to match against stored data.

        Returns a human-readable status message.
        """
        if category and key:
            return self._delete_exact(category, key)
        if category:
            return self._delete_exact(category)
        if match_text:
            return self._delete_by_match(match_text)
        return "Silinecek bir sey belirtilmedi."

    def format(self) -> str:
        """Format all stored data into a human-readable string.

        Returns empty string if store is empty.
        """
        if not self._data:
            return ""
        lines: list[str] = []
        for category, items in self._data.items():
            if isinstance(items, dict):
                for k, v in items.items():
                    display = self._value_text(v)
                    lines.append(f"{category}/{k}: {display}")
            else:
                lines.append(f"{category}: {self._value_text(items)}")
        return "\n".join(lines)

    def load(self) -> None:
        """Reload data from disk, discarding in-memory changes."""
        self._load()

    def save(self) -> None:
        """Persist current in-memory data to disk."""
        self._save()

    def clear(self) -> None:
        """Remove all data and reset the store."""
        self._data = {}
        self._save()

    # ── Persistence ─────────────────────────────────────────────────

    def _load(self) -> None:
        try:
            if self._file.exists():
                raw = self._file.read_text(encoding="utf-8")
                self._data = json.loads(raw) if raw.strip() else {}
            else:
                self._data = {}
        except Exception:
            traceback.print_exc()
            self._data = {}

    def _save(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            self._file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            traceback.print_exc()

    # ── Deep merge ──────────────────────────────────────────────────

    @staticmethod
    def _deep_merge(base: dict, update: dict) -> dict:
        result = base.copy()
        for k, v in update.items():
            if isinstance(v, dict) and isinstance(result.get(k), dict):
                result[k] = MemoryStore._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    # ── Text normalization ──────────────────────────────────────────

    @staticmethod
    def _normalize(text: str) -> str:
        text = (text or "").strip().casefold()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.replace("ı", "i")
        return " ".join(text.split())

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        normalized = MemoryStore._normalize(text)
        return [t for t in re.split(r"[^a-z0-9]+", normalized) if t]

    @staticmethod
    def _value_text(value: Any) -> str:
        if isinstance(value, dict):
            base = value.get("value")
            if base is not None:
                return str(base)
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    # ── Search internals ────────────────────────────────────────────

    def _search_dict(
        self,
        data: dict,
        path: list[str],
        needle: str,
        results: list[dict[str, Any]],
    ):
        for k, v in data.items():
            current_path = path + [k]
            # Check if this key or its stringified value matches
            haystacks = [
                self._normalize(k),
                self._normalize(self._value_text(v)),
            ]
            if any(needle in hay for hay in haystacks):
                category = ".".join(path) if path else k
                results.append({
                    "category": category,
                    "key": k,
                    "value": v,
                })
            # Recurse into nested dicts
            if isinstance(v, dict):
                self._search_dict(v, current_path, needle, results)

    # ── Delete internals ────────────────────────────────────────────

    def _delete_exact(self, category: str, key: str | None = None) -> str:
        if key is None:
            if category in self._data:
                del self._data[category]
                self._save()
                return f"{category} hafizadan kaldirildi."
            return "Bu kaydi bulamadim."
        bucket = self._data.get(category)
        if isinstance(bucket, dict) and key in bucket:
            del bucket[key]
            if not bucket:
                del self._data[category]
            self._save()
            return f"{category}/{key} hafizadan kaldirildi."
        return "Bu kaydi bulamadim."

    def _delete_by_match(self, match_text: str) -> str:
        needle = self._normalize(match_text)
        if not needle:
            return "Arama metni gerekli."
        for cat, bucket in list(self._data.items()):
            if isinstance(bucket, dict):
                for item_key, item_value in list(bucket.items()):
                    if self._entry_matches(needle, cat, item_key, item_value):
                        del bucket[item_key]
                        if not bucket:
                            del self._data[cat]
                        self._save()
                        return f"{cat}/{item_key} hafizadan kaldirildi."
            else:
                if self._entry_matches(needle, cat, cat, bucket):
                    del self._data[cat]
                    self._save()
                    return f"{cat} hafizadan kaldirildi."
        return "Eslestigim bir kayit bulamadim."

    def _entry_matches(self, needle: str, category: str, item_key: str, item_value: Any) -> bool:
        haystacks = [
            self._normalize(category),
            self._normalize(item_key),
            self._normalize(self._value_text(item_value)),
        ]
        if any(needle in hay for hay in haystacks):
            return True
        tokens = [t for t in self._tokenize(needle) if len(t) >= 3]
        if not tokens:
            return False
        entry_tokens: list[str] = []
        for hay in haystacks:
            entry_tokens.extend(self._tokenize(hay))
        matched = sum(
            1 for token in tokens
            if any(token in et or et in token for et in entry_tokens)
        )
        if len(tokens) == 1:
            return matched == 1
        return matched >= min(2, len(tokens))
