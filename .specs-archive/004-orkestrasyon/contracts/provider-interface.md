# Provider Interface Contract

## Contract: `BaseProvider.send_text(text)`

### Purpose
Tüm metin girdileri (STT, UI text input) için tek geçit. Provider uygulaması metni kendi pipeline'ına iletir.

### Input
- `text: str` — Kullanıcıdan gelen metin (STT veya UI). Azami 10.000 karakter.

### Output
- `None` — Asynchronous fire-and-forget

### Contract Tests
```python
async def test_send_text_reaches_provider():
    """send_text() çağrısı provider'ın input pipeline'ına ulaşmalı."""
    p = OllamaProvider()
    await p.start(mock_jarvis)
    await p.send_text("merhaba")
    # Ollama: text input_queue'da olmalı
    received = await asyncio.wait_for(p.input_queue.get(), timeout=1.0)
    assert received == "merhaba"
    await p.stop()
```

```python
async def test_send_text_gemini():
    """Gemini send_text session.send_client_content çağırmalı."""
    p = GeminiProvider()
    p.session = MagicMock()
    await p.send_text("test")
    p.session.send_client_content.assert_called_once()
```

---

## Contract: `BaseProvider.send_audio(data)`

### Purpose
Ham ses verisini provider'a iletir. Gemini: sesi API'ya forward eder. Ollama: no-op (kendi STT loop'u var).

### Input
- `data: bytes` — PCM int16, 16000Hz, mono ham ses

### Output
- `None`

### Contract Tests
```python
async def test_send_audio_gemini():
    """Gemini send_audio out_queue'ya koymalı."""
    p = GeminiProvider()
    p.out_queue = asyncio.Queue()
    await p.send_audio(b"\\x00" * 1024)
    msg = await asyncio.wait_for(p.out_queue.get(), timeout=1.0)
    assert msg["mime_type"] == "audio/pcm"
    assert isinstance(msg["data"], bytes)
```

```python
async def test_send_audio_ollama_noop():
    """Ollama send_audio no-op olmalı (exception fırlatmamalı)."""
    p = OllamaProvider()
    await p.send_audio(b"\\x00" * 1024)  # should not raise
```

---

## Contract: `JarvisUI.safe_call(fn, *args)`

### Purpose
Thread-safe UI güncelleme. Main thread'de direkt çalışır, background thread'de `after(0)` ile schedule eder.

### Input
- `fn: Callable` — Main thread'de çalıştırılacak fonksiyon
- `*args, **kwargs` — Fonksiyona iletilecek argümanlar

### Output
- Main thread'de: `fn`'in dönüş değeri
- Background thread'de: `None` (non-blocking)

### Contract Tests
```python
def test_safe_call_from_main_thread():
    """safe_call main thread'de direkt çalışmalı."""
    ui = JarvisUI()
    called = []
    result = ui.safe_call(lambda: called.append(1))
    assert called == [1]
```

```python
def test_safe_call_from_bg_thread():
    """safe_call background thread'de after(0) ile schedule etmeli."""
    ui = JarvisUI()
    called = []
    def bg():
        ui.safe_call(lambda: called.append(1))
    t = threading.Thread(target=bg)
    t.start()
    t.join()
    # after(0) ile schedule edildi, henüz çalışmamış olabilir
    # ama exception fırlatmamalı
```

---

## Contract: `JarvisLive.set_state(new_state)`

### Purpose
UI state geçişlerini merkezi olarak yönetir. Geçersiz geçişleri engeller ve loglar.

### Input
- `new_state: str` — Hedef state: LISTENING, THINKING, SPEAKING, ERROR, MUTED, PAUSED

### Output
- Geçerli geçiş: UI state değişir, yeni state Tkinter animasyonuna yansır
- Geçersiz geçiş: Log yazılır, UI state değişmez

### State Machine

```
LISTENING ──→ THINKING
LISTENING ──→ SPEAKING
LISTENING ──→ MUTED
LISTENING ──→ PAUSED
THINKING  ──→ SPEAKING
THINKING  ──→ ERROR
THINKING  ──→ LISTENING
SPEAKING  ──→ LISTENING
SPEAKING  ──→ ERROR
SPEAKING  ──→ THINKING
ERROR     ──→ LISTENING
ERROR     ──→ THINKING
MUTED     ──→ LISTENING
PAUSED    ──→ LISTENING
```

### Contract Tests
```python
def test_state_transition_valid():
    """Geçerli state geçişleri çalışmalı."""
    app = JarvisLive(mock_ui)
    app.set_state("THINKING")
    assert mock_ui._jarvis_state == "THINKING"
```

```python
def test_state_transition_invalid():
    """Geçersiz state geçişleri engellenmeli."""
    app = JarvisLive(mock_ui)
    app.set_state("THINKING")
    app.set_state("MUTED")  # THINKING → MUTED geçersiz
    assert mock_ui._jarvis_state == "THINKING"  # değişmemeli
```
