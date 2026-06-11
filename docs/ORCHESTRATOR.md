# Orkestrasyon Katmanı

## Sorumluluklar

Orkestratör (`main.py` → `JarvisLive` sınıfı) tüm JARVIS sistemini yöneten ana denetleyicidir. Sorumlulukları:

- Provider (LLM) seçimi ve yaşam döngüsü yönetimi (Gemini / Ollama)
- Tool dispatch: 40+ aracı ilgili action modülüne yönlendirme
- Skill routing: LLM'den önce skill eşleşmesi kontrolü
- State machine: LISTENING → THINKING → SPEAKING → ERROR geçişleri
- UI callback'leri: state güncellemeleri, log yazma
- Audio pipeline: wake word, VAD, barge-in, streaming STT/TTS
- Arka plan servisleri: cron, file watcher, process timeline, disk predictor
- Thread-safe ses durumu yönetimi

## Ana Sınıf / Fonksiyonlar

### `class JarvisLive`

- **Lokasyon:** `main.py`
- **Açıklama:** JARVIS çekirdek orkestratör sınıfı. Tüm sistemi başlatır, çalıştırır ve yönetir.

**Parametreler:**
| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|-----------|----------|
| `_user_initiated` | bool | False | Kullanıcı ilk mesajı gönderene kadar False |
| `_is_speaking` | bool | False | JARVIS konuşuyor mu |
| `_backend_type` | str | "gemini" | Mevcut backend |

**İç Akış (run()):**
```
1. load_app_config() → backend_type, api_key oku
2. Provider seçimi:
   ├── Gemini API anahtarı var → GeminiProvider
   ├── Ollama seçili → OllamaProvider
   └── Hiçbiri → SetupDialog aç
3. provider.start(jarvis)
4. provider.run_loop()   ← bloklar
5. Hata/kesinti → provider.stop()
```

### `_execute_tool()`

- **Lokasyon:** `main.py`
- **Açıklama:** Tool çağrılarını action modüllerine yönlendirir.

```python
async def _execute_tool(self, tool_name: str, args: dict, loop: asyncio.AbstractEventLoop) -> str:
    handler_name = TOOL_HANDLER_MAP.get(tool_name)
    if not handler_name:
        return f"Hata: '{tool_name}' bilinmiyor."
    
    handler = getattr(self, handler_name, None)
    if handler is None:
        return f"Hata: '{tool_name}' handler'i bulunamadi."
    
    try:
        return await handler(args, loop)
    except Exception:
        traceback.print_exc()
        self.set_state("ERROR")
        return f"'{tool_name}' çalıştırılırken hata."
```

**İç Akış:**
1. `TOOL_HANDLER_MAP`'den handler adını bul (dict dispatch)
2. `getattr(self, handler_name)` ile metodu çöz
3. Handler yoksa → hata döndür
4. Thread pool'da çalıştır (blokeli işlemler için `run_in_executor`)
5. Hata varsa → ERROR state + traceback

### `_on_text_command()`

- **Lokasyon:** `main.py`
- **Açıklama:** Kullanıcı metin komutlarını işler.

```python
def _on_text_command(self, text: str):
    if not text or not text.strip():
        return
    self._user_initiated = True  # AI'nın izinsiz aksiyon almasını engeller
    text = text.strip()[:10000]  # Input cap
    
    # Önce skill manager dene (AI'sız, anında yanıt)
    skill_result = get_skill_manager().route(text)
    if skill_result:
        self.write_log(f"[Skill] {skill_result}")
        return
    
    # Skill eşleşmezse LLM'e gönder
    asyncio.run_coroutine_threadsafe(
        self._current_provider.send_text(text),
        self._loop
    )
```

## Routing Mantığı

```
Kullanıcı komutu (ses/metin)
    │
    ▼
_on_text_command()
    │
    ├── SkillManager.route(text)
    │       │
    │       ├── ✨ EŞLEŞTİ → Skill doğrudan çalışır → UI'da göster
    │       │                    LLM'e gidilmez, anında yanıt
    │       │
    │       └── ❌ EŞLEŞMEDİ → Provider.send_text()
    │               │
    │               ├── Gemini → Tool call mı?
    │               │       ├── Evet → _execute_tool() → action modülü
    │               │       └── Hayır → Doğrudan yanıt (TTS)
    │               │
    │               └── Ollama → System prompt + function calling
    │                       ├── Tool çağrısı → _execute_tool()
    │                       └── Yanıt → TTS zinciri
```

### Intent Classification Metodu

JARVIS **2 seviyeli routing** kullanır:

1. **Skill Routing (Öncelikli):** SkillManager regex pattern'leri ile komutu eşleştirir. Basit, öngörülebilir komutlar (tarayıcı aç, hava durumu sor, saat kaç) AI'a gitmeden çözülür.
2. **LLM Routing (Fallback):** Skill eşleşmezse, LLM provider (Gemini/Ollama) doğal dil anlayışı + tool calling ile işler.

### Koşullu Dallanma Kuralları

| Koşul | Davranış |
|-------|----------|
| Skill eşleşti | LLM çağrılmaz, anında yanıt |
| Gemini modu + tool call | `_execute_tool()` ile action modülü |
| Gemini modu + text | Doğrudan Gemini yanıtı → TTS |
| Ollama modu + tool | System prompt'tan JSON tool çağrısı ayrıştırma |
| Ollama modu + text | Chat yanıtı → TTS zinciri |
| Backend yok | SetupDialog aç |

