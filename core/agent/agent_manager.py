"""
Agent Manager — Central orchestrator for the ACA subsystem
Adler ASİ tarafından yapılmıştır
"""
from __future__ import annotations

import threading
import time
import traceback
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from core.agent.agent_memory import AgentMemory
from core.agent.approval_manager import ApprovalManager, RiskLevel
from core.agent.executor import Executor
from core.agent.observer import Observer
from core.agent.planner import Planner
from core.agent.reflection import Reflection
from core.agent.task_graph import Status, TaskGraph, TaskNode
from core.notification import notify as _notify


class GoalStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentGoal:
    """A goal to be executed by the ACA."""
    goal_id: str
    text: str
    status: GoalStatus = GoalStatus.PENDING
    created_at: float = 0.0
    started_at: float | None = None
    completed_at: float | None = None
    result: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal_id": self.goal_id,
            "text": self.text,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentGoal:
        data = dict(data)
        data["status"] = GoalStatus(data["status"])
        return cls(**data)


class AgentManager:
    """Central orchestrator for the Autonomous Computer Agent.

    Coordinates observe → plan → act → reflect loop.
    Runs goals in background threads to avoid blocking the main pipeline.
    """

    def __init__(
        self,
        jarvis: object | None = None,
        max_steps: int = 20,
        max_duration: int = 300,
    ):
        self._jarvis = jarvis

        # Sub-components (agent_memory first — planner depends on it)
        self.agent_memory = AgentMemory(
            base_path=self._resolve_memory_path(),
        )
        self.observer = Observer(
            capture_screen=self._make_screen_capture(),
        )
        self.planner = Planner(
            llm_callable=self._make_llm_callable(),
            agent_memory=self.agent_memory,
        )
        self.executor = Executor(
            tool_handlers=self._build_tool_handlers(),
            shell_executor=self._make_shell_executor(),
        )
        self.reflection = Reflection(
            evaluate_callable=self._make_evaluate_callable(),
        )
        self.approval_manager = ApprovalManager()

        # Execution state
        self._current_goal: AgentGoal | None = None
        self._current_graph: TaskGraph | None = None
        self._execution_history: list[dict[str, Any]] = []
        self._request_id_to_cv: dict[str, threading.Event] = {}
        self._approval_results: dict[str, bool] = {}
        self._approval_mode: bool = False
        self._running: bool = False
        self._cancel_requested: bool = False
        self._lock = threading.Lock()
        self._log_history: list[str] = []

        # Execution limits (configurable per FR-026)
        self._start_time: float = 0.0
        self._max_steps = max_steps
        self._max_duration = max_duration
        self._step_counter = 0

        # Callbacks for UI updates
        self.on_state_update: Callable[[dict[str, Any]], None] | None = None

    # ── JARVIS wiring helpers ───────────────────────────────

    def _resolve_memory_path(self) -> str | None:
        if self._jarvis is None:
            return None
        from pathlib import Path
        return str(Path("memory") / "agent")

    def _make_screen_capture(self) -> Callable[[], str] | None:
        if self._jarvis is None:
            return None
        def _capture() -> str:
            try:
                from actions.screen_vision import analyze_screen
                result = analyze_screen(
                    query="Ekrandaki tüm metinleri ve arayüz öğelerini oku.",
                    target="active_window",
                )
                return str(result)
            except Exception:
                import traceback; traceback.print_exc()
                return "Ekran analizi basarisiz."
        return _capture

    def _make_llm_callable(self) -> Callable[[str], str | None] | None:
        if self._jarvis is None:
            return None
        def _llm(prompt: str) -> str | None:
            try:
                provider = getattr(self._jarvis, "_provider", None)
                if provider is None:
                    return None
                if hasattr(provider, "generate_content"):
                    response = provider.generate_content(prompt)
                    return response.text if hasattr(response, "text") else str(response)
                if hasattr(provider, "_generate_text"):
                    return provider._generate_text(prompt)
                return None
            except Exception:
                import traceback; traceback.print_exc()
                return None
        return _llm

    def _make_evaluate_callable(self) -> Callable[[str, str], tuple[str, int] | None] | None:
        if self._jarvis is None:
            return None
        def _evaluate(task_desc: str, result: str) -> tuple[str, int] | None:
            try:
                provider = getattr(self._jarvis, "_provider", None)
                if provider is None:
                    return None
                eval_prompt = (
                    f"Görev: {task_desc}\n\n"
                    f"Sonuç: {result}\n\n"
                    "Bu görev başarıyla tamamlandı mı? Önce 'EVET' veya 'HAYIR' yaz, "
                    "sonra kısa bir açıklama yap."
                )
                if hasattr(provider, "generate_content"):
                    response = provider.generate_content(eval_prompt)
                    text = response.text if hasattr(response, "text") else str(response)
                elif hasattr(provider, "_generate_text"):
                    text = provider._generate_text(eval_prompt)
                else:
                    return None
                success = 1 if text.strip().upper().startswith("EVET") else 0
                return (text, success)
            except Exception:
                import traceback; traceback.print_exc()
                return None
        return _evaluate

    def _build_tool_handlers(self) -> dict[str, Callable[..., str]] | None:
        if self._jarvis is None:
            return None
        try:
            from core.tool_registry import TOOL_HANDLER_MAP
            handlers: dict[str, Callable[..., str]] = {}
            for tool_name, method_name in TOOL_HANDLER_MAP.items():
                handler = getattr(self._jarvis, method_name, None)
                if handler is not None:
                    handlers[tool_name] = handler
            return handlers
        except Exception:
            import traceback; traceback.print_exc()
            return None

    def _make_shell_executor(self) -> Callable[[str], str] | None:
        if self._jarvis is None:
            return None
        def _shell(command: str) -> str:
            try:
                from actions.shell import shell_run
                result = shell_run(command=command)
                return str(result)
            except Exception:
                import traceback; traceback.print_exc()
                return f"Shell komutu basarisiz: {command}"
        return _shell

    # ── Public API ──────────────────────────────────────────

    def execute_goal(self, goal_text: str) -> str:
        """Execute a goal in a background thread.

        Returns the goal_id immediately. The goal runs asynchronously.
        """
        # Check _user_initiated gate
        if self._jarvis is not None:
            user_initiated = getattr(self._jarvis, "_user_initiated", False)
            if not user_initiated:
                msg = "ACA: Kullanici etkilesimi olmadan agent calistirilamaz."
                self._log(msg)
                return msg

        goal_id = f"goal_{int(time.time())}"
        self._current_goal = AgentGoal(
            goal_id=goal_id,
            text=goal_text,
            status=GoalStatus.PENDING,
        )
        self._cancel_requested = False
        self._execution_history = []

        self._log(f"ACA: Hedef baslatiliyor — \"{goal_text}\" [ID: {goal_id}]")

        thread = threading.Thread(
            target=self._run_goal_loop,
            args=(goal_text, goal_id),
            daemon=True,
            name=f"aca-goal-{goal_id}",
        )
        thread.start()

        return "ACA: Hedef baslatildi."

    def cancel_goal(self) -> str:
        """Cancel the currently running goal."""
        self._cancel_requested = True
        if self._current_goal:
            self._current_goal.status = GoalStatus.CANCELLED
        self._log("ACA: Hedef iptal edildi.")
        return "ACA: Hedef iptal edildi."

    def approve_current_step(self) -> bool:
        """Approve the currently pending approval request (called from agent skill)."""
        pending = self.approval_manager.get_all_pending()
        if not pending:
            return False
        req = pending[0]
        return self.respond_to_approval(req.request_id, True)

    def reject_current_step(self) -> bool:
        """Reject the currently pending approval request (called from agent skill)."""
        pending = self.approval_manager.get_all_pending()
        if not pending:
            return False
        req = pending[0]
        return self.respond_to_approval(req.request_id, False)

    def respond_to_approval(self, request_id: str, approved: bool) -> bool:
        """Respond to a pending approval request. Thread-safe."""
        result = self.approval_manager.respond_to_approval(request_id, approved)
        if result:
            cv = self._request_id_to_cv.pop(request_id, None)
            if cv:
                self._approval_results[request_id] = approved
                cv.set()
        return result

    def get_goal_status(self) -> dict[str, Any] | None:
        """Get current goal status for UI rendering."""
        with self._lock:
            if self._current_goal is None:
                return None
            goal = self._current_goal
            graph = self._current_graph

            steps: list[dict[str, Any]] = []
            active_step = 0
            if graph is not None:
                for i, node in enumerate(graph.get_execution_order()):
                    steps.append({
                        "step_id": node.step_id,
                        "description": node.description,
                        "status": node.status.value,
                        "tool_name": node.tool_name,
                        "retry_count": node.retry_count,
                        "confidence": node.confidence,
                    })
                    if node.status == Status.IN_PROGRESS:
                        active_step = i

            pending_requests = self.approval_manager.get_all_pending()
            approval_data = None
            if pending_requests:
                req = pending_requests[0]
                approval_data = {
                    "request_id": req.request_id,
                    "tool_name": req.tool_name,
                    "params": req.params,
                    "risk_level": req.risk_level.value,
                    "description": req.description,
                    "step_id": req.step_id,
                }

            return {
                "goal_id": goal.goal_id,
                "goal_text": goal.text,
                "status": goal.status.value,
                "steps": steps,
                "active_step": active_step,
                "total_steps": goal.total_steps,
                "completed_steps": goal.completed_steps,
                "failed_steps": goal.failed_steps,
                "logs": list(self._log_history[-50:]),
                "approval_request": approval_data,
                "enabled": self._running or self._current_goal is not None,
                "approval_mode": self._approval_mode,
                "max_steps": self._max_steps,
                "max_duration": self._max_duration,
            }

    def set_approval_mode(self, enabled: bool):
        """Enable or disable approval mode for medium-risk actions."""
        self._approval_mode = enabled
        mode_name = "acik" if enabled else "kapali"
        self._log(f"ACA: Onay modu {mode_name}.")

    def is_approval_mode(self) -> bool:
        return self._approval_mode

    def get_config(self) -> dict:
        return {
            "max_steps": self._max_steps,
            "max_duration": self._max_duration,
        }

    def set_max_steps(self, value: int):
        self._max_steps = max(1, min(100, value))
        self._log(f"ACA: Maksimum adim {self._max_steps} olarak ayarlandi.")

    def set_max_duration(self, value: int):
        self._max_duration = max(10, min(3600, value))
        self._log(f"ACA: Maksimum sure {self._max_duration}s olarak ayarlandi.")

    def is_running(self) -> bool:
        return self._running

    def is_available(self) -> bool:
        """Return True if AgentManager is fully initialized and ready.
        
        All sub-components must exist and be configured with real references.
        """
        return (
            self.agent_memory is not None
            and self.observer is not None
            and self.planner is not None
            and self.executor is not None
            and self.reflection is not None
            and self.approval_manager is not None
        )

    # ── Internal execution loop ─────────────────────────────

    def _run_goal_loop(self, goal_text: str, goal_id: str):
        """Main execution loop: observe → plan → act → reflect."""
        self._running = True
        self._step_counter = 0
        self._start_time = time.time()

        try:
            if self._current_goal is None:
                return

            self._current_goal.status = GoalStatus.IN_PROGRESS
            self._current_goal.started_at = time.time()
            self._emit_update()

            # Step 1: PLAN
            self._log("ACA: Plan olusturuluyor...")
            graph = self.planner.create_plan(goal_text)
            self._current_graph = graph
            self._current_goal.total_steps = len(graph.nodes)
            self._log(f"ACA: Plan hazir — {len(graph.nodes)} adim.")

            try:
                _notify("ACA Görev", f"Basladi: {goal_text[:60]}", priority="normal")
            except Exception:
                pass

            self._emit_update()

            execution_order = graph.get_execution_order()

            # Step 2: EXECUTE each step with retry loop
            for node in execution_order:
                if self._cancel_requested:
                    self._current_goal.status = GoalStatus.CANCELLED
                    self._log("ACA: Hedef kullanici tarafindan iptal edildi.")
                    break

                # Check execution limits
                if not self._check_limits(node):
                    break

                node_retries = 0
                node_success = False
                max_retries = node.max_retries

                while node_retries <= max_retries and not node_success:
                    if self._cancel_requested:
                        break

                    if node_retries > 0:
                        self._log(f"ACA: ↻ [{node.step_id}] Yeniden deneniyor "
                                  f"({node_retries}/{max_retries})...")

                    node.status = Status.IN_PROGRESS
                    node.started_at = time.time()
                    self._emit_update()

                    self._log(f"ACA: [{node.step_id}] {node.description}")

                    # OBSERVE before
                    self._log("ACA: → Gozlem yapiliyor...")
                    world_before = self.observer.capture()
                    node.observation_before = world_before

                    # APPROVAL check (only on first attempt)
                    if node_retries == 0:
                        approval_ok = self._check_approval(node, goal_text)
                        if not approval_ok:
                            node.status = Status.CANCELLED
                            self._log(f"ACA: [{node.step_id}] Kullanici onayi reddetti.")
                            self._current_goal.status = GoalStatus.CANCELLED
                            break

                    # ACT
                    self._log(f"ACA: → Calistiriliyor: {node.tool_name or node.action_type.value}")
                    step_result = self.executor.execute_step(node, world_before)
                    node.result = step_result.get("result", "")
                    node.retry_count = node_retries

                    # TRACK execution history for loop detection
                    self._execution_history.append({
                        "step_id": node.step_id,
                        "tool_name": node.tool_name,
                        "params": dict(node.params),
                        "success": step_result.get("success", False),
                    })

                    # OBSERVE after
                    world_after = self.observer.capture()
                    node.observation_after = world_after

                    # REFLECT
                    reflection = self.reflection.evaluate_step(
                        node, world_before, world_after, node.result,
                    )
                    node.reflection = reflection.analysis
                    node.confidence = reflection.confidence

                    if reflection.success:
                        node.status = Status.SUCCESS
                        self._current_goal.completed_steps += 1
                        node_success = True
                        self._log(f"ACA: ✅ [{node.step_id}] Basarili "
                                  f"(guven: {reflection.confidence:.1%})")
                    else:
                        node.status = Status.FAILED
                        node_retries += 1
                        if node_retries <= max_retries:
                            node.status = Status.PENDING
                        self._log(f"ACA: ❌ [{node.step_id}] Basarisiz "
                                  f"(deneme {node_retries}/{max_retries}) — "
                                  f"{reflection.analysis[:100]}")

                if self._cancel_requested:
                    break

                # Loop detection: check after each step
                if self.reflection.detect_loop(self._execution_history):
                    self._log(f"ACA: 🔄 Döngü tespit edildi — [{node.step_id}] "
                              f"ayni arac tekrarlaniyor.")
                    node.status = Status.FAILED
                    node.reflection = "Dongu tespit edildi"
                    self._current_goal.failed_steps += 1
                    # Attempt replan
                    self._log("ACA: Plan yeniden olusturuluyor...")
                    new_graph = self.planner.replan(node, world_after, self._current_graph)
                    self._current_graph = new_graph
                    execution_order = new_graph.get_execution_order()
                    # Continue with new plan from the first new node
                    self._step_counter += 1
                    self._emit_update()
                    continue

                self._step_counter += 1
                self._emit_update()

            # Handle stuck goals: all remaining nodes failed or incomplete
            if self._current_graph and self._current_graph.remaining_nodes():
                failed = self._current_graph.failed_nodes()
                if len(failed) > 0 and len(failed) == len(self._current_graph.remaining_nodes()) + len(failed) - len([n for n in self._current_graph.nodes.values() if n.status == Status.SUCCESS]):
                    self._log(f"ACA: Hedef tamamlanamadi. {len(failed)} adim basarisiz.")
                    self._current_goal.status = GoalStatus.FAILED
                    self._current_goal.result = f"Hedef tamamlanamadi. {len(failed)} basarisiz adim."
                    self._emit_update()

            # Step 3: FINALIZE
            self._finalize_goal()

        except Exception:
            traceback.print_exc()
            if self._current_goal:
                self._current_goal.status = GoalStatus.FAILED
                self._current_goal.result = f"Beklenmeyen hata: {traceback.format_exc()}"
            self._log("ACA: ❌ Hedef sirasinda hata olustu.")
        finally:
            self._running = False
            self._emit_update()
            self._save_session()

    def _check_limits(self, node: TaskNode) -> bool:
        """Check execution limits. Returns False if limit exceeded."""
        if self._step_counter >= self._max_steps:
            self._log(
                f"ACA: ⛔ Adim siniri asildi ({self._max_steps}). "
                f"Hedef durduruldu."
            )
            self._current_goal.status = GoalStatus.CANCELLED
            return False

        elapsed = time.time() - self._start_time
        if elapsed > self._max_duration:
            self._log(
                f"ACA: ⛔ Sure siniri asildi ({self._max_duration}s). "
                f"Hedef durduruldu."
            )
            self._current_goal.status = GoalStatus.CANCELLED
            return False

        return True

    def _check_approval(self, node: TaskNode, goal_text: str) -> bool:
        """Check if step needs approval. Blocks until user responds if needed.

        Returns True if execution should proceed, False if denied.
        """
        risk = self.approval_manager.classify_action(
            node.tool_name, node.params,
        )

        needs_approval = (risk == RiskLevel.HIGH
                          or (risk == RiskLevel.MEDIUM and self._approval_mode))

        if not needs_approval:
            return True

        req = self.approval_manager.request_approval(
            step_id=node.step_id,
            goal_text=goal_text,
            tool_name=node.tool_name,
            params=node.params,
            risk_level=risk,
            description=node.description,
        )

        # Create event for this request
        cv = threading.Event()
        self._request_id_to_cv[req.request_id] = cv

        msg = (
            f"ACA: 🛑 Onay gerekiyor — {node.description}\n"
            f"    Arac: {node.tool_name}\n"
            f"    Risk: {risk.value}\n"
            f"    Istek: {req.request_id}"
        )
        self._log(msg)

        # Notify UI
        self._emit_update()

        # Wait for approval with timeout (2 minutes)
        approved = cv.wait(timeout=120)
        if not approved:
            self._log("ACA: ⏰ Onay zamani asildi, adim gecildi.")
            return False

        result = self._approval_results.pop(req.request_id, False)
        if result:
            self._log(f"ACA: ✅ Onaylandi — {node.tool_name}")
            return True
        else:
            self._log(f"ACA: ❌ Reddedildi — {node.tool_name}")
            return False

    def _finalize_goal(self):
        """Finalize goal execution and log summary."""
        if self._current_goal is None:
            return

        goal = self._current_goal

        # Determine overall status
        if goal.status != GoalStatus.CANCELLED:
            failed = self._current_graph.failed_nodes() if self._current_graph else []
            if failed:
                goal.status = GoalStatus.FAILED
                goal.result = (
                    f"Hedef tamamlanamadi. "
                    f"{len(failed)} adim basarisiz."
                )
            else:
                remaining = self._current_graph.remaining_nodes() if self._current_graph else []
                if not remaining:
                    goal.status = GoalStatus.COMPLETED
                    goal.result = "Hedef basariyla tamamlandi."
                else:
                    goal.status = GoalStatus.CANCELLED
                    goal.result = f"Hedef yarida kaldi ({len(remaining)} adim kaldi)."

        goal.completed_at = time.time()

        # Save workflow template on successful completion (US5)
        if goal.status == GoalStatus.COMPLETED and self._current_graph is not None:
            try:
                self._save_workflow_template(goal)
            except Exception:
                traceback.print_exc()

        summary = (
            f"ACA: {'🏁' if goal.status == GoalStatus.COMPLETED else '⛔'} "
            f"Hedef {goal.status.value} — "
            f"{goal.completed_steps}/{goal.total_steps} adim tamam, "
            f"{goal.failed_steps} basarisiz."
        )
        self._log(summary)

        try:
            status_emoji = "🏁" if goal.status == GoalStatus.COMPLETED else "⛔"
            _notify("ACA Görev", f"{status_emoji} {goal.status.value}: {goal.text[:50]}",
                    priority="normal")
        except Exception:
            pass

        if self._jarvis is not None:
            setattr(self._jarvis, "_user_initiated", False)

    def _save_workflow_template(self, goal: AgentGoal):
        """Save a reusable workflow template on successful completion (US5)."""
        if self._current_graph is None:
            return

        template_id = f"tpl_{int(time.time())}"
        graph = self._current_graph

        # Build keyword set from goal text
        normalized = self.agent_memory._normalize_goal_text(goal.text)
        keywords = list(set(normalized.split())) if normalized else []

        # Extract state-independent step data (strip observation data)
        steps = []
        for node in graph.get_execution_order():
            steps.append({
                "step_id": node.step_id,
                "description": node.description,
                "action_type": node.action_type.value,
                "tool_name": node.tool_name,
                "params": dict(node.params),
                "dependencies": list(node.dependencies),
            })

        template_data = {
            "template_id": template_id,
            "intent": goal.text,
            "normalized_intent": normalized,
            "keywords": keywords,
            "steps": steps,
            "edges": list(graph.edges),
            "created_at": time.time(),
            "completion_count": 1,
        }
        self.agent_memory.save_template(template_id, template_data)
        self._log(f"ACA: 📋 Is akisi kaydedildi ({template_id}) — {len(steps)} adim.")

    def _save_session(self):
        """Save the full execution session to memory."""
        if self._current_goal is None:
            return

        try:
            session_id = f"session_{int(time.time())}"
            session_data = {
                "session_id": session_id,
                "goal": self._current_goal.to_dict(),
                "graph": self._current_graph.to_dict() if self._current_graph else {},
                "execution_history": self._execution_history,
                "completed_at": time.time(),
            }
            self.agent_memory.save_session(session_id, session_data)
            self._log(f"ACA: Oturum kaydedildi ({session_id}).")
        except Exception:
            traceback.print_exc()

    # ── Helpers ─────────────────────────────────────────────

    def _log(self, message: str):
        """Write a log entry via jarvis and optional callback."""
        self._log_history.append(message)
        if self._jarvis is not None:
            try:
                self._jarvis.write_log(message)
            except Exception:
                pass

    def _emit_update(self):
        """Emit state update via on_state_update callback."""
        if self.on_state_update:
            try:
                state = self.get_goal_status()
                if state:
                    self.on_state_update(state)
            except Exception:
                traceback.print_exc()
