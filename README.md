# J.A.R.V.I.S — Sesli Asistan / Voice Assistant / Sprachassistent

> **J**ust **A** **R**ather **V**ery **I**ntelligent **S**ystem  
> **🇹🇷** Adler ASİ tarafından yapılmıştır · İyilik iyidir...  
> **🇬🇧** Made by Adler ASİ · Goodness is good...  
> **🇩🇪** Hergestellt von Adler ASİ · Güte ist gut...

---

## 🌍 Proje Hakkında / About / Über das Projekt

**🇹🇷 Türkçe:** J.A.R.V.I.S, **Windows, Linux ve macOS** işletim sistemlerinde çalışan, gerçek zamanlı sesli komutlarla yönetilen, yapay zeka destekli kişisel asistandır. Google Gemini AI (bulut) veya Ollama (yerel, çevrimdışı) backend desteği sunar. Sesli diyalog, sistem kontrolü, dosya yönetimi, takvim ve hatırlatıcı yönetimi, hava durumu sorgulama, medya oynatma, WhatsApp mesajlaşma, YouTube analizi, ekran görüntüsü analizi ve daha birçok özelliği AI destekli veya AI'sız olarak yerine getirir.

**🇬🇧 English:** J.A.R.V.I.S is a real-time, voice-controlled, AI-powered personal assistant that runs on **Windows, Linux and macOS**. It supports Google Gemini AI (cloud) or Ollama (local, offline) as backend. Features include voice dialogue, system control, file management, calendar and reminders, weather queries, media playback, WhatsApp messaging, YouTube analytics, screen analysis, and many more capabilities — both AI-powered and AI-free.

**🇩🇪 Deutsch:** J.A.R.V.I.S ist ein KI-gestützter persönlicher Assistent mit Echtzeit-Sprachsteuerung für **Windows, Linux und macOS**. Mit Google Gemini AI (Cloud) oder Ollama (lokal, offline) als Backend bietet es Sprachdialog, Systemsteuerung, Dateiverwaltung, Kalender- und Erinnerungsverwaltung, Wetterabfragen, Medienwiedergabe, WhatsApp-Nachrichten, YouTube-Analyse, Bildschirmanalyse und viele weitere Funktionen — sowohl KI-gestützt als auch KI-frei.

---

## ✨ Tüm Özellikler / All Features / Alle Funktionen

### 🎤 Ses & Konuşma / Voice & Speech / Stimme & Sprache

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Sesli Diyalog** | Gerçek zamanlı mikrofon girişi, doğal konuşma | Real-time voice dialogue | Echtzeit-Sprachdialog |
| **Çift Backend** | Gemini AI (bulut) veya Ollama (yerel, offline) | Dual AI backend | Dual-KI-Backend |
| **Gürültü Bastırma** | RNNoise ile gerçek zamanlı gürültü bastırma (48kHz/16kHz), otomatik bypass | Noise suppression (RNNoise) | Geräuschunterdrückung (RNNoise) |
| **VAD** | Ses aktivite dedeksiyonu — WebRTC / enerji tabanlı fallback | Voice Activity Detection | Spracherkennungsaktivierung |
| **Wake Word** | Enerji tabanlı wake word ("Jarvis", "Computer", özelleştirilebilir) | Wake word detection | Aufwachwort-Erkennung |
| **Barge-In** | Konuşma sırasında kesip yeni komut verme | Barge-in support | Unterbrechung während der Antwort |
| **Streaming STT** | faster-whisper ile gerçek zamanlı yazıya çevirme, VAD filtreleme | Streaming speech-to-text | Echtzeit-Spracherkennung |
| **Çoklu TTS** | Piper (yerel), Edge-TTS (bulut), pyttsx3, Windows Speech | Multi-engine text-to-speech | Mehrere TTS-Engines |
| **Düzeltme** | Türkçe hece bölünmesi düzeltme, transkript temizleme | Turkish syllable-split correction | Türkische Silbenkorrektur |

