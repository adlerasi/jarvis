# Feature Specification: Skill Engine

**Feature Branch**: `004-skill-engine`

**Created**: 2026-06-10

**Status**: Draft

**Input**: Mevcut SkillManager'ı standalone library olarak çıkarma (Principle VI)

---

## User Stories

### User Story 1 — Standalone Skill Engine Library (Priority: P1)
The skill loading, hot-reload, routing, and lifecycle management logic is extracted from `core/skill_manager.py` into `packages/skill-engine/`. JARVIS imports from the library and wires its application-specific handlers.

**Independent Test**: Run `pip install -e packages/skill-engine/`, import `SkillEngine` from it, load a test skill directory, verify routing works without JARVIS imports.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** imported, **Then** no JARVIS-specific imports exist in the library code
2. **Given** a skill directory with valid skills, **When** `SkillEngine.load_all()` is called, **Then** all skills are loaded and routable
3. **Given** the library is installed, **When** `pip show skill-engine` is run, **Then** metadata (name, version) is correct

### User Story 2 — Skill Contract & Interface (Priority: P1)
Every skill MUST follow a defined contract: `route_<name>_request(user_text: str) -> str | None`. The library validates this contract on load and rejects malformed skills with clear error messages. Additional lifecycle hooks (`on_load`, `on_unload`, `on_error`) are optional — no-op by default, skills implement them if needed. triggers.json file tracking stays in the library for change detection; trigger content processing is the app layer's responsibility.

**Independent Test**: Create a skill without a route function → verify library rejects it with `SkillLoadError`. Create a skill with an invalid route signature → verify rejection.

**Acceptance Scenarios**:
1. **Given** a skill directory with no `route_` function, **When** loaded, **Then** `SkillLoadError` is raised
2. **Given** a skill directory with a valid route function, **When** loaded, **Then** the skill is registered and callable
3. **Given** a loaded skill, **When** `route()` matches, **Then** the route function result is returned

### User Story 3 — Hot-Reload Watcher (Priority: P2)
The file-watcher thread that automatically detects skill changes (new skills, modified skills, removed directories) is part of the library with configurable interval and pluggable notification callbacks. Uses `threading` (same as current implementation).

**Independent Test**: Create a watcher, add a new skill file to the watched directory → verify the watcher fires a "loaded" event within `interval * 2` seconds.

**Acceptance Scenarios**:
1. **Given** a running watcher, **When** a new skill directory + skill file appears, **Then** it's auto-loaded without manual intervention
2. **Given** a running watcher, **When** a skill file is modified, **Then** it's hot-reloaded
3. **Given** a running watcher, **When** a skill directory is removed, **Then** the skill is disabled

### User Story 4 — CLI Interface (Priority: P2)
The library MUST expose a CLI interface conforming to Principle VI:
- List skills (`skill-engine list`)
- Get skill info (`skill-engine info <name>`)
- Reload all (`skill-engine reload`)
- JSON output via `--json` flag

**Independent Test**: Run `python -m skill_engine list --json` → verify valid JSON array with expected keys.

**Acceptance Scenarios**:
1. **Given** the library is installed, **When** `python -m skill_engine list` is run, **Then** output is human-readable text via stdout
2. **Given** `--json` flag is passed, **When** `python -m skill_engine list --json` is run, **Then** output is valid JSON
3. **Given** a non-existent skill, **When** `python -m skill_engine info unknown` is run, **Then** a clear error message is printed

### User Story 5 — JARVIS Integration (Priority: P1)
JARVIS's `core/skill_manager.py` becomes a thin adapter that imports from `skill_engine` and passes JARVIS-specific configuration (custom skill directory path, app-level callbacks).

**Independent Test**: After integration, `get_skill_manager()` returns a working instance that loads all 18 JARVIS skills identically to the current implementation.

**Acceptance Scenarios**:
1. **Given** JARVIS starts, **When** `get_skill_manager()` is called, **Then** it returns a configured `SkillEngine` instance with `SKILLS_DIR` pointing to JARVIS's `skills/`
2. **Given** a JARVIS skill is modified, **When** the watcher detects the change, **Then** the skill is reloaded (same behavior as current)
3. **Given** JARVIS is running, **When** `skill_manager.route("merhaba")` is called, **Then** it matches the greeting skill (same as current behavior)

---

## Resolved Ambiguities

1. ✅ **Lifecycle hooks** — Eklenecek: `on_load(skill_id)`, `on_unload(skill_id)`, `on_error(skill_id, exception)`.
   Varsayılan olarak boş (no-op), skill'ler ihtiyaç duyarsa implemente eder.
2. ✅ **triggers.json** — Library'de kalır, sadece dosya değişiklik tespiti (mtime) için kullanılır.
   Trigger içeriğini işleme app katmanının sorumluluğundadır. En az karışıklık bu yaklaşımda.
3. ✅ **Watcher altyapısı** — `threading` devam. Basit polling loop için ideal, async ek yük getirir.

## Out of Scope
- Skill development/debugging tools (separate feature)
- Skill marketplace/registry (separate feature)
- Multi-process skill isolation (future)
- Skill dependency management (future)

---

## Requirement Completeness Checklist
- [x] No `[NEEDS CLARIFICATION]` markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] No speculative or "might need" features
- [x] All phases have clear prerequisites and deliverables
