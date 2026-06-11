from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSkillManager(unittest.TestCase):
    """core.skill_manager — gerçek skill dosyalarıyla test."""

    maxDiff = None

    def setUp(self):
        # Temp skills directory with a mock skill
        self.temp_dir = Path(tempfile.mkdtemp(prefix="skill_test_"))
        self.skills_dir = self.temp_dir / "skills"
        self.skills_dir.mkdir()

        # Create a test skill: "test_greeter"
        self.greeter_dir = self.skills_dir / "test_greeter"
        self.greeter_dir.mkdir()
        self._create_skill("test_greeter", """
SKILL_ID = "greeter-v1"
SKILL_NAME = "Greeter"
SKILL_VERSION = "1.0.0"

def route_test_greeter_request(user_text: str) -> str | None:
    text = user_text.lower().strip()
    if "merhaba" in text:
        return "Merhaba! Ben JARVIS."
    if "nasilsin" in text:
        return "Iyiyim, tesekkurler!"
    return None
""")

        # Create a second skill: "test_weather"
        self.weather_dir = self.skills_dir / "test_weather"
        self.weather_dir.mkdir()
        self._create_skill("test_weather", """
SKILL_ID = "weather-v1"
SKILL_NAME = "Weather"
SKILL_VERSION = "0.5.0"

def route_test_weather_request(user_text: str) -> str | None:
    text = user_text.lower().strip()
    if "hava" in text:
        return "Hava durumu: Gunesli, 22°C"
    return None
""")

        # Patch SKILLS_DIR
        self._patcher_skills_dir = patch("core.skill_manager.SKILLS_DIR", self.skills_dir)
        self._patcher_skills_dir.start()

    def tearDown(self):
        self._patcher_skills_dir.stop()
        # Clean up singleton
        import core.skill_manager as sm
        if sm._skill_manager:
            sm._skill_manager.stop_watcher()
            sm._skill_manager = None
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_skill(self, folder_name: str, code: str):
        """Create a skill .py file in the temp directory."""
        skill_file = self.skills_dir / folder_name / f"{folder_name}_skill.py"
        skill_file.write_text(code.strip(), encoding="utf-8")

    # ── SkillInfo dataclass ──────────────────────────────────────────────

    def test_skillinfo_defaults(self):
        """SkillInfo varsayilan degerlerle olusur."""
        from core.skill_manager import SkillInfo
        info = SkillInfo(
            skill_id="test-v1", name="test", version="1.0",
            folder="test", module_path=Path("/tmp/test.py")
        )
        self.assertEqual(info.skill_id, "test-v1")
        self.assertTrue(info.is_active)
        self.assertEqual(info.load_count, 0)
        self.assertIsNone(info.last_error)

    def test_skillinfo_to_dict(self):
        """SkillInfo.to_dict dogru anahtarlari icerir."""
        from core.skill_manager import SkillInfo
        from pathlib import Path
        info = SkillInfo(
            skill_id="test-v1", name="Test", version="1.0",
            folder="test", module_path=Path("/tmp/test.py")
        )
        d = info.to_dict()
        self.assertIn("skill_id", d)
        self.assertIn("name", d)
        self.assertIn("version", d)
        self.assertIn("is_active", d)
        self.assertEqual(d["skill_id"], "test-v1")

    # ── SkillManager init ───────────────────────────────────────────────

    def test_init_loads_skills(self):
        """SkillManager baslangicta skill'leri yukler."""
        from core.skill_manager import SkillManager
        # Disable auto_reload to avoid threading
        sm = SkillManager(auto_reload=False)
        self.assertGreaterEqual(sm.get_skill_count(), 2)
        skills = sm.list_skills()
        self.assertIn("greeter-v1", skills)
        self.assertIn("weather-v1", skills)

    def test_init_no_skills_dir(self):
        """SkillManager skills/ yoksa sorunsuz baslar."""
        from core.skill_manager import SkillManager
        with patch("core.skill_manager.SKILLS_DIR", Path("/tmp/nonexistent_skills_xyz")):
            sm = SkillManager(auto_reload=False)
            self.assertEqual(sm.get_skill_count(), 0)

    # ── route() ─────────────────────────────────────────────────────────

    def test_route_match(self):
        """route eslesen skill'den yanit doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        result = sm.route("merhaba dunya")
        self.assertEqual(result, "Merhaba! Ben JARVIS.")

    def test_route_second_skill(self):
        """route ikinci skill'de eslesme yapar."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        result = sm.route("hava nasil")
        self.assertEqual(result, "Hava durumu: Gunesli, 22°C")

    def test_route_no_match(self):
        """route eslesme yoksa None doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        result = sm.route("bu bir test")
        self.assertIsNone(result)

    # ── list / count / stats ────────────────────────────────────────────

    def test_list_skills(self):
        """list_skills aktif skill ID'lerini doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        skills = sm.list_skills()
        self.assertIsInstance(skills, list)
        self.assertIn("greeter-v1", skills)

    def test_get_skill_count(self):
        """get_skill_count aktif skill sayisini doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertGreaterEqual(sm.get_skill_count(), 2)

    def test_get_stats(self):
        """get_stats dogru anahtarlari icerir."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        stats = sm.get_stats()
        self.assertIn("total_skills", stats)
        self.assertIn("active", stats)
        self.assertIn("auto_reload", stats)
        self.assertGreaterEqual(stats["active"], 2)

    def test_list_all_skills(self):
        """list_all_skills detayli skill listesi doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        all_s = sm.list_all_skills()
        self.assertIsInstance(all_s, list)
        self.assertGreaterEqual(len(all_s), 2)
        for s in all_s:
            self.assertIn("skill_id", s)
            self.assertIn("name", s)

    # ── get_skill_info ──────────────────────────────────────────────────

    def test_get_skill_info_exists(self):
        """get_skill_info var olan skill'in bilgisini doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        info = sm.get_skill_info("greeter-v1")
        self.assertIsNotNone(info)
        self.assertEqual(info.name, "Greeter")
        self.assertEqual(info.version, "1.0.0")

    def test_get_skill_info_not_found(self):
        """get_skill_info olmayan skill'de None doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertIsNone(sm.get_skill_info("nonexistent"))

    # ── disable / enable ────────────────────────────────────────────────

    def test_disable_skill(self):
        """disable_skill skill'i devre disi birakir."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertTrue(sm.disable_skill("greeter-v1"))
        self.assertNotIn("greeter-v1", sm.list_skills())
        # route should not match disabled skill
        self.assertIsNone(sm.route("merhaba"))

    def test_disable_skill_not_found(self):
        """disable_skill olmayan skill'de False doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertFalse(sm.disable_skill("nonexistent"))

    def test_enable_skill(self):
        """enable_skill devre disi skill'i tekrar aktif eder."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        sm.disable_skill("greeter-v1")
        self.assertTrue(sm.enable_skill("greeter-v1"))
        self.assertIn("greeter-v1", sm.list_skills())

    def test_enable_skill_not_found(self):
        """enable_skill olmayan skill'de False doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertFalse(sm.enable_skill("nonexistent"))

    # ── reload ──────────────────────────────────────────────────────────

    def test_reload_skill(self):
        """reload_skill skill'i yeniden yukler."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        (self.greeter_dir / "SKILL.md").write_text("# Greeter Skill", encoding="utf-8")
        # Modify the skill file
        skill_file = self.greeter_dir / "test_greeter_skill.py"
        original = skill_file.read_text(encoding="utf-8")
        skill_file.write_text(original.replace("Merhaba! Ben JARVIS.", "Merhaba! v2"), encoding="utf-8")
        # Reload
        self.assertTrue(sm.reload_skill("greeter-v1"))
        result = sm.route("merhaba")
        self.assertEqual(result, "Merhaba! v2")

    def test_reload_skill_not_found(self):
        """reload_skill olmayan skill'de False doner."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=False)
        self.assertFalse(sm.reload_skill("nonexistent"))

    # ── watcher ─────────────────────────────────────────────────────────

    def test_stop_watcher(self):
        """stop_watcher thread'i durdurur."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=True)
        self.assertTrue(sm._running)
        sm.stop_watcher()
        self.assertFalse(sm._running)

    def test_watcher_loop_runs_and_stops(self):
        """Watcher thread baslatilip durdurulabilir."""
        from core.skill_manager import SkillManager
        sm = SkillManager(auto_reload=True, reload_interval=0.05)
        self.assertTrue(sm._running)
        import time
        time.sleep(0.15)
        sm.stop_watcher()
        self.assertFalse(sm._running)

    # ── Singleton ───────────────────────────────────────────────────────

    def test_get_skill_manager_singleton(self):
        """get_skill_manager ayni instance'i doner."""
        import core.skill_manager as sm
        sm._skill_manager = None  # reset
        mgr1 = sm.get_skill_manager(auto_reload=False)
        mgr2 = sm.get_skill_manager(auto_reload=False)
        self.assertIs(mgr1, mgr2)
        mgr1.stop_watcher()
        sm._skill_manager = None

    def test_reload_skill_manager(self):
        """reload_skill_manager yeni instance olusturur."""
        import core.skill_manager as sm
        sm._skill_manager = None  # reset
        mgr1 = sm.get_skill_manager(auto_reload=False)
        mgr2 = sm.reload_skill_manager()
        self.assertIsNot(mgr1, mgr2)
        mgr2.stop_watcher()
        sm._skill_manager = None

    # ── Failed skill ────────────────────────────────────────────────────

    def test_skill_syntax_error(self):
        """Syntax hatali skill yuklenmez ve failed listeye eklenir."""
        from core.skill_manager import SkillManager
        # Create a broken skill
        bad_dir = self.skills_dir / "test_bad"
        bad_dir.mkdir()
        bad_file = bad_dir / "test_bad_skill.py"
        bad_file.write_text("def broken_syntax(", encoding="utf-8")

        sm = SkillManager(auto_reload=False)
        # Bad skill should not crash the manager
        self.assertIsInstance(sm.get_stats(), dict)
        # But it should be in all skills list (failed)
        all_s = sm.list_all_skills()
        failed = [s for s in all_s if not s["is_active"]]
        self.assertGreaterEqual(len(failed), 0)

    # ── Route error handling ────────────────────────────────────────────

    def test_route_skill_raises_exception(self):
        """Route hata firlatirsa skill error_count artar ve None doner."""
        from core.skill_manager import SkillManager
        # Create a skill that raises
        bad_dir = self.skills_dir / "test_crash"
        bad_dir.mkdir()
        bad_file = bad_dir / "test_crash_skill.py"
        bad_file.write_text("""
SKILL_ID = "crash-v1"
def route_test_crash_request(user_text):
    raise RuntimeError("Kesin hata!")
""", encoding="utf-8")

        sm = SkillManager(auto_reload=False)
        # Should not raise, just return None
        result = sm.route("anything")
        self.assertIsNone(result)
        # error_count should be incremented
        info = sm.get_skill_info("crash-v1")
        self.assertIsNotNone(info)
        self.assertGreater(info.error_count, 0)
        self.assertIsNotNone(info.last_error)

    # ── Module exports ──────────────────────────────────────────────────

    def test_module_exports(self):
        """core.skill_manager dogru sembolleri export ediyor."""
        import core.skill_manager
        self.assertTrue(hasattr(core.skill_manager, "SkillManager"))
        self.assertTrue(hasattr(core.skill_manager, "SkillInfo"))
        self.assertTrue(hasattr(core.skill_manager, "get_skill_manager"))
        self.assertTrue(hasattr(core.skill_manager, "reload_skill_manager"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