### 🤖 AI & Otomasyon / AI & Automation / KI & Automatisierung

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **ACA Agent** | Otonom çok adımlı görev yürütücü (Observer→Planner→Executor→Reflection) | Autonomous Computer Agent | Autonomer Computer-Agent |
| **Tool Registry** | 44 araç — Gemini function calling / Ollama JSON tool calls | 44 tools in registry | 44 Werkzeuge registriert |
| **Function Calling** | AI'ın tool çağrısı yaparak işlem yürütmesi | AI function calling | KI-Funktionsaufrufe |
| **Ollama JSON Tools** | Yerel LLM ile tool çağrısı (system prompt içinde tanımlı) | Local LLM tool execution | Lokale LLM-Werkzeuge |
| **Risk Yönetimi** | RiskLevel: NONE→HIGH, MEDIUM+ için kullanıcı onayı | Risk-based approval | Risikobasierte Genehmigung |

### 🧩 Skill Sistemi / Skill System / Skill-System

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **17 Skill Modülü** | AI'sız doğrudan işlem, ~1-5ms yanıt süresi | AI-free response in ~1-5ms | KI-freie Reaktion in ~1-5ms |
| **Hot-Reload** | Skill modüllerini runtime'da yeniden yükleme (3sn interval) | Runtime hot-reload | Live-Neuladen zur Laufzeit |
| **Dinamik Yükleme** | skills/ klasörünü runtime tarama + dynamic import | Dynamic skill loading | Dynamisches Skill-Laden |
| **Regex Routing** | Kullanıcı metnini regex pattern'lerle eşleştirme | Regex-based command routing | Regex-basiertes Routing |

### 🖥️ Kullanıcı Arayüzü / User Interface / Benutzeroberfläche

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Tkinter Desktop UI** | 2200×1320 pencere, özel tema | Desktop UI (Tkinter) | Desktop-Oberfläche (Tkinter) |
| **Konsantrik Halka** | 3 katmanlı animasyonlu durum göstergesi (OrbCanvas) | Animated status indicator | Animierte Statusanzeige |
| **Durum Renkleri** | 🟢 Dinleme 🔵 Konuşma 🟡 Düşünme 🔴 Hata 🟣 Sessiz ⚪ Duraklatıldı | Status colors | Statusfarben |
| **Sol Panel** | Hava durumu, sistem bilgisi, saat | Left info panel | Linkes Informationspanel |
| **Sağ Panel** | Log, debug, ayarlar sekmesi | Right panel (log, debug, settings) | Rechtes Panel (Log, Debug, Einstellungen) |
| **Kontrol Paneli** | Sessize alma, duraklatma, ses efekti kontrolü | Control bar | Kontrollleiste |
| **Kurulum Sihirbazı** | İlk çalıştırmada SetupDialog (API anahtarı, TTS seçimi) | First-run setup wizard | Ersteinrichtungsassistent |
| **Web Arayüzü** | Opsiyonel HTTP/WebSocket web UI | Optional web UI | Optionale Weboberfläche |
| **Ses Efektleri** | SFX/HUD.mp3 — açılış/kapanış sesleri | Sound effects | Soundeffekte |
| **Koyu Tema** | Özel renk paleti, font ve boyut sabitleri | Dark theme | Dunkles Design |

