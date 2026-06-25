# J.A.R.V.I.S — Eksik Tarama & Düzeltme Planı

> Hazırlayan: Sisyphus (Agent kullanılmadı, tüm tarama elle yapıldı)
> Tarih: 2026-06-10
> Test: 2512 test OK (100s)

---

## ✅ FSC WAVE 1 — Bare Except & Bug Fix (2026-06-25)

**Kapsam:** FSC plan.md items 1-17 — 7 dosyada 60 satır değişiklik.

| # | Değişiklik | Kanıt |
|---|-----------|-------|
| WF1 | `web_ui.py` destroy() bare except → log | `print(f"[WebUI] Error during destroy: {e}")` |
| WF2 | `replace_stt.py` cleanup bare except → log | `print(f"[Ollama STT] Cleanup error: {e}")` |
| WF3 | `app_config.py` 3 bare except → log | `print(f"[App Config] Error ... : {e}")` |
| WF4 | `ollama_provider.py` 7 bare except → specific exception + log | Her caught exception loglanıyor |
| WF5 | `orchestrator.py` _distribute() 9 bare except → `logger.debug()` | `logger.debug("[AudioPipeline] ... error: %s", e)` |
| WF6 | `debugging_jarvis_skill.py` exec() → `_SAFE_MODULES` allowlist | Modül adı validation |
| WF7 | `voice_manager.py` bare except → log | `print(f"[VoiceManager] Config load error: {e}")` |
| WF8 | `ollama_provider.py` _stt_listen_loop → `finally` cleanup log | Resource leak koruması |

**Test:** 2512 passed (1 pre-existing failure, 4 skipped)

---

## ✅ ÖNCEDEN DÜZELTİLENLER (doğrula, dokunma)

| # | Sorun | Durum | Kanıt |
|---|-------|-------|-------|
| F1 | `actions/__init__.py` — `"detect_network_anomalies"` hayalet `__all__` girişi | ✅ Düzeltildi | `from actions import scan_network_anomalies, check_ip` çalışıyor |
| F2 | `vision/__init__.py` eksik (2 dosya import ediyor) | ✅ Oluşturuldu | `from vision import CameraCapture` çalışıyor |
| F3 | `actions/watchdog/__init__.py` eksik | ✅ Oluşturuldu | `from actions.watchdog import FileWatcher` çalışıyor |
| F4 | 15 test dosyası smoke suite'te yok | ✅ Eklendi | Smoke test 910→2512 test'e çıktı |

---

## 📋 DÜZELTİLMESİ GEREKENLER (öncelik sırasına göre)

### DALGA 1 — Kod Kalitesi (Yüksek Öncelik)

| ID | Dosya | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **Q1** | `core/proactive_voice.py` | **9 fonksiyonda dönüş tipi eksik** | Tüm `def`'lere `->` tip imzası ekle | 5 dk |
| **Q2** | `core/streaming_tts.py` | **9 fonksiyonda dönüş tipi eksik** | Tip imzalarını ekle | 5 dk |
| **Q3** | `core/emotion_tts.py` | **6 fonksiyonda dönüş tipi eksik** | Tip imzalarını ekle | 3 dk |
| **Q4** | `core/streaming_stt.py` | **4 fonksiyonda dönüş tipi eksik** | Tip imzalarını ekle | 3 dk |
| **Q5** | `core/thinking_aloud.py` | **3 fonksiyonda dönüş tipi eksik** | Tip imzalarını ekle | 2 dk |
| **Q6** | `core/ollama_provider.py` | **1 fonksiyonda dönüş tipi eksik** | Tip imzası ekle | 1 dk |
| **Q7** | `core/skill_manager.py` | **1 fonksiyonda dönüş tipi eksik** | Tip imzası ekle | 1 dk |

**Toplam Q1-Q7**: ~20 dk, 33 fonksiyona tip imzası eklenecek.

### DALGA 2 — Test Kapsamı (Orta Öncelik)

