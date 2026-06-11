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


class TestTextUtils(unittest.TestCase):
    """core/text_utils.py pure fonksiyon testleri (provider abstraction)."""

    # ── clean_transcript_text ──────────────────────────────────

    def test_clean_transcript_text_normal(self):
        """clean_transcript_text normal metni oldugu gibi birakir."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("Merhaba dünya")
        self.assertEqual(text, "Merhaba dünya")
        self.assertFalse(had_noise)

    def test_clean_transcript_text_control_brackets(self):
        """clean_transcript_text [tag] ve <ctrl> tokenlarini temizler."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("[Müzik] Merhaba <ctrl123> dünya")
        self.assertNotIn("[Müzik]", text)
        self.assertNotIn("<ctrl123>", text)
        self.assertIn("Merhaba", text)
        self.assertIn("dünya", text)
        self.assertTrue(had_noise)

    def test_clean_transcript_text_control_chars(self):
        """clean_transcript_text kontrol karakterlerini temizler (<32)."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("Merhaba\x00dünya\x01test")
        self.assertNotIn("\x00", text)
        self.assertNotIn("\x01", text)
        self.assertTrue(had_noise)

    def test_clean_transcript_text_empty(self):
        """clean_transcript_text bos string icin ('', False) doner."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("")
        self.assertEqual(text, "")
        self.assertFalse(had_noise)

    def test_clean_transcript_text_none(self):
        """clean_transcript_text None icin ('', False) doner."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text(None)
        self.assertEqual(text, "")
        self.assertFalse(had_noise)

    def test_clean_transcript_text_whitespace(self):
        """clean_transcript_text fazla bosluklari teke indirir."""
        from core.text_utils import clean_transcript_text
        text, had_noise = clean_transcript_text("Merhaba   dünya    test")
        self.assertEqual(text, "Merhaba dünya test")
        self.assertFalse(had_noise)

    def test_clean_transcript_text_nfc(self):
        """clean_transcript_text NFC normalizasyonu yapar."""
        from core.text_utils import clean_transcript_text
        # decomposed (NFD) form of 'ş' = s + combining cedilla
        s_cedilla = "s\u0327"
        text, had_noise = clean_transcript_text(f"Merhaba{s_cedilla}")
        self.assertIn("ş", text)  # should be composed form
        self.assertFalse(had_noise)

    # ── fix_turkish_syllable_split ─────────────────────────────

    def test_fix_syllable_split_single_letter_merge(self):
        """fix_turkish_syllable_split tek harfli parcayi birlestirir."""
        from core.text_utils import fix_turkish_syllable_split
        result = fix_turkish_syllable_split("İ stanbul")
        self.assertEqual(result, "İstanbul")

    def test_fix_syllable_split_multi_short_merge(self):
        """fix_turkish_syllable_split kisa parcalari birlestirir (max 8)."""
        from core.text_utils import fix_turkish_syllable_split
        result = fix_turkish_syllable_split("ya vaş laş")
        self.assertEqual(result, "yavaşlaş")

    def test_fix_syllable_split_preserves_stop_words(self):
        """fix_turkish_syllable_split Türkçe stop kelimeleri ayri tutar."""
        from core.text_utils import fix_turkish_syllable_split
        result = fix_turkish_syllable_split("ve bir için")
        self.assertEqual(result, "ve bir için")

    def test_fix_syllable_split_normal_text(self):
        """fix_turkish_syllable_split normal metni degistirmez."""
        from core.text_utils import fix_turkish_syllable_split
        result = fix_turkish_syllable_split("Merhaba dünya nasılsın")
        self.assertEqual(result, "Merhaba dünya nasılsın")

    def test_fix_syllable_split_empty(self):
        """fix_turkish_syllable_split bos string icin bos doner."""
        from core.text_utils import fix_turkish_syllable_split
        self.assertEqual(fix_turkish_syllable_split(""), "")

    def test_fix_syllable_split_single_word(self):
        """fix_turkish_syllable_split tek kelimeyi degistirmez."""
        from core.text_utils import fix_turkish_syllable_split
        self.assertEqual(fix_turkish_syllable_split("Merhaba"), "Merhaba")


# =============================================================================
# 24. CORE / TOOL_REGISTRY — UNIT TESTS
# =============================================================================
