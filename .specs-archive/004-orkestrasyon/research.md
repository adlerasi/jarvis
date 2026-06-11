# Research: Orkestrasyon Onarımı

**Phase 0 — Teknoloji Araştırması ve Karar Kaydı**

---

## 1. Thread Güvenliği — Tkinter Calls from Background Threads

### Problem
Tkinter widget'ları yalnızca main thread'den değiştirilebilir. JARVIS'te:
- `StreamingSTT._transcription_loop()` → `_on_stt_text()` → `ui.write_log()` (daemon thread)
- `OllamaProvider._stt_listen_loop()` → `ui.set_state()`, `ui.write_log()`, `ui.set_mic_level()` (asyncio thread)
- `GeminiProvider._listen_audio()` → `out_queue.put()` (asyncio thread)

### Mevcut Çözümler
1. **`ui.safe_call()`**: `JarvisUI`'de tanımlı, `root.after(0, ...)` kullanır. Sadece ACA callback'inde kullanılıyor (main.py:1013).
2. **`ui.after()`**: Tkinter'ın doğrudan `after()` metodu — aynı işlev.

### Decision
**Tüm UI çağrıları için `safe_call()` wrapper'ı kullanılacak.**

Rationale:
- `safe_call()` zaten mevcut, genişletilmesi gerekiyor
- `after()` doğrudan kullanmaktan daha güvenli (hata yönetimi + debug)
- Tüm UI erişimleri için tek bir geçit (gateway) pattern'i

Alternatives considered:
- `queue.Queue` + main thread poll — çok karmaşık
- `asyncio.run_coro_threadsafe()` — coroutine'in Tkinter'a erişmesini engellemez

### Implementation
```python
# ui.py'de safe_call genişletmesi
def safe_call(self, fn, *args, **kwargs):
    """Thread-safe UI call — schedules fn on main thread."""
    if threading.current_thread() is threading.main_thread():
        return fn(*args, **kwargs)
    result = []
    def _wrapper():
        try:
            r = fn(*args, **kwargs)
            result.append(r)
        except Exception as e:
            result.append(e)
    self.root.after(0, _wrapper)
    # Optional: wait for result (blocking)
    # while not result: time.sleep(0.001)
    # return result[0]
```

---

## 2. RNNoise Gürültü Bastırma

### Problem
`audio/noise_suppressor.py` mevcut ve çalışıyor. Ollama provider'da `_HAS_RNNOISE` kontrol ediliyor ama `noise_suppressor.process()` hiç çağrılmıyor.

### Decision
**RNNoise, Ollama STT loop'unda VAD'dan ÖNCE uygulanacak.**

Rationale:
- Gürültü bastırma VAD doğruluğunu artırır
- STT kalitesini iyileştirir
- RNNoise zaten bağımlılık olarak mevcut, ek maliyet yok

### API
```python
# audio/noise_suppressor.py
ns = NoiseSuppressor(sample_rate=16000)
clean_data = ns.process(noisy_data)  # bytes → bytes
```

### Integration Point
```python
# ollama_provider.py _stt_listen_loop()
raw_data = stream.read(...)
if _HAS_RNNOISE:
    raw_data = self._noise_suppressor.process(raw_data)
# ... sonra VAD
```

---

## 3. Provider Arayüz Standardizasyonu

### Problem
- `BaseProvider` abstract `send_text(text)` tanımlar
- `GeminiProvider.send_text()` → `session.send_client_content()` (doğru)
- `OllamaProvider.send_text()` → `input_queue.put()` (doğru)
- Ama `_on_stt_text()` doğrudan `_provider.input_queue.put_nowait()` çağırır

### Decision
**Tüm metin girişi `send_text()` üzerinden yapılacak. `send_audio()` abstract method olarak eklenecek.**

### Contract
```python
class BaseProvider(ABC):
    async def send_text(self, text: str) -> None: ...
    async def send_audio(self, data: bytes) -> None: ...  # YENİ
    # Gemini: sesi out_queue'ya koy
    # Ollama: no-op (ses kendi STT loop'unda işlenir)
```

---

## 4. Dual STT Cleanup

### Problem
StreamingSTT (`core/streaming_stt.py`) Gemini modunda da çalışır ama transkripsiyonları `input_queue.put_nowait()` ile gönderilir — Gemini bu queue'yu kullanmaz.

### Decision
**StreamingSTT sadece Ollama modunda başlatılacak.** Gemini modunda `_asimilasyon_init()`'de atlanacak.

Alternatives considered:
- StreamingSTT'yi her iki provider'a da beslemek → gereksiz CPU, Gemini zaten kendi STT'sini yapar
- StreamingSTT'yi Gemini'ye `send_text()` ile bağlamak → çift transkripsiyon (yerel + bulut), API maliyeti artar

---

## 5. Dual VAD Cleanup

