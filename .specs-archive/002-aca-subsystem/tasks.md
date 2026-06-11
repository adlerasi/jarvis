---

description: "Task list for ACA Subsystem implementation"

---

# Tasks: ACA Subsystem

**Input**: Design documents from `specs/002-aca-subsystem/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, quickstart.md

**Tests**: Not explicitly requested in spec — implementation-only tasks. Tests will be added during implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `core/`, `tests/`, `skills/`, `ui/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the ACA package structure and shared data types

- [ ] T001 Create `core/agent/__init__.py` with public API exports (AgentManager, Planner, Executor, Observer, Reflection, TaskGraph, ApprovalManager, AgentMemory)
- [ ] T002 [P] Create `core/agent/task_graph.py` with TaskNode dataclass (step_id, description, action_type enum, tool_name, params, dependencies, status enum, retry_count, confidence, observation_before/after, result, reflection, timestamps) and TaskGraph class (graph_id, goal_id, nodes list, edges list, add_node, add_edge, get_execution_order, to_dict/from_dict serialization)
- [ ] T003 [P] Create `memory/agent/index.json` initial file with empty JSON object `{}` and `memory/agent/goals/`, `memory/agent/sessions/`, `memory/agent/templates/` directories with `.gitkeep`
- [ ] T004 [P] Create `tests/test_aca_subsystem.py` with test class skeleton and placeholder test method for each user story
- [ ] T005 Add `pyautogui` to `requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that ALL user stories depend on

- [ ] T006 Create `core/agent/observer.py` — `Observer` class that wraps `analyze_screen()` (via jarvis reference), captures active window title (via `wmctrl`-like fallback or platform API), tracks top-10 processes via `psutil`, and returns `WorldState` dict (`{"timestamp", "screen_text", "active_window_title", "running_processes", "recent_files"}`). Thread-safe `capture() -> dict` method.
- [ ] T007 [P] Create `core/agent/agent_memory.py` — `AgentMemory` class using existing `memory/memory_manager.py` patterns. Methods: `save_goal(AgentGoal)`, `load_goal(goal_id)`, `save_session(AgentSession)`, `load_session(session_id)`, `save_template(WorkflowTemplate)`, `find_templates(intent_hash)`, `save_current_goal(goal_id_or_None)`, `load_current_goal()`. Stores data in `memory/agent/` directory.
- [ ] T008 [P] Create `core/agent/planner.py` — `Planner` class that receives goal text, calls existing LLM provider (via jarvis ref) with structured prompt for task decomposition, builds TaskGraph from LLM response, validates graph (no cycles, all deps exist, max 20 steps). Methods: `create_plan(goal_text) -> TaskGraph`, `replan(failed_node, world_state, previous_graph) -> TaskGraph`.
- [ ] T009 [P] Create `core/agent/executor.py` — `Executor` class that maps action_type to implementation: `tool` actions dispatch via jarvis tool registry handler map, `shell` actions go through `actions/shell.shell_run()`, `input` actions use `pyautogui` (click, type, key combo, drag). Methods: `execute_step(node, world_state) -> StepResult`, `execute_tool(tool_name, params) -> str`, `execute_pyautogui(action_type, params) -> str`. Includes 30s per-step timeout.
- [ ] T010 Create `core/agent/approval_manager.py` — `ApprovalManager` class with static risk table (low/medium/high). Methods: `classify_action(tool_name, params) -> risk_level`, `request_approval(step, goal) -> ApprovalRequest`, `respond_to_approval(request_id, approved) -> bool`, `is_high_risk(tool_name) -> bool`. High-risk actions: `kill_process`, `cleanup_folder`, `cleanup_recycle_bin`, `control_service`, `shell_run` with write intent. Medium-risk (require approval only in approval mode): `shell_run`, `browser_control` with download, `set_process_priority`.
- [ ] T011 [P] Create `core/agent/reflection.py` — `Reflection` class that compares `observation_after` vs expected outcome using LLM (via jarvis). Methods: `evaluate_step(node, world_state_before, world_state_after, tool_result) -> ReflectionResult(success: bool, confidence: float, analysis: str)`, `detect_loop(execution_history: list) -> bool` (same tool+params 3+ times).

---

## Phase 3: User Story 1 — Goal-Driven Task Execution (Priority: P1) 🎯 MVP

**Goal**: Core observe → plan → act → reflect loop works end-to-end. User gives a goal, ACA creates a plan, executes each step via tools, observes results, and completes the task.

**Independent Test**: "Open Notepad and type ACA test" — verify Notepad opens, text is typed, agent reports success.

- [ ] T012 [P] [US1] Create `core/agent/agent_manager.py` — `AgentManager` class, the central orchestrator. Holds references to Planner, Executor, Observer, Reflection, ApprovalManager, AgentMemory. Accepts `jarvis` reference. Main method: `async execute_goal(goal_text: str)`. Flow: create AgentGoal → planner.create_plan → loop over steps → observer.capture → executor.execute_step → observer.capture → reflection.evaluate_step → on success continue / on failure retry or replan. Emits progress via `jarvis.write_log()` at each transition. Respects `_user_initiated` gate (checks `jarvis._user_initiated` before first execution).
- [ ] T013 [US1] Wire AgentManager into `main.py` — instantiate AgentManager with jarvis reference during startup (in `__init__` or `_init_services`), expose as `self.agent_manager`. Add `_handle_agent_goal(goal_text)` handler method registered in `_TOOL_HANDLERS` dict (tool name: "agent_execute_goal").
- [ ] T014 [US1] Register `agent_execute_goal` tool in `core/tool_registry.py` _TOOL_DEFS list with parameters: `goal_text` (STRING, "The high-level goal for the autonomous agent to complete"). Add entry to VALID_TOOLS and TOOL_HANDLER_MAP.
- [ ] T015 [US1] Integrate Observer with AgentManager — call `observer.capture()` before and after each tool-execution step. Store WorldState in TaskNode's `observation_before` and `observation_after` fields.

**Checkpoint**: At this point, US1 should be fully functional. User can say "Open Notepad and type test" and ACA executes it with observe-plan-act-reflect loop.

---

## Phase 4: User Story 2 — Dynamic Replanning & Error Recovery (Priority: P1)

**Goal**: When a step fails or produces an unexpected screen state, the agent detects it, retries up to 2 times, and if still failing, replans from the current state or escalates to the user.

**Independent Test**: "Open Calculator and compute 15 * 3" while Calculator is already open — agent detects already-open state and adapts. Or simulate an unexpected dialog and verify agent dismisses and retries.

- [ ] T016 [P] [US2] Add retry logic to AgentManager's execution loop: after `reflection.evaluate_step()` returns `success=false`, increment `node.retry_count`. If `retry_count < 2`, call `observer.capture()` again and retry the same step. If `retry_count >= 2`, call `planner.replan()` with the failed node and current world state.
- [ ] T017 [P] [US2] Implement `planner.replan()` — takes failed TaskNode and current WorldState as context, calls LLM with "The previous plan failed at step X (description: Y). Current state: Z. Generate remaining steps to still achieve the goal." Returns new TaskGraph from the failure point forward. Assigns new step_ids (continue from last ID).
- [ ] T018 [US2] Implement user escalation in AgentManager — when replanning also fails or the LLM indicates goal cannot be achieved, call `jarvis.write_log("ACA: Goal cannot be completed. Reason: ...")` and set goal status to `failed`. Present user with current state and suggested options.
- [ ] T019 [P] [US2] Implement loop detection in AgentManager — after each reflection, call `reflection.detect_loop(history)`. If loop detected, halt execution, set goal status to `failed`, write error to UI, and store loop details in session audit log.

**Checkpoint**: US1 + US2 work together. Agent handles failures gracefully, retries, and escalates when stuck.

---

## Phase 5: User Story 3 — Human Approval & Safety Controls (Priority: P1)

**Goal**: High-risk actions (delete, kill, shell, etc.) require user approval. Approval mode enables medium-risk gates. Execution limits enforced.

**Independent Test**: "Delete temp files" with approval mode on — verify approval request appears and action only executes after approve.

- [ ] T020 [P] [US3] Integrate ApprovalManager into AgentManager execution loop — before executing a step, call `approval_manager.classify_action(tool_name, params)`. If `risk_level=high` (always) or `risk_level=medium` AND approval_mode=True, create ApprovalRequest, call `jarvis.focus_panel("agent")` and `jarvis.write_log()` with action details, then wait for `approval_manager.respond_to_approval()` callback.
- [ ] T021 [P] [US3] Add `approval_mode` property to AgentManager — `is_approval_mode() -> bool` and `set_approval_mode(bool)`. When mode changes, write log and update UI state. Default: `False`.
- [ ] T022 [US3] Implement execution limits in AgentManager — after each step, check: step count > 20, wall-clock time > 5 minutes. If either exceeded, halt execution, write "Execution limit reached (X steps / Y minutes). Partial progress: Z" to UI, set goal status to `cancelled`.
- [ ] T023 [US3] Implement timeout protection in Executor — each `execute_step()` call has a 30-second timeout via `asyncio.wait_for()` or `threading.Timer`. On timeout, raise TimeoutError, which AgentManager catches and feeds to reflection/retry loop.

**Checkpoint**: US1-3 complete. Safe, approved, limited execution with human oversight.

---

## Phase 6: User Story 4 — Agent Panel in JARVIS UI (Priority: P2)

**Goal**: Dedicated UI panel showing goal, task graph, step statuses, logs, and approval controls.

**Independent Test**: Run a 3-step goal and verify the Agent Panel displays all elements with real-time updates.

- [ ] T024 [P] [US4] Create UI rendering section in `ui.py` — add Agent Panel section (below existing panels) rendered in the main drawing loop. Panel shows: goal text, task graph (step list with status badges), active step highlight, log scrollback section, approval request area with Approve/Deny buttons.
- [ ] T025 [P] [US4] Add state attributes to `JarvisUI` for agent display: `agent_goal_text`, `agent_steps: list[dict]`, `agent_active_step: int`, `agent_log: list[str]`, `agent_approval_request: ApprovalRequest | None`, `agent_confidence: float`, `agent_enabled: bool`.
- [ ] T026 [US4] Implement AgentManager → UI data flow — AgentManager pushes state updates via `jarvis.write_log()` for log entries, and a new `jarvis.update_agent_state(steps, active_step, goal_text, confidence)` method that calls `ui.safe_call()` to update agent_* attributes. The UI drawing loop reads these attributes each frame.
- [ ] T027 [US4] Wire approval buttons in UI — Add event handlers in `JarvisUI` for Approve/Deny button clicks. When clicked, call `agent_manager.respond_to_approval(request_id, approved=True/False)`. Button area visible only when `agent_approval_request is not None`.

**Checkpoint**: US1-4 complete. Full visual feedback during agent execution.

---

## Phase 7: User Story 5 — Reusable Workflow Learning (Priority: P3)

**Goal**: Successful plans are cached and reused for similar goals. Over time, common tasks execute faster.

**Independent Test**: Execute the same goal twice — second run should use cached plan and complete faster.

- [ ] T028 [P] [US5] Implement workflow saving in AgentManager — after a goal completes successfully (`status=completed`), call `agent_memory.save_template()` with the TaskGraph (stripped of session-specific observation data), normalized goal text hash, and extracted keywords. Store in `memory/agent/templates/{id}.json` and update `index.json`.
- [ ] T029 [P] [US5] Implement workflow retrieval in Planner — `create_plan()` first calls `agent_memory.find_templates(normalized_goal_text)`. If match found with confidence > 0.7, load the cached TaskGraph, pass of the state-independent nodes (keep tool_name, params, description; remove observation data), and skip LLM call. Log "Using cached workflow from [template_id]".
- [ ] T030 [US5] Implement text normalization for goal matching in AgentMemory — `normalize_goal_text(text) -> str` using NFC normalization, lowercasing, stopword removal (Turkish + English stopwords), and whitespace collapse. `compute_similarity(a, b) -> float` using keyword overlap with fallback (no external NLP dependencies).

**Checkpoint**: US1-5 complete. Agent learns from experience.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Agent skill, safety hardening, documentation, and final integration

- [ ] T031 [P] Create `skills/agent/agent_skill.py` — following SkillManager v3 pattern. Define `SKILL_ID = "agent-v1"`, `SKILL_NAME = "Agent"`, `SKILL_VERSION = "1.0.0"`. Implement `route_agent_request(user_text) -> str | None` that matches Turkish/English automation intent patterns ("do this for me", "complete this task", "handle this automatically", "benim için yap", "şu işi hallet", "otomatik yap"). On match, route to `agent_manager.execute_goal()` via threaded call.
- [ ] T032 [P] Create `skills/agent/SKILL.md` with metadata, trigger examples, and usage documentation.
- [ ] T033 Implement `_user_initiated` gate check in AgentManager — before any execution, check `jarvis._user_initiated` (or equivalent flag). If False, reject with "ACA requires user interaction first". This applies the existing constitution Principle V security rule.
- [ ] T034 Add audit logging to AgentManager — after each goal (success or failure), save full AgentSession to `memory/agent/sessions/{session_id}.json` via `agent_memory.save_session()`. Include all plan versions, approval requests, world states, and final summary.
- [ ] T035 [P] Add shell command safety pass in Executor — before calling `shell_run()`, verify the command passes through existing `actions/shell.py` blocked-command list and security prefix check. If blocked, skip and mark step as failed with "Shell command rejected by security filter".
- [ ] T036 [P] Verify ACA integration with existing JARVIS test suite — run `.venv/bin/python3 -m unittest tests.test_smoke -v` and confirm 0 pre-existing failures. Fix any ACA-related regressions.
- [ ] T037 Run `lsp_diagnostics` on all new/modified files and resolve any issues.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1) → Must be complete first (foundation for all other stories)
  - US2 (P1) → Depends on US1 (requires execution loop)
  - US3 (P1) → Depends on US1 (requires execution loop), independent of US2
  - US4 (P2) → Depends on US1 (requires agent state), independent of US2/US3
  - US5 (P3) → Depends on US1 + US2 (requires completed goals + replanning)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: MVP — Can start after Foundational. Foundation for all other stories.
- **US2 (P1)**: Can start after US1 — adds retry/replan on top of execution loop
- **US3 (P1)**: Can start after US1 — adds approval gates around execution, parallel to US2
- **US4 (P2)**: Can start after US1 — adds visualization of existing agent state
- **US5 (P3)**: Can start after US1+US2 — needs completed goals and error handling

### Parallel Opportunities

- T002, T003, T004 (Phase 1) can run in parallel
- T007, T008, T009, T010, T011 (Phase 2) can all run in parallel (independent files)
- T012, T013, T014, T015 (US1) should run sequentially (T012 central, T013-015 integrate)
- T016, T017, T019 (US2) can run in parallel once US1 is complete
- T020, T021, T023 (US3) can run in parallel once US1 is complete
- T024, T025 (US4) can run in parallel once US1 is complete
- T028, T029 (US5) can run in parallel once US1+US2 complete
- T031, T032, T035 (Polish) can run in parallel

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup → 5 tasks
2. Complete Phase 2: Foundational → 6 tasks (T006-T011)
3. Complete Phase 3: US1 → 4 tasks (T012-T015)
4. **STOP and VALIDATE**: Test US1 independently
5. **This is the MVP** — core observe-plan-act-reflect loop working

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Core agent loop works (MVP!)
3. Add US2 → Error recovery
4. Add US3 → Safety controls
5. Add US4 → UI visualization
6. Add US5 → Workflow learning
7. Polish → Final hardening

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 + Phase 2 together
2. Once Foundation is done:
   - Developer A: US1 + US2 (core execution + recovery)
   - Developer B: US3 + US4 (approvals + UI) (can start after US1 foundation)
3. Developer A/B merge → US5 + Polish
