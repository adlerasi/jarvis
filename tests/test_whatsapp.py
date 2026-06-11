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


class TestWhatsApp(unittest.TestCase):
    """whatsapp modulu — pure fonksiyon + validation testleri."""

    def setUp(self):
        from actions import whatsapp
        self.mod = whatsapp

    def test_normalize_phone_valid(self):
        """_normalize_phone gecerli numarayi 90 ile dondurur."""
        result = self.mod._normalize_phone("+905551112233")
        self.assertEqual(result, "905551112233")

    def test_normalize_phone_with_0(self):
        """_normalize_phone 0 ile baslayani 90+... yapar."""
        result = self.mod._normalize_phone("05551112233")
        self.assertEqual(result, "905551112233")

    def test_normalize_phone_10_digits(self):
        """_normalize_phone 10 haneli numaraya 90 ekler."""
        result = self.mod._normalize_phone("5551112233")
        self.assertEqual(result, "905551112233")

    def test_normalize_phone_too_short(self):
        """_normalize_phone cok kisa numarada ValueError."""
        with self.assertRaises(ValueError):
            self.mod._normalize_phone("123")

    def test_normalize_phone_too_long(self):
        """_normalize_phone cok uzun numarada ValueError."""
        with self.assertRaises(ValueError):
            self.mod._normalize_phone("1234567890123456")

    def test_normalize_phone_strips_non_digits(self):
        """_normalize_phone rakam disi karakterleri temizler."""
        result = self.mod._normalize_phone("+90 (555) 111-22-33")
        self.assertEqual(result, "905551112233")

    def test_normalize_lookup(self):
        """_normalize_lookup Turkce karakterleri normalize eder."""
        result = self.mod._normalize_lookup("İstanbul Şöför")
        self.assertNotIn("İ", result)
        self.assertNotIn("ş", result)
        self.assertNotIn("ö", result)

    def test_normalize_lookup_spaces(self):
        """_normalize_lookup fazla bosluklari teke indirir."""
        result = self.mod._normalize_lookup("  Ali   Veli  ")
        self.assertEqual(result, "ali veli")

    def test_normalize_lookup_empty(self):
        """_normalize_lookup bos string calisir."""
        self.assertEqual(self.mod._normalize_lookup(""), "")
        self.assertEqual(self.mod._normalize_lookup(None), "")

    def test_contact_key(self):
        """_contact_key ismi altcizgili anahtara cevirir."""
        result = self.mod._contact_key("Ali Veli")
        self.assertEqual(result, "ali_veli")

    def test_contact_key_turkce(self):
        """_contact_key Turkce karakterleri handle eder."""
        result = self.mod._contact_key("Şükran İnan")
        self.assertNotIn("ş", result)
        self.assertNotIn("ı", result)
        self.assertIn("inan", result)

    def test_find_contact_empty(self):
        """_find_contact bos sorguda None doner."""
        self.assertIsNone(self.mod._find_contact(""))
        self.assertIsNone(self.mod._find_contact(None))

    def test_unfold_vcf_lines(self):
        """_unfold_vcf_lines VCF satirlarini birlestirir."""
        lines = ["BEGIN:VCARD", "FN:Test", "  Kisisi", "TEL:123", "END:VCARD"]
        result = self.mod._unfold_vcf_lines("\n".join(lines))
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1], "FN:Test Kisisi")

    def test_unfold_vcf_lines_no_fold(self):
        """_unfold_vcf_lines katlanmamis VCF'de satirlar aynen kalir."""
        lines = ["BEGIN:VCARD", "FN:Test", "END:VCARD"]
        result = self.mod._unfold_vcf_lines("\n".join(lines))
        self.assertEqual(result, lines)

    def test_save_contact_empty_name(self):
        """save_whatsapp_contact bos isimle hata doner."""
        result = self.mod.save_whatsapp_contact("", "+905551112233")
        self.assertIn("bos olamaz", result)

    def test_save_contact_invalid_phone(self):
        """save_whatsapp_contact gecersiz telefonla hata doner."""
        result = self.mod.save_whatsapp_contact("Ali", "123")
        self.assertIn("formatta", result)

    def test_import_vcf_no_file(self):
        """import_phone_book_from_vcf olmayan dosyada hata doner."""
        result = self.mod.import_phone_book_from_vcf("/nonexistent/file.vcf")
        self.assertIn("bulunamadi", result)

    def test_send_whatsapp_empty_message(self):
        """send_whatsapp_message bos mesajla hata doner."""
        result = self.mod.send_whatsapp_message("")
        self.assertIn("bos olamaz", result)

    def test_send_whatsapp_no_recipient(self):
        """send_whatsapp_message adres yoksa hata doner."""
        result = self.mod.send_whatsapp_message("Selam", phone_number="", recipient_name="")
        self.assertIn("gerekli", result)

    def test_send_whatsapp_invalid_phone(self):
        """send_whatsapp_message gecersiz numarayla hata doner."""
        result = self.mod.send_whatsapp_message("Selam", phone_number="123")
        self.assertIn("formatta", result)


# =============================================================================
# 18. MEDIA — SAF FONKSIYON TESTLERI
# =============================================================================
