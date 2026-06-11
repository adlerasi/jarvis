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

TEST_DIR = Path(tempfile.mkdtemp(prefix="test_memory_"))
TEST_MEMORY_FILE = TEST_DIR / "memory.json"

from memory._store import MemoryStore


def _make_test_store():
    return MemoryStore(file_path=str(TEST_MEMORY_FILE))


class TestMemoryManager(unittest.TestCase):
    """memory_manager pure fonksiyon testleri."""

    def setUp(self):
        from memory import memory_manager
        self.mod = memory_manager
        # Reset singleton so each test gets fresh store
        self.mod._store = None
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        if TEST_MEMORY_FILE.exists():
            TEST_MEMORY_FILE.unlink()

    def _patch_store(self):
        return patch("memory.memory_manager._get_store", return_value=_make_test_store())

    def test_deep_merge_flat(self):
        """_deep_merge duz sozlukleri birlestirir."""
        base = {"a": 1, "b": 2}
        self.mod._deep_merge(base, {"b": 3, "c": 4})
        self.assertEqual(base, {"a": 1, "b": 3, "c": 4})

    def test_deep_merge_nested(self):
        """_deep_merge ic ice sozlukleri recursive birlestirir."""
        base = {"user": {"name": "Ali", "age": 30}}
        self.mod._deep_merge(base, {"user": {"age": 31, "city": "Istanbul"}})
        self.assertEqual(base["user"], {"name": "Ali", "age": 31, "city": "Istanbul"})

    def test_deep_merge_overwrite_non_dict(self):
        """_deep_merge dict olmayan degeri dict ile ezer."""
        base = {"x": "string"}
        self.mod._deep_merge(base, {"x": {"y": 1}})
        self.assertEqual(base, {"x": {"y": 1}})

    def test_normalize_text(self):
        """_normalize_text Turkce karakterleri normalize eder."""
        text = self.mod._normalize_text("İstanbul")
        self.assertIn("istanbul", text)
        self.assertEqual(self.mod._normalize_text("  Merhaba  "), "merhaba")
        self.assertEqual(self.mod._normalize_text(""), "")

    def test_tokenize_text(self):
        """_tokenize_text metni token'lara ayirir."""
        tokens = self.mod._tokenize_text("Merhaba dünya")
        self.assertIn("merhaba", tokens)
        self.assertIn("dunya", tokens)

    def test_entry_value_text_dict(self):
        """_entry_value_text dict'ten value alanini cikarir."""
        result = self.mod._entry_value_text({"value": "test_value"})
        self.assertEqual(result, "test_value")

    def test_entry_value_text_plain(self):
        """_entry_value_text duz degeri string'e cevirir."""
        self.assertEqual(self.mod._entry_value_text("direct"), "direct")
        self.assertEqual(self.mod._entry_value_text(42), "42")
        self.assertEqual(self.mod._entry_value_text(None), "None")

    def test_entry_matches_exact(self):
        """_entry_matches tam eslesme bulur."""
        result = self.mod._entry_matches("test", "category", "key", "test_value")
        self.assertTrue(result)

    def test_entry_matches_no_match(self):
        """_entry_matches eslesme yoksa False doner."""
        result = self.mod._entry_matches("xyz_not_found_12345", "cat", "key", "value")
        self.assertFalse(result)

    def test_format_memory_for_prompt_empty(self):
        """format_memory_for_prompt bos dict icin '' doner."""
        result = self.mod.format_memory_for_prompt({})
        self.assertEqual(result, "")

    def test_format_memory_for_prompt_with_data(self):
        """format_memory_for_prompt dict'i prompt formatina cevirir."""
        memory = {"identity": {"name": {"value": "Ali"}}}
        result = self.mod.format_memory_for_prompt(memory)
        self.assertIn("identity/name", result)
        self.assertIn("Ali", result)

    def test_load_memory_returns_dict(self):
        """load_memory() dict doner (bos olsa bile)."""
        with self._patch_store():
            result = self.mod.load_memory()
        self.assertIsInstance(result, dict)

    def test_update_and_delete_memory_cycle(self):
        """update_memory + delete_memory CRUD dongusu calisir."""
        with self._patch_store():
            original = self.mod.load_memory()
            try:
                test_key = f"_test_key_{os.urandom(4).hex()}"
                self.mod.update_memory({"notes": {test_key: {"value": "test_value"}}})
                loaded = self.mod.load_memory()
                self.assertIn(test_key, loaded.get("notes", {}))

                # Sil
                result = self.mod.delete_memory("notes", test_key)
                self.assertIn("kaldirildi", result)
                loaded_after = self.mod.load_memory()
                self.assertNotIn(test_key, loaded_after.get("notes", {}))
            finally:
                # Temizlik: test kaydini kalici birakma
                try:
                    self.mod.delete_memory("notes", test_key)
                except Exception:
                    pass

    # ── load_memory file I/O ─────────────────────────────────────────

    def test_load_memory_no_file(self):
        """load_memory dosya yokken {} doner."""
        with self._patch_store():
            result = self.mod.load_memory()
        self.assertEqual(result, {})

    def test_load_memory_corrupted_json(self):
        """load_memory bozuk JSON'da {} doner."""
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        TEST_MEMORY_FILE.write_text("{invalid", encoding="utf-8")
        with self._patch_store():
            result = self.mod.load_memory()
        self.assertEqual(result, {})

    # ── delete_memory standalone ──────────────────────────────────────

    def test_delete_memory_category_key_exact(self):
        """delete_memory category+key ile tam eslesme siler."""
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        TEST_MEMORY_FILE.write_text(json.dumps({"cats": {"whiskers": {"value": "fluffy"}}}), encoding="utf-8")
        with self._patch_store():
            result = self.mod.delete_memory("cats", "whiskers")
        self.assertIn("kaldirildi", result)
        loaded = json.loads(TEST_MEMORY_FILE.read_text(encoding="utf-8"))
        self.assertNotIn("whiskers", loaded.get("cats", {}))

    def test_delete_memory_empty_bucket_removes_category(self):
        """delete_memory son entry silinince kategori de silinir."""
        TEST_DIR.mkdir(parents=True, exist_ok=True)
        TEST_MEMORY_FILE.write_text(json.dumps({"cats": {"whiskers": "fluffy"}}), encoding="utf-8")
        with self._patch_store():
            self.mod.delete_memory("cats", "whiskers")
        loaded = json.loads(TEST_MEMORY_FILE.read_text(encoding="utf-8"))
        self.assertNotIn("cats", loaded)

    def test_delete_memory_not_found(self):
        """delete_memory olmayan kayitta hata mesaji doner."""
        with self._patch_store():
            store = self.mod._get_store()
            store.data.update({"existing": {"real": "value"}})
            result = self.mod.delete_memory("nonexistent", "nope")
        self.assertIn("bulamadim", result)

    def test_delete_memory_empty_storage(self):
        """delete_memory bos hafizada uyari doner."""
        with self._patch_store():
            result = self.mod.delete_memory("x", "y")
        self.assertIn("yok", result)

    def test_delete_memory_match_text(self):
        """delete_memory match_text ile fuzzy silme calisir."""
        with patch("memory.memory_manager._get_store",
                   return_value=MemoryStore(file_path=str(TEST_MEMORY_FILE))):
            self.mod._get_store().data.update({"cats": {"whiskers": {"value": "fluffy"}}})
            result = self.mod.delete_memory(match_text="whiskers")
        self.assertIn("kaldirildi", result)

    def test_delete_memory_no_args(self):
        """delete_memory argsiz hata mesaji doner."""
        with self._patch_store():
            store = self.mod._get_store()
            store.data.update({"dummy": "data"})
            result = self.mod.delete_memory()
        self.assertIn("gerekli", result)

    # ── _entry_matches edge cases ────────────────────────────────────────

    def test_entry_matches_short_token(self):
        """_entry_matches <3 char token'lari yoksayar."""
        result = self.mod._entry_matches("ab", "cat", "key", "value")
        self.assertFalse(result)

    def test_entry_matches_partial_token(self):
        """_entry_matches kismi token eslesmesi."""
        result = self.mod._entry_matches("whisk", "cat", "key", "whiskers")
        self.assertTrue(result)

    def test_entry_matches_single_token_min_match(self):
        """_entry_matches tek tokenda 1 eslesme yeterli."""
        result = self.mod._entry_matches("whiskers", "animal", "whiskers", "soft")
        self.assertTrue(result)

    # ── _normalize_text edge cases ───────────────────────────────────────

    def test_normalize_text_none(self):
        """_normalize_text None'u bos string yapar."""
        result = self.mod._normalize_text(None)
        self.assertEqual(result, "")

    def test_normalize_text_combining_chars(self):
        """_normalize_text NFKD combining karakterleri temizler."""
        result = self.mod._normalize_text("caf\u00e9")
        self.assertEqual(result, "cafe")

    def test_normalize_text_dotted_i(self):
        """_normalize_text İ (dotted I) -> i, ı -> i."""
        result = self.mod._normalize_text("IĞDIR")
        self.assertIn("i", result)
        self.assertNotIn("\u0130", result)

    # ── _entry_value_text edge cases ─────────────────────────────────────

    def test_entry_value_text_dict_no_value_key(self):
        """_entry_value_text 'value' anahtari olmayan dict'i JSON'a cevirir."""
        result = self.mod._entry_value_text({"raw": "data"})
        self.assertIn("raw", result)
        self.assertIn("data", result)

    # ── format_memory_for_prompt edge cases ──────────────────────────────

    def test_format_memory_for_prompt_whatsapp(self):
        """format_memory_for_prompt whatsapp_contacts ozel formatini kullanir."""
        memory = {
            "whatsapp_contacts": {
                "ali": {
                    "display_name": "Ali Veli",
                    "value": "+905551234567",
                    "aliases": ["veli", "ali"]
                }
            }
        }
        result = self.mod.format_memory_for_prompt(memory)
        self.assertIn("whatsapp_contacts/Ali Veli", result)
        self.assertIn("+905551234567", result)

    def test_format_memory_for_prompt_non_dict_item(self):
        """format_memory_for_prompt dict olmayan ogeyi duz yazdirir."""
        memory = {"favorite_color": "blue"}
        result = self.mod.format_memory_for_prompt(memory)
        self.assertIn("favorite_color: blue", result)

    def test_format_memory_for_prompt_dict_no_value(self):
        """format_memory_for_prompt 'value' anahtari olmayan dict'i aynen yazdirir."""
        memory = {"prefs": {"theme": {"raw": "dark"}}}
        result = self.mod.format_memory_for_prompt(memory)
        self.assertIn("prefs/theme", result)

    # ── Module constants ────────────────────────────────────────────

    def test_memory_file_constant(self):
        """MEMORY_FILE memory/ icinde ve .json uzantili."""
        self.assertIn("memory", str(self.mod.MEMORY_FILE))
        self.assertTrue(str(self.mod.MEMORY_FILE).endswith(".json"))

    def test_base_dir_constant(self):
        """BASE_DIR proje kokunu gosterir."""
        self.assertTrue((self.mod.BASE_DIR / "main.py").exists())


# =============================================================================
# 6. SAGLIK (health) — SAF FONKSIYON TESTLERI
# =============================================================================