### Fallback Mekanizmaları

1. **No API key:** `has_gemini_api_key()` False → SetupDialog ile kullanıcıdan API anahtarı iste
2. **Ollama bağlantı hatası:** HTTP timeout/refused → log + ERROR state
3. **Gemini stream hatası:** Yeniden bağlanma dene, başaramazsa ERROR state
4. **Tool çalışma hatası:** Hata mesajı LLM'e geri bildirim olarak döner

## Approval Flow (Onay Mekanizması)

### ACA Agent Onay Sistemi (`core/agent/approval_manager.py`)

```
ApprovalManager
├── RiskLevel dört seviye:
│   ├── NONE (sınırsız)     → otomatik
│   ├── LOW (inceleme)      → log + devam
│   ├── MEDIUM (onay gerekli) → kullanıcı onayı bekle
│   └── HIGH (yasak)        → engelle
│
├── approve(action) → bool
│   └── RiskLevel MEDIUM ise UI callback ile kullanıcıya sor
│
└── İzin verilenler:
    ├── Dosya okuma: NONE
    ├── Dosya yazma: LOW (bilinen konumlar), MEDIUM (sistem)
    ├── Shell komutu: MEDIUM
    └── Sistem değişikliği: HIGH
```

### Ana Pipeline Onayı (main.py)

| İşlem | Onay Gerekli | Not |
|-------|-------------|-----|
| Browser kontrol | `_user_initiated` | AI izinsiz açamaz |
| Shell komutu | İçerik filtresi | `BLOCKED_PREFIXES` ile korunur |
| Tool çağrısı | Tool whitelist | `VALID_TOOLS` seti |
| Skill çalıştırma | Pattern eşleşmesi | Öngörülebilir komutlar |

## Hata Yönetimi & Retry

### Exception Handling Stratejisi

```python
# main.py — Global exception handlers
sys.excepthook = handle_exception          # Ana thread exception
threading.excepthook = handle_thread_exception  # Thread exception
```

| Hata Türü | Davranış |
|-----------|----------|
| Provider bağlantı hatası | Yeniden bağlan, 3 deneme |
| Tool çalışma hatası | Hata string'i LLM'e döner |
| UI hatası | `_gui_queue` ile thread-safe hata iletimi |
| Beklenmeyen exception | `logs/jarvis.log`'a yaz, CRASH log dosyasına kaydet |
| Stream parsing hatası | Kısmi chunk'lar atlanır, traceback gerekmez |

### Thread Safety

| Korumalı Alan | Kilit | Kullanım |
|---------------|-------|----------|
| `_is_speaking` | `_speaking_lock` (Lock) | Konuşma durumu |
| Ses callback'leri | Queue lock | UI güncellemeleri |
| Tool execution | ThreadPoolExecutor | Blokeli işlemler |
| Audio stream | Sequential open | PortAudio race condition |

## Kod Referansı

### 1. Ana Çalışma Döngüsü (`run()`)

```python
def run(self):
    config = load_app_config()
    self._backend_type = config.get("backend_type", "gemini")
    
    if not has_gemini_api_key():
        self._backend_type = "ollama"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    self._loop = loop
    
    try:
        provider = self._create_provider()
        loop.run_until_complete(provider.start(self))
        
        if hasattr(provider, '_on_stt_text'):
            provider._on_stt_text = self._on_stt_text
            provider._on_user_spoke = self._on_user_spoke
        
        loop.run_until_complete(provider.run_loop())
    except KeyboardInterrupt:
        pass
    finally:
        if provider:
            loop.run_until_complete(provider.stop())
        loop.close()
```

**Adım adım:**
1. Config'den backend türünü oku
2. API anahtarı yoksa Ollama'ya düş
3. asyncio event loop oluştur
4. Provider'ı yarat ve başlat
5. Provider'ın run_loop()'u çalıştır (bloklar)
6. Kesinti/hatada provider'ı durdur

### 2. Tool Handler Dispatch

```python
_TOOL_HANDLERS = {
    "set_volume":        "_handle_set_volume",
    "get_system_health": "_handle_get_system_health",
    "open_app":          "_handle_open_app",
    "sys_info":          "_handle_sys_info",
    "browser_control":   "_handle_browser_control",
    "shell_run":         "_handle_shell_run",
    "send_whatsapp":     "_handle_send_whatsapp",
    ...
    40 entries total
}
```

### 3. Thread Modeli

```python
# Ana thread: asyncio event loop
# UI thread: Tkinter mainloop (process_gui_queue ile senkron)
# Background: ThreadPoolExecutor (blokeli işlemler)
# Cron: threading.Thread (zamanlanmış görevler)
# File watcher: watchdog polling thread

self._executor = ThreadPoolExecutor(max_workers=4)
```

[Bkz. ARCHITECTURE.md](ARCHITECTURE.md) | [Bkz. AGENTS.md](AGENTS.md) | [Bkz. SKILLS.md](SKILLS.md) | [Bkz. STATE_MANAGEMENT.md](STATE_MANAGEMENT.md)
