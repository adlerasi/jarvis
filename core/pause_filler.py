"""Pause Fillers — natural Turkish hesitation tokens for conversational flow.

Inserts filler words ("ee...", "sey...", "yani...") at natural
pause points in LLM responses to make speech sound more human.

Usage:
    pf = PauseFiller(rate=0.3)
    text = pf.fill("Yarin hava guzel olacak ve disari cikabiliriz")
    # -> "Yarin hava guzel olacak ee... ve disari cikabiliriz"
"""

from __future__ import annotations

import random
import re
from typing import Optional

_FILLERS: dict[str, list[str]] = {
    "mid": [
        "ee...",
        "sey...",
        "yani...",
        "hani...",
    ],
    "start": [
        "Aslinda...",
        "Biliyor musun...",
        "Bak su sekilde...",
        "Soyle ki...",
    ],
    "end": [
        "degil mi?",
        "oyle degil mi?",
        "anladin mi?",
        "dimii?",
    ],
}

# Regex for natural pause points: before conjunctions, after commas
_PAUSE_BEFORE = re.compile(
    r"(?<=[a-zA-ZğüşıöçĞÜŞİÖÇ0-9])\s+(ve|veya|ama|fakat|lakin|ancak|cunku|çünkü"
    r"|ile|ya da|veya da)\s+",
    re.IGNORECASE,
)
_PAUSE_AFTER_COMMA = re.compile(r",\s*")


class PauseFiller:
    """Inserts Turkish filler words at natural pause points.

    Args:
        rate: Probability (0.0–1.0) of inserting a filler at any
            given pause point. 0.2–0.3 is natural for most contexts.
        mid_fillers: List of midline filler tokens.
        start_fillers: List of sentence-start filler tokens.
        end_fillers: List of sentence-end filler tokens.
    """

    def __init__(
        self,
        rate: float = 0.25,
        mid_fillers: Optional[list[str]] = None,
        start_fillers: Optional[list[str]] = None,
        end_fillers: Optional[list[str]] = None,
    ):
        self.rate = max(0.0, min(1.0, rate))
        self._mid = mid_fillers or _FILLERS["mid"]
        self._start = start_fillers or _FILLERS["start"]
        self._end = end_fillers or _FILLERS["end"]

    # ── Public API ───────────────────────────────────────────

    def fill(self, text: str) -> str:
        """Add filler tokens at natural pause points."""
        if not text or self.rate <= 0:
            return text

        result = text

        # 1. After commas (low rate)
        result = _PAUSE_AFTER_COMMA.sub(
            lambda m: self._maybe_insert(m.group() + self._pick("mid")),
            result,
        )

        # 2. Before conjunctions (mid rate)
        result = _PAUSE_BEFORE.sub(
            lambda m: f" {self._maybe_insert('')} {m.group(1)} ",
            result,
        )

        # 3. Add a start filler occasionally (only for longer sentences)
        if len(text) > 40 and random.random() < self.rate * 0.5:
            result = f"{self._pick('start')} {result[0].lower()}{result[1:]}"

        return result

    # ── Internal ─────────────────────────────────────────────

    def _pick(self, category: str) -> str:
        pool = getattr(self, f"_{category}", self._mid)
        return random.choice(pool)

    def _maybe_insert(self, fallback: str) -> str:
        if random.random() < self.rate:
            return self._pick("mid")
        return fallback
