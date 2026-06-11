<!--
  Sync Impact Report — v0.0.0 → v1.0.0
  - Initial constitution created
  - Added: Principle I (Code Quality & Maintainability)
  - Added: Principle II (Testing Excellence & Coverage)
  - Added: Principle III (User Experience Consistency)
  - Added: Principle IV (Performance & Responsiveness)
  - Added: Principle V (Security & Privacy)
  - Added: Section (Technology & Platform Standards)
  - Added: Section (Development Workflow & Quality Gates)
  - Added: Governance rules
  - Templates requiring updates: plan-template ✅ (generic, no changes needed),
    spec-template ✅ (generic, no changes needed),
    tasks-template ✅ (generic, no changes needed)
  - Follow-up TODOs: none
  - v2.0.0: Added Phase -1 Pre-Implementation Gates (Articles VII-IX),
    Project Structure (7.3), Development Practices (8.1, 9.1),
    realistic test environments, CLI interface requirements,
    Strict TDD gate
  - v2.1.0: Added Article X (Requirements-First Gate),
    Specification Standards (10.1, 10.2), Amendment Process (4.2)
  - v2.1.1: Added Implementation Plan Standard (10.3)
-->
# J.A.R.V.I.S Constitution

## Core Principles

### I. Code Quality & Maintainability (NON-NEGOTIABLE)
- Type hints on ALL public signatures — no exceptions
- `snake_case` for functions/variables, `PascalCase` for classes
- Prefer `pathlib.Path` over `os.path`
- **Never** suppress types: no `# type: ignore`, no `Any` casts
- Use dict dispatch pattern over `elif` chains for tool routing
- Every `except` MUST log via `traceback.print_exc()` before pass.
  Exceptions: NDJSON stream parsers (expected partial chunks),
  best-effort fallback functions (outer caller handles logging)
- Extract submodules rather than bloating single files past 500 LOC

### II. Testing Excellence & Strict TDD (NON-NEGOTIABLE)
- Current baseline: **1976+ tests, 0 pre-existing failures** — MUST
  be maintained or improved with every change
- **Strict Red-Green-Refactor** — No implementation code shall be
  written before:
  1. Unit tests are written
  2. Tests are validated and approved by the user
  3. Tests are confirmed to FAIL (Red phase)
- **Realistic test environments**:
  - Prefer real databases over mocks
  - Use actual service instances over stubs
  - Contract tests mandatory before implementation
- New module = new test class in `tests/test_smoke.py` or new
  `tests/test_<module>.py`
- Use `unittest` framework — no pytest. `@patch` allowed only for
  side-effect isolation (browser opens, URL calls)
- Runner: `.venv/bin/python3 -m unittest tests.test_smoke -v`
- Coverage target: all application modules, 0 skips

### III. User Experience Consistency
- UI state indicators MUST be consistent: 🟢 Listening, 🔵 Speaking,
  🟡 Thinking, 🔴 Error, 🟣 Muted, ⚪ Paused
- Tkinter concentric ring animation renders at all states
- Audio pipeline: 48kHz primary processing, graceful 16kHz fallback.
  RNNoise enabled by default, silent bypass if unavailable
- Turkish text MUST be NFC-normalized before processing. Skill regex
  patterns MUST include ASCII fallback variants
  (ş→s, ç→c, ü→u, ö→o, ğ→g, ı→i)
- UI Settings panel exposes backend, voice model, and TTS selection
  consistently

### IV. Performance & Responsiveness
- Voice pipeline (STT → AI → TTS) MUST complete under 3s on target
  hardware
- Background threads (wake word, VAD, skill hot-reload) MUST NOT
  block UI main loop
- Application startup under 2s on target hardware
- Memory: JSON-backed key-value store only — no unbounded caches
- Prompt construction and tool dispatch complete under 100ms

### V. Security & Privacy
- `_user_initiated` gate: AI tools with side effects (browser, file
  ops, shell) MUST check user-initiated flag before executing
- OS detection injected into system prompt at build time — prevents
  cross-platform command generation
- Input validation: STT text cap 10k chars, tool call arg cap 500
  chars, total tool call cap 2k chars
- Tool name whitelist — unknown names rejected
- API keys in gitignored files only: `config/api_keys.json`

### VI. Standalone Library First (NON-NEGOTIABLE)
- Every feature tracked in Specify MUST begin its existence as a
  standalone installable Python library under `packages/<name>/`
- No feature shall be implemented directly within application code
  without first being abstracted into a reusable library component
- Library packages use `src/` layout with `pyproject.toml` and expose
  a clean public API via `__init__.py`
- Application-specific wiring (dependency injection, provider
  adapters, environment setup) belongs in the application layer, not
  the library
