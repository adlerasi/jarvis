# Feature Specification: Memory Store

**Feature Branch**: `005-memory-store`

**Created**: 2026-06-10

**Status**: Draft

**Input**: JSON-backed key-value store with search — standalone library

---

## User Stories

### User Story 1 — Standalone Memory Store Library (Priority: P1)
The JSON key-value store logic (CRUD, deep merge, persistence) is extracted from `memory/memory_manager.py` into `packages/memory-store/`. JARVIS imports from the library with a configurable file path.

**Independent Test**: Run `pip install -e packages/memory-store/`, import `MemoryStore`, create an instance with a temp file path, store and retrieve a value.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** imported, **Then** no JARVIS-specific imports exist in the library code
2. **Given** a MemoryStore instance with a file path, **When** `set("key", "value")` is called, **Then** the value is persisted to disk
3. **Given** a stored key, **When** `get("key")` is called, **Then** the original value is returned

### User Story 2 — Deep Merge (Priority: P1)
Nested dictionary merge: when updating, nested dicts are merged recursively (not replaced), non-dict values are overwritten.

**Independent Test**: `store.set("user", {"name": "Ali"})` → `store.merge("user", {"age": 30})` → `store.get("user")` returns `{"name": "Ali", "age": 30}`.

**Acceptance Scenarios**:
1. **Given** a nested dict, **When** merged with overlapping keys, **Then** nested keys are combined
2. **Given** a string value, **When** merged with a dict, **Then** the string is replaced by the dict
3. **Given** flat keys, **When** merged, **Then** new keys are added

### User Story 3 — Text Search (Priority: P1)
Search across all stored data by normalized text matching. Supports Turkish character normalization.

**Independent Test**: `store.set("city", "İstanbul")` → `store.search("istanbul")` returns matching entries.

[NEEDS CLARIFICATION: Should search return full entries or just matching keys? Current implementation matches keys and values and deletes by match. What's the exact search API signature?]

**Acceptance Scenarios**:
1. **Given** stored data, **When** searched by a normalized keyword, **Then** matching entries are returned
2. **Given** Turkish text, **When** searched with ASCII fallback, **Then** matches are found (e.g., "İstanbul" matches "istanbul")
3. **Given** no matches, **When** searched, **Then** empty result is returned

### User Story 4 — Delete by Match (Priority: P2)
Delete entries by exact category/key path or by text match.

**Independent Test**: `store.delete(category="user", key="name")` removes that specific entry. `store.delete(match_text="Ali")` removes all entries matching "Ali".

**Acceptance Scenarios**:
1. **Given** an entry, **When** deleted by category/key, **Then** the entry is removed from disk
2. **Given** an entry, **When** deleted by match_text, **Then** the first matching entry is removed
3. **Given** a non-existent key, **When** deleted, **Then** a clear error message is returned

### User Story 5 — Prompt Formatting (Priority: P2)
Format stored memory into a human-readable string for LLM prompts.

[NEEDS CLARIFICATION: Should the formatting logic be part of the library or the app layer? The current `format_memory_for_prompt` is specific to JARVIS's prompt structure. If in the library, it should be generic key=value formatting; app layer adds JARVIS-specific formatting on top.]

**Independent Test**: Call `store.format()` on a populated store, verify output contains stored keys and values in readable format.

**Acceptance Scenarios**:
1. **Given** stored data, **When** `format()` is called, **Then** output is a readable string with key=value pairs
2. **Given** an empty store, **When** `format()` is called, **Then** empty string is returned

### User Story 6 — CLI Interface (Priority: P2)
The library MUST expose a CLI conforming to Principle VI: get, set, delete, search, preview commands with `--json` flag.

**Independent Test**: `python -m memory_store set user name Ali --json` → valid JSON output confirming the write.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** `python -m memory_store get user name` is run, **Then** the stored value is printed to stdout
2. **Given** `--json` flag, **When** any command is run, **Then** output is valid JSON
3. **Given** an invalid command, **When** run, **Then** a clear error message is printed to stderr

---

## Resolved Ambiguities

1. ✅ **Search API** — `search(text)` returns a list of `{"category", "key", "value"}` dicts for all matches. Simple and complete.
2. ✅ **Prompt formatting** — Library provides a generic `format()` that returns `category/key: value` lines. JARVIS-specific formatting (whatsapp aliases, etc.) stays in the app layer.

## Out of Scope
- Voice memory / conversation transcripts (separate feature)
- Session management
- Embedding/vector search (future)
- Migration between storage backends (future)
- Encryption at rest (future)

## Requirement Completeness Checklist
- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] No speculative or "might need" features
- [x] All phases have clear prerequisites and deliverables