| ID | Modül | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **T1** | `actions/youtube_stats.py` | **Hiç test dosyası yok** | `tests/test_youtube_stats.py` oluştur (mevcut test_youtube.py'den ayrıştır) | 15 dk |
| **T2** | `skills/browser/` | **Skill testi yok** | `tests/test_skill_browser.py` oluştur | 10 dk |
| **T3** | `skills/weather/` | **Skill testi yok** | `tests/test_skill_weather.py` oluştur | 10 dk |
| **T4** | `skills/media/` | **Skill testi yok** | `tests/test_skill_media.py` oluştur | 10 dk |
| **T5** | `skills/network/` | **Skill testi yok** | `tests/test_skill_network.py` oluştur | 10 dk |
| **T6** | `skills/reminders/` | **Skill testi yok** | `tests/test_skill_reminders.py` oluştur | 10 dk |
| **T7** | `skills/calendar/` | **Skill testi yok** | `tests/test_skill_calendar.py` oluştur | 10 dk |
| **T8** | `skills/vision/` | **Skill testi yok** | `tests/test_skill_vision.py` oluştur | 10 dk |
| **T9** | `skills/whatsapp/` | **Skill testi yok** | `tests/test_skill_whatsapp.py` oluştur | 10 dk |
| **T10** | `skills/youtube/` | **Skill testi yok** | `tests/test_skill_youtube.py` oluştur | 10 dk |
| **T11** | `skills/debugging_jarvis/` | **Skill testi var ama smoke suite'te değil** | Smoke'a eklendi ✅ | — |
| **T12** | Her yeni test için | **Smoke suite'e ekle** | `test_smoke.py`'ye import satırı ekle | 1 dk/test |

**Toplam T1-T12**: ~105 dk, 10 yeni test dosyası.

### DALGA 3 — Ölü Kod / Temizlik (Düşük Öncelik)

| ID | Dosya | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **D1** | `replace_stt.py` (184 satır) | **Bir kerelik migration script'i, artık kullanılmıyor** | Sil veya `scripts/archive/`'a taşı | 2 dk |
| **D2** | `web_ui.py` (105 satır) | **`pywebview` dependency'si yorum satırında, çalışmaz durumda** | Sil veya dependency'i aktifleştir + uyarı ekle | 5 dk |
| **D3** | `helpers/bin/README.md` | **Boş `bin/` dizini, klasörün tek içeriği README** | Sil veya binary'leri ekle | 2 dk |
| **D4** | `captures/` | **Boş dizin, hiçbir şey içermiyor** | Sil (git'te yoksa) | 1 dk |
| **D5** | `assets/thinking_phrases.json` | **Tek dosya, kullanılıyor mu kontrol et** | Doğrula, kullanılmıyorsa arşivle | 3 dk |
| **D6** | `setup_report_*.txt` (2 dosya) | **Root'ta dağınık duran setup raporları** | `.gitignore`'a ekle veya sil | 1 dk |

**Toplam D1-D6**: ~14 dk.

### DALGA 4 — Dokümantasyon Güncelleme (Düşük Öncelik)

| ID | Dosya | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **M1** | `README.md` | "1976 test" yazıyor, gerçek: 2512 | Test sayısını güncelle | 2 dk |
| **M2** | `CLAUDE.md` | Eski docs/ yapısını referans alıyor | docs/ satır sayılarını güncelle | 5 dk |
| **M3** | `.gitignore` | `setup_report_*.txt` ve geçici test dosyaları gitignore'da yok | Ekle | 1 dk |

**Toplam M1-M3**: ~8 dk.

---

## ✅ TAMAMLANANLAR

| Dalga | İş | Tarih |
|-------|-----|-------|
| **FSC Wave 1** — Bug Fix | 7 dosyada bare except fix + exec allowlist + resource leak | 2026-06-25 ✅ |
| Test | 1119 → 2512 (81 dosya, tüm skill testleri) | ✅ |

## ⏱ KALAN SÜRE TAHMİNİ

| Dalga | İş | Süre |
|-------|-----|------|
| 1 — Kod Kalitesi | 33 fonksiyona tip imzası | ~20 dk |
| 2 — Test Kapsamı | 10 yeni test dosyası | ~105 dk |
| 3 — Ölü Kod | 6 dosya/dizin temizliği | ~14 dk |
| 4 — Dokümantasyon | 3 dosyada güncelleme | ~8 dk |
| **Toplam** | **19 iş kalemi** | **~147 dk (~2.5 saat)** |

---

## 🔍 TARAMADA BULUNAN AMA SORUN OLMAYANLAR (bilgi amaçlı)

| Konu | Açıklama |
|------|----------|
| `voice/` dizini 2.1 GB | faster-whisper STT modeli + Piper TTS sesi — normal, `.gitignore`'da |
| `memory/*.db` dosyaları | SQLite veritabanları (cron, disk_history, process_timeline) — normal çalışma |
| `logs/` 88K | Log dosyaları — normal, `.gitignore`'da |
| `config/api_keys.json` | API key'ler — normal, `.gitignore`'da |
| `# pywebview` yorum satırı | Bilinçli seçim (bağımlılık eklenmemiş) |
| 142 `print()` çağrısı | Proje genelinde tutarlı `[PREFIX]` pattern'i kullanılıyor, refactor büyük iş |

---

## 🚀 ÖNERİLEN İŞ AKIŞI

```
1. DALGA 1 (type hints)      → ~20dk → 20dk
2. Smoke test kontrol         → ~2dk  → 22dk
3. DALGA 3 (ölü kod temizlik) → ~14dk → 36dk
4. Smoke test kontrol         → ~2dk  → 38dk
5. DALGA 4 (dokümantasyon)   → ~8dk  → 46dk
6. DALGA 2 (test kapsamı)    → ~105dk → 2.5 saat
```

> Not: DALGA 2 en uzun süren iş. Önce DALGA 1-3-4'ü bitirip sağlam bir temel oluşturmak, sonra DALGA 2'ye (test yazma) girmek önerilir.
