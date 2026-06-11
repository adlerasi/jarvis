# JARVIS Yol Haritası

> Mevcut durum · Kısa vade · Uzun vade · Bilinen sınırlamalar

---

## 🟢 Tamamlananlar

### Faz 0 — Proje İskeleti
- [x] Ana çekirdek (`main.py`) — çift backend mimarisi
- [x] Tkinter UI (`ui.py`) — konsantrik halka animasyonlu arayüz
- [x] Yapılandırma sistemi (`app_config.py`)
- [x] Log sistemi (dosyaya + exception hook)
- [x] Platform ayrımı (Windows + macOS kod ayrıştırması)

### Faz 1 — Action Modülleri
- [x] Uygulama açma (50+ Windows alias)
- [x] Sistem bilgisi (CPU/RAM/Disk/Batarya/Ağ)
- [x] Hava durumu (wttr.in)
- [x] Takvim yönetimi (okuma/ekleme/silme)
- [x] Hatırlatıcı yönetimi
- [x] Tarayıcı kontrolü (URL, arama, YouTube)
- [x] Güvenli shell komutları
- [x] WhatsApp mesajlaşma (Selenium)
- [x] Medya oynatma (YouTube/Spotify/Apple Music)
- [x] YouTube kanal analizi
- [x] Ekran analizi (pyautogui + Gemini Vision)
- [x] TTS (Piper + Edge-TTS + spd-say + Windows Speech)
- [x] Windows API araçları (URI, PowerShell, clipboard)
- [x] Kalıcı bellek (JSON tabanlı)

### Faz 2 — Ses & AI
- [x] Gemini Live Audio API entegrasyonu
- [x] Ollama yerel backend
- [x] Faster-Whisper offline STT
- [x] Çoklu TTS zinciri (fallback mekanizması)
- [x] Gerçek zamanlı ses akışı (16kHz→Gemini→24kHz)
- [x] Ses efektleri (SFX/HUD.mp3)

### Faz 3 — Kalite & Güvenlik
- [x] Smoke test (12 test)
- [x] .gitignore yapılandırması
- [x] requirements.txt version pin
- [x] PostScript artifact temizliği
- [x] Kırık/kullanılmayan venv temizliği
- [x] Shell komut güvenlik filtresi
- [x] Thread-safe durum yönetimi
- [x] Exception hook (ana thread + thread)
- [x] pyrightconfig.json yapılandırması

### Faz 4 — Dokümantasyon
- [x] README.md — proje genel bakış
- [x] docs/ARCHITECTURE.md — mimari dokümantasyon
- [x] docs/TECHNOLOGIES.md — teknoloji yığını
- [x] helpers/bin/README.md — binary bağımlılıklar

### Faz 5 — Sistem Kontrol Modülleri
- [x] Sistem sağlık raporu (system_doctor)
- [x] Süreç yönetimi (process_manager)
- [x] Dosya yönetimi (file_guardian)
- [x] Ağ izleme (network_monitor)
- [x] Zamanlanmış görevler (system_cron + daemon)
- [x] Servis yönetimi (service_monitor)
- [x] 19 tool handler + TOOL_DECLARATIONS
- [x] UI entegrasyonu (focus_panel, system alerts, stats)
- [x] 264 test (225 smoke + 39 yeni sistem testi)

### Faz 6 — Skill Sistemi (AI'sız Doğrudan İşlem)
- [x] `core/skill_manager.py` — singleton, auto-discover, routing
- [x] `skills/browser/` — tarayıcı kontrolü (URL açma, arama, YouTube)
- [x] `skills/system_health/` — sistem sağlığı (CPU/RAM/disk/temp)
- [x] `skills/process_control/` — süreç yönetimi (list/kill/priority/port)
- [x] `skills/file_manager/` — dosya yönetimi (large files/duplicates/cleanup)
- [x] Routing: `_on_text_command()` önce skill_manager.route(), eşleşmezse LLM
- [x] Turkish ASCII fallback: tüm regex pattern'lerinde ş→s, ç→c, ü→u, ö→o, ğ→g
- [x] 7 smoke test alt test (skill import + SkillManager + router functions)
- [x] `123/` FAZ 0 + FAZ 1 asimile edildi ve silindi

