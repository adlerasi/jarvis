# UI Refactor — Faz 1: ui.py → Modüllere Bölünmesi

> **Durum: 🔴 HENÜZ UYGULANMADI** — `ui.py` (1800+ satir) henüz modüllere ayrilmamistir.  
> Bu doküman hedef mimariyi tanimlar. Uygulama için REFACTORING_GUIDE.md'deki Faz 3'e bakin.

> Bu doküman `REFACTOR_COMMAND_UI.md`'nin Faz 1 bölümüdür.
> Bkz. [UI_REFACTOR_GUIDE.md](UI_REFACTOR_GUIDE.md) — kurallar ve strateji
> Bkz. [UI_REFACTOR_PHASE2.md](UI_REFACTOR_PHASE2.md) — health.py refactor

## 📏 KURAL: MAKSİMUM DOSYA SATIR SAYISI

| Dosya Tipi | Maksimum Satır | Açıklama |
|-----------|---------------|----------|
| `__init__.py` (facade) | **80 satır** | Sadece public API delegate |
| Bileşen sınıfı (Button, Panel, Card) | **120 satır** | Tek sorumluluk |
| Yardımcı modül (utils, parser, config) | **100 satır** | Saf fonksiyonlar |
| Test dosyası | **150 satır** | Bir test senaryosu |
| Koordinatör/Manager | **150 satır** | Birden fazla bileşeni yönetir |
| **KESİN KURAL** | **200 satır** | Hiçbir dosya 200 satırı geçemez |

> **İHLAL EDİLİRSE:** Ajan dosyayı tekrar parçalamak zorundadır.

---

## 🔴 FAZ 1: ui.py → 12 Modüle Bölünmesi

### 1.1 `ui/__init__.py` (Facade, max 80 satır)

```python
"""JARVIS UI — Public API Facade."""
from __future__ import annotations

from .main_window import MainWindow
from .layout import LayoutManager
from .components.input_bar import InputBar
from .components.base_button import BracketButton
from .panels.left_panel import LeftPanel
from .panels.right_panel import RightPanel
from .panels.agent_panel import AgentPanel
from .panels.settings_panel import SettingsPanel
from .animation.animator import Animator
from .sound_manager import SoundManager
from .orb_canvas import OrbCanvas
from .theme import C_BG

__all__ = ["JarvisUI"]

class JarvisUI:
    """JARVIS UI Facade — tüm bileşenleri koordine eder."""

    def __init__(self):
        self._window = MainWindow()
        self._layout = LayoutManager(self._window.root)
        self._sound = SoundManager()
        self._animator = Animator(self)
        self._setup_callbacks()

    def _setup_callbacks(self):
        self._layout.input_bar.on_submit = self._on_text_command
        self._layout.mute_btn.on_click = self._toggle_mute
        self._layout.pause_btn.on_click = self._toggle_pause

    # Public API — tüm eski metodlar delegate
    def set_state(self, state: str): self._animator.set_state(state)
    def write_log(self, text: str): self._layout.right_panel.log.add(text)
    def set_user_speaking(self, value: bool): self._animator.set_user_speaking(value)
    def show_health_hologram(self, query: str, data: str): 
        self._layout.left_panel.show_health_overlay(query, data)
    def show_system_alert(self, msg: str, duration: int = 10):
        self._layout.system_alert.show(msg, duration)
    def set_mic_level(self, level: float): self._layout.right_panel.set_mic_level(level)
    def play_success_sfx(self): self._sound.play_success()
    def play_error_sfx(self): self._sound.play_error()
    def focus_panel(self, section: str, duration_ms: int = 4200):
        self._layout.focus_panel(section, duration_ms)
    def destroy(self): self._window.destroy()

    # Callbacks (dışarıdan set edilir)
    on_text_command = None
    on_pause_toggle = None
    on_stop_command = None
    on_voice_change = None
    on_effects_state_change = None
    on_agent_approval = None
    on_approval_mode_toggle = None
    on_config_change = None

    def _on_text_command(self, text: str):
        if self.on_text_command:
            import threading
            threading.Thread(target=self.on_text_command, args=(text,), daemon=True).start()

    def _toggle_mute(self):
        pass  # delegate to layout

    def _toggle_pause(self):
        pass  # delegate to layout
```

### 1.2 `ui/main_window.py` (max 120 satır)

```python
"""Tkinter pencere yönetimi — geometry, fullscreen, resize."""
from __future__ import annotations
import tkinter as tk
from .theme import C_BG

class MainWindow:
    """Ana pencere — Tkinter root wrapper."""
    def __init__(self):
        self.root = tk.Tk()
        self.root.configure(bg=C_BG)
        self.root.title("JARVIS")
        self.root.overrideredirect(True)
        self._setup_geometry()

    def _setup_geometry(self):
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        if hasattr(self.root, 'attributes'):
            self.root.attributes('-fullscreen', False)
        self.root.geometry(f"{w}x{h}+0+0")

    def set_fullscreen(self, fullscreen: bool):
        self.root.attributes('-fullscreen', fullscreen)

    def destroy(self):
        self.root.destroy()
```

