from __future__ import annotations

import unittest
from unittest.mock import patch, MagicMock, PropertyMock


class MockTkRoot:
    """Minimal Tk root mock for SetupDialog tests."""
    def __init__(self):
        self.winfo_width = MagicMock(return_value=1600)
        self.winfo_height = MagicMock(return_value=900)


class MockJarvis:
    """Minimal JarvisUI mock for SetupDialog tests."""
    def __init__(self):
        self.root = MockTkRoot()
        self.W = 1600
        self._api_key_ready = False
        self._current_voice = "Charon"
        self.log_messages = []

    def write_log(self, msg: str):
        self.log_messages.append(msg)

    def set_state(self, state: str):
        self._state = state

    def _refresh_settings_status(self):
        pass


class TestSetupDialogInit(unittest.TestCase):
    """SetupDialog baslangic durumu testleri."""

    def test_constructor_stores_jarvis(self):
        from ui.setup_dialog import SetupDialog
        jarvis = MockJarvis()
        dlg = SetupDialog(jarvis)
        self.assertIs(dlg._jarvis, jarvis)

    def test_constructor_sets_widget_refs_to_none(self):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(MockJarvis())
        self.assertIsNone(dlg.frame)
        self.assertIsNone(dlg.api_entry)
        self.assertIsNone(dlg.youtube_api_entry)
        self.assertIsNone(dlg.youtube_handle_entry)
        self.assertIsNone(dlg.model_menu)
        self.assertIsNone(dlg.tts_menu)

    def test_constructor_sets_string_vars_to_none(self):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(MockJarvis())
        self.assertIsNone(dlg._backend_var)
        self.assertIsNone(dlg._ollama_model_var)
        self.assertIsNone(dlg._ollama_tts_var)

    def test_is_open_returns_false_initially(self):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(MockJarvis())
        self.assertFalse(dlg.is_open())

    def test_close_before_show(self):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(MockJarvis())
        dlg.close()
        self.assertIsNone(dlg.frame)


class TestSetupDialogShow(unittest.TestCase):
    """SetupDialog.show() testleri — Tkinter mock ile."""

    def setUp(self):
        self.jarvis = MockJarvis()
        # Fully mock tkinter so no real Tk() is created
        self.tk_patch = patch("ui.setup_dialog.tk")
        self.mock_tk = self.tk_patch.start()
        # Setup Frame mock
        self.mock_frame = MagicMock()
        self.mock_frame.winfo_exists.return_value = True
        self.mock_tk.Frame.return_value = self.mock_frame
        # Label, Entry, Button, OptionMenu, Radiobutton all return mocks
        self.mock_tk.Label.return_value = MagicMock()
        self.mock_tk.Entry.return_value = MagicMock()
        self.mock_tk.Button.return_value = MagicMock()
        self.mock_tk.OptionMenu.return_value = MagicMock()
        self.mock_tk.Radiobutton.return_value = MagicMock()
        # StringVar
        self.mock_tk.StringVar.return_value = MagicMock()
        self.mock_tk.StringVar.return_value.get.return_value = "gemini"

    def tearDown(self):
        self.tk_patch.stop()

    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["qwen2.5:1.5b"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "piper-fahrettin", "label": "Fahrettin (Piper)"},
    ])
    def test_show_creates_frame(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=False)
        self.assertIsNotNone(dlg.frame)

    @patch("ui.setup_dialog.load_app_config", return_value={})
    @patch("ui.setup_dialog.get_ollama_models", return_value=[])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[])
    def test_show_with_empty_config(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=True)
        self.assertIsNotNone(dlg.frame)

    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini",
        "gemini_api_key": "AIzaSyTestKey",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["qwen2.5:1.5b"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "piper-fahrettin", "label": "Fahrettin (Piper)"},
    ])
    def test_show_sets_title_widgets(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=False)
        # At least one Label should have been created
        self.assertTrue(self.mock_tk.Label.called)

    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "ollama",
        "ollama_model": "qwen2.5:1.5b",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["qwen2.5:1.5b"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "piper-fahrettin", "label": "Fahrettin (Piper)"},
    ])
    def test_show_with_ollama_preselect(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=True)
        self.assertIsNotNone(dlg.frame)

    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini",
        "youtube_api_key": "",
        "youtube_channel_handle": "",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["qwen2.5:1.5b"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "piper-fahrettin", "label": "Fahrettin (Piper)"},
    ])
    def test_show_shows_warning_when_youtube_missing(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=False)
        self.assertIsNotNone(dlg.frame)

    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "ollama",
        "ollama_model": "",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=[])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[])
    def test_show_no_models_fallback(self, mock_tts, mock_models, mock_config):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.jarvis)
        dlg.show(edit_mode=False)
        self.assertIsNotNone(dlg.frame)


