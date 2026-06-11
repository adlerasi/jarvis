# LLM Entegrasyonu

## Desteklenen LLM'ler

| Sağlayıcı | Model | API Tipi | Kullanım Alanı | Ses Desteği |
|-----------|-------|----------|----------------|-------------|
| Gemini | Gemini 2.0 Flash (Live API) | Bidirectional streaming (WebSocket) | Birincil backend | ✅ Doğal ses |
| Ollama | qwen2.5:1.5b (değiştirilebilir) | HTTP `/api/chat` (REST) | Yerel/offline backend | ❌ TTS zinciri |

## LLM Client Mimarisi

### Provider Abstraction Pattern

```
BaseProvider (ABC)
    │
    ├── GeminiProvider (core/gemini_provider.py)
    │   ├── Gemini Live API bidirectional streaming
    │   ├── Audio I/O: PyAudio 16kHz in → 24kHz out
    │   ├── Tool calls: Native function_declarations
    │   └── System prompt: Google AI format
    │
    └── OllamaProvider (core/ollama_provider.py)
        ├── Ollama HTTP /api/chat
        ├── Audio I/O: STT + TTS zinciri (VAD + f-w + Piper)
        ├── Tool calls: System prompt'tan JSON parsing
        └── System prompt: Custom format (text_utils ile)
```

```python
# core/provider_base.py — Abstract interface
class BaseProvider(ABC):
    """Tüm LLM provider'lar için soyut arayüz."""
    
    async def start(self, jarvis: Any) -> None:
        """Provider'ı başlat."""
        self.jarvis = jarvis
    
    @abstractmethod
    async def stop(self) -> None:
        """Kaynakları temizle."""
    
    @abstractmethod
    async def send_text(self, text: str) -> None:
        """Metin gönder."""
    
    @abstractmethod
    async def run_loop(self) -> None:
        """Ana işlem döngüsü."""
    
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @property
    def supports_streaming_audio(self) -> bool: return False
    @property
    def supports_tool_calls(self) -> bool: return False
```

### Gemini Provider (`core/gemini_provider.py`)

```python
class GeminiProvider(BaseProvider):
    """Gemini Live API bidirectional streaming provider."""
    
    async def start(self, jarvis):
        await super().start(jarvis)
        config = load_app_config()
        self._client = genai.Client(api_key=config["gemini_api_key"])
        self._session = None  # Live session
        
    async def run_loop(self):
        # 4 eşzamanlı TaskGroup coroutine
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._send_realtime())   # ses gönderme
            tg.create_task(self._listen_audio())    # mikrofon dinleme
            tg.create_task(self._receive_audio())   # yanıt işleme
            tg.create_task(self._play_audio())      # ses çalma
    
    async def _receive_audio(self):
        """Gemini yanıtlarını işle — tool call + transcription + audio."""
        async for msg in self._session.receive():
            if tool_call := msg.tool_call:
                for fc in tool_call.function_calls:
                    result = await self._j()._execute_tool(fc.name, fc.args, self._loop)
                    await self._session.send(function_response(id=fc.id, response=result))
            elif audio := msg.audio:
                self._audio_queue.put_nowait(audio.data)  # TTS için
```

### Ollama Provider (`core/ollama_provider.py`)

```python
class OllamaProvider(BaseProvider):
    """Ollama HTTP API provider — STT + chat + TTS."""
    
    async def run_loop(self):
        # VAD ile ses dinle
        await self._stt_listen_loop()  # PyAudio → VAD → f-w transcribe
    
    async def _stt_listen_loop(self):
        while self._running:
            audio = await self._record_audio()
            if self._vad.is_speech(audio):
                text = self._stt.transcribe(audio)
                text = clean_transcript_text(text)
                await self.send_text(text)
    
    async def send_text(self, text: str):
        # Ollama chat API
        response = await self._ollama_chat(text)
        # TTS zinciri
        await self._tts.speak(response)
```

## Prompt Yönetimi

### Sistem Prompt'ları

- **Lokasyon:** `core/prompt.txt`
- **Format:** Düz metin (f-string ile dinamik değerler eklenir)

```python
# main.py — Prompt hazırlama
def _build_system_prompt(self) -> str:
    base = PROMPT_PATH.read_text(encoding="utf-8")
    
    # OS bilgisi enjekte et
    os_info = f"[SISTEM BILGISI]\nIsletim Sistemi: {sys.platform}\n"
    base = base.replace("[SISTEM_BILGISI]", os_info)
    
    # Bellek enjekte et
    memory_str = format_memory_for_prompt()
    if memory_str:
        base += f"\n\n[KULLANICI BILGILERI]\n{memory_str}"
    
    return base
```

### Ollama Tool Calling (System Prompt ile)

