"""
ACA Subsystem test suite
Adler ASİ tarafından yapılmıştır
"""
from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from aca_core import (
    ActionType, AgentMemory, ApprovalManager, ApprovalRequest,
    ApprovalStatus, Executor, Observer, Planner, Reflection,
    RiskLevel, Status, TaskGraph, TaskNode,
)
from core.agent.agent_manager import AgentManager, AgentGoal


class TestTaskNode(unittest.TestCase):
    """TaskNode dataclass tests."""

    def test_default_status_is_pending(self):
        node = TaskNode(step_id="s1", description="test", action_type=ActionType.TOOL)
        self.assertEqual(node.status, Status.PENDING)

    def test_to_dict_roundtrip(self):
        node = TaskNode(step_id="s1", description="test", action_type=ActionType.SHELL,
                         tool_name="shell_run", params={"command": "echo hi"})
        d = node.to_dict()
        restored = TaskNode.from_dict(d)
        self.assertEqual(restored.step_id, "s1")
        self.assertEqual(restored.action_type, ActionType.SHELL)
        self.assertEqual(restored.params, {"command": "echo hi"})

    def test_serialization_includes_all_fields(self):
        node = TaskNode(step_id="s1", description="test", action_type=ActionType.INPUT,
                         tool_name="pyautogui", params={"keys": "hello"})
        d = node.to_dict()
        for key in ("step_id", "description", "action_type", "tool_name", "params",
                     "status", "retry_count", "confidence"):
            self.assertIn(key, d)


class TestTaskGraph(unittest.TestCase):
    """TaskGraph DAG tests."""

    def test_empty_graph(self):
        g = TaskGraph(graph_id="g1")
        self.assertEqual(len(g.get_execution_order()), 0)

    def test_single_node_order(self):
        g = TaskGraph()
        g.add_node(TaskNode(step_id="s1", description="step 1", action_type=ActionType.TOOL))
        order = g.get_execution_order()
        self.assertEqual(len(order), 1)
        self.assertEqual(order[0].step_id, "s1")

    def test_topological_order(self):
        g = TaskGraph()
        g.add_node(TaskNode(step_id="s1", description="first", action_type=ActionType.TOOL))
        g.add_node(TaskNode(step_id="s2", description="second", action_type=ActionType.TOOL, dependencies=["s1"]))
        g.add_node(TaskNode(step_id="s3", description="third", action_type=ActionType.TOOL, dependencies=["s2"]))
        g.add_edge("s1", "s2")
        g.add_edge("s2", "s3")
        order = g.get_execution_order()
        self.assertEqual([n.step_id for n in order], ["s1", "s2", "s3"])

    def test_cycle_detection(self):
        g = TaskGraph()
        g.add_node(TaskNode(step_id="s1", description="a", action_type=ActionType.TOOL))
        g.add_node(TaskNode(step_id="s2", description="b", action_type=ActionType.TOOL))
        g.add_edge("s1", "s2")
        g.add_edge("s2", "s1")
        self.assertTrue(g.has_cycle())

    def test_roots_and_leaves(self):
        g = TaskGraph()
        g.add_node(TaskNode(step_id="s1", description="root", action_type=ActionType.TOOL))
        g.add_node(TaskNode(step_id="s2", description="mid", action_type=ActionType.TOOL))
        g.add_node(TaskNode(step_id="s3", description="leaf", action_type=ActionType.TOOL))
        g.add_edge("s1", "s2")
        g.add_edge("s2", "s3")
        roots = g.get_roots()
        leaves = g.get_leaves()
        self.assertEqual([n.step_id for n in roots], ["s1"])
        self.assertEqual([n.step_id for n in leaves], ["s3"])

    def test_remaining_nodes(self):
        g = TaskGraph()
        n1 = TaskNode(step_id="s1", description="done", action_type=ActionType.TOOL, status=Status.SUCCESS)
        n2 = TaskNode(step_id="s2", description="pending", action_type=ActionType.TOOL)
        n3 = TaskNode(step_id="s3", description="failed", action_type=ActionType.TOOL, status=Status.FAILED)
        g.add_node(n1)
        g.add_node(n2)
        g.add_node(n3)
        remaining = g.remaining_nodes()
        self.assertEqual([n.step_id for n in remaining], ["s2"])

    def test_json_roundtrip(self):
        g = TaskGraph(graph_id="g_test", goal_id="goal_test")
        g.add_node(TaskNode(step_id="s1", description="first", action_type=ActionType.TOOL,
                             tool_name="open_app", params={"app_name": "notepad"}))
        g.add_node(TaskNode(step_id="s2", description="second", action_type=ActionType.INPUT,
                             tool_name="pyautogui", params={"keys": "hello"}))
        g.add_edge("s1", "s2")
        raw = g.to_json()
        restored = TaskGraph.from_json(raw)
        self.assertEqual(restored.graph_id, "g_test")
        self.assertEqual(restored.goal_id, "goal_test")
        self.assertEqual(len(restored.nodes), 2)
        self.assertEqual(len(restored.edges), 1)

    def test_max_20_steps_limit(self):
        """Validation: planner should enforce max 20 steps."""
        g = TaskGraph()
        for i in range(20):
            g.add_node(TaskNode(step_id=f"s{i}", description=f"step {i}", action_type=ActionType.TOOL))
        order = g.get_execution_order()
        self.assertEqual(len(order), 20)


