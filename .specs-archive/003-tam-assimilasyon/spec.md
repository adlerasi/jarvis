# Feature Specification: Tam Assimilasyon

**Feature Branch**: `003-tam-assimilasyon`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "%100 gercek kod ile tam asimilasyon baska agent kullanma sen calıs"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic ACA Startup & Readiness (Priority: P1)

The user launches JARVIS. The ACA subsystem initializes automatically during startup — no manual activation needed. The Agent Manager is ready, the observer is primed, the planner is connected to the LLM provider, and the agent skill is hot-loaded in the skill manager. The Agent Panel in the UI shows "Ready" state.

**Why this priority**: P1 — full assimilation means the ACA is an integral part of JARVIS, not a separate module requiring manual launch.

**Independent Test**: Start JARVIS, wait 3 seconds, then check via `agent_manager.is_running()` returns `False` (idle) but `agent_manager` is fully initialized and accessible through the UI Agent Panel (visible "Ready" badge). Verify `skills/agent/agent_skill.route_agent_request` is registered in the skill manager.

**Acceptance Scenarios**:

1. **Given** JARVIS starts, **When** the init sequence completes, **Then** `AgentManager` is instantiated and its `is_available()` returns `True`
2. **Given** JARVIS is running, **When** the user checks the UI, **Then** the Agent Panel shows "✅ Hazir" (Ready) status without requiring any user action
3. **Given** startup is complete, **When** inspected, **Then** `agent_skill` is loaded in the skill manager with all 5 intents (execute_goal, get_status, cancel_goal, approve_step, reject_step)

---

### User Story 2 - Real Tool Execution via ACA (Priority: P1)

The user says "Benim icin masaustunde test.txt olustur." The agent skill routes this to AgentManager. The Planner uses the real LLM provider (not a mock) to decompose the goal into: open Notepad → type text → save file. The Executor dispatches each step through the real tool registry — `open_app` launches Notepad, `pyautogui` types the text and presses Ctrl+S, `shell_run` or `pyautogui` handles the Save dialog. Every action produces real side effects.

**Why this priority**: P1 — "100% real code" means no simulated steps, no stubs, no mock execution. Every action goes through the actual JARVIS tool pipeline.

**Independent Test**: Run `agent_manager.execute_goal("Masaustunde test.txt olustur")` and verify Notepad actually opens, text is typed, and the file appears on the desktop within 60 seconds.

**Acceptance Scenarios**:

1. **Given** an ACA goal is received, **When** the planner runs, **Then** it calls the real LLM provider (Gemini or Ollama) — verified by checking LLM provider logs
2. **Given** the executor dispatches an `open_app` step, **When** executed, **Then** the actual application launches (verified by process list change)
3. **Given** the executor dispatches a `pyautogui.typewrite` step, **When** executed, **Then** text is actually typed into the active window (verified by screen observation after the step)
4. **Given** the executor dispatches a `shell_run` step, **When** executed, **Then** the real `subprocess.run()` executes with the command string through `actions/shell.py` security filter
5. **Given** all steps complete, **When** the agent finishes, **Then** the observable desktop state matches the goal intent (file exists, window is open, etc.)

---

### User Story 3 - Real-Time Agent Panel with Live State (Priority: P2)

The ACA executes a multi-step goal. The Agent Panel in the JARVIS UI updates in real-time: step transitions show within 500ms, the current step is highlighted, the log shows each action with timestamps, and the progress bar advances. No polling or manual refresh needed — all updates arrive via callbacks from the Agent Manager.

**Why this priority**: P2 — full assimilation requires the ACA to be visible and controllable through JARVIS's native UI, not a separate window or headless process.

**Independent Test**: Execute a 3-step goal and record the Agent Panel state at 500ms intervals. Verify each step transition is reflected in the panel within 500ms of the executor completing the step.

**Acceptance Scenarios**:

