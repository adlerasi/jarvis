"""
Contract tests for Skill Engine library.

These tests define the interaction boundary between skill-engine and its
consumers (JARVIS app layer, CLI users, skill authors).  They MUST pass
with any compliant implementation.

Realistic environment: uses temporary directories and real filesystem
operations (no mocks for the filesystem layer).
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from typing import Any


# ── Helpers ────────────────────────────────────────────────────────────

def _create_skill(dir_path: Path, folder_name: str, code: str) -> Path:
    """Write a skill .py file into a temporary directory."""
    skill_dir = dir_path / folder_name
    skill_dir.mkdir(exist_ok=True)
    skill_file = skill_dir / f"{folder_name}_skill.py"
    skill_file.write_text(code.strip(), encoding="utf-8")
    return skill_file


SAMPLE_SKILL_CODE = """
SKILL_ID = "{name}-v1"
SKILL_NAME = "{name}"
SKILL_VERSION = "1.0.0"

def route_{name}_request(user_text: str) -> str | None:
    text = user_text.lower().strip()
    if "merhaba" in text:
        return "Merhaba!"
    return None
"""


# ── Contract: Skill Module Interface ──────────────────────────────────

class SkillModuleContract(unittest.TestCase):
    """A skill module MUST expose a route function with the correct signature.

    The library MUST validate this contract on load and reject malformed
    skills with a SkillLoadError (or subclass thereof).
    """

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="skill_ctr_"))
        self._skills_dir = self._tmp / "skills"
        self._skills_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_engine(self):
        """Instantiate the library's SkillEngine with a controlled directory."""
        from skill_engine import SkillEngine
        return SkillEngine(skills_dir=str(self._skills_dir), auto_reload=False)

    # ── Positive contract ─────────────────────────────────────────

    def test_valid_skill_loads_and_routes(self):
        """A skill with route_{name}_request loads and returns results."""
        _create_skill(self._skills_dir, "test_greeter",
                      SAMPLE_SKILL_CODE.format(name="test_greeter"))
        engine = self._make_engine()
        result = engine.route("merhaba")
        self.assertEqual(result, "Merhaba!")

    def test_skill_with_lifecycle_hooks(self):
        """A skill that defines on_load/on_unload/on_error does NOT break loading."""
        code = """
SKILL_ID = "hooktest-v1"
SKILL_NAME = "HookTest"
SKILL_VERSION = "1.0.0"

def route_hooktest_request(user_text: str) -> str | None:
    return "ok"

def on_load(skill_id: str):
    pass

def on_unload(skill_id: str):
    pass

def on_error(skill_id: str, exc: Exception):
    pass
"""
        _create_skill(self._skills_dir, "hooktest", code)
        engine = self._make_engine()
        result = engine.route("anything")
        self.assertEqual(result, "ok")

    def test_skill_without_route_returns_none(self):
        """A skill with no matching route returns None (no match)."""
        _create_skill(self._skills_dir, "test_greeter",
                      SAMPLE_SKILL_CODE.format(name="test_greeter"))
        engine = self._make_engine()
        result = engine.route("bu bir test")
        self.assertIsNone(result)

    # ── Negative contract ────────────────────────────────────────

    def test_skill_missing_route_function_is_rejected(self):
        """Skill without route function appears as failed in stats."""
        code = """
SKILL_ID = "bad-v1"
SKILL_NAME = "Bad"
SKILL_VERSION = "0.0.1"
# No route function at all
"""
        _create_skill(self._skills_dir, "bad", code)
        engine = self._make_engine()
        stats = engine.get_stats()
        self.assertGreater(stats["failed"], 0)

    def test_skill_syntax_error_is_rejected(self):
        """Skill with Python syntax error appears as failed in stats."""
        _create_skill(self._skills_dir, "broken", """
SKILL_ID = "broken-v1"
this is not valid python
""")
        engine = self._make_engine()
        stats = engine.get_stats()
        self.assertGreater(stats["failed"], 0)

    def test_route_wrong_signature_is_rejected(self):
        """Route function with wrong signature appears as failed in stats."""
        code = """
SKILL_ID = "bad-v1"
SKILL_NAME = "Bad"
def route_bad_request(a, b, c):
    return str(a)
"""
        _create_skill(self._skills_dir, "bad", code)
        engine = self._make_engine()
        stats = engine.get_stats()
        self.assertGreater(stats["failed"], 0)


# ── Contract: SkillEngine Public API ──────────────────────────────────

class SkillEngineAPIContract(unittest.TestCase):
    """SkillEngine MUST expose the documented public methods."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="skill_ctr_"))
        self._skills_dir = self._tmp / "skills"
        self._skills_dir.mkdir()
        _create_skill(self._skills_dir, "test_greeter",
                      SAMPLE_SKILL_CODE.format(name="test_greeter"))
        _create_skill(self._skills_dir, "test_weather", """
SKILL_ID = "weather-v1"
SKILL_NAME = "Weather"
SKILL_VERSION = "0.5.0"
def route_test_weather_request(user_text: str) -> str | None:
    if "hava" in user_text.lower():
        return "Gunesli, 22°C"
    return None
