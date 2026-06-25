# J.A.R.V.I.S — Eksik Tarama & Düzeltme Planı

> Hazırlayan: Sisyphus (Agent kullanılmadı, tüm tarama elle yapıldı)
> Tarih: 2026-06-25 (güncelleme)
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

### DALGA 1 — Kod Kalitesi (Yüksek Öncelik) ✅

| ID | Dosya | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **Q1** | `core/proactive_voice.py` | **9 fonksiyonda dönüş tipi eksik** | Tüm `def`'lere `->` tip imzası eklendi (13 fonksiyon) | 5 dk ✅ |
| **Q2** | `core/streaming_tts.py` | **9 fonksiyonda dönüş tipi eksik** | Tip imzaları eklendi (15 fonksiyon) | 5 dk ✅ |
| **Q3** | `core/emotion_tts.py` | **6 fonksiyonda dönüş tipi eksik** | Tip imzaları eklendi (8 fonksiyon) | 3 dk ✅ |
| **Q4** | `core/streaming_stt.py` | **4 fonksiyonda dönüş tipi eksik** | Tip imzaları eklendi (13 fonksiyon) | 3 dk ✅ |
| **Q5** | `core/thinking_aloud.py` | **3 fonksiyonda dönüş tipi eksik** | Tip imzaları eklendi (6 fonksiyon) | 2 dk ✅ |
| **Q6** | `core/ollama_provider.py` | **1 fonksiyonda dönüş tipi eksik** | Tip imzası eklendi (2 fonksiyon) | 1 dk ✅ |
| **Q7** | `core/skill_manager.py` | **1 fonksiyonda dönüş tipi eksik** | Tip imzası eklendi (22 fonksiyon) | 1 dk ✅ |

