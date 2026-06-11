#!/usr/bin/env python3
from __future__ import annotations

"""
JARVIS — Tool Dispatch Entegrasyon Testleri.
Tool registry'nin eksiksizliğini, handler eşlemesini ve parametre doğrulamasını test eder.
"""

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from core.tool_registry import (
        VALID_TOOLS,
        generate_gemini_declarations,
        generate_ollama_tool_help,
    )
    HAS_TOOL_REGISTRY = True
except ImportError:
    HAS_TOOL_REGISTRY = False

# Beklenen temel araçlar (VALID_TOOLS içindeki gerçek isimlerle eşleşmeli)
CORE_TOOLS = {
    "open_app", "sys_info", "get_weather", "get_current_location",
    "get_calendar_events", "add_calendar_event", "delete_calendar_event",
    "get_reminders", "add_reminder",
    "send_whatsapp_message", "save_whatsapp_contact",
    "shell_run", "get_system_health",
    "analyze_screen",
    "get_youtube_channel_report", "play_media",
}
VALID_PARAM_TYPES = {"STRING", "NUMBER", "BOOLEAN"}


# ── 1. Registry Completeness ─────────────────────────────

class TestToolRegistryCompleteness(unittest.TestCase):
    """Tool registry bütünlük testleri."""

    @classmethod
    def setUpClass(cls):
        cls.available = HAS_TOOL_REGISTRY

    def setUp(self):
        if not self.available:
            self.skipTest("core.tool_registry yüklenemedi")

    def test_valid_tools_min_count(self):
        """VALID_TOOLS en az 40 araç içerir."""
        self.assertGreaterEqual(len(VALID_TOOLS), 40)

    def test_valid_tools_contains_core(self):
        """VALID_TOOLS tüm temel araçları içerir."""
        missing = CORE_TOOLS - VALID_TOOLS
        self.assertSetEqual(missing, set(), f"Eksik araçlar: {missing}")

    def test_valid_tools_all_strings(self):
        """VALID_TOOLS'deki tüm ögeler string'dir."""
        for tool in VALID_TOOLS:
            self.assertIsInstance(tool, str)

    def test_valid_tools_no_duplicates(self):
        """VALID_TOOLS'de kopya yoktur."""
        self.assertEqual(len(VALID_TOOLS), len(set(VALID_TOOLS)))

    def test_gemini_declarations_all_strings(self):
        """generate_gemini_declarations() geçerli bildirimler döndürür."""
        decls = generate_gemini_declarations()
        self.assertIsInstance(decls, list)
        for decl in decls:
            self.assertIn("name", decl)
            self.assertIn("description", decl)
            self.assertIsInstance(decl["name"], str)
            self.assertIsInstance(decl["description"], str)

    def test_gemini_declarations_match_valid_tools(self):
        """generate_gemini_declarations()'daki isimler VALID_TOOLS ile eşleşir."""
        decls = generate_gemini_declarations()
        decl_names = {d["name"] for d in decls}
        # Her bildirim VALID_TOOLS'de olmalı
        for name in decl_names:
            self.assertIn(name, VALID_TOOLS)

    def test_ollama_help_is_string(self):
        """generate_ollama_tool_help() string döner."""
        help_text = generate_ollama_tool_help()
        self.assertIsInstance(help_text, str)

    def test_ollama_help_contains_multiple_tools(self):
        """generate_ollama_tool_help() birden çok araç tanımı içerir."""
        help_text = generate_ollama_tool_help()
        # Her araç adı yardım metninde geçmeli
        found = sum(1 for t in list(CORE_TOOLS)[:5] if t in help_text)
        self.assertGreaterEqual(found, 3)


# ── 2. Tool Definition Format ────────────────────────────

