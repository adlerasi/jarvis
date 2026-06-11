from __future__ import annotations

import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

BASE_DIR = Path(__file__).resolve().parent.parent


class TestDiskPredictor(unittest.TestCase):
    """DiskPredictor SQLite tabanli disk tahmin modulu testleri."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "test_disk.db"

    def tearDown(self):
        self.tmp.cleanup()

    def test_module_import(self):
        """actions.disk_predictor import edilebilmeli."""
        from actions.disk_predictor import DiskPredictor
        self.assertIsNotNone(DiskPredictor)

    def test_init_creates_db(self):
        """__init__ SQLite DB dosyasini olusturmali."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        self.assertTrue(self.db_path.exists())

    def test_init_db_tables(self):
        """DB'de dogru tablolar olusmali."""
        from actions.disk_predictor import DiskPredictor
        import sqlite3
        dp = DiskPredictor(db_path=self.db_path)
        conn = sqlite3.connect(str(self.db_path))
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        self.assertIn(("disk_history",), tables)

    def test_record_sample(self):
        """record_sample() calisabilmeli (en azindan hata firlatmamali)."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp.record_sample()
        self.assertIsInstance(result, str)

    def test_predict_full_insufficient_data(self):
        """predict_full() yetersiz veride hata mesaji dondurmeli."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp.predict_full("/")
        self.assertIn("error", result)
        self.assertIn("Yetersiz", result["error"])

    def test_simple_prediction_upward(self):
        """_simple_prediction yukari trend hesaplamali."""
        from actions.disk_predictor import DiskPredictor
        import time
        dp = DiskPredictor(db_path=self.db_path)
        now = time.time()
        rows = [
            (now - 86400 * 10, 30.0, 100),
            (now - 86400 * 5,  35.0, 100),
            (now,               40.0, 100),
        ]
        result = dp._simple_prediction(rows)
        self.assertIn("trend", result)
        self.assertEqual(result["trend"], "up")
        self.assertIsNotNone(result["days_until_full"])
        self.assertGreater(result["daily_growth"], 0)

    def test_simple_prediction_downward(self):
        """_simple_prediction asagi trend tespit etmeli."""
        from actions.disk_predictor import DiskPredictor
        import time
        dp = DiskPredictor(db_path=self.db_path)
        now = time.time()
        rows = [
            (now - 86400 * 10, 80.0, 100),
            (now - 86400 * 5,  70.0, 100),
            (now,               60.0, 100),
        ]
        result = dp._simple_prediction(rows)
        self.assertEqual(result["trend"], "down")
        self.assertIsNone(result["days_until_full"])

    def test_simple_prediction_insufficient(self):
        """_simple_prediction 2'den az satirda hata dondurmeli."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp._simple_prediction([(time.time(), 50.0, 100)])
        self.assertIn("error", result)

    def test_get_disk_history_empty(self):
        """get_disk_history kayit yokken mesaj dondurmeli."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp.get_disk_history("/test", days=30)
        self.assertIn("bulunamadı", result)

    def test_cleanup_old_records(self):
        """cleanup_old_records calisabilmeli."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp.cleanup_old_records(keep_days=1)
        self.assertIn("temizlendi", result)

    def test_get_all_predictions_empty(self):
        """get_all_predictions veri yokken mesaj dondurmeli."""
        from actions.disk_predictor import DiskPredictor
        dp = DiskPredictor(db_path=self.db_path)
        result = dp.get_all_predictions()
        self.assertIn("Henüz", result)

    def test_record_and_get_history(self):
        """record_sample sonrasi get_disk_history calismali."""
        from actions.disk_predictor import DiskPredictor
        import sqlite3
        dp = DiskPredictor(db_path=self.db_path)

        # Manuel veri ekle
        now = time.time()
        conn = sqlite3.connect(str(self.db_path))
        conn.execute(
            "INSERT INTO disk_history (timestamp, mountpoint, percent, used_bytes, free_bytes) VALUES (?, ?, ?, ?, ?)",
            (now, "/test", 50.0, 50000000000, 50000000000)
        )
        conn.commit()
        conn.close()

        result = dp.get_disk_history("/test", days=30)
        self.assertNotIn("bulunamadı", result)
        self.assertIn("50.0", result)

    def test_default_min_samples(self):
        """MIN_SAMPLES varsayilan degeri 7 olmali."""
        from actions.disk_predictor import DiskPredictor
        self.assertEqual(DiskPredictor.MIN_SAMPLES, 7)

    def test_confidence_thresholds(self):
        """CONFIDENCE esikleri dogru olmali."""
        from actions.disk_predictor import DiskPredictor
        self.assertEqual(DiskPredictor.CONFIDENCE_HIGH, 0.85)
        self.assertEqual(DiskPredictor.CONFIDENCE_MEDIUM, 0.60)

    def test_get_all_predictions_with_data(self):
        """get_all_predictions veri varken calismali."""
        from actions.disk_predictor import DiskPredictor
        import sqlite3
        dp = DiskPredictor(db_path=self.db_path)
        now = time.time()
        conn = sqlite3.connect(str(self.db_path))
        for i in range(8):
            conn.execute(
                "INSERT INTO disk_history (timestamp, mountpoint, percent, used_bytes, free_bytes) VALUES (?, ?, ?, ?, ?)",
                (now - 86400 * (7 - i), "/test", 30.0 + i * 2, 50000000000, 50000000000)
            )
        conn.commit()
        conn.close()

        result = dp.get_all_predictions()
        self.assertIsInstance(result, str)
        self.assertIn("/test", result)


class TestDiskPredictorQuickFunctions(unittest.TestCase):
    """record_disk_sample ve predict_disk_full wrapper testleri."""

    def test_record_disk_sample(self):
        """record_disk_sample calisabilmeli."""
        from actions.disk_predictor import record_disk_sample
        result = record_disk_sample()
        self.assertIsInstance(result, str)

    def test_predict_disk_full(self):
        """predict_disk_full dict dondurmeli."""
        from actions.disk_predictor import predict_disk_full
        result = predict_disk_full("/nonexistent")
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main(verbosity=2)
