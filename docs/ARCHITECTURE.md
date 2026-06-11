# JARVIS Mimarisi

## Genel Bakış

JARVIS, **çift backend** mimarisiyle çalışan, gerçek zamanlı sesli asistandır.  
Birincil backend **Google Gemini AI Audio API**, ikincil backend ise **Ollama** (yerel)dir.

```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS Çekirdeği                        │
│                        main.py                               │
│                     JarvisLive sınıfı                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Gemini AI   │    │   Ollama     │    │    Tkinter   │   │
│  │  (bulut)     │    │  (yerel)     │    │    UI (ui.py)│   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Action Modülleri (actions/)              │   │
│  │  open_app  sys_info  weather  calendar  reminders    │   │
│  │  browser   shell    whatsapp  media   youtube_stats  │   │
│  │  screen_vision  tts  windows_utils  health           │   │
│  │  system_doctor  process_manager  file_guardian      │   │
│  │  network_monitor  system_cron  service_monitor       │   │
│  │  [disk_predictor] [process_timeline] [net_anomaly]  │   │
│  │  [cron_web_ui] [watchdog/file_watcher]              │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Ses İşleme (audio/)                         │   │
│  │  noise_suppressor.py  RNNoise gürültü bastırma        │   │
│  │  microphone.py         SoundDevice mikrofon akışı     │   │
│  │  lib/librnnoise.so    RNNoise C kütüphanesi           │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Skill Modülleri (skills/)                   │   │
│  │  browser/         browser_skill.py  (tarayıcı)        │   │
│  │  system_health/   system_health_skill.py  (sistem)     │   │
│  │  process_control/ process_control_skill.py  (süreç)    │   │
│  │  file_manager/    file_manager_skill.py  (dosya)       │   │
│  │  weather/         weather_skill.py  (hava durumu)      │   │
│  │  youtube/         youtube_skill.py  (YouTube)          │   │
│  │  vision/          vision_skill.py  (ekran analizi)     │   │
│  │  calendar/        calendar_skill.py  (takvim)          │   │
│  │  reminders/       reminders_skill.py  (hatırlatıcı)    │   │
│  │  whatsapp/        whatsapp_skill.py  (WhatsApp)        │   │
│  │  media/           media_skill.py  (medya oynatma)      │   │
│  │  network/         network_skill.py  (ağ izleme)        │   │
│  │  scheduler/       scheduler_skill.py  (zamanlanmış)    │   │
│  │  services/        services_skill.py  (servis yönetimi) │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │    Bellek     │    │  Yapılandırma│                       │
│  │ memory/       │    │  config/     │                       │
│  └──────────────┘    └──────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 Çekirdek Mimarisi

### JarvisLive Sınıfı (`main.py`) — Provider Abstraction Pattern

Ana controller sınıfı, **provider abstraction** ile backend'lerden bağımsız çalışır:

```
JarvisLive
├── __init__()          → UI callback'leri bağlar, durum değişkenlerini kurar
│                       → _user_initiated = False
│                       → skill_manager = get_skill_manager()
│
├── run()              → Ana döngü: backend seçimi, provider oluşturma, bağlanma
│   ├── GeminiProvider (Live API — ses akışı + tool calls)
│   └── OllamaProvider (HTTP Chat — VAD/STT + TTS)
│
├── _execute_tool()    → Tool çağrılarını action modüllerine yönlendirir
│                      → TOOL_HANDLER_MAP (tool_registry.py) ile dict dispatch
│
├── set_speaking()     → Konuşma durumunu yönetir (thread-safe)
├── _interrupt_audio() → Ses akışını keser
│
├── _on_text_command() → Metin komutlarını işler, _user_initiated = True yapar
│                      → Önce skill_manager.route() dener, eşleşirse direkt çalıştırır
│                      → Eşleşmezse provider.send_text() ile LLM'e iletir
├── _on_pause_toggle() → Duraklatma durumunu yönetir
├── _on_effects_state_change() → Ses efektleri durumunu yönetir
│
└── _focus_ui_section_for_tool() → UI panel odağını yönetir

#### Sistem Kontrol Handler'ları (main.py sonu)
```
_handle_get_system_health()    → system_doctor.get_system_health()
_handle_cleanup_temp_files()   → system_doctor.cleanup_temp_files()
_handle_cleanup_recycle_bin()  → system_doctor.cleanup_recycle_bin()
_handle_list_processes()       → process_manager.list_processes()
_handle_kill_process()         → process_manager.kill_process()
_handle_set_process_priority() → process_manager.set_process_priority()
_handle_find_process_by_port() → process_manager.find_process_by_port()
_handle_find_large_files()     → file_guardian.find_large_files()
_handle_find_duplicate_files() → file_guardian.find_duplicate_files()
_handle_cleanup_folder()       → file_guardian.cleanup_folder()
_handle_get_folder_summary()   → file_guardian.get_folder_summary()
_handle_get_network_summary()  → network_monitor.get_network_summary()
_handle_list_net_connections() → network_monitor.list_connections()
_handle_ping_host()            → network_monitor.ping_host()
_handle_add_cron_job()         → system_cron.add_cron_job()
_handle_list_cron_jobs()       → system_cron.list_cron_jobs()
_handle_remove_cron_job()      → system_cron.remove_cron_job()
_handle_list_services()        → service_monitor.list_services()
_handle_control_service()      → service_monitor.control_service()
_handle_set_volume()           → windows_utils.set_volume() (pactl/osascript/nircmd)
_handle_browser_skill()        → skills.browser.browser_skill (AI tool çağrısı için)
```