# ── Observer ─────────────────────────────────────────────

class TestObserver(unittest.TestCase):
    """Observer: desktop state capture, screen/process/window."""

    def test_capture_returns_expected_keys(self):
        obs = Observer()
        state = obs.capture()
        for key in ("timestamp", "screen_text", "active_window_title",
                     "running_processes", "recent_files"):
            self.assertIn(key, state)

    def test_capture_screen_text_fallback_on_import_error(self):
        obs = Observer()
        text = obs._do_capture_screen()
        self.assertIsInstance(text, str)
        # If screen_vision not installed, returns fallback message
        self.assertGreater(len(text), 0)

    def test_capture_processes_returns_list(self):
        obs = Observer()
        procs = obs._capture_running_processes()
        self.assertIsInstance(procs, list)
        # All items have expected keys
        for p in procs:
            for key in ("pid", "name", "cpu", "memory"):
                self.assertIn(key, p)

    def test_last_capture_stores_previous_state(self):
        obs = Observer()
        state = obs.capture()
        self.assertEqual(obs.last_capture(), state)

    def test_active_window_title_returns_string(self):
        obs = Observer()
        title = obs._capture_active_window_title()
        self.assertIsInstance(title, str)


# ── Planner ──────────────────────────────────────────────

class TestPlanner(unittest.TestCase):
    """Planner: goal decomposition, fallback, validation."""

    def test_create_plan_no_jarvis_falls_back(self):
        p = Planner()
        graph = p.create_plan("Notepad ac")
        self.assertIsInstance(graph, TaskGraph)
        # Fallback plan has at least 1 step
        self.assertGreaterEqual(len(graph.nodes), 1)

    def test_fallback_plan_returns_valid_graph(self):
        p = Planner()
        graph = p._fallback_plan("test goal")
        self.assertIsInstance(graph, TaskGraph)
        self.assertGreaterEqual(len(graph.nodes), 1)
        # Fallback step uses analyze_screen tool
        first = graph.get_execution_order()[0]
        self.assertEqual(first.tool_name, "analyze_screen")

    def test_validate_graph_returns_true_for_valid(self):
        p = Planner()
        g = TaskGraph(graph_id="test", goal_id="test")
        g.add_node(TaskNode(step_id="s1", description="a",
                             action_type=ActionType.TOOL, tool_name="open_app"))
        self.assertTrue(p._validate_graph(g))

    def test_validate_graph_empty_returns_false(self):
        p = Planner()
        g = TaskGraph(graph_id="test", goal_id="test")
        self.assertFalse(p._validate_graph(g))

    def test_validate_graph_over_20_steps_returns_false(self):
        p = Planner()
        g = TaskGraph(graph_id="test", goal_id="test")
        for i in range(21):
            g.add_node(TaskNode(step_id=f"s{i}", description=f"step {i}",
                                 action_type=ActionType.TOOL))
        self.assertFalse(p._validate_graph(g))

    def test_parse_llm_response_valid_json(self):
        p = Planner()
        json_text = '{"steps": [{"step_id": "s1", "description": "test", "action_type": "tool", "tool_name": "open_app", "params": {}, "dependencies": []}]}'
        graph = p._parse_llm_response(json_text, "test goal")
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(graph.nodes["s1"].tool_name, "open_app")

    def test_parse_llm_response_with_markdown_fence(self):
        p = Planner()
        md_text = '```json\n{"steps": [{"step_id": "s1", "description": "test", "action_type": "shell", "tool_name": "shell_run", "params": {"command": "echo hi"}, "dependencies": []}]}\n```'
        graph = p._parse_llm_response(md_text, "test goal")
        self.assertEqual(len(graph.nodes), 1)
        self.assertEqual(graph.nodes["s1"].action_type, ActionType.SHELL)

    def test_replan_no_jarvis_returns_retry_graph(self):
        p = Planner()
        failed = TaskNode(step_id="s1", description="fail",
                           action_type=ActionType.TOOL, result="error")
        prev = TaskGraph(graph_id="g", goal_id="goal")
        prev.add_node(failed)
        graph = p.replan(failed, {}, prev)
        self.assertIsInstance(graph, TaskGraph)
        self.assertGreaterEqual(len(graph.nodes), 1)

    def test_try_cached_workflow_no_memory_returns_none(self):
        p = Planner()
        self.assertIsNone(p._try_cached_workflow("test"))

    def test_replan_returns_valid_graph(self):
        p = Planner()
        failed = TaskNode(step_id="s1", description="test fail",
                           action_type=ActionType.TOOL)
        prev = TaskGraph(graph_id="g", goal_id="goal")
        prev.add_node(failed)
        graph = p.replan(failed, {}, prev)
        self.assertTrue(len(graph.nodes) >= 1)


