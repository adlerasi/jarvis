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


class TestYouTubeStats(unittest.TestCase):
    """youtube_stats pure fonksiyon testleri — API cagrisi yok."""

    def setUp(self):
        from actions import youtube_stats
        self.mod = youtube_stats

    def test_format_int(self):
        """_format_int sayilari Turkce formata cevirir."""
        self.assertEqual(self.mod._format_int(1000), "1.000")
        self.assertEqual(self.mod._format_int(1500000), "1.500.000")
        self.assertEqual(self.mod._format_int(0), "0")
        self.assertEqual(self.mod._format_int(999), "999")

    def test_parse_duration_seconds(self):
        """_parse_duration_seconds ISO 8601 surelerini cozer."""
        self.assertEqual(self.mod._parse_duration_seconds("PT1H30M15S"), 5415)
        self.assertEqual(self.mod._parse_duration_seconds("PT45M20S"), 2720)
        self.assertEqual(self.mod._parse_duration_seconds("PT5S"), 5)
        self.assertEqual(self.mod._parse_duration_seconds("PT2H"), 7200)
        self.assertEqual(self.mod._parse_duration_seconds(""), 0)
        self.assertEqual(self.mod._parse_duration_seconds(None), 0)
        self.assertEqual(self.mod._parse_duration_seconds("P1DT1H"), 0)  # ISO_DAY_RE yok

    def test_format_duration(self):
        """_format_duration sureyi Turkce formata cevirir."""
        self.assertEqual(self.mod._format_duration("PT1H30M15S"), "1s 30dk")
        self.assertEqual(self.mod._format_duration("PT45M20S"), "45dk 20sn")
        self.assertEqual(self.mod._format_duration("PT5S"), "5sn")
        self.assertEqual(self.mod._format_duration(""), "")

    def test_parse_dt(self):
        """_parse_dt ISO tarihlerini cozer."""
        result = self.mod._parse_dt("2026-01-15T10:30:00Z")
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 1)
        self.assertIsNone(self.mod._parse_dt(""))
        self.assertIsNone(self.mod._parse_dt(None))
        self.assertIsNone(self.mod._parse_dt("invalid"))

    def test_average(self):
        """_average ortalama hesaplar."""
        self.assertEqual(self.mod._average([1, 2, 3, 4, 5]), 3.0)
        self.assertEqual(self.mod._average([10]), 10.0)
        self.assertEqual(self.mod._average([]), 0.0)

    def test_normalize_channel_ref_with_at(self):
        """_normalize_channel_ref @ ile baslayan handle'i tanir."""
        with patch("actions.youtube_stats.get_app_config_value", return_value=""):
            result_type, result_val = self.mod._normalize_channel_ref("@testchannel")
            self.assertEqual(result_type, "forHandle")
            self.assertEqual(result_val, "@testchannel")

    def test_normalize_channel_ref_with_url(self):
        """_normalize_channel_ref YouTube URL'sini cozer."""
        with patch("actions.youtube_stats.get_app_config_value", return_value=""):
            result_type, result_val = self.mod._normalize_channel_ref(
                "https://www.youtube.com/@testchannel"
            )
            self.assertEqual(result_type, "forHandle")
            self.assertEqual(result_val, "@testchannel")

    def test_normalize_channel_ref_with_channel_id(self):
        """_normalize_channel_ref channel ID'yi tanir."""
        with patch("actions.youtube_stats.get_app_config_value", return_value=""):
            channel_id = "UC1234567890123456789012"
            result_type, result_val = self.mod._normalize_channel_ref(channel_id)
            self.assertEqual(result_type, "id")
            self.assertEqual(result_val, channel_id)

    def test_normalize_channel_ref_empty(self):
        """_normalize_channel_ref bos degerde (None, '') doner."""
        with patch("actions.youtube_stats.get_app_config_value", return_value=""):
            result_type, result_val = self.mod._normalize_channel_ref("")
            self.assertIsNone(result_type)
            self.assertEqual(result_val, "")

    def test_normalize_channel_ref_plain_text(self):
        """_normalize_channel_ref duz metni @ ile handle'a cevirir."""
        with patch("actions.youtube_stats.get_app_config_value", return_value=""):
            result_type, result_val = self.mod._normalize_channel_ref("testchannel")
            self.assertEqual(result_type, "forHandle")
            self.assertEqual(result_val, "@testchannel")

    # ── _days_ago_text ──────────────────────────────────────────────────

    def test_days_ago_text_none(self):
        """_days_ago_text gecersiz tarihte '' doner."""
        result = self.mod._days_ago_text("")
        self.assertEqual(result, "")

    def test_days_ago_text_bugun(self):
        """_days_ago_text bugun icin 'bugun' doner."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        result = self.mod._days_ago_text(now.isoformat())
        self.assertEqual(result, "bugün")

    # ── _trend_sentence ─────────────────────────────────────────────────

    def test_trend_sentence_few_videos(self):
        """_trend_sentence 4'ten az videoda '' doner."""
        videos = [{"views": 100}, {"views": 200}, {"views": 300}]
        result = self.mod._trend_sentence(videos)
        self.assertEqual(result, "")

    def test_trend_sentence_balanced(self):
        """_trend_sentence dengeli performans."""
        videos = [{"views": 200}] * 6
        result = self.mod._trend_sentence(videos)
        self.assertIn("dengeli", result)

    # ── _api_get ────────────────────────────────────────────────────────

    @patch("actions.youtube_stats.requests.get")
    def test_api_get_success(self, mock_get):
        """_api_get basarili yanitta JSON doner."""
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = {"items": [{"id": "test"}]}
        result = self.mod._api_get("videos", {"part": "snippet"}, "fake_key")
        self.assertEqual(result, {"items": [{"id": "test"}]})

    @patch("actions.youtube_stats.requests.get")
    def test_api_get_key_invalid(self, mock_get):
        """_api_get gecersiz anahtarda RuntimeError firlatir."""
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 400
        mock_get.return_value.json.return_value = {
            "error": {"errors": [{"reason": "keyInvalid"}]}
        }
        with self.assertRaises(RuntimeError) as ctx:
            self.mod._api_get("channels", {}, "bad_key")
        self.assertIn("gecersiz", str(ctx.exception))

    @patch("actions.youtube_stats.requests.get")
    def test_api_get_quota_exceeded(self, mock_get):
        """_api_get kota asiminda RuntimeError firlatir."""
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 403
        mock_get.return_value.json.return_value = {
            "error": {"errors": [{"reason": "quotaExceeded"}]}
        }
        with self.assertRaises(RuntimeError) as ctx:
            self.mod._api_get("channels", {}, "key")
        self.assertIn("dolu", str(ctx.exception))

    @patch("actions.youtube_stats.requests.get")
    def test_api_get_forbidden(self, mock_get):
        """_api_get forbidden hatasinda RuntimeError firlatir."""
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 403
        mock_get.return_value.json.return_value = {
            "error": {"errors": [{"reason": "forbidden"}]}
        }
        with self.assertRaises(RuntimeError) as ctx:
            self.mod._api_get("channels", {}, "key")
        self.assertIn("aktif degil", str(ctx.exception))

    @patch("actions.youtube_stats.requests.get")
    def test_api_get_not_found(self, mock_get):
        """_api_get 404'te RuntimeError firlatir."""
        mock_get.return_value.ok = False
        mock_get.return_value.status_code = 404
        mock_get.return_value.json.return_value = {}
        with self.assertRaises(RuntimeError) as ctx:
            self.mod._api_get("channels", {}, "key")
        self.assertIn("bulunamadi", str(ctx.exception))

    # ── get_youtube_channel_report ──────────────────────────────────────

    @patch("actions.youtube_stats.get_app_config_value", return_value="")
    def test_get_report_no_api_key(self, mock_config):
        """get_youtube_channel_report API anahtari yoksa uyari doner."""
        result = self.mod.get_youtube_channel_report()
        self.assertIn("API Key", result)

    @patch("actions.youtube_stats.get_app_config_value", return_value="fake_key")
    @patch("actions.youtube_stats._fetch_channel_payload",
           side_effect=RuntimeError("YouTube kanalini bulamadim."))
    def test_get_report_channel_not_found(self, mock_fetch, mock_config):
        """get_youtube_channel_report kanal bulunamazsa hata mesaji doner."""
        result = self.mod.get_youtube_channel_report()
        self.assertIn("bulamadim", result)

    @patch("actions.youtube_stats.get_app_config_value", return_value="fake_key")
    @patch("actions.youtube_stats._fetch_channel_payload")
    @patch("actions.youtube_stats._fetch_recent_videos", return_value=[])
    def test_get_report_overview(self, mock_videos, mock_fetch, mock_config):
        """get_youtube_channel_report genel bakis metni icerir."""
        mock_fetch.return_value = (
            {
                "snippet": {"title": "Test Kanal", "customUrl": "@testchannel"},
                "statistics": {
                    "subscriberCount": "1500",
                    "viewCount": "50000",
                    "videoCount": "120",
                },
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "UUtest123"}
                },
            },
            "@testchannel",
        )
        result = self.mod.get_youtube_channel_report()
        self.assertIn("Test Kanal", result)
        self.assertIn("1.500", result)
        self.assertIn("50.000", result)

    @patch("actions.youtube_stats.get_app_config_value", return_value="fake_key")
    @patch("actions.youtube_stats._fetch_channel_payload")
    def test_get_report_with_valid_videos(self, mock_fetch, mock_config):
        """get_youtube_channel_report video verisiyle detayli metin doner."""
        from datetime import datetime, timezone, timedelta
        mock_fetch.return_value = (
            {
                "snippet": {"title": "Test Kanal", "customUrl": "@test"},
                "statistics": {
                    "subscriberCount": "1000",
                    "viewCount": "100000",
                    "videoCount": "50",
                },
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "UUtest"}
                },
            },
            "@test",
        )
        mock_videos = [
            {
                "title": "Video 1",
                "published_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                "views": 5000,
                "likes": 200,
                "comments": 50,
                "duration": "PT10M",
            },
            {
                "title": "Video 2",
                "published_at": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                "views": 3000,
                "likes": 150,
                "comments": 30,
                "duration": "PT5M",
            },
        ]
        with patch.object(self.mod, "_fetch_recent_videos", return_value=mock_videos):
            result = self.mod.get_youtube_channel_report()
        self.assertIn("Video 1", result)
        self.assertIn("5.000", result)

# =============================================================================