### 📂 Sistem & Dosya Yönetimi / System & File Management / System & Dateiverwaltung

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Uygulama Açma** | 50+ uygulama alias sistemi ile hızlı erişim (tüm platformlar) | App launcher (50+ aliases) | App-Starter (50+ Aliase) |
| **Sistem Bilgisi** | CPU, RAM, Disk, Pil, Saat, Tarih, Ağ sorgulama | System information | Systeminformationen |
| **Sistem Sağlığı** | Sağlık taraması, disk doluluk tahmini, geçici dosya temizliği | System health check | Systemdiagnose |
| **Dosya Yönetimi** | Büyük dosya bulma, yinelenen dosya tespiti, klasör temizlik | File management | Dateiverwaltung |
| **Dosya İzleme** | Gerçek zamanlı dosya sistemi izleyici (watchdog) | File system watcher | Dateisystem-Überwacher |
| **Süreç Yönetimi** | Süreç listeleme, durdurma, zaman çizelgesi | Process management | Prozessverwaltung |
| **Servis Yönetimi** | Sistem servislerini listeleme/başlatma/durdurma | Service management | Dienstverwaltung |

### 🌐 Ağ & İletişim / Network & Communication / Netzwerk & Kommunikation

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Ağ İzleme** | Bağlantı listesi, ping testi, bant genişliği takibi | Network monitoring | Netzwerküberwachung |
| **Anomali Tespiti** | Ağ anomali algılama | Network anomaly detection | Netzwerkanomalie-Erkennung |
| **Tarayıcı Kontrolü** | URL açma, Google arama, YouTube oynatma | Browser control | Browser-Steuerung |
| **WhatsApp** | WhatsApp Web/Desktop üzerinden mesaj gönderme, kişi kaydetme | WhatsApp messaging | WhatsApp-Nachrichten |
| **Shell Komutları** | Güvenlik filtreli komut çalıştırma (tüm platformlar) | Shell commands (security filtered) | Shell-Befehle (sicherheitsgefiltert) |

### 📅 Takvim & Planlama / Calendar & Scheduling / Kalender & Planung

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Takvim Yönetimi** | Etkinlik okuma/ekleme/silme (Windows takvimi, ICS) | Calendar management | Kalenderverwaltung |
| **Hatırlatıcılar** | Apple Reminders (macOS) ve yerel hatırlatıcı ekleme/listeleme | Reminders | Erinnerungen |
| **Zamanlanmış Görevler** | Cron benzeri görev zamanlama, web arayüzü | Task scheduling (cron-like) | Aufgabenplanung (cron-ähnlich) |

### 🌤️ Medya & Bilgi / Media & Information / Medien & Informationen

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Hava Durumu** | wttr.in API ile anlık hava durumu, 50+ şehir desteği | Weather (wttr.in) | Wetter (wttr.in) |
| **Medya Oynatma** | YouTube, Spotify, Apple Music desteği | Media playback (YouTube/Spotify/Apple) | Medienwiedergabe (YouTube/Spotify/Apple) |
| **YouTube Analizi** | Kanal istatistikleri, abone/izlenme raporu, video performansı | YouTube channel analytics | YouTube-Kanalanalyse |
| **Konum Tespiti** | IP adresine göre yaklaşık konum | Location detection | Standortermittlung |
| **Ekran Analizi** | Ekran görüntüsü + Gemini Vision ile AI analizi (hata okuma, buton tespiti) | Screen analysis (Gemini Vision) | Bildschirmanalyse (Gemini Vision) |

### 🔒 Güvenlik / Security / Sicherheit

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Shell Bloklist** | Tehlikeli komutlar engellenir (rm, sudo, dd, shutdown, vb.) | Shell command blocklist | Shell-Befehlssperrliste |
| **Input Validasyonu** | Karakter sınırları, tool adı whitelist | Input validation | Eingabevalidierung |
| **API Anahtar Koruması** | config/api_keys.json → .gitignore ile koruma | API key protection | API-Schlüsselschutz |
| **Command Timeout** | Tüm shell komutları 30sn timeout ile sınırlı | 30-second command timeout | 30-Sekunden-Befehlszeitlimit |
| **Tool Whitelist** | Sadece kayıtlı araçlar çalıştırılabilir | Tool name whitelist | Werkzeugnamen-Whitelist |

### 🧠 Bellek & Durum / Memory & State / Speicher & Zustand

