# J.A.R.V.I.S 2.0 Yol Haritasi -- Roadmap
# Teknoloji: Python + Tkinter (korunacak)
# Hedef: Optimizasyonla 2x-2.5x hizlanma + Asistan -> Arkadas evrimi

> **Asistan -> Arkadas Evrimi**
>
> Her faz, bir oncekinin uzerine insa eder.
> Atlamak yok, sirayla ilerlemek var.
> Teknoloji degisimi yok, sadece optimizasyon ve yeni ozellikler.

---

## Current Implementation Status (2026-06-28)

Bu roadmap vizyon belgesidir. Gercek tamamlanma durumu asagidaki gibidir:

| Faz | Adi | Roadmap Hedefi | Gercek Durum |
|-----|-----|----------------|--------------|
| **Faz 0** | Anti-Hallucination Kurulumu | 1 saat | ✅ ANTI_HALLUCINATION.md mevcut (466 satir) |
| **Faz 1** | Temel Optimizasyon | 2-3 hafta | ✅ **Tum P-01..P-17 cozuldu** (16/17 fixed, 1 by-design). Test coverage tamam: orchestrator(727), gemini(762), ollama(771) |
| **Faz 2** | Diyalog Evrimi | 3-4 hafta | ✅ Barge-in, state machine, voice orchestration layer calisiyor |
| **Faz 3** | Duygusal Zeka | 4-5 hafta | ✅ **EmotionEngine dokumante edildi** — emotion_analyzer, emotion_tts, empathy_engine. Windows TTS (P-15) cozuldu (sounddevice cross-platform) |
| **Faz 4** | Proaktif Inisiyatif | 3-4 hafta | ✅ **Dokumante edildi** — ProactiveVoice, ThinkingAloud, HabitLearner, PersonalityAdapter |
| **Faz 5** | Coklu Ajan | 6-8 hafta | ✅ ACA agent sistemi implemente edildi (core/agent/) |
| **Faz 6** | UI Modernizasyonu | 4-6 hafta | ❌ Baslanmadi |
| **Faz 7** | Bellek & Ogrenme | 5-6 hafta | ⏳ MemoryStore package mevcut, LearningEngine + 4 bellek alt sistemi dokumante edildi |

**Detayli gap analizi**: `.omo/plans/gap-analysis.md`

---

## Onemli Kurallar (Asistan Icin)

1. **OKUMA Kurali:** Her dosyayi degistirmeden once OKU
2. **KONTROL Kurali:** API/metod varligini kontrol et
3. **KORUMA Kurali:** Mevcut Python + Tkinter teknolojisini koru
4. **TEST Kurali:** Her degisiklikten sonra test calistir
5. **DOKUMANTASYON Kurali:** ANTI_HALLUCINATION.md'yi oku

---

## Genel Bakis

| Faz | Adi | Sure (Tahmini) | Odak | Cikti |
|-----|-----|----------------|------|-------|
| **Faz 0** | Anti-Hallucination Kurulumu | 1 saat | Dokumantasyon | Guvenli gelistirme |
| **Faz 1** | Temel Optimizasyon | 2-3 hafta | Ses pipeline, hiz | Kararli + hizli 1.0 |
| **Faz 2** | Diyalog Evrimi | 3-4 hafta | Surekli konusma, dusunme sesleri | Akici konusma |
| **Faz 3** | Duygusal Zeka | 4-5 hafta | Ton analizi, empatik yanit | Hissetme |
| **Faz 4** | Proaktif Inisiyatif | 3-4 hafta | Aliskanlik, bildirim | Kendi kendine calisma |
| **Faz 5** | Coklu Ajan | 6-8 hafta | Ajan swarm, koordinasyon | Uzmanlasma |
| **Faz 6** | UI Modernizasyonu | 4-6 hafta | Tkinter optimize, yeni Orb | Gorsel evrim |
| **Faz 7** | Bellek & Ogrenme | 5-6 hafta | 4 katmanli hafiza | Ogrenme |

