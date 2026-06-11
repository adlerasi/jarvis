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


class TestCalendar(unittest.TestCase):
    """calendar modulu — pure fonksiyon + validation testleri."""

    def setUp(self):
        from actions import calendar
        self.mod = calendar

    def test_load_events_no_file(self):
        """_load_events dosya yokken liste doner."""
        result = self.mod._load_events()
        self.assertIsInstance(result, list)

    def test_parse_iso_valid(self):
        """_parse_iso gecerli ISO cozer."""
        from datetime import datetime
        result = self.mod._parse_iso("2024-03-15T14:30:00")
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 15)
        self.assertEqual(result.hour, 14)
        self.assertEqual(result.minute, 30)

    def test_parse_iso_z_suffix(self):
        """_parse_iso Z ekini cozer."""
        result = self.mod._parse_iso("2024-12-31T23:59:59Z")
        self.assertEqual(result.year, 2024)

    def test_parse_iso_empty_raises(self):
        """_parse_iso bos string ValueError firlatir."""
        with self.assertRaises(ValueError):
            self.mod._parse_iso("")

    def test_parse_iso_none_raises(self):
        """_parse_iso None ValueError firlatir."""
        with self.assertRaises(ValueError):
            self.mod._parse_iso(None)

    def test_to_event_valid(self):
        """_to_event gecerli dict'i event formatina cevirir."""
        event = self.mod._to_event({
            "id": "test-1",
            "title": "Toplanti",
            "start_iso": "2024-06-15T10:00:00",
            "end_iso": "2024-06-15T11:00:00",
        })
        assert event is not None
        self.assertEqual(event["title"], "Toplanti")
        self.assertEqual(event["id"], "test-1")
        self.assertFalse(event["all_day"])

    def test_to_event_missing_end(self):
        """_to_event bitis yoksa +1 saat ekler."""
        event = self.mod._to_event({
            "id": "t-1",
            "title": "Test",
            "start_iso": "2024-06-15T10:00:00",
        })
        assert event is not None
        self.assertEqual(event["end_ts"] - event["start_ts"], 3600)

    def test_to_event_bad_date_returns_none(self):
        """_to_event gecersiz tarihle None doner."""
        event = self.mod._to_event({"id": "x", "title": "X", "start_iso": "gecersiz"})
        self.assertIsNone(event)

    def test_to_event_empty_fields(self):
        """_to_event bos alanlari varsayilanla doldurur."""
        event = self.mod._to_event({"start_iso": "2024-06-15T10:00:00"})
        assert event is not None
        self.assertEqual(event["title"], "Adsiz etkinlik")
        self.assertEqual(event["location"], "")
        self.assertEqual(event["calendar"], "Windows Local")

    def test_month_start(self):
        """_month_start gunu 1'e cevirir, saatleri sifirlar."""
        from datetime import datetime
        result = self.mod._month_start(datetime(2024, 3, 15, 14, 30, 0))
        self.assertEqual(result.day, 1)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.year, 2024)

    def test_add_months_same_year(self):
        """_add_months ayni yil icinde ekleme yapar."""
        from datetime import datetime
        result = self.mod._add_months(datetime(2024, 1, 1), 3)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.year, 2024)

    def test_add_months_year_boundary(self):
        """_add_months yil sinirini gecer."""
        from datetime import datetime
        result = self.mod._add_months(datetime(2024, 10, 1), 5)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.year, 2025)

    def test_normalize_query_today(self):
        """_normalize_query bos/None sorguyu bugun olarak algilar."""
        result = self.mod._normalize_query("")
        self.assertEqual(result["kind"], "today")
        result2 = self.mod._normalize_query(None)
        self.assertEqual(result2["kind"], "today")

    def test_normalize_query_tomorrow(self):
        """_normalize_query 'yarin' algilar."""
        result = self.mod._normalize_query("yarin")
        self.assertEqual(result["kind"], "tomorrow")
        result = self.mod._normalize_query("tomorrow")
        self.assertEqual(result["kind"], "tomorrow")

    def test_normalize_query_week(self):
        """_normalize_query hafta algilar."""
        result = self.mod._normalize_query("bu hafta")
        self.assertEqual(result["kind"], "week")

    def test_normalize_query_next_month(self):
        """_normalize_query 'gelecek ay' algilar."""
        result = self.mod._normalize_query("gelecek ay")
        self.assertEqual(result["kind"], "next_month")

    def test_normalize_query_next(self):
        """_normalize_query 'siradaki' algilar."""
        result = self.mod._normalize_query("siradaki")
        self.assertEqual(result["kind"], "next")

    def test_normalize_query_agenda(self):
        """_normalize_query 'ajanda' algilar."""
        result = self.mod._normalize_query("ajanda")
        self.assertEqual(result["kind"], "agenda")

    def test_normalize_query_this_month(self):
        """_normalize_query 'bu ay' algilar."""
        result = self.mod._normalize_query("bu ay")
        self.assertEqual(result["kind"], "this_month")

    def test_normalize_query_n_days(self):
        """_normalize_query '5 gun' algilar."""
        result = self.mod._normalize_query("5 gun")
        self.assertEqual(result["kind"], "days")
        self.assertEqual(result["limit"], 10)  # 5 * 2

    def test_normalize_query_n_weeks(self):
        """_normalize_query '3 hafta' algilar."""
        result = self.mod._normalize_query("3 hafta")
        self.assertEqual(result["kind"], "weeks")

    def test_normalize_query_n_months(self):
        """_normalize_query '2 ay' algilar."""
        result = self.mod._normalize_query("2 ay")
        self.assertEqual(result["kind"], "months")

    def test_day_label_today(self):
        """_day_label bugun 'bugun' doner."""
        from datetime import datetime
        now = datetime(2024, 6, 15, 12, 0, 0)
        result = self.mod._day_label(now, now)
        self.assertEqual(result, "bugun")

    def test_day_label_tomorrow(self):
        """_day_label yarin 'yarin' doner."""
        from datetime import datetime, timedelta
        now = datetime(2024, 6, 15, 12, 0, 0)
        result = self.mod._day_label(now + timedelta(days=1), now)
        self.assertEqual(result, "yarin")

    def test_day_label_other(self):
        """_day_label diger gunler icin tarih doner."""
        from datetime import datetime
        now = datetime(2024, 6, 15, 12, 0, 0)
        future = datetime(2024, 6, 20, 0, 0, 0)
        result = self.mod._day_label(future, now)
        self.assertNotIn("bugun", result)
        self.assertNotIn("yarin", result)
        self.assertIn("20", result)

    def test_format_time_range_all_day(self):
        """_format_time_range tum gun etkinligini dogru formatlar."""
        from datetime import datetime
        event = {"start_ts": int(datetime(2024, 6, 15, 0, 0, 0).timestamp()),
                 "end_ts": int(datetime(2024, 6, 15, 23, 59, 59).timestamp()),
                 "all_day": True}
        result = self.mod._format_time_range(event, datetime(2024, 6, 15, 12, 0, 0))
        self.assertIn("tum gun", result)

    def test_format_event_line_with_calendar(self):
        """_format_event_line calendar bilgisini ekler."""
        from datetime import datetime
        event = {"start_ts": int(datetime(2024, 6, 15, 10, 0, 0).timestamp()),
                 "end_ts": int(datetime(2024, 6, 15, 11, 0, 0).timestamp()),
                 "all_day": False,
                 "title": "Test",
                 "calendar": "Is",
                 "location": ""}
        now = datetime(2024, 6, 15, 12, 0, 0)
        result = self.mod._format_event_line(event, now)
        self.assertIn("Test", result)
        self.assertIn("[Is]", result)

    def test_format_event_line_with_location(self):
        """_format_event_line konum bilgisini ekler."""
        from datetime import datetime
        event = {"start_ts": int(datetime(2024, 6, 15, 10, 0, 0).timestamp()),
                 "end_ts": int(datetime(2024, 6, 15, 11, 0, 0).timestamp()),
                 "all_day": False,
                 "title": "Toplanti",
                 "calendar": "",
                 "location": "Ofis"}
        result = self.mod._format_event_line(event, datetime(2024, 6, 15, 12, 0, 0))
        self.assertIn("Toplanti", result)
        self.assertIn("@ Ofis", result)

    def test_add_calendar_event_empty_title(self):
        """add_calendar_event bos baslikla hata doner."""
        result = self.mod.add_calendar_event("", "2024-06-15T10:00:00")
        self.assertIn("basligi gerekli", result)

    def test_add_calendar_event_empty_start(self):
        """add_calendar_event baslangic yoksa hata doner."""
        result = self.mod.add_calendar_event("Test", "")
        self.assertIn("tarihi gerekli", result)

    def test_add_calendar_event_bad_date(self):
        """add_calendar_event gecersiz tarihle hata doner."""
        result = self.mod.add_calendar_event("Test", "gecersiz")
        self.assertIn("tarih okunamadi", result)

    def test_delete_calendar_event_empty_title(self):
        """delete_calendar_event bos baslikla hata doner."""
        result = self.mod.delete_calendar_event("")
        self.assertIn("basligi gerekli", result)


# =============================================================================
# 14. REMINDERS — SAF FONKSIYON TESTLERI
# =============================================================================
