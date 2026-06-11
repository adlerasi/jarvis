# UI / Arayüz Katmanı

## UI Mimarisi

JARVIS birincil olarak **Tkinter Desktop UI** kullanır. İkincil olarak **web_ui.py** ile opsiyonel web arayüzü sunar.

```
┌─────────────────────────────────────────────────────────────────┐
│                        UI KATMANI                                │
│                                                                  │
│  JarvisUI (ui.py)                    web_ui.py                   │
│  ├── Tkinter Toplevel                ├── HTTP Server             │
│  ├── Konsantrik halka                ├── WebSocket               │
│  ├── Panel sistemi                   └── HTML/JS frontend        │
│  ├── SoundManager                                               │
│  └── SetupDialog                                               │
│         │                                                       │
│         ▼ IPC: _gui_queue (thread-safe queue)                   │
│         ▼ Callback: on_text_command, on_pause_toggle            │
└─────────────────────────────────────────────────────────────────┘
```

### Bileşen Haritası

| Bileşen | Dosya | Amaç | Veri Bağlantısı |
|---------|-------|------|-----------------|
| JarvisUI | `ui.py` (1818 satır) | Ana Tkinter penceresi | `_gui_queue`, callbacks |
| OrbCanvas | `ui/orb_canvas.py` | Konsantrik halka animasyonu | `set_state()` |
| SoundManager | `ui/sound_manager.py` | Ses efektleri (SFX) | `_sync_sound_state()` |
| SetupDialog | `ui/setup_dialog.py` | İlk kurulum sihirbazı | `config/api_keys.json` |
| draw_utils | `ui/draw_utils.py` | Canvas çizim yardımcıları | OrbCanvas |
| text_utils | `ui/text_utils.py` | Metin işleme (UI) | Panel render |
| theme | `ui/theme.py` | Renk, font, boyut sabitleri | Tüm UI bileşenleri |
| Web UI | `web_ui.py` | HTTP tabanlı web arayüzü | HTTP/WebSocket |

## Ekranlar / View'lar

### Ana Pencere (2200×1320)

```
┌────────────────────────────────────────────────────────────────────┐
│ HEADER (HDR_H=72px)                                                │
│ [Logo] [Durum Orb] [Panel butonları]                               │
├──────────┬────────────────────────────────────┬────────────────────┤
│ SOL      │           ORTA                      │     SAĞ            │
│ PANEL    │                                    │     PANEL           │
│ (360px)  │   Konsantrik Halka (OrbCanvas)     │     (410px)         │
│          │                                    │                     │
│ Hava     │   ┌──────────────────────────┐     │  Log Panel          │
│ durumu   │   │      ╭────────────────╮   │     │  Debug Panel        │
│          │   │     ╱  ╭──────────╮   ╲    │     │  Settings Sekmesi  │
│ Sistem   │   │    │  ╱  ╭────╮  ╲  │   │     │                     │
│ bilgisi  │   │    │ │  │ DURUM│  │ │   │     │                     │
│          │   │    │  ╲  ╰────╯  ╱  │   │     │                     │
│ Zaman    │   │     ╲  ╰──────────╯  ╱    │     │                     │
│          │   │      ╰──────────────────╯     │     │                     │
│          │   └──────────────────────────┘     │                     │
│          │   [Durum Metni] [Mikrofon Butonu]  │                     │
├──────────┴────────────────────────────────────┴────────────────────┤
│ INPUT ÇUBUĞU (INPUT_H=34px)                                        │
│ [Metin girişi alanı]                                               │
├────────────────────────────────────────────────────────────────────┤
│ KONTROL PANELİ (CONTROL_H=146px)                                   │
│ [Mute/Unmute] [Duraklat/Devam] [Ses efekti geçişi]                │
├────────────────────────────────────────────────────────────────────┤
│ FOOTER (FOOTER_H=26px) — Platform bilgisi · Sosyal medya ikonları │
└────────────────────────────────────────────────────────────────────┘
```

### Konsantrik Halka (OrbCanvas)

OrbCanvas, JARVIS'in en belirgin UI öğesidir. 3 katmanlı dairesel animasyon:

- **İç halka:** Statik, merkez nokta — canlı olduğunu gösterir
- **Orta halka:** Dönen segmentler — state'e göre renk değiştirir
- **Dış halka:** Durum rengiyle yanıp söner

```python
# ui/orb_canvas.py — Ana çizim metodu
def draw(self):
    self.delete("orb")
    cx, cy = self._center
    # İç halka (sabit)
    self.create_oval(cx-15, cy-15, cx+15, cy+15, fill=color, tag="orb")
    # Orta halka (dönen segmentler)
    for i in range(segments):
        angle = start + i * step
        # ... arc çizimi
    # Dış halka (durum)
    self.create_oval(cx-r, cy-r, cx+r, cy+r, outline=color, width=2, tag="orb")
```

### Durum Renkleri

