from __future__ import annotations

import sys
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestMultimodalEngine(unittest.TestCase):
    """MultimodalEngine — thin wrapper, mock-heavy tests."""

    def setUp(self):
        from core.multimodal import MultimodalEngine
        self.engine = MultimodalEngine()
        self.Engine = MultimodalEngine

    # ── Factory ─────────────────────────────────────────────────────────

    def test_factory_creates_engine(self):
        """create_multimodal_engine MultimodalEngine instance'i doner."""
        from core.multimodal import create_multimodal_engine
        engine = create_multimodal_engine()
        self.assertIsInstance(engine, self.Engine)

    # ── analyze_screen ──────────────────────────────────────────────────

    @patch("actions.screen_vision.analyze_screen",
           return_value="Ekranda bir pencere var.")
    def test_analyze_screen_success(self, mock_analyze):
        """analyze_screen basarili olunca sonuc doner."""
        result = self.engine.analyze_screen("Ne goruyorsun?")
        self.assertEqual(result, "Ekranda bir pencere var.")
        mock_analyze.assert_called_once_with(query="Ne goruyorsun?")

    @patch("actions.screen_vision.analyze_screen",
           return_value="Ekranda ne var?")
    def test_analyze_screen_default_query(self, mock_analyze):
        """analyze_screen query'siz cagrilinca varsayilan sorgu kullanilir."""
        result = self.engine.analyze_screen()
        self.assertEqual(result, "Ekranda ne var?")
        mock_analyze.assert_called_once_with(query="Ekranda ne var?")

    @patch("actions.screen_vision.analyze_screen",
           side_effect=ImportError("no module"))
    def test_analyze_screen_import_error(self, mock_analyze):
        """analyze_screen ImportError'da None doner."""
        result = self.engine.analyze_screen()
        self.assertIsNone(result)

    @patch("actions.screen_vision.analyze_screen",
           side_effect=Exception("genel hata"))
    def test_analyze_screen_generic_error(self, mock_analyze):
        """analyze_screen genel hatada None doner."""
        result = self.engine.analyze_screen()
        self.assertIsNone(result)

    # ── capture_photo ───────────────────────────────────────────────────

    @patch("vision.camera_capture.CameraCapture")
    def test_capture_photo_success(self, mock_camera_cls):
        """capture_photo basarili olunca bytes doner."""
        mock_instance = MagicMock()
        mock_instance.capture.return_value = b"fake_jpeg_data"
        mock_camera_cls.return_value = mock_instance

        result = self.engine.capture_photo()
        self.assertEqual(result, b"fake_jpeg_data")
        self.assertIsNotNone(self.engine._camera)

    @patch("vision.camera_capture.CameraCapture")
    def test_capture_photo_caches_camera(self, mock_camera_cls):
        """capture_photo CameraCapture'i cache'ler, ikinci cagri yeni instance olusturmaz."""
        mock_instance = MagicMock()
        mock_instance.capture.return_value = b"jpeg"
        mock_camera_cls.return_value = mock_instance

        self.engine.capture_photo()
        self.engine.capture_photo()
        self.assertEqual(mock_camera_cls.call_count, 1)

    # ── analyze_camera ──────────────────────────────────────────────────

    @patch("core.multimodal.MultimodalEngine.capture_photo", return_value=None)
    def test_analyze_camera_no_photo(self, mock_capture):
        """analyze_camera fotograf alinamazsa uyari doner."""
        result = self.engine.analyze_camera("Ne var?")
        self.assertEqual(result, "Kamera goruntusu alinamadi.")

    @patch("core.multimodal.MultimodalEngine.capture_photo", return_value=b"jpeg")
    @patch("PIL.Image")
    @patch("google.genai.Client")
    @patch("app_config.get_app_config_value", return_value="fake_key")
    def test_analyze_camera_success(self, mock_config, mock_client, mock_pil, mock_capture):
        """analyze_camera basarili olunca analiz sonucu doner."""
        mock_client_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Bir kedi goruyorum."
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client.return_value = mock_client_instance

        result = self.engine.analyze_camera("Ne var?")
        self.assertEqual(result, "Bir kedi goruyorum.")

    # ── analyze_image_file ──────────────────────────────────────────────

    def test_analyze_image_file_not_found(self):
        """analyze_image_file olmayan dosyada uyari doner."""
        result = self.engine.analyze_image_file("/nonexistent/image.jpg")
        self.assertIn("bulunamadi", result.lower())

    @patch("app_config.get_app_config_value", return_value="")
    def test_analyze_image_file_no_api_key(self, mock_config):
        """analyze_image_file API anahtari yoksa uyari doner."""
        result = self.engine.analyze_image_file(str(BASE_DIR / "main.py"))
        self.assertIn("anahtari gerekli", result)

    @patch("app_config.get_app_config_value", return_value="fake_key")
    def test_analyze_image_file_import_error(self, mock_config):
        """analyze_image_file PIL/genai yoksa uyari doner."""
        import builtins
        original_import = builtins.__import__
        def mock_import(name, *args, **kwargs):
            if name == "google":
                raise ImportError("no genai")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = self.engine.analyze_image_file(str(BASE_DIR / "main.py"))
        self.assertIn("kutuphanesi gerekli", result)

    # ── get_stats ───────────────────────────────────────────────────────

    @patch("core.multimodal.MultimodalEngine._check_screen_vision",
           return_value=True)
    def test_get_stats_screen_available(self, mock_check):
        """get_stats screen_vision durumunu gosterir."""
        stats = self.engine.get_stats()
        self.assertTrue(stats["screen_vision_available"])

    def test_get_stats_camera_initially_none(self):
        """get_stats baslangicta camera_available False olmali."""
        stats = self.engine.get_stats()
        self.assertFalse(stats["camera_available"])

    def test_get_stats_keys(self):
        """get_stats dogru anahtarlari icerir."""
        stats = self.engine.get_stats()
        self.assertIn("screen_vision_available", stats)
        self.assertIn("camera_available", stats)

    # ── _check_screen_vision ────────────────────────────────────────────

    @patch("actions.screen_vision.analyze_screen")
    def test_check_screen_vision_true(self, mock_analyze):
        """_check_screen_vision import basariliysa True doner."""
        result = self.engine._check_screen_vision()
        self.assertTrue(result)

    def test_check_screen_vision_false(self):
        """_check_screen_vision import yoksa False doner."""
        engine = self.engine
        key = "actions.screen_vision"
        had_key = key in sys.modules
        old = sys.modules.pop(key, None)
        with patch("builtins.__import__") as mock_import:
            def fake_import(name, *args, **kwargs):
                if name == "actions.screen_vision":
                    raise ImportError("no module")
                return original_import(name, *args, **kwargs)
            _builtins = __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__
            original_import = _builtins["__import__"]
            mock_import.side_effect = fake_import
            result = engine._check_screen_vision()
        if had_key:
            sys.modules[key] = old
        self.assertFalse(result)

    # ── Module exports ──────────────────────────────────────────────────

    def test_module_exports(self):
        """core.multimodal __all__ dogru sembolleri export ediyor."""
        from core import multimodal
        expected = {"MultimodalEngine", "create_multimodal_engine"}
        self.assertEqual(set(multimodal.__all__), expected)
