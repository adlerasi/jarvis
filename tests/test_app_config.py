from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestAppConfig(unittest.TestCase):
    """app_config — gerçek dosya I/O ile test (mock sadece subprocess/network)."""

    maxDiff = None

    def setUp(self):
        # Patch CONFIG_PATH to a temp file so we never touch the real config
        self.temp_dir = Path("/tmp") / f"test_app_config_{os.getpid()}"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.temp_dir / "api_keys.json"
        self.config_dir = self.temp_dir

        self._patcher_config_path = patch("app_config.CONFIG_PATH", self.config_file)
        self._patcher_config_dir = patch("app_config.CONFIG_DIR", self.config_dir)
        self.mock_config_path = self._patcher_config_path.start()
        self.mock_config_dir = self._patcher_config_dir.start()

    def tearDown(self):
        self._patcher_config_path.stop()
        self._patcher_config_dir.stop()
        if self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)

    # ── load_app_config ─────────────────────────────────────────────────

    def test_load_app_config_no_file(self):
        """load_app_config config dosyasi yokken DEFAULT_CONFIG doner."""
        from app_config import load_app_config, DEFAULT_CONFIG
        cfg = load_app_config()
        self.assertEqual(cfg["backend_type"], "gemini")
        self.assertEqual(cfg["voice"], "Charon")
        # All DEFAULT_CONFIG keys present
        for k in DEFAULT_CONFIG:
            self.assertIn(k, cfg)

    def test_load_app_config_with_file(self):
        """load_app_config var olan JSON dosyasini okur."""
        self.config_file.write_text(json.dumps({"voice": "Puck", "backend_type": "ollama"}), encoding="utf-8")
        from app_config import load_app_config
        cfg = load_app_config()
        self.assertEqual(cfg["voice"], "Puck")
        self.assertEqual(cfg["backend_type"], "ollama")

    def test_load_app_config_corrupted_file(self):
        """load_app_config bozuk JSON'da DEFAULT_CONFIG doner."""
        self.config_file.write_text("{broken json", encoding="utf-8")
        from app_config import load_app_config, DEFAULT_CONFIG
        cfg = load_app_config()
        for k in DEFAULT_CONFIG:
            self.assertIn(k, cfg)

    def test_load_app_config_empty_file(self):
        """load_app_config bos dosyada DEFAULT_CONFIG doner."""
        self.config_file.write_text("", encoding="utf-8")
        from app_config import load_app_config, DEFAULT_CONFIG
        cfg = load_app_config()
        for k in DEFAULT_CONFIG:
            self.assertIn(k, cfg)

    # ── save_app_config ─────────────────────────────────────────────────

    def test_save_app_config_creates_file(self):
        """save_app_config yeni dosya olusturur ve yazar."""
        from app_config import save_app_config
        result = save_app_config({"voice": "Kore"})
        self.assertTrue(self.config_file.exists())
        self.assertEqual(result["voice"], "Kore")
        # Verify on disk
        raw = json.loads(self.config_file.read_text(encoding="utf-8"))
        self.assertEqual(raw["voice"], "Kore")

    def test_save_app_config_merges_existing(self):
        """save_app_config mevcut config'i korur, sadece yeni degerleri ekler."""
        self.config_file.write_text(json.dumps({"voice": "Kore", "backend_type": "ollama"}), encoding="utf-8")
        from app_config import save_app_config
        result = save_app_config({"backend_type": "gemini"})
        self.assertEqual(result["voice"], "Kore")        # preserved
        self.assertEqual(result["backend_type"], "gemini")  # updated

    def test_save_app_config_skips_none(self):
        """save_app_config None degerleri atlar."""
        self.config_file.write_text(json.dumps({"voice": "Kore"}), encoding="utf-8")
        from app_config import save_app_config
        result = save_app_config({"voice": None, "backend_type": "gemini"})
        self.assertEqual(result["voice"], "Kore")  # unchanged
        self.assertEqual(result["backend_type"], "gemini")

    def test_save_app_config_empty_updates(self):
        """save_app_config bos dict ile mevcut config'i korur."""
        self.config_file.write_text(json.dumps({"voice": "Kore"}), encoding="utf-8")
        from app_config import save_app_config
        result = save_app_config({})
        self.assertEqual(result["voice"], "Kore")

    # ── get_app_config_value ────────────────────────────────────────────

    def test_get_app_config_value_exists(self):
        """get_app_config_value var olan anahtari doner."""
        self.config_file.write_text(json.dumps({"voice": "Puck"}), encoding="utf-8")
        from app_config import get_app_config_value
        self.assertEqual(get_app_config_value("voice"), "Puck")

    def test_get_app_config_value_default(self):
        """get_app_config_value olmayan anahtarda default doner."""
        from app_config import get_app_config_value
        self.assertEqual(get_app_config_value("nonexistent", "fallback"), "fallback")

    def test_get_app_config_value_no_default(self):
        """get_app_config_value olmayan anahtarda None doner."""
        from app_config import get_app_config_value
        self.assertIsNone(get_app_config_value("nonexistent"))

    # ── has_gemini_api_key ──────────────────────────────────────────────

    def test_has_gemini_api_key_true(self):
        """has_gemini_api_key dolu anahtarda True doner."""
        self.config_file.write_text(json.dumps({"gemini_api_key": "AIzaSyTest123"}), encoding="utf-8")
        from app_config import has_gemini_api_key
        self.assertTrue(has_gemini_api_key())

    def test_has_gemini_api_key_empty(self):
        """has_gemini_api_key bos anahtarda False doner."""
        self.config_file.write_text(json.dumps({"gemini_api_key": ""}), encoding="utf-8")
        from app_config import has_gemini_api_key
        self.assertFalse(has_gemini_api_key())

    def test_has_gemini_api_key_missing(self):
        """has_gemini_api_key eksik anahtarda False doner."""
        self.config_file.write_text(json.dumps({"voice": "Puck"}), encoding="utf-8")
        from app_config import has_gemini_api_key
        self.assertFalse(has_gemini_api_key())

    # ── DEFAULT_CONFIG ──────────────────────────────────────────────────

    def test_default_config_structure(self):
        """DEFAULT_CONFIG dogru anahtarlara sahip."""
        from app_config import DEFAULT_CONFIG
        expected_keys = {"gemini_api_key", "voice", "youtube_api_key",
                         "youtube_channel_handle", "backend_type",
                         "ollama_model", "ollama_tts_voice"}
        self.assertEqual(set(DEFAULT_CONFIG.keys()), expected_keys)
        self.assertEqual(DEFAULT_CONFIG["backend_type"], "gemini")
        self.assertEqual(DEFAULT_CONFIG["ollama_tts_voice"], "piper-fahrettin")

    # ── get_ollama_tts_voices (subprocess) ──────────────────────────────

    @patch("subprocess.run")
    def test_get_ollama_tts_voices_edge_tts(self, mock_run):
        """get_ollama_tts_voices edge-tts basarili olunca sesleri ekler."""
        from app_config import get_ollama_tts_voices
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="tr-TR-AhmetNeural\nFake line\ntr-TR-EmelNeural\n"
        )
        # Ensure Fahrettin model doesn't exist in our temp
        with patch("app_config.Path.exists", return_value=True):
            voices = get_ollama_tts_voices()
        ids = [v["id"] for v in voices]
        self.assertIn("piper-fahrettin", ids)
        self.assertIn("edge-ahmet", ids)
        self.assertIn("edge-emel", ids)
        self.assertIn("spd-say", ids)

    @patch("subprocess.run", side_effect=FileNotFoundError("no edge-tts"))
    def test_get_ollama_tts_voices_no_edge(self, mock_run):
        """get_ollama_tts_voices edge-tts yoksa sadece yerel sesleri doner."""
        from app_config import get_ollama_tts_voices
        with patch("app_config.Path.exists", return_value=True):
            voices = get_ollama_tts_voices()
        ids = [v["id"] for v in voices]
        self.assertIn("piper-fahrettin", ids)
        self.assertIn("spd-say", ids)
        self.assertNotIn("edge-ahmet", ids)

    @patch("subprocess.run", side_effect=FileNotFoundError("no edge-tts"))
    def test_get_ollama_tts_voices_no_fahrettin(self, mock_run):
        """get_ollama_tts_voices Fahrettin modeli yoksa spd-say doner."""
        from app_config import get_ollama_tts_voices
        with patch("app_config.Path.exists", return_value=False):
            voices = get_ollama_tts_voices()
        ids = [v["id"] for v in voices]
        self.assertNotIn("piper-fahrettin", ids)
        self.assertIn("spd-say", ids)

    # ── get_ollama_models (network) ─────────────────────────────────────

    @patch("urllib.request.urlopen")
    def test_get_ollama_models_success(self, mock_urlopen):
        """get_ollama_models API'den model listesi doner."""
        from app_config import get_ollama_models
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "models": [{"name": "qwen2.5:1.5b"}, {"name": "llama3:latest"}]
        }).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        models = get_ollama_models()
        self.assertEqual(models, ["qwen2.5:1.5b", "llama3:latest"])

    @patch("urllib.request.urlopen", side_effect=Exception("Connection refused"))
    def test_get_ollama_models_failure(self, mock_urlopen):
        """get_ollama_models baglanti hatasinda bos liste doner."""
        from app_config import get_ollama_models
        models = get_ollama_models()
        self.assertEqual(models, [])

    # ── Module exports ──────────────────────────────────────────────────

    def test_module_functions_exist(self):
        """app_config modulu tum public fonksiyonlari export ediyor."""
        import app_config
        for name in ("load_app_config", "save_app_config", "get_app_config_value",
                      "has_gemini_api_key", "get_ollama_tts_voices", "get_ollama_models"):
            self.assertTrue(hasattr(app_config, name), f"Eksik: {name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
