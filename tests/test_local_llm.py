from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestLocalLLMConfig(unittest.TestCase):
    """core.local_llm pure fonksiyon/state testleri (network gerektirmeyen)."""

    def test_module_import(self):
        """core.local_llm import edilebilmeli."""
        from core import local_llm
        self.assertIsNotNone(local_llm)

    def test_load_model_config_returns_dict(self):
        """_load_model_config her zaman dict doner."""
        from core.local_llm import _load_model_config
        config = _load_model_config()
        self.assertIsInstance(config, dict)

    def test_load_model_config_has_llm_key(self):
        """_load_model_config icinde llm anahtari var."""
        from core.local_llm import _load_model_config
        config = _load_model_config()
        self.assertIn("llm", config)

    def test_load_model_config_has_ollama_defaults(self):
        """_load_model_config varsayilan ollama ayarlarina sahip."""
        from core.local_llm import _load_model_config
        config = _load_model_config()
        ollama = config["llm"]["ollama"]
        self.assertEqual(ollama["endpoint"], "http://localhost:11434")
        self.assertEqual(ollama["default_model"], "qwen2.5:1.5b")
        self.assertEqual(ollama["embedding_model"], "nomic-embed-text")

    def test_local_llm_init_defaults(self):
        """LocalLLM varsayilan config ile baslatilir."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        self.assertEqual(llm.endpoint, "http://localhost:11434")
        self.assertEqual(llm.current_model, "qwen2.5:1.5b")
        self.assertEqual(llm._fallback, "qwen2.5:7b")
        self.assertEqual(llm._embedding_model, "nomic-embed-text")

    def test_current_model_property(self):
        """current_model property okunup yazilabilmeli."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        self.assertEqual(llm.current_model, "qwen2.5:1.5b")
        llm.current_model = "llama3:8b"
        self.assertEqual(llm.current_model, "llama3:8b")

    def test_get_parameters_returns_dict(self):
        """get_parameters parametre dict'i dondurur."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        params = llm.get_parameters()
        self.assertIsInstance(params, dict)
        self.assertEqual(params.get("temperature"), 0.7)
        self.assertEqual(params.get("top_p"), 0.9)
        self.assertEqual(params.get("max_tokens"), 2048)

    def test_get_parameters_returns_copy(self):
        """get_parameters disariya kopya doner (ic state degismez)."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        params = llm.get_parameters()
        params["temperature"] = 99.9
        self.assertEqual(llm.get_parameters()["temperature"], 0.7)

    def test_set_parameter_updates(self):
        """set_parameter ile parametre guncellenebilir."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        llm.set_parameter("temperature", 1.5)
        self.assertEqual(llm.get_parameters()["temperature"], 1.5)

    def test_set_parameter_new_key(self):
        """set_parameter yeni anahtar ekleyebilir."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        llm.set_parameter("custom_param", "test_value")
        self.assertEqual(llm.get_parameters()["custom_param"], "test_value")

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        stats = llm.get_stats()
        self.assertIn("ollama_running", stats)
        self.assertIn("current_model", stats)
        self.assertIn("fallback_model", stats)
        self.assertIn("embedding_model", stats)
        self.assertIn("endpoint", stats)
        self.assertIn("parameters", stats)
        self.assertEqual(stats["current_model"], "qwen2.5:1.5b")
        self.assertEqual(stats["endpoint"], "http://localhost:11434")
        self.assertIsInstance(stats["parameters"], dict)

    @unittest.skip("Ortamda Ollama calisiyor olabilir, local test")
    def test_get_stats_has_running_key(self):
        """get_stats ollama_running anahtarini icerir."""
        from core.local_llm import LocalLLM
        llm = LocalLLM()
        stats = llm.get_stats()
        self.assertIn("ollama_running", stats)
        self.assertIsInstance(stats["ollama_running"], bool)

    def test_factory_creates_local_llm(self):
        """create_local_llm LocalLLM instance'i dondurur."""
        from core.local_llm import create_local_llm
        llm = create_local_llm()
        from core.local_llm import LocalLLM
        self.assertIsInstance(llm, LocalLLM)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from core.local_llm import __all__
        self.assertIn("LocalLLM", __all__)
        self.assertIn("create_local_llm", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
