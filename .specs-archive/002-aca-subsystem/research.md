# Technical Research: ACA Subsystem

**Phase**: 0 — Research & Decision Record
**Date**: 2026-06-10
**Status**: All decisions confirmed — no open clarifications

## Decision Record

### 1. Mouse/Keyboard Control Library

**Decision**: `pyautogui` (cross-platform, pure Python)

**Rationale**: Lightweight, pure Python (no C compilation needed), works on Windows/Linux/macOS out of the box. Handles click, drag, type, key combo, screenshot (though we use our own screen_vision for analysis). Matches the zero-native-dependency philosophy of JARVIS (RNNoise is the only C dep).

**Alternatives considered**:
- `pywinauto` — Windows-only, powerful but overkill for basic click/type. Adds Windows-only dependency.
- `win32api` / `SendInput` — native Windows, but breaks cross-platform support.
- `pynput` — good keyboard/mouse monitoring, but control APIs are less ergonomic than pyautogui.

### 2. LLM Provider for Planning & Reflection

**Decision**: Reuse active JARVIS provider (Gemini or Ollama) via existing provider abstraction.

**Rationale**: The ACA planner and reflection loop need LLM reasoning (task decomposition, result evaluation). Rather than creating a separate LLM connection, the ACA calls `jarvis._execute_tool()` for tool actions and uses the provider's LLM capabilities through the same pattern the existing system uses. This means no additional API keys, no redundant connections, and consistent model behavior.

**Alternatives considered**:
- Dedicated LLM client — wastes resources, duplicates connection logic.
- Local model only — limits planning quality when user switches to Gemini.

### 3. Execution Model (In-Process vs Subprocess)

**Decision**: In-process, background thread.

**Rationale**: The ACA needs access to `jarvis` reference (UI, tool registry, config). Running in-process gives direct access without IPC overhead. Background thread prevents blocking the voice pipeline. The SkillManager already uses this exact pattern (daemon thread + hot-reload).

**Alternatives considered**:
- Subprocess — cleaner isolation but loses direct jarvis access. Would need IPC (pipes/sockets) for tool dispatch.
- Async task — possible but the ACA may have long-running steps (browser navigation, file operations) that don't map well to asyncio.

### 4. Observation Strategy

**Decision**: Poll-based observation before each UI-affecting step, using existing `analyze_screen()`.

**Rationale**: The existing screen_vision module already handles screen capture + Gemini Vision analysis with retry logic. The observer wraps this and adds process list tracking (via psutil) for a richer world state. Poll-on-step is simpler than continuous observation and sufficient for the ACA's use case.

**Alternatives considered**:
- Continuous observer thread — higher overhead, constant Gemini API costs. Better for real-time UI change detection but not needed for step-based execution.
- Event-based (UI automation events) — Windows-only, complex, adds dependency.

### 5. Human Approval UI Pattern

**Decision**: Use existing `focus_panel()` + `write_log()` from JarvisUI, with new approval callback mechanism.

**Rationale**: The JARVIS UI already has `focus_panel()` for surfacing sections and `write_log()` for text output. Approval requests are a natural extension: the approval_manager halts execution, calls `focus_panel("agent")` to bring the Agent Panel into view, writes the action details via `write_log()`, and sets a callback for user response (Approve/Deny buttons rendered in the Agent Panel).

### 6. Risk Classification

**Decision**: Static classification table in `approval_manager.py`.

| Risk Level | Actions | Approval Required |
|------------|---------|-------------------|
| Low | observe, open_app, browser_control (search), get_system_health | No |
| Medium | shell_run (read-only), browser_control (download), list_processes | Yes (in approval mode) |
| High | kill_process, cleanup_folder, control_service, shell_run (write), file deletion | Always (even outside approval mode) |

**Rationale**: Simple, predictable, easy to audit. Can be extended with dynamic risk scoring later.

### 7. Workflow Learning Strategy

**Decision**: Store normalized goal text → task graph JSON in agent memory. Retrieve by text similarity (keyword overlap + TF-IDF cosine similarity via `sklearn` or pure-Python fallback).

**Rationale**: The existing `memory/memory_manager.py` is JSON-backed, which maps directly to storing task graphs as JSON. Text similarity retrieval is lightweight and doesn't require a vector database. Pure-Python fallback avoids adding sklearn as a dependency if not already present.
