"""
JARVIS Windows — UI v3
Concentric teal rings · Segmented arcs
Adler ASİ tarafından yapılmıştır
"""
from __future__ import annotations


import os, time, math, random, signal, threading, queue, traceback
import tkinter as tk
from collections import deque
from pathlib import Path
import psutil
from PIL import Image, ImageTk

from app_config import has_gemini_api_key, load_app_config, save_app_config, get_ollama_models, get_ollama_tts_voices
from actions.weather import get_weather_summary
from actions.windows_utils import open_url

from ui.theme import (
    C_BG, C_PRI, C_ORG, C_ORG2, C_MID, C_DIM, C_DIMMER, C_TEXT, C_PANEL,
    C_GREEN, C_RED, C_MUTED, C_BLUE, C_GOLD,
    ORB_COLORS, STATE_HEX_COLORS,
    W_TARGET, H_TARGET, LEFT_W_T, RIGHT_W_T, HDR_H, FOOTER_H, INPUT_H, CONTROL_H,
    VOICES,
    FONT_BODY_FAMILY, FONT_DISPLAY_FAMILY,
    font_body, font_body_bold, font_display,
)
from ui.draw_utils import _ac, _bar, _sparkline, _bracket, _draw_info_card as _draw_info_card_impl, _orb_rgb as _orb_rgb_impl
from ui.text_utils import _split_summary_lines, _parse_weather_card as _parse_weather_card_impl, _parse_health_card as _parse_health_card_impl
from ui.setup_dialog import SetupDialog

BASE_DIR = Path(__file__).resolve().parent

def _num_threads_safe(proc):
    """psutil.num_threads() wrapper that handles process exit race condition."""
    try:
        return proc.num_threads()
    except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
        return 0


def _resolve_sfx_dir() -> Path:
    return BASE_DIR / "SFX"
IS_WINDOWS = (os.name == 'nt')

SYSTEM_NAME = "J.A.R.V.I.S"
MODEL_BADGE = "VOICE CORE · Windows"


# ── SoundManager ─────────────────────────────────────────────────────────────
from ui.sound_manager import SoundManager
from ui.orb_canvas import OrbCanvas

# ─────────────────────────────────────────────────────────────────────────────

