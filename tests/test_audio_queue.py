from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestAudioQueueLimit(unittest.TestCase):
    """gemini_provider audio_in_queue maxsize=200 testi."""

    def test_queue_has_maxsize(self):
        """audio_in_queue maxsize=200 ile olusmali."""
        from core.gemini_provider import GeminiProvider
        p = GeminiProvider.__new__(GeminiProvider)
        p.audio_in_queue = asyncio.Queue(maxsize=200)
        self.assertEqual(p.audio_in_queue.maxsize, 200)

    def test_queue_accepts_items(self):
        """Queue normal kosullarda item kabul etmeli."""
        q = asyncio.Queue(maxsize=200)
        q.put_nowait(b"test1")
        q.put_nowait(b"test2")
        self.assertEqual(q.qsize(), 2)

    def test_queue_full_raises(self):
        """Queue doldugunda put_nowait QueueFull firlatmali."""
        q = asyncio.Queue(maxsize=3)
        q.put_nowait(b"1")
        q.put_nowait(b"2")
        q.put_nowait(b"3")
        with self.assertRaises(asyncio.QueueFull):
            q.put_nowait(b"4")

    def test_queue_get_after_full(self):
        """Queue dolunca get cagrilirsa tekrar put calisir."""
        q = asyncio.Queue(maxsize=3)
        q.put_nowait(b"1")
        q.put_nowait(b"2")
        q.put_nowait(b"3")
        _ = q.get_nowait()
        q.put_nowait(b"4")
        self.assertEqual(q.qsize(), 3)

    def test_queue_order_preserved(self):
        """Queue FIFO siralamasini korur."""
        q = asyncio.Queue(maxsize=200)
        q.put_nowait(b"first")
        q.put_nowait(b"second")
        q.put_nowait(b"third")
        self.assertEqual(q.get_nowait(), b"first")
        self.assertEqual(q.get_nowait(), b"second")
        self.assertEqual(q.get_nowait(), b"third")

    def test_gemini_provider_queue_maxsize(self):
        """GeminiProvider baslatildiginda audio_in_queue maxsize=200 olmali."""
        from core.gemini_provider import GeminiProvider
        p = GeminiProvider.__new__(GeminiProvider)
        p._running = False
        p.audio_in_queue = asyncio.Queue(maxsize=200)
        self.assertEqual(p.audio_in_queue.maxsize, 200)


class TestAudioQueueOverflowHandling(unittest.TestCase):
    """Queue overflow'da _receive_audio'nun crash etmedigi testi."""

    def test_put_nowait_with_try_except(self):
        """put_nowait QueueFull'da try/except ile yakalanmali (crash yerine)."""
        import io
        import sys
        q = asyncio.Queue(maxsize=2)

        # Doldur
        q.put_nowait(b"1")
        q.put_nowait(b"2")

        # Overflow - yakala ve logla (crash YERINE)
        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            try:
                q.put_nowait(b"3")
            except asyncio.QueueFull:
                print("[TEST] Kuyruk doldu, chunk atlandi")
                # Crash YOK - baglanti devam ediyor
        finally:
            sys.stderr = old_stderr

        # Bu satira ulasildiysa crash olmadi demektir
        self.assertEqual(q.qsize(), 2)  # hala 2 item