# ── Executor ─────────────────────────────────────────────

class TestExecutor(unittest.TestCase):
    """Executor: step dispatch, timeout, action routing."""

    def test_execute_step_observe_returns_immediately(self):
        ex = Executor()
        node = TaskNode(step_id="s1", description="observe",
                         action_type=ActionType.OBSERVE)
        result = ex.execute_step(node, {})
        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "Gozlendi.")

    def test_execute_step_wait_sleeps(self):
        ex = Executor()
        node = TaskNode(step_id="s1", description="wait 0.01s",
                         action_type=ActionType.WAIT,
                         params={"seconds": 0.01})
        t0 = time.time()
        result = ex.execute_step(node, {})
        elapsed = time.time() - t0
        self.assertTrue(result["success"])
        self.assertGreaterEqual(elapsed, 0.005)

    def test_execute_step_unknown_action_returns_error(self):
        ex = Executor()
        node = TaskNode(step_id="s1", description="bad",
                         action_type=ActionType.INPUT,
                         tool_name="nonexistent", params={"action": "invalid"})
        result = ex.execute_step(node, {})
        # Should not crash - pyautogui import might fail gracefully
        self.assertIn("success", result)

    def test_execute_tool_no_handler_returns_error(self):
        ex = Executor()
        result = ex._execute_tool("nonexistent_tool", {})
        self.assertIn("Arac", result)

    def test_execute_shell_empty_command(self):
        ex = Executor()
        result = ex._execute_shell({"command": ""})
        self.assertEqual(result, "Komut belirtilmedi.")

    def test_execute_pyautogui_unknown_action(self):
        ex = Executor()
        result = ex._execute_pyautogui({"action": "nonexistent", "text": ""})
        self.assertIn("Bilinmeyen", result)

    def test_pyautogui_import_fallback(self):
        ex = Executor()
        # Simulate pyautogui missing by calling with action that requires it
        result = ex._execute_pyautogui({"action": "click"})
        # Should not crash - either runs or returns error string
        self.assertIsInstance(result, str)


# ── Reflection ───────────────────────────────────────────

