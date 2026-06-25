"""Reference Resolver — resolves Turkish pronominal references.

Maps ambiguous referents ("bunu", "sunu", "onceki", "su dosya") to
concrete objects from the conversation history using simple
heuristics (recency, noun phrase matching).

Usage:
    resolver = ReferenceResolver()
    resolved = resolver.resolve(
        "bunu ac", history=recent_turns
    )
    # -> {"type": "file", "name": "report.pdf", "turn_id": 3}
"""

from __future__ import annotations

import re
from typing import Any, Optional

# Turkish demonstrative pronouns and their likely referent types
_DEMONSTRATIVES: dict[str, list[str]] = {
    "bunu": ["file", "app", "command"],
    "sunu": ["file", "app", "command"],
    "onu": ["file", "app", "contact"],
    "bunlar": ["file", "app"],
    "sunlar": ["file"],
    "onlari": ["file", "contact"],
    "su dosyayi": ["file"],
    "bu dosyayi": ["file"],
    "su klasoru": ["folder"],
    "bu klasoru": ["folder"],
    "su uygulamayi": ["app"],
    "bu uygulamayi": ["app"],
    "onceki": ["turn"],
    "bir onceki": ["turn"],
    "son": ["turn"],
}

# Patterns that might introduce a noun phrase after the pronoun
_NOUN_AFTER = re.compile(
    r"(bunu|sunu|onu|su|bu)\s+(\w+)", re.IGNORECASE
)


class ReferenceResolver:
    """Resolves ambiguous references using conversation context.

    Uses recency-based heuristics:
    1. If the reference contains an explicit noun ("su dosya"), match type.
    2. Otherwise, scan recent turns for the most likely referent
       based on action verbs and noun phrases.
    """

    def resolve(
        self,
        user_text: str,
        history: Optional[list[dict]] = None,
    ) -> Optional[dict[str, Any]]:
        """Try to resolve a reference in *user_text*.

        Args:
            user_text: The user's current utterance.
            history: List of conversation turns (from ConversationTranscript).

        Returns:
            Dict with keys ``type``, ``text``, ``turn_id``, or None.
        """
        text_lower = user_text.lower().strip()
        history = history or []

        # 1. Check registered demonstrative phrases first (full match)
        for phrase in sorted(_DEMONSTRATIVES, key=len, reverse=True):
            if phrase in text_lower:
                return self._resolve_demonstrative(
                    phrase, _DEMONSTRATIVES[phrase], history
                )

        # 2. Check for "onceki" / "bir onceki"
        if "onceki" in text_lower or "önceki" in text_lower:
            return self._resolve_previous(history)

        # 3. Check for explicit "su X" / "bu X" patterns (fallback)
        noun_match = _NOUN_AFTER.search(text_lower)
        if noun_match:
            pronoun = noun_match.group(1)
            noun = noun_match.group(2)
            return self._resolve_with_noun(pronoun, noun, history)

        return None

    # ── Resolution strategies ────────────────────────────────

    @staticmethod
    def _resolve_with_noun(
        pronoun: str, noun: str, history: list[dict]
    ) -> Optional[dict[str, Any]]:
        noun_lower = noun.lower()
        # Scan recent turns for the noun
        for turn in reversed(history):
            user_text = turn.get("user", {}).get("text", "").lower()
            assistant_text = turn.get("jarvis", {}).get("text", "").lower()
            if noun_lower in user_text or noun_lower in assistant_text:
                return {
                    "type": "noun_phrase",
                    "text": noun,
                    "context": turn,
                    "turn_id": turn.get("turn_id"),
                }
        return {
            "type": "noun_phrase",
            "text": noun,
            "context": None,
            "turn_id": None,
        }

    @staticmethod
    def _resolve_demonstrative(
        phrase: str, types: list[str], history: list[dict]
    ) -> Optional[dict[str, Any]]:
        # Scan newest-first for the most recent relevant entity
        for turn in reversed(history):
            turn_text = (
                turn.get("user", {}).get("text", "")
                + " "
                + turn.get("jarvis", {}).get("text", "")
            ).lower()

            # Check for file names, app names, etc.
            for t in types:
                if t == "file":
                    match = re.search(r"(\w+\.\w+)", turn_text)
                    if match:
                        return {
                            "type": "file",
                            "text": match.group(1),
                            "context": turn,
                            "turn_id": turn.get("turn_id"),
                        }
                elif t == "app":
                    match = re.search(
                        r"(ac(?:il)?(?:di|sin|ma)\w*)\s+(\w+)",
                        turn_text,
                    )
                    if match:
                        return {
                            "type": "app",
                            "text": match.group(2),
                            "context": turn,
                            "turn_id": turn.get("turn_id"),
                        }

            # Fallback: return the last assistant response
            assistant_text = turn.get("jarvis", {}).get("text", "")
            if assistant_text:
                return {
                    "type": "turn",
                    "text": assistant_text[:100],
                    "context": turn,
                    "turn_id": turn.get("turn_id"),
                }

        return None

    @staticmethod
    def _resolve_previous(
        history: list[dict],
    ) -> Optional[dict[str, Any]]:
        if not history:
            return None
        # Return the user utterance from the previous turn
        prev = history[-1]
        return {
            "type": "previous_turn",
            "text": prev.get("user", {}).get("text", ""),
            "turn_id": prev.get("turn_id"),
            "context": prev,
        }