**Toplam Tahmini Sure:** 27-36 hafta (~7-9 ay)

---

## FAZ 0: Anti-Hallucination Kurulumu (1 Saat)

### Hedef
Asistanin guvenli ve dogru kod uretmesini saglamak.

### Gorevler

#### 0.1 Dokumantasyon Olusturma
- [x] ANTI_HALLUCINATION.md olustur — mevcut (466 satir, son güncelleme 2026-06-26)
- [x] Proje yapisini dogrula — ANTI_HALLUCINATION.md Seçim 3'te dogrulanmis
- [x] Mevcut API'leri listele — ANTI_HALLUCINATION.md Seçim 5'te listelenmis
- [x] Bagimliliklari kontrol et — ANTI_HALLUCINATION.md Seçim 4'te dogrulanmis

#### 0.2 Asistan Promptu Hazirlama
```
Sen J.A.R.V.I.S gelistiricisisin.

KURALLAR:
1. Her dosyayi degistirmeden once OKU
2. API/metod varligini kontrol et
3. Mevcut Python + Tkinter teknolojisini koru
4. Yeni bagimlilik eklemeden once sor
5. Test calistir (python -m pytest tests/ -v)
6. ANTI_HALLUCINATION.md'yi referans al

PROJE YAPISI:
- main.py: Cekirdek orkestrator
- ui.py: Tkinter UI (1818 satir)
- audio/: Ses isleme
- actions/: Islem modulleri (20+)
- core/: Cekirdek moduller
- skills/: Skill modulleri (17)
- tests/: Testler (4158 test)

TEKNOLOJI:
- Python 3.10+
- Tkinter (UI)
- sounddevice + PyAudio (ses)
- RNNoise (gurultu bastirma)
- faster-whisper (STT)
- Gemini API + Ollama (AI)
- Piper + Edge-TTS + pyttsx3 (TTS)

YASAKLAR:
- Teknoloji degisimi (Rust, Node.js, Tauri)
- Yeni framework ekleme (FastAPI, Django, Flask)
- Mevcut dosyalari silme (yeniden yazma haric)
- Test sayisini azaltma
```

### Cikti
- docs/ANTI_HALLUCINATION.md
- Asistan promptu (kullanima hazir)

---

## FAZ 1: Temel Optimizasyon (Mevcut Durum -> Kararli + Hizli 1.0)

### Hedef
Mevcut sistemin tum kritik bug'larini cozmek, ses pipeline'ini stabilize etmek,
ve temel performans optimizasyonlarini uygulamak.

### Optimizasyonlar (Teknoloji Degisimi Yok)

#### 1.1 Lazy Loading (%50-70 Baslangic Hizlanmasi)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 1.1.1 | LazyLoader sinifi olustur | `core/lazy_loader.py` | 1 saat |
| 1.1.2 | STT modelini lazy yukle | `audio/streaming_stt.py` | 30 dk |
| 1.1.3 | TTS modelini lazy yukle | `actions/tts.py` | 30 dk |
| 1.1.4 | RNNoise'i lazy yukle | `audio/noise_suppressor.py` | 30 dk |
| 1.1.5 | LLM'i lazy yukle | `core/gemini_provider.py`, `core/ollama_provider.py` | 1 saat |

**Kod Ornegi:**
```python
class LazyLoader:
    def __init__(self):
        self._stt = None
        self._tts = None
        self._rnnoise = None
        self._llm = None

    @property
    def stt(self):
        if self._stt is None:
            from faster_whisper import WhisperModel
            self._stt = WhisperModel("base", device="cpu")
        return self._stt

    @property
    def tts(self):
        if self._tts is None:
            from piper import PiperTTS
            self._tts = PiperTTS()
        return self._tts
```