""")

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_engine(self, **kw):
        from skill_engine import SkillEngine
        return SkillEngine(skills_dir=str(self._skills_dir), auto_reload=False, **kw)

    def test_list_skills_returns_all_loaded(self):
        """list_skills() returns IDs of all successfully loaded skills."""
        engine = self._make_engine()
        skills = engine.list_skills()
        self.assertIsInstance(skills, list)
        self.assertIn("test_greeter-v1", skills)
        self.assertIn("weather-v1", skills)

    def test_get_skill_info_returns_metadata(self):
        """get_skill_info(id) returns SkillInfo with expected fields."""
        engine = self._make_engine()
        info = engine.get_skill_info("test_greeter-v1")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "test_greeter")
        self.assertEqual(info.version, "1.0.0")

    def test_get_skill_info_unknown_returns_none(self):
        """get_skill_info() for non-existent skill returns None."""
        engine = self._make_engine()
        self.assertIsNone(engine.get_skill_info("nobody"))

    def test_get_stats_returns_summary(self):
        """get_stats() returns dict with expected keys."""
        engine = self._make_engine()
        stats = engine.get_stats()
        for key in ("total", "active", "failed", "errors"):
            self.assertIn(key, stats)

    def test_disable_and_enable_skill(self):
        """disable_skill() removes from routing; enable_skill() restores."""
        engine = self._make_engine()
        self.assertIn("test_greeter-v1", engine.list_skills())
        engine.disable_skill("test_greeter-v1")
        self.assertNotIn("test_greeter-v1", engine.list_skills())
        engine.enable_skill("test_greeter-v1")
        self.assertIn("test_greeter-v1", engine.list_skills())

    def test_reload_skill_preserves_functionality(self):
        """reload_skill() reloads and route still works after."""
        engine = self._make_engine()
        before = engine.route("merhaba")
        engine.reload_skill("test_greeter-v1")
        after = engine.route("merhaba")
        self.assertEqual(before, after)

    def test_reload_all_preserves_all(self):
        """reload_all() reloads every skill without errors."""
        engine = self._make_engine()
        engine.reload_all()
        self.assertIn("test_greeter-v1", engine.list_skills())
        self.assertIn("weather-v1", engine.list_skills())

    def test_route_returns_first_match(self):
        """route() returns the first matching skill's result."""
        engine = self._make_engine()
        result = engine.route("merhaba")
        self.assertEqual(result, "Merhaba!")
        result = engine.route("hava durumu")
        self.assertEqual(result, "Gunesli, 22°C")


# ── Contract: Hot-Reload Watcher ──────────────────────────────────────

class WatcherContract(unittest.TestCase):
    """The watcher MUST detect filesystem changes within a bounded time."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="skill_ctr_"))
        self._skills_dir = self._tmp / "skills"
        self._skills_dir.mkdir()
        # Pre-load one skill so we have a baseline
        _create_skill(self._skills_dir, "existing",
                      SAMPLE_SKILL_CODE.format(name="existing"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)
        from skill_engine import SkillEngine
        SkillEngine._reset_instance()

    def test_watcher_detects_new_skill(self):
        """Adding a new skill file triggers auto-load within interval*2."""
        from skill_engine import SkillEngine
        engine = SkillEngine(skills_dir=str(self._skills_dir),
                             auto_reload=True, reload_interval=0.5)
        before = set(engine.list_skills())
        _create_skill(self._skills_dir, "newbie",
                      SAMPLE_SKILL_CODE.format(name="newbie"))
        time.sleep(1.5)  # Wait for watcher to pick it up
        after = set(engine.list_skills())
        self.assertGreater(len(after), len(before))

    def test_watcher_detects_skill_deletion(self):
        """Removing a skill directory triggers disable."""
        from skill_engine import SkillEngine
        engine = SkillEngine(skills_dir=str(self._skills_dir),
                             auto_reload=True, reload_interval=0.5)
        # Add a skill first
        _create_skill(self._skills_dir, "ephemeral",
                      SAMPLE_SKILL_CODE.format(name="ephemeral"))
        time.sleep(1.5)
        self.assertIn("ephemeral-v1", engine.list_skills())
        # Remove it
        import shutil
        shutil.rmtree(self._skills_dir / "ephemeral")
        time.sleep(1.5)
        self.assertNotIn("ephemeral-v1", engine.list_skills())


# ── Contract: CLI Interface ──────────────────────────────────────────

class CLIContract(unittest.TestCase):
    """The CLI MUST conform to Principle VI: stdin/stdout, JSON support."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="skill_ctr_"))
        self._skills_dir = self._tmp / "skills"
        self._skills_dir.mkdir()
        _create_skill(self._skills_dir, "test_greeter",
                      SAMPLE_SKILL_CODE.format(name="test_greeter"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _cli(self, *args: str) -> subprocess.CompletedProcess:
        """Run the skill-engine CLI with given args."""
        env = {  # Point the CLI to our temp skills dir
            "SKILL_ENGINE_SKILLS_DIR": str(self._skills_dir),
        }
        return subprocess.run(
            [sys.executable, "-m", "skill_engine", *args],
            capture_output=True, text=True, timeout=10,
            env={**env, **{k: v for k, v in env.items()}},
        )

    def test_cli_list_returns_text(self):
        """`skill-engine list` writes human-readable text to stdout."""
        result = self._cli("list")
        self.assertEqual(result.returncode, 0)
        self.assertIn("test_greeter-v1", result.stdout)

    def test_cli_list_json_is_valid(self):
        """`skill-engine list --json` writes valid JSON to stdout."""
        result = self._cli("list", "--json")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_cli_info_returns_details(self):
        """`skill-engine info <id>` shows metadata for a skill."""
        result = self._cli("info", "test_greeter-v1")
        self.assertEqual(result.returncode, 0)

    def test_cli_info_unknown_returns_error(self):
        """`skill-engine info <unknown>` exits non-zero with error."""
        result = self._cli("info", "does-not-exist")
        self.assertNotEqual(result.returncode, 0)

    def test_cli_reload_returns_success(self):
        """`skill-engine reload` reloads all skills and exits 0."""
        result = self._cli("reload")
        self.assertEqual(result.returncode, 0)