| 🇹🇷 Özellik | 🇹🇷 Açıklama | 🇬🇧 English | 🇩🇪 Deutsch |
|-------------|-------------|-------------|-------------|
| **Kalıcı Bellek** | Kullanıcı tercihleri ve geçmişi JSON dosyasında saklama | Persistent memory (JSON) | Dauerhafter Speicher (JSON) |
| **Durum Makinesi** | LISTENING→THINKING→SPEAKING→ERROR thread-safe geçişler | Thread-safe state machine | Thread-sichere Zustandsmaschine |
| **Queue IPC** | Thread-safe _gui_queue ile UI iletişimi | Queue-based IPC | Warteschlangenbasierte IPC |

---

## 🚀 Hızlı Kurulum / Quick Setup / Schnellinstallation

### Gereksinimler / Requirements / Voraussetzungen

- Python 3.10+ (3.13 önerilir / recommended / empfohlen)
- **Windows** 10/11 · **Linux** (test: Ubuntu 24+, Debian 12+) · **macOS**
- Ses giriş/çıkış donanımı (mikrofon + hoparlör) / microphone + speaker / Mikrofon + Lautsprecher
- İnternet bağlantısı (Gemini modu için, Ollama offline çalışır) / Internet (Gemini) or offline (Ollama)

### 1. Depoyu Klonla / Clone / Klonen

```bash
git clone <repo-url> jarvis
cd jarvis
```

### 2. Sanal Ortam Oluştur / Virtual Environment / Virtuelle Umgebung

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Bağımlılıkları Yükle / Install Dependencies / Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 4. API Anahtarını Yapılandır / Configure API Key / API-Schlüssel konfigurieren

`config/api_keys.json` dosyasına Gemini API anahtarını girin:

```json
{
  "gemini_api_key": "AIzaSy...",
  "voice": "Charon",
  "backend_type": "gemini",
  "ollama_model": "qwen2.5:1.5b",
  "ollama_tts_voice": "piper-fahrettin",
  "youtube_api_key": "",
  "youtube_channel_handle": ""
}
```

Alternatif: `config/api_keys.example.json` dosyasını kopyalayıp düzenleyin.

### 5. RNNoise Gürültü Bastırma (opsiyonel / optional)

```bash
python scripts/install_rnnoise.py
```

RNNoise C kütüphanesini otomatik indirir/derler (`audio/lib/librnnoise.so` / `.dll` / `.dylib`).  
Kütüphane yoksa JARVIS bypass modunda çalışır — gürültü bastırma olmaz, uygulama devam eder.

### 6. Otomatik Kurulum / Auto Setup (opsiyonel / optional)

**Windows:**
```powershell
.\setup.ps1
```

**Linux / macOS:** (manuel kurulum önerilir / manual setup recommended / manuelle Einrichtung empfohlen)

---

## 🎮 Kullanım / Usage / Verwendung

**Windows:**
```powershell
.venv\Scripts\Activate.ps1
python main.py
```

**Linux / macOS:**
```bash
source .venv/bin/activate
python3 main.py
```

### UI Kontrolleri / Controls / Steuerung

| 🇹🇷 Kontrol | 🇹🇷 İşlev | 🇬🇧 Function | 🇩🇪 Funktion |
|-------------|----------|-------------|-------------|
| 🟢 Dinleme | Mikrofon açık, komut bekliyor | Listening — awaiting command | Hört zu — wartet auf Befehl |
| 🔵 Konuşma | JARVIS yanıt veriyor | Speaking — responding | Spricht — Antwortet |
| 🟡 Düşünme | İşlem yapılıyor | Thinking — processing | Denkt — Verarbeitet |
| 🔴 Hata | Bir sorun oluştu | Error — something went wrong | Fehler — Etwas ist schiefgelaufen |
| 🟣 Sessiz | Ses çıkışı kapalı | Muted — audio output off | Stumm — Audioausgabe aus |
| ⚪ Duraklatıldı | Tüm işlemler durdu | Paused — all operations stopped | Pausiert — Alle Vorgänge gestoppt |