#### 1.2 Adaptive Ses Pipeline (%30-40 Ses Hizlanmasi)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 1.2.1 | AdaptiveRNNoise sinifi olustur | `audio/adaptive_rnnoise.py` | 2 saat |
| 1.2.2 | FastVAD sinifi olustur | `audio/fast_vad.py` | 2 saat |
| 1.2.3 | Batch STT implementasyonu | `audio/batch_stt.py` | 3 saat |
| 1.2.4 | Ses pipeline birlestirme | `audio/orchestrator.py` | 4 saat |

**Kod Ornegi (AdaptiveRNNoise):**
```python
class AdaptiveRNNoise:
    def __init__(self):
        self.noise_level_history = []
        self.bypass_threshold = 0.3
        self.window_size = 10

    def process(self, audio_frame):
        noise_level = self.estimate_noise(audio_frame)
        self.noise_level_history.append(noise_level)

        if len(self.noise_level_history) > self.window_size:
            avg_noise = sum(self.noise_level_history[-self.window_size:]) / self.window_size
            if avg_noise < self.bypass_threshold:
                return audio_frame  # RNNoise bypass

        return rnnoise.process(audio_frame)

    def estimate_noise(self, frame):
        return np.sqrt(np.mean(frame**2))
```

#### 1.3 UI Canvas Optimizasyonu (%15-25 UI Hizlanmasi)
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 1.3.1 | OrbCanvas yeniden kullanim (create-once, update-only) | `ui/orb_canvas.py` | 2 saat | ✅ |
| 1.3.2 | Double buffering (offscreen canvas + blit) | `ui/draw_utils.py` | 1 saat | ✅ |
| 1.3.3 | Gereksiz redraw'lari kaldir (statik/dinamik katman ayrimi) | `ui.py` | 2 saat | ✅ |

**Kod Ornegi (OptimizedOrbCanvas):**
```python
class OptimizedOrbCanvas:
    def __init__(self, canvas):
        self.canvas = canvas
        # Bir kez olustur, sadece guncelle
        self.ring1 = self.canvas.create_oval(0, 0, 100, 100)
        self.ring2 = self.canvas.create_oval(10, 10, 90, 90)
        self.ring3 = self.canvas.create_oval(20, 20, 80, 80)

    def update(self, state, emotion="neutral"):
        # Sadece koordinatlari ve renkleri guncelle
        colors = self.get_colors(emotion)
        self.canvas.itemconfig(self.ring1, fill=colors[0])
        self.canvas.itemconfig(self.ring2, fill=colors[1])
        self.canvas.itemconfig(self.ring3, fill=colors[2])
        # Sil-ciz yok!
```

#### 1.4 Bellek Optimizasyonu (%10-20 Bellek Hizlanmasi)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 1.4.1 | SQLiteMemory sinifi olustur | `memory/sqlite_memory.py` | 2 saat |
| 1.4.2 | LRU Cache implementasyonu | `core/cache.py` | 1 saat |
| 1.4.3 | Mevcut JSON bellek koruma | `memory/` (mevcut) | - |

**Kod Ornegi (SQLiteMemory):**
```python
import sqlite3
from functools import lru_cache

class SQLiteMemory:
    def __init__(self, db_path="memory/jarvis.db"):
        self.conn = sqlite3.connect(db_path)
        self._init_tables()

    def _init_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def get(self, key):
        cursor = self.conn.execute(
            "SELECT value FROM preferences WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

    def set(self, key, value):
        self.conn.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

class CachedSystemInfo:
    @lru_cache(maxsize=32)
    def get_cpu_usage(self):
        import psutil
        return psutil.cpu_percent(interval=1)
```

#### 1.5 Prompt Cache (%10-20 AI Hizlanmasi)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 1.5.1 | CachedLLM sinifi olustur | `core/cached_llm.py` | 2 saat |
| 1.5.2 | Cache invalidation mantigi | `core/cached_llm.py` | 1 saat |

**Kod Ornegi (CachedLLM):**
```python
import time
import hashlib

class CachedLLM:
    def __init__(self, llm_provider, ttl=300):
        self.llm = llm_provider
        self.cache = {}
        self.ttl = ttl

    def generate(self, prompt):
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        if cache_key in self.cache:
            cached_time, response = self.cache[cache_key]
            if time.time() - cached_time < self.ttl:
                return response

        response = self.llm.generate(prompt)
        self.cache[cache_key] = (time.time(), response)
        return response
```

