# J.A.R.V.I.S — Test Rehberi

> Test altyapisi, calistirma komutlari, yeni test ekleme kurallari.

---

## Test Altyapisi

| Ozellik | Deger |
|---------|-------|
| Framework | `unittest` |
| Runner | `.venv/bin/python3 -m unittest` |
| Toplam test | 1261 |
| Basarisiz | 0 |
| Atlanan | 2 |
| Mock | `@patch` (sadece yan etki testlerinde) |

---

## Testleri Calistirma

### Tum Testler

```bash
# Linux/macOS
.venv/bin/python3 -m unittest discover tests -v

# Windows
.venv\Scripts\python.exe -m unittest discover tests -v
```

### Smoke Test (Hizli)

```bash
.venv/bin/python3 -m unittest tests.test_smoke -v
```

### Tek Modul

```bash
.venv/bin/python3 -m unittest tests.test_skill_manager -v
.venv/bin/python3 -m unittest tests.test_vad_engine -v
.venv/bin/python3 -m unittest tests.test_text_utils -v
```

### Tek Test Metodu

```bash
.venv/bin/python3 -m unittest tests.test_text_utils.TestTextUtils.test_clean_transcript_text -v
```

### Build Script

```bash
# Linux/macOS
./build.sh

# Windows
.\build.ps1
```

---

## Test Dosya Yapisi

```
tests/
+-- __init__.py
+-- conftest.py                   # Test yapilandirmasi
+-- test_aca_subsystem.py         # ACA subsystem tests
+-- test_actions.py               # Action modulleri
+-- test_app_config.py            # Yapilandirma testleri
+-- test_audio_buffer.py          # Audio buffer
+-- test_audio_queue.py           # Audio queue (voice orchestration)
+-- test_audio_system.py          # Audio system (TTS/STT)
+-- test_barge_in.py              # Barge-in detektoru
+-- test_browser.py               # Browser action
+-- test_calendar.py              # Calendar action
+-- test_config.py                # Config okuma
+-- test_conversation_transcript.py
+-- test_cron_web_ui.py           # Cron web UI
+-- test_disk_predictor.py        # Disk tahmin
+-- test_draw_utils.py            # UI draw utils
+-- test_emotion_tts.py           # Emotion TTS
+-- test_fahrettin_vad.py         # Fahrettin VAD
+-- test_file_guardian.py         # File guardian
+-- test_file_watcher.py          # File watcher
+-- test_health.py                # Health modulu
+-- test_local_llm.py             # Local LLM
+-- test_location.py              # Location action
+-- test_main.py                  # main.py import
+-- test_media.py                 # Media action
+-- test_memory.py                # Memory manager
+-- test_microphone.py            # Microphone stream
+-- test_multimodal.py            # Multimodal engine
+-- test_network_anomaly.py       # Network anomaly
+-- test_network_monitor.py       # Network monitor
+-- test_noise_suppressor.py      # RNNoise suppressor
+-- test_open_app.py              # Open app action
+-- test_orb_canvas.py            # UI orb canvas
+-- test_pipeline.py              # Pipeline testleri
+-- test_proactive_voice.py       # Proactive voice
+-- test_process_manager.py       # Process manager
+-- test_process_timeline.py      # Process timeline
+-- test_provider_base.py         # Provider base
+-- test_reminders.py             # Reminders action
+-- test_screen_vision.py         # Screen vision
+-- test_service_monitor.py       # Service monitor
+-- test_shell.py                 # Shell action
+-- test_skill_debugging.py       # Debugging skill test
+-- test_skill_file_manager.py    # File manager skill test
+-- test_skill_greeting.py        # Greeting skill test
+-- test_skill_manager.py         # Skill manager
+-- test_skill_process_control.py # Process control skill test
+-- test_skill_scheduler.py       # Scheduler skill test
+-- test_skill_services.py        # Services skill test
+-- test_skill_system_health.py   # System health skill test
+-- test_skill_voice_coding.py    # Voice coding skill test
+-- test_skills.py                # Skill modulleri
+-- test_smoke.py                 # Smoke test (tum moduller, ~1121 test)
+-- test_sound_manager.py         # Sound manager
+-- test_state_machine.py         # Voice state machine
+-- test_state_ui.py              # State UI integration
+-- test_streaming_stt.py         # Streaming STT
+-- test_streaming_tts.py         # Streaming TTS
+-- test_sys_info.py              # Sys info action
+-- test_system_cron.py           # System cron
+-- test_system_doctor.py         # System doctor
+-- test_text_utils.py            # Text utils
+-- test_thinking_aloud.py        # Thinking aloud
+-- test_tool_dispatch.py         # Tool dispatch tests
+-- test_tool_registry.py         # Tool registry
+-- test_tts.py                   # TTS action
+-- test_ui.py                    # UI import
+-- test_ui_text_utils.py         # UI text utils
+-- test_vad_engine.py            # VAD engine
+-- test_voice_manager.py         # Voice manager
+-- test_voice_memory.py          # Voice memory
+-- test_wake_word.py             # Wake word
+-- test_weather.py               # Weather action
+-- test_whatsapp.py              # WhatsApp action
+-- test_windows_utils.py         # Windows utils
+-- test_youtube.py               # YouTube action
+-- manual/                       # Manuel test betikleri
|   +-- test_audio.py / test_audio2.py / test_audio3.py
|   +-- test_full_pipeline.py
|   +-- test_mic.py / test_mic_nosudo.py
|   +-- test_mic_stt.py / test_mic_stt2.py
|   +-- test_mic_user.py
|   +-- test_oww.py
|   +-- test_pyaudio_play.py
|   +-- test_stt_user.py / test_stt_user2.py
|   +-- test_sudo_play.py
|   +-- test_tts_play.py / test_tts_user.py
|   +-- test_ui_stt.py
|   +-- test_vad.py
```

