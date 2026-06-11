# Data Model: Orkestrasyon Onarımı

**Phase 1 — Değişen Arayüzler ve Veri Yapıları**

---

## 1. BaseProvider Arayüzü

### Mevcut
```python
class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    async def start(self, jarvis: Any) -> None: ...
    async def stop(self): ...
    async def run_loop(self): ...
    async def send_text(self, text: str) -> None: ...
```

### Hedef (eklenen: `send_audio`)
```python
class BaseProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    async def start(self, jarvis: Any) -> None: ...
    async def stop(self): ...
    async def run_loop(self): ...

    # ── Text input ──
    async def send_text(self, text: str) -> None:
        """Provider'a metin gönder. Tüm text girişleri buradan geçer."""
        raise NotImplementedError

    # ── Audio input (opsiyonel) ──
    async def send_audio(self, data: bytes) -> None:
        """Provider'a ham ses gönder. Gemini out_queue'ya koyar, Ollama no-op."""
        pass  # optional — varsayılan no-op
```

### Değişen Implementasyonlar

**GeminiProvider.send_audio()**:
```python
async def send_audio(self, data: bytes) -> None:
    q = self.out_queue
    if q is not None:
        await q.put({"data": data, "mime_type": "audio/pcm"})
```

**OllamaProvider.send_audio()**: no-op (ses kendi STT loop'unda işlenir)

---

## 2. UI Thread-Safe Call

### Mevcut
```python
# ui.py'de
def safe_call(self, fn, *args, **kwargs):
    self.root.after(0, lambda: fn(*args, **kwargs))
```

### Hedef (return value desteği + thread check)
```python
def safe_call(self, fn, *args, **kwargs):
    """Thread-safe UI call. Main thread'de direkt, değilse after(0) ile schedule eder."""
    if threading.current_thread() is threading.main_thread():
        return fn(*args, **kwargs)
    result_container = []
    def _wrapper():
        try:
            r = fn(*args, **kwargs)
            result_container.append(("ok", r))
        except Exception as e:
            result_container.append(("error", e))
            traceback.print_exc()
    self.root.after_idle(_wrapper)
    # Return immediately — async pattern
```

---

## 3. Jarvis State Machine

### Mevcut — Dağınık
```python
j.ui.set_state("THINKING")   # 15+ yerde
```

### Hedef — Merkezi
```python
# JarvisLive'e eklenecek
VALID_STATE_TRANSITIONS = {
    "LISTENING": {"THINKING", "SPEAKING", "MUTED", "PAUSED"},
    "THINKING":  {"SPEAKING", "ERROR", "LISTENING"},
    "SPEAKING":  {"LISTENING", "ERROR", "THINKING"},
    "ERROR":     {"LISTENING", "THINKING"},
    "MUTED":     {"LISTENING"},
    "PAUSED":    {"LISTENING"},
}

def set_state(self, new_state: str):
    """Merkezi state yöneticisi — geçersiz geçişleri engeller."""
    current = getattr(self.ui, "_jarvis_state", "LISTENING")
    if new_state in self.VALID_STATE_TRANSITIONS.get(current, {new_state}):
        self.ui.set_state(new_state)
    else:
        print(f"[JARVIS] Invalid state transition: {current} → {new-state}")
```

---

## 4. Ollama Provider Config Cache

### Mevcut
```python
# _stt_listen_loop'da her frame'de:
cfg = _load_app_config()
```

### Hedef
```python
class OllamaProvider(BaseProvider):
    def __init__(self):
        ...
        self._cached_config: dict = {}
        self._stt_restart_count: int = 0

    async def start(self, jarvis):
        await super().start(jarvis)
        self._cached_config = _load_app_config()  # bir kere oku
        self._stt_restart_count = 0

    def _refresh_config(self):
        """Çağrıldığında cache'i yenile (on_config_change'dan)."""
        self._cached_config = _load_app_config()
```

---

## 5. RNNoise Instance

### OllamaProvider'a eklenecek
```python
class OllamaProvider(BaseProvider):
    def __init__(self):
        ...
        self._noise_suppressor = None

    async def start(self, jarvis):
        ...
        if _HAS_RNNOISE:
            try:
                from audio.noise_suppressor import NoiseSuppressor
                self._noise_suppressor = NoiseSuppressor(sample_rate=16000)
                print("[Ollama] RNNoise aktif")
            except Exception:
                self._noise_suppressor = None
```

---

## 6. StreamingSTT Yaşam Döngüsü

### Mevcut — Her zaman başlatılır
```python
# main.py _asimilasyon_init()
self.streaming_stt_engine = create_streaming_stt(...)
self.streaming_stt_engine.start()
```

### Hedef — Sadece Ollama modunda
```python
# main.py _asimilasyon_init()
backend = self.app_config.get("backend_type", "gemini")
if backend == "ollama":
    self.streaming_stt_engine = create_streaming_stt(...)
    self.streaming_stt_engine.start()
else:
    self.streaming_stt_engine = None
```

---

## 7. Etkilenen Dosyalar ve Değişen Fonksiyonlar

| Dosya | Fonksiyon | Değişiklik |
|-------|-----------|------------|
| `main.py` | `_asimilasyon_init()` | StreamingSTT conditional, VAD cleanup |
| `main.py` | `run()` | Provider geçişi senkronizasyonu |
| `main.py` | `_on_stt_text()` | `send_text()` kullan |
| `main.py` | `_on_text_command()` | (doğru zaten) |
| `main.py` | `set_state()` | YENİ: merkezi state machine |
| `main.py` | `_on_agent_state_update()` | (zaten safe_call kullanıyor) |
| `ui.py` | `safe_call()` | Thread check + return value |
| `core/ollama_provider.py` | `__init__`, `start()` | Config cache, RNNoise, restart count |
| `core/ollama_provider.py` | `_stt_listen_loop()` | RNNoise, safe_call, config cache |
| `core/ollama_provider.py` | `run_loop()` | Config cache, restart limit |
| `core/gemini_provider.py` | `_listen_audio()` | safe_call for UI |
| `core/gemini_provider.py` | `send_audio()` | BaseProvider'dan override |
| `core/provider_base.py` | class BaseProvider | `send_audio()` abstract |
| `core/streaming_tts.py` | `_worker_loop()` | Restart on crash |
| `core/emotion_tts.py` | `_speak_piper_emotion()` | Platform player |
