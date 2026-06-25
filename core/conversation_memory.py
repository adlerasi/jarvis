"""Conversation Memory — token-aware context window manager.

Extends ConversationTranscript with:
- Token-aware window sizing (approximate)
- Turn-based summarization for long conversations
- Provider-agnostic context formatting

Usage:
    ctx = ContextWindowManager(max_tokens=4096)
    ctx.add_turn(user_text="merhaba", assistant_text="merhaba!")
    prompt = ctx.build_prompt(system_prompt)  # auto-truncated to max_tokens
"""

from __future__ import annotations

from typing import Optional

from memory.conversation_transcript import ConversationTranscript

# Rough token estimation: ~4 chars per token for Turkish/English
_CHARS_PER_TOKEN = 4


class ContextWindowManager:
    """Token-aware conversation context manager.

    Wraps ConversationTranscript and automatically
    sizes the context window to fit within a token budget.
    """

    def __init__(
        self,
        max_tokens: int = 4096,
        max_turns: int = 50,
        transcript: Optional[ConversationTranscript] = None,
    ):
        self.max_tokens = max_tokens
        self._transcript = transcript or ConversationTranscript(
            max_turns=max_turns, auto_save=True
        )

    # ── Delegated transcript API ────────────────────────────

    @property
    def transcript(self) -> ConversationTranscript:
        return self._transcript

    def add_turn(
        self,
        user_text: str,
        assistant_text: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Log a conversation turn."""
        self._transcript.add_turn(
            user_text=user_text,
            jarvis_text=assistant_text,
            metadata=metadata,
        )

    def clear(self) -> None:
        self._transcript.clear()

    # ── Context window management ───────────────────────────

    def build_prompt(
        self,
        system_prompt: str,
        extra_context: str = "",
        reserve_tokens: int = 0,
    ) -> str:
        """Build a prompt that fits within the token budget.

        reserve_tokens is typically handled by the LLM client itself --
        set to 0 to maximize context usage, or pass a value if the
        caller also limits total prompt+response length.
        """
        # Fixed overhead: system prompt + extra + conversation markers
        overhead = (
            len(system_prompt) + len(extra_context) + 200
        ) // _CHARS_PER_TOKEN
        budget = self.max_tokens - overhead - reserve_tokens
        if budget <= 0:
            return f"{system_prompt}\n\n{extra_context}"

        # Build conversation history, dropping oldest turns until it fits
        all_turns = self._transcript.get_recent(999)  # get all stored
        history_lines: list[str] = []
        history_chars = 0
        max_chars = budget * _CHARS_PER_TOKEN

        # Iterate newest-first so we keep recent context
        for turn in reversed(all_turns):
            user_text = turn.get("user", {}).get("text", "")
            assistant_text = turn.get("jarvis", {}).get("text", "")
            turn_text = ""
            if user_text:
                turn_text += f"Kullanici: {user_text}\n"
            if assistant_text:
                turn_text += f"JARVIS: {assistant_text}\n"

            turn_chars = len(turn_text)
            if history_chars + turn_chars > max_chars:
                break  # budget exhausted; drop older turns
            history_lines.append(turn_text)
            history_chars += turn_chars

        # Reverse back to chronological order
        history_str = "".join(reversed(history_lines))

        if not history_str.strip():
            return f"{system_prompt}\n\n{extra_context}"

        return (
            f"{system_prompt}\n\n"
            f"[SON KONUSMALAR]\n{history_str}\n"
            f"{extra_context}"
        )

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimate for Turkish/English text."""
        return len(text) // _CHARS_PER_TOKEN

    @property
    def stats(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "total_turns": self._transcript.turn_count,
            "stored_turns": len(self._transcript.get_recent(999)),
        }
