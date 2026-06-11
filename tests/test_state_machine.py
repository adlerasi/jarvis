from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestStateMachineTransitions(unittest.TestCase):
    """JarvisLive.set_state() gecerli/gecersiz gecis testleri — mock yok, gercek dict."""

    def setUp(self):
        from main import JarvisLive
        self.transitions = JarvisLive._VALID_TRANSITIONS

    # ── Gecerli gecisler ────────────────────────────────────

    def test_listening_to_thinking(self):
        """LISTENING -> THINKING gecerli."""
        self.assertIn("THINKING", self.transitions["LISTENING"])

    def test_listening_to_error(self):
        """LISTENING -> ERROR gecerli."""
        self.assertIn("ERROR", self.transitions["LISTENING"])

    def test_listening_to_paused(self):
        """LISTENING -> PAUSED gecerli."""
        self.assertIn("PAUSED", self.transitions["LISTENING"])

    def test_thinking_to_listening(self):
        """THINKING -> LISTENING gecerli."""
        self.assertIn("LISTENING", self.transitions["THINKING"])

    def test_thinking_to_speaking(self):
        """THINKING -> SPEAKING gecerli."""
        self.assertIn("SPEAKING", self.transitions["THINKING"])

    def test_thinking_to_error(self):
        """THINKING -> ERROR gecerli."""
        self.assertIn("ERROR", self.transitions["THINKING"])

    def test_thinking_to_paused(self):
        """THINKING -> PAUSED gecerli."""
        self.assertIn("PAUSED", self.transitions["THINKING"])

    def test_speaking_to_listening(self):
        """SPEAKING -> LISTENING gecerli (konusma bitti, dinle)."""
        self.assertIn("LISTENING", self.transitions["SPEAKING"])

    def test_speaking_to_thinking(self):
        """SPEAKING -> THINKING gecerli (araya girme -> dusun)."""
        self.assertIn("THINKING", self.transitions["SPEAKING"])

    def test_speaking_to_error(self):
        """SPEAKING -> ERROR gecerli."""
        self.assertIn("ERROR", self.transitions["SPEAKING"])

    def test_speaking_to_paused(self):
        """SPEAKING -> PAUSED gecerli."""
        self.assertIn("PAUSED", self.transitions["SPEAKING"])

    def test_error_to_listening(self):
        """ERROR -> LISTENING gecerli (hatadan kurtarma)."""
        self.assertIn("LISTENING", self.transitions["ERROR"])

    def test_error_to_thinking(self):
        """ERROR -> THINKING gecerli."""
        self.assertIn("THINKING", self.transitions["ERROR"])

    def test_error_to_paused(self):
        """ERROR -> PAUSED gecerli."""
        self.assertIn("PAUSED", self.transitions["ERROR"])

    def test_paused_to_listening(self):
        """PAUSED -> LISTENING gecerli."""
        self.assertIn("LISTENING", self.transitions["PAUSED"])

    def test_paused_to_thinking(self):
        """PAUSED -> THINKING gecerli."""
        self.assertIn("THINKING", self.transitions["PAUSED"])

    def test_paused_to_error(self):
        """PAUSED -> ERROR gecerli."""
        self.assertIn("ERROR", self.transitions["PAUSED"])

    # ── Gecersiz gecisler ───────────────────────────────────

    def test_listening_to_speaking_invalid(self):
        """LISTENING -> SPEAKING gecersiz (once THINKING lazim)."""
        self.assertNotIn("SPEAKING", self.transitions["LISTENING"])

    def test_listening_to_listening_invalid(self):
        """LISTENING -> LISTENING gecersiz (ayni durum)."""
        self.assertNotIn("LISTENING", self.transitions["LISTENING"])

    def test_thinking_to_thinking_invalid(self):
        """THINKING -> THINKING gecersiz (ayni durum)."""
        self.assertNotIn("THINKING", self.transitions["THINKING"])

    def test_speaking_to_speaking_invalid(self):
        """SPEAKING -> SPEAKING gecersiz (ayni durum)."""
        self.assertNotIn("SPEAKING", self.transitions["SPEAKING"])

    def test_error_to_speaking_invalid(self):
        """ERROR -> SPEAKING gecersiz (hata -> konusma)."""
        self.assertNotIn("SPEAKING", self.transitions["ERROR"])

    def test_error_to_error_invalid(self):
        """ERROR -> ERROR gecersiz (ayni durum)."""
        self.assertNotIn("ERROR", self.transitions["ERROR"])

    def test_paused_to_speaking_invalid(self):
        """PAUSED -> SPEAKING gecersiz."""
        self.assertNotIn("SPEAKING", self.transitions["PAUSED"])

    def test_paused_to_paused_invalid(self):
        """PAUSED -> PAUSED gecersiz (ayni durum)."""
        self.assertNotIn("PAUSED", self.transitions["PAUSED"])

    # ── Tum durumlarin kumesi ───────────────────────────────

    def test_all_states_covered(self):
        """5 durumun tamami _VALID_TRANSITIONS'da tanimli."""
        expected = {"LISTENING", "THINKING", "SPEAKING", "ERROR", "PAUSED"}
        self.assertEqual(set(self.transitions.keys()), expected)

    def test_each_state_has_transitions(self):
        """Her durum en az 2 gecerli gecise sahip (kendisi haric)."""
        for state, allowed in self.transitions.items():
            self.assertGreaterEqual(len(allowed), 2,
                f"{state} sadece {len(allowed)} gecise sahip")


class TestStateMachineDeduplication(unittest.TestCase):
    """set_state ayni durumu iki kez cagrildiginda atlama testi."""

    def test_transition_dict_allows_no_self_loops(self):
        """Hicbir durum kendine gecise izin vermez."""
        from main import JarvisLive
        transitions = JarvisLive._VALID_TRANSITIONS
        for state in transitions:
            self.assertNotIn(state, transitions[state],
                f"{state} kendine gecis iceriyor")


class TestValidTransitionsCount(unittest.TestCase):
    """Gecerli gecis sayisi kontrol."""

    def test_listening_has_three_transitions(self):
        """LISTENING: THINKING, ERROR, PAUSED."""
        from main import JarvisLive
        self.assertEqual(JarvisLive._VALID_TRANSITIONS["LISTENING"],
                         {"THINKING", "ERROR", "PAUSED"})

    def test_thinking_has_four_transitions(self):
        """THINKING: LISTENING, SPEAKING, ERROR, PAUSED."""
        from main import JarvisLive
        self.assertEqual(JarvisLive._VALID_TRANSITIONS["THINKING"],
                         {"LISTENING", "SPEAKING", "ERROR", "PAUSED"})

    def test_speaking_has_four_transitions(self):
        """SPEAKING: LISTENING, THINKING, ERROR, PAUSED."""
        from main import JarvisLive
        self.assertEqual(JarvisLive._VALID_TRANSITIONS["SPEAKING"],
                         {"LISTENING", "THINKING", "ERROR", "PAUSED"})

    def test_error_has_three_transitions(self):
        """ERROR: LISTENING, THINKING, PAUSED."""
        from main import JarvisLive
        self.assertEqual(JarvisLive._VALID_TRANSITIONS["ERROR"],
                         {"LISTENING", "THINKING", "PAUSED"})

    def test_paused_has_three_transitions(self):
        """PAUSED: LISTENING, THINKING, ERROR."""
        from main import JarvisLive
        self.assertEqual(JarvisLive._VALID_TRANSITIONS["PAUSED"],
                         {"LISTENING", "THINKING", "ERROR"})
