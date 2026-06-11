# Feature Specification: ACA Subsystem

**Feature Branch**: `002-aca-subsystem`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "Build an Autonomous Computer Agent (ACA) for JARVIS. The ACA must transform JARVIS from a voice assistant into a goal-driven desktop agent capable of observing, planning, executing, monitoring and recovering from complex computer tasks."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Goal-Driven Task Execution (Priority: P1)

The user gives JARVIS a high-level goal: "Download the latest Python release." The ACA automatically decomposes this into steps: open browser → navigate to python.org → find download → click download → verify file appears. The agent observes each step's result via screen_vision and adjusts if the page layout differs from expected.

**Why this priority**: P1 — goal decomposition and multi-step execution is the core value proposition. Without it, the ACA is not autonomous.

**Independent Test**: Give the agent a controlled goal in a known environment (e.g., "Open Notepad, type 'ACA test', and save to Desktop as aca_test.txt"). Verify all 3 steps execute in order and the file exists.

**Acceptance Scenarios**:

1. **Given** a high-level goal with no step-by-step instructions, **When** the agent receives it, **Then** it produces a structured task graph with at least 3 ordered steps within 10 seconds
2. **Given** a task graph is ready, **When** execution begins, **Then** each step uses the appropriate existing tool from the registry (browser_control, shell_run, open_app, analyze_screen)
3. **Given** a step involves a UI interaction (click, type), **When** the action completes, **Then** the agent observes the screen to confirm the expected state change
4. **Given** all steps succeed, **When** the plan finishes, **Then** the agent reports a final summary including what was done and the final observed state

---

### User Story 2 - Dynamic Replanning & Error Recovery (Priority: P1)

While executing "Find the cheapest flight to Berlin" the agent encounters an unexpected pop-up ad or a CAPTCHA. The observer detects the anomaly (screen state does not match expected), the reflection loop labels it as a failure, the planner generates an alternative approach (dismiss pop-up / wait for user input), and execution resumes.

**Why this priority**: P1 — real-world desktop automation is unreliable without self-correction. The agent must handle unpredictable UI states.

**Independent Test**: Simulate an unexpected dialog (e.g., a "Save As" dialog when the agent expects a blank Notepad) and verify the agent detects the mismatch, logs it, and retries or escalates within 15 seconds.

**Acceptance Scenarios**:

1. **Given** an action produces an unexpected screen state, **When** the observer captures the result, **Then** the reflection loop identifies the mismatch within 3 seconds
2. **Given** a mismatch is detected, **When** recovery is possible (dismiss dialog, retry), **Then** the planner generates an alternative step and execution resumes
3. **Given** an unrecoverable error, **When** the agent exhausts 2 retry attempts, **Then** it escalates to the user with the current state, the failed step, and suggested options
4. **Given** the user provides guidance, **When** the agent receives it, **Then** it updates the plan and continues execution

---

### User Story 3 - Human Approval & Safety Controls (Priority: P1)

The user enables "approval mode." When the ACA attempts to delete a file, kill a process, or run a shell command, it pauses, displays the intended action in the UI, and waits for explicit confirmation. The user can approve, deny, or modify the action. The agent also respects execution limits (max steps, timeouts, loop detection).

**Why this priority**: P1 — safety is non-negotiable for an agent with keyboard/mouse/shell access. Human approval prevents accidental damage.

**Independent Test**: Trigger a high-risk action (e.g., tell the agent to "delete temp files" with approval mode on) and verify a UI approval request appears, blocks execution, and the action only proceeds after explicit approval.

**Acceptance Scenarios**:

1. **Given** approval mode is enabled, **When** the agent queues a high-risk action (delete file, kill process, shell command, download executable, service modification), **Then** execution pauses and a structured approval request appears in the JARVIS UI
2. **Given** an approval request is displayed, **When** the user approves, **Then** the action executes normally and the plan continues
3. **Given** an approval request is displayed, **When** the user denies, **Then** the step is marked as skipped, the reason is logged, and the plan adjusts
4. **Given** the agent exceeds 20 total steps or 5 minutes wall-clock time, **When** the limit is reached, **Then** execution halts and the user is notified with a summary of partial progress
5. **Given** the agent detects it is repeating the same action (same tool + same params) 3+ times, **When** loop detection triggers, **Then** execution pauses and the user is asked to intervene

---

### User Story 4 - Agent Panel in JARVIS UI (Priority: P2)

A new Agent Panel in the JARVIS UI shows: current goal, execution state, a visual task graph (steps with edges), currently active step highlighted, completed steps with checkmarks, pending approval requests, a log of observations and actions, and a confidence score for the current step.

**Why this priority**: P2 — the agent functions headless without this, but the panel is essential for user trust, debugging, and transparency.

**Independent Test**: Run a 3-step goal and verify the Agent Panel renders at least: the goal text, 3 steps, the active step highlighted, completion status for finished steps, and a log entry per step — all updating in real-time without manual refresh.

**Acceptance Scenarios**:

