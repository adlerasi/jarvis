from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class TestGreetingSkill(unittest.TestCase):
    """greeting_skill pure function tests -- no action imports, no mocks needed."""

    def setUp(self):
        from skills.greeting.greeting_skill import route_greeting_request
        self.route = route_greeting_request

    def test_route_merhaba(self):
        result = self.route("merhaba")
        self.assertIsNotNone(result)
        self.assertIn("Sistem calisiyor", result)

    def test_route_selam(self):
        result = self.route("selam")
        self.assertIsNotNone(result)

    def test_route_naber(self):
        result = self.route("naber")
        self.assertIsNotNone(result)

    def test_route_nasilsin(self):
        result = self.route("nasılsın")
        self.assertIsNotNone(result)

    def test_route_nasilsin_ascii_fallback(self):
        result = self.route("nasilsin")
        self.assertIsNotNone(result)

    def test_route_calisiyor_mu(self):
        result = self.route("çalışıyor musun")
        self.assertIsNotNone(result)

    def test_route_hello(self):
        result = self.route("hello")
        self.assertIsNotNone(result)

    def test_route_jarvis_kimsin(self):
        result = self.route("jarvis kimsin")
        self.assertIsNotNone(result)

    def test_route_hot_reload_nedir(self):
        result = self.route("hot-reload nedir")
        self.assertIsNotNone(result)

    def test_route_no_match(self):
        result = self.route("bugün hava çok güzel")
        self.assertIsNone(result)

    def test_route_empty_string(self):
        result = self.route("")
        self.assertIsNone(result)

    def test_route_no_match(self):
        # "kaç skill var" has kaç before skill — patterns expect skill.*?kaç
        result = self.route("kaç skill var")
        self.assertIsNone(result)

    def test_route_sistem_kontrol(self):
        result = self.route("sistem kontrol dene")
        self.assertIsNotNone(result)