#### Arka Plan Servisleri (main.py __init__ sonu)
```
start_cron_daemon()            → system_cron cron döngüsü
FileWatcher(paths, ui)         → watchdog/file_watcher.py dosya izleme
ProcessTimeline().poll()       → process_timeline.py süreç zaman çizelgesi
CronWebServer(port=8765)       → cron_web_ui.py web arayüzü
DiskPredictor().record_sample()→ disk_predictor.py (6 saatte bir cron)
NetworkAnomalyDetector().scan()→ network_anomaly.py (2 dakikada bir cron)
```
```

### Thread Modeli

```
Ana Thread (main.py)
└── run() → asyncio event loop (ana döngü)
    ├── Provider seçimi (config → Gemini / Ollama)
    │
    ├── Gemini modu — TaskGroup (4 eşzamanlı coroutine)
    │   ├── _send_realtime()   → ses gönderme (out_queue → Gemini)
    │   ├── _listen_audio()    → ses alma (mikrofon → out_queue + local modüller)
    │   ├── _receive_audio()   → yanıt işleme (tool calls + transcription)
    │   └── _play_audio()      → ses çalma (audio_in_queue → hoparlör)
    │
    ├── Ollama modu — async loop
    │   ├── _stt_listen_loop()     → VAD + faster-whisper (PyAudio task)
    │   ├── _stt_fallback_listen() → speech_recognition yedek STT
    │   └── input_queue → _ollama_chat() → TTS
    │
    ├── UI Thread (Tkinter mainloop)
    │   ├── _sync_sound_state() → ses durumu senkronizasyonu
    │   └── _animate_orb()     → halka animasyonu (after())
    │
    └── Arka Plan Thread'leri
        ├── FileWatcher         → dosya sistemi izleme (watchdog/polling)
        ├── ProcessTimeline     → süreç zaman çizelgesi (5sn polling)
        ├── CronWebServer       → HTTP sunucu (port 8765)
        ├── DiskPredictor       → disk örnekleme (6 saat)
        └── NetworkAnomaly      → ağ taraması (2 dk)
```

**Önemli**: Ses akışı PortAudio üzerinden yapılır. Thread race condition'larını önlemek için giriş/çıkış stream'leri sırayla (sequential) açılır.

---

## 🔄 Ses Akışı

### Gemini Backend

```
Mikrofon → pyaudio (16kHz, paInt16, mono) 
         → out_queue (asyncio.Queue, maxsize=10)
         → Gemini Live API (send_realtime_input)
         │
         ← Gemini Live API (receive)
         → audio_in_queue (asyncio.Queue)
         → pyaudio (24kHz, paInt16, mono)
         → Hoparlör
```

### Ollama Backend

```
Mikrofon → SpeechRecognition (Google STT) 
         → Faster-Whisper (fallback, offline)
         → RNNoise (noise_suppressor.py):
             1. 16kHz → 48kHz upsampling (zero-order hold)
             2. RNNoise C kütüphanesi ile gürültü bastırma
             3. 48kHz → 16kHz downsampling
             4. VAD probability çıktısı
         → clean_transcript_text() (text_utils):
              1. unicodedata.normalize("NFC") — decomposed Türkçe karakter düzeltmesi
              2. fix_turkish_syllable_split() — faster-whisper hece bölmesi birleştirme
         → VAD (Voice Activity Detection)
         → Ollama API (HTTP /api/chat)
         → TTS Zinciri:
             1. Piper (yerel, offline)
             2. Edge-TTS (bulut, Microsoft Neural)
             3. spd-say (son fallback)
         → subprocess (aplay/mpg123)
         → Hoparlör
