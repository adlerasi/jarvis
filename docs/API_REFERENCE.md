# Dahili API Referansı

## Modüller Arası Arayüzler

### main.py `JarvisLive` → Provider API

```
JarvisLive → provider.start(jarvis_self)  # Provider'ı başlat
JarvisLive → provider.run_loop()          # Ana döngüyü çalıştır
JarvisLive → provider.stop()              # Provider'ı durdur
JarvisLive → provider.send_text(text)     # Metin gönder
```

| Metot | Parametreler | Dönüş | Açıklama |
|-------|-------------|-------|----------|
| `start(jarvis)` | `jarvis: JarvisLive` | `None` | Provider'a Jarvis referansını verir |
| `run_loop()` | Yok | `None` (bloklar) | Ana işlem döngüsü |
| `stop()` | Yok | `None` | Kaynakları temizle |
| `send_text(text)` | `text: str` | `None` | Kullanıcı metnini LLM'e ilet |
| `send_audio(data)` | `data: bytes` | `None` | Ses verisini LLM'e ilet (opsiyonel) |

**Provider → JarvisLive (callback'ler):**

```python
# Provider içinde kullanılan Jarvis metotları
self._j()._execute_tool(name, args, loop)  # Tool çağrısı
self._j().set_state(state)                  # State güncelle
self._j().write_log(text)                   # Log yaz
self._j().write_debug(text)                 # Debug yaz
self._j()._speak_response(text)             # TTS ile konuş
self._j()._speak_proactive(text)            # Kendi kendine konuş
```

### main.py `JarvisLive` → Action Modülleri

```
JarvisLive._execute_tool(tool_name, args, loop)
    │
    ├── TOOL_HANDLER_MAP[tool_name] → handler_name
    ├── getattr(self, handler_name) → handler metod
    │
    └── handler(args, loop) → str sonuç
```

Handler API:
| Metot | Parametreler | Dönüş | Açıklama |
|-------|-------------|-------|----------|
| `_handle_open_app(args, loop)` | `args: dict`, `loop: event_loop` | `str` | Uygulama aç |
| `_handle_sys_info(args, loop)` | `args: dict`, `loop: event_loop` | `str` | Sistem bilgisi |
| `_handle_browser_control(args, loop)` | `args: dict`, `loop: event_loop` | `str` | Tarayıcı kontrol |
| ... | ... | ... | 40 handler |

### JarvisLive → SkillManager API

```python
# core/skill_manager.py
class SkillManager:
    def route(self, user_text: str) -> str | None
    def list_skills(self) -> list[str]
    def get_skill(self, skill_id: str) -> SkillInfo | None
    def reload_skill(self, skill_id: str) -> bool
```

| Metot | Parametreler | Dönüş | Açıklama |
|-------|-------------|-------|----------|
| `route(text)` | `text: str` | `str \| None` | Metni skill'lerle eşleştir |
| `list_skills()` | Yok | `list[str]` | Yüklü skill ID'leri |
| `get_skill(id)` | `id: str` | `SkillInfo \| None` | Skill detayı |
| `reload_skill(id)` | `id: str` | `bool` | Skill'i yeniden yükle |

### Skill → SkillEngine API

```python
# core/_skill_engine.py
class SkillEngine:
    def discover_and_load(self, skills_dir: Path) -> None
    def route(self, user_text: str) -> str | None
    def get_skills(self) -> dict[str, SkillInfo]
    def get_skill(self, skill_id: str) -> SkillInfo | None
    def reload_skill(self, skill_id: str) -> bool
    def unload_skill(self, skill_id: str) -> None
```

### ACA Agent API

```python
# core/agent/agent_manager.py
class AgentManager:
    def execute_goal(self, goal_text: str, callbacks: dict | None = None) -> str
    def get_goal(self, goal_id: str) -> AgentGoal | None
    def list_goals(self) -> list[AgentGoal]
    def cancel_goal(self, goal_id: str) -> bool
    
    # Alt bileşenler
    self.observer: Observer
    self.planner: Planner
    self.executor: Executor
    self.reflection: Reflection
    self.approval: ApprovalManager
```

| Metot | Parametreler | Dönüş | Açıklama |
|-------|-------------|-------|----------|
| `execute_goal(text, cb)` | `text: str`, `callbacks: dict` | `str` | Otonom görev başlat |
| `get_goal(id)` | `goal_id: str` | `AgentGoal \| None` | Goal durumu |
| `list_goals()` | Yok | `list[AgentGoal]` | Tüm goal'ler |
| `cancel_goal(id)` | `goal_id: str` | `bool` | Goal'i iptal et |

### UI ↔ Backend API

```python
# ui.py → main.py callback'leri
ui.on_text_command = self._on_text_command       # Metin komutu
ui.on_pause_toggle = self._on_pause_toggle       # Duraklat
ui.on_effects_state_change = self._on_effects_state_change  # Efekt
ui.on_agent_approval = self._on_agent_approval   # ACA onay

# main.py → ui.py güncellemeleri (thread-safe queue)
def _enqueue_msg(self, msg: dict):
    self._ui._gui_queue.put(msg)

# Kuyruk mesaj formatı:
msg = {
    "type": "state" | "log" | "debug" | "panel",
    "state": "LISTENING",          # type=state için
    "text": "Sistem bilgisi...",   # type=log/debug için
    "panel": "weather",            # type=panel için
}
```

### Tool Registry API

```python
# core/tool_registry.py
_TOOL_DEFS: list[tuple[str, str, dict, list[str]]]  # (name, desc, params, required)
VALID_TOOLS: set[str]                                 # Whitelist
TOOL_HANDLER_MAP: dict[str, str]                      # {name: handler_method}

def generate_gemini_declarations() -> list[dict]
def generate_ollama_tool_help() -> str
```

### Bellek API

```python
# memory/memory_manager.py
def load_memory() -> dict
def update_memory(updates: dict) -> None
def delete_memory(category: str, key: str | None = None, match_text: str | None = None) -> None
def format_memory_for_prompt() -> str
```

### Config API

```python
# app_config.py
def load_app_config() -> dict                           # JSON'dan oku + DEFAULT merge
def save_app_config(updates: dict) -> dict              # JSON'a yaz
def get_app_config_value(key: str, default=None)        # Tek değer oku
def has_gemini_api_key() -> bool                        # API anahtarı var mı?
def get_ollama_models() -> list[str]                    # localhost:11434/api/tags
def get_ollama_tts_voices() -> list[dict]               # Piper + Edge + spd-say
```

### Donanım Tespit API

```python
# core/hardware_detector.py
class HardwareDetector:
    @staticmethod
    def detect_all() -> dict[str, HardwareInfo]
    @staticmethod
    def check_display() -> HardwareInfo
    @staticmethod
    def check_audio() -> HardwareInfo
    @staticmethod
    def check_camera() -> HardwareInfo
```

## Veri Şemaları (Schemas)

### SkillInfo

```python
@dataclass
class SkillInfo:
    skill_id: str
    name: str
    version: str
    folder: str
    module_path: Path
    md_path: Path | None
    triggers_path: Path | None
    route_func: Callable[[str], str | None] | None
    loaded_at: datetime
    last_modified: float
    load_count: int
    error_count: int
    last_error: str | None
    is_active: bool
```

### AgentGoal

```python
@dataclass
class AgentGoal:
    goal_id: str
    text: str
    status: GoalStatus  # PENDING / IN_PROGRESS / COMPLETED / FAILED / CANCELLED
    created_at: float
    started_at: float | None
    completed_at: float | None
    result: str
    total_steps: int
    completed_steps: int
    failed_steps: int
```

### HardwareInfo

```python
@dataclass
class HardwareInfo:
    status: str           # "ok" / "unavailable" / "error"
    label: str            # İnsan okunabilir isim
    detail: str           # Detaylı açıklama
    available: bool
    device_index: int | None  # PyAudio device index
    devices: list[dict]       # Tespit edilen cihazlar
```

### State Machine Validasyonu

```python
_VALID_TRANSITIONS: dict[str, set[str]] = {
    "INITIALISING":  {"LISTENING", "ERROR"},
    "LISTENING":     {"THINKING", "SPEAKING", "ERROR", "PAUSED", "MUTED"},
    "THINKING":      {"SPEAKING", "LISTENING", "ERROR"},
    "SPEAKING":      {"LISTENING", "THINKING", "ERROR", "PAUSED", "MUTED"},
    "ERROR":         {"LISTENING"},
    "PAUSED":        {"LISTENING"},
    "MUTED":         {"LISTENING"},
}
```

## Error Kodları & Exception Hiyerarşisi

```
Exception
├── SkillEngineError (core/_skill_engine.py)
│   ├── SkillLoadError        — Skill modülü yüklenemezse
│   └── SkillNotFoundError    — Skill ID bulunamazsa
│
├── RuntimeError
│   ├── "Cannot start UI — display required"    — Headless ortam
│   ├── "Mikrofon bulunamadi"                    — Ses donanımı yok
│   └── "{name}: jarvis not set (call start())"  — Provider başlatılmamış
│
├── asyncio.TimeoutError        — HTTP/Ollama timeout
├── httpx.RequestError          — Ollama bağlantı hatası
├── json.JSONDecodeError        — Stream/yanıt parse hatası
└── pyaudio.PaError             — PortAudio hatası
```

### Hata Loglama Pattern'i

```python
# DOĞRU — Her except için traceback
try:
    sonuc = riskli_islem()
except Exception:
    traceback.print_exc()

# İSTİSNA — NDJSON stream parser (beklenen kısmi chunk)
except Exception:
    pass  # Flood'u önlemek için

# İSTİSNA — Best-effort fallback
except Exception:
    pass  # Dış çağrıcı zaten logluyor
```

[Bkz. ARCHITECTURE.md](ARCHITECTURE.md) | [Bkz. ORCHESTRATOR.md](ORCHESTRATOR.md) | [Bkz. CONFIG.md](CONFIG.md)
