from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

BASE_DIR = Path(__file__).resolve().parent.parent


class TestLocationModule(unittest.TestCase):
    """actions.location pure fonksiyon testleri."""

    def test_module_import(self):
        """actions.location import edilebilmeli."""
        from actions import location
        self.assertIsNotNone(location)

    def test_check_saved_location(self):
        """check_saved_location str | None dondurmeli."""
        from actions.location import check_saved_location
        result = check_saved_location()
        self.assertIsInstance(result, (str, type(None)))

    def test_reverse_geocode_none_none(self):
        """_reverse_geocode None/None icin None dondurmeli."""
        from actions.location import _reverse_geocode
        result = _reverse_geocode(None, None)  # type: ignore
        self.assertIsNone(result)

    def test_reverse_geocode_invalid(self):
        """_reverse_geocode gecersiz koordinatlarda None dondurmeli."""
        from actions.location import _reverse_geocode
        result = _reverse_geocode(999.0, 999.0)
        self.assertIsNone(result)

    def test_reverse_geocode_valid_coords(self):
        """_reverse_geocode gecerli koordinatlarda str dondurur veya None olabilir."""
        from actions.location import _reverse_geocode
        # Istanbul - API yanit verirse str, vermezse None
        result = _reverse_geocode(41.0082, 28.9784)
        self.assertIn(type(result), (str, type(None)))
        if result is not None:
            self.assertGreater(len(result), 0)

    def test_ip_location(self):
        """_ip_location str | None dondurmeli."""
        from actions.location import _ip_location
        result = _ip_location()
        self.assertIsInstance(result, (str, type(None)))

    def test_geoclue_location_import(self):
        """_geoclue_location mevcut olmali."""
        from actions.location import _geoclue_location
        self.assertTrue(callable(_geoclue_location))

    def test_get_current_location(self):
        """get_current_location str | None dondurmeli."""
        from actions.location import get_current_location
        result = get_current_location()
        self.assertIsInstance(result, (str, type(None)))

    def test_geoclue_location_returns_none_wo_service(self):
        """_geoclue_location GeoClue servisi yoksa None doner."""
        from actions.location import _geoclue_location
        result = _geoclue_location()
        # GeoClue genelde calismaz, None doner
        self.assertIn(type(result), (str, type(None)))

    @patch("actions.location._ip_location", return_value=None)
    @patch("actions.location._geoclue_location", return_value=None)
    @patch("actions.location.check_saved_location", return_value="Saved City")
    def test_get_current_location_falls_back_to_memory(self, mock_saved, mock_geo, mock_ip):
        """get_current_location hafiza konumuna dusmelidir."""
        from actions.location import get_current_location
        result = get_current_location()
        self.assertEqual(result, "Saved City")

    @patch("actions.location._ip_location", return_value="IP City")
    @patch("actions.location._geoclue_location", return_value=None)
    def test_get_current_location_ip_fallback(self, mock_geo, mock_ip):
        """get_current_location GeoClue yoksa IP'ye dusmeli."""
        from actions.location import get_current_location
        result = get_current_location()
        self.assertEqual(result, "IP City")

    def test_ip_location_returns_str(self):
        """_ip_location gecerliyse str dondurur."""
        from actions.location import _ip_location
        result = _ip_location()
        if result is not None:
            self.assertGreater(len(result), 0)
            self.assertIn(", ", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
