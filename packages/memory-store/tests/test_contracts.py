"""
Contract tests for Memory Store library.

Tests define the interaction boundary between memory-store and its
consumers. Uses real filesystem operations (temp files), no mocks.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class MemoryStoreBaseContract(unittest.TestCase):
    """Basic CRUD operations."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_store(self, **kw):
        from memory_store import MemoryStore
        return MemoryStore(file_path=str(self._file), **kw)

    def test_set_and_get_string(self):
        store = self._make_store()
        store.set("greeting", "Merhaba")
        self.assertEqual(store.get("greeting"), "Merhaba")

    def test_set_and_get_dict(self):
        store = self._make_store()
        store.set("user", {"name": "Ali", "age": 30})
        self.assertEqual(store.get("user"), {"name": "Ali", "age": 30})

    def test_get_nonexistent_returns_none(self):
        store = self._make_store()
        self.assertIsNone(store.get("nothing"))

    def test_set_overwrites(self):
        store = self._make_store()
        store.set("key", "first")
        store.set("key", "second")
        self.assertEqual(store.get("key"), "second")

    def test_set_nested_key(self):
        store = self._make_store()
        store.set("user.name", "Ali")
        self.assertEqual(store.get("user.name"), "Ali")

    def test_persistence_across_instances(self):
        store1 = self._make_store()
        store1.set("city", "Istanbul")
        del store1
        store2 = self._make_store()
        self.assertEqual(store2.get("city"), "Istanbul")

    def test_load_reloads_from_disk(self):
        store = self._make_store()
        store.set("x", 1)
        # Manually modify the file behind the store's back
        data = json.loads(self._file.read_text(encoding="utf-8"))
        data["x"] = 999
        self._file.write_text(json.dumps(data), encoding="utf-8")
        store.load()
        self.assertEqual(store.get("x"), 999)


class MemoryStoreMergeContract(unittest.TestCase):
    """Deep merge behaviour."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_store(self):
        from memory_store import MemoryStore
        return MemoryStore(file_path=str(self._file))

    def test_merge_adds_new_keys(self):
        store = self._make_store()
        store.merge("user", {"city": "Istanbul"})
        self.assertEqual(store.get("user"), {"city": "Istanbul"})

    def test_merge_combines_nested(self):
        store = self._make_store()
        store.set("user", {"name": "Ali", "age": 30})
        store.merge("user", {"age": 31, "city": "Istanbul"})
        self.assertEqual(store.get("user"), {"name": "Ali", "age": 31, "city": "Istanbul"})

    def test_merge_non_dict_overwritten_by_dict(self):
        store = self._make_store()
        store.set("x", "string")
        store.merge("x", {"y": 1})
        self.assertEqual(store.get("x"), {"y": 1})

    def test_merge_nested_path(self):
        store = self._make_store()
        store.set("a.b", {"c": 1})
        store.merge("a.b", {"d": 2})
        self.assertEqual(store.get("a.b"), {"c": 1, "d": 2})

    def test_multiple_merges_accumulate(self):
        store = self._make_store()
        store.merge("prefs", {"theme": "dark"})
        store.merge("prefs", {"lang": "tr"})
        store.merge("prefs", {"theme": "light"})
        self.assertEqual(store.get("prefs"), {"theme": "light", "lang": "tr"})


class MemoryStoreSearchContract(unittest.TestCase):
    """Text search with Turkish normalization."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_store(self):
        from memory_store import MemoryStore
        return MemoryStore(file_path=str(self._file))

    def test_search_by_value(self):
        store = self._make_store()
        store.set("city", "Istanbul")
        results = store.search("Istanbul")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["key"], "city")

    def test_search_turkish_normalization(self):
        store = self._make_store()
        store.set("city", "İstanbul")
        results = store.search("istanbul")
        self.assertGreaterEqual(len(results), 1)

    def test_search_by_category_key(self):
        store = self._make_store()
        store.set("user.name", "Ali")
        store.set("user.city", "Ankara")
        results = store.search("user")
        self.assertGreaterEqual(len(results), 1)

    def test_search_no_match_returns_empty(self):
        store = self._make_store()
        store.set("a", "b")
        results = store.search("xyzzy")
        self.assertEqual(len(results), 0)

    def test_search_return_format(self):
        store = self._make_store()
        store.set("city", "Ankara")
        results = store.search("ankara")
        self.assertIn("category", results[0])
        self.assertIn("key", results[0])
        self.assertIn("value", results[0])