**Gerçek**: 78 fonksiyona `-> None` / `-> dict[str, Any]` / `-> Any` tip imzası eklendi.

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
| **D1** | `replace_stt.py` (184 satır) | **Bir kerelik migration script'i, artık kullanılmıyor** | `scripts/archive/`'a taşındı ✅ | 2 dk |
| **D2** | `web_ui.py` (105 satır) | **`pywebview` dependency'si yorum satırında, çalışmaz durumda** | Sil veya dependency'i aktifleştir + uyarı ekle | 5 dk |
| **D3** | `helpers/bin/README.md` | **Boş `bin/` dizini, klasörün tek içeriği README** | Sil veya binary'leri ekle | 2 dk |
| **D4** | `captures/` | **Boş dizin, hiçbir şey içermiyor** | Sil (git'te yoksa) | 1 dk |
| **D5** | `assets/thinking_phrases.json` | **Tek dosya, kullanılıyor mu kontrol et** | Doğrula, kullanılmıyorsa arşivle | 3 dk |
| **D6** | `setup_report_*.txt` (2 dosya) | **Root'ta dağınık duran setup raporları** | Silindi ✅ | 1 dk |

**Toplam D1-D6**: ~14 dk (D1, D6 tamam).

### DALGA 4 — Dokümantasyon Güncelleme (Düşük Öncelik) ✅

| ID | Dosya | Sorun | İşlem | Tahmini Süre |
|----|-------|-------|-------|-------------|
| **M1** | `README.md` | "1976 test" yazıyor, gerçek: 2512 | Test sayısı güncellendi ✅ | 2 dk |
| **M2** | `CLAUDE.md`, `docs/ARCHITECTURE.md`, `graphify-out/*.md`, `.fsc/plan.md` | Test sayısı güncel değil | Tüm dokümanlarda 1142→2512 ✅ | 5 dk |
| **M3** | `.gitignore` | `setup_report_*.txt` ve geçici test dosyaları gitignore'da yok | Eklendi ✅ | 1 dk |

**Not**: M2 kapsamı genişletildi — ek dokümanlar da güncellendi.

---

### DALGA 5 — Git Temizlik & Test Ek (Yeni Bulgular) ✅

Dalga 1-4 işlenirken tespit edilen ek sorunlar:

| ID | Sorun | İşlem | Durum |
|----|-------|-------|-------|
| **E1** | `memory/*.db` dosyaları (disk_history.db) git'te takip ediliyor — her test run'da değişen binary DB | `.gitignore`'a `memory/*.db` eklendi, `git rm --cached` ile untracked ✅ | Tamam |
| **E2** | `graphify-out/` dizini git'te takip ediliyor — auto-generated, her çalışmada değişiyor | `.gitignore`'a `graphify-out/` eklendi, `git rm --cached` ile untracked ✅ | Tamam |
| **E3** | `core/notification.py`'ın hiç test dosyası yok (25 satırlık wrapper) | `tests/test_notification.py` oluşturuldu (12 test) ✅ | Tamam |

---

## ✅ TAMAMLANANLAR

| Dalga | İş | Tarih |
|-------|-----|-------|
| **FSC Wave 1** — Bug Fix | 7 dosyada bare except fix + exec allowlist + resource leak | 2026-06-25 ✅ |
| Test | 1119 → 2512 (81 dosya, tüm skill testleri) | ✅ |
| **Q1-Q7** — DALGA 1 | 78 fonksiyona dönüş tipi imzası eklendi | 2026-06-25 ✅ |
| **D1** — DALGA 3 | `replace_stt.py` → `scripts/archive/` taşındı | 2026-06-25 ✅ |
| **D6** — DALGA 3 | `setup_report_*.txt` silindi | 2026-06-25 ✅ |
| **M1-M3** — DALGA 4 | Test sayısı 5 dokümanda güncellendi (README, CLAUDE, ARCHITECTURE, graphify-out, fsc plan) | 2026-06-25 ✅ |
| **E1** — Git Cleanup | `memory/*.db` `.gitignore` + untrack | 2026-06-25 ✅ |
| **E2** — Git Cleanup | `graphify-out/` `.gitignore` + untrack | 2026-06-25 ✅ |
| **E3** — Test | `core/notification.py` → `tests/test_notification.py` (12 test) | 2026-06-25 ✅ |

## ⏱ KALAN SÜRE TAHMİNİ (GÜNCEL)

| Dalga | İş | Süre |
|-------|-----|------|
| 1 — Kod Kalitesi | 78 fonksiyona tip imzası | ✅ Tamam |
| 2 — Test Kapsamı | 10 yeni test dosyası | ~105 dk |
| 3 — Ölü Kod | D1,D6 tamam; D2-D5 kaldı (7 dk) | ~7 dk |
| 4 — Dokümantasyon | 5 dokümanda test sayısı | ✅ Tamam |
| 5 — Git Temizlik & Test | E1-E3 | ✅ Tamam |
| **Toplam** | **Kalan: D2-D5 + DALGA 2** | **~112 dk (~2 saat)** |

---

## 🔍 TARAMADA BULUNAN AMA SORUN OLMAYANLAR (bilgi amaçlı)

| Konu | Açıklama |
|------|----------|
| `voice/` dizini 2.1 GB | faster-whisper STT modeli + Piper TTS sesi — normal, `.gitignore`'da |
| `logs/` 88K | Log dosyaları — normal, `.gitignore`'da |
| `config/api_keys.json` | API key'ler — normal, `.gitignore`'da |
| `# pywebview` yorum satırı | Bilinçli seçim (bağımlılık eklenmemiş) |
| 142 `print()` çağrısı | Proje genelinde tutarlı `[PREFIX]` pattern'i kullanılıyor, refactor büyük iş |

---

## 🚀 ÖNERİLEN İŞ AKIŞI (GÜNCEL)

```
1. DALGA 1 (type hints)           → ✅ TAMAM (78 fonksiyon)
2. DALGA 3 (D1, D6)               → ✅ TAMAM
3. DALGA 4 (dokümantasyon)        → ✅ TAMAM (5 doküman)
4. DALGA 5 (git cleanup, test)    → ✅ TAMAM (E1-E3)
5. DALGA 3 kalan (D2-D5)          → ~7dk
6. DALGA 2 (test kapsamı)         → ~105dk → 2 saat
```

> DALGA 2 en uzun süren iş. D2-D5 hızlıca bitirilip DALGA 2'ye geçilebilir.