```

---

## 🎨 UI Mimarisi

### Tkinter UI (`ui.py`)

```
JarvisUI (Tkinter.Toplevel)
├── Ana Pencere (2200×1320)
│   ├── Header (HDR_H=72px)
│   │   ├── Logo / Sistem adı
│   │   ├── Durum göstergesi (orb)
│   │   └── Panel yönlendirme
│   │
│   ├── Sol Panel (LEFT_W_T=360px)
│   │   ├── Hava durumu
│   │   ├── Sistem bilgisi
│   │   └── Zaman
│   │
│   ├── Orta Panel (konsantrik halka)
│   │   ├── _OrbCanvas — özel animasyonlu canvas
│   │   │   ├── İç halka (canlı)
│   │   │   ├── Orta halka (dönen segmentler)
│   │   │   └── Dış halka (durum renkli)
│   │   ├── Durum metni
│   │   └── Mikrofon butonu
│   │
│   ├── Sağ Panel (RIGHT_W_T=410px)
│   │   ├── Log paneli
│   │   ├── Debug paneli
│   │   └── Ayarlar sekmesi
│   │
│   ├── Input Çubuğu (INPUT_H=34px)
│   │   └── Metin girişi
│   │
│   ├── Kontrol Paneli (CONTROL_H=146px)
│   │   ├── Mute/Unmute
│   │   ├── Duraklat/Devam
│   │   └── Ses efekti geçişi
│   │
│   └── Footer (FOOTER_H=26px)
│       ├── Platform bilgisi
│       └── Sosyal medya ikonları
│
├── SoundManager
│   ├── playsound ile SFX çalma
│   └── _sync_sound_state ile thread-safe durum yönetimi
│
└── Yardımcı Metotlar
    ├── set_state() — durum geçişleri + renk güncelleme
    ├── write_log() — log yazma
    ├── write_debug() — debug yazma
    ├── mark_user_activity() — kullanıcı etkinliği işareti
    └── focus_panel() — panel odağı yönetimi
```

### Durum Makinesi

```
INITIALISING → LISTENING ↔ SPEAKING
                    ↕        ↕
                THINKING → ERROR
                    ↕
               MUTED / PAUSED
```

Her durum, orb (konsantrik halka) rengini değiştirir:
- **LISTENING**: Yeşil `#00ff88`
- **SPEAKING**: Mavi `#4488ff`
- **THINKING**: Altın `#ffcc00`
- **ERROR**: Kırmızı `#ff3344`
- **MUTED**: Koyu pembe `#cc2255`
- **PAUSED**: Koyu teal `#1e3c37`

---

## 🧩 Action Modülleri

### İletişim Modeli

```
Gemini/Ollama → function_call → _execute_tool()
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            loop.run_in_executor()        Direkt fonksiyon çağrısı
            (thread pool)                 (basit işlemler)
                    │                               │
                    ▼                               ▼
            Action Modülü → str result    → JarvisLive._execute_tool()
                                            → result looks like error?
                                              → EVET: ERROR state
                                              → HAYIR: success SFX + LISTENING
```

### Modül Listesi

| Modül | İşlev | Backend |
|-------|-------|---------|
| `open_app.py` | 50+ Windows uygulamasını açma | `os.startfile` / `subprocess` |
| `sys_info.py` | CPU, RAM, Disk, Batarya, Ağ, Saat/Tarih | `psutil` + `socket` |
| `weather.py` | wttr.in API ile anlık hava durumu | `requests` |
| `calendar.py` | Windows takvim CRUD | PowerShell COM |
| `reminders.py` | Hatırlatıcı yönetimi | PowerShell COM |
| `browser.py` | URL açma, Google arama, YouTube oynatma | `webbrowser` + URI |
| `shell.py` | Güvenlik filtreli komut çalıştırma | `subprocess` |
| `whatsapp.py` | WhatsApp mesaj gönderme | Selenium WebDriver |
| `media.py` | YouTube/Spotify medya oynatma | URI + webbrowser |
| `youtube_stats.py` | Kanal istatistikleri ve video analizi | YouTube Data API |
| `screen_vision.py` | Ekran görüntüsü + Gemini Vision analizi | `pyautogui` + Gemini |
| `tts.py` | 3 backend TTS (Piper → Edge → spd-say) | subprocess |
| `windows_utils.py` | Windows API (URI, PowerShell, clipboard, ses) | `ctypes` + `powershell` |
| `health.py` | Platform sağlık verisi (iCloud/Windows) | platform-conditional |
| `system_doctor.py` | Sistem sağlık raporu (disk, RAM, CPU, ağ) | `psutil` |
| `process_manager.py` | Süreç listeleme/öldürme/öncelik | `psutil` |
| `file_guardian.py` | Büyük dosya, yinelenen dosya, klasör temizlik | `os` + `pathlib` |
| `network_monitor.py` | Ağ özeti, bağlantı listesi, ping | `psutil` + `socket` |
| `system_cron.py` | Zamanlanmış görev ekleme/listeleme/silme | `sqlite3` + `threading` |
| `service_monitor.py` | Windows servis listeleme/kontrol | `psutil` |
| `disk_predictor.py` | Disk doluluk tahmini (opsiyonel) | `psutil` + `sqlite3` |
| `process_timeline.py` | Süreç zaman çizelgesi (opsiyonel) | `psutil` + `sqlite3` |
| `network_anomaly.py` | Ağ anomali tespiti (opsiyonel) | `psutil` |
| `cron_web_ui.py` | Cron web yönetim arayüzü (opsiyonel) | `http.server` |
| `watchdog/file_watcher.py` | Gerçek zamanlı dosya izleme (opsiyonel) | `watchdog` / polling |
---

## 🧩 Skill Sistemi

### Skill Manager (`core/skill_manager.py`)

