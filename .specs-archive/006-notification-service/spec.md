# Feature Specification: Notification Service

**Feature Branch**: `006-notification-service`

**Created**: 2026-06-10

**Status**: Draft

**Input**: Cross-platform desktop notification library with unified API

---

## User Stories

### User Story 1 — Unified Desktop Notification API (Priority: P1)
A single `notify(title, message, priority)` function that works across Linux, Windows, and macOS using native notification mechanisms (notify-send, PowerShell BurntToast, osascript). No external dependencies.

**Independent Test**: Call `notify("Test", "Hello from library")` and verify the notification appears on the desktop.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** `notify()` is called, **Then** a desktop notification is displayed
2. **Given** no notification backend is available, **When** `notify()` is called, **Then** it falls back to stdout with a warning
3. **Given** priority is set to "critical", **When** `notify()` is called, **Then** the notification has urgent appearance (where supported)

### User Story 2 — Event-Driven Notification Bus (Priority: P2)
A `NotificationBus` that decouples notification emitters from handlers. Emitters publish events; handlers subscribe and deliver via their preferred channel (desktop, voice, log).

**Independent Test**: Create a bus, subscribe a desktop handler, publish a "reminder" event with title+message → verify the handler fires.

**Acceptance Scenarios**:
1. **Given** a NotificationBus, **When** a handler subscribes, **Then** `subscribe()` returns a subscription token
2. **Given** a subscription, **When** an event is published, **Then** the handler is called with the event data
3. **Given** a subscription, **When** `unsubscribe()` is called, **Then** the handler stops receiving events

### User Story 3 — Voice Notification Channel (Priority: P2)
An optional `VoiceHandler` that speaks notifications via a configurable TTS callable. Useful for voice assistants like JARVIS where audio alerts matter.

[NEEDS CLARIFICATION: Should the voice handler be in the library or in JARVIS app layer? The library can define a `VoiceHandler` that takes a `speak: Callable[[str], None]` parameter. JARVIS passes its TTS function.]

**Independent Test**: Create a VoiceHandler with a lambda that captures text → verify the lambda is called with the notification message.

**Acceptance Scenarios**:
1. **Given** a VoiceHandler with a speak callable, **When** a notification is sent, **Then** the speak callable is invoked with the message
2. **Given** no speak callable, **When** a notification is sent, **Then** it's silently ignored (no crash)

### User Story 4 — Log Channel (Priority: P2)
A `LogHandler` that writes notifications to a file or stdout with timestamps.

**Independent Test**: Create a LogHandler with a temp file path, send a notification, verify the file contains the expected entry.

**Acceptance Scenarios**:
1. **Given** a LogHandler with a file path, **When** a notification is sent, **Then** the file contains a timestamped entry
2. **Given** a LogHandler with stdout, **When** a notification is sent, **Then** the entry is printed to stdout

### User Story 5 — CLI Interface (Priority: P2)
CLI conforming to Principle VI: send notification, list channels, test command, `--json` flag.

**Independent Test**: `python -m notify_core send "Baslik" "Mesaj"` → notification appears. `python -m notify_core send "Baslik" "Mesaj" --json` → JSON output confirming delivery.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** `python -m notify_core send "Title" "Body"` is run, **Then** a desktop notification appears
2. **Given** `--json` flag, **When** any command is run, **Then** output is valid JSON

---

## Resolved Ambiguities

1. ✅ **Voice handler** — Library defines `VoiceHandler(speak=None)` where `speak` is an optional `Callable[[str], None]`. JARVIS provides its TTS function via this parameter. When None, voice delivery is silently skipped.

## Out of Scope
- Push notifications to mobile devices (future)
- Notification persistence/queueing across restarts (future)
- Notification grouping/deduplication (future)
- Rich notifications with images/actions (future)

## Requirement Completeness Checklist
- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] No speculative or "might need" features
- [x] All phases have clear prerequisites and deliverables
