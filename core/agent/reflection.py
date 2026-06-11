"""Reflection — Step evaluation, confidence scoring, and loop detection."""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ReflectionResult:
    success: bool = False
    confidence: float = 0.0
    analysis: str = ""
    suggestion: str = ""


class Reflection:
    """Evaluates step execution results via an injected LLM callable.

    ``evaluate_callable`` — optional ``(task_description, result) -> (analysis, success_bool)``.
    When omitted the fallback always returns success (for testing/headless).
    """

    def __init__(
        self,
        evaluate_callable: Callable[[str, str], tuple[str, int] | None] | None = None,
    ):
        self._evaluate = evaluate_callable
        self._history: list[dict[str, Any]] = []

    def evaluate_step(
        self,
        node: Any,
        world_before: dict[str, Any] | None = None,
        world_after: dict[str, Any] | None = None,
        result_text: str = "",
    ) -> ReflectionResult:
        if self._evaluate is not None:
            try:
                analysis, success_code = self._evaluate(
                    node.description, result_text,
                )
                confidence = 1.0 if success_code == 1 else 0.3
                return ReflectionResult(
                    success=(success_code == 1),
                    confidence=confidence,
                    analysis=analysis or "Degerlendirme yapilamadi.",
                    suggestion=self._generate_suggestion(node, success_code == 1),
                )
            except Exception:
                traceback.print_exc()

        return ReflectionResult(
            success=True,
            confidence=0.5,
            analysis="Reflection callable kullanilamadi, basarili kabul edildi.",
        )

    def detect_loop(self, execution_history: list[dict[str, Any]]) -> bool:
        if len(execution_history) < 4:
            return False
        recent = execution_history[-4:]
        tool_ids = [(e.get("tool_name"), e.get("step_id")) for e in recent]
        if len(set(tool_ids)) <= 2:
            return True
        if len(execution_history) >= 3:
            last_three = execution_history[-3:]
            if all(e.get("tool_name") == last_three[0].get("tool_name")
                   for e in last_three):
                return True
        return False

    def _generate_suggestion(self, node: Any, success: bool) -> str:
        if success:
            return "Siradaki adima gec."
        tool = getattr(node, "tool_name", None) or ""
        if "shell" in tool:
            return "Komut syntax'ini kontrol et veya farkli parametrelerle dene."
        if "browser" in tool:
            return "Sayfanin yuklendigini kontrol et veya URL'i dogrula."
        return "Adimi farkli bir yaklasimla tekrar dene."