```
SkillManager (singleton)
├── __init__()
│   └── _load_all_skills()
│       ├── skills/ klasöründeki her alt klasörü tara
│       ├── SKILL.md varsa metadata parse et
│       ├── triggers.json varsa trigger tanımlarını oku
│       └── route_xxx_request() fonksiyonunu bul ve kaydet
├── route(user_text) → str | None
│   └── Tüm router fonksiyonlarını sırayla dene
│       → İlk eşleşen skill'in sonucunu döndür
│       → Hiçbiri eşleşmezse None döndür (LLM'e git)
└── list_skills() → list[str]
    → Yüklü skill ID'lerini döndür
```

### İletişim Modeli

Skill sistemi, kullanıcı metnini **AI'a göndermeden önce** işler:

```
Kullanıcı: "youtube aç"
         │
         ▼
  _on_text_command()
         │
         ├── skill_manager.route(text)
         │       │
         │       ├── EŞLEŞTİ → skill doğrudan çalışır
         │       │              Sonuç UI'da gösterilir
         │       │              LLM'e GİDİLMEZ
         │       │
         │       └── EŞLEŞMEDİ → Normal LLM akışına devam
         │
         └── Gemini/Ollama → actions/...
```

### Action vs Skill Farkı

| | Action Modülü | Skill Modülü |
|---|---|---|
| **Kim çağırır?** | AI (function_call) | SkillManager, AI'dan önce |
| **AI dahil mi?** | Evet, AI düşünür sonra çağırır | Hayır, anında çalışır |
| **Hız** | ~1-3sn (AI düşünme süresi) | ~1ms |
| **Kayıt** | tool_registry.py (tek kaynak) + _TOOL_HANDLERS | skills/ klasörü + route fonksiyonu |
| **Kullanım** | Karmaşık, bağlam gerektiren işler | Basit, öngörülebilir komutlar |

### Yeni Skill Ekleme

```python
# skills/yeni_skill/yeni_skill.py
TRIGGERS = {
    "action_name": [
        r"(?:tetikleyici|keyword).*?(?:örnek|pattern)",
    ],
}

def route_yeni_skill_request(user_text: str) -> str | None:
    """user_text'te trigger ara, eşleşirse skill çalıştır."""
    text = user_text.lower()
    for action, patterns in TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return f"Skill sonucu: {action}"
    return None
```

**Kurallar:**
- `route_<name>_request(user_text) → str | None` fonksiyonu zorunlu
- TRIGGERS dict inline (triggers.json opsiyonel)
- Türkçe karakterler için ASCII fallback eklenmeli: `(?:yavaş|yavas)`, `(?:göster|goster)`, `(?:işlem|islem)`
- SkillManager otomatik keşfeder, kayıt gerekmez

---

## 💾 Veri Akışı

### Yapılandırma

```
app_config.py
├── DEFAULT_CONFIG (dict) — 7 varsayılan anahtar
├── load_app_config() → JSON'dan oku + DEFAULT ile merge
├── save_app_config(updates) → JSON'a yaz
├── get_app_config_value(key, default) → tek değer oku
├── has_gemini_api_key() → API anahtarı var mı?
├── get_ollama_models() → localhost:11434/api/tags
└── get_ollama_tts_voices() → Piper + Edge + spd-say
```

### Bellek Sistemi

```
memory/memory_manager.py
├── load_memory() → JSON'dan oku
├── update_memory(updates) → _deep_merge ile birleştir + yaz
├── delete_memory(category, key, match_text) → sil
└── format_memory_for_prompt() → system prompt'a ekle

Kategoriler: identity, preferences, projects, notes
```

### Log Sistemi

```
main.py
├── logging.basicConfig → logs/jarvis.log (DEBUG seviyesi)
├── handle_exception() → yakalanmayan exception'ları logla
├── handle_thread_exception() → thread exception'larını logla
└── httpcore → WARNING seviyesinde (gereksiz DEBUG'leri kapat)
```

---

## 🛡 Güvenlik Mimarisi

### Shell Komut Filtreleme (`actions/shell.py`)

```
BLOCKED_PREFIXES = [
    "rm", "sudo", "mkfs", "dd", "shutdown", "reboot",
    "init", "poweroff", "halt", ":(){", "diskutil",
    "mv /", "chmod 777 /"
]

Her komut:
1. normalize edilir (lowercase + trim)
2. BLOCKED_PREFIXES ile karşılaştırılır
3. Bloklanırsa → güvenlik uyarısı
4. Geçerse → subprocess.run(timeout=30)
```

### Platform Güvenliği

- macOS özel kodları `if IS_MACOS:` bloğu içinde
- Windows'ta `rm -rf /` gibi UNIX komutları çalışmaz
- API anahtarları `.gitignore` ile korunuyor
- Tüm action modülleri try/except ile sarılı
- **`_user_initiated` güvenlik gate**: `_handle_browser_control()` kullanıcı ilk mesajını gönderene kadar `_user_initiated = False` kontrolü yapar. AI'nın izinsiz tarayıcı açmasını engeller.
- **OS detection**: `GeminiProvider.build_config()` sistem prompt'una `[SISTEM BILGISI]` enjekte eder (OS, shell, path separator). AI'nın yanlış platform komutu üretmesini önler.
- **Input validation**: Tool call girişi 2000 char, arg değerleri 500 char ile sınırlı; tool adı whitelist ile doğrulanır
- **Exception logging**: Tüm `except Exception: pass`'ler `traceback.print_exc()` ile loglanır (NDJSON streaming hariç)