1. **Given** the ACA begins executing a goal, **When** the first step transitions to `in_progress`, **Then** the Agent Panel highlights it within 500ms
2. **Given** a step completes, **When** the result is returned, **Then** the panel updates the step badge to ✅ and advances the progress bar
3. **Given** the agent writes a log entry via `self._log()`, **When** called, **Then** the Agent Panel log appends the entry with timestamp and step reference
4. **Given** the agent completes or fails, **When** the final state is set, **Then** the panel shows the final status ("🏁 Basarili" or "⛔ Basarisiz") and a summary

---

### User Story 4 - Production Error Resilience (Priority: P2)

During execution, a tool returns an unexpected error. The executor's 30-second timeout catches a hung operation. The reflection loop detects the failure, logs it with full traceback, retries once (not mock — actual retry), and if it fails again, replans. If the LLM provider is unreachable during replanning, the planner falls back to a hardcoded plan. Every real-world failure mode is handled without crashing the entire ACA or JARVIS.

**Why this priority**: P2 — real code encounters real errors. The subsystem must handle timeouts, import errors, LLM failures, and UI state mismatches gracefully.

**Independent Test**: Force a tool timeout (set `_step_timeout` to 1s and execute a step that takes 2s) and verify the ACA catches it, logs it, and retries or replans without crashing JARVIS.

**Acceptance Scenarios**:

1. **Given** a step exceeds the 30-second timeout, **When** the `ThreadPoolExecutor` raises `TimeoutError`, **Then** the executor returns a structured error, not an unhandled exception
2. **Given** a step fails with a real exception (e.g., `pyautogui` fails because no screen), **When** caught, **Then** `traceback.print_exc()` is called and the error is recorded in the step's `result` field
3. **Given** the LLM provider is unavailable during planning, **When** `_call_llm_for_plan` raises, **Then** `_fallback_plan` returns a valid single-step graph
4. **Given** the executor's import for `shell_run` fails, **When** caught, **Then** a descriptive error string is returned, and the agent continues to the next step
5. **Given** any unexpected exception in the execution loop, **When** caught by the outer try/except in `_run_goal_loop`, **Then** `_running` is set to `False`, the goal is marked `FAILED`, and `traceback.print_exc()` is called

---

### User Story 5 - Natural Language Goal Activation via Skill (Priority: P1)

The user speaks "Masaustunde bir metin dosyasi olustur ve icine merhaba yaz." The voice pipeline transcribes, the skill manager matches this to the agent skill, `route_agent_request()` classifies it as `execute_goal`, extracts the goal text, and calls `agent_manager.execute_goal()`. The entire flow — from voice to ACA execution — happens without any manual tool invocation.

**Why this priority**: P1 — full assimilation means the ACA is accessible through JARVIS's primary interface (voice + skills), not just programmatic API calls.

**Independent Test**: Pass the string "Masaustunde bir txt dosyasi olustur" through `route_agent_request()` with a real `agent_manager` reference and verify it returns a success response string within 5 seconds.

**Acceptance Scenarios**:

1. **Given** the user says a Turkish sentence expressing automation intent, **When** `route_agent_request()` receives the text, **Then** it returns a non-None response indicating goal acceptance
2. **Given** the input text contains a clear goal but no action keyword, **When** `classify_agent_intent()` runs, **Then** it returns `none` and `route_agent_request()` returns `None` (does not trigger falsely)
3. **Given** `execute_agent_skill()` receives an `execute_goal` action, **When** the goal text is extracted, **Then** `agent_manager.execute_goal()` is called with the extracted goal text (not the full trigger phrase)
4. **Given** the user says "İptal et" mid-execution, **When** routed, **Then** `cancel_goal()` is called and execution halts

---

### Edge Cases