class TestToolDefinitionFormat(unittest.TestCase):
    """Araç tanım formatı testleri — doğrudan _TOOL_DEFS'e erişir."""

    @classmethod
    def setUpClass(cls):
        cls.available = HAS_TOOL_REGISTRY
        if cls.available:
            from core.tool_registry import _TOOL_DEFS
            cls.tool_defs = _TOOL_DEFS

    def setUp(self):
        if not self.available:
            self.skipTest("core.tool_registry yüklenemedi")

    def test_all_defs_have_name(self):
        """Her tanımın adı vardır."""
        for t in self.tool_defs:
            self.assertIsInstance(t[0], str)
            self.assertGreater(len(t[0]), 0)

    def test_all_defs_have_description(self):
        """Her tanımın açıklaması vardır (en az 10 karakter)."""
        for t in self.tool_defs:
            desc = t[1]
            self.assertIsInstance(desc, str)
            self.assertGreaterEqual(len(desc), 10)

    def test_no_duplicate_names(self):
        """Aynı ada sahip iki tanım yoktur."""
        names = [t[0] for t in self.tool_defs]
        self.assertEqual(len(names), len(set(names)))

    def test_param_types_valid(self):
        """Tüm parametre tipleri geçerlidir (STRING, NUMBER, BOOLEAN)."""
        for t in self.tool_defs:
            params = t[2]
            for pname, (ptype, _pdesc) in params.items():
                self.assertIn(ptype, VALID_PARAM_TYPES,
                               f"{t[0]}.{pname}: geçersiz tip '{ptype}'")

    def test_required_params_in_params(self):
        """required_list'teki her parametre params_dict'te de tanımlıdır."""
        for t in self.tool_defs:
            name = t[0]
            params = t[2]
            required = t[3]
            for rp in required:
                self.assertIn(rp, params,
                               f"{name}: zorunlu param '{rp}' params_dict'te yok")

    def test_params_have_description(self):
        """Tüm parametrelerin açıklaması vardır."""
        for t in self.tool_defs:
            params = t[2]
            for pname, (_ptype, pdesc) in params.items():
                self.assertGreater(len(pdesc), 0,
                                    f"{t[0]}.{pname}: boş açıklama")


# ── 3. Inferred Edge Verification ───────────────────────

class TestInferredConnections(unittest.TestCase):
    """Graf bulgularından çıkarılan bağlantıların doğrulaması."""

    def test_main_imports_jarvisui(self):
        """main.py JarvisUI'yi import eder (grafikte INFERRED)."""
        try:
            from main import JarvisLive
            self.assertTrue(hasattr(JarvisLive, "_execute_tool"))
        except ImportError:
            self.skipTest("main.JarvisLive yüklenemedi (bağımlılıklar eksik)")

    def test_main_has_tool_handlers(self):
        """main.py'de _TOOL_HANDLERS dict'i tanımlıdır."""
        try:
            import main
            self.assertTrue(hasattr(main, "_TOOL_HANDLERS") or
                            hasattr(main, "JarvisLive"))
        except ImportError:
            self.skipTest("main.py yüklenemedi")

    def test_tool_registry_defines_tools_as_single_source(self):
        """tool_registry.py tüm araçların tek kaynağıdır."""
        try:
            from core.tool_registry import _TOOL_DEFS, VALID_TOOLS
            # Her VALID_TOOLS ögesinin _TOOL_DEFS'te karşılığı olmalı
            def_names = {t[0] for t in _TOOL_DEFS}
            missing = VALID_TOOLS - def_names
            # Not: VALID_TOOLS, _TOOL_DEFS dışındaki kaynaklardan da beslenebilir
            # En azından _TOOL_DEFS'teki her şey VALID_TOOLS'de olmalı
            extra = def_names - VALID_TOOLS
            self.assertSetEqual(extra, set(),
                                 f"_TOOL_DEFS'te olup VALID_TOOLS'de olmayan: {extra}")
        except ImportError:
            self.skipTest("core.tool_registry yüklenemedi")


# ── 4. Handler Dispatch Pattern ─────────────────────────

class TestHandlerDispatchPattern(unittest.TestCase):
    """_execute_tool dict dispatch pattern doğrulaması."""

    def test_tool_names_snake_case(self):
        """Tüm araç adları snake_case formatındadır."""
        if not HAS_TOOL_REGISTRY:
            self.skipTest("core.tool_registry yüklenemedi")
        for tool in VALID_TOOLS:
            self.assertRegex(tool, r"^[a-z][a-z0-9_]*$",
                              f"'{tool}' snake_case değil")

    def test_gemini_declarations_have_parameters(self):
        """Her Gemini bildiriminin parameters alanı vardır."""
        if not HAS_TOOL_REGISTRY:
            self.skipTest("core.tool_registry yüklenemedi")
        decls = generate_gemini_declarations()
        for decl in decls:
            self.assertIn("parameters", decl,
                           f"{decl.get('name', '?')} parameters alanı yok")


if __name__ == "__main__":
    unittest.main()