### Problem
main.py:277-292'de `create_vad_engine()` ile oluşturulan `vad_engine` hiçbir yerde beslenmez. Callback'leri (`_on_vad_speech_start/end`) asla tetiklenmez.

### Decision
**main.py'deki `vad_engine` kaldırılacak.** VAD sadece provider içinde (Ollama'da FahrettinVAD) yönetilecek.

Etki: `_on_vad_speech_start` ve `_on_vad_speech_end` callback'leri çalışmayacak. Bu callback'ler sadece log yazar (`[VAD] Konusma basladi/sona erdi`) — kaldırılmaları kullanıcı deneyimini etkilemez.

---

## 6. Ollama Task Management

### Problem
`_stt_listen_loop` exception fırlatırsa, `run_loop()` her turda yeni bir task oluşturur → sonsuz restart döngüsü.

### Decision
**Restart sayacı eklenecek: max 3 deneme, sonra STT tamamen durur ve kullanıcıya bildirilir.**

```python
self._stt_restart_count = 0
MAX_STT_RESTARTS = 3

# _stt_listen_loop sonunda veya exception handler'da:
self._stt_restart_count += 1
if self._stt_restart_count > MAX_STT_RESTARTS:
    j.ui.write_log("ERR: STT 3 kez çöktü, yeniden başlatılmıyor.")
    return  # task sonlansın, yeniden başlamasın
```

---

## 7. UI State Machine

### Problem
`j.ui.set_state()` 15+ yerde doğrudan çağrılır. State geçiş kuralları dağınık.

### Decision
**Merkezi `jarvis.set_state()` metodu oluşturulacak.** State geçiş mantığı tek yerde toplanacak.

```python
def set_state(self, new_state: str):
    """Merkezi state yöneticisi."""
    allowed = {
        "LISTENING": ["THINKING", "SPEAKING"],  # listening'den sadece thinking/speaking'e
        "THINKING": ["SPEAKING", "ERROR", "LISTENING"],
        "SPEAKING": ["LISTENING", "ERROR"],
        "ERROR": ["LISTENING", "THINKING"],
        "MUTED": ["LISTENING"],
        "PAUSED": ["LISTENING"],
    }
    current = getattr(self.ui, "_jarvis_state", "LISTENING")
    if new_state in allowed.get(current, [new_state]):
        self.ui.set_state(new_state)
```

---

## 8. EmotionTTS Windows Uyumu

### Problem
`_speak_piper_emotion()` `aplay` kullanır — Linux'a özel.

### Decision
**Platform kontrollü player seçimi.** Windows'ta `winsound` veya `sounddevice`, Linux'ta `aplay`.

```python
import platform
if platform.system() == "Windows":
    import winsound
    winsound.PlaySound(wav_path, winsound.SND_FILENAME)
else:
    subprocess.run(["aplay", "-q", wav_path])
```

---

## 9. Config Caching

### Problem
`cfg = _load_app_config()` her STT frame'inde (~30ms) diskten okunur.

### Decision
**Config provider başlangıcında bir kez okunur, `_cached_config`'de tutulur.** Sadece `on_config_change` çağrıldığında yenilenir.

```python
self._cached_config = _load_app_config()
# _stt_listen_loop'da:
cfg = self._cached_config
# _run_loop'da:
cfg = self._cached_config
```

---

## 10. Provider Switch Graceful Shutdown

### Problem
Provider değişiminde eski provider'ın kaynakları (PyAudio, HTTP client) sıralı temizlenmez.

### Decision
**`run()` metodunda önce `provider.stop()` tamamlanır, SONRA yeni provider başlatılır.** `_shutdown_event` benzeri mekanizma ile senkronizasyon.

```python
finally:
    self._provider = None
    try:
        await provider.stop()
    except Exception:
        pass
# Bu zaten böyle — sorun TaskGroup'un hemen iptal edilmesi.
# Çözüm: provider.stop()'da TaskGroup'daki tüm task'lerin tamamlandığını bekle.
```

---

## Karar Kaydı

| Karar | Alternatif | Gerekçe |
|-------|-----------|---------|
| `safe_call()` ile thread güvenliği | Queue + poll | Daha basit, zaten mevcut |
| RNNoise VAD'dan önce | VAD'dan sonra | Gürültü VAD'ı yanıltmasın |
| StreamingSTT sadece Ollama | Her iki modda | CPU tasarrufu, API maliyeti |
| `send_text()` standardizasyonu | Mevcut durum | Provider değişimine dayanıklı |
| Config cache | Her frame okuma | 30ms → 0ms disk I/O |
| Platform kontrollü TTS | `aplay` her yerde | Windows çalışır |
| Max 3 STT restart | Sonsuz restart | Debug'ı kolay, kaynak koruma |
| Merkezi state machine | Dağınık set_state | Tutarlı UI |
