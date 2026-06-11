# Data Model: ACA Subsystem

**Date**: 2026-06-10
**Source**: [spec.md](./spec.md) — Key Entities section + FR-009, FR-024, FR-025

## Entities

### AgentGoal

Represents the user's high-level objective for an ACA session.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `goal_id` | str (UUID) | Yes | Unique identifier |
| `text` | str | Yes | User's goal description (raw text) |
| `normalized_text` | str | Yes | NFC-normalized, lowercased, stopword-removed version for matching |
| `status` | enum | Yes | `pending` / `active` / `completed` / `failed` / `cancelled` |
| `created_at` | ISO datetime | Yes | When goal was received |
| `started_at` | ISO datetime | No | When execution began |
| `completed_at` | ISO datetime | No | When execution finished |
| `plan` | TaskGraph | No | The generated task graph |
| `result_summary` | str | No | Final summary reported to user |
| `error_count` | int | Yes | Total errors encountered (default 0) |
| `session_id` | str | Yes | Links to AgentSession |

### TaskGraph

A directed acyclic graph (DAG) of steps representing the execution plan.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `graph_id` | str (UUID) | Yes | Unique identifier |
| `goal_id` | str | Yes | Parent goal |
| `nodes` | list[TaskNode] | Yes | All steps in execution order |
| `edges` | list[tuple[int,int]] | Yes | Dependency edges: `(from_step_id, to_step_id)` |
| `created_at` | ISO datetime | Yes | When plan was generated |
| `version` | int | Yes | Incremented on each replan (default 1) |

**Serialization**: JSON file at `memory/agent/goals/{goal_id}/plan.json`

### TaskNode

A single atomic step within a TaskGraph.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `step_id` | int | Yes | 1-based index within the graph |
| `description` | str | Yes | Human-readable action description |
| `action_type` | enum | Yes | `observe` / `tool` / `shell` / `input` / `approval_wait` / `llm_reason` |
| `tool_name` | str | No | Tool registry name (for `tool` action_type) |
| `params` | dict | No | Parameters to pass to the tool |
| `dependencies` | list[int] | Yes | step_ids that must complete first |
| `status` | enum | Yes | `pending` / `in_progress` / `completed` / `failed` / `skipped` |
| `retry_count` | int | Yes | Number of retry attempts (default 0, max 2) |
| `confidence` | float | No | 0.0–1.0 confidence from observer (null if not observed) |
| `observation_before` | str | No | Screen state text captured before execution |
| `observation_after` | str | No | Screen state text captured after execution |
| `result` | str | No | Tool return value or error message |
| `reflection` | str | No | Reflection loop evaluation text |
| `started_at` | ISO datetime | No | When step execution began |
| `completed_at` | ISO datetime | No | When step finished |

### WorldState

Snapshot of the desktop environment at a point in time.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | float | Yes | `time.time()` when captured |
| `screen_text` | str | Yes | Output of `analyze_screen()` |
| `active_window_title` | str | Yes | Current foreground window title |
| `active_window_pid` | int | No | PID of foreground window |
| `running_processes` | list[dict] | No | Top processes: `[{pid, name, cpu%, memory%}]` |
| `recent_files` | list[str] | No | Recently modified files in watch dirs (max 10) |

### ApprovalRequest

Action requiring human confirmation before execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | str (UUID) | Yes | Unique identifier |
| `step_id` | int | Yes | Step requesting approval |
| `goal_id` | str | Yes | Parent goal |
| `action_description` | str | Yes | Human-readable description of the action |
| `tool_name` | str | Yes | Tool to be called |
| `params` | dict | Yes | Parameters to be passed |
| `risk_level` | enum | Yes | `low` / `medium` / `high` |
| `status` | enum | Yes | `pending` / `approved` / `denied` |
| `requested_at` | ISO datetime | Yes | When approval was requested |
| `responded_at` | ISO datetime | No | When user responded |
| `response_notes` | str | No | Optional user note with their decision |

### AgentSession

Complete record of an ACA run from goal to completion.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | str (UUID) | Yes | Unique identifier |
| `goal` | AgentGoal | Yes | The goal that drove this session |
| `plan_versions` | list[TaskGraph] | Yes | All plan versions (original + replans) |
| `approval_requests` | list[ApprovalRequest] | Yes | All approvals during this session |
| `world_states` | list[WorldState] | Yes | All observations captured |
| `started_at` | ISO datetime | Yes | Session start |
| `completed_at` | ISO datetime | No | Session end |
| `final_summary` | str | No | Report delivered to user |
| `was_successful` | bool | No | Whether goal was achieved |

**Serialization**: JSON file at `memory/agent/sessions/{session_id}.json`

### WorkflowTemplate

Reusable plan learned from a completed goal.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `template_id` | str (UUID) | Yes | Unique identifier |
| `intent_hash` | str | Yes | Hash of normalized goal text for fast lookup |
| `goal_text` | str | Yes | Original goal text |
| `task_graph_json` | dict | Yes | Serialized task graph (stripped of session-specific observation data) |
| `success_count` | int | Yes | How many times this template completed successfully |
| `failure_count` | int | Yes | How many times it failed |
| `last_used` | ISO datetime | No | Last retrieval timestamp |
| `created_at` | ISO datetime | Yes | When template was saved |
| `tags` | list[str] | No | Auto-extracted keywords (e.g., ["browser", "download", "file"]) |

**Serialization**: JSON file at `memory/agent/templates/{template_id}.json`

## Entity Relationships

```text
User
  └─ provides ──► AgentGoal
                    └─ has ──► TaskGraph (1..N — replanning creates new versions)
                                 └─ contains ──► TaskNode (1..*)
                                                    └─ may trigger ──► ApprovalRequest (0..*)
                    └─ captures ──► WorldState (0..*)
                    └─ logged by ──► AgentSession (1)
                                      └─ may produce ──► WorkflowTemplate (0..1)
```

## Persistence Strategy

All entities serialize to JSON in the `memory/agent/` directory:

```
memory/
├── agent/
│   ├── current_goal.json       # Single active goal (or null)
│   ├── goals/
│   │   └── {goal_id}/
│   │       ├── plan.json       # TaskGraph
│   │       └── session.json    # AgentSession
│   ├── sessions/
│   │   └── {session_id}.json   # Full session archive
│   ├── templates/
│   │   └── {template_id}.json  # WorkflowTemplate
│   └── index.json              # Lookup index: goal_text → template_ids
```

This mirrors the existing `memory/memory.json` pattern while keeping ACA data in a dedicated subdirectory.