### 1.3 `ui/components/base_button.py` (max 120 satır)

```python
"""Temel buton bileşeni — hover efektli, özelleştirilebilir."""
from __future__ import annotations
import tkinter as tk

class HoverButton(tk.Canvas):
    """Hover efekti olan tıklanabilir buton."""
    def __init__(self, parent, text="", command=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._text = text
        self._command = command
        self._hovered = False
        self._setup_bindings()

    def _setup_bindings(self):
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _on_enter(self, e): self._hovered = True; self._redraw()
    def _on_leave(self, e): self._hovered = False; self._redraw()
    def _on_click(self, e):
        if self._command:
            self._command()

    def _redraw(self):
        self.delete("all")
        bg = "#3a3a4a" if self._hovered else "#2a2a3a"
        self.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(),
                              fill=bg, outline="")
        self.create_text(self.winfo_width()//2, self.winfo_height()//2,
                         text=self._text, fill="white")

class BracketButton(HoverButton):
    """Köşeli parantez içinde buton: [ Buton ]"""
    def _redraw(self):
        self.delete("all")
        bg = "#3a3a4a" if self._hovered else "transparent"
        display = f"[ {self._text} ]"
        self.create_text(self.winfo_width()//2, self.winfo_height()//2,
                         text=display, fill="#00ff88" if self._hovered else "#888",
                         font=("Consolas", 11))
```

### 1.4 `ui/components/input_bar.py` (max 100 satır)

```python
"""Metin giriş çubuğu — kullanıcı yazılı komut girişi."""
from __future__ import annotations
import tkinter as tk

class InputBar(tk.Frame):
    def __init__(self, parent, on_submit=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_submit = on_submit
        self._entry = tk.Entry(self, font=("Consolas", 14), bg="#1a1a2a",
                               fg="white", insertbackground="white",
                               relief=tk.FLAT, bd=0)
        self._entry.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self._entry.bind("<Return>", self._on_submit)

    def _on_submit(self, e):
        text = self._entry.get().strip()
        if text and self.on_submit:
            self._entry.delete(0, tk.END)
            self.on_submit(text)

    def focus(self):
        self._entry.focus_set()
```

### 1.5 `ui/components/volume_slider.py` (max 80 satır)

```python
"""Ses seviyesi kaydırıcısı."""
from __future__ import annotations
import tkinter as tk

class VolumeSlider(tk.Frame):
    def __init__(self, parent, initial=0.5, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._value = initial
        self.on_change = on_change
        self._slider = tk.Scale(self, from_=0, to=100, orient=tk.HORIZONTAL,
                                command=self._on_change, showvalue=False,
                                bg="#1a1a2a", fg="white", troughcolor="#2a2a3a",
                                highlightthickness=0)
        self._slider.set(initial * 100)
        self._slider.pack(fill=tk.X, padx=5)

    def _on_change(self, val):
        self._value = int(val) / 100
        if self.on_change:
            self.on_change(self._value)

    @property
    def value(self): return self._value
    def set(self, v): self._slider.set(v * 100); self._value = v
```

### 1.6 `ui/components/voice_selector.py` (max 80 satır)

```python
"""Ses seçici — farklı TTS sesleri arasında geçiş."""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk

class VoiceSelector(tk.Frame):
    def __init__(self, parent, voices=None, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.on_change = on_change
        self._voices = voices or ["piper-fahrettin", "piper-default"]
        self._combo = ttk.Combobox(self, values=self._voices, state="readonly",
                                   font=("Consolas", 10))
        self._combo.set(self._voices[0])
        self._combo.pack(fill=tk.X, padx=5, pady=2)
        self._combo.bind("<<ComboboxSelected>>", self._on_select)

    def _on_select(self, e):
        if self.on_change:
            self.on_change(self._combo.get())
```

### 1.7 `ui/panels/left_panel.py` (max 120 satır)

```python
"""Sol panel — sistem bilgileri, hologram, durum kartları."""
from __future__ import annotations
import tkinter as tk
from .cards.time_card import TimeCard
from .cards.weather_card import WeatherCard
from .cards.system_card import SystemCard
from .cards.health_card import HealthCard

class LeftPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#1a1a2a")
        self.time_card = TimeCard(self)
        self.weather_card = WeatherCard(self)
        self.system_card = SystemCard(self)
        self.health_card = HealthCard(self)
        self._health_overlay = None
        self._pack_cards()

    def _pack_cards(self):
        self.time_card.pack(fill=tk.X, padx=5, pady=2)
        self.weather_card.pack(fill=tk.X, padx=5, pady=2)
        self.system_card.pack(fill=tk.X, padx=5, pady=2)
        self.health_card.pack(fill=tk.X, padx=5, pady=2)

    def show_health_overlay(self, query: str, data: str):
        self.health_card.show_overlay(query, data)
```