class MemoryStoreDeleteContract(unittest.TestCase):
    """Delete operations."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_store(self):
        from memory_store import MemoryStore
        return MemoryStore(file_path=str(self._file))

    def test_delete_by_category_key(self):
        store = self._make_store()
        store.set("user.name", "Ali")
        store.delete(category="user", key="name")
        self.assertIsNone(store.get("user.name"))

    def test_delete_by_match_text(self):
        store = self._make_store()
        store.set("city", "Ankara")
        result = store.delete(match_text="Ankara")
        self.assertIsNone(store.get("city"))

    def test_delete_nonexistent_returns_message(self):
        store = self._make_store()
        result = store.delete(category="ghost", key="nothing")
        self.assertIsInstance(result, str)

    def test_delete_emptied_category_removed(self):
        store = self._make_store()
        store.set("user.name", "Ali")
        store.delete(category="user", key="name")
        # The category key itself should be gone
        all_data = store._data
        self.assertNotIn("user", all_data)


class MemoryStoreFormatContract(unittest.TestCase):
    """Prompt formatting."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _make_store(self):
        from memory_store import MemoryStore
        return MemoryStore(file_path=str(self._file))

    def test_format_returns_string(self):
        store = self._make_store()
        store.set("city", "Istanbul")
        output = store.format()
        self.assertIsInstance(output, str)
        self.assertIn("city", output)
        self.assertIn("Istanbul", output)

    def test_format_empty_returns_empty_string(self):
        store = self._make_store()
        self.assertEqual(store.format(), "")

    def test_format_nested(self):
        store = self._make_store()
        store.set("user.name", "Ali")
        store.set("user.city", "Ankara")
        output = store.format()
        self.assertIn("Ali", output)
        self.assertIn("Ankara", output)


class MemoryStoreCLIContract(unittest.TestCase):
    """CLI: stdin/stdout/--json per Principle VI."""

    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp(prefix="mem_ctr_"))
        self._store_file = self._tmp / "store.json"

    def tearDown(self):
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _cli(self, *args: str) -> subprocess.CompletedProcess:
        env = {"MEMORY_STORE_FILE": str(self._store_file)}
        return subprocess.run(
            [sys.executable, "-m", "memory_store", *args],
            capture_output=True, text=True, timeout=10,
            env={**{k: v for k, v in env.items()}},
        )

    def test_cli_set_and_get(self):
        r1 = self._cli("set", "user", "name", "Ali")
        self.assertEqual(r1.returncode, 0)
        r2 = self._cli("get", "user", "name")
        self.assertEqual(r2.returncode, 0)
        self.assertIn("Ali", r2.stdout)

    def test_cli_get_nonexistent(self):
        result = self._cli("get", "ghost")
        self.assertNotEqual(result.returncode, 0)

    def test_cli_set_json_output(self):
        result = self._cli("set", "city", "Istanbul", "--json")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["key"], "city")

    def test_cli_search(self):
        self._cli("set", "city", "Ankara")
        result = self._cli("search", "ankara")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Ankara", result.stdout)

    def test_cli_delete(self):
        self._cli("set", "temp", "value")
        result = self._cli("delete", "temp")
        self.assertEqual(result.returncode, 0)

    def test_cli_preview(self):
        self._cli("set", "a", "1")
        self._cli("set", "b", "2")
        result = self._cli("preview")
        self.assertEqual(result.returncode, 0)
        self.assertIn("a", result.stdout)
