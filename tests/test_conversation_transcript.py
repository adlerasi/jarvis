from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch


class TestConversationTranscript(unittest.TestCase):
    """memory.conversation_transcript saf fonksiyon testleri."""

    def test_module_import(self):
        """memory.conversation_transcript import edilebilmeli."""
        from memory import conversation_transcript
        self.assertIsNotNone(conversation_transcript)

    def test_init_defaults(self):
        """ConversationTranscript varsayilan parametrelerle baslatilir."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        self.assertEqual(ct.max_turns, 50)
        self.assertEqual(ct.turn_count, 0)
        self.assertEqual(len(ct._turns), 0)
        self.assertFalse(ct.auto_save)

    def test_init_custom(self):
        """ConversationTranscript ozel parametrelerle baslatilir."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(max_turns=10, auto_save=False)
        self.assertEqual(ct.max_turns, 10)

    def test_add_turn_increases_count(self):
        """add_turn sonrasi turn_count artar."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("merhaba", "merhaba nasil yardimci olabilirim")
        self.assertEqual(ct.turn_count, 1)
        self.assertEqual(len(ct._turns), 1)

    def test_add_turn_stores_data(self):
        """add_turn kullanici ve jarvis metinlerini saklar."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("naber", "iyiyim senden?", metadata={"test": True})
        turn = ct._turns[0]
        self.assertEqual(turn["user"]["text"], "naber")
        self.assertEqual(turn["jarvis"]["text"], "iyiyim senden?")
        self.assertTrue(turn["metadata"]["test"])

    def test_get_recent(self):
        """get_recent son N turn'u doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        for i in range(10):
            ct.add_turn(f"user{i}", f"jarvis{i}")
        recent = ct.get_recent(3)
        self.assertEqual(len(recent), 3)
        self.assertEqual(recent[-1]["user"]["text"], "user9")

    def test_get_recent_all(self):
        """get_recent n>turn_count ise tumunu doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("a", "b")
        recent = ct.get_recent(100)
        self.assertEqual(len(recent), 1)

    def test_get_formatted_empty(self):
        """get_formatted bos transcript icin bos string doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        self.assertEqual(ct.get_formatted(), "")

    def test_get_formatted_content(self):
        """get_formatted dogru formatta string doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("merhaba", "merhaba")
        ct.add_turn("hava nasil", "gunesli")
        formatted = ct.get_formatted()
        self.assertIn("[SON KONUSMALAR]", formatted)
        self.assertIn("Kullanici: hava nasil", formatted)
        self.assertIn("JARVIS: gunesli", formatted)

    def test_search_finds_match(self):
        """search eslesen turn'lari bulur."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("merhaba", "merhaba nasil yardim")
        ct.add_turn("hava soguk", "evet cok soguk")
        results = ct.search("soguk")
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("soguk", results[0]["user"]["text"].lower())

    def test_search_both_fields(self):
        """search kullanici ve jarvis metninde ara."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("hava yagmurlu", "yagmur yagiyor disarida")
        ct.add_turn("tesekkurler", "rica ederim")
        # "yagmur" both turn'in user'inda ve jarvis'inde var
        results = ct.search("yagmur")
        self.assertEqual(len(results), 1)

    def test_search_case_insensitive(self):
        """search buyuk/kucuk harf duyarsizdir."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("MERHABA", "Merhaba")
        results = ct.search("merhaba")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        """search eslesme yoksa bos liste doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("merhaba", "merhaba")
        results = ct.search("olmayan")
        self.assertEqual(results, [])

    def test_max_turns_enforced(self):
        """max_turns asiminda eski turn'lar silinir."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(max_turns=3, auto_save=False)
        for i in range(10):
            ct.add_turn(f"user{i}", f"jarvis{i}")
        self.assertEqual(len(ct._turns), 3)
        self.assertEqual(ct._turns[0]["user"]["text"], "user7")

    def test_clear_resets_state(self):
        """clear tum turn'lari ve sayaci sifirlar."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("a", "b")
        ct.clear()
        self.assertEqual(ct.turn_count, 0)
        self.assertEqual(len(ct._turns), 0)

    def test_new_session_clears(self):
        """new_session clear yapar (auto_save=False iken kaydetmez)."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("a", "b")
        ct.new_session()
        self.assertEqual(ct.turn_count, 0)

    def test_get_stats_structure(self):
        """get_stats dogru anahtarlara sahip dict doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("test", "yanit")
        stats = ct.get_stats()
        self.assertIn("session_id", stats)
        self.assertIn("total_turns", stats)
        self.assertIn("current_turns", stats)
        self.assertIn("max_turns", stats)
        self.assertEqual(stats["total_turns"], 1)
        self.assertEqual(stats["current_turns"], 1)

    def test_save_returns_path(self):
        """save turn varken dosya yolu dondurur."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        ct.add_turn("a", "b")
        with patch("builtins.open", unittest.mock.mock_open()):
            result = ct.save()
            self.assertIsNotNone(result)
            self.assertIn("transcript_", result)

    def test_save_no_turns_none(self):
        """save turn yokken None doner."""
        from memory.conversation_transcript import ConversationTranscript
        ct = ConversationTranscript(auto_save=False)
        result = ct.save()
        self.assertIsNone(result)

    def test_factory_creates_transcript(self):
        """create_transcript ConversationTranscript instance'i dondurur."""
        from memory.conversation_transcript import create_transcript, ConversationTranscript
        ct = create_transcript(auto_save=False)
        self.assertIsInstance(ct, ConversationTranscript)

    def test_module_exports(self):
        """__all__ dogru sembolleri export ediyor."""
        from memory.conversation_transcript import __all__
        self.assertIn("ConversationTranscript", __all__)
        self.assertIn("create_transcript", __all__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