### 1.8 `ui/panels/cards/base_card.py` (max 80 satır)

```python
"""Temel kart bileşeni — hologram tarzı bilgi kartı."""
from __future__ import annotations
import tkinter as tk

class BaseCard(tk.Frame):
    def __init__(self, parent, title="", **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#12121e", highlightbackground="#2a2a3a",
                       highlightthickness=1)
        self._title = title
        self._title_label = tk.Label(self, text=title, font=("Consolas", 9, "bold"),
                                     fg="#00ff88", bg="#12121e", anchor="w")
        self._title_label.pack(fill=tk.X, padx=8, pady=(4, 0))
        self._body = tk.Frame(self, bg="#12121e")
        self._body.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    def clear_body(self):
        for w in self._body.winfo_children():
            w.destroy()

    def set_body_text(self, text: str, fg="#aaa"):
        self.clear_body()
        tk.Label(self._body, text=text, font=("Consolas", 11),
                 fg=fg, bg="#12121e", justify="left",
                 wraplength=280).pack(anchor="w")
```

### 1.9 `ui/panels/cards/time_card.py` (max 60 satır)

```python
"""Saat/tarih kartı."""
from __future__ import annotations
import tkinter as tk
import time
from .base_card import BaseCard

class TimeCard(BaseCard):
    def __init__(self, parent):
        super().__init__(parent, title="⏰ ZAMAN")
        self._time_label = tk.Label(self._body, font=("Consolas", 20, "bold"),
                                     fg="white", bg="#12121e")
        self._time_label.pack()
        self._date_label = tk.Label(self._body, font=("Consolas", 10),
                                     fg="#888", bg="#12121e")
        self._date_label.pack()
        self._update()

    def _update(self):
        now = time.localtime()
        self._time_label.config(text=time.strftime("%H:%M:%S", now))
        self._date_label.config(text=time.strftime("%A, %d %B %Y", now))
        self.after(1000, self._update)
```

### 1.10 `ui/panels/cards/weather_card.py` (max 60 satır)

```python
"""Hava durumu kartı."""
from __future__ import annotations
import tkinter as tk
from .base_card import BaseCard

class WeatherCard(BaseCard):
    def __init__(self, parent):
        super().__init__(parent, title="🌤 HAVA")
        self._label = tk.Label(self._body, text="Yükleniyor...",
                                font=("Consolas", 12), fg="white", bg="#12121e")
        self._label.pack(anchor="w")

    def set_weather(self, text: str):
        self._label.config(text=text)
```

### 1.11 `ui/panels/cards/system_card.py` (max 100 satır)

```python
"""Sistem durumu kartı — CPU, RAM, disk, uptime."""
from __future__ import annotations
import tkinter as tk
from .base_card import BaseCard

class SystemCard(BaseCard):
    def __init__(self, parent):
        super().__init__(parent, title="💻 SISTEM")
        self._lines = []
        for _ in range(5):
            lbl = tk.Label(self._body, font=("Consolas", 10), fg="#aaa",
                           bg="#12121e", anchor="w")
            lbl.pack(fill=tk.X)
            self._lines.append(lbl)

    def update_stats(self, cpu, mem, disk, temp, uptime):
        data = [
            f"CPU:  {cpu}%",
            f"RAM:  {mem}%",
            f"DISK: {disk}%",
            f"ISIsi: {temp}°C" if temp else "ISIsi: N/A",
            f"Acik: {uptime}",
        ]
        for lbl, text in zip(self._lines, data):
            lbl.config(text=text)
            lbl.config(fg="#ff6b6b" if "%" in text and any(
                int(text.split()[-1].rstrip("%")) > 80 
                for part in text.split(":") 
                if part.strip().rstrip("%").isdigit()
            ) else "#aaa")
```

### 1.12 `ui/panels/cards/health_card.py` (max 50 satır)

```python
"""Sağlık verisi kartı — günlük sağlık özeti."""
from __future__ import annotations
from .base_card import BaseCard

class HealthCard(BaseCard):
    def __init__(self, parent):
        super().__init__(parent, title="❤️ SAGLIK")
        self._overlay = None

    def show_overlay(self, query: str, data: str):
        self.set_body_text(data)
```

### 1.13 `ui/panels/right_panel.py` (max 100 satır)