class TestSetupDialogActions(unittest.TestCase):
    """SetupDialog _save, _close, _on_backend_change testleri."""

    def setUp(self):
        self.jarvis = MockJarvis()
        self.dlg_jarvis = MagicMock()
        self.dlg_jarvis.root.winfo_width.return_value = 1600
        self.dlg_jarvis.root.winfo_height.return_value = 900
        self.dlg_jarvis.W = 1600
        self.dlg_jarvis._api_key_ready = False
        self.dlg_jarvis._current_voice = "Charon"

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini", "gemini_api_key": "AIzaSyKey",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "v1", "label": "V1"},
    ])
    def test_close_destroys_frame(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        mock_frame = MagicMock()
        mock_frame.winfo_exists.return_value = True
        mock_tk.Frame.return_value = mock_frame
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.show(edit_mode=False)
        dlg.close()
        mock_frame.destroy.assert_called_once()
        self.assertIsNone(dlg.frame)

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini", "gemini_api_key": "",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "v1", "label": "V1"},
    ])
    def test_save_gemini_empty_key_does_not_save(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.show(edit_mode=False)
        dlg.api_entry = MagicMock()
        dlg.api_entry.get.return_value = ""
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "gemini"
        with patch("ui.setup_dialog.save_app_config") as mock_save:
            dlg._save()
            mock_save.assert_not_called()

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "gemini", "gemini_api_key": "AIzaSyKey",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "v1", "label": "V1"},
    ])
    def test_save_gemini_with_key_saves(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.show(edit_mode=False)
        dlg.api_entry = MagicMock()
        dlg.api_entry.get.return_value = "AIzaSyNewKey"
        dlg.youtube_api_entry = MagicMock()
        dlg.youtube_api_entry.get.return_value = ""
        dlg.youtube_handle_entry = MagicMock()
        dlg.youtube_handle_entry.get.return_value = ""
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "gemini"
        dlg._ollama_model_var = MagicMock()
        dlg._ollama_model_var.get.return_value = ""
        dlg._ollama_tts_var = MagicMock()
        dlg._ollama_tts_var.get.return_value = "piper-fahrettin"
        with patch("ui.setup_dialog.save_app_config") as mock_save:
            dlg._save()
            mock_save.assert_called_once()
            args = mock_save.call_args[0][0]
            self.assertEqual(args["gemini_api_key"], "AIzaSyNewKey")
            self.assertEqual(args["backend_type"], "gemini")

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={
        "backend_type": "ollama", "gemini_api_key": "",
    })
    @patch("ui.setup_dialog.get_ollama_models", return_value=["qwen2.5:1.5b"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[
        {"id": "piper-fahrettin", "label": "Fahrettin (Piper)"},
    ])
    def test_save_ollama_works_without_key(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.show(edit_mode=False)
        dlg.api_entry = MagicMock()
        dlg.api_entry.get.return_value = ""
        dlg.youtube_api_entry = MagicMock()
        dlg.youtube_api_entry.get.return_value = ""
        dlg.youtube_handle_entry = MagicMock()
        dlg.youtube_handle_entry.get.return_value = ""
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "ollama"
        dlg._ollama_model_var = MagicMock()
        dlg._ollama_model_var.get.return_value = "qwen2.5:1.5b"
        dlg._ollama_tts_var = MagicMock()
        dlg._ollama_tts_var.get.return_value = "piper-fahrettin"
        with patch("ui.setup_dialog.save_app_config") as mock_save:
            dlg._save()
            mock_save.assert_called_once()
            args = mock_save.call_args[0][0]
            self.assertEqual(args["backend_type"], "ollama")
            self.assertEqual(args["ollama_model"], "qwen2.5:1.5b")

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={"backend_type": "gemini"})
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[{"id": "v1", "label": "V1"}])
    def test_on_backend_change_ollama_enables_menu(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.model_menu = MagicMock()
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "ollama"
        dlg._on_backend_change()
        dlg.model_menu.config.assert_called_with(state="normal")

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={"backend_type": "gemini"})
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[{"id": "v1", "label": "V1"}])
    def test_on_backend_change_gemini_disables_menu(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg.model_menu = MagicMock()
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "gemini"
        dlg._on_backend_change()
        dlg.model_menu.config.assert_called_with(state="disabled")

    @patch("ui.setup_dialog.tk")
    @patch("ui.setup_dialog.load_app_config", return_value={"backend_type": "gemini"})
    @patch("ui.setup_dialog.get_ollama_models", return_value=["model1"])
    @patch("ui.setup_dialog.get_ollama_tts_voices", return_value=[{"id": "v1", "label": "V1"}])
    def test_on_backend_change_no_model_menu(self, mock_tts, mock_models, mock_config, mock_tk):
        from ui.setup_dialog import SetupDialog
        dlg = SetupDialog(self.dlg_jarvis)
        dlg._backend_var = MagicMock()
        dlg._backend_var.get.return_value = "gemini"
        dlg.model_menu = None
        dlg._on_backend_change()
