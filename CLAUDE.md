# J.A.R.V.I.S — Development Guidelines

## Architecture

- **Core loop**: `main.py` → Provider (Gemini/Ollama) streaming → `JarvisUI (ui.py)` for display
- **Audio pipeline**: `audio/noise_suppressor.py` (RNNoise ctypes wrapper) → 48kHz processing or 16kHz upsampling pipeline → integrated in `core/ollama_provider.py` before VAD
- **VAD system**: Unified "Fahrettin" VAD wrapper (`core/fahrettin_vad.py`) wrapping `VADEngine` (`core/vad_engine.py`). Backend chain: Silero → WebRTC → Energy. Auto-downsampling from 48kHz to 16kHz. Thread-safe.
- **Wake word**: `core/wake_word.py` — openWakeWord → Porcupine → Energy fallback chain. Activated in `main.py`, gates STT in `ollama_provider.py`.
- **Provider abstraction**: `core/provider_base.py` (abstract interface) → `core/gemini_provider.py` (Gemini Live API) / `core/ollama_provider.py` (Ollama HTTP). Providers receive `jarvis` reference for UI, tools, config, audio.
- **Tool registry**: `core/tool_registry.py` — single source for all 40 tools (Gemini declarations + Ollama prompt text + handler map + valid_tools set)
- **Text utils**: `core/text_utils.py` — shared `clean_transcript_text()` and `fix_turkish_syllable_split()`
- **UI layer**: Tkinter-based, single `JarvisUI` class in `ui.py`, rendered via `ui/` package
- **Actions**: Self-contained modules in `actions/` — each exports 1-3 pure-ish functions
- **Memory**: JSON-backed, key-value store via `memory/memory_manager.py`
- **Config**: `config/api_keys.json` + `config/audio.yaml` — loaded via `app_config.py`

## UI Package (`ui/`)

| File | Purpose |
|------|---------|
| `__init__.py` | Re-exports all names from `ui.py` for backward compat |
| `ui.py` | Legacy main UI (1985 lines); will be slimmed over time |
| `sound_manager.py` | Audio playback — ambient loop, foreground SFX, volume |
| `orb_canvas.py` | Orb particle rendering — stateless, pure math |

**Import rule**: Submodules (`ui/sound_manager.py`, `ui/orb_canvas.py`) MUST NOT `from ui import ...` at module level — circular imports. Pass values as parameters or import via `importlib` (see `__init__.py`).

## Code Style

- Follow existing patterns strictly (disciplined codebase)
- `snake_case` for functions/variables, `PascalCase` for classes
- Type hints on all public signatures
- `# ── Section separators ──` for large files (80+ lines)
- Prefer `pathlib.Path` over `os.path`
- Exception handling: log via `traceback.print_exc()`, propagate via `write_log()`

## Tool Dispatch in main.py

`_execute_tool` uses a **dict dispatch** pattern:

```python
_TOOL_HANDLERS = {
    "open_app": "_handle_open_app",
    "sys_info": "_handle_sys_info",
    ...
}
```

Each handler is `async def _handle_<name>(self, args, loop) -> str`.
Adding a new tool = add handler method + registry entry. No elif chain.

## Skill Manager (v3 — Hot-Reload)

- **Location**: `core/skill_manager.py` — singleton, auto-loads all skills from `skills/` directory
- **Pattern**: Each skill folder (`skills/<name>/`) must contain:
  - `<name>_skill.py` with a `route_<name>_request(user_text) → str | None` function
  - `SKILL.md` — optional (YAML frontmatter)
- **Metadata** (optional, recommended):
  - `SKILL_ID` — unique ID (format: `<name>-v<ver>`, e.g. `weather-v1`). Falls back to folder name if None/empty.
  - `SKILL_NAME` — display name. Falls back to folder name.
  - `SKILL_VERSION` — semver string. Falls back to `"0.0.0"`.
- **Flow**: `_on_text_command()` calls `skill_manager.route(text)` BEFORE sending to LLM
  - If skill matches → execute directly, return result to UI, skip LLM
  - If no match → continue to normal Gemini/Ollama flow
