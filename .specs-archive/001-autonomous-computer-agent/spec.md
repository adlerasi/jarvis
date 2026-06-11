# Feature Specification: Autonomous Computer Agent

**Feature Branch**: `001-autonomous-computer-agent`

**Created**: 2026-06-10

**Status**: Draft

**Input**: User description: "Build an Autonomous Computer Agent for JARVIS that can observe the desktop, understand UI elements, control mouse and keyboard, open applications, navigate websites, complete multi-step tasks, and recover from failures."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Core Agent Loop: Observe, Plan, Act, Reflect (Priority: P1)

The user asks JARVIS to perform a multi-step computer task (e.g., "Find the latest invoice PDF, open it, and email it to ahmet"). The agent observes the current desktop state, creates a step-by-step plan, executes actions via mouse/keyboard/app-control, and reflects on each step's result before proceeding.

**Why this priority**: P1 — without the core observe-plan-act-reflect loop, no higher-level task automation is possible. This is the foundational capability.

**Independent Test**: Can be fully tested by giving the agent a controlled two-step task in a known desktop state (e.g., "Open Notepad and type 'hello'"). The test verifies that the agent observes the desktop, plans the steps, executes them, and reports the outcome.

**Acceptance Scenarios**:

1. **Given** the agent receives a multi-step desktop task, **When** it begins execution, **Then** it observes the current screen and produces a structured plan with at least 2 steps
2. **Given** the agent has a plan, **When** it executes step 1 (e.g., clicking an app icon), **Then** it captures the resulting screen state and confirms the action had the expected effect
3. **Given** a step succeeds, **When** the agent reflects on the result, **Then** it proceeds to the next planned step automatically
4. **Given** all steps complete, **When** the agent finishes, **Then** it reports a final summary of what was accomplished

---

### User Story 2 - Error Recovery & Human Approval Mode (Priority: P1)

The agent encounters an unexpected desktop state (e.g., a pop-up dialog, app not found, permission denied). It detects the anomaly, attempts recovery (retry, alternative approach), and if recovery fails, asks for human approval or guidance. The user can also request the agent to pause and wait for confirmation before each action.

**Why this priority**: P1 — error recovery is essential for real-world reliability; human approval is critical for safety with keyboard/mouse control.

**Independent Test**: Can be tested by simulating a known failure scenario (e.g., target app is not installed) and verifying the agent detects the failure, attempts one recovery strategy, then escalates to the user with a clear description.

**Acceptance Scenarios**:

1. **Given** the agent executes a step that fails, **When** it detects the failure via screen observation, **Then** it logs the error and attempts up to 2 automatic recovery strategies (retry, different approach)
2. **Given** all recovery strategies fail, **When** the agent cannot proceed, **Then** it presents the user with the current state, the failed step, and suggested next action options
3. **Given** human approval mode is enabled, **When** the agent is about to execute a UI-affecting action (click, type, drag), **Then** it pauses and displays the intended action for user confirmation
4. **Given** the user denies an action, **When** the agent receives the rejection, **Then** it aborts the current plan and reports cancellation

---

### User Story 3 - Progress Display & Reasoning in UI (Priority: P2)

While the autonomous agent is working, JARVIS's UI shows real-time progress: current step, reasoning (why this step), observed screen state summary, and completion percentage. The user can follow along and understand what the agent is doing at all times.

**Why this priority**: P2 — essential for trust and usability but not strictly required for the agent to function. The agent can run headless until this is implemented.

**Independent Test**: Can be tested by running a 3-step task and verifying that the JARVIS UI displays at least 3 distinct progress updates with reasoning text, without manual intervention.

**Acceptance Scenarios**:

1. **Given** the agent is executing a plan, **When** each step begins, **Then** the UI displays "Step N/M: [action description]" via `write_log()`
2. **Given** the agent observes the screen, **When** analysis completes, **Then** the UI shows a brief summary of what was observed
3. **Given** the agent encounters an error, **When** recovery is attempted, **Then** the UI shows the error and the recovery strategy being tried
4. **Given** the plan completes, **When** the agent finishes, **Then** the UI shows a final success status for a configurable duration

---

### User Story 4 - Goal Planning with Task Decomposition (Priority: P2)

The agent receives a high-level goal (e.g., "Organize my Downloads folder") and autonomously decomposes it into a structured task plan with sub-goals, dependency tracking, and estimated steps.

**Why this priority**: P2 — the agent can work with explicit step-by-step instructions from the user (US1), but autonomous decomposition makes it much more powerful.

