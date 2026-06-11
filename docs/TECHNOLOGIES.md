# JARVIS Teknoloji Yığını

## Genel Bakış

JARVIS, **Python 3.12** tabanlı, çok katmanlı bir sesli asistan uygulamasıdır.  
Aşağıda kullanılan tüm teknolojiler, kütüphaneler ve araçlar detaylandırılmıştır.

---

## 🎯 Çekirdek Teknolojiler

### Python 3.12+

| Özellik | Kullanım Alanı |
|---------|---------------|
| `asyncio` | Tüm asenkron I/O (ses akışı, API çağrıları) |
| `threading` | UI dışı işlemler, TTS ses çalma |
| `subprocess` | Piper, edge-tts, PowerShell, shell komutları |
| `tempfile` | Geçici WAV/MP3 dosyaları |
| `pathlib` | Platform-bağımsız dosya yolları |
| `dataclasses` | (ileri kullanım) |

---

## 🧠 Yapay Zeka

### Google Gemini AI

| Bileşen | Sürüm | Amaç |
|---------|-------|------|
| `google-genai` | ≥1.0.0 | Gemini API Python SDK |
| Gemini 2.5 Flash | latest | Sesli diyalog, tool calling, vision |
| **Live Audio API** | v1alpha | Gerçek zamanlı ses giriş/çıkış akışı |
| **Speech Config** | — | Doğal ses sentezi (Charon/Puck/Aoede/Kore vb.) |
| **Function Calling** | — | Tool declaration + execution |

API Endpoint: `generativelanguage.googleapis.com`  
Model: `models/gemini-2.5-flash-native-audio-latest`

**Ses Modelleri (Voice):**
- Charon (varsayılan)
- Puck, Aoede, Kore, Fenrir, Leda, Orus, Zephyr

### Ollama (Yerel Backend)

