from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

try:
    import pyaudio  # noqa: F401
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

try:
    from google import genai  # noqa: F401
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestUIModuleConstants(unittest.TestCase):
    """ui.py modul sabitleri — Tkinter baslatmadan test edilir."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        from pathlib import Path
        _ui_path = Path(__file__).resolve().parent.parent / "ui.py"
        _spec = importlib.util.spec_from_file_location("ui_legacy_test", _ui_path)
        cls.ui_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(cls.ui_mod)

    def test_orb_colors_has_seven_states(self):
        """ORB_COLORS 7 durum icerir."""
        from ui.theme import ORB_COLORS
        self.assertEqual(len(ORB_COLORS), 7)

    def test_orb_colors_all_rgb_tuples(self):
        """ORB_COLORS degerlerinin hepsi 3'lü RGB tup."""
        from ui.theme import ORB_COLORS
        for state, color in ORB_COLORS.items():
            self.assertIsInstance(state, str)
            self.assertIsInstance(color, tuple)
            self.assertEqual(len(color), 3)
            for channel in color:
                self.assertTrue(0 <= channel <= 255)

    def test_state_hex_colors_five_states(self):
        """STATE_HEX_COLORS 5 durum icerir."""
        from ui.theme import STATE_HEX_COLORS
        self.assertEqual(len(STATE_HEX_COLORS), 5)

    def test_state_hex_colors_format(self):
        """STATE_HEX_COLORS degerleri #rrggbb formatinda."""
        from ui.theme import STATE_HEX_COLORS
        for state, color in STATE_HEX_COLORS.items():
            self.assertIsInstance(state, str)
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith("#"))
            self.assertEqual(len(color), 7)

    def test_voices_has_eight_names(self):
        """VOICES 8 ses adi icerir."""
        from ui.theme import VOICES
        self.assertEqual(len(VOICES), 8)
        self.assertIn("Charon", VOICES)

    def test_color_constants_format(self):
        """Renk sabitleri #rrggbb formatinda."""
        from ui.theme import C_BG, C_PRI, C_TEXT, C_GREEN, C_RED, C_BLUE, C_GOLD
        for name, color in [("C_BG", C_BG), ("C_PRI", C_PRI), ("C_TEXT", C_TEXT),
                             ("C_GREEN", C_GREEN), ("C_RED", C_RED),
                             ("C_BLUE", C_BLUE), ("C_GOLD", C_GOLD)]:
            self.assertIsInstance(color, str)
            self.assertTrue(color.startswith("#"), f"{name}={color} # ile baslamali")
            self.assertEqual(len(color), 7)

    def test_dimension_constants_positive(self):
        """Boyut sabitleri pozitif integer."""
        from ui.theme import W_TARGET, H_TARGET, LEFT_W_T, RIGHT_W_T, HDR_H, FOOTER_H, INPUT_H, CONTROL_H
        for name, val in [("W_TARGET", W_TARGET), ("H_TARGET", H_TARGET),
                          ("LEFT_W_T", LEFT_W_T), ("RIGHT_W_T", RIGHT_W_T),
                          ("HDR_H", HDR_H), ("FOOTER_H", FOOTER_H),
                          ("INPUT_H", INPUT_H), ("CONTROL_H", CONTROL_H)]:
            self.assertIsInstance(val, int)
            self.assertGreater(val, 0)

    def test_system_name_constant(self):
        """SYSTEM_NAME dogru deger."""
        self.assertEqual(self.ui_mod.SYSTEM_NAME, "J.A.R.V.I.S")

    def test_model_badge_constant(self):
        """MODEL_BADGE dogru deger."""
        self.assertEqual(self.ui_mod.MODEL_BADGE, "VOICE CORE · Windows")