- What happens when the user closes the Agent Panel mid-execution? The ACA continues running in the background — re-opening the panel shows current state (not reset).
- What if the skill manager hot-reload clears the agent skill while a goal is running? The goal continues — only subsequent goal requests are affected until the skill reloads.
- How does the ACA behave when pyautogui is not installed (headless/server environment)? The executor returns descriptive errors and falls back to tool-only actions.
- What if the user issues a new voice command while the ACA is executing? The new command is processed by JARVIS normally — the ACA does not block other functionality. The user must explicitly cancel the current goal.
- What happens if JARVIS is restarted while the ACA has an active goal? In-memory state is lost. The agent memory (JSON store) retains partial session data for review.

## Requirements *(mandatory)*

### Functional Requirements

**Automatic Startup & Initialization**

- **FR-001**: `AgentManager` MUST be instantiated in `main.py`'s `_asimilasyon_init()` or equivalent startup path, not lazily on first use
- **FR-002**: On initialization, `AgentManager` MUST create all sub-components (planner, executor, observer, approval_manager, agent_memory) with real references — no None defaults for core dependencies
- **FR-003**: The agent skill (`skills/agent/agent_skill.py`) MUST be loaded by `skill_manager` during startup, not deferred
- **FR-004**: The Agent Panel in `ui.py` MUST be rendered by default (visible state) and show "✅ Hazir" when the ACA is idle

**Real Tool Execution Pipeline**

- **FR-005**: The planner MUST use the real LLM provider for decomposition — `_call_llm_for_plan()` must go through `core/provider_base` or direct LLM call, not return a stub plan
- **FR-006**: The executor MUST dispatch all tool actions through the real `jarvis` tool handler map (registered via `_build_tool_handler_map()`), not simulated dispatch
- **FR-007**: PyAutoGUI actions (click, type, key, drag, scroll, hotkey) MUST execute against the real OS — no dry-run mode, no mock wrapper
- **FR-008**: Shell commands MUST pass through `actions/shell.shell_run()` with the real security filter, 30-second timeout, and output truncation
- **FR-009**: Observer screen capture MUST call `actions/screen_vision.analyze_screen()` with the real Gemini Vision API — no cached or simulated state

**Real-Time UI Integration**

- **FR-010**: The Agent Panel MUST receive live updates via the `on_state_update` callback registered in `AgentManager` — no polling, no setInterval
- **FR-011**: Step transitions (pending → in_progress → completed/failed) MUST update the panel within 500ms of the state change
- **FR-012**: Log entries from `AgentManager._log()` MUST appear in the panel's scrollable log section automatically
- **FR-013**: Approval requests (F6 approve / F7 reject key bindings) MUST work in real-time — pressing F6 calls `agent_manager.approve_current_step()` and execution resumes on the same step

**Error Handling Resilience**

- **FR-014**: Every `except` block in ACA modules MUST call `traceback.print_exc()` (constitution rule) — no silent catches
- **FR-015**: The executor's 30-second step timeout MUST use `concurrent.futures.ThreadPoolExecutor` (already implemented) — no `signal.alarm()` or other platform-specific mechanisms
- **FR-016**: If `actions.shell.shell_run` or `actions.screen_vision.analyze_screen` are not importable, the executor MUST return a descriptive error string, not raise `ImportError`
- **FR-017**: If the LLM provider raises any exception during planning, `create_plan()` MUST fall back to `_fallback_plan()` without propagating the exception to the caller
- **FR-018**: The `_run_goal_loop` outer try/except MUST catch `Exception` (not `BaseException`), log via `traceback.print_exc()`, set `_running = False`, and mark the goal as `FAILED`

**Skill-Driven Natural Language Access**

- **FR-019**: `route_agent_request()` MUST correctly classify all 5 intents (execute_goal, get_status, cancel_goal, approve_step, reject_step) using the defined regex patterns
- **FR-020**: On `execute_goal`, the goal text MUST be the user's input with trigger phrases stripped — not the raw input text
- **FR-021**: When `agent_manager` is `None`, `execute_agent_skill()` MUST return a descriptive Turkish message: "ACA sistemi henuz baslatilmadi."
- **FR-022**: The agent skill MUST NOT contain any blocking calls — `execute_goal()` is async; the skill returns immediately with a confirmation string

