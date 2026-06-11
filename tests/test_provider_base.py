from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class TestProviderBase(unittest.TestCase):
    """core.provider_base abstract interface testleri."""

    def test_module_import(self):
        """core.provider_base import edilebilmeli."""
        from core import provider_base
        self.assertIsNotNone(provider_base)

    def test_base_provider_class(self):
        """BaseProvider sinifi mevcut ve ABC'den turemis."""
        from core.provider_base import BaseProvider
        from abc import ABC
        self.assertTrue(issubclass(BaseProvider, ABC))

    def _make_concrete(self):
        """Helper: returns a concrete BaseProvider subclass instance."""
        from core.provider_base import BaseProvider
        class _TestProvider(BaseProvider):
            async def stop(self): pass
            async def send_text(self, text): pass
            async def run_loop(self): pass
            @property
            def name(self): return "test"
        return _TestProvider()

    def test_base_provider_init(self):
        """BaseProvider __init__ jarvis=None ile baslatir."""
        from core.provider_base import BaseProvider
        bp = self._make_concrete()
        self.assertIsNone(bp.jarvis)
        self.assertIsNone(bp._loop)

    def test_supports_streaming_audio_default(self):
        """supports_streaming_audio varsayilan False."""
        from core.provider_base import BaseProvider
        bp = self._make_concrete()
        self.assertFalse(bp.supports_streaming_audio)

    def test_supports_tool_calls_default(self):
        """supports_tool_calls varsayilan False."""
        from core.provider_base import BaseProvider
        bp = self._make_concrete()
        self.assertFalse(bp.supports_tool_calls)

    def test_send_audio_default_noop(self):
        """send_audio varsayilan no-op, hata firlatmaz."""
        from core.provider_base import BaseProvider
        bp = self._make_concrete()
        result = asyncio.run(bp.send_audio(b"test_data"))
        self.assertIsNone(result)

    def test_concrete_subclass_can_implement(self):
        """BaseProvider'dan tureyen sinif abstract metodlari implement edebilmeli."""
        from core.provider_base import BaseProvider

        class TestProvider(BaseProvider):
            async def stop(self):
                pass
            async def send_text(self, text):
                pass
            async def run_loop(self):
                pass
            @property
            def name(self):
                return "test"

        tp = TestProvider()
        self.assertEqual(tp.name, "test")
        self.assertFalse(tp.supports_streaming_audio)
        self.assertFalse(tp.supports_tool_calls)

    def test_j_helper_raises_before_start(self):
        """_j() jarvis None iken RuntimeError firlatmali."""
        from core.provider_base import BaseProvider

        class TestProvider(BaseProvider):
            async def stop(self):
                pass
            async def send_text(self, text):
                pass
            async def run_loop(self):
                pass
            @property
            def name(self):
                return "test"

        tp = TestProvider()
        with self.assertRaises(RuntimeError):
            tp._j()

    def test_j_helper_after_start(self):
        """_j() jarvis set edilmis ise jarvis'i dondurmeli."""
        from core.provider_base import BaseProvider

        class TestProvider(BaseProvider):
            async def stop(self):
                pass
            async def send_text(self, text):
                pass
            async def run_loop(self):
                pass
            @property
            def name(self):
                return "test"

        tp = TestProvider()
        tp.jarvis = "test_jarvis"
        self.assertEqual(tp._j(), "test_jarvis")

    def test_concrete_subclass_must_implement_abstract(self):
        """Abstract metodlari implement etmeyen sinif instantiate edilememeli."""
        from core.provider_base import BaseProvider

        class IncompleteProvider(BaseProvider):
            pass

        with self.assertRaises(TypeError):
            IncompleteProvider()


if __name__ == "__main__":
    unittest.main(verbosity=2)
