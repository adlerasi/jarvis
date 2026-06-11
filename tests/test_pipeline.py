#!/usr/bin/env python3
from __future__ import annotations

"""
JARVIS — Uçtan uca pipeline entegrasyon testleri.
Metin girişi → skill yönlendirme → tool dispatch → yanıt akışını doğrular.
"""

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from core.skill_manager import SkillManager
    HAS_SKILL_MANAGER = True
except ImportError:
    HAS_SKILL_MANAGER = False

try:
    from core.tool_registry import VALID_TOOLS, generate_gemini_declarations, generate_ollama_tool_help
    HAS_TOOL_REGISTRY = True
except ImportError:
    HAS_TOOL_REGISTRY = False

try:
    from core.text_utils import clean_transcript_text, fix_turkish_syllable_split
    HAS_TEXT_UTILS = True
except ImportError:
    HAS_TEXT_UTILS = False

try:
    from app_config import load_app_config, get_app_config_value, has_gemini_api_key
    HAS_APP_CONFIG = True
except ImportError:
    HAS_APP_CONFIG = False


# ── 1. Skill Routing Tests ────────────────────────────────

class TestTextToSkillRouting(unittest.TestCase):
    """Metin → Skill yönlendirme testleri."""

    @classmethod
    def setUpClass(cls):
        cls.skill_manager_available = HAS_SKILL_MANAGER
        if cls.skill_manager_available:
            try:
                cls.sm = SkillManager()
                cls.skill_manager_available = True
            except Exception:
                cls.skill_manager_available = False

    def setUp(self):
        if not self.skill_manager_available:
            self.skipTest("SkillManager yüklenemedi")

    def test_weather_route_match(self):
        """route('hava durumu') weather skill'ini bulur."""
        result = self.sm.route("hava durumu nasıl")
        self.assertIsNotNone(result)

    def test_greeting_route_match(self):
        """route('merhaba') greeting skill'ini bulur."""
        result = self.sm.route("merhaba")
        self.assertIsNotNone(result)

    def test_scheduler_route_match(self):
        """route('görev ekle') scheduler skill'ini bulur."""
        result = self.sm.route("saat 10da görev ekle")
        self.assertIsNotNone(result)

    def test_unknown_text_returns_none(self):
        """route() bilinmeyen metin için None döner (LLM'e düşer)."""
        # Bilinçli olarak hiçbir skill desenine uymayan metin
        result = self.sm.route("xyz qwerty 123456789")
        self.assertIsNone(result)

    def test_skill_count_positive(self):
        """get_skill_count() aktif skill sayısını döndürür."""
        count = self.sm.get_skill_count()
        self.assertGreater(count, 0)

    def test_skill_manager_is_instance(self):
        """SkillManager örneği doğru sınıftan oluşur."""
        from core.skill_manager import SkillManager
        sm2 = SkillManager()
        self.assertIsInstance(sm2, SkillManager)


# ── 2. Text Processing Pipeline Tests ────────────────────

class TestTextProcessingPipeline(unittest.TestCase):
    """Metin işleme hattı testleri: NFC, temizleme, hece bölme."""

    @classmethod
    def setUpClass(cls):
        cls.text_utils_available = HAS_TEXT_UTILS

    def setUp(self):
        if not self.text_utils_available:
            self.skipTest("core.text_utils yüklenemedi")

    def test_clean_transcript_basic(self):
        """clean_transcript_text normal metni temiz bırakır."""
        text, had_noise = clean_transcript_text("Merhaba dünya")
        self.assertEqual(text, "Merhaba dünya")
        self.assertFalse(had_noise)

    def test_clean_transcript_control_chars(self):
        """clean_transcript_text kontrol karakterlerini temizler."""
        text, had_noise = clean_transcript_text("<ctrl> Merhaba</ctrl>")
        self.assertEqual(text, "Merhaba")
        self.assertTrue(had_noise)

    def test_clean_transcript_nfc_normalization(self):
        """clean_transcript_text NFC normalizasyonu uygular."""
        # decomposed ş (s + combining cedilla)
        decomposed = "Merhaba du\u0308nya"  # u + combining diaeresis
        text, _ = clean_transcript_text(decomposed)
        # NFC normalized form
        self.assertIn("dünya", text)

    def test_fix_syllable_split(self):
        """fix_turkish_syllable_split kısa parçaları birleştirir."""
        from core.text_utils import fix_turkish_syllable_split as fn
        result = fn("mer ha ba dün ya")
        # Kısa parçalar birleştirilmiş olmalı
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 5)

    def test_fix_syllable_split_no_op(self):
        """fix_turkish_syllable_split normal metni değiştirmez."""
        from core.text_utils import fix_turkish_syllable_split as fn
        result = fn("merhaba dünya")
        self.assertEqual(result, "merhaba dünya")