- **New skill**: Create `skills/yeni_skill/yeni_skill.py`, implement `route_yeni_skill_request()`, SkillManager auto-discovers it
- **Hot-Reload**: Watcher thread checks `skills/` every 3s for new/changed/deleted skill files and reloads automatically (daemon thread, no restart needed). Callbacks for `loaded`/`reloaded`/`disabled` events.
- **17 skills loaded**: browser, system_health, process_control, file_manager, network, scheduler, services, weather, youtube, vision, calendar, reminders, whatsapp, media, demo, greeting, debugging_jarvis
- **Trigger pattern note**: All Turkish regex patterns MUST include ASCII fallback variants for each special character (ş→s, ç→c, ü→u, ö→o, ğ→g, ı→i) to handle keyboard/STT input differences. Example: `(?:yavaş|yavas)` not just `(?:yavaş)`.
- **Detaylı döküman**: `docs/SKILL_YUKLEME.md`

## Testing

- **Framework**: `unittest` — no pytest, no mocks (use `@patch` only for side-effect tests like URL opening)
- **Runner**: `.venv/bin/python3 -m unittest tests.test_smoke -v`
- **Coverage target**: all 19+ modules, 0 skips
- **2512 tests** (growing): smoke, constants, pure functions, error paths, skill tests. 1 pre-existing failure (Icon/ dir).
- New module = new test class in `tests/test_smoke.py` or new file `tests/test_<module>.py`
- Browser/web-dependent tests use `@patch` to prevent actual URL opens

## Key Config

- `.venv/bin/python3` (3.13.13) — NOT system `python3` (3.12.3, PEP 668)
- Backend: `config->ollama`, model `qwen2.5:1.5b`
- Real Gemini API key in `config/api_keys.json` (gitignored)
- SFX dir: `BASE_DIR/SFX/`
- Audio config: `config/audio.yaml` — sample_rate 48000, VAD fahrettin (energy_threshold 50.0)

## Refactoring Patterns

1. **Extract submodule**: Create `ui/<name>.py`, import in `__init__.py` via `importlib`, update caller
2. **Dict dispatch**: Replace `elif` chains with `TOOL_HANDLERS` registry
3. **Provider abstraction**: Extract backend-specific logic into `core/provider_base.py` abstract interface + provider implementations. Provider receives `jarvis` reference for cross-cutting concerns.
4. **Never suppress types**: No `# type: ignore`, `@ts-ignore` (JS), or `Any` casts

## Security Patterns

1. **`_user_initiated` gate**: AI tools that have side effects (browser, file ops) should check a flag that starts `False` and flips `True` when the user first speaks/types. Blocks AI-initiated calls before user interaction.
2. **OS detection in prompt**: Inject `[SISTEM BILGISI]` section into system prompt at build time so AI knows the actual OS, shell, and path separator — prevents cross-platform command generation.

## Error Handling Patterns

1. **Silent exception logging**: Every `except Exception: pass` must call `traceback.print_exc()` before pass. Two exceptions:
   - NDJSON streaming parsers (main.py Ollama chunk parsing) — partial/incomplete JSON is expected, logging every chunk would flood output
   - Best-effort fallback functions returning defaults (windows_utils, process_manager, youtube_stats) — outer callers handle logging
2. **Cleanup exception logging**: `close()`/`terminate()`/`kill()` cleanup blocks in `finally` must also log via `traceback.print_exc()` to avoid silently hiding resource leaks
3. **Stream parsing**: NDJSON/stream parsers should use `traceback.print_exc()` only on non-trivial failures, not on expected partial chunks

## Input Validation

1. **STT text cap**: `_on_text_command()` rejects text > 10000 chars (guards against memory issues from malformed input)
2. **Tool call arg cap**: `parse_local_tool_call()` rejects any individual arg value > 500 chars (prevents overly long injection-like values)
3. **Tool call total cap**: `parse_local_tool_call()` rejects input > 2000 chars total
4. **Tool name whitelist**: Only pre-registered tool names in `valid_tools` set are accepted — unknown names return `None`

## Turkish STT Processing

1. **NFC normalization**: `unicodedata.normalize("NFC", text)` before any text processing. Prevents decomposed Turkish characters (ç, ş, ğ, ö, ü, ı) from breaking word boundaries and syllable-split detection.
2. **Syllable split fix**: After NFC, run a post-processing pass that merges very short pieces (≤3 chars) with adjacent words, with a total cap (≤8 chars) to prevent over-merging. Exclude common Turkish stop words.

## Checklist Before Shipping

- [ ] `lsp_diagnostics` clean on changed files
- [ ] `.venv/bin/python3 -m unittest discover tests -v` passes (2512 OK, 1 pre-existing failure)
- [ ] `build.sh` or `build.ps1` compiles clean
- [ ] No dead code, no mock/placeholder tests