**Independent Test**: Can be tested by giving the agent a vague goal with no step-by-step instructions (e.g., "Check my system health and save a report") and verifying it produces a plan with at least 2 meaningful steps.

**Acceptance Scenarios**:

1. **Given** a high-level goal like "Check system health and send me a summary", **When** the agent creates a plan, **Then** the plan includes at least: call `system_health` tool, format results, deliver to user
2. **Given** a goal that requires browser navigation, **When** the agent plans, **Then** the plan includes screen observation steps between each browser action
3. **Given** a goal with multiple independent sub-tasks, **When** the agent decomposes it, **Then** independent tasks are flagged for potential parallel execution
4. **Given** the plan is created, **When** displayed to the user, **Then** the estimated step count and overall goal are clearly visible

---

### Edge Cases

- What happens when the desktop is locked or the screen saver is active?
- How does the agent handle unexpected dialogs (e.g., "Are you sure?" confirmation boxes)?
- What happens when a required tool (screen_vision, shell) returns an error?
- How does the system behave when no active window is available for observation?
- What happens if the agent's plan exceeds a maximum step limit (e.g., 20 steps)?
- How does the agent recover from a mis-click that opens the wrong application?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST observe the current desktop state using the existing `analyze_screen()` function from `actions/screen_vision.py`
- **FR-002**: The agent MUST produce a structured plan (ordered list of steps) before executing any actions
- **FR-003**: The agent MUST execute actions using the existing tool registry (`core/tool_registry.py`): `browser_control`, `shell_run`, `list_processes`, `kill_process`, `find_large_files`, `cleanup_folder`, `open_app`
- **FR-004**: The agent MUST capture the resulting screen state after each UI-affecting action and verify the expected change occurred
- **FR-005**: The agent MUST detect execution failures via screen observation (unexpected dialogs, unchanged state, error messages)
- **FR-006**: The agent MUST attempt up to 2 automatic recovery strategies before escalating to the user
- **FR-007**: The agent MUST expose a human approval mode where each UI-affecting action requires user confirmation
- **FR-008**: The agent MUST support direct mouse and keyboard control (click at coordinates, type text, drag) as new low-level actions
- **FR-009**: The agent MUST display progress and reasoning in the JARVIS UI via `write_log()` updates at each step
- **FR-010**: The agent MUST persist the current plan, step status, and execution history in memory for reflection
- **FR-011**: The agent SHOULD decompose high-level goals into sub-tasks automatically when explicit steps are not provided
- **FR-012**: The agent SHOULD log full execution history (plan, observations, actions, reflections) to a structured file
- **FR-013**: The agent MUST respect the `_user_initiated` security gate — no autonomous actions before user interaction

### Key Entities *(include if feature involves data)*

- **AgentPlan**: Ordered list of steps, each with description, action type, parameters, status (pending/in_progress/completed/failed), and reflection notes. Stored in memory.
- **StepResult**: Outcome of a single step execution, containing observed screen state text, success/failure flag, error details, and timestamp.
- **AgentSession**: A complete run from goal receipt to final delivery, containing the original goal, the plan, all step results, and final summary. Persisted to logs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: User can give a 3-step desktop task and the agent completes it without human intervention in under 60 seconds
- **SC-002**: Agent detects and recovers from at least 2 distinct error types (app not found, unexpected dialog) automatically
- **SC-003**: Human approval mode adds no more than 3 seconds of overhead per approved action
- **SC-004**: Progress updates appear in the UI within 1 second of each step transition
- **SC-005**: Agent successfully plans and executes at least 80% of a test suite of 10 common desktop tasks on first attempt
- **SC-006**: Agent respects the `_user_initiated` gate — 0 false-positive autonomous triggers in 100 test runs

## Assumptions

- Desktop observation is performed via Gemini Vision through the existing `analyze_screen()` function — no new vision infrastructure
- Mouse/keyboard control is implemented via platform-native APIs (Windows: `pywinauto` or `pyautogui`, Linux/macOS: cross-platform fallback)
- The existing tool registry handles all application-level actions (open app, browser, shell, file ops, process mgmt)
- The agent runs in the same Python process as JARVIS, sharing the tool registry and UI references
- Screen observation requires an unlocked, visible desktop session
- The agent is a single-user feature — no multi-user or concurrent session support in v1
- Maximum plan depth is 20 steps per goal (cap prevents runaway execution)
- The agent uses the same Gemini model that JARVIS uses for LLM reasoning (planning, reflection)