**Configuration & State Persistence**

- **FR-023**: Agent memory (`memory/agent/`) MUST be persisted to the filesystem using the existing `memory/memory_manager.py` JSON store, not in-memory-only
- **FR-024**: Agent goals, session data, and workflow templates MUST survive JARVIS restart — loaded from disk on `AgentManager` initialization
- **FR-025**: Maximum execution limits (20 steps, 5 minutes wall-clock) MUST be enforced with hard checks before each step — no soft limits
- **FR-026**: All ACA configuration (max_steps, max_duration, approval_mode) MUST be configurable via `AgentManager.__init__` parameters with sensible defaults

### Key Entities

- **AgentManager**: Central orchestrator. Owns all sub-components. Single entry point for `execute_goal()`, `cancel_goal()`, `get_goal_status()`. Emits state updates via `on_state_update` callback.
- **Planner**: LLM-based goal decomposer. Accepts goal text, returns `TaskGraph`. Supports replanning from failure point. Falls back to `_fallback_plan()` if LLM unavailable.
- **Executor**: Tool dispatcher. Maps `action_type` to real handler functions. Enforces 30s per-step timeout. Handles tool, shell, pyautogui, and observe action types.
- **Observer**: Desktop state collector. Captures screen text, active window, process list. Returns structured `WorldState` dict.
- **AgentMemory**: JSON-persisted store for sessions, goals, and workflow templates. Provides `find_templates()` for similar-intent matching.
- **TaskGraph**: DAG of steps with topological ordering. Supports JSON serialization, failure detection, remaining node calculation.
- **TaskNode**: Single step with step_id, description, action_type, tool_name, params, dependencies, status, retry_count. Serializable.
- **AgentPanel**: UI section in `JarvisUI` displaying goal state, step list with status badges, scrollable log, progress bar, and approval controls.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ACA initializes within 1 second of JARVIS startup — verified by checking `AgentManager.is_available()` returns `True` 1s after `_asimilasyon_init()` completes
- **SC-002**: A 3-step desktop goal (open app, type text, save) completes with real side effects in under 90 seconds on target hardware
- **SC-003**: Agent Panel state updates appear within 500ms of each step transition — verified by timestamp comparison over 10 test runs
- **SC-004**: Zero unhandled exceptions in ACA modules during a 30-minute continuous execution stress test with 5 diverse goals
- **SC-005**: `route_agent_request()` correctly classifies and routes at least 20/25 test phrases covering all 5 intents + false positives
- **SC-006**: The executor timeout mechanism catches and recovers from a deliberately hung step in under 35 seconds (30s timeout + 5s grace)
- **SC-007**: Agent memory persists and retrieves at least 90% of completed goal sessions across JARVIS restarts
- **SC-008**: The ACA does not block or degrade JARVIS voice interaction response time — voice commands processed within 3s even during ACA execution

## Assumptions

- The ACA runs on Windows (primary target) where pyautogui and screen_vision work natively. On Linux/macOS, pyautogui actions and screen capture may behave differently.
- The LLM provider (Gemini or Ollama) is already configured in `config/api_keys.json` and initialized during JARVIS startup — the ACA does not manage provider lifecycle.
- pyautogui is installed (`requirements.txt`) and importable at runtime. If missing, the ACA continues with tool-only actions.
- The user has a working display and desktop session — the ACA cannot function in headless/server environments.
- The screen_vision `analyze_screen()` function has network access to the Gemini API (or configured local model).
- Approval mode defaults to `off` — the ACA auto-executes all steps unless the user enables approval mode.
- The ACA is not designed for multi-user scenarios — it runs in-process with a single JARVIS instance.
- All ACA state is ephemeral in-memory during execution; only session summaries and templates are persisted to disk.