- Exception: trivial single-file utilities that have no reuse
  potential outside the application
- Rationale: decouples feature development from application
  constraints, enables independent testing, and enforces clean
  API boundaries from day one
- **CLI interface requirements**: Every library package MUST expose
  a CLI interface that:
  - Accepts text as input (via stdin, command-line arguments, or files)
  - Produces text as output (via stdout)
  - Supports JSON format for structured data exchange (opt-in via
    `--json` or `--format json` flag)

## Technology & Platform Standards

**Runtime**: Python 3.10+ (3.13 preferred), `.venv` virtual env

**Backend**: Provider abstraction (`core/provider_base.py`) with
  Gemini Live API and Ollama HTTP implementations

**Audio**: RNNoise (C ctypes wrapper, 48kHz), Sounddevice,
  Faster-Whisper STT, Piper TTS / Edge-TTS / Windows Speech

**UI**: Tkinter, single `JarvisUI` class, submodules via `importlib`
  (no circular imports)

**Tool Registry**: Single `core/tool_registry.py` — declarations,
  handler map, valid_tools set in one place

**Primary Platform**: Windows 10/11 | **Secondary**: Linux, macOS

## Project Structure

**7.3 Minimal Project Structure** (NON-NEGOTIABLE):
- Maximum 3 projects for initial implementation
- Additional projects require documented justification in the
  relevant spec or plan

## Development Practices

**8.1 Framework Trust** (NON-NEGOTIABLE):
- Use framework features directly rather than wrapping them
- Avoid creating abstraction layers over framework APIs unless
  the abstraction provides clear cross-cutting value (testing,
  logging, or feature gating)

**9.1 Integration-First** (NON-NEGOTIABLE):
- Contract tests MUST be defined and written before implementation
- Real service instances preferred over stubs and mocks
- Contracts define the interaction boundary between components

## Specification Standards

**10.1 Ambiguity-First Spec Writing**:
- When creating a spec from a user prompt, ALL ambiguities MUST be
  marked inline with `[NEEDS CLARIFICATION: specific question]`
- Do NOT guess unspecified details — if the prompt doesn't specify
  something, mark it as needing clarification

**10.2 Requirement Completeness Checklist**:
Before a spec is considered complete:
- [ ] No `[NEEDS CLARIFICATION]` markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] No speculative or "might need" features
- [ ] All phases have clear prerequisites and deliverables

### 10.3 Implementation Plan Standard
Implementation plans MUST remain high-level and readable.
Any code samples, detailed algorithms, or extensive technical
specifications MUST be placed in a separate `implementation-details/`
file co-located with the plan.

## Phase -1: Pre-Implementation Gates

Before ANY implementation work begins, ALL four gates MUST pass:

### Article VII — Simplicity Gate
- [ ] Using ≤3 projects?
- [ ] No future-proofing? (implement only what is needed now)

### Article VIII — Anti-Abstraction Gate
- [ ] Using framework directly? (no unnecessary wrappers)
- [ ] Single model representation? (one source of truth for each domain concept)

### Article IX — Integration-First Gate
- [ ] Contracts defined? (interaction boundaries specified)
- [ ] Contract tests written? (tests confirm contracts before implementation)

### Article X — Requirements-First Gate
Before ANY design or implementation discussion:
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)

## Development Workflow & Quality Gates

**Pre-Merge Checklist** (ALL MUST pass):
1. `lsp_diagnostics` clean on changed files
2. `.venv/bin/python3 -m unittest tests.test_smoke -v` — all pass
3. `build.sh` / `build.ps1` compiles clean
4. No dead code, no placeholder/mock tests
5. API keys never committed

**Skills**: New skills go in `skills/<name>/<name>_skill.py` with
  `route_<name>_request()`. Hot-reload watcher at 3s interval.
  Each skill MUST include Turkish regex with ASCII fallback.

**Commit Style**: Concise, describes WHAT and WHY, not HOW. No emoji.

## Governance

This constitution **supersedes all other individual practices**. All
PRs, reviews, and implementation MUST verify compliance with every
applicable principle.

### 4.2 Amendment Process
Modifications to this constitution require:
- Explicit documentation of the rationale for change
- Review and approval by project maintainers
- Backwards compatibility assessment

Semantic version bump:
- MAJOR: Principle removal or redefinition
- MINOR: New principle or expanded guidance
- PATCH: Clarifications, typo fixes

Use `CLAUDE.md` and `AGENTS.md` for day-to-day guidance; this
constitution defines non-negotiable governing principles.

**Version**: 2.1.1 | **Ratified**: 2026-06-10 | **Last Amended**: 2026-06-10