1. **Given** an ACA session starts, **When** the goal is set, **Then** the Agent Panel displays the goal and an empty task graph
2. **Given** a task graph is generated, **When** displayed, **Then** each step shows: step number, description, status badge (pending/in_progress/completed/failed), and estimated duration
3. **Given** a step is executing, **When** observed, **Then** the active step is visually highlighted and a confidence score (0–100%) is shown based on screen observation clarity
4. **Given** the agent writes a log entry, **When** the panel receives it, **Then** it appends to a scrollable log with timestamp and step reference
5. **Given** a human approval request is active, **When** triggered, **Then** the panel shows Approve/Deny buttons and the action details

---

### User Story 5 - Reusable Workflow Learning (Priority: P3)

After the user manually completes a task or approves an ACA-executed workflow, the agent memory stores the successful plan. Next time the user asks for a similar goal, the agent retrieves and adapts the previous plan. Over time, common tasks (download file, create folder, generate report) execute faster from learned patterns.

**Why this priority**: P3 — valuable for long-term UX improvement but not required for MVP. Requires the agent memory system to be mature.

**Independent Test**: Execute the same goal twice. Verify the second execution uses a cached plan (faster planning phase) and completes with at least as many correct steps as the first.

**Acceptance Scenarios**:

1. **Given** a goal has been completed successfully, **When** the same goal is given again, **Then** the planning phase completes 50% faster using the cached workflow
2. **Given** a cached workflow exists, **When** the desktop state differs (different apps open), **Then** the agent adapts the plan rather than blindly reusing it
3. **Given** a workflow fails when reused, **When** the agent detects the failure, **Then** it falls back to full replanning and stores the corrected version

---

### Edge Cases

- What happens when the desktop is locked, screen is off, or the user is away?
- How does the agent handle multiple monitors with different DPI settings?
- What if a tool (analyze_screen, shell_run) returns an error mid-plan?
- How does the agent behave when the LLM (Gemini) is unavailable for planning/reflection?
- What happens if the user speaks a new command while the ACA is executing?
- How does the system handle applications that require admin elevation?
- What if the observed screen contains no recognizable UI elements (blank desktop)?

## Requirements *(mandatory)*

### Functional Requirements

**Core Architecture**

- **FR-001**: The system MUST create a new `core/agent/` package with files: `agent_manager.py`, `planner.py`, `executor.py`, `observer.py`, `reflection.py`, `task_graph.py`, `approval_manager.py`, `agent_memory.py`
- **FR-002**: `agent_manager.py` MUST act as the central orchestrator, accepting goals, coordinating planner/executor/observer/reflection, and managing the agent lifecycle (start, pause, resume, cancel)
- **FR-003**: The agent MUST follow the existing JARVIS provider abstraction pattern — it receives a `jarvis` reference for UI, tools, and config access
- **FR-004**: All ACA modules MUST use `snake_case`, type hints on all public signatures, and follow the error handling pattern (traceback.print_exc() in except blocks)

**Observation Layer**

- **FR-005**: `observer.py` MUST capture the current desktop state using `actions/screen_vision.analyze_screen()` before each UI-interaction step
- **FR-006**: The observer MUST also track active window title, running process list (via `actions/process_manager`), and recent filesystem changes (via `actions/file_guardian`)
- **FR-007**: The observer MUST maintain a structured "world state" dict: `{ "screen_text": str, "active_window": str, "processes": [...], "timestamp": float }`

**Planning System**

- **FR-008**: `planner.py` MUST decompose a high-level goal into a task graph (ordered steps with dependencies) using the JARVIS LLM (Gemini or Ollama via existing provider)
- **FR-009**: Each task graph node MUST contain: `step_id`, `description`, `action_type` (observe/tool/approval_wait/shell), `tool_name`, `params`, `dependencies`, `status`, `retry_count`, `confidence`
- **FR-010**: The planner MUST support dynamic replanning — if a step fails, regenerate remaining steps from the current state
- **FR-011**: The planner MUST assign priority to steps and detect parallelizable independent steps

**Execution Engine**

- **FR-012**: `executor.py` MUST dispatch actions through the existing tool registry handler map (`core/tool_registry.py`), calling the appropriate handler method
- **FR-013**: The executor MUST support these action types: `browser_control`, `shell_run`, `open_app`, `analyze_screen`, `list_processes`, `kill_process`, `find_large_files`, `cleanup_folder`, `get_folder_summary`, `get_network_summary`, `list_services`, `control_service`
- **FR-014**: The executor MUST implement low-level mouse/keyboard actions (click at coordinates, type text, key combo, drag) using a cross-platform library
- **FR-015**: The executor MUST automatically select the best tool for a given action description (e.g., "open browser" → `open_app`, "search google" → `browser_control`)
- **FR-016**: The executor MUST apply timeouts per step (default 30s, configurable) and enforce global execution limits

**Reflection Loop**

- **FR-017**: `reflection.py` MUST evaluate each step result against the expected outcome using screen observation and tool return values
- **FR-018**: On failure, the reflection loop MUST increment retry_count and signal the planner for alternative approach if retries exceed 2
- **FR-019**: The reflection loop MUST detect infinite loops (same action+params 3+ times) and trigger escalation