class TestReflection(unittest.TestCase):
    """Reflection: heuristic evaluation, loop detection."""

    def test_heuristic_error_marker_returns_failure(self):
        ref = Reflection()
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        result = ref._heuristic_evaluate(node, "Hata: dosya bulunamadi")
        self.assertFalse(result.success)
        self.assertAlmostEqual(result.confidence, 0.7)

    def test_heuristic_success_marker_returns_success(self):
        ref = Reflection()
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        result = ref._heuristic_evaluate(node, "basarili: islem tamamlandi")
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.confidence, 0.8)

    def test_heuristic_neutral_with_result_returns_success(self):
        ref = Reflection()
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        result = ref._heuristic_evaluate(node, "Komut calisti, cikti: OK")
        self.assertTrue(result.success)
        self.assertAlmostEqual(result.confidence, 0.5)

    def test_heuristic_empty_result_returns_failure(self):
        ref = Reflection()
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        result = ref._heuristic_evaluate(node, "")
        self.assertFalse(result.success)
        self.assertAlmostEqual(result.confidence, 0.4)

    def test_heuristic_conflicting_markers_returns_failure(self):
        ref = Reflection()
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        result = ref._heuristic_evaluate(node, "basarili Hata")
        self.assertFalse(result.success)
        self.assertAlmostEqual(result.confidence, 0.3)

    def test_detect_loop_less_than_3_returns_false(self):
        ref = Reflection()
        history = [
            {"tool_name": "open_app", "params": {}, "step_id": "s1"},
            {"tool_name": "open_app", "params": {}, "step_id": "s2"},
        ]
        self.assertFalse(ref.detect_loop(history))

    def test_detect_loop_3_repeated_detected(self):
        ref = Reflection()
        history = [
            {"tool_name": "open_app", "params": {"app": "x"}, "step_id": "s1"},
            {"tool_name": "open_app", "params": {"app": "x"}, "step_id": "s2"},
            {"tool_name": "open_app", "params": {"app": "x"}, "step_id": "s3"},
        ]
        self.assertTrue(ref.detect_loop(history))

    def test_detect_loop_same_tool_4_times(self):
        ref = Reflection()
        history = [
            {"tool_name": "shell_run", "params": {}, "step_id": "s1"},
            {"tool_name": "shell_run", "params": {}, "step_id": "s2"},
            {"tool_name": "shell_run", "params": {}, "step_id": "s3"},
            {"tool_name": "shell_run", "params": {}, "step_id": "s4"},
        ]
        self.assertTrue(ref.detect_loop(history))

    def test_detect_loop_diff_tools_no_loop(self):
        ref = Reflection()
        history = [
            {"tool_name": "open_app", "params": {}, "step_id": "s1"},
            {"tool_name": "shell_run", "params": {}, "step_id": "s2"},
            {"tool_name": "analyze_screen", "params": {}, "step_id": "s3"},
            {"tool_name": "open_app", "params": {}, "step_id": "s4"},
        ]
        self.assertFalse(ref.detect_loop(history))


# ── Approval Manager ─────────────────────────────────────

