from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class TestThinkingAloud(unittest.TestCase):
    """core.thinking_aloud pure fonksiyon ve state testleri."""

    def test_module_import(self):
        """core.thinking_aloud import edilebilmeli."""
        from core import thinking_aloud
        self.assertIsNotNone(thinking_aloud)

    def test_load_phrases_default_when_no_file(self):
        """_load_phrases dosya yoksa varsayilanlari dondurur."""
        from core.thinking_aloud import _load_phrases
        fake_path = Path("/tmp/nonexistent_phrases.json")
        phrases = _load_phrases(fake_path)
        self.assertIn("processing", phrases)
        self.assertIn("searching", phrases)
        self.assertIn("thinking", phrases)
        self.assertIn("Bir saniye...", phrases["processing"])

    def test_load_phrases_from_file(self):
        """_load_phrases gecerli JSON dosyasindan yukler."""
        from core.thinking_aloud import _load_phrases
        data = {"processing": ["Test ediliyor..."], "custom": ["Custom phrase"]}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = Path(f.name)
        try:
            phrases = _load_phrases(tmp_path)
            self.assertEqual(phrases["processing"], ["Test ediliyor..."])
            self.assertEqual(phrases["custom"], ["Custom phrase"])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_load_phrases_empty_list_skipped(self):
        """_load_phrases bos listeyi varsayilana eklemez."""
        from core.thinking_aloud import _load_phrases
        data = {"processing": []}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f)
            tmp_path = Path(f.name)
        try:
            phrases = _load_phrases(tmp_path)
            # Empty list should be skipped, defaults kept
            self.assertIn("Bir saniye...", phrases["processing"])
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_thinking_aloud_init_defaults(self):
        """ThinkingAloud varsayilan degerlerle baslatilir."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud()
        self.assertFalse(ta.is_active)
        self.assertEqual(ta._context, "processing")
        self.assertEqual(ta.voice, "piper-fahrettin")
        self.assertEqual(ta.min_interval, 3.0)
        self.assertEqual(ta.max_interval, 8.0)

    def test_thinking_aloud_init_custom(self):
        """ThinkingAloud ozel parametrelerle baslatilir."""
        from core.thinking_aloud import ThinkingAloud
        cb = lambda p: None
        ta = ThinkingAloud(voice="test-voice", min_interval=1.0, max_interval=2.0, on_phrase=cb)
        self.assertEqual(ta.voice, "test-voice")
        self.assertEqual(ta.min_interval, 1.0)
        self.assertEqual(ta.max_interval, 2.0)
        self.assertIs(ta.on_phrase, cb)

    def test_set_context_valid(self):
        """set_context gecerli context ile state gunceller."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud()
        ta.set_context("searching")
        self.assertEqual(ta._context, "searching")

    def test_set_context_invalid_ignored(self):
        """set_context gecersiz context'i ignore eder."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud()
        ta.set_context("invalid_context_xyz")
        self.assertEqual(ta._context, "processing")

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud()
        stats = ta.get_stats()
        self.assertIn("active", stats)
        self.assertIn("context", stats)
        self.assertIn("phrases_loaded", stats)
        self.assertFalse(stats["active"])
        self.assertEqual(stats["context"], "processing")
        self.assertGreater(stats["phrases_loaded"], 0)

    def test_speak_random_calls_on_phrase(self):
        """_speak_random on_phrase callback'ini cagirir."""
        from core.thinking_aloud import ThinkingAloud
        captured = []
        ta = ThinkingAloud(on_phrase=lambda p: captured.append(p))
        ta._speak_random()
        self.assertEqual(len(captured), 1)
        self.assertIn(captured[0], ta.phrases["processing"])

    def test_start_without_callback_starts_thread(self):
        """start thread baslatir ve active=True yapar."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud(on_phrase=lambda p: None)
        ta.start("processing")
        self.assertTrue(ta.is_active)
        self.assertIsNotNone(ta._thread)
        self.assertTrue(ta._thread.is_alive())
        ta.stop()

    def test_start_does_not_duplicate_thread(self):
        """start cagrisi zaten aktifse ikinci thread baslatmaz."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud(on_phrase=lambda p: None)
        ta.start()
        thread_id = id(ta._thread)
        ta.start()
        self.assertEqual(id(ta._thread), thread_id)
        ta.stop()

    def test_stop_cleans_up(self):
        """stop thread'i durdurur ve active=False yapar."""
        from core.thinking_aloud import ThinkingAloud
        ta = ThinkingAloud(on_phrase=lambda p: None)
        ta.start()
        self.assertTrue(ta.is_active)
        ta.stop()
        self.assertFalse(ta.is_active)
        self.assertIsNone(ta._thread)

    def test_factory_creates_thinking_aloud(self):
        """create_thinking_aloud ThinkingAloud instance'i dondurur."""
        from core.thinking_aloud import create_thinking_aloud, ThinkingAloud
        ta = create_thinking_aloud()
        self.assertIsInstance(ta, ThinkingAloud)
        self.assertEqual(ta.voice, "piper-fahrettin")

    def test_factory_with_callback(self):
        """create_thinking_aloud on_phrase parametresini iletir."""
        from core.thinking_aloud import create_thinking_aloud
        cb = lambda p: None
        ta = create_thinking_aloud(voice="custom", on_phrase=cb)
        self.assertIs(ta.on_phrase, cb)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from core.thinking_aloud import __all__
        self.assertIn("ThinkingAloud", __all__)
        self.assertIn("create_thinking_aloud", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