class TestUIModuleFunctions(unittest.TestCase):
    """ui.py modul seviyesi fonksiyonlar."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        from pathlib import Path
        _ui_path = Path(__file__).resolve().parent.parent / "ui.py"
        _spec = importlib.util.spec_from_file_location("ui_legacy_fn_test", _ui_path)
        cls.ui_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(cls.ui_mod)

    def test_font_body_returns_tuple(self):
        """font_body tuple doner."""
        from ui.theme import font_body
        result = font_body(12)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ("Grift", 12))

    def test_font_body_bold_returns_tuple(self):
        """font_body_bold tuple doner."""
        from ui.theme import font_body_bold
        result = font_body_bold(14)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ("Grift", 14, "bold"))

    def test_font_display_returns_tuple(self):
        """font_display tuple doner."""
        from ui.theme import font_display
        result = font_display(18)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ("Grift Extra Bold", 18))

    def test_resolve_sfx_dir_returns_path(self):
        """_resolve_sfx_dir Path doner."""
        from pathlib import Path
        result = self.ui_mod._resolve_sfx_dir()
        self.assertIsInstance(result, Path)
        self.assertTrue(str(result).endswith("SFX"))


class TestUISoundManager(unittest.TestCase):
    """SoundManager — ses oynatmasiz testler."""

    def setUp(self):
        from ui.sound_manager import SoundManager
        self.sm = SoundManager()

    def test_init_defaults(self):
        """SoundManager varsayilan degerlerle baslar."""
        self.assertTrue(self.sm._enabled)
        self.assertEqual(self.sm._volume, 0.20)

    def test_get_volume_returns_float(self):
        """get_volume float doner."""
        vol = self.sm.get_volume()
        self.assertIsInstance(vol, float)

    def test_set_volume_clamps_low(self):
        """set_volume dusuk degeri 0'a kilitler."""
        self.sm.set_volume(-0.5)
        self.assertEqual(self.sm.get_volume(), 0.0)

    def test_set_volume_clamps_high(self):
        """set_volume yuksek degeri 1'e kilitler."""
        self.sm.set_volume(2.0)
        self.assertEqual(self.sm.get_volume(), 1.0)

    def test_set_volume_normal(self):
        """set_volume normal degeri korur."""
        self.sm.set_volume(0.5)
        self.assertAlmostEqual(self.sm.get_volume(), 0.5)

    def test_toggle_flips_enabled(self):
        """toggle _enabled degerini tersine cevirir."""
        initial = self.sm._enabled
        result = self.sm.toggle()
        self.assertEqual(result, not initial)
        self.assertEqual(self.sm._enabled, not initial)

    def test_toggle_twice_restores(self):
        """toggle iki kez cagrilinca eski haline doner."""
        initial = self.sm._enabled
        self.sm.toggle()
        self.sm.toggle()
        self.assertEqual(self.sm._enabled, initial)

    def test_set_enabled_false(self):
        """set_enabled(False) _enabled'i False yapar."""
        self.sm.set_enabled(False)
        self.assertFalse(self.sm._enabled)

    def test_set_enabled_true(self):
        """set_enabled(True) _enabled'i True yapar."""
        self.sm.set_enabled(False)
        self.sm.set_enabled(True)
        self.assertTrue(self.sm._enabled)

    def test_set_volume_accepts_int(self):
        """set_volume int deger kabul eder."""
        self.sm.set_volume(75)
        self.assertEqual(self.sm.get_volume(), 1.0)  # clamped


class TestUIJarvisUIStaticMethods(unittest.TestCase):
    """JarvisUI static metodlari — Tkinter baslatmadan test."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        from pathlib import Path
        _ui_path = Path(__file__).resolve().parent.parent / "ui.py"
        _spec = importlib.util.spec_from_file_location("ui_legacy_jarvis_test", _ui_path)
        cls.ui_mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(cls.ui_mod)
        cls.cls = cls.ui_mod.JarvisUI

    def test_state_badge_text_initialising(self):
        """_state_badge_text INITIALISING → CONNECTING."""
        self.assertEqual(self.cls._state_badge_text("INITIALISING"), "CONNECTING")

    def test_state_badge_text_error(self):
        """_state_badge_text ERROR → ERROR."""
        self.assertEqual(self.cls._state_badge_text("ERROR"), "ERROR")

    def test_state_badge_text_listening(self):
        """_state_badge_text LISTENING → ONLINE."""
        self.assertEqual(self.cls._state_badge_text("LISTENING"), "ONLINE")

    def test_state_badge_text_speaking(self):
        """_state_badge_text SPEAKING → ONLINE."""
        self.assertEqual(self.cls._state_badge_text("SPEAKING"), "ONLINE")

    def test_state_badge_text_thinking(self):
        """_state_badge_text THINKING → ONLINE."""
        self.assertEqual(self.cls._state_badge_text("THINKING"), "ONLINE")

    def test_state_badge_text_muted(self):
        """_state_badge_text MUTED → ONLINE."""
        self.assertEqual(self.cls._state_badge_text("MUTED"), "ONLINE")

    def test_state_badge_text_paused(self):
        """_state_badge_text PAUSED → ONLINE."""
        self.assertEqual(self.cls._state_badge_text("PAUSED"), "ONLINE")

    def test_ac_returns_hex(self):
        """_ac alpha composite hex renk dondurur."""
        result = self.cls._ac(0, 255, 136, 255)
        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("#"))
        self.assertEqual(len(result), 7)

    def test_ac_zero_alpha(self):
        """_ac alpha=0 siyah doner."""
        result = self.cls._ac(255, 255, 255, 0)
        self.assertEqual(result, "#000000")

    def test_ac_clamps_alpha(self):
        """_ac alpha degerini 0-255 arasina kilitler."""
        result = self.cls._ac(255, 0, 0, 300)
        self.assertEqual(result, "#ff0000")

    def test_split_summary_lines_empty(self):
        """_split_summary_lines bos string icin [] doner."""
        self.assertEqual(self.cls._split_summary_lines(""), [])
        self.assertEqual(self.cls._split_summary_lines(None), [])

    def test_split_summary_lines_normal(self):
        """_split_summary_lines virgulle ayrilmis metni boler."""
        result = self.cls._split_summary_lines("a, b, c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_split_summary_lines_ve_replacement(self):
        """_split_summary_lines ' ve ' yerine ', ' koyar."""
        result = self.cls._split_summary_lines("a ve b")
        self.assertEqual(result, ["a", "b"])

    def test_split_summary_lines_limit(self):
        """_split_summary_lines limit kadar oge doner."""
        result = self.cls._split_summary_lines("a, b, c, d, e, f", limit=3)
        self.assertEqual(len(result), 3)

    def test_split_summary_lines_strips_dot(self):
        """_split_summary_lines bas/sondaki noktayi temizler."""
        result = self.cls._split_summary_lines("a., .b, c.")
        self.assertEqual(result, ["a", "b", "c"])


# =============================================================================
# 23. CORE / TEXT_UTILS — UNIT TESTS
# =============================================================================