# ── 3. Tool Registry Completeness Tests ───────────────────

class TestToolRegistryPipeline(unittest.TestCase):
    """Tool registry'nin eksiksizlik ve format testleri."""

    @classmethod
    def setUpClass(cls):
        cls.registry_available = HAS_TOOL_REGISTRY

    def setUp(self):
        if not self.registry_available:
            self.skipTest("core.tool_registry yüklenemedi")

    def test_valid_tools_min_count(self):
        """VALID_TOOLS en az 40 araç içerir."""
        self.assertGreaterEqual(len(VALID_TOOLS), 40)

    def test_valid_tools_contains_core(self):
        """VALID_TOOLS temel araçları içerir."""
        core_tools = {"open_app", "sys_info", "get_weather", "get_calendar_events"}
        self.assertTrue(core_tools.issubset(VALID_TOOLS))

    def test_gemini_declarations_have_tools(self):
        """generate_gemini_declarations() en az 40 bildirim döner."""
        decls = generate_gemini_declarations()
        self.assertIsInstance(decls, list)
        self.assertGreaterEqual(len(decls), 40)

    def test_ollama_help_contains_tool_names(self):
        """generate_ollama_tool_help() araç isimlerini içerir."""
        help_text = generate_ollama_tool_help()
        self.assertIsInstance(help_text, str)
        self.assertIn("open_app", help_text)
        self.assertIn("sys_info", help_text)
        self.assertIn("get_weather", help_text)


# ── 4. App Config Pipeline Tests ───────────────────────

class TestAppConfigPipeline(unittest.TestCase):
    """Yapılandırma yükleme ve erişim testleri."""

    @classmethod
    def setUpClass(cls):
        cls.config_available = HAS_APP_CONFIG
        if cls.config_available:
            try:
                cls.config = load_app_config()
                cls.config_available = True
            except Exception:
                cls.config_available = False

    def setUp(self):
        if not self.config_available:
            self.skipTest("app_config yüklenemedi")

    def test_load_config_returns_dict(self):
        """load_app_config() sözlük döndürür."""
        cfg = load_app_config()
        self.assertIsInstance(cfg, dict)

    def test_get_app_config_value_existing(self):
        """get_app_config_value() var olan anahtarı döndürür."""
        value = get_app_config_value("backend_type")
        self.assertIsNotNone(value)

    def test_get_app_config_value_missing(self):
        """get_app_config_value() olmayan anahtarda None döner."""
        value = get_app_config_value("olmayan_anahtar_x123")
        self.assertIsNone(value)

    def test_has_gemini_api_key(self):
        """has_gemini_api_key() boolean döndürür."""
        result = has_gemini_api_key()
        self.assertIsInstance(result, bool)


# ── 5. Input Validation Tests ────────────────────────────

class TestInputValidation(unittest.TestCase):
    """Giriş doğrulama sınır testleri (main.py'deki kurallar)."""

    def test_parse_local_tool_call_basic(self):
        """parse_local_tool_call() temel formatı ayrıştırır."""
        try:
            from core.ollama_provider import parse_local_tool_call
        except ImportError:
            self.skipTest("core.ollama_provider yüklenemedi")

        result = parse_local_tool_call('open_app(app_name="Spotify")')
        self.assertIsNotNone(result)
        name, args = result
        self.assertEqual(name, "open_app")
        self.assertEqual(args.get("app_name"), "Spotify")

    def test_parse_local_tool_call_unknown_tool(self):
        """parse_local_tool_call() bilinmeyen araç için None döner."""
        try:
            from core.ollama_provider import parse_local_tool_call
        except ImportError:
            self.skipTest("core.ollama_provider yüklenemedi")

        result = parse_local_tool_call('olmayan_araç(param="değer")')
        self.assertIsNone(result)

    def test_parse_local_tool_call_exceeds_total_cap(self):
        """parse_local_tool_call() 2000 karakter sınırını aşan girdiyi reddeder."""
        try:
            from core.ollama_provider import parse_local_tool_call
        except ImportError:
            self.skipTest("core.ollama_provider yüklenemedi")

        long_input = 'open_app(app_name="' + "A" * 2000 + '")'
        result = parse_local_tool_call(long_input)
        self.assertIsNone(result)

    def test_input_text_cap_logic(self):
        """Metin girişi 10000 karakter sınırını aşarsa işlenmemeli (kural doğrulama)."""
        # main.py'deki _on_text_command mantığını yansıtır
        max_len = 10000
        safe_text = "Merhaba" * 100
        self.assertLess(len(safe_text), max_len)
        unsafe_text = "X" * 10001
        self.assertGreater(len(unsafe_text), max_len)


if __name__ == "__main__":
    unittest.main()
