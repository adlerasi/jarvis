from __future__ import annotations

import unittest


class TestUITextUtils(unittest.TestCase):
    """ui.text_utils saf fonksiyon testleri."""

    def test_module_import(self):
        """ui.text_utils import edilebilmeli."""
        from ui import text_utils
        self.assertIsNotNone(text_utils)

    def test_split_summary_lines_empty(self):
        """_split_summary_lines bos string bos liste doner."""
        from ui.text_utils import _split_summary_lines
        self.assertEqual(_split_summary_lines(""), [])
        self.assertEqual(_split_summary_lines(None), [])
        self.assertEqual(_split_summary_lines("   "), [])

    def test_split_summary_lines_basic(self):
        """_split_summary_lines virgulle ayrilmis metni boler."""
        from ui.text_utils import _split_summary_lines
        result = _split_summary_lines("a, b, c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_split_summary_lines_with_ve(self):
        """_split_summary_lines ' ve ' virgule cevirir."""
        from ui.text_utils import _split_summary_lines
        result = _split_summary_lines("a ve b ve c")
        self.assertEqual(result, ["a", "b", "c"])

    def test_split_summary_lines_limit(self):
        """_split_summary_lines limit kadar ogeden fazlasini keser."""
        from ui.text_utils import _split_summary_lines
        result = _split_summary_lines("a, b, c, d, e, f", limit=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(result, ["a", "b", "c"])

    def test_parse_weather_card_empty(self):
        """_parse_weather_card bos metin varsayilan doner."""
        from ui.text_utils import _parse_weather_card
        result = _parse_weather_card("")
        self.assertEqual(result["city"], "Istanbul")
        self.assertEqual(result["primary"], "--")

    def test_parse_weather_card_alınamadı(self):
        """_parse_weather_card 'alinamadi' iceren metin varsayilan doner."""
        from ui.text_utils import _parse_weather_card
        result = _parse_weather_card("Hava durumu alınamadı")
        self.assertEqual(result["primary"], "--")

    def test_parse_weather_card_valid(self):
        """_parse_weather_card gecerli metni ayristirir."""
        from ui.text_utils import _parse_weather_card
        result = _parse_weather_card("Istanbul icin: 25 derece, Az bulutlu, Nem: %45")
        self.assertEqual(result["city"], "Istanbul")
        self.assertEqual(result["primary"], "25°C")
        self.assertIn("Az bulutlu", result["details"])

    def test_parse_weather_card_city_extraction(self):
        """_parse_weather_card sehir adini dogru cikarir."""
        from ui.text_utils import _parse_weather_card
        result = _parse_weather_card("Ankara için: 18 derece, Açık")
        self.assertEqual(result["city"], "Ankara")

    def test_parse_health_card_empty(self):
        """_parse_health_card bos metin varsayilan doner."""
        from ui.text_utils import _parse_health_card
        result = _parse_health_card("")
        self.assertEqual(result, ["Sağlık verisi alınamadı."])

    def test_parse_health_card_valid(self):
        """_parse_health_card gecerli metni ayristirir."""
        from ui.text_utils import _parse_health_card
        result = _parse_health_card("CPU: %25, RAM: %60, Disk: %45")
        self.assertIn("CPU: %25", result)

    def test_parse_health_card_limit(self):
        """_parse_health_card en fazla 4 satir doner."""
        from ui.text_utils import _parse_health_card
        result = _parse_health_card("a, b, c, d, e, f, g")
        self.assertLessEqual(len(result), 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