class JarvisUI:
    def __init__(self):
        # ── Hardware check: display required for UI ──
        try:
            from core.hardware_detector import HardwareDetector
            dpy = HardwareDetector.check_display()
            if dpy.status != "ok":
                raise RuntimeError(
                    f"Cannot start UI — {dpy.label}: {dpy.detail}\n"
                    "Run in headless/CLI mode instead."
                )
        except ImportError:
            pass  # during early module bootstrap, proceed with best-effort

        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S")
        self.root.update_idletasks()

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        margin_x = max(24, int(sw * 0.025))
        margin_y = max(54, int(sh * 0.055))
        # Adaptive sizing: cap at 92% of screen or absolute max for ultra-large
        max_w = min(int(sw * 0.92), max(W_TARGET, sw))
        max_h = min(int(sh * 0.92), max(H_TARGET, sh))
        self.W = min(max(640, sw - margin_x), sw, max_w)
        self.H = min(max(520, sh - margin_y), sh, max_h)
        _geo = f"{self.W}x{self.H}+{(sw-self.W)//2}+{max(0, (sh-self.H)//2 - 8)}"
        self.root.geometry(_geo)
        self.root.minsize(min(self.W, sw), min(self.H, sh))
        self.root.resizable(True, True)
        self.root.configure(bg=C_BG)
        self.root.attributes('-topmost', True)
        self.root.lift()
        self.root.focus_force()
        # Pencere yoneticisi bazen geometry'yi override eder, tekrar zorla.
        for delay in (80, 220, 600, 1200):
            self.root.after(delay, self._force_startup_size)
        # Birkaç saniye sonra topmost'u kapat (normal davranış)
        self.root.after(3000, lambda: self.root.attributes('-topmost', False))

        self._window_geometry = _geo
        self._normal_size = (self.W, self.H)
        self._fullscreen = False

        self._set_layout_metrics(self.W, self.H)

        # ── State ────────────────────────────────────────────────────────────
        self.speaking        = False
        self.user_speaking   = False
        self.muted           = False
        self.paused          = False
        self.scale           = 1.0
        self.target_scale    = 1.0
        self.halo_a          = 55.0
        self.target_halo     = 55.0
        self.last_t          = time.time()
        self.tick            = 0
        self.rings_spin      = [0.0, 45.0, 90.0, 200.0]  # 4 ayrı halka
        self.pulse_r         = []
        self.status_blink    = True
        self._jarvis_state   = "INITIALISING"
        self._user_speaking_until = 0.0

        # ── ACA Agent state ──────────────────────────────────────────────────
        self.agent_goal_text: str = ""
        self.agent_steps: list[dict] = []
        self.agent_active_step: int = 0
        self.agent_log: list[str] = []
        self.agent_approval_request: dict | None = None
        self.agent_confidence: float = 0.0
        self.agent_enabled: bool = True
        self.agent_approval_mode: bool = False
        self.agent_max_steps: int = 20
        self.agent_max_duration: int = 300

        # ── Health overlay ───────────────────────────────────────────────────
        self._health_visible  = False
        self._health_query    = "all"
        self._health_display  = ""
        self._health_hide_job = None
        self._system_alert = ""
        self._system_alert_until = 0.0
        self._weather_card = {
            "city": "Istanbul",
            "primary": "--",
            "details": ["Hava durumu yükleniyor..."],
        }
        self._health_card_lines = ["Sağlık özeti yükleniyor..."]
        self._panel_focus = ""
        self._panel_focus_until = 0.0
        self._brief_refresh_busy = False
        self._mic_level = 0.0
        self._started_at = time.time()
        self._error_hold_until = 0.0
        self._settings_open = False
        self._settings_tab = "settings"
        self._debug_entries = deque(maxlen=160)
        self._startup_sfx_played = False
        self._settings_geometry = {
            "btn_x": 14,
            "btn_y": 12,
            "btn_w": 250,
            "btn_h": 46,
            "panel_x": 14,
            "panel_y": HDR_H + 10,
            "panel_w": 320,
            "panel_h": 292,
        }
        self._setup_dialog = SetupDialog(self)

        # ── Callbacks ────────────────────────────────────────────────────────
        self.on_text_command = None
        self.on_pause_toggle = None
        self.on_stop_command = None
        self.on_voice_change = None
        self.on_effects_state_change = None
        self.on_agent_approval = None
        self.on_approval_mode_toggle = None
        self.on_config_change = None

        self.root.bind("<F6>", lambda e: self._on_agent_approve())
        self.root.bind("<F7>", lambda e: self._on_agent_deny())
        self.root.bind("<F8>", lambda e: self._on_approval_toggle())
        self.root.bind("<F9>", lambda e: self._on_config_change("max_steps", 5))
        self.root.bind("<F10>", lambda e: self._on_config_change("max_steps", -5))
        self.root.bind("<Shift-F9>", lambda e: self._on_config_change("max_duration", 30))
        self.root.bind("<Shift-F10>", lambda e: self._on_config_change("max_duration", -30))

        # ── Voice ────────────────────────────────────────────────────────────
        self._current_voice = self._load_voice()

        # ── Sound ────────────────────────────────────────────────────────────
        self.sound = SoundManager()

        # ── Stats ────────────────────────────────────────────────────────────
        self._stats      = {'cpu': 0.0, 'ram': 0.0, 'disk': 0.0,
                            'battery': 100.0, 'net_up': 0.0, 'net_down': 0.0}
        self._cpu_hist   = [0.0] * 24
        self._last_net   = psutil.net_io_counters()
        self._last_net_t = time.time()
        self._wave_jarvis = [random.randint(4, 26) for _ in range(18)]
        self._wave_user   = [random.randint(2, 10) for _ in range(18)]

        # ── Typing ───────────────────────────────────────────────────────────
        self.typing_queue = deque()
        self.is_typing    = False

        # ── Partiküller (arka plan, az sayıda) ───────────────────────────────
        self.particles = [
            {
                'x':  random.uniform(0, self.W),
                'y':  random.uniform(0, self.H),
                'vx': random.uniform(-0.15, 0.15),
                'vy': random.uniform(-0.15, 0.15),
                'r':  random.uniform(0.5, 1.8),
                'a':  random.randint(15, 70),
            }
            for _ in range(24)
        ]

        self.orb_particles = [
            {
                'angle': random.uniform(0, math.tau),
                'orbit': random.uniform(0.06, 0.98),
                'speed': random.uniform(-0.030, 0.030),
                'size': random.uniform(0.8, 2.8),
                'phase': random.uniform(0, math.tau),
                'wobble': random.uniform(0.010, 0.040),
                'depth': random.uniform(0.30, 1.00),
            }
            for _ in range(160)
        ]
        self.orb_shell_particles = [
            {
                'angle': random.uniform(0, math.tau),
                'speed': random.uniform(-0.020, 0.020),
                'size': random.uniform(1.4, 3.8),
                'phase': random.uniform(0, math.tau),
                'glow': random.uniform(0.4, 1.0),
            }
            for _ in range(84)
        ]

        # ── Canvas ───────────────────────────────────────────────────────────
        self.bg = tk.Canvas(self.root, width=self.W, height=self.H,
                            bg=C_BG, highlightthickness=0)
        self.bg.place(x=0, y=0)

        # ── 3D Orb ───────────────────────────────────────────────────────────
        self._orb = OrbCanvas(self.root, size=self.FACE)
        self._orb.place(x=self.FCX, y=self.FCY, anchor="center")


        # ── Log ──────────────────────────────────────────────────────────────
        self.log_frame = tk.Frame(self.root, bg="#030e0e",
                                  highlightbackground=C_MID,
                                  highlightthickness=1)
        self.log_frame.place(x=self.CHAT_X, y=self.CHAT_Y,
                             width=self.CHAT_W, height=self.CHAT_H)
        self.log_text = tk.Text(
            self.log_frame, fg=C_TEXT, bg="#030e0e",
            insertbackground=C_TEXT, borderwidth=0,
            wrap="word", font=font_body(12), padx=12, pady=8)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self.log_text.tag_config("you", foreground="#d0f0ee")
        self.log_text.tag_config("ai",  foreground=C_PRI)
        self.log_text.tag_config("sys", foreground=C_GOLD)
        self.log_text.tag_config("err", foreground=C_RED)

        self._build_input_bar(self.CHAT_W)
        self._build_mute_button()
        self._build_pause_button()
        self._build_shutdown_button()
        self._build_settings_panel()
        self._build_voice_selector(self._settings_body)
        self._build_sfx_button(self._settings_body)
        self._build_api_button(self._settings_body)
        self._build_fx_slider(self._settings_body)
        self._layout_settings_controls()
        self._place_layout_widgets()

        # Orb tıklama = pause/resume
        self.bg.bind("<Button-1>", self._on_canvas_click)

        self.root.bind("<F4>",        lambda e: self._toggle_mute())
        self.root.bind("<Command-m>", lambda e: self._toggle_mute())
        self.root.bind("<Escape>",    lambda e: self._shutdown())
        self.root.bind("<F5>",        lambda e: self._toggle_pause())
        self.root.bind("<F11>",       lambda e: self._toggle_fullscreen())
        self.root.bind("<Command-f>", lambda e: self._toggle_fullscreen())

        cfg = load_app_config()
        self._api_key_ready = (cfg.get("backend_type", "gemini") == "ollama") or has_gemini_api_key()
        if not self._api_key_ready:
            self._setup_dialog.show()

        self._effects_active = None
        self._sync_sound_state()
        self.root.after(180, self._play_startup_sfx_once)
        self._kick_brief_refresh()
        self._build_social_bar()
        if self._fullscreen:
            self.root.after(120, self._enter_fullscreen)
        # Thread-safe GUI queue
        self._gui_queue = queue.Queue()
        self._process_gui_queue()

        self._animate()
        self.root.protocol("WM_DELETE_WINDOW", self._shutdown)

    def _force_startup_size(self):
        if self._fullscreen:
            self._enter_fullscreen()
            return
        self.root.geometry(self._window_geometry)
        self._resize_surface(*self._normal_size)
        self.root.update_idletasks()

    def safe_call(self, func, *args, **kwargs):
        """Thread-safe UI call. Main thread'de direkt çalışır, bg thread'de queue'ya ekler."""
        if threading.current_thread() is threading.main_thread():
            try:
                return func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
                return None
        self._gui_queue.put((func, args, kwargs))
        return None

    def _process_gui_queue(self):
        while not self._gui_queue.empty():
            try:
                func, args, kwargs = self._gui_queue.get_nowait()
                func(*args, **kwargs)
            except Exception:
                traceback.print_exc()
        self.root.after(40, self._process_gui_queue)

    def _enter_fullscreen(self):
        sw = max(self.root.winfo_screenwidth(), self.root.winfo_width(), self.W)
        sh = max(self.root.winfo_screenheight(), self.root.winfo_height(), self.H)
        self.root.attributes("-fullscreen", True)
        self.root.geometry(f"{sw}x{sh}+0+0")
        self._resize_surface(sw, sh)

    def _set_layout_metrics(self, width: int, height: int):
        self.W = int(width)
        self.H = int(height)
        self.LEFT_W = min(LEFT_W_T, int(self.W * 0.23))
        self.RIGHT_W = min(RIGHT_W_T, int(self.W * 0.25))
        center_w = self.W - self.LEFT_W - self.RIGHT_W
        orb_area_h = self.H - HDR_H - CONTROL_H - FOOTER_H - 24
        self.FCX = self.LEFT_W + center_w // 2
        self.FCY = HDR_H + orb_area_h // 2 + 6
        self.FACE = min(int(orb_area_h * 0.90), int(center_w * 0.86), 860)

        self.CENTER_X0 = self.LEFT_W
        self.CENTER_X1 = self.W - self.RIGHT_W
        self.CTRL_X = self.LEFT_W + 18
        self.CTRL_Y = HDR_H + orb_area_h + 2
        self.CTRL_W = center_w - 36
        self.CHAT_PANEL_X = self.W - self.RIGHT_W + 8
        self.CHAT_PANEL_Y = HDR_H + 8
        self.CHAT_PANEL_W = self.RIGHT_W - 14
        self.CHAT_PANEL_H = self.H - HDR_H - FOOTER_H - 16
        self.CHAT_X = self.CHAT_PANEL_X + 10
        self.CHAT_Y = self.CHAT_PANEL_Y + 34
        self.CHAT_W = self.CHAT_PANEL_W - 20
        self.CHAT_H = self.CHAT_PANEL_H - 90
        self.CHAT_INPUT_Y = self.CHAT_PANEL_Y + self.CHAT_PANEL_H - INPUT_H - 10

        if hasattr(self, "_orb") and self._orb:
            self._orb.place(x=self.FCX, y=self.FCY, anchor="center")


    # ── Social bar ───────────────────────────────────────────────────────────
    def _build_social_bar(self):
        ICON_SIZE = 28
        ICON_DIR  = BASE_DIR / "Icon"

        bar = tk.Frame(self.root, bg=C_BG)
        self._social_bar = bar
        bar.place(x=14, y=self.H - FOOTER_H - 52)

        def _open(url):
            return lambda e: open_url(url)

        def _load_icon(filename: str):
            try:
                img = Image.open(ICON_DIR / filename).convert("RGBA")
                img = img.resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                return None

        name_lbl = tk.Label(
            bar, text="Adler ASİ",
            fg="#3a8a82", bg=C_BG,
            font=font_display(14), cursor="hand2",
            justify="left",
        )
        name_lbl.pack(side="left", padx=(0, 10))
        name_lbl.bind("<Button-1>", _open("https://www.instagram.com/adler_asi/?hl=tr"))

        self._icon_ig = _load_icon("instagram-logo.png")
        self._icon_yt = _load_icon("youtube-logo.png")

        if self._icon_ig:
            ig_lbl = tk.Label(bar, image=self._icon_ig, bg=C_BG, cursor="hand2")
            ig_lbl.pack(side="left", padx=4)
            ig_lbl.bind("<Button-1>", _open("https://www.instagram.com/adler_asi/?hl=tr"))

        if self._icon_yt:
            yt_lbl = tk.Label(bar, image=self._icon_yt, bg=C_BG, cursor="hand2")
            yt_lbl.pack(side="left", padx=4)
            yt_lbl.bind("<Button-1>", _open("https://www.instagram.com/adler_asi/?hl=tr"))

    # ── Voice ─────────────────────────────────────────────────────────────────
    def _load_voice(self) -> str:
        try:
            return str(load_app_config().get("voice", "Charon") or "Charon")
        except Exception:
            return "Charon"

    # ── Shutdown button (sağ alt, büyük) ────────────────────────────────────
    def _build_shutdown_button(self):
        BW, BH = 140, 36
        self._shutdown_canvas = tk.Canvas(
            self.root, width=BW, height=BH,
            bg=C_BG, highlightthickness=0, cursor="hand2")
        self._shutdown_canvas.bind("<Button-1>", lambda e: self._shutdown())
        self._draw_shutdown_button()

    def _draw_shutdown_button(self):
        c = self._shutdown_canvas
        BW, BH = 140, 36
        c.delete("all")
        # Köşe braket stili
        bl = 8
        for bx, by, sx, sy in [(0, 0, 1, 1), (BW, 0, -1, 1),
                                (0, BH, 1, -1), (BW, BH, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=C_RED, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=C_RED, width=2)
        c.create_text(BW//2, BH//2, text="⏻  SHUTDOWN",
                      fill=C_RED, font=font_display(11))

    def _build_settings_panel(self):
        geo = self._settings_geometry
        self._settings_btn_canvas = tk.Canvas(
            self.root,
            width=geo["btn_w"],
            height=geo["btn_h"],
            bg=C_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_btn_canvas.place(x=geo["btn_x"], y=geo["btn_y"])
        self._settings_btn_canvas.bind("<Button-1>", lambda e: self._toggle_settings_panel())
        self._draw_settings_button()

        self._settings_panel = tk.Frame(
            self.root,
            bg="#041111",
            highlightbackground=C_MID,
            highlightthickness=1,
        )
        self._settings_panel.place_forget()

        self._settings_title = tk.Label(
            self._settings_panel,
            text="SETTINGS",
            fg=C_PRI,
            bg="#041111",
            font=font_display(11),
        )
        self._settings_tab_settings = tk.Canvas(
            self._settings_panel,
            width=108,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_settings.bind("<Button-1>", lambda e: self._set_settings_tab("settings"))
        self._settings_tab_debug = tk.Canvas(
            self._settings_panel,
            width=96,
            height=28,
            bg="#041111",
            highlightthickness=0,
            cursor="hand2",
        )
        self._settings_tab_debug.bind("<Button-1>", lambda e: self._set_settings_tab("debug"))
        self._settings_body = tk.Frame(self._settings_panel, bg="#041111")
        self._debug_body = tk.Frame(self._settings_panel, bg="#041111")
        self._settings_sfx_label = tk.Label(
            self._settings_body,
            text="SFX",
            fg=C_MID,
            bg="#041111",
            font=font_body_bold(8),
        )
        self._settings_status_primary = tk.Label(
            self._settings_body,
            text="",
            fg=C_TEXT,
            bg="#041111",
            font=font_body_bold(9),
            anchor="w",
            justify="left",
        )
        self._settings_status_secondary = tk.Label(
            self._settings_body,
            text="",
            fg=C_MID,
            bg="#041111",
            font=font_body(9),
            anchor="w",
            justify="left",
        )
        self._debug_text = tk.Text(
            self._debug_body,
            fg=C_TEXT,
            bg="#020a0a",
            insertbackground=C_TEXT,
            borderwidth=0,
            wrap="word",
            font=font_body(10),
            padx=10,
            pady=10,
            highlightthickness=1,
            highlightbackground=C_DIM,
        )
        self._debug_text.tag_config("info", foreground=C_TEXT)
        self._debug_text.tag_config("warn", foreground=C_GOLD)
        self._debug_text.tag_config("err", foreground=C_RED)
        self._debug_text.configure(state="disabled")
        self._draw_settings_tabs()
        self._render_debug_logs()
        self._refresh_settings_status()

    def _draw_settings_button(self):
        c = self._settings_btn_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        accent = C_BLUE if self._settings_open else C_MID
        inner = "#062020" if self._settings_open else "#021010"
        c.create_rectangle(0, 0, bw, bh, fill=inner, outline="")
        bl = 9
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1), (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx + sx * bl, by, fill=accent, width=2)
            c.create_line(bx, by, bx, by + sy * bl, fill=accent, width=2)
        c.create_text(14, 15, text="SYSTEM SETTINGS", fill=C_PRI, font=font_display(10), anchor="w")
        c.create_text(14, 33, text=MODEL_BADGE, fill="#4f7b78", font=font_body(9), anchor="w")
        c.create_text(bw - 14, bh // 2, text="▾" if self._settings_open else "▸",
                      fill=accent, font=font_display(14), anchor="e")

    def _toggle_settings_panel(self):
        self._settings_open = not self._settings_open
        self._draw_settings_button()
        self._place_layout_widgets()

    def _draw_settings_tabs(self):
        for key, canvas, label in (
            ("settings", self._settings_tab_settings, "SETTINGS"),
            ("debug", self._settings_tab_debug, "DEBUG"),
        ):
            active = self._settings_tab == key
            bw = int(canvas["width"])
            bh = int(canvas["height"])
            canvas.delete("all")
            outline = C_PRI if active else C_DIM
            fill = "#082020" if active else "#041111"
            text_col = C_PRI if active else "#5ea7a0"
            canvas.create_rectangle(0, 0, bw, bh, fill=fill, outline="")
            bl = 7
            for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1), (0, bh, 1, -1), (bw, bh, -1, -1)]:
                canvas.create_line(bx, by, bx + sx * bl, by, fill=outline, width=1)
                canvas.create_line(bx, by, bx, by + sy * bl, fill=outline, width=1)
            canvas.create_text(bw // 2, bh // 2, text=label, fill=text_col, font=font_body_bold(9))

    def _set_settings_tab(self, tab: str):
        self._settings_tab = "debug" if tab == "debug" else "settings"
        self._draw_settings_tabs()
        self._place_layout_widgets()

    def _layout_settings_controls(self):
        inner_w = self._settings_geometry["panel_w"] - 24
        self._api_canvas.place(x=0, y=2)
        self._sfx_canvas.place(x=inner_w - int(self._sfx_canvas["width"]) - 4, y=0)
        self._settings_status_primary.place(x=0, y=38, width=inner_w)
        self._settings_status_secondary.place(x=0, y=58, width=inner_w)
        self._settings_sfx_label.place(x=0, y=92)
        self._volume_label.place(x=0, y=116)
        self._volume_scale.place(x=0, y=136, width=inner_w, height=26)
        self._voice_label.place(x=0, y=178)
        self._voice_menu.place(x=88, y=172, width=inner_w - 88, height=30)

    def _refresh_settings_status(self):
        if not hasattr(self, "_settings_status_primary"):
            return
        cfg = load_app_config()
        backend = cfg.get("backend_type", "gemini")
        gemini_ready = bool(str(cfg.get("gemini_api_key", "") or "").strip())
        yt_key_ready = bool(str(cfg.get("youtube_api_key", "") or "").strip())
        yt_handle = str(cfg.get("youtube_channel_handle", "") or "").strip()

        if backend == "ollama":
            model = cfg.get("ollama_model", "Varsayılan")
            primary_text = f"Ollama ({model})"
        else:
            primary_text = "Gemini (Live)" if gemini_ready else "Gemini API Eksik"

        primary = [
            primary_text,
            "YT hazir" if yt_key_ready and yt_handle else "YT eksik",
        ]
        yt_missing = not (yt_key_ready and yt_handle)
        if yt_handle:
            handle_text = yt_handle
        else:
            handle_text = "@handle girilmedi"
        secondary = f"Kanal: {handle_text}"

        self._settings_status_primary.configure(
            text="  ·  ".join(primary),
            fg=C_ORG if yt_missing else C_TEXT,
        )
        self._settings_status_secondary.configure(text=secondary)

    def write_debug(self, text: str, level: str = "INFO"):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.write_debug, text, level)
            return
        clean = " ".join(str(text or "").split())
        if not clean:
            return
        self._append_debug_entry(clean, level)

    def _append_debug_entry(self, text: str, level: str = "INFO"):
        stamp = time.strftime("%H:%M:%S")
        lvl = (level or "INFO").upper()
        self._debug_entries.append((lvl, f"[{stamp}] {lvl}: {text}"))
        self._render_debug_logs()

    def _render_debug_logs(self):
        if not hasattr(self, "_debug_text"):
            return
        self._debug_text.configure(state="normal")
        self._debug_text.delete("1.0", tk.END)
        if not self._debug_entries:
            self._debug_text.insert(tk.END, "Henüz not edilebilir hata yok.\n", "info")
        else:
            for level, line in self._debug_entries:
                tag = "err" if level == "ERROR" else "warn" if level == "WARN" else "info"
                self._debug_text.insert(tk.END, line + "\n", tag)
        self._debug_text.see(tk.END)
        self._debug_text.configure(state="disabled")

    def _build_api_button(self, parent=None):
        parent = parent or self.root
        bw, bh = 154, 28
        self._api_canvas = tk.Canvas(
            parent, width=bw, height=bh,
            bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._api_canvas.bind("<Button-1>", lambda e: self._setup_dialog.show(edit_mode=self._api_key_ready))
        self._draw_api_button()

    def _draw_api_button(self):
        c = self._api_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        bl = 6
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1), (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx + sx * bl, by, fill=C_BLUE, width=1)
            c.create_line(bx, by, bx, by + sy * bl, fill=C_BLUE, width=1)
        c.create_text(bw // 2, bh // 2, text="⌘ API SETTINGS",
                      fill=C_BLUE, font=font_body_bold(10))

    def _build_fx_slider(self, parent=None):
        parent = parent or self.root
        slider_w = 280
        self._volume_label = tk.Label(
            parent,
            text=f"FX LEVEL  {int(self.sound.get_volume() * 100)}%",
            fg=C_PRI,
            bg=parent.cget("bg"),
            font=font_body_bold(10),
        )
        self._volume_scale = tk.Scale(
            parent,
            from_=0,
            to=100,
            orient="horizontal",
            length=slider_w,
            showvalue=False,
            resolution=1,
            troughcolor="#071818",
            bg=parent.cget("bg"),
            fg=C_TEXT,
            activebackground=C_PRI,
            highlightthickness=0,
            borderwidth=0,
            sliderlength=18,
            width=10,
            command=self._on_volume_change,
        )
        self._volume_scale.set(int(self.sound.get_volume() * 100))

    def _on_volume_change(self, value):
        try:
            volume = max(0, min(100, int(float(value))))
        except (TypeError, ValueError):
            return
        self._volume_label.configure(text=f"FX LEVEL  {volume}%")
        self.sound.set_volume(volume / 100.0)

    def _play_startup_sfx_once(self):
        pass

    def _sync_sound_state(self):
        enabled = self._sfx_on and not self.paused
        self.sound.set_enabled(enabled)
        if enabled and self._jarvis_state == "THINKING":
            self.sound.start_thinking()
        if enabled != self._effects_active:
            self._effects_active = enabled
            if self.on_effects_state_change:
                try:
                    self.on_effects_state_change(enabled)
                except Exception:
                    traceback.print_exc()

    # ── SFX toggle ───────────────────────────────────────────────────────────
    def _build_sfx_button(self, parent=None):
        parent = parent or self.root
        BW, BH = 98, 36
        self._sfx_canvas = tk.Canvas(parent, width=BW, height=BH,
                                     bg=parent.cget("bg"), highlightthickness=0, cursor="hand2")
        self._sfx_canvas.bind("<Button-1>", lambda e: self._toggle_sfx())
        self._sfx_on = True
        self._draw_sfx_button()

    def _draw_sfx_button(self):
        c = self._sfx_canvas
        BW = int(c["width"])
        BH = int(c["height"])
        c.delete("all")
        col  = C_PRI if self._sfx_on else C_MID
        text = "♪ SFX ON"  if self._sfx_on else "♪ SFX OFF"
        bl = 6
        for bx, by, sx, sy in [(0, 0, 1, 1), (BW, 0, -1, 1),
                                (0, BH, 1, -1), (BW, BH, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=1)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=1)
        c.create_text(BW//2, BH//2, text=text, fill=col, font=font_body_bold(9))

    def _toggle_sfx(self):
        self._sfx_on = not self._sfx_on
        self._draw_sfx_button()
        self._sync_sound_state()

    # ── Voice selector ───────────────────────────────────────────────────────
    def _build_voice_selector(self, parent=None):
        parent = parent or self.root
        self._voice_var = tk.StringVar(value=self._current_voice)
        self._voice_label = tk.Label(parent, text="VOICE", fg=C_MID, bg=parent.cget("bg"),
                                     font=font_body_bold(8))

        self._voice_menu = tk.OptionMenu(parent, self._voice_var, *VOICES,
                                         command=self._on_voice_select)
        self._voice_menu.config(
            fg=C_PRI, bg=C_PANEL, activeforeground=C_BG,
            activebackground=C_PRI, font=font_body(10),
            borderwidth=0, highlightthickness=1,
            highlightbackground=C_MID, width=12)
        self._voice_menu["menu"].config(
            fg=C_PRI, bg=C_PANEL, font=font_body(10),
            activeforeground=C_BG, activebackground=C_PRI)

    def _on_voice_select(self, voice: str):
        self._current_voice = voice
        save_app_config({"voice": voice})
        if self.on_voice_change:
            threading.Thread(target=self.on_voice_change, args=(voice,), daemon=True).start()

    # ── Mute button ──────────────────────────────────────────────────────────
    def _build_mute_button(self):
        self._mute_canvas = tk.Canvas(self.root, width=126, height=36,
                                      bg=C_BG, highlightthickness=0, cursor="hand2")
        self._mute_canvas.bind("<Button-1>", lambda e: self._toggle_mute())
        self._draw_mute_button()

    def _draw_mute_button(self):
        c = self._mute_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        if self.muted:
            col, icon, lbl = C_MUTED, "🔇", " MUTED"
        else:
            col, icon, lbl = C_GREEN, "🎙", " LIVE"
        bl = 6
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1),
                                (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)
        c.create_text(bw//2, bh//2, text=f"{icon}{lbl}",
                      fill=col, font=font_body_bold(11))

    def _build_pause_button(self):
        self._pause_canvas = tk.Canvas(self.root, width=126, height=36,
                                       bg=C_BG, highlightthickness=0, cursor="hand2")
        self._pause_canvas.bind("<Button-1>", lambda e: self._toggle_pause())
        self._draw_pause_button()

    def _draw_pause_button(self):
        c = self._pause_canvas
        bw = int(c["width"])
        bh = int(c["height"])
        c.delete("all")
        if self.paused:
            col, text = C_GOLD, "▶ RESUME"
        else:
            col, text = C_BLUE, "⏸ PAUSE"
        bl = 6
        for bx, by, sx, sy in [(0, 0, 1, 1), (bw, 0, -1, 1),
                               (0, bh, 1, -1), (bw, bh, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)
        c.create_text(bw//2, bh//2, text=text, fill=col, font=font_body_bold(11))

    def _toggle_mute(self):
        self.muted = not self.muted
        self._draw_mute_button()
        if self.muted:
            self.write_log("SYS: Mikrofon kapatıldı.")
        else:
            self.write_log("SYS: Mikrofon açık.")
        self._sync_sound_state()

    # ── Orb tıklama = pause ──────────────────────────────────────────────────
    def _on_canvas_click(self, event):
        dx = event.x - self.FCX
        dy = event.y - self.FCY
        if dx*dx + dy*dy <= (self.FACE * 0.40)**2:
            self._toggle_pause()

    def _toggle_pause(self):
        self.paused = not self.paused
        self._draw_pause_button()
        if self.paused:
            self.set_state("PAUSED")
            self.write_log("SYS: JARVIS duraklatıldı.")
        else:
            self.set_state("THINKING")
            self.write_log("SYS: JARVIS devam ediyor...")
        self._sync_sound_state()
        if self.on_pause_toggle:
            try:
                self.on_pause_toggle(self.paused)
            except Exception:
                traceback.print_exc()

    def destroy(self):
        self.sound.stop_all()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _shutdown(self):
        self.write_log("SYS: JARVIS kapatılıyor...")
        self.root.after(500, self.root.destroy)

    def _toggle_fullscreen(self):
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self._enter_fullscreen()
        else:
            self.root.attributes("-fullscreen", False)
            self.root.geometry(self._window_geometry)
            self._resize_surface(*self._normal_size)

    def _resize_surface(self, width: int, height: int):
        self._set_layout_metrics(width, height)
        self.bg.configure(width=self.W, height=self.H)
        self.bg.place(x=0, y=0)
        self._place_layout_widgets()
        if hasattr(self, "_social_bar"):
            self._social_bar.place(x=14, y=self.H - FOOTER_H - 52)
        for p in self.particles:
            p["x"] %= self.W
            p["y"] %= self.H

    # ── Input bar ────────────────────────────────────────────────────────────
    def _build_input_bar(self, lw: int):
        x0 = self.CHAT_X
        btn_w = 76
        gap = 8
        inp_w = lw - btn_w - gap

        self._input_var   = tk.StringVar()
        self._input_entry = tk.Entry(
            self.root, textvariable=self._input_var,
            fg=C_TEXT, bg="#041212", insertbackground=C_TEXT,
            borderwidth=0, font=font_body(11),
            highlightthickness=1, highlightbackground=C_DIM,
            highlightcolor=C_PRI)
        self._input_entry.place(
            x=x0, y=self.CHAT_INPUT_Y, width=inp_w, height=INPUT_H)
        self._input_entry.bind("<Return>",   self._on_input_submit)
        self._input_entry.bind("<KP_Enter>", self._on_input_submit)

        self._send_btn = tk.Button(
            self.root, text="SEND ▸",
            command=self._on_input_submit,
            fg=C_ORG, bg=C_PANEL,
            activeforeground=C_BG, activebackground=C_ORG,
            font=font_body_bold(10),
            borderwidth=0, cursor="hand2",
            highlightthickness=1, highlightbackground=C_ORG)
        self._send_btn.place(
            x=x0+inp_w+gap, y=self.CHAT_INPUT_Y,
            width=btn_w, height=INPUT_H)

    def _place_layout_widgets(self):
        self.log_frame.place(x=self.CHAT_X, y=self.CHAT_Y, width=self.CHAT_W, height=self.CHAT_H)
        gap = 12
        mute_w = 126
        pause_w = 126
        shutdown_w = int(self._shutdown_canvas["width"])
        total = mute_w + pause_w + shutdown_w + gap * 2
        start_x = self.FCX - total // 2
        row1_y = self.CTRL_Y + 20

        self._mute_canvas.place(x=start_x, y=row1_y)
        self._pause_canvas.place(x=start_x + mute_w + gap, y=row1_y)
        self._shutdown_canvas.place(x=start_x + mute_w + pause_w + gap * 2, y=row1_y)

        geo = self._settings_geometry
        panel_x = geo["panel_x"]
        panel_y = geo["panel_y"]
        panel_w = geo["panel_w"]
        panel_h = geo["panel_h"]
        if self._settings_open:
            self._settings_panel.place(x=panel_x, y=panel_y, width=panel_w, height=panel_h)
            self._settings_panel.lift()
            self._settings_title.place(x=14, y=12)
            self._settings_tab_settings.place(x=14, y=40)
            self._settings_tab_debug.place(x=130, y=40)
            if self._settings_tab == "debug":
                self._settings_body.place_forget()
                self._debug_body.place(x=12, y=76, width=panel_w - 24, height=panel_h - 88)
                self._debug_text.place(x=0, y=0, width=panel_w - 24, height=panel_h - 88)
                self._debug_body.lift()
            else:
                self._debug_body.place_forget()
                self._settings_body.place(x=12, y=76, width=panel_w - 24, height=panel_h - 88)
                self._settings_body.lift()
        else:
            self._settings_panel.place_forget()
            self._settings_title.place_forget()
            self._settings_tab_settings.place_forget()
            self._settings_tab_debug.place_forget()
            self._settings_body.place_forget()
            self._debug_body.place_forget()

        inp_w = self.CHAT_W - 84
        self._input_entry.place(x=self.CHAT_X, y=self.CHAT_INPUT_Y, width=inp_w, height=INPUT_H)
        self._send_btn.place(x=self.CHAT_X + inp_w + 8, y=self.CHAT_INPUT_Y, width=76, height=INPUT_H)

    def _on_input_submit(self, event=None):
        text = self._input_var.get().strip()
        if not text:
            return
        if self.paused:
            self.write_log("SYS: JARVIS duraklatılmış durumda. Devam etmek için pause'u kapat.")
            return
        self._input_var.set("")
        if text.lower() in ("sus", "dur", "stop", "sessiz", "kes"):
            self.write_log("SYS: ⏹ Ses kesildi.")
            if self.on_stop_command:
                threading.Thread(target=self.on_stop_command, daemon=True).start()
            return
        if self.on_text_command:
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    # ── State & callbacks ────────────────────────────────────────────────────
    def set_state(self, state: str):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.set_state, state)
            return
        previous = getattr(self, "_jarvis_state", "")
        self._jarvis_state = state
        self.speaking = (state == "SPEAKING")
        if hasattr(self, "_orb") and self._orb:
            self._orb.set_state(state)
        if state == "THINKING":
            self.sound.start_thinking()
        elif previous == "THINKING":
            self.sound.stop_thinking()
        if state == "ERROR" and previous != "ERROR":
            self.sound.play_error()

    def set_user_speaking(self, value: bool):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.set_user_speaking, value)
            return
        self.mark_user_activity(value)

    def mark_user_activity(self, active: bool = True):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.mark_user_activity, active)
            return
        self.user_speaking = active
        self._user_speaking_until = time.time() + (0.9 if active else 0.0)

    def get_effects_volume(self) -> float:
        return self.sound.get_volume()

    def effects_enabled(self) -> bool:
        return bool(self._effects_active)

    def play_success_sfx(self):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.play_success_sfx)
            return
        self.sound.play_success()

    def play_error_sfx(self):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.play_error_sfx)
            return
        self.sound.play_error()

    def set_mic_level(self, level: float):
        """Update microphone level indicator (0.0–1.0). Thread-safe."""
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.set_mic_level, level)
            return
        self._mic_level = max(0.0, min(1.0, level))

    def _on_agent_approve(self):
        if self.agent_approval_request and self.on_agent_approval:
            req_id = self.agent_approval_request.get("request_id", "")
            if req_id:
                self.on_agent_approval(req_id, True)
                self.agent_approval_request = None

    def _on_agent_deny(self):
        if self.agent_approval_request and self.on_agent_approval:
            req_id = self.agent_approval_request.get("request_id", "")
            if req_id:
                self.on_agent_approval(req_id, False)
                self.agent_approval_request = None

    def _on_approval_toggle(self):
        if self.on_approval_mode_toggle:
            self.on_approval_mode_toggle()

    def _on_config_change(self, key: str, delta: int):
        if self.on_config_change:
            self.on_config_change(key, delta)

    def _update_agent_state(self, state: dict):
        """Update ACA agent UI state from AgentManager. Thread-safe."""
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self._update_agent_state, state)
            return
        self.agent_goal_text = state.get("goal_text", "")
        self.agent_steps = state.get("steps", [])
        self.agent_active_step = state.get("active_step", 0)
        self.agent_approval_request = state.get("approval_request")
        self.agent_confidence = 0.0
        self.agent_enabled = state.get("enabled", False)
        self.agent_approval_mode = state.get("approval_mode", False)
        self.agent_log = state.get("logs", [])
        self.agent_max_steps = state.get("max_steps", 20)
        self.agent_max_duration = state.get("max_duration", 300)
        # Extract confidence from active step if available
        steps = self.agent_steps
        if steps and self.agent_active_step < len(steps):
            self.agent_confidence = steps[self.agent_active_step].get("confidence", 0.0)

    def focus_panel(self, section: str, duration_ms: int = 4200):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.focus_panel, section, duration_ms)
            return
        section = (section or "").strip().lower()
        if not section:
            return
        self._panel_focus = section
        self._panel_focus_until = time.time() + max(0.8, duration_ms / 1000.0)

    def _state_color(self, state: str | None = None) -> str:
        effective = state or self._jarvis_state
        if effective == "PAUSED":
            return C_MID
        return STATE_HEX_COLORS.get(effective, C_PRI)

    @staticmethod
    def _state_badge_text(state: str) -> str:
        if state == "INITIALISING":
            return "CONNECTING"
        if state == "ERROR":
            return "ERROR"
        return "ONLINE"

    # ── Log ──────────────────────────────────────────────────────────────────
    def write_log(self, text: str):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.write_log, text)
            return
        self.typing_queue.append(text)
        tl = text.lower()
        if tl.startswith("siz:") or tl.startswith("you:"):
            self.mark_user_activity(True)
            self.set_state("THINKING")
        elif tl.startswith("err:") or "error" in tl:
            self._error_hold_until = time.time() + 8.0
            self.set_state("ERROR")
            self.write_debug(text, level="ERROR")
        if not self.is_typing:
            self._start_typing()

    def _start_typing(self):
        if not self.typing_queue:
            self.is_typing = False
            if self._jarvis_state == "ERROR" and time.time() < self._error_hold_until:
                return
            if not self.speaking:
                self.set_state("LISTENING")
            return
        self.is_typing = True
        text = self.typing_queue.popleft()
        tl   = text.lower()
        if   tl.startswith("siz:") or tl.startswith("you:"):   tag = "you"
        elif tl.startswith("jarvis:") or tl.startswith("ai:"): tag = "ai"
        elif tl.startswith("err:") or "error" in tl:           tag = "err"
        else:                                                    tag = "sys"
        self.log_text.configure(state="normal")
        self._type_char(text, 0, tag)

    def _type_char(self, text, i, tag):
        if i < len(text):
            self.log_text.insert(tk.END, text[i], tag)
            self.log_text.see(tk.END)
            self.root.after(7, self._type_char, text, i+1, tag)
        else:
            self.log_text.insert(tk.END, "\n")
            self.log_text.configure(state="disabled")
            self.root.after(20, self._start_typing)

    # ── Stats ────────────────────────────────────────────────────────────────
    def _update_stats(self):
        try:
            self._stats['cpu']  = psutil.cpu_percent()
            self._stats['ram']  = psutil.virtual_memory().percent
            self._stats['disk'] = psutil.disk_usage('/').percent
            batt = psutil.sensors_battery()
            self._stats['battery'] = batt.percent if batt else 100.0
            now = time.time()
            net = psutil.net_io_counters()
            dt  = now - self._last_net_t
            if dt > 0:
                self._stats['net_up']   = max(0, (net.bytes_sent - self._last_net.bytes_sent) / dt / 1024)
                self._stats['net_down'] = max(0, (net.bytes_recv - self._last_net.bytes_recv) / dt / 1024)
            self._last_net   = net
            self._last_net_t = now
            self._cpu_hist.pop(0)
            self._cpu_hist.append(self._stats['cpu'])
            # Süreç ve thread sayısı
            self._stats['processes'] = len(psutil.pids())
            self._stats['threads'] = sum(
                _num_threads_safe(p) for p in psutil.process_iter()
            )
        except Exception:
            traceback.print_exc()

    # ── Animation loop ───────────────────────────────────────────────────────
    def _animate(self):
        self.tick += 1
        t   = self.tick
        now = time.time()

        if self.user_speaking and now > self._user_speaking_until:
            self.user_speaking = False

        if t % 90 == 0:
            threading.Thread(target=self._update_stats, daemon=True).start()
        if t % 1800 == 1:
            self._kick_brief_refresh()
        if t % 600 == 0:
            threading.Thread(target=self._check_system_alerts, daemon=True).start()

        if self.speaking and t % 3 == 0:
            self._wave_jarvis = [random.randint(6, 30) for _ in range(18)]
        if self.user_speaking and t % 3 == 0:
            self._wave_user = [random.randint(5, 24) for _ in range(18)]

        if now - self.last_t > (0.12 if self.speaking else 0.50):
            if self.paused:
                self.target_scale = random.uniform(0.58, 0.64)
                self.target_halo  = random.uniform(5, 10)
            elif self.speaking:
                self.target_scale = random.uniform(0.98, 1.10)
                self.target_halo  = random.uniform(180, 250)
            elif self.user_speaking:
                self.target_scale = random.uniform(0.88, 0.98)
                self.target_halo  = random.uniform(120, 175)
            elif self._jarvis_state in ("THINKING", "INITIALISING"):
                self.target_scale = random.uniform(0.80, 0.88)
                self.target_halo  = random.uniform(95, 145)
            else:
                self.target_scale = random.uniform(0.72, 0.80)
                self.target_halo  = random.uniform(34, 58)
            self.last_t = now

        sp          = 0.34 if self.speaking else 0.18
        self.scale  += (self.target_scale - self.scale) * sp
        self.halo_a += (self.target_halo   - self.halo_a) * sp

        if self.paused:
            spds = [0.0, 0.0, 0.0, 0.0]
        elif self.speaking:
            spds = [1.6, -1.1, 2.4, -0.7]
        else:
            spds = [0.55, -0.35, 0.90, -0.28]
        for i, spd in enumerate(spds):
            self.rings_spin[i] = (self.rings_spin[i] + spd) % 360

        # Pulse rings
        pspd  = 4.2 if self.speaking else 1.8
        limit = self.FACE * 0.68
        self.pulse_r = [r + pspd for r in self.pulse_r if r + pspd < limit]
        if len(self.pulse_r) < 3 and random.random() < (0.07 if self.speaking else 0.02):
            self.pulse_r.append(0.0)

        for p in self.particles:
            p['x'] = (p['x'] + p['vx']) % self.W
            p['y'] = (p['y'] + p['vy']) % self.H

        if t % 38 == 0:
            self.status_blink = not self.status_blink

        self._draw()
        self.root.after(33, self._animate)

    # ── Yardımcı (delegated to ui/ sub-modules) ────────────────
    _ac = staticmethod(_ac)
    _split_summary_lines = staticmethod(_split_summary_lines)
    _parse_weather_card = staticmethod(_parse_weather_card_impl)
    _parse_health_card = staticmethod(_parse_health_card_impl)
    _bar = _bar
    _sparkline = _sparkline
    _bracket = _bracket

    def _orb_rgb(self):
        return _orb_rgb_impl(self._jarvis_state, self.paused)

    def _kick_brief_refresh(self):
        if self._brief_refresh_busy:
            return
        self._brief_refresh_busy = True
        threading.Thread(target=self._refresh_brief_cards, daemon=True).start()

    def _refresh_brief_cards(self):
        city = "Istanbul"
        try:
            from memory.memory_manager import load_memory
            mem = load_memory()
            city = (mem.get("preferences", {}).get("weather_location", {})).get("value") or "Istanbul"
            weather = get_weather_summary(city)
            self._weather_card = self._parse_weather_card(weather)
        except Exception:
            self._weather_card = {
                "city": city,
                "primary": "--",
                "details": ["Hava durumu alınamadı."],
            }
        finally:
            self._brief_refresh_busy = False

    def force_weather_refresh(self):
        """AI tarafından çağrılır — weather_location değişince paneli anında günceller."""
        self._kick_brief_refresh()

    def _bar(self, c, x, y, w, h, pct, color):
        c.create_rectangle(x, y, x+w, y+h, fill="#061212", outline=C_DIM, width=1)
        fw = max(1, int(w * pct / 100))
        c.create_rectangle(x+1, y+1, x+fw, y+h-1, fill=color, outline="")

    def _sparkline(self, c, x, y, w, h, data):
        c.create_rectangle(x, y, x+w, y+h, fill="#050e0e", outline=C_DIM, width=1)
        n = len(data)
        if n < 2:
            return
        step = (w - 2) / (n - 1)
        h2   = h - 2
        coords = []
        for i, v in enumerate(data):
            coords.append(x + 1 + i * step)
            coords.append(y + h - 1 - int(h2 * v / 100))
        c.create_line(*coords, fill=C_PRI, width=1, smooth=True)

    def _bracket(self, c, x0, y0, pw, ph, col=None, bl=12):
        col = col or C_PRI
        for bx, by, sx, sy in [(x0, y0, 1, 1), (x0+pw, y0, -1, 1),
                                (x0, y0+ph, 1, -1), (x0+pw, y0+ph, -1, -1)]:
            c.create_line(bx, by, bx+sx*bl, by, fill=col, width=2)
            c.create_line(bx, by, bx, by+sy*bl, fill=col, width=2)

    def _draw_info_card(self, c, x0, y0, pw, ph, title, accent=C_PRI):
        focus = max(0.0, min(1.0, getattr(self, "_card_focus_boost", 0.0)))
        dimmed = bool(getattr(self, "_card_dimmed", False))
        _draw_info_card_impl(c, x0, y0, pw, ph, title, accent,
                             focus=focus, dimmed=dimmed)

    def _focus_boost_for(self, section: str) -> float:
        if self._panel_focus != section:
            return 0.0
        remaining = self._panel_focus_until - time.time()
        if remaining <= 0:
            return 0.0
        pulse = 0.65 + 0.35 * math.sin(self.tick * 0.12)
        return min(1.0, remaining / 4.0) * pulse

    # ── Health overlay (sol panel) ────────────────────────────────────────────
    def show_health_hologram(self, query: str, data_str: str):
        def _show():
            self._health_visible = True
            self._health_query   = query.lower()
            self._health_display = data_str
            self._panel_focus = "health"
            self._panel_focus_until = time.time() + 5.0
            if self._health_hide_job:
                self.root.after_cancel(self._health_hide_job)
            self._health_hide_job = self.root.after(14000, self._hide_health_hologram)
        self.root.after(0, _show)

    def _hide_health_hologram(self):
        self._health_visible  = False
        self._health_hide_job = None

    # ── System Alert ──────────────────────────────────────────────────────────
    def show_system_alert(self, message: str, duration_sec: int = 10):
        if threading.current_thread() is not threading.main_thread():
            self.safe_call(self.show_system_alert, message, duration_sec)
            return
        self._system_alert = message
        self._system_alert_until = time.time() + duration_sec
        self.write_log(f"SYS ALERT: {message}")

    def _draw_system_alert(self, c):
        if time.time() > self._system_alert_until:
            self._system_alert = ""
            return
        if not self._system_alert:
            return
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.15)
        alpha = int(180 + 75 * pulse)
        banner_h = 28
        c.create_rectangle(0, HDR_H, self.W, HDR_H + banner_h,
                           fill=self._ac(255, 51, 68, alpha), outline="")
        c.create_text(self.W // 2, HDR_H + banner_h // 2,
                      text=f"⚠ {self._system_alert}",
                      fill="#ffffff", font=font_body_bold(11))

    def _check_system_alerts(self):
        try:
            import psutil
            for part in psutil.disk_partitions():
                if os.name == "nt" and ("cdrom" in part.opts or part.fstype == ""):
                    continue
                if part.device.startswith("/dev/loop"):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    if usage.percent >= 95:
                        self.show_system_alert(f"KRİTİK: {part.device} %{usage.percent:.0f} dolu!", 30)
                    elif usage.percent >= 85:
                        self.show_system_alert(f"UYARI: {part.device} %{usage.percent:.0f} dolu", 20)
                except Exception:
                    continue
            vm = psutil.virtual_memory()
            if vm.percent >= 95:
                self.show_system_alert(f"KRİTİK: RAM %{vm.percent:.0f} kullanımda!", 30)
            elif vm.percent >= 85:
                self.show_system_alert(f"UYARI: RAM %{vm.percent:.0f} kullanımda", 20)
        except Exception:
            traceback.print_exc()

    def _draw_health_overlay(self, c):
        x0, y0 = 4, HDR_H + 4
        pw = self.LEFT_W - 8
        ph = self.H - HDR_H - FOOTER_H - 90
        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.08)

        c.create_rectangle(x0, y0, x0+pw, y0+ph,
                           fill="#011510", outline=C_PRI, width=1)
        self._bracket(c, x0, y0, pw, ph, col=C_ORG, bl=10)

        title_col = self._ac(0, 212, 192, int(200 + 55*pulse))
        c.create_text(x0+pw//2, y0+18, text="◈ HEALTH ◈",
                      fill=title_col, font=font_display(11))
        c.create_line(x0+8, y0+30, x0+pw-8, y0+30, fill=C_MID)

        lines = [l for l in self._health_display.split('\n') if l.strip()]
        ly = y0 + 44
        for line in lines:
            if ly > y0 + ph - 14:
                break
            if line.startswith("──"):
                c.create_line(x0+8, ly, x0+pw-8, ly, fill=C_DIM)
                ly += 10
            elif ":" in line:
                parts = line.split(":", 1)
                lbl   = parts[0].strip()
                val   = parts[1].strip() if len(parts) > 1 else ""
                c.create_text(x0+10, ly, text=lbl+":", fill=C_MID,
                              font=font_body(10), anchor="w")
                c.create_text(x0+pw-10, ly, text=val, fill=C_ORG,
                              font=font_body_bold(10), anchor="e")
                ly += 20
            else:
                c.create_text(x0+10, ly, text=line, fill=C_TEXT,
                              font=font_body(9), anchor="w")
                ly += 17

    # ── Sol panel ─────────────────────────────────────────────────────────────
    def _draw_left_panel(self, c):
        if self._health_visible:
            self._draw_health_overlay(c)
            return

        x0 = 10
        y0 = HDR_H + 10
        pw = self.LEFT_W - 18
        gap = 14
        total_h = self.H - HDR_H - FOOTER_H - 20
        card_area_h = total_h - gap * 3
        pad = 14
        bw = pw - 2 * pad

        cards = [
            ("time", 0.22, "TIME", C_GOLD),
            ("weather", 0.20, f"WEATHER · {self._weather_card['city'].upper()}", C_BLUE),
            ("system", 0.28, "SYSTEM STATUS", C_PRI),
            ("health", 0.30, "HEALTH SUMMARY", C_GREEN),
        ]
        any_focus_active = bool(self._panel_focus) and (self._panel_focus_until > time.time())
        weights = []
        for section, weight, _, _ in cards:
            weights.append(weight + (0.12 if self._focus_boost_for(section) > 0.08 else 0.0))
        total_weight = sum(weights)
        heights = [int(card_area_h * (weight / total_weight)) for weight in weights]
        heights[-1] += card_area_h - sum(heights)

        current_y = y0
        for (section, _, title, accent), ph in zip(cards, heights):
            focus_boost = self._focus_boost_for(section)
            dimmed = any_focus_active and focus_boost <= 0.08
            shift_x = int(14 * focus_boost)
            extra_w = int(22 * focus_boost)
            section_x = x0 + shift_x
            section_pw = pw + extra_w
            section_pad = pad + int(2 * focus_boost)
            section_bw = section_pw - 2 * section_pad
            muted_label = "#647270" if dimmed else C_MID
            muted_text = "#7e8a88" if dimmed else C_TEXT
            muted_primary = "#8ea19d" if dimmed else C_PRI
            muted_blue = "#829594" if dimmed else C_BLUE
            muted_green = "#85a393" if dimmed else C_GREEN
            muted_gold = "#a1997e" if dimmed else C_GOLD
            muted_warn = "#8d7f77" if dimmed else C_ORG2
            muted_red = "#8a7779" if dimmed else C_RED
            self._card_focus_boost = focus_boost
            self._card_dimmed = dimmed
            self._draw_info_card(c, section_x, current_y, section_pw, ph, title, accent=accent if not dimmed else "#72807f")

            if section == "time":
                c.create_text(section_x+section_pad, current_y+64, text=time.strftime("%H:%M"),
                              fill=muted_primary, font=font_display(36 if focus_boost > 0.08 else 34), anchor="w")
                c.create_text(section_x+section_pad, current_y+92, text=time.strftime(":%S"),
                              fill=muted_label, font=font_body_bold(13), anchor="w")
                c.create_text(section_x+section_pad, current_y+118, text=time.strftime("%d %B %Y").upper(),
                              fill=muted_gold, font=font_body_bold(11), anchor="w")
                c.create_text(section_x+section_pad, current_y+138, text=time.strftime("%A").upper(),
                              fill=muted_text, font=font_body(10), anchor="w")

            elif section == "weather":
                c.create_text(section_x+section_pad, current_y+58, text=self._weather_card["primary"],
                              fill=muted_primary, font=font_display(30 if focus_boost > 0.08 else 28), anchor="w")
                c.create_text(section_x+section_pad, current_y+84, text=self._weather_card["city"].upper(),
                              fill=muted_label, font=font_body_bold(10), anchor="w")
                wy = current_y + 108
                for line in self._weather_card["details"][:3]:
                    c.create_text(section_x+section_pad, wy, text=f"• {line}", fill=muted_text,
                                  font=font_body(10), anchor="w")
                    wy += 17

            elif section == "system":
                cy = current_y + 44
                uptime = int(time.time() - self._started_at)
                up_min, up_sec = divmod(uptime, 60)
                up_hr, up_min = divmod(up_min, 60)
                c.create_text(section_x+section_pad, cy, text=f"UPTIME  {up_hr:02d}:{up_min:02d}:{up_sec:02d}",
                              fill=muted_label, font=font_body_bold(9), anchor="w")
                cy += 22
                for label, key, unit in [("CPU", "cpu", "%"), ("RAM", "ram", "%"), ("DISK", "disk", "%"), ("BATTERY", "battery", "%")]:
                    val = self._stats[key]
                    col = C_RED if val > 80 and key != "battery" else C_ORG if val > 55 and key != "battery" else (C_RED if key == "battery" and val < 20 else C_GREEN if key == "battery" else C_PRI)
                    if dimmed:
                        col = muted_red if col == C_RED else muted_warn if col == C_ORG else muted_green if col == C_GREEN else muted_primary
                    c.create_text(section_x+section_pad, cy, text=label, fill=muted_label, font=font_body(10), anchor="w")
                    c.create_text(section_x+section_pw-section_pad, cy, text=f"{val:.0f}{unit}", fill=col, font=font_body_bold(10), anchor="e")
                    cy += 14
                    self._bar(c, section_x+section_pad, cy, section_bw, 7, val, col)
                    cy += 16

                # Yeni: Süreç ve thread sayısı
                proc_count = self._stats.get('processes', 0)
                thread_count = self._stats.get('threads', 0)
                if proc_count > 0:
                    c.create_text(section_x+section_pad, cy, text="SÜREÇLER", fill=muted_label, font=font_body(10), anchor="w")
                    c.create_text(section_x+section_pw-section_pad, cy, text=f"{proc_count}", fill=muted_primary, font=font_body_bold(10), anchor="e")
                    cy += 16
                if thread_count > 0:
                    c.create_text(section_x+section_pad, cy, text="THREADLER", fill=muted_label, font=font_body(10), anchor="w")
                    c.create_text(section_x+section_pw-section_pad, cy, text=f"{thread_count}", fill=muted_primary, font=font_body_bold(10), anchor="e")
                    cy += 16

                up = self._stats["net_up"]
                down = self._stats["net_down"]
                up_s = f"{up:.1f} KB/s" if up < 1000 else f"{up/1024:.1f} MB/s"
                down_s = f"{down:.1f} KB/s" if down < 1000 else f"{down/1024:.1f} MB/s"
                c.create_line(section_x+section_pad, cy-4, section_x+section_pw-section_pad, cy-4, fill="#173130" if dimmed else C_DIM)
                c.create_text(section_x+section_pad, cy+10, text=f"▲ {up_s}", fill=muted_warn, font=font_body(10), anchor="w")
                c.create_text(section_x+section_pw-section_pad, cy+10, text=f"▼ {down_s}", fill=muted_green, font=font_body(10), anchor="e")

            elif section == "health":
                hy = current_y + 48
                for line in self._health_card_lines[:5]:
                    c.create_text(section_x+section_pad, hy, text=f"• {line}", fill=muted_text,
                                  font=font_body(10), anchor="w")
                    hy += 21

            current_y += ph + gap

        self._card_focus_boost = 0.0
        self._card_dimmed = False

    # ── ACA Agent Panel ───────────────────────────────────────────────────────
    def _draw_agent_panel(self, c):
        if not self.agent_enabled:
            return

        x0 = self.LEFT_W + 12
        pw = self.W - self.LEFT_W - self.RIGHT_W - 24
        y0 = max(HDR_H + 10, self.FCY + self.FACE // 2 + 20)
        ph = self.H - y0 - FOOTER_H - 14

        if ph < 60:
            return

        pad = 10
        idle = not self.agent_goal_text
        accent = C_GREEN if idle else (C_ORG if self.agent_approval_request else C_PRI)

        self._draw_info_card(c, x0, y0, pw, ph, "ACA AJAN", accent=accent)

        cy = y0 + 42

        mode_text = "🛡️ AÇIK" if self.agent_approval_mode else "🛡️ KAPALI"
        mode_col = C_GREEN if self.agent_approval_mode else C_DIM
        c.create_text(x0 + pw - pad, cy - 10, text=mode_text,
                      fill=mode_col, font=font_body_bold(8), anchor="e")

        if idle:
            c.create_text(x0 + pad, cy, text="✅ Hazir",
                          fill=C_GREEN, font=font_body_bold(12), anchor="w")
            cy += 22
            c.create_text(x0 + pad, cy,
                          text=f"Adim: {self.agent_max_steps} | Sure: {self.agent_max_duration}s  [F9/F10]",
                          fill=C_DIM, font=font_body(8), anchor="w")
            return
        # Goal text
        goal_display = self.agent_goal_text[:60]
        if len(self.agent_goal_text) > 60:
            goal_display += "..."
        c.create_text(x0 + pad, cy, text=f"🎯 {goal_display}",
                      fill=C_TEXT, font=font_body_bold(10), anchor="w")
        cy += 20

        total = max(1, len(self.agent_steps))
        done = sum(1 for s in self.agent_steps if s.get("status") in ("completed", "failed"))
        bar_w = pw - pad * 2 - 50
        bar_h = 6
        frac = done / total
        c.create_rectangle(x0 + pad, cy, x0 + pad + bar_w, cy + bar_h,
                           fill="#061212", outline=C_DIM, width=1)
        fw = max(1, int(bar_w * frac))
        c.create_rectangle(x0 + pad + 1, cy + 1, x0 + pad + fw, cy + bar_h - 1,
                           fill=C_GREEN if frac < 1 else C_PRI, outline="")
        c.create_text(x0 + pad + bar_w + 6, cy + bar_h // 2,
                      text=f"{done}/{total}", fill=C_MID,
                      font=font_body(8), anchor="w")
        cy += 14

        # Step list (max 4 visible)
        max_visible = min(len(self.agent_steps), 4)
        for i in range(max_visible):
            step = self.agent_steps[i]
            sid = step.get("step_id", f"s{i}")
            desc = step.get("description", "")
            status = step.get("status", "pending")
            is_active = (i == self.agent_active_step)

            status_symbols = {
                "pending": "○",
                "in_progress": "◉",
                "success": "✓",
                "failed": "✗",
                "cancelled": "—",
            }
            status_colors = {
                "pending": C_MID,
                "in_progress": C_ORG,
                "success": C_GREEN,
                "failed": C_RED,
                "cancelled": C_DIM,
            }
            sym = status_symbols.get(status, "○")
            col = status_colors.get(status, C_MID)

            # Check if width is reasonable for text
            desc_display = desc[:50]
            if len(desc) > 50:
                desc_display += "..."

            c.create_text(x0 + pad + 4, cy, text=sym, fill=col,
                          font=font_body_bold(12), anchor="w")
            c.create_text(x0 + pad + 22, cy, text=desc_display, fill=C_TEXT if is_active else C_MID,
                          font=font_body_bold(10) if is_active else font_body(10), anchor="w")
            cy += 18

        # Approval request section
        if self.agent_approval_request:
            cy += 4
            req = self.agent_approval_request
            c.create_line(x0 + pad, cy, x0 + pw - pad, cy, fill=C_ORG, width=1)
            cy += 6
            c.create_text(x0 + pad, cy, text="🛑 ONAY GEREKIYOR", fill=C_ORG2,
                          font=font_body_bold(10), anchor="w")
            cy += 16
            c.create_text(x0 + pad, cy, text=req.get("description", "")[:60],
                          fill=C_TEXT, font=font_body(9), anchor="w")
            cy += 14
            c.create_text(x0 + pad, cy, text=f"Arac: {req.get('tool_name', '')}",
                          fill=C_MID, font=font_body(9), anchor="w")

        if self.agent_log:
            cy += 6
            c.create_line(x0 + pad, cy, x0 + pw - pad, cy, fill=C_DIM, width=1)
            cy += 4
            c.create_text(x0 + pad, cy, text="📋 LOG",
                          fill=C_PRI, font=font_body_bold(9), anchor="w")
            cy += 14
            max_log = min(len(self.agent_log), 5)
            for entry in self.agent_log[-max_log:]:
                display = entry[:65]
                if len(entry) > 65:
                    display += "..."
                c.create_text(x0 + pad + 4, cy, text=display,
                              fill=C_MID, font=font_body(8), anchor="w")
                cy += 13

        cy += 4
        c.create_line(x0 + pad, cy, x0 + pw - pad, cy, fill=C_DIM, width=1)
        cy += 4
        c.create_text(x0 + pad, cy,
                      text=f"Adim: {self.agent_max_steps} | Sure: {self.agent_max_duration}s  [F9/F10]",
                      fill=C_DIM, font=font_body(7), anchor="w")

    # ── Sağ panel ─────────────────────────────────────────────────────────────
    def _draw_right_panel(self, c):
        x0  = self.CHAT_PANEL_X
        y0  = self.CHAT_PANEL_Y
        pw  = self.CHAT_PANEL_W
        ph  = self.CHAT_PANEL_H
        pad = 10

        c.create_rectangle(x0, y0, x0+pw, y0+ph, fill="#030d0d", outline="")
        self._bracket(c, x0, y0, pw, ph, col=C_MID)

        if self.paused:
            sc, st = C_MID, "PAUSED"
        else:
            sc, st = self._state_color(self._jarvis_state), self._jarvis_state

        c.create_text(x0+14, y0+16, text="CONVERSATION", fill=C_PRI,
                      font=font_display(11), anchor="w")
        c.create_text(x0+pw-pad, y0+16, text=st, fill=sc,
                      font=font_body_bold(10), anchor="e")
        c.create_line(x0+pad, y0+28, x0+pw-pad, y0+28, fill=C_DIM)

        # Son 3 log satırı (hızlı görünüm)
        ly = y0 + 38
        for entry in list(self._debug_entries)[-3:]:
            lvl_tag = entry[0] if isinstance(entry, tuple) else "INFO"
            text = entry[1] if isinstance(entry, tuple) else entry
            col = C_RED if lvl_tag == "ERROR" else C_GOLD if lvl_tag == "WARN" else C_MID
            c.create_text(x0+pad, ly, text=text, fill=col,
                          font=font_body(8), anchor="w")
            ly += 15

        # Mikrofon seviye göstergesi
        mic_y = y0 + ph - 24
        mic_w = pw - pad * 2
        mic_h = 8
        lvl = max(0.0, min(1.0, self._mic_level))
        c.create_rectangle(x0+pad, mic_y, x0+pad+mic_w, mic_y+mic_h,
                           fill="#061212", outline=C_DIM, width=1)
        fw = max(1, int(mic_w * lvl))
        col = C_GREEN if lvl < 0.5 else C_ORG if lvl < 0.8 else C_RED
        c.create_rectangle(x0+pad+1, mic_y+1, x0+pad+fw, mic_y+mic_h-1,
                           fill=col, outline="")
        c.create_text(x0+pad+mic_w, mic_y-2, text="MIC", fill=C_MID,
                      font=font_body(8), anchor="e")

    # ── ORB (ana çizim) ───────────────────────────────────────────────────────
    def _draw_orb(self, c):
        pass

    # ── Ana çizim ─────────────────────────────────────────────────────────────
    def _draw(self):
        c  = self.bg
        W  = self.W
        H  = self.H
        t  = self.tick
        c.delete("all")

        # ── Arka plan ────────────────────────────────────────────────────────
        # Nokta ızgarası — çok ince
        step = 48
        for x in range(0, W, step):
            for y in range(0, H, step):
                c.create_rectangle(x, y, x+1, y+1, fill=C_DIMMER, outline="")

        # Tarama çizgisi (yavaş, çok soluk)
        scan_y = (t * 0.7) % (H + 60) - 30
        for i in range(2):
            ly = (scan_y + i * 20) % H
            c.create_line(0, ly, W, ly+35, fill="#081818", width=1)

        # ── Bölücü çizgiler (ince, soluk) ────────────────────────────────────
        c.create_line(self.LEFT_W, HDR_H, self.LEFT_W, H-FOOTER_H,
                      fill=C_DIM, width=1)
        c.create_line(W-self.RIGHT_W, HDR_H, W-self.RIGHT_W, H-FOOTER_H,
                      fill=C_DIM, width=1)

        # ── Yan paneller ──────────────────────────────────────────────────────
        self._draw_left_panel(c)
        self._draw_right_panel(c)

        # ── ACA Agent Panel ──────────────────────────────────────────────────
        self._draw_agent_panel(c)

        # ── Orb ──────────────────────────────────────────────────────────────
        self._draw_orb(c)

        state_label = "PAUSED" if self.paused else self._jarvis_state
        state_col = self._state_color(state_label)
        c.create_text(self.FCX, self.CTRL_Y - 34, text=SYSTEM_NAME,
                      fill=C_TEXT, font=font_display(18))
        c.create_text(self.FCX, self.CTRL_Y - 12, text=f"● {state_label.title()}",
                      fill=state_col, font=font_body_bold(11))

        # ── HEADER ───────────────────────────────────────────────────────────
        c.create_rectangle(0, 0, W, HDR_H, fill="#010a0a", outline="")
        # Alt çizgi — teal parlak
        c.create_line(0, HDR_H, W, HDR_H, fill=C_MID, width=1)
        for i in range(3):
            a = 60 - i * 18
            c.create_line(0, HDR_H-1-i, W, HDR_H-1-i,
                          fill=self._ac(0, 180, 165, a), width=1)

        # Sistem uyarısı (header altında)
        self._draw_system_alert(c)

        # Büyük başlık
        c.create_text(W//2, 24, text=SYSTEM_NAME,
                      fill=C_PRI, font=font_display(26))
        c.create_text(W//2, 52, text="Just A Rather Very Intelligent System",
                      fill=C_MID, font=font_body(11))

        # Sol: model badge
        c.create_text(22, 36, text=MODEL_BADGE,
                      fill=C_DIM, font=font_body(10), anchor="w")

        # Sağ: durum indikatörü
        indicator_state = "PAUSED" if self.paused else self._jarvis_state
        ind_col = self._state_color(indicator_state)
        indicator_text = self._state_badge_text(indicator_state)
        sym = "●" if self.status_blink else "○"
        c.create_text(W-22, 36, text=f"{sym}  {indicator_text}",
                      fill=ind_col, font=font_body_bold(11), anchor="e")

        # ── FOOTER ───────────────────────────────────────────────────────────
        c.create_rectangle(0, H-FOOTER_H, W, H, fill="#010a0a", outline="")
        c.create_line(0, H-FOOTER_H, W, H-FOOTER_H, fill=C_DIM, width=1)
        c.create_text(W//2, H-13, fill=C_DIM, font=font_body(9),
                      text="JARVIS · Windows Edition · Realtime Voice Core")
        c.create_text(W-18, H-13, fill=C_DIM, font=font_body(9),
                      text="[F4] MUTE  [F5] PAUSE  [ESC] EXIT", anchor="e")

    # ── (Setup dialog extracted to ui/setup_dialog.py) ─────────────────────