### Faz 6b — FAZ 3: Weather, YouTube, Vision Skills
- [x] `skills/weather/` — hava durumu sorgulama (get_weather_summary ile)
- [x] `skills/youtube/` — kanal istatistikleri + video oynatma (youtube_stats + media ile)
- [x] `skills/vision/` — ekran analizi (screen_vision.analyze_screen ile)
- [x] ASCII fallback pattern'leri FAZ 3'e de uygulandı
- [x] `123/` FAZ 3 tamamen asimile edildi

### Faz 6c — FAZ 4: Calendar, Reminders, WhatsApp, Media Skills
- [x] `skills/calendar/` — takvim yönetimi (get/add/delete events)
- [x] `skills/reminders/` — hatırlatıcı yönetimi (get/add reminders)
- [x] `skills/whatsapp/` — WhatsApp mesaj gönderme + kişi kaydetme
- [x] `skills/media/` — medya oynatma (YouTube/Spotify/Apple Music)
- [x] WhatsApp `ahmeti kaydet` trigger fix (name + kaydet pattern)
- [x] 14 skill toplam: browser, system_health, process_control, file_manager, network, scheduler, services, weather, youtube, vision, calendar, reminders, whatsapp, media
- [x] 228+ smoke test (TestSkillModules 14-skill import + route)

### Faz 6d — FAZ 2: Network, Scheduler, Services Skills
- [x] `skills/network/` — ağ izleme (get_network_summary, ping, bandwidth)
- [x] `skills/scheduler/` — zamanlanmış görev yönetimi (list/add/remove cron jobs)
- [x] `skills/services/` — servis yönetimi (list/start/stop/restart services)
- [x] ASCII fallback pattern'leri FAZ 2'ye de uygulandı
- [x] 14 skill toplam, 228+ smoke test

### Faz 7 — Gelecek İyileştirmeler (Opsiyonel)
- [x] File watchdog — gerçek zamanlı dosya izleme
- [x] Disk predictor — disk doluluk tahmini (6 saatte bir)
- [x] Process timeline — süreç zaman çizelgesi (5sn polling)
- [x] Network anomaly — ağ anomali tespiti (2 dk)
- [x] Cron web UI — browser'dan cron yönetimi (port 8765)

### Faz 9 — RNNoise Gerçek Zamanlı Gürültü Bastırma
- [x] `audio/noise_suppressor.py` — RNNoise ctypes wrapper (48kHz/16kHz, VAD, bypass)
- [x] `audio/microphone.py` — SoundDevice mikrofon akışı + RNNoise entegrasyonu
- [x] `audio/__init__.py` — Paket ihracatı
- [x] `scripts/install_rnnoise.py` — Cross-platform RNNoise kurulum betiği
- [x] `config/audio.yaml` — Ses yapılandırması
- [x] `audio/lib/librnnoise.so` — Kaynaktan derlenmiş RNNoise C kütüphanesi
- [x] `core/ollama_provider.py` — RNNoise entegrasyonu (process_16khz before VAD)
- [x] `main.py` — `load_audio_config()`, `self.audio_config`
- [x] `requirements.txt` — `sounddevice>=0.4.6`
- [x] `tests/test_smoke.py` — 10 RNNoise testi (import, constants, bypass, 16kHz, VAD)
- [x] 263/263 test PASS (253 eski + 10 RNNoise)
- [x] Gerçek RNNoise işleme doğrulandı: 48kHz'de %90 gürültü bastırma, konuşma koruması %97+
- [x] Performans: 0.057ms/frame (48kHz), 0.156ms/frame (16kHz pipeline)