**Human Approval System**

- **FR-020**: `approval_manager.py` MUST classify actions as low-risk (observe, open app) or high-risk (delete, kill, shell, service control, download)
- **FR-021**: In approval mode, high-risk actions MUST pause execution and display a structured approval request in the JARVIS UI via `focus_panel()` and `write_log()`
- **FR-022**: Approval requests MUST show: action description, tool name, parameters, estimated risk level, and Approve/Deny buttons
- **FR-023**: The approval manager MUST respect the existing `_user_initiated` security gate — no autonomous pre-user-interaction actions

**Agent Memory**

- **FR-024**: `agent_memory.py` MUST persist goals, plans, execution history, failures, and learned workflows using the existing `memory/memory_manager.py` JSON-backed store
- **FR-025**: Successful plans MUST be stored as reusable workflow templates keyed by goal intent (normalized text hash)
- **FR-026**: The agent MUST retrieve and adapt stored workflows when similar goals are detected (cosine similarity or keyword overlap on goal text)

**UI Integration**

- **FR-027**: The ACA MUST integrate with the JARVIS UI through the existing `jarvis` reference: `write_log()` for agent log entries, `set_state("THINKING")` during planning, `focus_panel("agent")` for approval requests
- **FR-028**: A new Agent Panel MUST render in the JARVIS UI showing: goal text, task graph with step statuses, active step highlight, scrollable log, and approval controls
- **FR-029**: All UI updates MUST be thread-safe using `safe_call()` pattern

**Agent Skill**

- **FR-030**: A new skill `skills/agent/agent_skill.py` MUST be created following the SkillManager v3 pattern: `route_agent_request(user_text) → str | None`
- **FR-031**: The skill MUST trigger on Turkish/English phrases expressing automation intent: "do this for me", "complete this task", "handle this automatically", "benim için yap", "şu işi hallet"
- **FR-032**: The skill MUST route matching requests to the Agent Manager's `execute_goal()` method

**Safety & Guardrails**

- **FR-033**: Maximum 20 steps per goal
- **FR-034**: Maximum 5 minutes wall-clock execution time per goal
- **FR-035**: Loop detection: same action+params repeated 3+ times triggers auto-pause
- **FR-036**: Shell commands MUST pass through existing `actions/shell.py` security filters (blocked commands list)
- **FR-037**: The agent MUST record all actions to a structured audit log at `logs/agent/`

### Key Entities

- **AgentGoal**: The user's high-level objective (text), received timestamp, status (pending/active/completed/failed/cancelled)
- **TaskGraph**: Directed acyclic graph of steps. Root nodes have no dependencies, leaf nodes produce the goal output. Supports serialization to/from JSON for persistence.
- **TaskNode**: A single step in the graph with: step_id (int), description (str), action_type (enum: observe/tool/approval_wait/llm_reason/shell/input), tool_name (str), params (dict), dependencies (list[int]), status (enum: pending/in_progress/completed/failed/skipped), retry_count (int), confidence (float 0-1), observation_result (str)
- **WorldState**: Snapshot of the desktop environment at a point in time: screen_text, active_window_title, running_processes, recent_files, timestamp
- **ApprovalRequest**: Action requiring human confirmation: request_id, action_description, tool_name, params, risk_level (low/medium/high), status (pending/approved/denied), responded_at
- **WorkflowTemplate**: Reusable plan from a completed goal: intent_hash, goal_text, task_graph_json, success_count, last_used

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can give a 5-step desktop goal and the ACA completes it without human intervention in under 120 seconds
- **SC-002**: ACA detects and recovers from at least 3 distinct error types (unexpected dialog, app not found, tool failure) automatically without user help
- **SC-003**: Human approval mode adds no more than 3 seconds overhead per approved action (from request display to execution resume)
- **SC-004**: Agent Panel updates appear in the UI within 500ms of each step transition
- **SC-005**: Loop detection triggers correctly in 100% of test cases with 4+ repeated actions
- **SC-006**: Zero false-positive escapes from the _user_initiated security gate in 200 test runs
- **SC-007**: At least 80% of goal decomposition plans produced by the planner result in successful task completion on first attempt for a test suite of 10 common goals
- **SC-008**: Agent memory successfully retrieves a cached workflow for 90% of goals that match a previously completed goal

## Assumptions

- The ACA runs in-process with JARVIS, sharing the same Python process, LLM provider connection, tool registry, and UI reference
- Screen observation uses the existing Gemini Vision pipeline via `actions/screen_vision.analyze_screen()`
- Low-level mouse/keyboard is implemented via `pyautogui` (cross-platform) or `pywinauto` (Windows-specific)
- The agent LLM (for planning and reflection) uses the same provider and model as the active JARVIS backend (Gemini or Ollama)
- Approval mode is opt-in — default mode is auto-execute with loop detection only
- The agent runs exclusively on desktop (no mobile, no server-headless support)
- All ACA modules are registered in the tool registry and follow the same handler pattern as existing tools
- The `core/agent/` package is loaded and initialized during JARVIS startup, not lazily