| State | Renk (Hex) | Açıklama |
|-------|-----------|----------|
| LISTENING | `#00ff88` Yeşil | Mikrofon açık, dinliyor |
| SPEAKING | `#4488ff` Mavi | JARVIS konuşuyor |
| THINKING | `#ffcc00` Altın | İşlem yapılıyor |
| ERROR | `#ff3344` Kırmızı | Hata oluştu |
| MUTED | `#cc2255` Koyu pembe | Ses kapalı |
| PAUSED | `#1e3c37` Koyu teal | Duraklatıldı |
| INITIALISING | `#8866ff` Mor | Başlangıç |

## UI ↔ Backend İletişimi

### Thread-safe Kuyruk (`_gui_queue`)

```python
# ui.py — Kuyruktan mesaj oku
def process_gui_queue(self):
    try:
        while True:
            msg = self._gui_queue.get_nowait()
            msg_type = msg.get("type")
            if msg_type == "state":
                self.set_state(msg["state"])
            elif msg_type == "log":
                self.write_log(msg["text"])
            elif msg_type == "debug":
                self.write_debug(msg["text"])
            elif msg_type == "panel":
                self._focus_panel(msg.get("panel"))
    except queue.Empty:
        pass
    finally:
        self.root.after(50, self.process_gui_queue)
```

### Callback Mekanizması

```python
# main.py — UI callback'leri bağlama
def _init_ui(self):
    ui = JarvisUI()
    ui.on_text_command = self._on_text_command    # Metin komutu
    ui.on_pause_toggle = self._on_pause_toggle    # Duraklat
    ui.on_effects_state_change = self._on_effects_state_change
    ui.on_agent_approval = self._on_agent_approval  # ACA onay
    ui.on_user_spoke = self._on_user_spoke
```

| Callback | Yön | Veri |
|----------|-----|------|
| `on_text_command(text)` | UI → Backend | Kullanıcı metni |
| `on_pause_toggle()` | UI → Backend | Boolean toggle |
| `on_effects_state_change(state)` | UI → Backend | Efekt durumu |
| `on_agent_approval(action, risk)` | UI → Backend | Onay kararı |
| `set_state(state)` | Backend → UI | State güncelleme |
| `write_log(text)` | Backend → UI | Log mesajı |
| `write_debug(text)` | Backend → UI | Debug mesajı |

## Sesli Arayüz Entegrasyonu

```
┌───────────────────────────────────────────────┐
│              SES DURUMU → UI                   │
│                                                │
│  Mikrofon active → Orb yeşil yanıp söner      │
│  JARVIS konuşuyor → Orb mavi, ses dalgası     │
│  İşlem yapılıyor → Orb altın, dönen segmentler│
│  Hata → Orb kırmızı, titreme efekti           │
└───────────────────────────────────────────────┘
```

### Setup Dialog (İlk Çalıştırma)

```python
# ui/setup_dialog.py
class SetupDialog:
    """İlk çalıştırmada API anahtarı girişi için dialog."""
    def __init__(self):
        self.root = tk.Toplevel()
        # Backend seçimi: Gemini / Ollama
        # API anahtarı girişi (Gemini)
        # Ollama model seçimi
        # TTS ses seçimi
```

## State → UI Binding

### State Makinesi Binding

```python
def set_state(self, new_state: str):
    """State değişikliğini UI'a yansıt."""
    # 1. State'i güncelle
    old_state = self._state
    self._state = new_state
    
    # 2. Orb rengini güncelle
    hex_color = STATE_HEX_COLORS.get(new_state, "#ffffff")
    self._set_orb_color(hex_color)
    
    # 3. Durum metnini güncelle
    labels = {
        "LISTENING": "Dinliyor...",
        "SPEAKING": "Yanıtlıyor...",
        "THINKING": "İşlem yapılıyor...",
        "ERROR": "Hata oluştu",
        "PAUSED": "Duraklatıldı",
        "MUTED": "Sessiz",
    }
    self._status_label.config(text=labels.get(new_state, ""))
    
    # 4. Geçiş validasyonu (VALID_TRANSITIONS)
    if new_state in _VALID_TRANSITIONS.get(old_state, []):
        self._animate_transition(old_state, new_state)
```

### Arkaplan Servis Göstergeleri

UI ayrıca arka plan servislerinin durumunu da gösterir:

| Bileşen | UI'da Nerede | Nasıl Güncellenir |
|---------|--------------|-------------------|
| Ses seviyesi | Kontrol paneli | `set_volume()` callback |
| Mikrofon durumu | Orb-canvas | `_on_user_spoke()` |
| Sistem bilgisi | Sol panel | `sys_info()` periyodik |
| Log | Sağ panel | `write_log()` |
| Debug | Sağ panel | `write_debug()` |

## Web UI (`web_ui.py`)

Opsiyonel web arayüzü, HTTP sunucusu üzerinden JARVIS'e erişim sağlar:

- **Port:** 8765 (varsayılan)
- **Teknoloji:** Python `http.server` + HTML/JS frontend
- **Özellikler:** 
  - Chat arayüzü
  - Durum göstergesi
  - Komut girişi
  - Yanıt görüntüleme

[Bkz. ARCHITECTURE.md](ARCHITECTURE.md) | [Bkz. STT_TTS.md](STT_TTS.md) | [Bkz. STATE_MANAGEMENT.md](STATE_MANAGEMENT.md)