---

## 🏗 Mimarî / Architecture / Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                      JARVIS Çekirdeği / Core                 │
│                        main.py (JarvisLive)                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Gemini AI   │    │   Ollama     │    │    Tkinter   │   │
│  │  (cloud)     │    │  (local)     │    │    UI (ui)   │   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │           │
│         ▼                   ▼                   ▼           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Actions Modülleri (20+)                   │   │
│  │  open_app  sys_info  weather  calendar  reminders    │   │
│  │  browser   shell    whatsapp  media   youtube_stats  │   │
│  │  screen_vision  tts  system_doctor  process_manager  │   │
│  │  file_guardian  network_monitor  system_cron  ...    │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │          Ses İşleme / Audio Pipeline                  │   │
│  │  RNNoise → VAD → Wake Word → STT → TTS              │   │
│  └──────────────────────────────────────────────────────┘   │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Skill Sist. │    │   ACA Agent  │    │  Tool Reg.   │   │
│  │ (17 module)  │    │ (O-P-E-R)    │    │  (44 tools)  │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 🧠 Çekirdek Bileşenler / Core Components / Kernkomponenten

| 🇹🇷 Bileşen | 🇹🇷 Açıklama | 📁 Dizin |
|-------------|-------------|----------|
| **Orkestratör** | JarvisLive ana controller — provider, tool dispatch, state machine | `main.py` |
| **Provider Base** | Soyut backend arayüzü (Gemini/Ollama ortak API) | `core/provider_base.py` |
| **Gemini Provider** | Gemini Live Audio API — sesli streaming diyalog | `core/gemini_provider.py` |
| **Ollama Provider** | Ollama HTTP — yerel STT + chat + TTS | `core/ollama_provider.py` |
| **Tool Registry** | 44 tool tanımı + declaration üreteci + handler haritası | `core/tool_registry.py` |
| **Skill Manager** | Skill yükleyici, hot-reload watcher, routing motoru | `core/skill_manager.py` |
| **ACA Agent** | Otonom çok adımlı görev yürütücü (O-P-E-R döngüsü) | `core/agent/` |
| **UI Katmanı** | Tkinter arayüz + OrbCanvas + SetupDialog + Web UI | `ui.py`, `ui/` |
| **Ses İşleme** | RNNoise, VAD, Wake Word, Streaming STT, TTS | `audio/`, `core/streaming_stt.py` |

---

## 📁 Dizin Yapısı / Directory Structure / Verzeichnisstruktur