### Thread Safety

Thread kullanan modüller ve koruma stratejileri:

| Modül | Korumalı Alan | Kullanılan Kilit | Durum |
|-------|--------------|-----------------|-------|
| `main.py` | `_is_speaking` | `_speaking_lock` (Lock) | ✅ |
| `core/skill_manager.py` | Skills listesi, watcher state | `_lock` (RLock) — 10+ yerde | ✅ |
| `ui/sound_manager.py` | `_all_sound_procs`, `_ambient_proc`, `_foreground_proc` | `_lock` (RLock) — 18 yerde | ✅ |
| `actions/watchdog/file_watcher.py` | Debounce timer, history, event queue | `_debounce_lock`, `_history_lock` | ✅ |
| `actions/system_cron.py:298` | NetworkAnomalyDetector.scan() | `_nad_lock` (Lock) — non-blocking acquire | ✅ |
| `actions/cron_web_ui.py` | `_running` flag | Yok (tek boolean, minör race) | ⚠️ Benign |

---

## 🔌 Backend Karşılaştırması

| Özellik | Gemini AI | Ollama |
|---------|-----------|--------|
| **Bağlantı** | İnternet gerekli | Tamamen yerel |
| **Gecikme** | Düşük (bulut) | Orta (CPU) |
| **Ses Kalitesi** | Yüksek (doğal) | Orta (TTS zinciri) |
| **STT** | Gemini Audio API | Google STT → Faster-Whisper |
| **TTS** | Gemini doğal ses | Piper → Edge-TTS → spd-say |
| **Tool Calling** | Yerleşik (function_declarations) | System prompt + JSON parsing |
| **Maliyet** | API kullanımı ücretli | Ücretsiz |
| **Gizlilik** | Bulut | Tamamen yerel |
| **Model** | Gemini 2.5 Flash | qwen2.5:1.5b (değiştirilebilir) |

---

## 🔊 Fahrettin VAD Sistemi

### Mimarisi

Unified VAD wrapper: `core/fahrettin_vad.py` → `core/vad_engine.py`

```
FahrettinVAD (core/fahrettin_vad.py)
├── __init__(config, engine, energy_threshold, sample_rate)
│   └── VADEngine (core/vad_engine.py) — arka uç motor
│       ├── Silero VAD (PyTorch, en doğru)     ← torch.from_numpy()
│       ├── WebRTC VAD (webrtcvad, hızlı)      ← webrtcvad.Vad()
│       └── Energy VAD (numpy, her zaman)       ← RMS threshold
│
├── is_speech(audio_bytes, sample_rate) → (bool, float)
│   └── Auto-downsample: 48kHz → 16kHz
│   └── Thread-safe (deque metrics)
│
├── get_debug_stats() → dict
│   └── RMS, noise_floor, speech_ratio, engine_name
│
└── reset() → istatistikleri sıfırla
```

### Backend Zinciri

| Sıra | Backend | Bağımlılık | Doğruluk | Hız |
|------|---------|-----------|----------|-----|
| 1 | Silero (PyTorch) | `torch` (~2GB) | ★★★★★ | Yavaş |
| 2 | WebRTC | `webrtcvad` | ★★★★ | Çok Hızlı |
| 3 | Energy (fallback) | `numpy` (her zaman) | ★★★ | Anlık |

### Konfigürasyon (`config/audio.yaml`)

```yaml
vad:
  fahrettin:
    engine: "energy"          # silero / webrtc / energy
    energy_threshold: 50.0    # RMS eşiği (eski 400+ → normal konuşma için 50)
    debug_log: false
```

### Thread Safety

- `FahrettinVAD` `is_speech()` thread-safe
- `VADEngine` state machine kilit korumasız (tek thread çağırır)
- Metrics `deque` append-only (lock-free safe)

---

## 🎤 Wake Word Sistemi

### Mimarisi (`core/wake_word.py`)

```
WakeWordEngine
├── Engine Zinciri:
│   ├── openWakeWord (Model.tflite, önerilen)    ← Model() predict
│   ├── Porcupine (pvporcupine, Picovoice)       ← pvporcupine.create()
│   └── Energy (numpy, son fallback)             ← RMS threshold
│
├── detect(audio_frame) → bool
│   ├── openWakeWord → threshold >= sensitivity
│   ├── açık değilse → Porcupine → threshold
│   ├── o da yoksa → Energy → RMS > eşik + min_duration
│   └── hiçbiri → False
│
├── set_activation_callback(callback)
├── set_deactivation_callback(callback)
│
└── Konfigürasyon (config/wake_word.yaml):
    ├── engine: "openwakeword"
    ├── wake_word: "jarvis"
    ├── openwakeword.sensitivity: 0.5
    ├── porcupine.sensitivity: 0.5
    └── energy.threshold: 0.03
```

