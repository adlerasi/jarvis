from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestVoiceManager(unittest.TestCase):
    """core.voice_manager pure fonksiyon ve state testleri."""

    def test_module_import(self):
        """core.voice_manager import edilebilmeli."""
        from core import voice_manager
        self.assertIsNotNone(voice_manager)

    def test_load_voices_config_defaults_when_no_file(self):
        """_load_voices_config dosya yoksa varsayilanlari dondurur."""
        from core.voice_manager import _load_voices_config
        config = _load_voices_config(Path("/tmp/nonexistent_voices.yaml"))
        self.assertEqual(config["default_voice"], "fahrettin")
        self.assertEqual(config["default_emotion"], "neutral")
        self.assertTrue(config["auto_voice_selection"])
        self.assertEqual(config["voices"], {})
        self.assertEqual(config["context_voice_mapping"], {})

    def test_load_voices_config_from_yaml(self):
        """_load_voices_config gecerli YAML dosyasindan yukler."""
        from core.voice_manager import _load_voices_config
        yaml_content = """
default_voice: test-voice
default_emotion: happy
voices:
  test-voice:
    id: test-tts
    engine: test
    gender: unspecified
context_voice_mapping:
  greeting: test-voice
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            config = _load_voices_config(tmp_path)
            self.assertEqual(config["default_voice"], "test-voice")
            self.assertEqual(config["default_emotion"], "happy")
            self.assertIn("test-voice", config["voices"])
            self.assertIn("greeting", config["context_voice_mapping"])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_voice_manager_init_defaults(self):
        """VoiceManager varsayilan config ile baslatilir."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        self.assertEqual(vm._current_voice_id, "fahrettin")
        self.assertEqual(vm._current_emotion, "neutral")
        self.assertTrue(vm._auto_select)
        self.assertEqual(vm._voices, {})

    def test_set_voice_unknown(self):
        """set_voice bilinmeyen ses icin False doner."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        result = vm.set_voice("nonexistent")
        self.assertFalse(result)
        self.assertEqual(vm._current_voice_id, "fahrettin")

    def test_get_voice_with_voices_config(self):
        """get_voice context mapping ile ses ID'si doner."""
        from core.voice_manager import VoiceManager
        yaml_content = """
voices:
  test-voice:
    id: test-tts-id
    engine: test
context_voice_mapping:
  greeting: test-voice
default_voice: test-voice
auto_voice_selection: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            vm = VoiceManager(config_path=tmp_path)
            voice_id = vm.get_voice("greeting")
            self.assertEqual(voice_id, "test-tts-id")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_get_voice_fallback(self):
        """get_voice context eslesmezse fallback ses doner."""
        from core.voice_manager import VoiceManager
        yaml_content = """
voices:
  main-voice:
    id: main-tts
    engine: test
default_voice: main-voice
auto_voice_selection: true
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            vm = VoiceManager(config_path=tmp_path)
            voice_id = vm.get_voice("unknown_context")
            self.assertEqual(voice_id, "main-tts")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_get_voice_no_auto_select(self):
        """get_voice auto_select=False iken context mapping kullanilmaz."""
        from core.voice_manager import VoiceManager
        yaml_content = """
voices:
  main-voice:
    id: main-tts
    engine: test
default_voice: main-voice
auto_voice_selection: false
context_voice_mapping:
  greeting: main-voice
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            vm = VoiceManager(config_path=tmp_path)
            # auto_select=false, mapping ignored, but fallback still works
            voice_id = vm.get_voice("greeting")
            self.assertEqual(voice_id, "main-tts")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_set_emotion(self):
        """set_emotion emotion state gunceller."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        vm.set_emotion("happy")
        self.assertEqual(vm._current_emotion, "happy")

    def test_get_emotion(self):
        """get_emotion current emotion doner."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        self.assertEqual(vm.get_emotion(), "neutral")
        vm.set_emotion("sad")
        self.assertEqual(vm.get_emotion(), "sad")

    def test_list_voices_empty(self):
        """list_voices bos liste doner (config yoksa)."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        self.assertEqual(vm.list_voices(), [])

    def test_list_voices_with_data(self):
        """list_voices ses listesini dondurur."""
        from core.voice_manager import VoiceManager
        yaml_content = """
voices:
  voice1:
    id: voice1-tts
    engine: test
    gender: female
    description: Test voice 1
  voice2:
    id: voice2-tts
    engine: test
    gender: male
    description: Test voice 2
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            vm = VoiceManager(config_path=tmp_path)
            voices = vm.list_voices()
            self.assertEqual(len(voices), 2)
            names = [v["name"] for v in voices]
            self.assertIn("voice1", names)
            self.assertIn("voice2", names)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_get_current_voice_info_none(self):
        """get_current_voice_info ses yoksa None doner."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        info = vm.get_current_voice_info()
        self.assertIsNone(info)

    def test_get_current_voice_info_with_data(self):
        """get_current_voice_info ses bilgisini dondurur."""
        from core.voice_manager import VoiceManager
        yaml_content = """
voices:
  main-voice:
    id: main-tts
    engine: test
    gender: female
    description: Main voice
default_voice: main-voice
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as f:
            f.write(yaml_content)
            tmp_path = Path(f.name)
        try:
            vm = VoiceManager(config_path=tmp_path)
            info = vm.get_current_voice_info()
            self.assertEqual(info["name"], "main-voice")
            self.assertEqual(info["id"], "main-tts")
            self.assertEqual(info["engine"], "test")
            self.assertEqual(info["emotion"], "neutral")
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from core.voice_manager import VoiceManager
        vm = VoiceManager(config_path=Path("/tmp/nonexistent.yaml"))
        stats = vm.get_stats()
        self.assertIn("current_voice", stats)
        self.assertIn("current_emotion", stats)
        self.assertIn("auto_select", stats)
        self.assertIn("available_voices", stats)
        self.assertEqual(stats["current_voice"], "fahrettin")
        self.assertEqual(stats["current_emotion"], "neutral")
        self.assertEqual(stats["available_voices"], 0)

    def test_factory_creates_voice_manager(self):
        """create_voice_manager VoiceManager instance'i dondurur."""
        from core.voice_manager import create_voice_manager, VoiceManager
        vm = create_voice_manager(config_path=Path("/tmp/nonexistent.yaml"))
        self.assertIsInstance(vm, VoiceManager)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from core.voice_manager import __all__
        self.assertIn("VoiceManager", __all__)
        self.assertIn("create_voice_manager", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