| Bileşen | Amaç |
|---------|------|
| **Ollama** | Yerel LLM sunucusu (localhost:11434) |
| **Model** | `qwen2.5:1.5b` (1.5B parametre, değiştirilebilir) |
| **API** | `/api/chat` (HTTP streaming) |
| **keep_alive** | 30 dk (model RAM'de tutulur) |
| **Warm-up** | Başlangıçta boş mesajla modele ön yükleme |

Ollama modunda tool calling, system prompt içinde JSON formatında tanımlanır ve yanıt ayrıştırılarak çalıştırılır.

---

## 🎤 Ses İşleme

### Gürültü Bastırma (RNNoise)

| Bileşen | Amaç |
|---------|------|
| **RNNoise** | Gerçek zamanlı gürültü bastırma (C kütüphanesi, ctypes ile sarılmış) |
| **librnnoise.so** | Kaynaktan derlenmiş RNNoise C kütüphanesi (3.7MB) |
| **Frame size** | 480 sample (10ms @ 48kHz) |
| **Desteklenen rate** | 48kHz (native), 16kHz (upsampling ile) |
| **VAD çıktısı** | `vad_probability` property — RNNoise dahili VAD olasılığı |
| **Bypass modu** | Kütüphane yoksa sessizce devre dışı, input aynen iletilir |

**Pipeline (Ollama STT için):**
```
16kHz giriş → np.repeat (3x upsampling) → 48kHz RNNoise (3 frame) → decimate → 16kHz çıkış
```

**Performans:**
- 48kHz native: ~0.06ms/frame (10ms budget'in %0.6'sı)
- 16kHz pipeline: ~0.16ms/frame (3 RNNoise frame işler)
- Gürültü bastırma: %75-90 (gürültü seviyesine bağlı)
- Konuşma koruma: %97+ (formant-based sinyaller)

### Speech-to-Text (STT)

| Kütüphane | Sürüm | Amaç |
|-----------|-------|------|
| `SpeechRecognition` | ≥3.10.0 | Google STT API (birincil, bulut) |
| `faster-whisper` | ≥1.0.0 | Yerel STT (fallback, offline) |
| `pyaudio` | ≥0.2.13 | PortAudio bağlantısı (mikrofon/hoparlör) |

**Faster-Whisper Yapılandırması:**
- Model: `large-v3` (int8 quantize, ~464MB)
- Device: CPU
- compute_type: int8
- cpu_threads: 8
- num_workers: 2
- language: tr
- beam_size: 1, best_of: 1, temperature: 0
- VAD filter: aktif (threshold: 0.5, min_speech_duration_ms: 250, min_silence_duration_ms: 500, speech_pad_ms: 400)

**STT Post-processing (Ollama modu):**
- `unicodedata.normalize("NFC")` — Decomposed Türkçe karakter (ç, ş, ğ, ö, ü, ı) düzeltmesi
- `_fix_turkish_syllable_split()` — Kısa parçaları (≤3 karakter) birleştir, toplam ≤8 karakter, stop-word sınırı

### Text-to-Speech (TTS) — Piper

| Bileşen | Amaç |
|---------|------|
| **Piper** | Yerel, offline TTS |
| **Model** | `tr_TR-fahrettin-medium.onnx` (~61MB) |
| **Config** | `tr_TR-fahrettin-medium.onnx.json` |
| **Player** | `aplay` (ALSA) |

Binary: `piper` (shutil.which ile bulunur, `~/.local/bin/`, `/usr/local/bin/`, `/usr/bin/`)

### Text-to-Speech (TTS) — Edge-TTS

| Bileşen | Amaç |
|---------|------|
| **edge-tts** | Microsoft Neural TTS (bulut, internet gerekli) |
| **Sesler** | `tr-TR-AhmetNeural` (erkek), `tr-TR-EmelNeural` (kadın) |
| **Player** | `mpg123` |

### Text-to-Speech (TTS) — Fallback

- **spd-say** (Speech Dispatcher) — son çare, Linux
- **Windows Speech** (System.Speech) — Windows modu

---

## 🖥 Kullanıcı Arayüzü

| Teknoloji | Amaç |
|-----------|------|
| **Tkinter** | Ana UI framework (Python standart) |
| **Pillow** | ≥10.0.0 | PNG ikon yükleme, yeniden boyutlandırma |
| **Canvas** | Özel konsantrik halka animasyonu |
| **after()** | Animasyon döngüsü (~16ms, ~60 FPS) |

### UI Bileşenleri

- `OrbCanvas`: Özel Tkinter Canvas widget — 3 katmanlı konsantrik halka
  - İç halka: canlı, nefes efekti
  - Orta halka: dönen segmentler (loading animasyonu)
  - Dış halka: durum rengi (yeşil/mavi/sarı/kırmızı)
- `SoundManager`: Thread-safe ses efekti yönetimi
- `SettingsFrame`: Backend, ses, model yapılandırması

### Font Sistemi

- **Grift** (body) — ana metin fontu
- **Grift Extra Bold** (display) — başlık fontu
- Sistemde yüklü olmalı, `Fonts/` dizininde bulunur

---

## 🔧 Sistem Araçları

| Kütüphane | Sürüm | Amaç |
|-----------|-------|------|
| `psutil` | ≥5.9.0 | Sistem bilgisi (CPU, RAM, disk, batarya, ağ, süreçler, servisler) |
| `requests` | ≥2.31.0 | HTTP (hava durumu, YouTube API) |
| `httpx` | ≥0.27.0 | Async HTTP (Ollama API streaming) |
| `pyautogui` | ≥0.9.54 | Ekran görüntüsü, fare/klavye kontrolü |
| `Pillow` | ≥10.0.0 | Görüntü işleme |
| `sqlite3` | (standart) | Zamanlanmış görev, disk tahmin, süreç zaman çizelgesi |

### Binary Bağımlılıklar (`helpers/bin/`)

| Binary | Amaç | Kurulum |
|--------|------|---------|
| `ffmpeg` | Ses/video dönüştürme | [ffmpeg.org](https://ffmpeg.org) |
| `mpg123` | MP3 çalma (Edge-TTS) | [mpg123.de](https://www.mpg123.de) |

---

## 🔌 API Servisleri

| Servis | Endpoint | Amaç |
|--------|----------|------|
| **Gemini AI** | `generativelanguage.googleapis.com` | Ana AI backend |
| **Ollama** | `localhost:11434` | Yerel AI backend |
| **wttr.in** | `https://wttr.in/{location}?format=j1` | Hava durumu |
| **YouTube Data API** | `https://www.googleapis.com/youtube/v3` | Kanal istatistikleri |
| **Google STT** | (SpeechRecognition) | Bulut STT |
| **Google Custom Search** | (pywhatkit) | YouTube arama |

---

## 🐍 Python Paketleri (requirements.txt)

```
google-genai>=1.0.0       # Gemini AI API SDK
SpeechRecognition>=3.10.0 # Google STT API
pyaudio>=0.2.13           # PortAudio ses I/O
faster-whisper>=1.0.0     # Yerel STT (offline)
httpx>=0.27.0             # Async HTTP (Ollama)
psutil>=5.9.0             # Sistem bilgisi
Pillow>=10.0.0            # Görüntü işleme
requests>=2.31.0          # HTTP (weather, YouTube)
pyautogui>=0.9.54         # Ekran görüntüsü
```

### Harici Python Modülleri (runtime import)

| Modül | Kullanım Yeri | Amaç |
|-------|--------------|------|
| `asyncio` | main.py | Async I/O |
| `wave`, `struct` | main.py | WAV dosya işleme |
| `unicodedata` | main.py | NFC normalizasyonu (Türkçe STT) |
| `json` | app_config.py, main.py | JSON yapılandırma |
| `urllib.request` | app_config.py | Ollama model listesi |
| `ctypes` | windows_utils.py | Windows API |
| `socket` | sys_info.py | Ağ bilgisi |
| `http.server` | windows_utils.py | Geçici HTTP sunucusu |
| `selenium` | whatsapp.py | WhatsApp Web otomasyonu |
| `sqlite3` | system_cron.py, disk_predictor.py, process_timeline.py | Zamanlanmış görev ve veri depolama |
| `fnmatch` | file_guardian.py | Dosya desen eşleştirme |
| `watchdog` | watchdog/file_watcher.py | Gerçek zamanlı dosya izleme (opsiyonel) |

---

## 🧩 Skill Sistemi

### Skill Manager (`core/skill_manager.py`)

| Özellik | Detay |
|---------|-------|
| **Mekanizma** | Singleton, `skills/` altındaki tüm `route_*_request()` fonksiyonlarını otomatik keşfeder |
| **18 skill yüklü** | agent, browser, calendar, debugging_jarvis, file_manager, greeting, media, network, process_control, reminders, scheduler, services, system_health, vision, voice_coding, weather, whatsapp, youtube |
| **Routing** | `_on_text_command()` önce `skill_manager.route()`, eşleşmezse LLM |
| **Trigger pattern** | Regex + keyword eşleştirme, Türkçe karakterlerde ASCII fallback zorunlu |

### Skill Modülleri (`skills/`)

| Skill | Backend Modül | Tetikleyici Örnek |
|-------|---------------|-------------------|
| `agent` | `core.tool_registry` | "gorev olustur", "senaryo calistir" |
| `browser` | `actions.browser` | "youtube aç", "google'da ara" |
| `calendar` | `actions.calendar` | "bugun takvimim", "toplanti ekle" |
| `debugging_jarvis` | — | "debug", "sorun", "hata" |
| `file_manager` | `actions.file_guardian` | "buyuk dosyalari bul", "downloads temizle" |
| `greeting` | — | "merhaba", "selam", "naber" |
| `media` | `actions.media` | "tarkan cal", "spotifyda jazz ac" |
| `network` | `actions.network_monitor` | "internet durumu", "google'a ping" |
| `process_control` | `actions.process_manager` | "chrome'u kapat", "port 8080" |
| `reminders` | `actions.reminders` | "hatirlatma ekle", "yapilacaklarim" |
| `scheduler` | `actions.system_cron` | "gorevlerim neler", "gorev ekle" |
| `services` | `actions.service_monitor` | "calisan servisler", "mysql'i baslat" |
| `system_health` | `actions.system_doctor` | "bilgisayarim yavas", "cpu kullanimi" |
| `vision` | `actions.screen_vision` | "ekranda ne var", "bu hatayi oku" |
| `voice_coding` | — | "kod", "kodla", "calistir" |
| `weather` | `actions.weather` | "hava nasil", "Ankara sicaklik" |
| `whatsapp` | `actions.whatsapp` | "anneye mesaj gonder", "ahmeti kaydet" |
| `youtube` | `actions.youtube_stats`, `actions.media` | "kanalim nasil", "youtube sarki ac" |

---

| Teknoloji | Amaç |
|-----------|------|
| **PowerShell** | Takvim, hatırlatıcı, ses yönetimi |
| **Start-Process** | Uygulama açma |
| **System.Speech** | Windows TTS |
| **Clipboard API** | Pano yönetimi |
| **Snipping Tool** | Ekran görüntüsü |
| **COM Objects** | Takvim (Outlook), hatırlatıcılar |

---

## 🧪 Test

| Araç | Amaç |
|------|------|
| `unittest` | Python standart test framework |
| `py_compile` | Syntax doğrulama |

### Test Kapsamı (1121 smoke test + 68 uzman testi, toplam 1189)

```
TestProjectStructure
├── test_core_is_package         → core/__init__.py varlığı
├── test_gitignore_updated       → .gitignore pattern'leri
├── test_icon_dir_exists         → Icon/ dizini ve PNG'ler
├── test_no_log_files_in_root    → Kökte .log yok
└── test_no_postscript_artifacts → PostScript artifact yok

TestConfig
├── test_app_config_loadable     → app_config import
├── test_pyrightconfig_valid_json → pyrightconfig geçerli JSON
└── test_requirements_has_versions → requirements version pin

TestActions
├── test_actions_package_importable → actions paketi
├── test_action_modules_importable  → Her modül ayrı ayrı
└── test_health_module_importable   → health modülü

TestSkillModules
├── test_skill_modules_importable     → 14 skill import
├── test_core_skill_manager_importable→ SkillManager import
├── test_skill_manager_loads_all_skills → 14 skill yükleme
└── test_each_skill_has_route_function  → route fonksiyonları

TestSystemPrompt
└── test_prompt_file_exists → core/prompt.txt varlığı

TestNoiseSuppressor (10 RNNoise testi)
├── test_noise_suppressor_import         → NoiseSuppressor sınıfı import
├── test_noise_suppressor_constants      → FRAME_SIZE=480, SUPPORTED_RATES
├── test_noise_suppressor_bypass         → enabled=False passthrough
├── test_noise_suppressor_16khz          → process_16khz bypass
├── test_noise_suppressor_context_manager → with NoiseSuppressor()
├── test_noise_suppressor_vad            → vad_probability float
├── test_noise_suppressor_process_stream → process_stream bypass
├── test_audio_package_importable        → audio/__init__.py ihracatı
├── test_microphone_importable           → MicrophoneStream import
└── test_noise_suppressor_cleanup        → _cleanup kapatma
```

---

## 📦 Proje Büyüklüğü

| Kategori | Boyut |
|----------|-------|
| Python kodu | ~11,000+ satır |
| Python dosyası | 45+ |
| Audio modülü | 271 satır (noise_suppressor) + 148 satır (microphone) |
| RNNoise C kütüphanesi | 3.7 MB (audio/lib/librnnoise.so) |
| Whisper STT modeli | ~464 MB |
| Whisper yedek model | ~1.6 GB (kullanılmıyor) |
| Piper TTS modeli | ~61 MB |
| Sanal ortam | ~547 MB |
| **Toplam** | **~2.6 GB** |
