from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch


class TestProactiveVoice(unittest.TestCase):
    """core.proactive_voice state ve queue testleri."""

    def test_module_import(self):
        """core.proactive_voice import edilebilmeli."""
        from core import proactive_voice
        self.assertIsNotNone(proactive_voice)

    def test_init_defaults(self):
        """ProactiveVoice varsayilan degerlerle baslatilir."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        self.assertEqual(pv.voice, "piper-fahrettin")
        self.assertFalse(pv._running)
        self.assertFalse(pv._user_active)
        self.assertIsNone(pv._last_greeting_date)
        self.assertIsNone(pv._thread)
        self.assertTrue(pv._queue.empty())

    def test_init_custom(self):
        """ProactiveVoice ozel parametrelerle baslatilir."""
        from core.proactive_voice import ProactiveVoice
        cb = lambda msg: None
        pv = ProactiveVoice(voice="custom-voice", on_speak=cb)
        self.assertEqual(pv.voice, "custom-voice")
        self.assertIs(pv.on_speak, cb)

    def test_is_running_property(self):
        """is_running property dogru deger doner."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        self.assertFalse(pv.is_running)

    def test_start_sets_running(self):
        """start _running=True yapar ve thread baslatir."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.start()
        self.assertTrue(pv._running)
        self.assertIsNotNone(pv._thread)
        self.assertTrue(pv._thread.is_alive())
        pv.stop()

    def test_start_idempotent(self):
        """start ikinci kez cagrildiginda yeni thread baslatmaz."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.start()
        thread_id = id(pv._thread)
        pv.start()
        self.assertEqual(id(pv._thread), thread_id)
        pv.stop()

    def test_stop_cleans_up(self):
        """stop thread'i durdurur ve _running=False yapar."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.start()
        pv.stop()
        self.assertFalse(pv._running)
        self.assertIsNone(pv._thread)

    def test_set_user_active(self):
        """set_user_active state gunceller."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.set_user_active(True)
        self.assertTrue(pv._user_active)
        pv.set_user_active(False)
        self.assertFalse(pv._user_active)

    def test_queue_message_when_user_inactive(self):
        """_queue_message user aktif degilken kuyruga ekler."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv._queue_message("Test mesaji")
        self.assertEqual(pv._queue.qsize(), 1)
        self.assertEqual(pv._queue.get(), "Test mesaji")

    def test_queue_message_when_user_active(self):
        """_queue_message user aktifken kuyruga EKLEMEZ."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.set_user_active(True)
        pv._queue_message("Test mesaji")
        self.assertTrue(pv._queue.empty())

    def test_on_user_activated_first_time(self):
        """on_user_activated ilk kez cagrildiginda greeting kuyruga eklenir."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_user_activated()
        self.assertIsNotNone(pv._last_greeting_date)
        self.assertEqual(pv._queue.qsize(), 1)
        msg = pv._queue.get_nowait()
        self.assertIn(msg, [
            "Merhaba! Nasilsiniz?",
            "Merhaba, size nasil yardimci olabilirim?",
            "Hosgeldiniz!",
            "Gunaydin! Bugun size nasil yardimci olabilirim?",
        ])

    def test_on_user_activated_same_day(self):
        """on_user_activated ayni gun ikinci kez greeting eklemez."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_user_activated()
        first_size = pv._queue.qsize()
        pv.on_user_activated()
        self.assertEqual(pv._queue.qsize(), first_size)

    def test_on_reminder_adds_to_queue(self):
        """on_reminder kuyruga hatirlatici mesaji ekler."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_reminder("Doktor randevusu")
        self.assertEqual(pv._queue.qsize(), 1)
        self.assertIn("Doktor randevusu", pv._queue.get())

    def test_on_custom_adds_to_queue(self):
        """on_custom kuyruga ozel mesaj ekler."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_custom("Ozel bildirim")
        self.assertEqual(pv._queue.qsize(), 1)
        self.assertEqual(pv._queue.get(), "Ozel bildirim")

    def test_on_idle_short_duration(self):
        """on_idle 120s altinda mesaj EKLEMEZ."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_idle(30)
        self.assertTrue(pv._queue.empty())

    def test_on_idle_long_duration(self):
        """on_idle 120s ustunde mesaj ekler."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        pv.on_idle(300)
        self.assertEqual(pv._queue.qsize(), 1)

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from core.proactive_voice import ProactiveVoice
        pv = ProactiveVoice()
        stats = pv.get_stats()
        self.assertIn("running", stats)
        self.assertIn("queue_size", stats)
        self.assertIn("voice", stats)
        self.assertIn("user_active", stats)
        self.assertFalse(stats["running"])
        self.assertEqual(stats["queue_size"], 0)
        self.assertEqual(stats["voice"], "piper-fahrettin")
        self.assertFalse(stats["user_active"])

    def test_speak_calls_on_speak_callback(self):
        """_speak on_speak callback'ini cagirir."""
        from core.proactive_voice import ProactiveVoice
        captured = []
        pv = ProactiveVoice(on_speak=lambda msg: captured.append(msg))
        pv._speak("Test konusma")
        self.assertEqual(captured, ["Test konusma"])

    def test_factory_creates_proactive_voice(self):
        """create_proactive_voice ProactiveVoice instance'i dondurur."""
        from core.proactive_voice import create_proactive_voice, ProactiveVoice
        pv = create_proactive_voice()
        self.assertIsInstance(pv, ProactiveVoice)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from core.proactive_voice import __all__
        self.assertIn("ProactiveVoice", __all__)
        self.assertIn("create_proactive_voice", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