### Entegrasyon

```
main.py → Ollama modu → _listen_audio() → WakeWordEngine.detect()
                                              │
                                      EŞLEŞİRSE → _on_text_command() akışını başlat
                                      EŞLEŞMEZSE → bekleme modunda kal
```

### Notlar

- Wake word sadece **Ollama modunda** aktiftir
- Gemini modunda wake word gerekmez (sürekli dinleme)
- RNNoise gürültü bastırma wake word öncesi uygulanır (`apply_noise_suppression_before: true`)

---

## 🎛 Audio Sistemi (`core/audio_system/`)

### Dizin Yapısı

```
core/audio_system/
├── __init__.py        — Paket dışa aktarımı (get_stt_engine, get_tts_engine)
├── stt_engine.py      — STT motorları (Google STT → Faster-Whisper → SpeechRecognition)
├── tts_engine.py      — TTS motorları (Piper → pyttsx3 → edge-tts → gTTS)
└── audio_player.py    — Ses çalma (WAV/MP3/bytes → aplay/mpg123/ffplay)
```

### STT Engine (`stt_engine.py`)

```
STTEngine
├── __init__(engine, model_size, device)
│   ├── engine="google" → SpeechRecognition (bulut, internet gerekli)
│   └── engine="whisper" → faster-whisper (yerel, offline)
│
├── transcribe(audio_bytes) → str
│   └── Google: Recognizer().recognize_google()
│   └── Whisper: WhisperModel().transcribe()
│
├── transcribe_file(path) → str
├── get_debug_info() → dict
└── is_available() → bool
```

### TTS Engine (`tts_engine.py`)

```
BaseTTSEngine (abstract)
├── PiperTTSEngine (yerel, offline, yüksek kalite)
│   └── subprocess: echo "..." | piper --model tr_TR-fahrettin-medium.onnx --output-raw | aplay
├── Pyttsx3Engine (cross-platform, offline)
│   └── pyttsx3.init() → engine.say()
├── EdgeTTSEngine (bulut, Microsoft Neural)
│   └── subprocess: edge-tts --voice tr-TR-AhmetNeural --text "..." --write-media out.mp3
├── GTTSEngine (bulut, Google)
│   └── gTTS(text=..., lang="tr") → mp3
└── FallbackChain
    ├── Piper → pyttsx3 → Edge → gTTS
    └── Her adımda availability kontrolü, ilk çalışan kullanılır
```

### Audio Player (`audio_player.py`)

```
AudioPlayer (singleton)
├── play_wav(path, blocking=False) → bool
│   └── aplay (Linux) / ffplay (cross) / PowerShell (Windows)
├── play_bytes(audio_data, sample_rate, blocking=False) → bool
└── stop() → tüm çalan sesleri durdur
```

---

## 🔄 Yeni Modüller

### Streaming STT (`core/streaming_stt.py`)

```
StreamingSTT
├── Queue-based async transcription
├── VAD filtering (gereksiz işlemeyi engelle)
├── Turkish syllable fix (fix_turkish_syllable_split)
└── RealtimeSTT (düşük gecikme modu)
```

### Streaming TTS (`core/streaming_tts.py`)

```
StreamingTTS
├── TTSBuffer — ön belleğe alma + akış
├── TTS akışını chunk chunk çalma
└── Barge-In desteği (konuşmayı kesme)
```

### Barge-In (`core/barge_in.py`)

```
BargeInDetector
├── create_barge_in_detector(config) → BargeInDetector
├── Sırasında:
│   ├── JARVIS konuşurken mikrofonu dinler
│   ├── Kullanıcı konuşmaya başlarsa → TTS'i kes
│   └── Yeni kullanıcı girdisini işlemeye başlar
└── Entegrasyon: main.py → _listen_audio() içinde
```

### Emotion TTS (`core/emotion_tts.py`)

```
EmotionTTS
├── SSML prosody etiketleriyle duygusal konuşma
├── Destek: piper, edge-tts, spd-say
└── Kullanım: EmotionTTS("mutlu", "Merhaba!") → SSML wrapped text
```

---

## 🔌 Provider Abstraction Detayı

### BaseProvider (`core/provider_base.py`)

```
BaseProvider (ABC)
│
├── Lifecycle:
│   ├── start(jarvis)      → jarvis referansını sakla, provider'ı başlat
│   ├── run_loop()         → ana işlem döngüsü (bloklar)
│   └── stop()             → kaynakları temizle
│
├── I/O:
│   ├── send_audio(data)   → ses gönder (ses destekli provider'lar override eder)
│   └── send_text(text)    → metin gönder (tüm provider'lar)
│
├── Properties:
│   ├── name               → "gemini" / "ollama"
│   ├── supports_streaming_audio → ses akışı desteği
│   └── supports_tool_calls → native tool calling desteği
│
└── Implementations:
    ├── GeminiProvider (core/gemini_provider.py)
    │   ├── Gemini Live API bidirectional streaming
    │   ├── Tool calls: function_declarations
    │   └── Audio: pyaudio 16kHz in → 24kHz out
    │
    └── OllamaProvider (core/ollama_provider.py)
        ├── Ollama HTTP /api/chat
        ├── Tool calls: system prompt + JSON parsing
        ├── STT: VAD → faster-whisper → syllable fix
        ├── TTS: Piper → Edge-TTS → spd-say
        └── RNNoise entegrasyonu (process_16khz metodu)
```

