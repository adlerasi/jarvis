"""
Reflection — Step evaluation and loop detection for ACA
Adler ASİ tarafından yapılmıştır

Standalone library version: LLM-based evaluation is delegated to an injected
callable ``evaluate_callable(prompt: str) → str | None``.
"""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Any, Callable

from aca_core.task_graph import TaskNode


@dataclass
class ReflectionResult:
    """Result of a step evaluation."""
    success: bool
    confidence: float
    analysis: str


REFLECTION_PROMPT = """Sen bir gorev degerlendiricisisin. Bir adimin basarili olup olmadigini degerlendir.

Adim: {description}
Arac: {tool_name}
Parametreler: {params}
Arac sonucu: {tool_result}

Adim oncesi ekran: {observation_before}
Adim sonrasi ekran: {observation_after}

Soru: Bu adim amaclanan sonuca ulasti mi?
Yaniti sadece JSON formatinda ver:
{{
  "success": true/false,
  "confidence": 0.0-1.0,
  "analysis": "Kisa Turkce analiz"
}}
"""


class Reflection:
    """Evaluates step execution results and detects execution loops.

    ``evaluate_callable`` is an optional callable ``(prompt: str) → str | None``
    that sends an evaluation prompt to an LLM.  Falls back to heuristic
    evaluation when unavailable or when the callable returns None.
    """

    def __init__(self, evaluate_callable: Callable[[str], str | None] | None = None):
        self._evaluate_callable = evaluate_callable

    def evaluate_step(self, node: TaskNode,
                       world_state_before: dict[str, Any],
                       world_state_after: dict[str, Any],
                       tool_result: str) -> ReflectionResult:
        # Try LLM evaluation first
        if self._evaluate_callable is not None:
            try:
                result = self._llm_evaluate(node, world_state_before,
                                              world_state_after, tool_result)
                if result is not None:
                    return result
            except Exception:
                traceback.print_exc()

        # Fallback: heuristic evaluation
        return self._heuristic_evaluate(node, tool_result)

    def _llm_evaluate(self, node: TaskNode,
                       world_state_before: dict[str, Any],
                       world_state_after: dict[str, Any],
                       tool_result: str) -> ReflectionResult | None:
        prompt = REFLECTION_PROMPT.format(
            description=node.description,
            tool_name=node.tool_name,
            params=node.params,
            tool_result=tool_result[:500],
            observation_before=str(world_state_before.get("screen_text", ""))[:300],
            observation_after=str(world_state_after.get("screen_text", ""))[:300],
        )
        text = self._evaluate_callable(prompt)
        if text and text.strip():
            return self._parse_reflection_json(text.strip())
        return None

    def _parse_reflection_json(self, text: str) -> ReflectionResult | None:
        import json

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            cleaned = cleaned[start:end + 1]

        data = json.loads(cleaned)
        return ReflectionResult(
            success=bool(data.get("success", False)),
            confidence=float(data.get("confidence", 0.0)),
            analysis=str(data.get("analysis", "")),
        )

    def _heuristic_evaluate(self, node: TaskNode, tool_result: str) -> ReflectionResult:
        result_lower = (tool_result or "").strip().lower()

        error_markers = (
            "hata", "error", "alinamadi", "alınamadı",
            "bulunamadi", "bulunamadı", "acilamadi", "açılamadı",
            "tamamlanamadi", "tamamlanamadı", "basarisiz", "başarısız",
            "zaman asimi", "engellendi", "mevcut degil",
        )

        success_markers = (
            "basarili", "başarılı", "tamamlandi", "tamamlandı",
            "calistirildi", "çalıştırıldı", "gonderildi", "gönderildi",
            "kaydedildi", "silindi", "acildi", "açıldı",
        )

        has_error = any(m in result_lower for m in error_markers)
        has_success = any(m in result_lower for m in success_markers)

        if has_error and not has_success:
            return ReflectionResult(
                success=False,
                confidence=0.7,
                analysis=f"Arac hatasi: {tool_result[:200]}",
            )
        elif has_success and not has_error:
            return ReflectionResult(
                success=True,
                confidence=0.8,
                analysis=f"Adim basariyla tamamlandi: {tool_result[:100]}",
            )
        elif not has_error and not has_success:
            if tool_result and len(tool_result) > 2:
                return ReflectionResult(
                    success=True,
                    confidence=0.5,
                    analysis=f"Adim calisti, sonuc: {tool_result[:100]}",
                )
            else:
                return ReflectionResult(
                    success=False,
                    confidence=0.4,
                    analysis="Sonuc alinamadi.",
                )
        else:
            return ReflectionResult(
                success=False,
                confidence=0.3,
                analysis="Celisen sinyaller: " + tool_result[:100],
            )

    def detect_loop(self, execution_history: list[dict[str, Any]]) -> bool:
        if len(execution_history) < 3:
            return False

        recent = execution_history[-10:] if len(execution_history) > 10 else execution_history

        signature_counts: dict[str, int] = {}
        for entry in recent:
            tool = entry.get("tool_name", "")
            params = entry.get("params", {})
            param_keys = frozenset(params.keys())
            sig = f"{tool}:{param_keys}"
            signature_counts[sig] = signature_counts.get(sig, 0) + 1

        for sig, count in signature_counts.items():
            if count >= 3:
                return True

        tool_sequence = [e.get("tool_name", "") for e in recent]
        if len(tool_sequence) >= 4:
            if len(set(tool_sequence[-4:])) == 1:
                return True

        return False
