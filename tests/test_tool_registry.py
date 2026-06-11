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


class TestToolRegistry(unittest.TestCase):
    """core/tool_registry.py testleri (provider abstraction)."""

    def test_valid_tools_count(self):
        """VALID_TOOLS 41 araci icerir."""
        from core.tool_registry import VALID_TOOLS
        self.assertEqual(len(VALID_TOOLS), 41)

    def test_valid_tools_contains_core(self):
        """VALID_TOOLS temel araclari icerir."""
        from core.tool_registry import VALID_TOOLS
        for tool in ("open_app", "sys_info", "get_weather", "get_current_location",
                     "shell_run", "browser_control", "play_media", "set_volume"):
            self.assertIn(tool, VALID_TOOLS)

    def test_valid_tools_contains_calendar(self):
        """VALID_TOOLS takvim araclarini icerir."""
        from core.tool_registry import VALID_TOOLS
        for tool in ("get_calendar_events", "add_calendar_event", "delete_calendar_event"):
            self.assertIn(tool, VALID_TOOLS)

    def test_valid_tools_contains_health(self):
        """VALID_TOOLS sistem sagligi araclarini icerir."""
        from core.tool_registry import VALID_TOOLS
        for tool in ("get_system_health", "cleanup_temp_files", "cleanup_recycle_bin",
                     "list_processes", "kill_process", "set_process_priority", "find_process_by_port"):
            self.assertIn(tool, VALID_TOOLS)

    def test_valid_tools_contains_file_tools(self):
        """VALID_TOOLS dosya araclarini icerir."""
        from core.tool_registry import VALID_TOOLS
        for tool in ("find_large_files", "find_duplicate_files", "cleanup_folder", "get_folder_summary"):
            self.assertIn(tool, VALID_TOOLS)

    def test_handler_map_size(self):
        """TOOL_HANDLER_MAP 41 tool handler icerir."""
        from core.tool_registry import TOOL_HANDLER_MAP
        self.assertEqual(len(TOOL_HANDLER_MAP), 41)

    def test_handler_map_all_have_handlers(self):
        """Her VALID_TOOLS icin TOOL_HANDLER_MAP'te handler vardir."""
        from core.tool_registry import VALID_TOOLS, TOOL_HANDLER_MAP
        for tool in VALID_TOOLS:
            self.assertIn(tool, TOOL_HANDLER_MAP,
                          f"{tool} TOOL_HANDLER_MAP'te eksik")

    def test_handler_map_format(self):
        """TOOL_HANDLER_MAP degerleri _handle_ ile baslar."""
        from core.tool_registry import TOOL_HANDLER_MAP
        for name, handler in TOOL_HANDLER_MAP.items():
            self.assertTrue(handler.startswith("_handle_"),
                            f"{name} handler'i _handle_ ile baslamiyor: {handler}")

    def test_gemini_declarations_format(self):
        """generate_gemini_declarations dogru formatta dict doner."""
        from core.tool_registry import generate_gemini_declarations
        decls = generate_gemini_declarations()
        self.assertIsInstance(decls, list)
        self.assertEqual(len(decls), 41)
        for d in decls:
            self.assertIn("name", d)
            self.assertIn("description", d)
            self.assertIn("parameters", d)
            self.assertEqual(d["parameters"]["type"], "OBJECT")
            self.assertIn("properties", d["parameters"])

    def test_gemini_declarations_required(self):
        """generate_gemini_declarations required alanini dogru ekler."""
        from core.tool_registry import generate_gemini_declarations
        decls = generate_gemini_declarations()
        open_app = next(d for d in decls if d["name"] == "open_app")
        self.assertIn("required", open_app["parameters"])
        self.assertIn("app_name", open_app["parameters"]["required"])
        get_weather = next(d for d in decls if d["name"] == "get_weather")
        self.assertNotIn("required", get_weather["parameters"])

    def test_gemini_declarations_types(self):
        """generate_gemini_declarations parametre tiplerini dogru ekler."""
        from core.tool_registry import generate_gemini_declarations
        decls = generate_gemini_declarations()
        open_app = next(d for d in decls if d["name"] == "open_app")
        props = open_app["parameters"]["properties"]
        self.assertEqual(props["app_name"]["type"], "STRING")

    def test_ollama_tool_help_format(self):
        """generate_ollama_tool_help string doner ve arac isimlerini icerir."""
        from core.tool_registry import generate_ollama_tool_help
        help_text = generate_ollama_tool_help()
        self.assertIsInstance(help_text, str)
        self.assertGreater(len(help_text), 500)
        self.assertIn("[KULLANILABİLİR ARAÇLAR]", help_text)
        self.assertIn("open_app(", help_text)
        self.assertIn("get_weather(", help_text)


# =============================================================================
# 16. RNNOISE — GÜRÜLTÜ BASTIRMA
# =============================================================================