Ollama native function calling desteklemediği için, tool'lar system prompt'a JSON formatında enjekte edilir:

```python
# core/tool_registry.py → Ollama formatı
def generate_ollama_tool_help() -> str:
    tools_text = "KULLANILABILIR ARACLAR:\n"
    for name, desc, params, required in _TOOL_DEFS:
        tools_text += f"- {name}: {desc}\n"
        tools_text += f"  Parameters: {json.dumps(params)}\n"
        tools_text += "  Cikti: JSON formatinda: {{\"tool\": \"{name}\", \"args\": {{...}}}}\n"
    return tools_text
```

## Context Window Yönetimi

### Gemini Live API

- **Context window:** Gemini tarafında yönetilir (otomatik)
- **History:** Konuşma geçmişi `session.send()` ile iletilir
- **Token limit:** Google AI tarafında aşılırsa otomatik özetleme

### Ollama

- **Context window:** `num_ctx` parametresi ile ayarlanabilir
- **History:** Son N mesaj (config'de ayarlanabilir)
- **Sliding window:** Eski mesajlar otomatik düşer

```python
async def _ollama_chat(self, text: str) -> str:
    messages = self._history[-self._max_history:]  # sliding window
    messages.append({"role": "user", "content": text})
    
    data = {
        "model": self._model,
        "messages": messages,
        "stream": False,
        "options": {"num_ctx": 4096},
    }
    
    async with httpx.AsyncClient() as client:
        r = await client.post("http://localhost:11434/api/chat", json=data, timeout=30)
        result = r.json()
        self._history.append({"role": "assistant", "content": result["message"]["content"]})
        return result["message"]["content"]
```

## Tool / Function Calling

### Gemini Native Function Calling

```python
# Gemini function_declarations formatı
def generate_gemini_declarations() -> list[dict]:
    declarations = []
    for name, description, params, required in _TOOL_DEFS:
        declarations.append({
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": params,
                "required": required,
            },
        })
    return declarations

# Kullanım: Gemini session'a tool olarak ekle
self._session = client.aio.live.connect(
    model="gemini-2.0-flash-exp",
    config=types.LiveConnectConfig(
        tools=[types.Tool(function_declarations=gemini_declarations)],
        response_modalities=["AUDIO"],
    ),
)
```

### Ollama Tool Calling (Manual JSON)

```python
def _parse_tool_call(self, text: str) -> tuple[str, dict] | None:
    """Ollama yanıtından tool çağrısını JSON olarak parse et."""
    try:
        data = json.loads(text)
        if "tool" in data and "args" in data:
            return data["tool"], data["args"]
    except json.JSONDecodeError:
        pass
    return None  # tool çağrısı değil, normal yanıt
```

## Streaming Response

### Gemini — Bidirectional Streaming

```python
# 4 coroutine eşzamanlı çalışır
async with asyncio.TaskGroup() as tg:
    tg.create_task(self._send_realtime())   # → Gemini (mikrofon)
    tg.create_task(self._listen_audio())    # → Gemini (handle events)
    tg.create_task(self._receive_audio())   # ← Gemini (responses)
    tg.create_task(self._play_audio())      # ← Gemini (audio playback)
```

### Ollama — HTTP Response

```python
# Streaming HTTP cevap
async with client.stream("POST", "http://localhost:11434/api/chat", json=data) as resp:
    async for line in resp.aiter_lines():
        chunk = json.loads(line)
        if chunk.get("done"):
            break
        text = chunk.get("message", {}).get("content", "")
        # UI'a partial güncelleme
        self._j().write_debug(text)
```

## Hata & Fallback

| Hata | Gemini | Ollama |
|------|--------|--------|
| API Key yok | SetupDialog aç | N/A |
| Bağlantı hatası | Yeniden bağlan (3 deneme) | Log + ERROR state |
| Timeout | Session rebuild | HTTP timeout exception |
| Rate limit | Exponential backoff | N/A |
| Tool exec hatası | Hata string'i LLM'e dön | Aynı |

## Maliyet & Performans Optimizasyonu

| Yöntem | Açıklama |
|--------|----------|
| **RNNoise ön işleme** | Daha az gereksiz ses → daha az API çağrısı |
| **VAD filtreleme** | Sessizlikte API çağrısı yapılmaz |
| **Input cap** | 10000 karakter metin sınırı |
| **Tool arg cap** | 500 karakter/arg, 2000 toplam |
| **History sliding** | Ollama'da son N mesaj tutulur |
| **Model seçimi** | Gemini 2.0 Flash (hızlı/ucuz) vs Ollama (ücretsiz) |

[Bkz. STT_TTS.md](STT_TTS.md) | [Bkz. ORCHESTRATOR.md](ORCHESTRATOR.md) | [Bkz. API_REFERENCE.md](API_REFERENCE.md)