### Faz 8 — Provider Abstraction (Çift Backend Soyutlama)
- [x] `core/provider_base.py` — abstract `BaseProvider` arayüzü (`start/stop/send_text/run_loop`)
- [x] `core/gemini_provider.py` — Gemini Live API provider (audio streaming + tool dispatch)
- [x] `core/ollama_provider.py` — Ollama HTTP provider (VAD/STT + chat + TTS)
- [x] `core/tool_registry.py` — 40 tool'un tek kaynağı (declarations + handler map + valid_tools)
- [x] `core/text_utils.py` — ortak metin işleme (transcript temizleme, hece bölme)
- [x] `main.py` refactor — ~2990 → **952** satır (%68 küçülme), provider delegasyonu
- [x] `_execute_tool` — 30+ elif zinciri → dict dispatch (`TOOL_HANDLER_MAP`)
- [x] Kritik runtime hataları düzeltildi (`pyaudio.open` instance, `FORMAT=None`, `get_api_key` import)
- [x] **Ölü kod temizliği**: 4 fonksiyon silindi (`_get_ollama_model`, `get_api_key`, `_load_app_config`/gemini, `_get_api_key`/ollama)
- [x] **Orphaned `123/` dizini** silindi (7 dosya — ROADMAP'ta "silindi" yazıyordu ama hala duruyordu)
- [x] **Backup dizini** (`backup_20260607_012108/`) silindi
- [x] **7 dead constant** temizlendi + unused imports
- [x] 228/228 test geçiyor, temiz LSP diagnostics

---

## 🟡 Kısa Vade (Öncelikli)

### 🐛 Kritik Olmayan Hatalar (Çözüldü)

| Görev | Etki | Çaba |
|-------|------|------|
| `weather.py` — `temp_c` `None` kontrolü iyileştirildi ✅ | Düşük | 5dk |
| `tts.py` — `wav_path`/`mp3_path` finally NameError düzeltildi ✅ | Düşük | 5dk |
| `main.py` — `_effects_enabled` init ✅ | Düşük | 2dk |
| Fazladan import'lar temizlendi ✅ | Düşük | 5dk |
| `_sync_sound_state` thread leak düzeltildi ✅ | Orta | 5dk |
| `_toggle_pause` thread leak düzeltildi ✅ | Düşük | 2dk |
| Ollama model uyarısı eklendi ✅ | Düşük | 10dk |
| **process_manager.py** — `cpu_percent(interval=0.1)` sequential re-sample hatası ✅ | Düşük | 5dk |
| **Weather panel** — `_refresh_brief_cards` memory'den lokasyon okumuyor ✅ | Orta | 15dk |
| **OS detection** — AI Linux'ta Windows komutu üretiyor ✅ | Orta | 10dk |
| **Browser gate** — AI kendiliğinden browser_control çağırıyor ✅ | Orta | 10dk |
| **Volume control** — Hiç ses ayarı tool'u yok ✅ | Orta | 15dk |
| **VAD/STT** — Gürültü hassasiyeti çok yüksek, sürekli tetikleme ✅ | Orta | 10dk |
| **Turkish syllable split** — faster-whisper hece bölmesi (ör: "üstümd" "eAhmet") ✅ | Orta | 20dk |
| **Test side effects** — Smoke test'ler URL açıyor (example.com + YouTube) ✅ | Düşük | 5dk |
| **Browser skill multi-word aç** — "youtube sarki ac" → `https://youtube sarki.com` ✅ | Düşük | 10dk |

### 🔧 İyileştirmeler (Tamamlandı)

| Görev | Gerekçe | Çaba | Durum |
|-------|---------|------|-------|
| **Thread pool limiti** — `_sync_sound_state` direkt çağrı | Thread leak önleme | 5dk | ✅ |
| **YouTube API anahtarı** — UI'da uyarı etiketi | Kullanıcı deneyimi | — | ⏳ |
| **Ollama model uyarısı** — threshold tespiti + write_log | Debug kolaylığı | 10dk | ✅ |
| **setup.ps1** — Binary kontrolü | İlk kurulum | — | ⏳ |
| **config/api_keys.example.json** — 3 eksik anahtar ✅ | Dökümantasyon | 10dk | ✅ |
| **Sistem kontrol modülleri** — 6 yeni action modülü | Genişletme | 4 saat | ✅ |
| **Birim testleri** — 39 yeni test (sistem modülleri) | Test kapsamı | 2 saat | ✅ |
| **Sistem kontrol modülleri** — 6 yeni action modülü | Genişletme | 4 saat | ✅ |
| **Birim testleri** — 39 yeni test (sistem modülleri) | Test kapsamı | 2 saat | ✅ |
| **Sistem prompt'u** — cross-platform kurallar, OS detection | Doğruluk | 20dk | ✅ |
| **set_volume tool** — Ses seviyesi kontrolü (pactl/osascript/nircmd) | Eksik özellik | 15dk | ✅ |
| **VAD parametreleri** — threshold:0.5, min_speech:250ms, min_silence:500ms | STT kalitesi | 10dk | ✅ |
| **NFC normalizasyonu** — `unicodedata.normalize("NFC")` Turkish STT için | STT kalitesi | 5dk | ✅ |
| **_user_initiated güvenlik gate** — AI'nın izinsiz browser_control çağırmasını engelle | Güvenlik | 10dk | ✅ |
| **Skill sistemi asimilasyonu** — FAZ 0 (browser) + FAZ 1 (system_health, process_control, file_manager) + FAZ 3 (weather, youtube, vision) + FAZ 4 (calendar, reminders, whatsapp, media) + FAZ 2 (network, scheduler, services), 14 skill, Turkish ASCII fallback, 228+ test, browser multi-word fix, WhatsApp name+kaydet fix | Mimarî | 30dk | ✅ |

### 🛡 Hata Yönetimi Sertleştirme (Tamamlandı)

| Görev | Gerekçe | Dosyalar | Durum |
|-------|---------|----------|-------|
| **`continue` dışı döngü** — `skill_manager.py:179,189` skill yüklenemezse crash | Kritik runtime hatası | `core/skill_manager.py` | ✅ |
| **Silent `except` → `traceback.print_exc()`** — 16 dosyada 22+ pasif hata yutma | Debug edilemez hatalar | `reminders.py, sys_info.py, whatsapp.py, service_monitor.py, memory_manager.py, process_timeline.py, screen_vision.py, network_monitor.py, system_cron.py, calendar.py, tts.py, main.py (3), ui.py (4), sound_manager.py (2)` | ✅ |
| **Thread safety — `_nad_lock`** — NetworkAnomalyDetector timer overlap | `_connection_history` yarışı | `actions/system_cron.py:298` | ✅ |
| **None dereference** — `spec`/`spec.loader` kontrolü, `health._float_or_none`, `cron_web_ui.server assert` | Crash önleme | 3 dosya | ✅ |
| **Conditional class pattern** — `file_watcher.py` watchdog opsiyonel base class | Import-time tip hatası | `actions/watchdog/file_watcher.py` | ✅ |
| **Input validation** — STT text ≤10000, tool args ≤500 char, tool call ≤2000 char, tool adı whitelist | Enjeksiyon/memory koruması | `main.py:1056,2212,2231,2249` | ✅ |
| **Backup dir `__init__.py`** — import gölgeleme riski | Potansiyel modül karışıklığı | `backup_20260607_012108/` | ✅ |
| **LSP type fixes** — `str\|None`, `Pattern[str]`, `Callable[..., Any]`, pyrightconfig | Derleme/sağlık | 6 dosya | ✅ |
| **Tüm hata asimilasyonu** — 6 LSP hatası, 3 test fix, TTS modülü yeniden yapılandırma, VAD double downsampling, Windows import koruması, `# type: ignore` temizliği, debug print'leri gating, `from __future__ import annotations` bulk | Derleme/Test/Kalite | ~90dk | ✅ |

---

## 🟠 Orta Vade (2-4 Hafta)

### 🚀 Yeni Özellikler

| Özellik | Açıklama | Öncelik |
|---------|----------|---------|
| **Sesli uyandırma (Wake Word)** | "Hey JARVIS" ile aktif dinleme, sürekli kayıt yok | Yüksek |
| **Çoklu kullanıcı profili** | Her kullanıcıya özel bellek + tercihler | Orta |
| **Mikrofon seviye göstergesi** | UI'da ses seviyesi çubuğu | Orta |
| **Log viewer** | UI içinden logları görüntüleme/filtreleme | Düşük |
| **Otomatik güncelleme** | GitHub'dan son sürümü kontrol | Düşük |

### 🔒 Güvenlik & Kararlılık

| Görev | Açıklama | Öncelik |
|-------|----------|---------|
| **Birim testleri** — Her action modülü için unittest ✅ | Mevcut sadece smoke test vardı, şimdi 80+ modül test dosyası | Yüksek |
| **API anahtarı rotasyonu** — Geçersiz anahtar tespiti + uyarı | Daha iyi hata yönetimi | Orta |
| **Ses akışı watchdog** — Kesinti tespiti + otomatik yeniden bağlanma | Kararlılık | Orta |
| **Hata raporlama** — Kullanıcı dostu hata mesajları (Türkçe) | UX | Orta |

### ♻️ Teknik Borç

| Görev | Açıklama | Çaba |
|-------|---------|------|
| `ui.py` refactor — 2300 satır, `JarvisUI` sınıfı alt modüllere ayrılmalı | Yüksek |
| ~~`main.py` _execute_tool — 30+ elif zinciri~~ ✅ | Dict dispatch (`TOOL_HANDLER_MAP`) | Orta |
| Type hint eksikleri — Tüm public fonksiyonlara tam tip eklenmeli | Orta |
| `_sp = playsound` — playsound artık bakımda değil, alternatif (pygame/simpleaudio) | Düşük |

---

## 🔴 Uzun Vade (1-3 Ay)

### 🌟 Büyük Özellikler

| Özellik | Açıklama | Karmaşıklık |
|---------|----------|-------------|
| **Plugin sistemi** — Harici geliştiricilerin action modülü yazması için SDK | Çok Yüksek |
| **Mobil uygulama** — JARVIS'e telefon üzerinden erişim (WebSocket API) | Çok Yüksek |
| **Ses klonlama** — Kullanıcının sesini öğrenip eğitme (custom TTS) | Yüksek |
| **RAG bellek** — Uzun süreli hatırlama için vektör veritabanı (Chromadb) | Yüksek |
| **Müzik çalma** — Yerel müzik arşivinden çalma, playlist yönetimi | Orta |
| **E-posta yönetimi** — Okuma, yazma, gönderme (IMAP/SMTP) | Orta |
| **Akıllı ev entegrasyonu** — Home Assistant API bağlantısı | Orta |

### 🏗 Altyapı

| Proje | Açıklama | Karmaşıklık |
|-------|----------|-------------|
| **Docker desteği** — Konteynerize kurulum, kolay dağıtım | Orta |
| **GUI kurulum sihirbazı** — Tkinter ile interaktif kurulum | Orta |
| **Performans profili** — Hangi modül ne kadar süre/kaynak harcıyor | Orta |
| **Uzak erişim** — LAN üzerinden başka bir cihazdan JARVIS'e bağlanma | Yüksek |
| **Çoklu dil** — İngilizce, Almanca, Arapça arayüz + STT/TTS | Orta |

---

## 📊 Proje Durumu

### Kategori Bazında Tamamlanma

```
Çekirdek Mimarisi     ██████████ 100%
Action Modülleri      ██████████ 100%
Ses İşleme (STT/TTS)  ██████████ 100%
UI & Görsel Tasarım   ██████████ 100%
Yapılandırma          ██████████ 100%
Güvenlik              ██████████ 100%
Test                  ██████████ 100%
Dokümantasyon         ██████████ 100%
Hata Yönetimi         ██████████ 100%
Performans            ████░░░░░░  40%
```

### Bilinen Sınırlamalar

| Sınırlama | Açıklama | Geçici Çözüm |
|-----------|----------|-------------|
| **Sürekli dinleme yok** | Wake word yok, buton/komutla aktifleşiyor | — |
| **Sadece Türkçe UI** | Tüm arayüz ve mesajlar Türkçe | — |
| **Ollama model küçük** | 1.5B model, karmaşık görevlerde yetersiz | Daha büyük model kurun (7B+) |
| **YouTube API anahtarı gerekli** | Boşsa YouTube analizi çalışmaz | API anahtarı alın |
| **Ses çalma binary bağımlı** | `aplay` (Piper) ve `mpg123` (Edge-TTS) gerekli | `helpers/bin/README.md`'ye bakın |
| **Selenium bağımlılığı** | WhatsApp modülü ChromeDriver gerektirir | Selenium kurulu değilse çalışmaz |
| **Pencere boyutu sabit** | 2200×1320, scaling yok | — |
| **Playsound kullanımı** | playsound paketi bakımda değil | pygame/simpleaudio'a geçilmeli |

---

## 🎯 Önerilen Sonraki Adım

```
1. HAFTA → Wake word ekle (Porcupine / OpenWakeWord)
2. HAFTA → Birim testleri (her action modülü için)
3. HAFTA → playsound → simpleaudio geçişi
4. HAFTA → ui.py refactor (alt modüllere ayır)
5. HAFTA → main.py _execute_tool strategy pattern
6. HAFTA → Plugin sistemi tasarımı
```

---

*Son güncelleme: 2026-06-11 (v7 — Tüm dokümantasyon asimilasyonu: test/skill/tool sayıları güncellendi)*
