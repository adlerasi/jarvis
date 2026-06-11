from __future__ import annotations

import sys
import unittest
from unittest.mock import patch, mock_open
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestVoiceCodingSkill(unittest.TestCase):
    """voice_coding_skill pure function tests."""

    def setUp(self):
        from skills.voice_coding.voice_coding_skill import (
            route_voice_coding_request,
            _extract_file_path,
            _extract_function_name,
            _handle_create,
            _handle_add_import,
            _handle_fix,
            _handle_refactor,
        )
        self.route = route_voice_coding_request
        self.extract_path = _extract_file_path
        self.extract_fn = _extract_function_name
        self.handle_create = _handle_create
        self.handle_add_import = _handle_add_import
        self.handle_fix = _handle_fix
        self.handle_refactor = _handle_refactor

    def test_extract_file_path_with_prefix(self):
        path = self.extract_path("file: deneme.py")
        self.assertEqual(path, "deneme.py")

    def test_extract_file_path_no_match(self):
        path = self.extract_path("merhaba dünya")
        self.assertIsNone(path)

    def test_extract_function_name_with_prefix(self):
        name = self.extract_fn("fonksiyon adı: test_func")
        self.assertEqual(name, "test_func")

    def test_extract_function_name_def(self):
        name = self.extract_fn("def my_function")
        self.assertEqual(name, "my_function")

    def test_extract_function_name_no_match(self):
        name = self.extract_fn("merhaba dünya")
        self.assertIsNone(name)

    def test_route_create_no_path(self):
        result = self.route("kod yaz")
        self.assertIsNotNone(result)
        self.assertIn("Dosya yolu", result)

    def test_route_add_import_no_path(self):
        result = self.route("import ekle")
        self.assertIsNotNone(result)
        self.assertIn("Dosya yolu", result)

    def test_route_no_match(self):
        result = self.route("merhaba bugün nasılsın")
        self.assertIsNone(result)

    def test_route_empty_string(self):
        result = self.route("")
        self.assertIsNone(result)

    def test_route_whitespace(self):
        result = self.route("   ")
        self.assertIsNone(result)

    @patch("skills.voice_coding.voice_coding_skill.Path.write_text")
    @patch("skills.voice_coding.voice_coding_skill.Path.exists", return_value=False)
    @patch("skills.voice_coding.voice_coding_skill.Path.mkdir")
    def test_route_create_file(self, mock_mkdir, mock_exists, mock_write):
        result = self.route("kod yaz path: test_create.py")
        self.assertIsNotNone(result)
        self.assertIn("olusturuldu", result)

    @patch("skills.voice_coding.voice_coding_skill.Path.exists", return_value=True)
    def test_route_create_existing_file(self, mock_exists):
        result = self.route("kod yaz path: test_create.py")
        self.assertIsNotNone(result)
        self.assertIn("zaten mevcut", result)

    @patch("skills.voice_coding.voice_coding_skill.Path.read_text",
           return_value="")
    @patch("skills.voice_coding.voice_coding_skill.Path.exists", return_value=True)
    def test_route_add_import_no_import_stmt(self, mock_exists, mock_read):
        result = self.route("import ekle path: test.py")
        self.assertIsNotNone(result)
        self.assertIn("Import ifadesi", result)

    @patch("skills.voice_coding.voice_coding_skill.Path.read_text",
           return_value="x = 1\n")
    @patch("skills.voice_coding.voice_coding_skill.Path.exists", return_value=True)
    def test_route_fix_no_error_desc(self, mock_exists, mock_read):
        # "fix error test.py" — the sub regex strips the entire text
        # (fix\s+error\s+\S+\s*) leaving empty error_desc → "okundu" branch
        result = self.route("fix error test.py")
        self.assertIsNotNone(result)
        self.assertIn("okundu", result)

    @patch("skills.voice_coding.voice_coding_skill.Path.read_text",
           return_value="x = 1\ndef foo():\n    pass\n")
    @patch("skills.voice_coding.voice_coding_skill.Path.exists", return_value=True)
    def test_route_refactor(self, mock_exists, mock_read):
        result = self.route("refactor et path: test.py")
        self.assertIsNotNone(result)
        self.assertIn("satir", result)

    def test_handle_create_no_path(self):
        result = self.handle_create("kod yaz")
        self.assertIn("belirtilmedi", result)

    def test_handle_add_import_no_path(self):
        result = self.handle_add_import("import ekle")
        self.assertIn("belirtilmedi", result)

    def test_handle_fix_no_path(self):
        result = self.handle_fix("kod duzelt")
        self.assertIn("belirtilmedi", result)

    def test_handle_refactor_no_path(self):
        result = self.handle_refactor("refactor et")
        self.assertIn("belirtilmedi", result)
