from __future__ import annotations

import sys, unittest
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from audio.thinking_sounds import ThinkingSounds


class TestThinkingSounds(unittest.TestCase):
    def setUp(self):
        self.ts = ThinkingSounds()

    def test_select_returns_string(self):
        result = self.ts.select(delay_ms=1000)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_select_short_delay_returns_short_sounds(self):
        result = self.ts.select(delay_ms=500)
        self.assertLess(len(result), 15)

    def test_select_long_delay_excited_category(self):
        result = self.ts.select(delay_ms=5000, category="excited")
        self.assertIsInstance(result, str)

    def test_select_nonexistent_category_falls_to_neutral(self):
        result = self.ts.select(delay_ms=2000, category="nonexistent")
        self.assertIn(result, self.ts._sounds["neutral"])

    def test_random_returns_string(self):
        result = self.ts.random()
        self.assertIsInstance(result, str)

    def test_random_specific_category(self):
        result = self.ts.random("processing")
        self.assertIn(result, self.ts._sounds["processing"])

    def test_random_empty_category_returns_empty_string(self):
        ts = ThinkingSounds(sounds={"empty": [], "neutral": ["x"]})
        result = ts.random("empty")
        self.assertEqual(result, "")

    def test_categories(self):
        cats = self.ts.categories
        self.assertIn("neutral", cats)
        self.assertIn("processing", cats)
        self.assertIn("thinking", cats)

    def test_count(self):
        total = self.ts.count()
        # Count all sounds in default dict
        expected = sum(len(v) for v in self.ts._sounds.values())
        self.assertEqual(total, expected)

    def test_select_empty_category_returns_empty(self):
        ts = ThinkingSounds(sounds={"neutral": []})
        result = ts.select(delay_ms=1000)
        self.assertEqual(result, "")

    def test_custom_sounds(self):
        custom = {"greeting": ["Merhaba"], "neutral": ["x"]}
        ts = ThinkingSounds(sounds=custom)
        self.assertEqual(ts.random("greeting"), "Merhaba")
        self.assertIn("greeting", ts.categories)
        self.assertIn("neutral", ts.categories)


    # ── TTS Integration ────────────────────────────────────

    def test_speak_no_callback_returns_false(self):
        result = self.ts.speak("test")
        self.assertFalse(result)

    def test_speak_with_callback(self):
        calls = []
        ts = ThinkingSounds(tts_callback=lambda t: calls.append(t))
        import time
        result = ts.speak("Merhaba")
        self.assertTrue(result)
        time.sleep(0.15)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], "Merhaba")

    def test_speak_empty_text_returns_false(self):
        calls = []
        ts = ThinkingSounds(tts_callback=lambda t: calls.append(t))
        result = ts.speak("")
        self.assertFalse(result)
        self.assertEqual(len(calls), 0)

    def test_play_delayed_selects_and_plays(self):
        calls = []
        ts = ThinkingSounds(tts_callback=lambda t: calls.append(t))
        import time
        text = ts.play_delayed(2000, "thinking")
        self.assertIn(text, ts._sounds["thinking"])
        time.sleep(0.15)
        self.assertEqual(calls[0], text)

    def test_is_speaking(self):
        ts = ThinkingSounds()
        self.assertFalse(ts.is_speaking)

    def test_speak_returns_true_with_callback(self):
        calls = []
        ts = ThinkingSounds(tts_callback=lambda t: calls.append(t))
        result = ts.speak("test")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
