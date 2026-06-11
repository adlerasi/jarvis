"""
Planner — Goal decomposition into executable task graphs
Adler ASİ tarafından yapılmıştır

Standalone library version: LLM plan generation is delegated to an injected
callable ``llm_callable(prompt: str) → str | None``.
"""
from __future__ import annotations

import json
import time
import traceback
from typing import Any, Callable

from aca_core.task_graph import ActionType, TaskGraph, TaskNode

PLANNER_SYSTEM_PROMPT = """Sen bir gorev planlayicisisin. Kullanici hedefini analiz et ve JSON olarak adim adim bir plan cikar.

Kurallar:
1. Her adim bir aksiyon tipine sahip olmali: tool | shell | input | observe | wait
2. "tool" aksiyonlari icin tool_name su araclardan biri olabilir: open_app, sys_info, browser_control, shell_run, analyze_screen, ...
3. "input" aksiyonlari icin tool_name "pyautogui" olur, params'da action (click/type/key/drag) ve hedef belirtilir
4. "shell" aksiyonlari icin tool_name "shell_run" olur, params'da command belirtilir
5. Adimlar birbirine bagimli olabilir (dependencies), en fazla 20 adim
6. Her adim icin aciklama (description) mutlaka Turkce olmali
7. JSON formatindaki ciktida sadece plan olmali, ekstra metin olmamali

Cikis formati (ornek):
{
  "steps": [
    {
      "step_id": "s1",
      "description": "Notepad uygulamasini ac",
      "action_type": "tool",
      "tool_name": "open_app",
      "params": {"app_name": "notepad"},
      "dependencies": []
    },
    {
      "step_id": "s2",
      "description": "Notepad'e 'Merhaba Dunya' yaz",
      "action_type": "input",
      "tool_name": "pyautogui",
      "params": {"action": "type", "text": "Merhaba Dunya"},
      "dependencies": ["s1"]
    }
  ]
}
"""


class Planner:
    """Creates and manages task graphs from goal descriptions.

    ``llm_callable`` is an optional callable ``(prompt: str) → str | None``
    that sends a planning prompt to an LLM and returns a JSON string.
    When omitted the planner falls back to ``_fallback_plan``.
    """

    def __init__(
        self,
        llm_callable: Callable[[str], str | None] | None = None,
        agent_memory: object | None = None,
    ):
        self._llm_callable = llm_callable
        self._agent_memory = agent_memory

    def create_plan(self, goal_text: str) -> TaskGraph:
        cached = self._try_cached_workflow(goal_text)
        if cached is not None:
            return cached

        if self._llm_callable is not None:
            try:
                full_prompt = f"{PLANNER_SYSTEM_PROMPT}\n\nKullanici hedefi: {goal_text}"
                llm_result = self._llm_callable(full_prompt)
                if llm_result:
                    graph = self._parse_llm_response(llm_result, goal_text)
                    if self._validate_graph(graph):
                        return graph
            except Exception:
                traceback.print_exc()

        return self._fallback_plan(goal_text)

    def _try_cached_workflow(self, goal_text: str) -> TaskGraph | None:
        if self._agent_memory is None:
            return None
        try:
            matches = self._agent_memory.find_templates(goal_text)
            for match in matches:
                score = match.get("match_score", 0.0)
                if score >= 0.7:
                    graph = TaskGraph(
                        graph_id=f"cached_{int(time.time())}",
                        goal_id=goal_text,
                    )
                    steps = match.get("steps", [])
                    for step_data in steps:
                        node = TaskNode(
                            step_id=step_data["step_id"],
                            description=step_data["description"],
                            action_type=ActionType(step_data["action_type"]),
                            tool_name=step_data.get("tool_name", ""),
                            params=dict(step_data.get("params", {})),
                            dependencies=list(step_data.get("dependencies", [])),
                        )
                        graph.add_node(node)
                    for from_id, to_id in match.get("edges", []):
                        if from_id in graph.nodes and to_id in graph.nodes:
                            graph.add_edge(from_id, to_id)
                    if self._validate_graph(graph):
                        return graph
        except Exception:
            traceback.print_exc()
        return None

    def replan(self, failed_node: TaskNode, world_state: dict[str, Any],
               previous_graph: TaskGraph) -> TaskGraph:
        context = (
            f"Onceki plan basarisiz oldu.\n"
            f"Basarisiz adim: {failed_node.step_id} - {failed_node.description}\n"
            f"Hata: {failed_node.result}\n"
            f"Mevcut durum: {world_state.get('screen_text', '')}\n"
            f"Hedefe hala ulasmak icin kalan adimlari olustur."
        )
        if self._llm_callable is not None:
            try:
                full_prompt = f"{PLANNER_SYSTEM_PROMPT}\n\n{context}"
                llm_result = self._llm_callable(full_prompt)
                if llm_result:
                    graph = self._parse_llm_response(llm_result,
                                                      previous_graph.goal_id)
                    if self._validate_graph(graph):
                        return graph
            except Exception:
                traceback.print_exc()

        g = TaskGraph(graph_id=f"replan_{int(time.time())}",
                       goal_id=previous_graph.goal_id)
        retry_node = TaskNode(
            step_id=f"r_{failed_node.step_id}",
            description=f"Tekrar dene: {failed_node.description}",
            action_type=failed_node.action_type,
            tool_name=failed_node.tool_name,
            params=dict(failed_node.params),
            max_retries=1,
        )
        g.add_node(retry_node)
        return g

    def _parse_llm_response(self, text: str, goal_text: str) -> TaskGraph:
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

        graph_id = f"plan_{int(time.time())}"
        g = TaskGraph(graph_id=graph_id, goal_id=goal_text)

        for step_data in data.get("steps", []):
            node = TaskNode(
                step_id=step_data.get("step_id", f"s_{len(g.nodes)}"),
                description=step_data.get("description", ""),
                action_type=ActionType(step_data.get("action_type", "tool")),
                tool_name=step_data.get("tool_name", ""),
                params=step_data.get("params", {}),
                dependencies=step_data.get("dependencies", []),
            )
            g.add_node(node)

        for node in g.nodes.values():
            for dep_id in node.dependencies:
                if dep_id in g.nodes:
                    g.add_edge(dep_id, node.step_id)

        return g

    def _validate_graph(self, graph: TaskGraph) -> bool:
        try:
            if len(graph.nodes) > 20:
                return False
            if len(graph.nodes) == 0:
                return False
            all_ids = set(graph.nodes.keys())
            for node in graph.nodes.values():
                for dep_id in node.dependencies:
                    if dep_id not in all_ids:
                        return False
            if graph.has_cycle():
                return False
            return True
        except Exception:
            traceback.print_exc()
            return False

    def _fallback_plan(self, goal_text: str) -> TaskGraph:
        g = TaskGraph(graph_id=f"fallback_{int(time.time())}",
                       goal_id=goal_text)
        g.add_node(TaskNode(
            step_id="s1",
            description=f"Gorev: {goal_text}",
            action_type=ActionType.TOOL,
            tool_name="analyze_screen",
            params={"query": goal_text},
        ))
        return g