```python
"""Sağ panel — log, mikrofon seviyesi, butonlar."""
from __future__ import annotations
import tkinter as tk

class RightPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#1a1a2a")
        self.log = self._create_log()
        self.mic_level = None
        self._create_controls()

    def _create_log(self):
        text = tk.Text(self, font=("Consolas", 9), bg="#0a0a1a", fg="#aaa",
                       relief=tk.FLAT, wrap=tk.WORD, state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        return text

    def _create_controls(self):
        frame = tk.Frame(self, bg="#1a1a2a")
        frame.pack(fill=tk.X, padx=5, pady=2)
        self.mic_label = tk.Label(frame, text="MIC: --", font=("Consolas", 9),
                                   fg="#888", bg="#1a1a2a")
        self.mic_label.pack(side=tk.LEFT)

    def set_mic_level(self, level: float):
        if self.mic_label:
            self.mic_label.config(text=f"MIC: {level:.0%}")
```

### 1.14 `ui/panels/agent_panel.py` (max 120 satır)

```python
"""ACA Agent durum paneli — goal takibi, onay butonları."""
from __future__ import annotations
import tkinter as tk

class AgentPanel(tk.Frame):
    def __init__(self, parent, on_approve=None, on_reject=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#12121e")
        self.on_approve = on_approve
        self.on_reject = on_reject
        self._goal_label = tk.Label(self, text="", font=("Consolas", 10),
                                     fg="#00ff88", bg="#12121e", wraplength=300)
        self._goal_label.pack(fill=tk.X, padx=5, pady=2)
        self._status_label = tk.Label(self, text="", font=("Consolas", 9),
                                       fg="#aaa", bg="#12121e")
        self._status_label.pack(fill=tk.X, padx=5, pady=2)
        self._btn_frame = tk.Frame(self, bg="#12121e")
        self._btn_frame.pack()

    def show_goal(self, goal_text: str):
        self._goal_label.config(text=f"🎯 {goal_text}")

    def show_status(self, status: str):
        self._status_label.config(text=status)

    def show_approval(self, action: str, callback):
        self._goal_label.config(text=f"⚠️ Onay: {action}")
        # Onay/Red butonları göster
```

### 1.15 `ui/panels/settings_panel.py` (max 120 satır)

```python
"""Ayarlar paneli — ses, mikrofon, backend seçimi."""
from __future__ import annotations
import tkinter as tk

class SettingsPanel(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(bg="#12121e")
        self._create_widgets()

    def _create_widgets(self):
        tk.Label(self, text="Ayarlar", font=("Consolas", 12, "bold"),
                 fg="#00ff88", bg="#12121e").pack(pady=5)
```

### 1.16 `ui/animation/animator.py` (max 120 satır)

```python
"""Animasyon motoru — durum geçişleri, Orb animasyonu."""
from __future__ import annotations
from .background import BackgroundAnimation

class Animator:
    def __init__(self, ui):
        self._ui = ui
        self._orb = None
        self._background = BackgroundAnimation()
        self._state = "LISTENING"

    def set_state(self, state: str):
        self._state = state
        # Orb rengini/animasyonunu güncelle

    def set_user_speaking(self, value: bool):
        pass  # Mikrofon animasyonu
```

### 1.17 `ui/animation/background.py` (max 80 satır)

```python
"""Arka plan animasyonu — parçacık sistemi."""
from __future__ import annotations

class BackgroundAnimation:
    def __init__(self):
        self._particles = []
        self._running = False

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def update(self):
        if not self._running:
            return
        # Parçacık konumlarını güncelle
```

### 1.18 `ui/layout.py` (max 120 satır)

```python
"""Layout yöneticisi — panel yerleşimi, focus yönetimi."""
from __future__ import annotations
import tkinter as tk
from .panels.left_panel import LeftPanel
from .panels.right_panel import RightPanel
from .panels.system_alert import SystemAlert
from .components.input_bar import InputBar
from .components.base_button import BracketButton

class LayoutManager:
    def __init__(self, root):
        self.root = root
        self._create_layout()

    def _create_layout(self):
        # Ana grid: left | center | right
        self.left_panel = LeftPanel(self.root)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        center = tk.Frame(self.root, bg="#0a0a1a")
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.right_panel = RightPanel(self.root)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Alt çubuk
        bottom = tk.Frame(center, bg="#1a1a2a")
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.input_bar = InputBar(bottom)
        self.input_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.mute_btn = BracketButton(bottom, text="Mute")
        self.mute_btn.pack(side=tk.RIGHT, padx=2)

        self.pause_btn = BracketButton(bottom, text="Pause")
        self.pause_btn.pack(side=tk.RIGHT, padx=2)

        # OrbCanvas (center'da)
        from .orb_canvas import OrbCanvas
        self.orb = OrbCanvas(center)
        self.orb.pack(fill=tk.BOTH, expand=True)

        # System alert (en üstte)
        self.system_alert = SystemAlert(self.root)

    def focus_panel(self, section: str, duration_ms: int = 4200):
        pass  # Panel focus animasyonu
```