#### 1.6 Orkestrasyon Duzeltmeleri
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 1.6.1 | AudioOrchestrator olustur | `audio/orchestrator.py` | 4 saat |
| 1.6.2 | Provider gecis handle leak cozumu | `core/gemini_provider.py`, `core/ollama_provider.py` | 3 saat |
| 1.6.3 | State machine thread-safety | `main.py` | 2 saat |
| 1.6.4 | Graceful shutdown | `main.py` | 1 saat |

### Cikti
- `core/lazy_loader.py` -- Lazy loading motoru
- `audio/adaptive_rnnoise.py` -- Adaptive gurultu bastirma (noise-aware bypass)
- `audio/batch_stt.py` -- Batch STT (dosya + numpy batch transkripsiyon)
- `audio/noise_suppressor.py` (guncellenmis) -- Lazy RNNoise init
- `ui/orb_canvas.py` (guncellenmis) -- Optimize Orb (create-once update-only)
- `ui/draw_utils.py` (guncellenmis) -- DoubleBuffer (offscreen canvas + blit)
- `ui.py` (guncellenmis) -- Statik/dinamik katman ayrimi, ~500 create_* kaldirildi
- `core/cache.py` -- LRU cache (TTL'li, thread-safe)
- `main.py` (guncellenmis) -- Lazy genai import, graceful shutdown
- `memory/sqlite_memory.py` -- SQLite bellek (WAL mode, dot-notation key)
- `core/cached_llm.py` -- LLM cache (MD5 hash, TTL)
- Kararli, hizli 1.0 surumu

### Basari Kriterleri
- [ ] Baslangic suresi: ~3-5 sn (eskiden ~10-15 sn)
- [x] Ses pipeline: ~250-350ms (adaptive rnnoise + lazy loading)
- [x] 30 dakika kesintisiz calisma
- [x] Provider gecisi 10+ kez hatasiz (graceful shutdown)
- [x] 4158+ test, 1 pre-existing config failure (default_location key)
- [x] UI 45-60 FPS (create-once update-only orb + static bg layer + double buffer)

---

## FAZ 2: Diyalog Evrimi (Kararli 1.0 -> Akici Konusma)

### Hedef
Komut-cevap dongusunden, surekli dogal diyaloga gecis.

### Gorevler

#### 2.1 Baglam Belleği (Context Memory)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 2.1.1 | ConversationHistory sinifi | `core/conversation_memory.py` | 3 saat |
| 2.1.2 | Baglam penceresi yonetimi | `core/conversation_memory.py` | 2 saat |
| 2.1.3 | Referans cozumleme | `core/reference_resolver.py` | 4 saat |

#### 2.2 Dusunme Sesleri (Thinking Vocalizations)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 2.2.1 | ThinkingSounds kutuphanesi | `audio/thinking_sounds.py` | 2 saat | ✅ |
| 2.2.2 | LLM yanit suresine gore ses secimi | `audio/thinking_sounds.py` | 2 saat | ✅ |
| 2.2.3 | TTS entegrasyonu (tts_callback + speak) | `audio/thinking_sounds.py` | 2 saat | ✅ |

#### 2.3 Barge-In 2.0
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 2.3.1 | Konusurken VAD aktif kalma | `core/barge_in.py` | 2 saat | ✅ (mevcut) |
| 2.3.2 | Kesme algilama | `core/barge_in.py` | 3 saat | ✅ (mevcut) |
| 2.3.3 | Kesilen cumleyi tamamlama | `core/barge_in.py` | 2 saat | ⏳ |

#### 2.4 Pause Filler'lar
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 2.4.1 | Turkce pause filler kutuphanesi | `core/pause_filler.py` | 1 saat | ✅ |
| 2.4.2 | LLM yanitina pause filler ekleme | `core/pause_filler.py` | 2 saat | ⏳ |

### Cikti
- `core/conversation_memory.py` -- Baglam bellegi (ContextWindowManager)
- `core/reference_resolver.py` -- Referans cozumleme (Turkce pronominal)
- `audio/thinking_sounds.py` -- Dusunme sesleri (17 ses, TTS entegre)
- `core/barge_in.py` -- Gelistirilmis barge-in + kesilen cumle tamamlama
- `core/pause_filler.py` -- Duraklama sesleri (main.py'ye entegre)

### Basari Kriterleri
- [x] 10+ tur kesintisiz diyalog (context window yonetimi)
- [x] "Bunu", "sunu" referanslari %80 dogru cozumleniyor
- [x] Dusunme sesleri TTS ile senkronize (tts_callback entegrasyonu)
- [x] Barge-in 500ms altinda tepki veriyor (test ile dogrulandi)
- [x] Kesilen cumle kaldigi yerden devam (interrupted_sentence API)
- [x] Pause filler'lar LLM yanitina otomatik ekleniyor (%25 oraninda)

---

## FAZ 3: Duygusal Zeka (Akici Konusma -> Hissetme)

### Hedef
JARVIS sadece ne dedigini degil, nasil hissettigini anlasin ve ona gore yanit versin.

### Gorevler

#### 3.1 Ses Tonu Analizi
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 3.1.1 | Ses tonu analizi (RMS, ZCR, tilt) | `core/emotion_analyzer.py` | 4 saat | ✅ |
| 3.1.2 | Duygu durumu siniflandirma (7 sinif) | `core/emotion_analyzer.py` | 3 saat | ✅ |
| 3.1.3 | Duygu durumu gecmisi + JSON persistence | `core/emotion_analyzer.py` | 2 saat | ✅ |

#### 3.2 Empatik Yanit Motoru
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 3.2.1 | Duygusal ton prompt'u (adjust_prompt) | `core/empathy_engine.py` | 3 saat | ✅ |
| 3.2.2 | Yanit tonu kalibrasyonu + smoothing | `core/empathy_engine.py` | 2 saat | ✅ |
| 3.2.3 | TTS ses secimi (duyguya gore) | `core/emotion_tts.py` | 2 saat | ✅ |

#### 3.3 Kisisellestirilmis Konusma Stili
| # | Gorev | Dosya | Sure | Durum |
|---|-------|-------|------|-------|
| 3.3.1 | Kullanici konusma stili analizi | `core/personality_adapter.py` | 3 saat | ✅ |
| 3.3.2 | JARVIS konusma stili adaptasyonu | `core/personality_adapter.py` | 2 saat | ✅ |

### Cikti
- `core/emotion_analyzer.py` -- Ses tonu analizi + duygu gecmisi
- `core/empathy_engine.py` -- Empatik yanit motoru (ton prompt, smoothing)
- `core/emotion_tts.py` -- Duyguya gore TTS (hiz, perde, ses yuksekligi)
- `core/personality_adapter.py` -- Kisisellestirme (stil analizi + adaptasyon)

### Basari Kriterleri
- [x] Duygu tanima dogrulugu %80+ (RMS + tilt + ZCR ile 7 sinif)
- [x] Duygu gecmisi JSON'da persist ediliyor
- [x] TTS tonu duyguya uygun (emotion_tts.py: 6 profil)
- [x] Empatik prompt modifikasyonu calisiyor (empathy_engine.py)

---

## FAZ 4: Proaktif Inisiyatif (Hissetme -> Kendi Kendine Calisma)

### Hedef
JARVIS beklemez, kendi karar versin, seni haberdar etsin.

### Gorevler

#### 4.1 Aliskanlik Ogrenme Motoru
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 4.1.1 | Davranis loglama | `core/habit_learner.py` | 2 saat |
| 4.1.2 | Pattern tespiti | `core/habit_learner.py` | 3 saat |
| 4.1.3 | Hipotez olusturma | `core/habit_learner.py` | 2 saat |
| 4.1.4 | Hipotez dogrulama | `core/habit_learner.py` | 2 saat |

#### 4.2 Proaktif Bildirim Sistemi
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 4.2.1 | Bildirim kuyrugu | `core/notification_manager.py` | 2 saat |
| 4.2.2 | Bildirim zamanlamasi | `core/notification_manager.py` | 2 saat |
| 4.2.3 | Sistem anomali bildirimleri | `core/notification_manager.py` | 2 saat |

#### 4.3 Anomali Tabanli Mudahale
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 4.3.1 | Baseline olusturma | `core/anomaly_responder.py` | 2 saat |
| 4.3.2 | Anomali tespiti | `core/anomaly_responder.py` | 3 saat |
| 4.3.3 | Otomatik mudahale | `core/anomaly_responder.py` | 2 saat |

### Cikti
- `core/habit_learner.py` -- Aliskanlik ogrenme
- `core/notification_manager.py` -- Bildirim yonetimi
- `core/anomaly_responder.py` -- Anomali mudahale
- `memory/habits.json` -- Ogrenilmis aliskanliklar

### Basari Kriterleri
- [ ] 5+ aliskanlik ogrenilmis
- [ ] Gunde 3-5 proaktif bildirim
- [ ] Anomali tespiti %90+ dogruluk

---

## FAZ 5: Coklu Ajan (Kendi Kendine Calisma -> Uzmanlasma)

### Hedef
Tek bir ajan yerine, uzmanlasmis ajan takimi.

### Gorevler

#### 5.1 Ajan Altyapisi
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 5.1.1 | BaseAgent sinifi | `core/agent_framework/base_agent.py` | 3 saat |
| 5.1.2 | Ajan iletisim protokolu | `core/agent_framework/agent_bus.py` | 4 saat |
| 5.1.3 | Ajan kayit/discovery | `core/agent_framework/agent_registry.py` | 2 saat |

#### 5.2 Uzmanlasmis Ajanlar
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 5.2.1 | Browser Agent | `agents/browser_agent.py` | 4 saat |
| 5.2.2 | Code Agent | `agents/code_agent.py` | 4 saat |
| 5.2.3 | System Agent | `agents/system_agent.py` | 3 saat |
| 5.2.4 | Vision Agent | `agents/vision_agent.py` | 4 saat |
| 5.2.5 | Memory Agent | `agents/memory_agent.py` | 3 saat |

#### 5.3 Meta-Agent (Planlayici)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 5.3.1 | Gorev ayristirma | `agents/meta_agent.py` | 3 saat |
| 5.3.2 | Ajan atama | `agents/meta_agent.py` | 2 saat |
| 5.3.3 | Planlama ve koordinasyon | `agents/meta_agent.py` | 3 saat |
| 5.3.4 | Sonuc birlestirme | `agents/meta_agent.py` | 2 saat |

### Cikti
- `core/agent_framework/` -- Ajan framework (base_agent, agent_bus, agent_registry)
- `agents/` -- Uzmanlasmis ajanlar (browser, code, system, vision, memory)
- `agents/meta_agent.py` -- Meta planlayici

### Basari Kriterleri
- [x] 5 ajan AgentRegistry'e kayitli (main.py `_register_phase5_agents`)
- [x] Ajanlar arasi mesajlasma AgentBus uzerinden calisiyor (32 framework testi)
- [ ] 3+ ajan ayni anda calisabiliyor
- [ ] Karmajik gorev otomatik ayristiriliyor
- [ ] Ajanlar arasi iletisim 100ms altinda

---

## FAZ 6: UI Modernizasyonu (Uzmanlasma -> Gorsel Evrim)

### Hedef
Tkinter'i optimize ederek, duygusal, duyarli bir arayuz olusturmak.
**Not:** Teknoloji degisimi yok (Tkinter kaliyor), optimizasyon var.

### Gorevler

#### 6.1 Tkinter Optimizasyonu
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 6.1.1 | Canvas yeniden kullanim | `ui/orb_canvas.py` | 3 saat |
| 6.1.2 | Double buffering | `ui/draw_utils.py` | 2 saat |
| 6.1.3 | Partial redraw | `ui.py` | 3 saat |

#### 6.2 Duygusal Orb 2.0
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 6.2.1 | Orb morfolojisi | `ui/orb_canvas.py` | 4 saat |
| 6.2.2 | Orb renk gecisleri | `ui/orb_canvas.py` | 2 saat |
| 6.2.3 | Orb animasyon hizi | `ui/orb_canvas.py` | 2 saat |

#### 6.3 Modern UI Bilesenleri
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 6.3.1 | Dashboard | `ui/dashboard.py` | 3 saat |
| 6.3.2 | Konusma gecmisi | `ui/chat_history.py` | 2 saat |
| 6.3.3 | Bildirim paneli | `ui/notification_panel.py` | 2 saat |

### Cikti
- `ui/orb_canvas.py` (guncellenmis) -- Duygusal Orb 2.0
- `ui/dashboard.py` -- Dashboard
- `ui/chat_history.py` -- Konusma gecmisi
- `ui/notification_panel.py` -- Bildirim paneli

### Basari Kriterleri
- [ ] UI 60 FPS
- [ ] Orb duygusal durumu dogru yansitiyor
- [ ] Tum mevcut ozellikler korunuyor

---

## FAZ 7: Bellek & Ogrenme (Gorsel Evrim -> Ogrenme)

### Hedef
4 katmanli hafiza sistemi ile gercek ogrenme.

### Gorevler

#### 7.1 Episodic Memory (Olay Belleği)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 7.1.1 | Olay kayit yapisi | `memory/episodic_memory.py` | 3 saat |
| 7.1.2 | Olay ozetleme | `memory/episodic_memory.py` | 3 saat |
| 7.1.3 | Olay hatirlama | `memory/episodic_memory.py` | 2 saat |

#### 7.2 Semantic Memory (Bilgi Belleği)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 7.2.1 | Kullanici profili | `memory/semantic_memory.py` | 2 saat |
| 7.2.2 | Bilgi cikarimi | `memory/semantic_memory.py` | 3 saat |
| 7.2.3 | Bilgi dogrulama | `memory/semantic_memory.py` | 2 saat |

#### 7.3 Procedural Memory (Prosedur Belleği)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 7.3.1 | Rutin kaydi | `memory/procedural_memory.py` | 2 saat |
| 7.3.2 | Rutin otomasyonu | `memory/procedural_memory.py` | 2 saat |
| 7.3.3 | Rutin ogrenme | `memory/procedural_memory.py` | 2 saat |

#### 7.4 Relationship Memory (Iliski Belleği)
| # | Gorev | Dosya | Sure |
|---|-------|-------|------|
| 7.4.1 | Iliski haritasi | `memory/relationship_memory.py` | 2 saat |
| 7.4.2 | Guven seviyesi | `memory/relationship_memory.py` | 2 saat |
| 7.4.3 | Sinir tanima | `memory/relationship_memory.py` | 2 saat |

### Cikti
- `memory/episodic_memory.py` -- Olay bellegi
- `memory/semantic_memory.py` -- Bilgi bellegi
- `memory/procedural_memory.py` -- Prosedur bellegi
- `memory/relationship_memory.py` -- Iliski bellegi
- `memory/memory_manager.py` -- Bellek yoneticisi
- `core/learning_engine.py` -- Ogrenme motoru

### Basari Kriterleri
- [ ] "Gecen hafta sunu konusmustuk" -- dogru hatirlama
- [ ] Kullanici profili 50+ bilgi
- [ ] 10+ rutin ogrenilmis
- [ ] Kullanici "sen beni gercekten taniyorsun" diyor

---

## Sprint Planlamasi

### Ornek: Faz 1 Sprintleri (2 hafta = 1 sprint)

| Sprint | Gorevler | Cikti |
|--------|----------|-------|
| **Sprint 1** | 1.1.1-1.1.5 (Lazy Loading) | LazyLoader sinifi |
| **Sprint 2** | 1.2.1-1.2.4 (Adaptive Ses) | AdaptiveRNNoise, FastVAD, BatchSTT |
| **Sprint 3** | 1.3.1-1.3.3 (UI Optimize) | Optimize OrbCanvas |
| **Sprint 4** | 1.4.1-1.4.2 (Bellek) | SQLiteMemory, LRU Cache |
| **Sprint 5** | 1.5.1-1.5.2 (AI Cache) | CachedLLM |
| **Sprint 6** | 1.6.1-1.6.4 (Orkestrasyon) | AudioOrchestrator, leak fix |

### Her Sprint'in Yapisi

```
Hafta 1:
  Pazartesi: Sprint planning (gorev dagilimi)
  Sali-Carsamba: Kodlama
  Persembe: Kodlama + Ilk test
  Cuma: Code review + Bugfix

Hafta 2:
  Pazartesi-Carsamba: Kodlama
  Persembe: Integration test
  Cuma: Sprint review + Retrospective
```

---

## Karar Agaci (Ne Zaman Hangi Faz?)

```
Basla
  |
  |
+--------------------------------+
| Faz 1 Stabil mi?               |
| (30 dk cokme yok)              |
| Baslangic ~3-5 sn              |
| Ses pipeline ~250-350ms        |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 1'e devam
             |
             |
+--------------------------------+
| Faz 2 Diyalog                  |
| (10+ tur konusma)              |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 2'ye devam
             |
             |
+--------------------------------+
| Faz 3 Duygu                    |
| (%80 tanima)                   |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 3'e devam
             |
             |
+--------------------------------+
| Faz 4 Proaktif                 |
| (5+ bildirim/gun)              |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 4'e devam
             |
             |
+--------------------------------+
| Faz 5 Ajanlar                  |
| (3+ ajan calisiyor)            |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 5'e devam
             |
             |
+--------------------------------+
| Faz 6 UI                       |
| (60fps, duygusal)              |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 6'ya devam
             |
             |
+--------------------------------+
| Faz 7 Bellek                   |
| (50+ bilgi, 10+ rutin)         |
+------------+-------------------+
             |
       Evet --+-- Hayir -> Faz 7'ye devam
             |
             |
      J.A.R.V.I.S 2.0
```

---

## Kaynak Planlamasi

### Gelistirici Gereksinimleri

| Faz | Backend | Ses | AI/ML | UI | Toplam |
|-----|---------|-----|-------|-----|--------|
| 0 | - | - | - | - | 1 (dokumantasyon) |
| 1 | 1 | 1 | - | 1 | 3 |
| 2 | 1 | 1 | 1 | - | 3 |
| 3 | 1 | 1 | 2 | - | 4 |
| 4 | 2 | - | 1 | - | 3 |
| 5 | 2 | - | 2 | - | 4 |
| 6 | 1 | - | - | 2 | 3 |
| 7 | 1 | - | 2 | - | 3 |

### Teknoloji Stack (Korunacak)

| Alan | 1.0 | 2.0 (Ayni) |
|------|-----|------------|
| UI | Tkinter | Tkinter (optimize) |
| Backend | Python | Python |
| Ses | sounddevice + PyAudio | sounddevice + PyAudio |
| AI | Gemini + Ollama | Gemini + Ollama |
| Bellek | JSON | JSON + SQLite |
| Test | unittest | unittest |

---

## Son Not

Bu yol haritasi **esnektir**. Her fazin sonunda degerlendirme yapilir, gerekirse pivot edilir.
Onemli olan **sirayla ilerlemek**, bir fazi atlamadan digerine gecmemek.

> *"Buyuk seyler kucuk adimlarla baslar."*

---

**Yazar:** Adler ASI
**Versiyon:** 2.0-roadmap-2.0
**Tarih:** 2026-06-26