---

## Test Turleri

### Smoke Test (`test_smoke.py`)

Her modulu import eder, hata vermediklerini dogrular:

```python
class TestSmoke(unittest.TestCase):
    def test_app_config_import(self):
        import app_config
        self.assertTrue(hasattr(app_config, "load_app_config"))
    
    def test_actions_import(self):
        from actions import open_app
        self.assertTrue(callable(open_app.open_app))
```

### Pure Fonksiyon Testleri

Ornek: `test_text_utils.py`

```python
class TestTextUtils(unittest.TestCase):
    def test_fix_turkish_syllable_split_basic(self):
        result = fix_turkish_syllable_split("Naber nasilsin iyi misin")
        self.assertEqual(result, "Naber nasilsin iyi misin")

    def test_fix_turkish_syllable_split_merged(self):
        result = fix_turkish_syllable_split("İ stanbul")
        self.assertEqual(result, "İstanbul")
```

### Error Path Testleri

```python
def test_system_health_mocked(self, mock_psutil):
    """psutil veri dondurmezse default degerler kullanilir."""
    mock_psutil.virtual_memory.return_value.percent = None
    result = get_system_health()
    self.assertIn("hata", result["memory"]["status"])
```

### Mock ile Yan Etki Testleri

Tarayici, shell, URL acma gibi yan etkiler `@patch` ile izole edilir:

```python
@patch("webbrowser.open")
def test_browser_control_url(self, mock_open):
    result = browser_control("open_url", url="https://example.com")
    mock_open.assert_called_once_with("https://example.com")
    self.assertIn("aciliyor", result.lower())
```

---

## Yeni Test Ekleme Kurallari

### 1. Modul Bazli Test

Her yeni modul icin yeni test dosyasi:

```bash
touch tests/test_yeni_modul.py
```

### 2. Basit Import Testi

```python
# tests/test_yeni_modul.py
import unittest

class TestYeniModul(unittest.TestCase):
    """Yeni Modul testleri"""

    def test_import(self):
        """Modul import edilebilmeli"""
        try:
            import yeni_modul
        except ImportError:
            self.fail("yeni_modul import edilemedi")
```

### 3. Pure Fonksiyon Testi

```python
def test_function_basic(self):
    """Temel fonksiyon dogru calismali"""
    result = yeni_modul.fonksiyon("input")
    self.assertEqual(result, "beklenen_output")

def test_function_edge_case(self):
    """Edge case'ler dogru calismali"""
    result = yeni_modul.fonksiyon("")
    self.assertIsNone(result)
```

### 4. Mock Testi (Yan Etki Varsa)

```python
@patch("yeni_modul.subprocess.run")
def test_function_side_effect(self, mock_run):
    """subprocess cagrisi mocklanmali"""
    mock_run.return_value.returncode = 0
    result = yeni_modul.fonksiyon("test")
    self.assertTrue(result)
```

### 5. Smoke Test'e Ekle

```python
# tests/test_smoke.py
class TestYeniModulSmoke:
    def test_import_yeni_modul(self):
        import yeni_modul
```

---

## Test Prensipleri

| Kural | Aciklama |
|-------|----------|
| **Framework** | Sadece `unittest`, pytest yok |
| **Mock** | Sadece yan etki testlerinde (URL acma, shell, dosya) |
| **Coverage** | 19+ modul, 0 skip hedefi |
| **Pure fonksiyon** | Input-output dogrulama, mock yok |
| **Error path** | Her hata senaryosu icin en az 1 test |
| **Yeni modul** = | Yeni test class'i `tests/test_smoke.py` veya yeni dosya |

---

## Bilinen Test Sorunlari

### Atlanan Testler (2 adet)

1. `test_disk_predictor` - Disk izni gerektiren test (sudo ile calisir)
2. `test_network_monitor` - Belirli ag durumlarinda atlanir

### pyaudio Bagimliligi

Pek cok test `import pyaudio` kontrolu yapar. pyaudio yoksa:
- `self.skipTest("pyaudio mevcut degil")` ile atlanir
- Hata vermez, dogrudan gecer

### Ses Donanim Testleri

Manuel testler (`tests/manual/`) gercek ses donanimi gerektirir:
- `test_mic.py` - Mikrofon testi
- `test_oww.py` - Wake word testi
- `test_mic_stt.py` - STT testi

Bu testler CI'da calismaz, sadece gelistirme sirasinda kullanilir.