---

## 🧰 Tool Registry (`core/tool_registry.py`)

### Mimarisi

```
_TOOL_DEFS → (name, description, params_dict, required_list)[]
    │
    ├── generate_gemini_declarations() → Gemini function_declarations formatı
    ├── generate_ollama_tool_help() → Ollama sistem prompt'u metni
    ├── VALID_TOOLS → whitelist seti
    └── TOOL_HANDLER_MAP → {name: handler_method_name}

Her handler: async def _handle_<name>(self, args, loop) -> str
```

### 40 Aracın Tam Listesi

| # | Araç Adı | Açıklama | Parametreler |
|---|----------|----------|-------------|
| 1 | `open_app` | Uygulama aç | app_name |
| 2 | `sys_info` | Sistem bilgisi | query |
| 3 | `get_weather` | Hava durumu | location (ops) |
| 4 | `get_current_location` | Konum bilgisi | - |
| 5 | `get_calendar_events` | Takvim oku | query, limit (ops) |
| 6 | `add_calendar_event` | Takvim ekle | title, start_iso, end_iso(ops), location(ops) |
| 7 | `delete_calendar_event` | Takvim sil | title, start_iso(ops) |
| 8 | `get_reminders` | Hatırlatıcı listele | query, limit(ops) |
| 9 | `add_reminder` | Hatırlatıcı ekle | title, due_iso(ops) |
| 10 | `browser_control` | Tarayıcı kontrol | action, url(ops), query(ops) |
| 11 | `shell_run` | Komut çalıştır | command |
| 12 | `send_whatsapp` | WhatsApp mesaj | contact, message |
| 13 | `save_whatsapp_contact` | WhatsApp kaydet | name, phone |
| 14 | `play_media` | Medya oynat | query, platform(ops) |
| 15 | `get_youtube_report` | YouTube analiz | channel_handle(ops) |
| 16 | `analyze_screen` | Ekran analizi | prompt(ops) |
| 17 | `get_system_health` | Sistem sağlık | - |
| 18 | `cleanup_temp_files` | Geçici dosya temizlik | days_old(ops) |
| 19 | `cleanup_recycle_bin` | Geri dönüşüm temizlik | - |
| 20 | `list_processes` | Süreç listele | sort_by(ops), limit(ops) |
| 21 | `kill_process` | Süreç öldür | pid, name(ops) |
| 22 | `set_process_priority` | Süreç öncelik | pid, priority |
| 23 | `find_process_by_port` | Port bul | port |
| 24 | `find_large_files` | Büyük dosya bul | folder(ops), min_gb(ops) |
| 25 | `find_duplicate_files` | Yinelenen dosya | folder(ops) |
| 26 | `cleanup_folder` | Klasör temizlik | folder, days_old(ops) |
| 27 | `get_folder_summary` | Klasör özeti | folder(ops) |
| 28 | `get_network_summary` | Ağ özeti | - |
| 29 | `list_connections` | Bağlantı listesi | state(ops) |
| 30 | `ping_host` | Ping testi | host |
| 31 | `add_cron_job` | Zamanlanmış görev ekle | name, interval_m, command |
| 32 | `list_cron_jobs` | Görev listele | - |
| 33 | `remove_cron_job` | Görev sil | name |
| 34 | `toggle_cron_job` | Görev aç/kapa | name |
| 35 | `start_cron_daemon` | Cron başlat | - |
| 36 | `list_services` | Servis listele | - |
| 37 | `control_service` | Servis kontrol | name, action |
| 38 | `set_volume` | Ses seviyesi | level |
| 39 | `get_memory` | Bellek oku | key(ops) |
| 40 | `set_memory` | Bellek yaz | key, value |

---

## 🧩 Skill Manager v3 — Hot-Reload

### Mimarisi (`core/skill_manager.py`)

```
SkillManager (singleton, v3)
├── 17 skill yüklü (sürekli artıyor)
├── Hot-Reload: watcher thread (3sn interval)
├── Otomatik keşif: skills/<name>/ klasörleri
└── Callback desteği: loaded/reloaded/disabled
```

### Skill Keşif Protokolü

```
skills/<name>/
├── <name>_skill.py        ← ZORUNLU: route_<name>_request(user_text)
├── SKILL.md               ← OPSİYONEL: YAML frontmatter (SKILL_ID, SKILL_NAME, SKILL_VERSION)
└── triggers.json          ← OPSİYONEL: trigger pattern'leri
```

### Hot-Reload Döngüsü

