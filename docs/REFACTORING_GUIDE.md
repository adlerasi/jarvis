# JARVIS Mimarisi Refactoring Rehberi
## God Object -> Moduler Mimari Donusumu

> **Durum:** >200 dosya | **Teshis:** God Objects (JarvisUI/JarvisLive), dusuk cohesion, 72+ izole node  
> **Hedef:** Yuksek cohesion, dusuk coupling, test edilebilir, olceklenebilir mimari  

## Genel Tamamlanma Durumu

| Faz | Kapsam | Durum | Aciklama |
|-----|--------|-------|----------|
| **Faz 1** | Core Layer (types, config, constants, exceptions, utils) | 🟡 **KISMEN** | `core/types.py` ✅ `core/config.py` ✅ `core/constants.py` ✅ `core/exceptions.py` ✅ — `core/utils/text.py`, `date.py`, `validation.py` ❌ |
| **Faz 2** | Event Bus + State Machine + Lifecycle | 🟢 **TAMAM** | `orchestrator/event_bus.py` ✅ `orchestrator/state_machine.py` ✅ `orchestrator/lifecycle.py` ✅ — `session_orchestrator.py` ❌ (JarvisLive henüz ayrıştırılmadı) |
| **Faz 3** | God Object Parcalama (JarvisUI, JarvisLive) | 🔴 **YAPILMADI** | `ui.py` hala tek parça. `orchestrator/session_orchestrator.py` yok. |
| **Faz 4** | Audio Pipeline Soyutlama | 🔴 **YAPILMADI** | Ses modulleri henüz `audio/pipeline.py` altinda toplanmadi. |
| **Faz 5** | Provider Soyutlama | 🟢 **TAMAM** | `providers/base.py` ✅ `providers/factory.py` ✅ — Ancak provider'lar hala `core/` altinda. |
| **Faz 6** | Skill Sistemi (Singleton'dan cikis) | 🟢 **TAMAM** | `skills/base.py` ✅ `skills/registry.py` ✅ — `skills/router.py` ❌ |
| **Faz 7** | Olu Kod Temizligi | 🔴 **YAPILMADI** | 72+ izole node, 1500+ zayif baglanti |
| **Test** | Unit/Integration ayrimi | 🔴 **YAPILMADI** | Tum testler `tests/` altinda duz, `unit/` ve `integration/` yok |

> ✅ = Tamamlandı | 🟡 = Kısmen | ❌ = Eksik | 🔴 = Henüz başlanmadı

---

## 1. Mevcut Hastaliklarin Teshisi

### 1.1 God Objects
| Nesne | Baglanti | Sorun |
|-------|----------|-------|
| `JarvisUI` | 85 edge | UI + Ses + LLM + Saglik + Dosya yonetimi hepsi burada |
| `JarvisLive` | 81 edge | Orkestrasyon + Provider + Ses pipeline + State machine ic ice |

**Sonuc:** Bir degisiklik 10 farkli yeri etkiler. Regresyon hatalari kacinilmaz.

### 1.2 Dusuk Cohesion (Birliktelik)
- `ui.py` icinde: `font_body_bold()`, `draw_utils`, `orb_canvas`, `sound_manager`, `state_machine`
- `main.py` icinde: `load_system_prompt()`, `clean_transcript_text()`, provider switch, event loop
- Bir modulun cohesion skoru **0.50+** olmali; sizdekiler **0.06-0.09**

### 1.3 Izole & Zayif Baglantilar
- **72 izole node:** Kullanilmayan fonksiyonlar, yarim entegrasyonlar, olu kod
- **1504 zayif baglanti:** Moduller birbirini dolayli/tahmini kullaniyor; dokumantasyon yetersiz

### 1.4 Singleton ve Siki Baglilik
- `SkillManager` singleton -> test edilemez, paralel calismaz
- `speak_text()`, `get_tts_engine()` her yere yayilmis kopru fonksiyonlar

---

## 2. Hedef Mimari: "Onion Architecture + Event-Driven"

```
+-----------------------------------------+
|  UI Layer (Tkinter)                     |  <- Sadece gorsel, is mantigi yok
|  - OrbCanvas                            |
|  - StateBadge                           |
|  - MicLevelIndicator                    |
+-----------------------------------------+
|  Orchestrator Layer (Event Bus)         |  <- Sadece koordinasyon
|  - SessionOrchestrator                  |
|  - EventBus (pub-sub)                   |
|  - StateMachine                         |
+-----------------------------------------+
|  Application Layer (Skills & Use Cases) |  <- Is mantigi
|  - SkillDispatcher                      |
|  - SkillRegistry (non-singleton)        |
|  - ToolRegistry                         |
+-----------------------------------------+
|  Infrastructure Layer                   |  <- Teknik detay
|  - AudioPipeline (RNNoise->VAD->STT->TTS)|
|  - LLMProviders (Ollama/Gemini)         |
|  - SystemAdapters (Process, Disk, Net)  |
+-----------------------------------------+
|  Core/Domain Layer                      |  <- Pure fonksiyonlar, types
|  - Types, Config, Utils                 |
|  - MemoryManager (interface)            |
+-----------------------------------------+
```

---

## 3. Yeni Dosya Yapisi (Onerilen)

```
jarvis/
+-- main.py                          # Sadece bootstrap: config -> orchestrator -> ui
|
+-- core/                            # Domain + Pure fonksiyonlar (hicbir IO yok)
|   +-- __init__.py
|   +-- types.py                     # Tum dataclass'lar, Enum'lar, Protocol'lar
|   +-- config.py                    # Config okuma/yazma (sadece I/O, logic yok)
|   +-- constants.py                 # Renkler, sesler, state'ler
|   +-- exceptions.py                # Ozel exception'lar
|   +-- utils/
|   |   +-- text.py                  # clean_transcript_text, split_sentences
|   |   +-- date.py                  # parse_iso, day_label
|   |   +-- validation.py            # Input sanitization
|
+-- orchestrator/                    # SADECE koordinasyon
|   +-- __init__.py
|   +-- session_orchestrator.py      # Eski JarvisLive'in yerine
|   +-- event_bus.py                 # Pub-sub: moduller birbirini dogrudan cagirmaz
|   +-- state_machine.py             # IDLE -> LISTENING -> THINKING -> SPEAKING
|   +-- lifecycle.py                 # start(), stop(), graceful shutdown
|
+-- ui/                              # SADECE Tkinter ve gorsel
|   +-- __init__.py
|   +-- app.py                       # Eski JarvisUI -> sadece root window
|   +-- orb_canvas.py                # 3D orb animasyonu (pure math + draw)
|   +-- components/
|   |   +-- state_badge.py           # Durum rozeti
|   |   +-- mic_level.py             # Mikrofon seviyesi gostergesi
|   |   +-- log_panel.py             # Log akisi
|   +-- draw_utils.py                # _ac, _bar, _bracket (pure fonksiyonlar)
|
+-- audio/                           # Ses pipeline (tek sorumluluk)
|   +-- __init__.py
|   +-- pipeline.py                  # AudioPipeline: RNNoise->VAD->STT->TTS sirasi
|   +-- microphone.py                # MicrophoneStream (sadece capture)
|   +-- noise_suppressor.py          # RNNoise wrapper (48kHz -> 16kHz resampling)
|   +-- vad_engine.py                # Silero/WebRTC/Energy VAD
|   +-- stt_engine.py              # faster-whisper + Google Speech fallback
|   +-- tts_engine.py              # Piper/edge-tts/pyttsx3 dispatcher
|   +-- emotion_tts.py             # Duygu modulasyonu
|   +-- voice_manager.py           # Ses tonu yonetimi
|   +-- audio_player.py            # Cross-platform player
|
+-- providers/                       # LLM provider'lar (isolated)
|   +-- __init__.py
|   +-- base.py                      # BaseProvider (ABC) -> jarvis ref YOK
|   +-- ollama_provider.py         # Sadece HTTP API cagrileri
|   +-- gemini_provider.py         # Sadece Gemini API cagrileri
|   +-- factory.py                   # create_provider(type, config) -> instance
|
+-- skills/                          # Her skill kendi klasorunde
|   +-- __init__.py
|   +-- registry.py                  # SkillRegistry (non-singleton, injectable)
|   +-- router.py                    # route_x_request() fonksiyonlari
|   +-- base.py                      # BaseSkill (ABC)
|   +-- weather/
|   |   +-- __init__.py
|   |   +-- skill.py                 # WeatherSkill class
|   |   +-- intent.py                # classify_weather_intent()
|   |   +-- tests/                   # Sadece weather testleri
|   +-- browser/
|   +-- reminders/
|   +-- calendar/
|   +-- media/
|   +-- youtube/
|   +-- whatsapp/
|   +-- system/
|   |   +-- __init__.py
|   |   +-- health.py
|   |   +-- process_manager.py
|   |   +-- disk_predictor.py
|   |   +-- network_monitor.py
|   +-- ...
|
+-- memory/                          # Kalici ve gecici bellek
|   +-- __init__.py
|   +-- manager.py                   # MemoryManager (interface-driven)
|   +-- conversation_transcript.py   # Son N konusma
|   +-- voice_memory.py              # Sesli oturum gecmisi
|
+-- actions/                         # OpenClaw'dan uyarlanan sistem aksiyonlari
|   +-- __init__.py
|   +-- file_watcher.py
|   +-- cron_web_ui.py
|   +-- system_cron.py
|   +-- ...
|
+-- tests/                           # Mirror directory yapisi
|   +-- unit/                        # Her modul icin izole test
|   +-- integration/                 # 2-3 modulun birlikte testi
|   +-- conftest.py                  # Fixtures, mock'lar
|
+-- docs/
|   +-- ARCHITECTURE.md              # Modul sozlesmeleri (contracts)
|   +-- API.md                       # Her modulun public API'si
```

---

## 4. Adim Adim Refactoring Plani (Fazli)

> **Guncel Durum:** Her fazin basinda ✅/🟡/🔴 isareti ile tamamlanma seviyesi belirtilmistir.  
> Faz 2, 5, 6 kodlari yazilmis, faz 1 kismen yazilmistir.  
> Faz 3, 4, 7 ve test yeniden yapilanmasi icin calisma baslatilmamistir.

### Faz 1: Temel Katman (1-2 gun) 🟡 KISMEN TAMAM
**Hedef:** `core/` katmanini olustur, tum moduller buraya bagimli olsun.
**Durum:** 4/7 dosya tamam. `core/utils/` altinda text.py, date.py, validation.py eksik.

```python
# core/types.py
from dataclasses import dataclass
from typing import Protocol, Optional, Callable
from enum import Enum, auto

class SystemState(Enum):
    IDLE = auto()
    INITIALISING = auto()
    CONNECTING = auto()
    LISTENING = auto()
    THINKING = auto()
    SPEAKING = auto()
    MUTED = auto()
    PAUSED = auto()
    ERROR = auto()

@dataclass(frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    frame_duration_ms: int = 10
    channels: int = 1

@dataclass(frozen=True)
class ProviderConfig:
    provider_type: str  # "ollama" | "gemini"
    api_key: Optional[str] = None
    model: str = "qwen2.5:1.8b"
    base_url: Optional[str] = None

class AudioChunk(Protocol):
    # Ses verisi protokolu - her audio modul bu sekilde konusur.
    def pcm_int16(self) -> bytes: ...
    def sample_rate(self) -> int: ...
    def duration_ms(self) -> int: ...
```

### Faz 2: Event Bus (1 gun) 🟢 TAMAM
**Hedef:** Moduller birbirini dogrudan cagirmasin, event'lerle haberlessin.
**Durum:** `orchestrator/event_bus.py`, `state_machine.py`, `lifecycle.py` yazildi.
- `session_orchestrator.py` (JarvisLive yerine) henuz yazilmadi — bu Faz 3 kapsaminda.

```python
# orchestrator/event_bus.py
from typing import Dict, List, Callable, Any
from collections import defaultdict

class EventBus:
    # Merkeziyetsiz haberlesme. Hicbir modul digerini import etmez.

    def __init__(self):
        self._subs: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        self._subs[event_type].append(callback)

    def publish(self, event_type: str, payload: Any = None):
        for cb in self._subs[event_type]:
            try:
                cb(payload)
            except Exception as e:
                # Hata izole kalir, diger callback'leri etkilemez
                self.publish("error", {"source": event_type, "exception": e})

# Kullanim:
# bus.publish("wake_word_detected", {"keyword": "jarvis"})
# bus.subscribe("stt_text", lambda p: skill_dispatcher.handle(p["text"]))
# bus.subscribe("state_change", lambda p: ui.update_state(p["new_state"]))
```

### Faz 3: God Object'leri Parcala (3-5 gun) 🔴 YAPILMADI

**Durum:** `ui.py` (1800+ satir) hala tek parca. `main.py`'deki `JarvisLive` (1300+ satir) henuz `session_orchestrator.py`'ye tasinmadi. Asagidaki kod ornekleri **hedef mimariyi** gosterir — henuz uygulanmadi.

#### 3a. JarvisUI -> ui/app.py (sadece container)
```python
# ui/app.py
import tkinter as tk
from ui.orb_canvas import OrbCanvas
from ui.components.state_badge import StateBadge
from ui.components.mic_level import MicLevelIndicator

class JarvisUI:
    # Sadece Tkinter pencere yonetimi. Is mantigi YOK.

    def __init__(self, event_bus: EventBus):
        self.bus = event_bus
        self.root = tk.Tk()

        # Bilesenler kendi iclerinde bagimsiz
        self.orb = OrbCanvas(self.root, event_bus)
        self.badge = StateBadge(self.root)
        self.mic = MicLevelIndicator(self.root)

        # Event'lere abone ol - dogrudan cagri yok
        event_bus.subscribe("state_change", self._on_state_change)
        event_bus.subscribe("mic_level", self._on_mic_level)

    def _on_state_change(self, payload):
        new_state = payload["new_state"]
        self.badge.set_state(new_state)
        self.orb.set_animation(new_state)

    def _on_mic_level(self, payload):
        self.mic.set_level(payload["level"])

    def run(self):
        self.root.mainloop()
```

#### 3b. JarvisLive -> orchestrator/session_orchestrator.py
```python
# orchestrator/session_orchestrator.py
from typing import Optional
from orchestrator.event_bus import EventBus
from orchestrator.state_machine import StateMachine
from audio.pipeline import AudioPipeline
from providers.factory import ProviderFactory
from skills.registry import SkillRegistry

class SessionOrchestrator:
    # Sadece koordinasyon. Hicbir API cagrisi yapmaz.

    def __init__(
        self,
        event_bus: EventBus,
        audio_pipeline: AudioPipeline,
        provider_factory: ProviderFactory,
        skill_registry: SkillRegistry,
    ):
        self.bus = event_bus
        self.audio = audio_pipeline
        self.providers = provider_factory
        self.skills = skill_registry
        self.state = StateMachine(event_bus)

        # Event abonelikleri
        event_bus.subscribe("wake_word_detected", self._start_listening)
        event_bus.subscribe("stt_final_text", self._process_user_input)
        event_bus.subscribe("tts_started", lambda _: self.state.transition_to("SPEAKING"))
        event_bus.subscribe("tts_finished", lambda _: self.state.transition_to("IDLE"))

    def _start_listening(self, payload):
        self.state.transition_to("LISTENING")
        self.audio.start_recording()

    def _process_user_input(self, payload):
        text = payload["text"]
        self.state.transition_to("THINKING")

        # 1. Skill on kapisi (pre-LLM gate)
        skill_result = self.skills.route(text)
        if skill_result:
            self.bus.publish("response_ready", {"text": skill_result, "source": "skill"})
            return

        # 2. LLM'e git
        provider = self.providers.get_active()
        response = provider.send_message(text)
        self.bus.publish("response_ready", {"text": response, "source": "llm"})
```

### Faz 4: Audio Pipeline (2-3 gun) 🔴 YAPILMADI

**Durum:** Ses modulleri (`audio/` altinda) mevcut ancak henuz `AudioPipeline` sinifi altinda toplanmadi. `audio/pipeline.py` bos bir cerceve olarak mevcut. Asagidaki kod **hedef mimariyi** gosterir.

```python
# audio/pipeline.py
from typing import Optional, Callable
from audio.microphone import MicrophoneStream
from audio.noise_suppressor import NoiseSuppressor
from audio.vad_engine import VADEngine
from audio.stt_engine import STTEngine
from audio.tts_engine import TTSEngine

class AudioPipeline:
    # Ses verisi tek yonde akar: Mic -> RNNoise -> VAD -> STT -> LLM -> TTS -> Speaker.

    def __init__(
        self,
        mic: MicrophoneStream,
        suppressor: NoiseSuppressor,
        vad: VADEngine,
        stt: STTEngine,
        tts: TTSEngine,
        event_bus,  # Protocol olarak
    ):
        self.mic = mic
        self.suppressor = suppressor
        self.vad = vad
        self.stt = stt
        self.tts = tts
        self.bus = event_bus

        # Zinciri kur
        self.mic.on_audio = self._on_mic_audio
        self.vad.on_speech_end = self._on_speech_segment
        self.stt.on_text = self._on_stt_text

    def _on_mic_audio(self, pcm_bytes: bytes, sample_rate: int):
        # 1. Gurultu bastirma (48kHz native -> RNNoise -> 16kHz)
        clean = self.suppressor.process(pcm_bytes, sample_rate)

        # 2. VAD'e gonder
        is_speech, confidence = self.vad.process_frame(clean)
        if is_speech:
            self.stt.feed_audio(clean)

        # 3. UI'e mikrofon seviyesi gonder
        level = self._calculate_level(clean)
        self.bus.publish("mic_level", {"level": level})

    def _on_speech_segment(self, segment: bytes):
        self.stt.finalize_segment(segment)

    def _on_stt_text(self, text: str):
        self.bus.publish("stt_final_text", {"text": text})

    def speak(self, text: str, emotion: str = "neutral"):
        self.bus.publish("tts_started", {})
        self.tts.speak(text, emotion=emotion)
        self.bus.publish("tts_finished", {})

    def start_recording(self):
        self.mic.start()

    def stop(self):
        self.mic.stop()
        self.stt.clear()
```

### Faz 5: Provider Soyutlama (1-2 gun) 🟢 TAMAM

**Hedef:** Ollama <-> Gemini gecisi tek satirda, sifir cakisma.
**Durum:** `providers/base.py` ve `providers/factory.py` yazildi. Provider'lar (gemini_provider.py, ollama_provider.py) hala `core/` altinda — `providers/` altina tasinmadi. Kod ornekleri asagida mevcuttur ve halihazirda uygulanmis durumdadir:

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import Iterator, Optional
from core.types import ProviderConfig

class BaseProvider(ABC):
    # Provider'lar birbirini bilmez. Orchestrator sadece bu interface'i gorur.

    def __init__(self, config: ProviderConfig):
        self.config = config

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def send_message(self, text: str) -> str: ...

    @abstractmethod
    def send_audio_chunk(self, chunk: bytes) -> Optional[str]: ...

    @abstractmethod
    def supports_streaming_audio(self) -> bool: ...

    @abstractmethod
    def supports_tools(self) -> bool: ...

    def cleanup(self):
        # Varsayilan: hicbir sey yapma. Override edilebilir.
        pass

# providers/factory.py
from core.types import ProviderConfig
from providers.ollama_provider import OllamaProvider
from providers.gemini_provider import GeminiProvider

class ProviderFactory:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._providers = {
            "ollama": OllamaProvider,
            "gemini": GeminiProvider,
        }
        self._active: Optional[BaseProvider] = None

    def create(self, provider_type: str) -> BaseProvider:
        if provider_type not in self._providers:
            raise ValueError(f"Bilinmeyen provider: {provider_type}")
        return self._providers[provider_type](self.config)

    def switch(self, provider_type: str):
        # Sifir cakisma: eski provider cleanup, yeni initialize.
        if self._active:
            self._active.cleanup()
        self._active = self.create(provider_type)

    def get_active(self) -> BaseProvider:
        if not self._active:
            raise RuntimeError("Provider atanmamis")
        return self._active
```

### Faz 6: Skill Sistemi (2-3 gun) 🟢 TAMAM

**Hedef:** Singleton kaldir, her skill bagimsiz, hot-reload destekli.
**Durum:** `skills/base.py` ve `skills/registry.py` yazildi. SkillRegistry non-singleton, injectable, auto-discover yapabiliyor. `skills/router.py` henuz yazilmadi. Kod ornekleri asagida mevcuttur ve halihazirda uygulanmis durumdadir:

```python
# skills/base.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class BaseSkill(ABC):
    # Her skill kendi intent classification ve execution'ini tasir.

    @property
    @abstractmethod
    def skill_id(self) -> str: ...

    @property
    @abstractmethod
    def triggers(self) -> list[str]: ...

    @abstractmethod
    def classify_intent(self, text: str) -> float:
        # 0.0-1.0 arasi eslesme skoru.
        ...

    @abstractmethod
    def execute(self, text: str, context: Dict[str, Any]) -> Optional[str]:
        # Skill calistir. Sonuc yoksa None dondur.
        ...

# skills/registry.py (NON-SINGLETON)
from typing import List, Optional
from skills.base import BaseSkill

class SkillRegistry:
    # Injectable, test edilebilir, coklu instance'a acik.

    def __init__(self):
        self._skills: List[BaseSkill] = []

    def register(self, skill: BaseSkill):
        self._skills.append(skill)

    def route(self, text: str, context: dict) -> Optional[str]:
        # En yuksek skorlu skill'i calistir. Esik altindaysa None.
        candidates = [(s, s.classify_intent(text)) for s in self._skills]
        candidates = [(s, score) for s, score in candidates if score > 0.6]

        if not candidates:
            return None

        best_skill, score = max(candidates, key=lambda x: x[1])
        return best_skill.execute(text, context)

    def reload_skill(self, skill_id: str):
        # Hot-reload: skill modulunu yeniden import et.
        pass
```

### Faz 7: Olu Kod Temizligi (1 gun) 🔴 YAPILMADI
**Hedef:** 72+ izole node'u ya entegre et, ya kaldir. Henuz baslanmadi.

```python
# scripts/cleanup_dead_code.py
# Bu script ile izole fonksiyonlari tespit etip karar ver:
# 1. Kullaniliyor mu? (grep ile ara)
# 2. Testi var mi? (pytest --collect-only)
# 3. Yoksa -> sil veya archive/ klasorune tas
```

---

## 5. Bagimlilik Kurallari (Kesin)

```
+-------------+     +-------------+     +-------------+
|     UI      |---->| Orchestrator|---->|  Skills     |
+-------------+     +-------------+     +-------------+
                           |                   |
                           v                   v
                    +-------------+     +-------------+
                    |   Audio     |     |  Providers  |
                    +-------------+     +-------------+
                           |                   |
                           +---------+---------+
                                     v
                              +-------------+
                              |    Core     |
                              |  (types,    |
                              |  utils)     |
                              +-------------+
```

**Kural:** Ok yonunde import. Geri donus YOK.
- `core` hicbir sey import etmez (sadece stdlib).
- `audio` sadece `core` import eder.
- `providers` sadece `core` import eder.
- `skills` sadece `core` ve kendi alt modullerini import eder.
- `orchestrator` `audio`, `skills`, `providers`'i bilir ama onlari instantiate etmez (DI ile alir).
- `ui` sadece `core` ve `orchestrator.event_bus`'i bilir.

---

## 6. Test Stratejisi (Cohesion'u Dogrula) 🔴 YAPILMADI

**Durum:** Tum testler `tests/` altinda duz liste halinde. `unit/` ve `integration/` alt klasorleri henuz olusturulmadi.

```
tests/
+-- unit/
|   +-- core/                  # Pure fonksiyonlar - hic mock yok
|   +-- audio/
|   |   +-- test_pipeline.py   # Zincir testi (mock her adim)
|   |   +-- test_vad.py        # Sadece VAD logic
|   |   +-- test_stt.py        # Sadece STT logic
|   +-- providers/
|   |   +-- test_ollama.py     # HTTP mock
|   |   +-- test_gemini.py     # API mock
|   +-- skills/
|   |   +-- test_weather.py    # WeatherSkill izole
|   +-- orchestrator/
|   |   +-- test_event_bus.py  # Pub-sub davranisi
|
+-- integration/
|   +-- test_audio_to_stt.py   # Mic -> VAD -> STT zinciri
|   +-- test_orchestrator_e2e.py  # Wake word -> Response
|   +-- test_provider_switch.py   # Ollama -> Gemini gecisi
|
+-- conftest.py                # Shared fixtures, factories
```

**Kural:** Unit test'te bir modul disariya cagri yapmaz. Integration test'te maksimum 3 modul.

---

## 7. Hizli Kazanimlar (Bugun Baslayabilecegin)

| # | Eylem | Tahmini Etki | Sure | Durum |
|---|-------|-------------|------|-------|
| 1 | `core/types.py` olustur, tum `Enum` ve `dataclass`'lari topla | Yuksek | 30 dk | ✅ |
| 2 | `EventBus` implemente et, `JarvisUI`'den `JarvisLive`'a dogrudan cagrilari kaldir | Cok Yuksek | 2 saat | ✅ |
| 3 | `speak_text()` fonksiyonunu `audio/pipeline.py`'ye tas, global erisimi kes | Yuksek | 1 saat | 🔴 |
| 4 | `SkillManager`'i singleton'dan cikar, constructor'dan al | Yuksek | 1 saat | ✅ |
| 5 | 72 izole fonksiyonu `grep` ile ara, kullanilmayanlari sil | Orta | 1 saat | 🔴 |
| 6 | `ui.py`'yi `ui/app.py`, `ui/orb_canvas.py`, `ui/draw_utils.py` olarak bol | Yuksek | 3 saat | 🔴 |
| 7 | `core/utils/text.py`, `date.py`, `validation.py` olustur | Orta | 30 dk | ❌ |
| 8 | `skills/router.py` olustur, route mantigini ayir | Orta | 30 dk | ❌ |
| 9 | `providers/` altina guncel provider'lari tasi | Yuksek | 1 saat | 🔴 |
| 10 | `orchestrator/session_orchestrator.py` olustur (JarvisLive'den ayir) | Cok Yuksek | 3 saat | 🔴 |

> ✅ = Yapildi | ❌ = Eksik (kolay, kisa surede tamamlanabilir) | 🔴 = Henuz baslanmadi

---

## 8. Sonuc Beklentisi

| Metrik | Refactoring Oncesi | Su Anki Durum | Hedef |
|--------|-------------------|---------------|-------|
| Cohesion (UI) | 0.07 | ~0.07 (degismedi, ui.py tek parca) | 0.50+ |
| Cohesion (Audio) | 0.12 | ~0.12 (degismedi, pipeline yok) | 0.60+ |
| God Object baglantisi | 85 | ~85 (JarvisUI/JarvisLive hala tek) | <20 |
| Izole node | 72 | 72+ (temizlik yapilmadi) | 0 |
| Zayif baglanti | 1504 | ~1504 (ziyadesiyle ayni) | <200 |
| Test coverage | Bilinmiyor | ~4691 test (duz tests/) | %80+ |
| Provider switch suresi | Patliyor | Patliyor (hata alabiliyor) | <100ms |
| event_bus | Yok | ✅ Var (106 satir) | ✅ |
| state_machine | String tabanli | ✅ Enum + EventBus (95 satir) | ✅ |
| skill_registry | Singleton | ✅ Non-singleton (152 satir) | ✅ |
| provider_factory | Yok | ✅ Var (76 satir) | ✅ |

---

> **Not:** Bu refactoring'i yaparken mevcut `main.py`'yi bozmadan calistirabilirsin. Yeni klasor yapisini yanina kur, eski dosyalardan parca parca tas. Eski `JarvisUI` ve `JarvisLive`'i silmeye **en son** karar ver.