class TestApprovalManager(unittest.TestCase):
    """ApprovalManager: risk classification, approval flow."""

    def setUp(self):
        self.am = ApprovalManager()

    def test_classify_high_risk_tool(self):
        level = self.am.classify_action("kill_process", {})
        self.assertEqual(level, RiskLevel.HIGH)

    def test_classify_medium_risk_tool(self):
        level = self.am.classify_action("shell_run", {"command": "echo hello"})
        self.assertEqual(level, RiskLevel.MEDIUM)

    def test_classify_shell_write_intent_high_risk(self):
        level = self.am.classify_action("shell_run", {"command": "rm -rf /tmp/test"})
        self.assertEqual(level, RiskLevel.HIGH)

    def test_classify_low_risk_tool(self):
        level = self.am.classify_action("open_app", {"app_name": "notepad"})
        self.assertEqual(level, RiskLevel.LOW)

    def test_classify_browser_download_medium(self):
        level = self.am.classify_action("browser_control", {"action": "download", "url": "https://example.com/file.exe"})
        self.assertEqual(level, RiskLevel.MEDIUM)

    def test_classify_browser_navigate_low(self):
        level = self.am.classify_action("browser_control", {"action": "navigate", "url": "https://example.com"})
        self.assertEqual(level, RiskLevel.LOW)

    def test_request_and_approve(self):
        req = self.am.request_approval("s1", "test goal", "shell_run",
                                        {"command": "del file"}, RiskLevel.HIGH,
                                        "test approval")
        self.assertEqual(req.status, ApprovalStatus.PENDING)
        self.assertTrue(self.am.respond_to_approval(req.request_id, True))
        self.assertEqual(req.status, ApprovalStatus.APPROVED)

    def test_request_and_deny(self):
        req = self.am.request_approval("s1", "test goal", "shell_run",
                                        {"command": "rm file"}, RiskLevel.HIGH)
        self.assertTrue(self.am.respond_to_approval(req.request_id, False))
        self.assertEqual(req.status, ApprovalStatus.DENIED)

    def test_respond_twice_returns_false(self):
        req = self.am.request_approval("s1", "test", "shell_run",
                                        {}, RiskLevel.HIGH)
        self.assertTrue(self.am.respond_to_approval(req.request_id, True))
        self.assertFalse(self.am.respond_to_approval(req.request_id, True))

    def test_respond_unknown_id_returns_false(self):
        self.assertFalse(self.am.respond_to_approval("nonexistent", True))

    def test_has_pending_true(self):
        self.am.request_approval("s1", "test", "shell_run",
                                  {}, RiskLevel.HIGH)
        self.assertTrue(self.am.has_pending())

    def test_has_pending_false(self):
        self.assertFalse(self.am.has_pending())

    def test_get_all_pending(self):
        self.am.request_approval("s1", "test", "shell_run",
                                  {}, RiskLevel.HIGH)
        pending = self.am.get_all_pending()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].status, ApprovalStatus.PENDING)

    def test_expire_old_requests(self):
        req = self.am.request_approval("s1", "test", "shell_run",
                                        {}, RiskLevel.HIGH)
        req.created_at = time.time() - 200  # older than 120s default
        self.am.expire_old_requests()
        self.assertEqual(req.status, ApprovalStatus.EXPIRED)

    def test_get_request_details_returns_string(self):
        req = self.am.request_approval("s1", "test goal", "shell_run",
                                        {"command": "echo hi"}, RiskLevel.MEDIUM)
        details = self.am.get_request_details(req.request_id)
        self.assertIn("ONAY GEREKIYOR", details)
        self.assertIn("shell_run", details)

    def test_get_request_details_unknown(self):
        details = self.am.get_request_details("nonexistent")
        self.assertIn("bulunamadi", details)

    def test_is_high_risk(self):
        self.assertTrue(self.am.is_high_risk("kill_process"))
        self.assertFalse(self.am.is_high_risk("open_app"))

    def test_approval_request_to_dict_roundtrip(self):
        req = self.am.request_approval("s1", "test", "shell_run",
                                        {"cmd": "test"}, RiskLevel.HIGH)
        d = req.to_dict()
        restored = ApprovalRequest.from_dict(d)
        self.assertEqual(restored.request_id, req.request_id)
        self.assertEqual(restored.risk_level, req.risk_level)
        self.assertEqual(restored.status, req.status)


# ── Agent Memory ─────────────────────────────────────────