```
Watcher Thread (3sn)
├── skills/ klasörünü tara
├── Yeni dosya → import et + route_func kaydet → callback: loaded
├── Değişen dosya → reload et → callback: reloaded
└── Silinen dosya → kaldır → callback: disabled
```

### 17 Aktif Skill

| Skill ID | Klasör | Versiyon |
|----------|--------|----------|
| `browser-v1` | skills/browser/ | 1.0 |
| `system_health-v1` | skills/system_health/ | 1.0 |
| `process_control-v1` | skills/process_control/ | 1.0 |
| `file_manager-v1` | skills/file_manager/ | 1.0 |
| `network-v1` | skills/network/ | 1.0 |
| `scheduler-v1` | skills/scheduler/ | 1.0 |
| `services-v1` | skills/services/ | 1.0 |
| `weather-v1` | skills/weather/ | 1.0 |
| `youtube-v1` | skills/youtube/ | 1.0 |
| `vision-v1` | skills/vision/ | 1.0 |
| `calendar-v1` | skills/calendar/ | 1.0 |
| `reminders-v1` | skills/reminders/ | 1.0 |
| `whatsapp-v1` | skills/whatsapp/ | 1.0 |
| `media-v1` | skills/media/ | 1.0 |
| `demo-v1` | skills/demo/ | 0.1 |
| `greeting-v1` | skills/greeting/ | 1.0 |
| `debugging_jarvis-v1` | skills/debugging_jarvis/ | 1.0 |

---

## 🛡 Hata Yönetimi Pattern'leri

### Exception Logging

```python
# DOGRU: Her except pass traceback ile loglanır
try:
    sonuc = riskli_islem()
except Exception:
    traceback.print_exc()  # ZORUNLU

# ISTISNA 1: NDJSON stream parser (main.py Ollama chunk)
#   → Kısmi/eksik JSON beklenir, her chunk loglamak flood yaratır

# ISTISNA 2: Best-effort fallback (windows_utils, process_manager, youtube_stats)
#   → Dış çağrıcı zaten logluyor

# ISTISNA 3: cleanup finally bloğu
#   → close()/terminate()/kill() de traceback.print_exc() ile loglanır
```

### Stream Parsing

```python
# NDJSON/stream parser'larda:
#   → Önemsiz kısmi chunk'larda traceback atlanır
#   → Gerçek hatalarda traceback.print_exc() ZORUNLU
```

### Input Validation

| Kural | Limit | Nerede |
|-------|-------|--------|
| STT text cap | 10000 char | `_on_text_command()` |
| Tool call arg cap | 500 char/arg | `parse_local_tool_call()` |
| Tool call total cap | 2000 char | `parse_local_tool_call()` |
| Tool name whitelist | Sadece kayıtlı | `VALID_TOOLS` seti |

### Cleanup Exception Logging

```python
finally:
    try:
        stream.close()
    except Exception:
        traceback.print_exc()  # Kaynak sızıntısını gizleme
```

---

## 📊 Kod İstatistikleri (Güncel)

| Ölçüt | Değer |
|-------|-------|
| Python satırı | ~11,000+ |
| Python dosyası | 45+ |
| Action modülü | 25 (20 ana + 5 opsiyonel) |
| Core modülü | 15+ |
| Audio modülü | 5 (noise_suppressor, microphone, lib, audio_system/) |
| Skill modülü | 17 |
| UI satırı | ~2,300 (ui.py + ui/ paketi) |
| Test sayısı | 1261 (unittest, 2 skip) |
| Dokümantasyon | 19 .md dosyası (docs/) |

---

## 📚 Dokümantasyon Haritası

| Dosya | Açıklama |
|-------|----------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Sistem Mimarisi — Bu dosya |
| [ORCHESTRATOR.md](ORCHESTRATOR.md) | Orkestrasyon katmanı — JarvisLive, tool dispatch, routing |
| [AGENTS.md](AGENTS.md) | Ajan sistemi — ACA, Skill Manager, yaşam döngüsü |
| [SKILLS.md](SKILLS.md) | Skill sistemi — yükleme, hot-reload, 18 skill listesi |
| [UI_LAYER.md](UI_LAYER.md) | Arayüz katmanı — Tkinter, OrbCanvas, SoundManager |
| [STT_TTS.md](STT_TTS.md) | Ses işleme — STT, TTS, VAD, Wake Word |
| [LLM_INTEGRATION.md](LLM_INTEGRATION.md) | LLM entegrasyonu — Gemini, Ollama, tool calling |
| [BROWSER_SKILL.md](BROWSER_SKILL.md) | Tarayıcı yönetimi — browser skill/action, güvenlik |
| [STATE_MANAGEMENT.md](STATE_MANAGEMENT.md) | Durum yönetimi — state machine, persistence, concurrency |
| [CONFIG.md](CONFIG.md) | Yapılandırma — API anahtarları, audio.yaml, validasyon |
| [API_REFERENCE.md](API_REFERENCE.md) | Dahili API referansı — modül arayüzleri, şemalar, hatalar |
| [DEPENDENCIES.md](DEPENDENCIES.md) | Bağımlılık haritası — Python paketleri, sistem araçları |