```
jarvis/
├── main.py                  # 🧠 Ana uygulama / Core orchestrator
├── ui.py                    # 🖥 Tkinter UI (1818 satır)
├── app_config.py            # ⚙️ Yapılandırma yönetimi
│
├── audio/                   # 🎤 Ses işleme
│   ├── noise_suppressor.py  # RNNoise gürültü bastırma (271 satır)
│   ├── microphone.py        # SoundDevice mikrofon akışı
│   └── lib/                 # RNNoise C kütüphanesi
│
├── actions/                 # 🔧 İşlem modülleri (20+)
│   ├── open_app.py          # Uygulama açma (50+ alias)
│   ├── sys_info.py          # Sistem bilgisi
│   ├── weather.py           # Hava durumu (wttr.in)
│   ├── calendar.py          # Takvim yönetimi
│   ├── reminders.py         # Hatırlatıcı yönetimi
│   ├── browser.py           # Tarayıcı kontrolü
│   ├── shell.py             # Güvenli shell komutları
│   ├── whatsapp.py          # WhatsApp mesajlaşma
│   ├── media.py             # Medya oynatma
│   ├── youtube_stats.py     # YouTube kanal analizi
│   ├── screen_vision.py     # Ekran görüntüsü + Vision AI
│   ├── tts.py               # Text-to-Speech (3 backend)
│   ├── system_doctor.py     # Sistem sağlık raporu
│   ├── process_manager.py   # Süreç yönetimi
│   ├── file_guardian.py     # Dosya yönetimi
│   ├── network_monitor.py   # Ağ izleme
│   ├── system_cron.py       # Zamanlanmış görevler
│   ├── service_monitor.py   # Servis yönetimi
│   ├── disk_predictor.py    # Disk doluluk tahmini
│   ├── process_timeline.py  # Süreç zaman çizelgesi
│   ├── network_anomaly.py   # Ağ anomali tespiti
│   ├── cron_web_ui.py       # Cron web arayüzü
│   └── watchdog/            # Dosya sistemi izleyici
│
├── core/                    # 🧠 Çekirdek
│   ├── provider_base.py     # Abstract BaseProvider
│   ├── gemini_provider.py   # Gemini Live API provider
│   ├── ollama_provider.py   # Ollama HTTP provider
│   ├── tool_registry.py     # 44 tool tek kaynağı
│   ├── skill_manager.py     # Skill yükleyici & router
│   ├── streaming_stt.py     # Gerçek zamanlı STT
│   ├── hardware_detector.py # Donanım algılama
│   └── agent/               # ACA Agent subsystem
│       ├── agent_manager.py # Agent yöneticisi
│       ├── observer.py      # Durum izleyici
│       ├── planner.py       # Görev planlayıcı
│       ├── executor.py      # Görev yürütücü
│       └── reflection.py    # Değerlendirici
│
├── skills/                  # 🧩 Skill modülleri (17 adet)
│   ├── browser/             # Tarayıcı kontrolü
│   ├── weather/             # Hava durumu
│   ├── media/               # Medya oynatma
│   ├── network/             # Ağ izleme
│   ├── calendar/            # Takvim yönetimi
│   ├── reminders/           # Hatırlatıcılar
│   ├── youtube/             # YouTube analizi
│   ├── vision/              # Ekran analizi
│   ├── whatsapp/            # WhatsApp mesajlaşma
│   ├── system_health/       # Sistem sağlığı
│   ├── process_control/     # Süreç kontrolü
│   ├── file_manager/        # Dosya yönetimi
│   ├── scheduler/           # Görev zamanlama
│   ├── services/            # Servis yönetimi
│   ├── greeting/            # Karşılama
│   ├── debugging_jarvis/    # Hata ayıklama
│   └── voice_coding/        # Sesli kodlama
│
├── ui/                      # 🎨 UI alt bileşenleri
│   ├── orb_canvas.py        # Konsantrik halka animasyonu
│   ├── sound_manager.py     # Ses efektleri (SFX)
│   ├── setup_dialog.py      # İlk kurulum sihirbazı
│   ├── theme.py             # Renk/font/boyut sabitleri
│   └── draw_utils.py        # Canvas çizim yardımcıları
│
├── config/                  # ⚙️ Yapılandırma
│   ├── api_keys.json        # API anahtarları (gitignore)
│   ├── api_keys.example.json
│   └── audio.yaml           # Ses yapılandırması
│
├── memory/                  # 💾 Kalıcı bellek
├── voice/                   # 🔊 Ses modelleri (STT/TTS)
├── tests/                   # 🧪 Testler (1463 test, 0 failure)
├── docs/                    # 📚 Dokümantasyon (20+ .md)
├── Icon/ SFX/ Fonts/        # 🎨 UI kaynakları
└── helpers/bin/             # 🔧 Binary bağımlılıklar
```

---

## ⚙️ Yapılandırma / Configuration / Konfiguration

### API Anahtarları / API Keys (`config/api_keys.json`)