class TestAgentMemory(unittest.TestCase):
    """AgentMemory: CRUD for goals, sessions, templates."""

    def setUp(self):
        # Use temp directory to avoid polluting real memory
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="aca_test_"))
        self.mem = AgentMemory(base_path=self._tmp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def test_save_and_load_goal(self):
        self.mem.save_goal("test_goal", {"text": "test", "status": "completed"})
        loaded = self.mem.load_goal("test_goal")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["text"], "test")
        self.assertEqual(loaded["status"], "completed")

    def test_list_goals(self):
        self.mem.save_goal("g1", {"text": "goal 1", "status": "completed"})
        self.mem.save_goal("g2", {"text": "goal 2", "status": "pending"})
        goals = self.mem.list_goals(limit=5)
        self.assertGreaterEqual(len(goals), 2)

    def test_save_and_load_session(self):
        self.mem.save_session("sess_1", {"goal_id": "g1", "status": "done"})
        loaded = self.mem.load_session("sess_1")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["goal_id"], "g1")

    def test_save_and_load_template(self):
        tpl = {
            "intent": "open notepad",
            "steps": [
                {"step_id": "s1", "description": "open",
                 "action_type": "tool", "tool_name": "open_app", "params": {}, "dependencies": []}
            ],
            "edges": [],
            "keywords": ["notepad", "open"],
        }
        self.mem.save_template("tpl_1", tpl)
        loaded = self.mem.load_template("tpl_1")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded["intent"], "open notepad")

    def test_find_templates_by_keyword_overlap(self):
        tpl = {
            "intent": "notepad ac",
            "steps": [],
            "edges": [],
            "keywords": ["notepad", "ac"],
        }
        self.mem.save_template("tpl_match", tpl)
        results = self.mem.find_templates("notepad ac")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["template_id"], "tpl_match")

    def test_find_templates_no_match(self):
        tpl = {
            "intent": "browser kapat",
            "steps": [],
            "edges": [],
            "keywords": ["browser", "kapat"],
        }
        self.mem.save_template("tpl_browser_kapat", tpl)
        results = self.mem.find_templates("notepad ac")
        self.assertEqual(len(results), 0)

    def test_save_current_goal(self):
        self.mem.save_current_goal("active_goal")
        loaded = self.mem.load_current_goal()
        self.assertEqual(loaded, "active_goal")

    def test_clear_current_goal(self):
        self.mem.save_current_goal("some_goal")
        self.mem.save_current_goal(None)
        loaded = self.mem.load_current_goal()
        self.assertIsNone(loaded)

    def test_normalize_goal_text(self):
        result = AgentMemory._normalize_goal_text("Bir test ve hedef")
        # Stopwords removed, normalized
        self.assertNotIn("bir", result)
        self.assertNotIn("ve", result)
        self.assertIn("test", result)

    def test_compute_similarity_identical(self):
        sim = AgentMemory.compute_similarity("notepad ac", "notepad ac")
        self.assertAlmostEqual(sim, 1.0)

    def test_compute_similarity_no_overlap(self):
        sim = AgentMemory.compute_similarity("notepad ac", "browser kapat")
        self.assertEqual(sim, 0.0)

    def test_compute_similarity_partial(self):
        sim = AgentMemory.compute_similarity("notepad ac ve yazi yaz",
                                              "notepad ac")
        self.assertGreater(sim, 0.0)
        self.assertLess(sim, 1.0)

    def test_compute_similarity_empty(self):
        sim = AgentMemory.compute_similarity("", "something")
        self.assertEqual(sim, 0.0)


# ── Agent Manager ────────────────────────────────────────

class TestAgentManager(unittest.TestCase):
    """AgentManager: lifecycle, limits, state."""

    def test_init_creates_components(self):
        am = AgentManager()
        self.assertIsNotNone(am.planner)
        self.assertIsNotNone(am.executor)
        self.assertIsNotNone(am.observer)
        self.assertIsNotNone(am.approval_manager)
        self.assertIsNotNone(am.agent_memory)

    def test_is_running_returns_false_initially(self):
        am = AgentManager()
        self.assertFalse(am.is_running())

    def test_get_goal_status_returns_none_when_idle(self):
        am = AgentManager()
        self.assertIsNone(am.get_goal_status())

    def test_check_limits_under_limit_returns_true(self):
        am = AgentManager()
        am._step_counter = 5
        am._start_time = time.time()
        am._current_goal = AgentGoal(goal_id="g1", text="test")
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        self.assertTrue(am._check_limits(node))

    def test_check_limits_over_steps_returns_false(self):
        am = AgentManager()
        am._max_steps = 10
        am._step_counter = 10
        am._current_goal = AgentGoal(goal_id="g1", text="test")
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        self.assertFalse(am._check_limits(node))

    def test_check_limits_over_duration_returns_false(self):
        am = AgentManager()
        am._max_duration = 1
        am._start_time = time.time() - 10
        am._step_counter = 0
        am._current_goal = AgentGoal(goal_id="g1", text="test")
        node = TaskNode(step_id="s1", description="test",
                         action_type=ActionType.TOOL)
        self.assertFalse(am._check_limits(node))

    def test_cancel_goal_returns_string(self):
        am = AgentManager()
        result = am.cancel_goal()
        self.assertIsInstance(result, str)

    def test_respond_to_approval_when_no_pending(self):
        am = AgentManager()
        # Should not crash and return False when no pending request
        result = am.respond_to_approval("nonexistent", True)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
