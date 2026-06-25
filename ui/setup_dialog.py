"""
JARVIS UI — Setup dialog
Modal setup frame for first-run and API configuration.
Extracted from JarvisUI for module size reduction.
"""

from __future__ import annotations

import threading
import traceback
import tkinter as tk

from app_config import load_app_config, save_app_config, get_ollama_models, get_ollama_tts_voices, validate_config
from ui.theme import (
    C_BG, C_PRI, C_MID, C_TEXT, C_DIM, C_DIMMER, C_ORG, C_GOLD, C_RED,
    font_body, font_body_bold, font_display,
)


class SetupDialog:
    """First-run setup & API settings modal dialog.

    Creps a centred tk.Frame overlay with backend selection, API key entry,
    and Ollama model/voice selection. Owned by a JarvisUI instance.
    """

    def __init__(self, jarvis: object):
        self._jarvis = jarvis
        self.root = jarvis.root
        self.W = jarvis.W

        # ── Widget references (set during _show) ────────────────────────────
        self.frame: tk.Frame | None = None
        self.api_entry: tk.Entry | None = None
        self.youtube_api_entry: tk.Entry | None = None
        self.youtube_handle_entry: tk.Entry | None = None

        self._backend_var: tk.StringVar | None = None
        self._ollama_model_var: tk.StringVar | None = None
        self._ollama_tts_var: tk.StringVar | None = None
        self._ollama_tts_label_var: tk.StringVar | None = None
        self.model_menu: tk.OptionMenu | None = None
        self.tts_menu: tk.OptionMenu | None = None

    # ── Public API ─────────────────────────────────────────────────────────

    def show(self, edit_mode: bool = False):
        """Show the setup dialog.  *edit_mode* controls the title text."""
        self._close()
        config = load_app_config()

        f = tk.Frame(self.root, bg="#00080d",
                     highlightbackground=C_PRI, highlightthickness=1)
        self.frame = f
        setup_w = min(780, max(580, int(self.W * 0.44)))
        setup_h = min(680, max(580, int(self.W * 0.55)))
        f.place(relx=0.5, rely=0.5, anchor="center", width=setup_w, height=setup_h)
        f.pack_propagate(False)

        # ── Title ──────────────────────────────────────────────────────────
        title = "◈ BACKEND & API AYARLARI" if edit_mode else "◈ İLK KURULUM GEREKLİ"
        subtitle = (
            "Gemini, YouTube ve yerel Ollama ayarlarinizi guncelleyin."
            if edit_mode else
            "Gemini API anahtarini girin veya yerel Ollama backend'ini secin."
        )

        tk.Label(f, text=title, fg=C_PRI, bg="#00080d",
                 font=font_display(20)).pack(pady=(20, 4))
        tk.Label(f, text=subtitle, fg=C_MID, bg="#00080d",
                 font=font_body(12)).pack(pady=(0, 10))

        # ── Backend selection ──────────────────────────────────────────────
        tk.Label(f, text="BACKEND SEÇİMİ", fg=C_PRI, bg="#00080d",
                 font=font_body_bold(11)).pack(pady=(8, 2))

        backend_frame = tk.Frame(f, bg="#00080d")
        backend_frame.pack(pady=4)

        self._backend_var = tk.StringVar(value=config.get("backend_type", "gemini"))
        self._ollama_model_var = tk.StringVar(value=config.get("ollama_model", ""))
        self._ollama_tts_var = tk.StringVar(value=config.get("ollama_tts_voice",
                                                              "piper-fahrettin"))

        def _mk_rb(text, value):
            return tk.Radiobutton(
                backend_frame, text=text, variable=self._backend_var,
                value=value, fg=C_TEXT, bg="#00080d", selectcolor="#00080d",
                activeforeground=C_PRI, activebackground="#00080d",
                font=font_body(11), command=self._on_backend_change,
            )

        _mk_rb("Gemini (Bulut)", "gemini").pack(side="left", padx=15)
        _mk_rb("Ollama (Yerel)", "ollama").pack(side="left", padx=15)

        # ── Ollama model ───────────────────────────────────────────────────
        model_frame = tk.Frame(f, bg="#00080d")
        model_frame.pack(pady=4)
        tk.Label(model_frame, text="Ollama Modeli:", fg=C_DIM, bg="#00080d",
                 font=font_body(11)).pack(side="left", padx=5)

        models = get_ollama_models()
        if not models:
            models = ["Model Bulunamadı (Ollama kapalı?)"]
        if not self._ollama_model_var.get() or self._ollama_model_var.get() not in models:
            self._ollama_model_var.set(models[0])

        self.model_menu = tk.OptionMenu(model_frame, self._ollama_model_var, *models)
        self.model_menu.config(
            fg=C_PRI, bg="#000d12", activeforeground=C_BG,
            activebackground=C_PRI, font=font_body(10),
            borderwidth=0, highlightthickness=1,
            highlightbackground=C_MID, width=28,
        )
        self.model_menu["menu"].config(
            fg=C_PRI, bg="#000d12", font=font_body(10),
            activeforeground=C_BG, activebackground=C_PRI,
        )
        self.model_menu.pack(side="left")

        # ── Ollama TTS voice ───────────────────────────────────────────────
        tts_frame = tk.Frame(f, bg="#00080d")
        tts_frame.pack(pady=4)
        tk.Label(tts_frame, text="Ollama Ses Motoru:", fg=C_DIM, bg="#00080d",
                 font=font_body(11)).pack(side="left", padx=5)

        tts_voices = get_ollama_tts_voices()
        tts_ids = [v["id"] for v in tts_voices]
        tts_labels = [v["label"] for v in tts_voices]

        saved_tts = self._ollama_tts_var.get()
        if saved_tts not in tts_ids:
            saved_tts = tts_ids[0] if tts_ids else "piper-fahrettin"
        self._ollama_tts_var.set(saved_tts)

        selected_label = (
            tts_labels[tts_ids.index(saved_tts)]
            if saved_tts in tts_ids and tts_labels
            else (tts_labels[0] if tts_labels else saved_tts)
        )
        self._ollama_tts_label_var = tk.StringVar(value=selected_label)

        def _on_tts_select(label_chosen):
            idx = tts_labels.index(label_chosen)
            self._ollama_tts_var.set(tts_ids[idx])
            self._ollama_tts_label_var.set(label_chosen)

        self.tts_menu = tk.OptionMenu(tts_frame, self._ollama_tts_label_var,
                                      *tts_labels, command=_on_tts_select)
        self.tts_menu.config(
            fg=C_PRI, bg="#000d12", activeforeground=C_BG,
            activebackground=C_PRI, font=font_body(10),
            borderwidth=0, highlightthickness=1,
            highlightbackground=C_MID, width=32,
        )
        self.tts_menu["menu"].config(
            fg=C_PRI, bg="#000d12", font=font_body(10),
            activeforeground=C_BG, activebackground=C_PRI,
        )
        self.tts_menu.pack(side="left")

        # ── Gemini API key ─────────────────────────────────────────────────
        tk.Label(f, text="GEMINI API KEY (Gemini için zorunlu)",
                 fg=C_DIM, bg="#00080d",
                 font=font_body(11)).pack(pady=(12, 2))
        self.api_entry = tk.Entry(
            f, width=54, fg=C_TEXT, bg="#000d12", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(12), show="*",
        )
        self.api_entry.pack(pady=(0, 6), ipady=4)
        current_key = str(config.get("gemini_api_key", "") or "")
        if current_key:
            self.api_entry.insert(0, current_key)

        # ── YouTube configs ────────────────────────────────────────────────
        yt_key = str(config.get("youtube_api_key", "") or "")
        yt_handle = str(config.get("youtube_channel_handle", "") or "")
        if not yt_key.strip() or not yt_handle.strip():
            warn_frame = tk.Frame(f, bg="#1a0f00")
            warn_frame.pack(pady=(4, 2), fill="x", padx=20)
            warns = []
            if not yt_key.strip():
                warns.append("⚠ YouTube API Key eksik — kanal istatistikleri calismaz.")
            if not yt_handle.strip():
                warns.append("⚠ YouTube handle girilmedi.")
            tk.Label(warn_frame, text=" ".join(warns), fg=C_ORG, bg="#1a0f00",
                     wraplength=500, font=font_body(9)).pack(pady=4)

        tk.Label(f, text="YOUTUBE API KEY (Opsiyonel)", fg=C_DIM, bg="#00080d",
                 font=font_body(11)).pack(pady=(6, 2))
        self.youtube_api_entry = tk.Entry(
            f, width=54, fg=C_TEXT, bg="#000d12", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(12), show="*",
        )
        self.youtube_api_entry.pack(pady=(0, 6), ipady=4)
        if yt_key:
            self.youtube_api_entry.insert(0, yt_key)

        tk.Label(f, text="YOUTUBE HANDLE / CHANNEL (Opsiyonel)",
                 fg=C_DIM, bg="#00080d",
                 font=font_body(11)).pack(pady=(6, 2))
        self.youtube_handle_entry = tk.Entry(
            f, width=54, fg=C_TEXT, bg="#000d12", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(12),
        )
        self.youtube_handle_entry.pack(pady=(0, 6), ipady=4)
        if yt_handle:
            self.youtube_handle_entry.insert(0, yt_handle)

        # ── Buttons ────────────────────────────────────────────────────────
        buttons = tk.Frame(f, bg="#00080d")
        buttons.pack(pady=12)

        tk.Button(buttons, text="▸ KAYDET", command=self._save,
                  bg=C_BG, fg=C_PRI, activebackground="#003344",
                  font=font_body_bold(12), borderwidth=0,
                  padx=20, pady=8).pack(side="left", padx=8)

        if edit_mode:
            tk.Button(buttons, text="KAPAT", command=self._close,
                      bg="#08111a", fg=C_DIM, activebackground="#10202b",
                      font=font_body_bold(12), borderwidth=0,
                      padx=20, pady=8).pack(side="left", padx=8)

        self._on_backend_change()

    def close(self):
        """Public alias for _close; used by JarvisUI."""
        self._close()

    def is_open(self) -> bool:
        return self.frame is not None and self.frame.winfo_exists()

    # ── Internal ──────────────────────────────────────────────────────────

    def _close(self):
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()
        self.frame = None
        self.api_entry = None
        self.youtube_api_entry = None
        self.youtube_handle_entry = None

    def _on_backend_change(self, _val=None):
        if self.model_menu is None:
            return
        backend = self._backend_var.get() if self._backend_var else "gemini"
        self.model_menu.config(state="normal" if backend == "ollama" else "disabled")

    def _save(self):
        jarvis = self._jarvis
        was_ready = getattr(jarvis, "_api_key_ready", False)

        backend = self._backend_var.get() if self._backend_var else "gemini"
        key = self.api_entry.get().strip() if self.api_entry else ""
        youtube_key = (
            self.youtube_api_entry.get().strip()
            if self.youtube_api_entry else ""
        )
        youtube_handle = (
            self.youtube_handle_entry.get().strip()
            if self.youtube_handle_entry else ""
        )
        ollama_model = self._ollama_model_var.get() if self._ollama_model_var else ""
        if "Yok" in ollama_model or "Bulunamadı" in ollama_model:
            ollama_model = ""
        ollama_tts_voice = "piper-fahrettin"
        if self._ollama_tts_var is not None:
            ollama_tts_voice = self._ollama_tts_var.get()
        voice = getattr(jarvis, "_current_voice", "Charon")

        # ── Validate with centralized function ──
        config = {
            "gemini_api_key": key,
            "youtube_api_key": youtube_key,
            "youtube_channel_handle": youtube_handle,
            "voice": voice,
            "backend_type": backend,
            "ollama_model": ollama_model,
            "ollama_tts_voice": ollama_tts_voice,
        }
        errors = validate_config(config)
        if errors:
            for err in errors:
                jarvis.write_log(f"SYS: {err}")
            # Flash the dialog border to indicate error
            if self.frame and self.frame.winfo_exists():
                orig_bg = self.frame.cget("highlightbackground")
                self.frame.config(highlightbackground=C_RED)
                jarvis.root.after(2000, lambda: (
                    self.frame.config(highlightbackground=orig_bg)
                    if self.frame and self.frame.winfo_exists()
                    else None
                ))
            return

        save_app_config(config)
        self._close()
        jarvis._api_key_ready = True
        jarvis._refresh_settings_status()
        if was_ready:
            jarvis.write_log("SYS: Ayarlar guncellendi.")
        else:
            jarvis.set_state("LISTENING")
            jarvis.write_log("SYS: JARVIS hazır. Dinliyorum...")