| 🇹🇷 Anahtar | Durum | 🇹🇷 Açıklama |
|-------------|-------|-------------|
| `backend_type` | ✅ Zorunlu | `"gemini"` veya `"ollama"` — backend seçimi |
| `voice` | ✅ Zorunlu | Gemini ses modeli (varsayılan: `Charon`) |
| `gemini_api_key` | ⚠️ Gemini modunda zorunlu | Google Gemini AI API anahtarı |
| `ollama_model` | ⚠️ Ollama modunda zorunlu | Ollama model adı (varsayılan: `qwen2.5:1.5b`) |
| `ollama_tts_voice` | ⭐ Önerilen | Yerel TTS sesi (varsayılan: `piper-fahrettin`) |
| `youtube_api_key` | — Opsiyonel | YouTube Data API anahtarı |
| `youtube_channel_handle` | — Opsiyonel | YouTube kanal handle'ı |

### UI Ayarları / UI Settings / UI-Einstellungen

UI ayarları uygulama içi `Settings` panelinden yapılır:

| 🇹🇷 Ayar | 🇹🇷 Açıklama | 🇬🇧 Setting | 🇩🇪 Einstellung |
|----------|-------------|-------------|-----------------|
| Backend | Gemini / Ollama seçimi | Backend selection | Backend-Auswahl |
| Voice | Ses modeli (Charon, Puck, Aoede, Kore, ...) | Voice model | Stimmenmodell |
| Ollama Model | Yerel model adı | Local model name | Lokaler Modellname |
| Ollama TTS Voice | Yerel TTS sesi | Local TTS voice | Lokale TTS-Stimme |

---

## 🔧 Geliştirici Bilgisi / Developer Info / Entwicklerinformationen

### Kod İstatistikleri / Code Stats / Code-Statistik

| 🇹🇷 Ölçüt | 🇹🇷 Değer | 🇬🇧 Metric | 🇩🇪 Metrik |
|-----------|----------|-----------|-----------|
| Python satırı | ~11,000+ | Lines of Python | Python-Zeilen |
| Python dosyası | 45+ | Python files | Python-Dateien |
| Action modülü | 20+ | Action modules | Aktionsmodule |
| Skill modülü | 17 | Skill modules | Skill-Module |
| Tool sayısı | 44 | Registered tools | Registrierte Werkzeuge |
| Test sayısı | 1463 (0 failure, 2 skip) | Tests | Tests |
| UI satırı | ~2,300 | UI lines | UI-Zeilen |
| Çekirdek satırı | ~2,000 | Core lines | Kern-Zeilen |
| Döküman dosyası | 20+ | Documentation files | Dokumentationsdateien |

### Test / Testing / Tests

```bash
python3 -m unittest discover tests -v
# veya / or
python -m unittest discover tests -v
```

### Dökümantasyon / Documentation / Dokumentation

Tüm dökümanlar `docs/` klasöründe:
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — Sistem mimarisi
- [AUDIO_PIPELINE.md](docs/AUDIO_PIPELINE.md) — Ses işleme hattı
- [TOOL_REGISTRY.md](docs/TOOL_REGISTRY.md) — 44 aracın tam listesi
- [SKILLS.md](docs/SKILLS.md) — Skill sistemi detayları
- [AGENTS.md](docs/AGENTS.md) — ACA Agent sistemi
- [UI_LAYER.md](docs/UI_LAYER.md) — Tkinter arayüz katmanı
- [STT_TTS.md](docs/STT_TTS.md) — Konuşma sentezi detayları
- [TECHNOLOGIES.md](docs/TECHNOLOGIES.md) — Teknoloji yığını
- [ORCHESTRATOR.md](docs/ORCHESTRATOR.md) — Orkestrasyon katmanı
- [SECURITY.md](docs/SECURITY.md) — Güvenlik modeli
- [CONFIGURATION.md](docs/CONFIGURATION.md) — Yapılandırma
- [API_REFERENCE.md](docs/API_REFERENCE.md) — Dahili API referansı
- [TESTING.md](docs/TESTING.md) — Test stratejisi
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) — Sorun giderme
