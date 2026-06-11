from __future__ import annotations

import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestUiSafeCall(unittest.TestCase):
    """ui.safe_call fonksiyonu thread-safe calistirma testi."""

    def setUp(self):
        from ui import JarvisUI
        self.UI = JarvisUI

    def test_set_state_updates_jarvis_state(self):
        """set_state('THINKING') _jarvis_state='THINKING' yapmali."""
        from ui import JarvisUI
        ui = JarvisUI.__new__(JarvisUI)
        ui._jarvis_state = ""
        ui._orb = None
        ui.speaking = False
        ui.sound = type("FakeSound", (), {
            "start_thinking": lambda self: None,
            "stop_thinking": lambda self: None,
            "play_error": lambda self: None,
        })()
        ui.set_state("THINKING")
        self.assertEqual(ui._jarvis_state, "THINKING")

    def test_set_state_speaking_flag(self):
        """set_state('SPEAKING') speaking=True yapmali."""
        from ui import JarvisUI
        ui = JarvisUI.__new__(JarvisUI)
        ui._jarvis_state = "THINKING"
        ui._orb = None
        ui.speaking = False
        ui.sound = type("FakeSound", (), {
            "start_thinking": lambda self: None,
            "stop_thinking": lambda self: None,
            "play_error": lambda self: None,
        })()
        ui.set_state("SPEAKING")
        self.assertTrue(ui.speaking)

    def test_set_state_listening_clears_speaking(self):
        """set_state('LISTENING') speaking=False yapmali."""
        from ui import JarvisUI
        ui = JarvisUI.__new__(JarvisUI)
        ui._jarvis_state = "SPEAKING"
        ui._orb = None
        ui.speaking = True
        ui.sound = type("FakeSound", (), {
            "start_thinking": lambda self: None,
            "stop_thinking": lambda self: None,
            "play_error": lambda self: None,
        })()
        ui.set_state("LISTENING")
        self.assertFalse(ui.speaking)

    def test_safe_call_executes_function(self):
        """safe_call verilen fonksiyonu calistirmali."""
        from ui import JarvisUI
        ui = JarvisUI.__new__(JarvisUI)
        results = []
        ui.safe_call(lambda: results.append("called"))
        self.assertEqual(results, ["called"])

    def test_safe_call_passes_args(self):
        """safe_call argumanlari fonksiyona iletmeli."""
        from ui import JarvisUI
        ui = JarvisUI.__new__(JarvisUI)
        results = []
        ui.safe_call(lambda x: results.append(x), 42)
        self.assertEqual(results, [42])


class TestJarvisLiveStateDelegation(unittest.TestCase):
    """JarvisLive.set_state() UI'ye dogru delegasyon yapiyor mu."""

    def test_set_state_delegates_to_ui(self):
        """set_state UI'nin set_state pulic ini cagirmali (safe_call uzerinden)."""
        from main import JarvisLive

        class RecordingUI:
            def __init__(self):
                self._jarvis_state = ""
                self.states = []
                self.sound = type("FakeSound", (), {
                    "start_thinking": lambda self: None,
                    "stop_thinking": lambda self: None,
                    "play_error": lambda self: None,
                })()
            def safe_call(self, fn, *args):
                fn(*args)
            def set_state(self, state):
                self._jarvis_state = state
                self.states.append(state)

        ui = RecordingUI()
        j = JarvisLive.__new__(JarvisLive)
        j.ui = ui
        j._VALID_TRANSITIONS = JarvisLive._VALID_TRANSITIONS

        j.set_state("THINKING")
        self.assertIn("THINKING", ui.states)

    def test_set_state_skips_duplicate(self):
        """Ayni state iki kez cagrilirsa UI'ye sadece bir kez gider."""
        from main import JarvisLive

        class RecordingUI:
            def __init__(self):
                self._jarvis_state = ""
                self.states = []
                self.sound = type("FakeSound", (), {
                    "start_thinking": lambda self: None,
                    "stop_thinking": lambda self: None,
                    "play_error": lambda self: None,
                })()
            def safe_call(self, fn, *args):
                fn(*args)
            def set_state(self, state):
                self._jarvis_state = state
                self.states.append(state)

        ui = RecordingUI()
        j = JarvisLive.__new__(JarvisLive)
        j.ui = ui
        j._VALID_TRANSITIONS = JarvisLive._VALID_TRANSITIONS

        j.set_state("THINKING")
        j.set_state("THINKING")  # duplicate
        self.assertEqual(len(ui.states), 1)


class TestStateFlowConsistency(unittest.TestCase):
    """LISTENING -> THINKING -> SPEAKING -> LISTENING akisi dogru calisiyor."""

    def test_full_conversation_cycle(self):
        """Normal konusma akisi: L -> T -> S -> L."""
        from main import JarvisLive
        trans = JarvisLive._VALID_TRANSITIONS

        current = "LISTENING"
        self.assertIn("THINKING", trans[current])
        current = "THINKING"
        self.assertIn("SPEAKING", trans[current])
        current = "SPEAKING"
        self.assertIn("LISTENING", trans[current])

    def test_barge_in_flow(self):
        """Araya girme: S -> T -> S -> L."""
        from main import JarvisLive
        trans = JarvisLive._VALID_TRANSITIONS

        current = "SPEAKING"
        self.assertIn("THINKING", trans[current])
        current = "THINKING"
        self.assertIn("SPEAKING", trans[current])
        current = "SPEAKING"
        self.assertIn("LISTENING", trans[current])

    def test_error_recovery_flow(self):
        """Hata kurtarma: T -> E -> L."""
        from main import JarvisLive
        trans = JarvisLive._VALID_TRANSITIONS

        current = "THINKING"
        self.assertIn("ERROR", trans[current])
        current = "ERROR"
        self.assertIn("LISTENING", trans[current])
