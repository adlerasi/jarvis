# Yapılandırma Sistemi

## Konfigürasyon Kaynakları (Öncelik Sırası)

1. **Kullanıcı ayarları** → `config/api_keys.json` (JSON dosya)
2. **UI üzerinden değişiklik** → `save_app_config()` ile JSON'a yazılır
3. **Varsayılan değerler** → `app_config.py`'de `DEFAULT_CONFIG` dict

### Yükleme Sırası

```python
DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "voice": "Charon",
    "youtube_api_key": "",
    "youtube_channel_handle": "",
    "backend_type": "gemini",
    "ollama_model": "",
    "ollama_tts_voice": "piper-fahrettin",
}

def load_app_config() -> dict:
    config = dict(DEFAULT_CONFIG)         # 1. Varsayılan
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))  # 2. JSON
        if isinstance(raw, dict):
            config.update(raw)            # 3. Merge (JSON kazanır)
    except Exception:
        pass
    return config
```

## Zorunlu Ayarlar

| Değişken | Açıklama | Varsayılan | Zorunlu |
|----------|----------|------------|---------|
| `gemini_api_key` | Gemini AI API anahtarı | `""` | Gemini modu için ✅ |
| `backend_type` | Backend seçimi: `gemini` / `ollama` | `"gemini"` | ❌ |
| `ollama_model` | Ollama model adı | `""` | Ollama modu için ✅ |
| `ollama_tts_voice` | Yerel TTS sesi | `"piper-fahrettin"` | ❌ |

## Opsiyonel Ayarlar

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `voice` | Gemini ses modeli (Charon, Puck, Aoede, Kore...) | `"Charon"` |
| `youtube_api_key` | YouTube Data API anahtarı | `""` |
| `youtube_channel_handle` | YouTube kanal handle'ı | `""` |

### Ses Yapılandırması (`config/audio.yaml`)

```yaml
# Ses sistemi yapılandırması
sample_rate: 16000
channels: 1
noise_suppression:
  enabled: true
  bypass_if_unavailable: true
vad:
  fahrettin:
    engine: "energy"          # silero / webrtc / energy
    energy_threshold: 50.0
    debug_log: false
wake_word:
  engine: "openwakeword"      # openwakeword / porcupine / energy
  wake_word: "jarvis"
  openwakeword:
    sensitivity: 0.5
```

## Ayarların Validasyonu

JARVIS **manuel validasyon** kullanır (Pydantic/dataclass yok):

```python
# app_config.py
def has_gemini_api_key() -> bool:
    value = str(get_app_config_value("gemini_api_key", "") or "").strip()
    return bool(value)

def get_ollama_models() -> list[str]:
    """Ollama API'den model listesini al."""
    try:
        url = "http://localhost:11434/api/tags"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []
```

### Geçersiz Yapılandırma Davranışı

| Durum | Davranış |
|-------|----------|
| API anahtarı yok + Gemini seçili | SetupDialog açılır, kullanıcıdan istenir |
| Ollama seçili + Ollama kapalı | `run_loop()` bağlantı hatası → ERROR state |
| Geçersiz voice adı | Varsayılan kullanılır (sessizce) |
| audio.yaml yok | Boş dict, her şey varsayılan |
| api_keys.json yok | DEFAULT_CONFIG kullanılır, yazma sırasında oluşturulur |

## Sıcak Yeniden Yükleme (Hot Reload)

### Config Hot Reload

Config **runtime sıcak yeniden yükleme desteklemez**. Değişiklikler için uygulamanın yeniden başlatılması gerekir.

```python
# Her config okuma JSON'dan yapılır (cache yok)
def load_app_config() -> dict:
    # Her çağrıda dosyayı okur
    ...

def get_app_config_value(key: str, default=None):
    return load_app_config().get(key, default)
```

### Skill Hot Reload

Skill sistemi **sıcak yeniden yükleme destekler**:

```python
# core/_skill_engine.py — 3sn interval
def _watch_skills(self):
    while self._running:
        self._check_for_changes()
        time.sleep(3)
```

### UI Config Değişikliği

UI üzerinden config değiştirildiğinde:

```python
# ui.py — Settings panel
def _save_settings(self):
    updates = {
        "gemini_api_key": self._entry_api_key.get(),
        "voice": self._voice_var.get(),
        "backend_type": self._backend_var.get(),
        "ollama_model": self._ollama_model_var.get(),
        "ollama_tts_voice": self._ollama_tts_var.get(),
    }
    save_app_config(updates)
    # Not: Uygulama yeniden başlatılmalı
```

## Dosya Konumları

| Dosya | Açıklama | .gitignore |
|-------|----------|------------|
| `config/api_keys.json` | API anahtarları | ✅ Evet |
| `config/api_keys.example.json` | Örnek yapılandırma | ❌ Hayır |
| `config/audio.yaml` | Ses yapılandırması | ❌ Hayır |
| `core/prompt.txt` | Sistem prompt'u | ❌ Hayır |
| `memory/*.json` | Kullanıcı belleği | ✅ Evet |
| `logs/jarvis.log` | Uygulama logları | ✅ Evet |

[Bkz. ARCHITECTURE.md](ARCHITECTURE.md) | [Bkz. API_REFERENCE.md](API_REFERENCE.md) | [Bkz. DEPENDENCIES.md](DEPENDENCIES.md)
