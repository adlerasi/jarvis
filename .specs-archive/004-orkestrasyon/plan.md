# Implementation Plan: Orkestrasyon Onarımı

**Branch**: `` | **Date**: 2026-06-11 | **Spec**: specs/004-orkestrasyon/spec.md

**Input**: Feature specification from `/specs/004-orkestrasyon/spec.md`

---

## Summary

JARVIS sesli asistanın üç katmanında (orkestrasyon, ses pipeline, chat/provider) tespit edilen **17 yapısal sorun** kataloglanmış ve 4 faza bölünmüştür. Kritik thread güvenliği sorunları, kullanılmayan/kullanılamayan modüller (RNNoise, VAD, çift STT), tutarsız provider arayüzü, ve düşük öncelikli sağlamlık iyileştirmeleri.

Onarım stratejisi: her sorunu en küçük değişiklikle düzelt, mevcut testlerin hepsinin geçtiğini doğrula, sonra bir sonraki soruna geç.

---

## Technical Context

**Language/Version**: Python 3.10+ (3.13 kullanılıyor)

**Primary Dependencies**:
- PyAudio (ses yakalama/oynatma)
- faster-whisper (STT, yerel)
- google-genai (Gemini Live API)
- httpx (Ollama HTTP istemcisi)
- numpy/scipy (ses işleme)
- Tkinter (UI)

**Storage**: JSON-backed key-value store (memory/), dosya sistemi (logs/)

**Testing**: unittest framework, runner: `.venv/bin/python3 -m unittest discover tests -v`
Mevcut: **2803 pass, 2 skip, 0 fail**

**Target Platform**: Windows 10/11 (birincil), Linux (test: Ubuntu 24+), macOS (ikincil)

**Project Type**: Desktop sesli asistan uygulaması (Tkinter UI + asyncio event loop)

**Performance Goals**:
- Ses pipeline (STT → AI → TTS) < 3sn
- UI state güncellemeleri < 100ms
- Config disk I/O: sadece değişiklikte, her frame'de değil

**Constraints**:
- Tkinter thread-safe DEĞİL — tüm UI çağrıları main thread'den
- PyAudio ALSA/PulseAudio lock — stream tek thread'den okunmalı
- Provider değişimi tüm kaynakların sıralı temizlenmesini gerektirir
- Tüm `except` blokları `traceback.print_exc()` çağırmalı (constitution)
- "Mock test placeholder yasak" — gerçek implementasyon

**Scale/Scope**: Tek geliştirici, tek makine, tek kullanıcılı asistan

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article VII — Simplicity Gate
- [x] ≤3 proje? → Evet, tek proje (monolitik), yeni paket eklenmiyor
- [x] Gelecek için kod yazılmıyor? → Sadece mevcut hatalar düzeltiliyor

### Article VIII — Anti-Abstraction Gate
- [x] Framework doğrudan kullanılıyor? → Evet, Tkinter/PyAudio/httpx direkt
- [x] Tek kaynak model? → Mevcut yapı korunuyor

### Article IX — Integration-First Gate
- [ ] Contracts defined? → Provider arayüzü değişiyor, contract olarak `send_text`/`send_audio` standardizasyonu research.md'de ele alınacak
- [ ] Contract tests written? → Henüz değil, Faz 1'de yazılacak

### Article X — Requirements-First Gate
- [x] WHAT/WHY net? → 17 sorun tespit edildi, her biri için kök neden biliniyor
- [x] Mevcut hatalar düzeltiliyor, yeni özellik eklenmiyor

### Pre-Merge Checklist
- [ ] `lsp_diagnostics` clean on changed files
- [ ] `.venv/bin/python3 -m unittest discover tests -v` — all pass
- [ ] No dead code, no placeholder/mock tests
- [ ] API keys never committed

---

## Complexity Tracking

> Constitution Article VI (Standalone Library First) bu feature için geçerli değil — mevcut kod onarımı, yeni özellik değil.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Art. VI bypass | Mevcut kod onarımı, yeni paket değil | Yeni paket mevcut import bağımlılıklarını kırar |

---

## 1. Arkaplan ve Metodoloji

### Kapsam
Bu doküman, JARVIS sesli asistan uygulamasının aşağıdaki üç ana katmanında tespit edilen tüm orkestrasyon sorunlarını kataloglamakta ve onarım planını sunmaktadır:

- **Orkestrasyon**: Provider yaşam döngüsü, backend geçişleri, modül başlatma sırası, kaynak yönetimi
- **Sesli Asistan**: STT pipeline, VAD yönetimi, mikrofon paylaşımı, ses seviyesi yönetimi
- **Chat/Provider**: Provider arayüzü, mesaj yönlendirme, event loop kullanımı, hata yönetimi

### Tarama Yöntemi
- Tüm `core/` dosyaları (26 Python dosyası) satır satır incelendi
- `main.py` (1107 satır) tüm orkestrasyon mantığı analiz edildi
- `actions/tts.py`, `audio/`, `core/audio_system/` ses pipeline'ı incelendi
- `core/agent/` ACA alt sistemi tarandı (önceki spekle ilgili)
- Test dosyaları (`tests/`) uyumluluk açısından kontrol edildi

### Toplam Tespit: **17 ayrı sorun** (8 kritik, 5 yüksek, 3 orta, 1 düşük)

---

## 2. Orkestrasyon Katmanı — Problem Kataloğu

### P-01 [KRİTİK] Çift STT Pipeline Çalışıyor (Gemini Modu)

**Dosya**: `main.py:294-301` + `core/gemini_provider.py:164-197`
**Tür**: Kaynak israfı + potansiyel çakışma

**Tanım**:
`_asimilasyon_init()` içinde `streaming_stt_engine` başlatılır (`core/streaming_stt.py`). Bu engine, Gemini provider'ın `_listen_audio()` metodunda `feed_audio()` ile beslenir. Sonuç: **İki STT aynı anda çalışır**:
1. StreamingSTT (yerel faster-whisper, CPU'da transkripsiyon yapar)
2. Gemini API (sunucu tarafında transkripsiyon yapar, `input_transcription` olarak döner)

**Kök Neden**:
- StreamingSTT, Gemini modu için tasarlanmamıştır (Gemini kendi transkripsiyonunu yapar)
- `_asimilasyon_init()` tüm modülleri "her ihtimale karşı" başlatır, provider tipine bakmaz

**Etki**:
- CPU/GPU'da gereksiz faster-whisper yükü (~1-2GB RAM, sürekli CPU kullanımı)
- StreamingSTT'nin `_on_stt_text()` callback'i Gemini'de işe yaramaz çünkü `input_queue` kullanılmaz

**Çözüm**:
- StreamingSTT yalnızca Ollama modunda başlatılmalı
- VEYA Gemini modunda streaming_stt_engine başlatılmamalı / feed_audio çağrılmamalı

---

### P-02 [KRİTİK] Çift VAD Instance (Biri Hiç Kullanılmıyor)

**Dosya**: `main.py:277-292` + `core/ollama_provider.py:464-481`
**Tür**: Kaynak israfı + yanıltıcı kod

**Tanım**:
İki ayrı VAD instance'ı oluşturulur:
1. `main.py`'de `self.vad_engine = create_vad_engine(...)` — `_asimilasyon_init()` içinde
2. `ollama_provider.py`'de `self._fahrettin_vad = FahrettinVAD(...)` — `_stt_listen_loop()` içinde

main.py'deki `vad_engine` HIÇBIR YERDE `feed_audio()` ile beslenmez. Callback'leri (`_on_vad_speech_start`, `_on_vad_speech_end`) asla tetiklenmez.

**Kök Neden**:
- VAD engine başlangıçta eklenmiş ancak audio pipeline'ına bağlanmamış
- Ollama provider kendi VAD'ını oluşturmuş (FahrettinVAD wrapper'ı ile)
- İki implementasyon arasında iletişim/kordinasyon yok

**Etki**:
- Bellek israfı (gereksiz VADEngine objesi)
- VAD callback'leri (`_on_vad_speech_start/end`) hiç çalışmaz
- `[VAD] Konusma basladi/sona erdi` logları asla görünmez

**Çözüm**:
- main.py'deki `vad_engine` kaldırılmalı veya FahrettinVAD'a yönlendirilmeli
- VAD lifecycle'ı sadece provider içinde yönetilmeli

---

### P-03 [YÜKSEK] StreamingSTT Callback'i Yanlış Provider'a Yönleniyor

**Dosya**: `main.py:365-387`
**Tür**: Veri kaybı / yanlış yönlendirme

**Tanım**:
`_on_stt_text()` callback'i şunu yapar:
```python
if self._provider is not None and hasattr(self._provider, 'input_queue'):
    self._provider.input_queue.put_nowait(text)
```
Bu sadece Ollama provider (`input_queue` attribute'u olan) için çalışır. Gemini provider'da `input_queue` yoktur — `send_text()` metodu vardır.

**Kök Neden**:
- Kod, her provider'ın aynı arayüzü kullandığını varsayar
- Gemini `send_text(text)` kullanır, Ollama `input_queue.put_nowait(text)` kullanır
- ProviderBase'de `send_text` abstract method olarak tanımlıdır (provider_base.py:73)

**Etki**:
- Gemini modunda StreamingSTT transkripsiyonları sessizce kaybolur
- Kullanıcı sadece Gemini API'sinin kendi transkripsiyonunu alır (bu zaten çalışır, ama StreamingSTT boşuna kaynak tüketir)

**Çözüm**:
- `_on_stt_text()` generic `send_text()` çağırmalı (provider_base'de tanımlı)
- `GeminiProvider.send_text()` zaten doğru çalışıyor
- Ollama için `send_text()` de `input_queue.put_nowait(text)` yapmalı

---

### P-04 [YÜKSEK] Provider Backend Geçişi Race Condition

**Dosya**: `main.py:606-650`
**Tür**: Race condition / kaynak sızıntısı

**Tanım**:
`run()` metodu her çevrimde config'den `backend_type` okur ve yeni provider oluşturur. Eski provider'ın `stop()` metodu çağrılır, ancak:
- Gemini provider'ın TaskGroup'u (`asyncio.TaskGroup`) iptal edilirken içindeki task'lerin tamamlanması beklenmez
- Ollama provider'ın `_stt_listen_loop` task'i cancel edilir ama PyAudio stream'i hemen kapanmaz
- Yeni provider oluşturulurken eski provider'ın kaynakları (PyAudio, HTTP client) hâlâ serbest bırakılıyor olabilir

**Kök Neden**:
- Provider geçişi sırasında graceful shutdown yok
- `TaskGroup` __aexit__'i tüm task'leri iptal eder ama kaynakların sıralı temizlenmesini garanti etmez
- `finally: await provider.stop()` çalışır ama bu sırada yeni provider zaten `run_loop()`'a başlamış olabilir

**Etki**:
- Geçiş sırasında "Input overflowed" veya "Device busy" hataları
- Nadiren de olsa PyAudio cihaz kitlenmesi (requires restart)
- Ses kaybı (1-3 saniye)

**Çözüm**:
- Provider değişiminde önce `stop()` tamamlanmalı, SONRA yeni provider start edilmeli
- `_shutdown_event` benzeri bir mekanizma ile senkronizasyon

---

### P-05 [ORTA] Config Diskten Her Loop Çevriminde Okunuyor

**Dosya**: `core/ollama_provider.py:494` + `core/ollama_provider.py:206`
**Tür**: Performans

**Tanım**:
Ollama provider'ın `_stt_listen_loop()`'unda HER SES FRAMINDE (`while self._running` içinde her `stream.read`'de):
```python
cfg = _load_app_config()
```
Bu, her ~30ms'de bir JSON/YAML dosyasını diskten okumak anlamına gelir (~33 kere/saniye).

Aynı şekilde `run_loop()`'unda da her mesajda diskten okunur (daha seyrek ama gereksiz).

**Kök Neden**:
- Config'in değişebileceği endişesiyle her seferinde yeniden okunuyor
- Cache mekanizması yok

**Etki**:
- Gereksiz disk I/O (~30MB/saniye okuma)
- UI backend değiştirildiğinde zaten yeni provider oluşuyor, bu nedenle anlık config okumaya gerek yok

**Çözüm**:
- Config'i provider başlangıcında bir kere oku, cache'le
- Sadece `on_config_change` callback'i ile güncelle

---

## 3. Sesli Asistan (Audio Pipeline) — Problem Kataloğu

### P-06 [KRİTİK] RNNoise Hiçbir Provider'da Kullanılmıyor

**Dosya**: `core/ollama_provider.py:35-39` (import ediliyor ama kullanılmıyor) + `core/gemini_provider.py` (hiç import edilmiyor)
**Tür**: Eksik özellik / gürültü sorunu

**Tanım**:
RNNoise kütüphanesi başarıyla import edilse bile (`_HAS_RNNOISE = True`), OLLAMA provider'ın `_stt_listen_loop()`'unda gürültü bastırma UYGULANMAZ. Gemini provider'da ise RNNoise hiç import edilmez.

Kullanıcının "dinlemiyor" şikayetinin sebeplerinden biri de gürültülü ortamda VAD/STT'nin çalışamaması olabilir.

**Kök Neden**:
- `audio/noise_suppressor.py` var ve çalışıyor (test edildi)
- RNNoise daha önce main.py'de kullanılıyordu, provider'lara taşınırken unutuldu
- Ollama provider'da import var ama uygulama kodu yok

**Etki**:
- Gürültülü ortamlarda VAD gürültüyü konuşma sanıp tetiklenir (veya tersi)
- STT kalitesi düşer (faster-whisper gürültülü kayıtta hatalı transkripsiyon yapar)
- Kullanıcı "dinlemiyor" veya "yanlış anlıyor" şikayeti yapar

**Çözüm**:
- Ollama provider'da RNNoise uygula: `stream.read()` sonrası → `noise_suppressor.process()` → VAD
- Gemini provider'da da isteğe bağlı RNNoise ekle

---

### P-07 [YÜKSEK] Gemini Modunda VAD Yok (Sadece Amplitude Gate)

**Dosya**: `core/gemini_provider.py:164-197`
**Tür**: Eksik özellik

**Tanım**:
Gemini provider'ın `_listen_audio()`'su sesi doğrudan API'ya iletir. Herhangi bir VAD uygulanmaz. Sadece `_is_speaking`, `muted`, `_paused` kontrolleri vardır (amplitude gate bile yok).

Bu, Gemini'nin kendi sunucu-tarafı VAD'ına güvenildiği anlamına gelir. Ancak:
- Wake word desteği yok (ses her zaman API'ya gider)
- Gereksiz bant genişliği tüketimi
- Gemini API kotaları gereksiz yere harcanır

**Kök Neden**:
- Gemini Live API zaten kendi VAD'ını yapar ama bu sunucu-tarafındadır
- Müşteri-tarafı VAD eklenmemiş

**Etki**:
- Sürekli ses akışı → API maliyeti artar
- Wake word olmadan her ses API'ya gider
- Sessizlik anlarında bile veri gönderilir

**Çözüm**:
- Gemini provider'a opsiyonel VAD ekle (config ile açılıp kapanabilir)
- VAD yokken sessizlikte gönderimi durdur (energy threshold)

---

### P-08 [ORTA] Ollama STT Loop — PyAudio Resource Leak Riski

**Dosya**: `core/ollama_provider.py:438-461, 625-632`
**Tür**: Kaynak yönetimi

**Tanım**:
PyAudio stream ve `pyaudio.PyAudio()` instance'ının temizlenmesi `try/finally` bloğunda yapılır. Ancak:
- Eğer `self._stt_task.cancel()` sonrası task hemen bitmezse (`except asyncio.CancelledError`), stream kapanmaz
- Eğer `_stt_listen_loop` dışarıdan cancel edilirse (provider değişimi), `finally` bloğu çalışmayabilir
- Stream açma başarısız olursa (tüm rate'ler denenir), sadece `p.terminate()` çağrılır — bu yeterli olabilir

**Kök Neden**:
- asyncio task cancellation ile PyAudio kaynak yönetimi arasında uyumsuzluk
- PyAudio'nun `__del__` metoduna güvenilmekte (çalışması garanti değil)

**Etki**:
- "PortAudio device locked" hatası (Linux ALSA'da sık)
- Mikrofonun diğer uygulamalar tarafından kullanılamaması
- "Input overflowed" uyarıları

**Çözüm**:
- Context manager (`with`) kullan
- `atexit` handler ekle
- `_cleanup_audio()` yardımcı metodu oluştur

---

## 4. Chat / Provider Katmanı — Problem Kataloğu

### P-09 [KRİTİK] Provider Arayüzü Tutarsız: Ollama input_queue, Gemini send_text

**Dosya**: `core/provider_base.py:73` + `core/ollama_provider.py:160` + `core/gemini_provider.py:108`
**Tür**: Tasarım/Tutarsızlık

**Tanım**:
`BaseProvider` soyut sınıfı `send_text` abstract methodu tanımlar:
```python
async def send_text(self, text: str) -> None:
    ...
```

GeminiProvider bunu uygular:
```python
async def send_text(self, text: str) -> None:
    await self.session.send_client_content(...)
```

OllamaProvider bunu uygular:
```python
async def send_text(self, text: str) -> None:
    await self.input_queue.put(text)
```

Ancak `_on_stt_text()` ve `_on_text_command()` doğrudan `send_text()` çağırmaz:
```python
# _on_stt_text
self._provider.input_queue.put_nowait(text)  # Yanlış! send_text kullanılmalı

# _on_text_command
await self._provider.send_text(text)  # Doğru!
```

**Kök Neden**:
- Kod evrimi sırasında provider arayüzü düzgün soyutlanmamış
- `_on_stt_text()` eski pattern'i kullanıyor (doğrudan queue erişimi)

**Etki**:
- `_on_stt_text` Gemini modunda sessizce başarısız olur (queue yoksa exception fırlatır)
- Provider değişikliklerinde kodun birden fazla yerde güncellenmesi gerekir

**Çözüm**:
- Tüm metin girişi `send_text()` üzerinden yapılmalı
- `input_queue.put_nowait` kaldırılmalı

---

### P-10 [YÜKSEK] Provider'ın send_audio Metodu Gemini'a Özel, Ollama Yok

**Dosya**: `core/provider_base.py` (tanımlı değil), `core/gemini_provider.py:102`, `core/ollama_provider.py` (yok)
**Tür**: Eksik soyutlama

**Tanım**:
`BaseProvider`'da `send_audio` tanımlı değil. GeminiProvider'da var:
```python
async def send_audio(self, data: bytes) -> None:
    q = self.out_queue
    if q is not None:
        await q.put({"data": data, "mime_type": "audio/pcm"})
```

OllamaProvider'da bu metod yok. Kimse `send_audio` çağırmıyor (çünkü Gemini kendi `_listen_audio`'sunda doğrudan `out_queue`'ya yazıyor).

**Kök Neden**:
- Ses akışı provider'ın içinde yönetiliyor (listen_audio metodu)
- Dışarıdan ses besleme arayüzü eksik (ileride streaming_stt'den besleme için gerekli olabilir)

**Etki**:
- Şu an için sorun yok (ses dahili olarak yönetiliyor)
- Gelecekte ortak ses pipeline'ı kurmak zorlaşır

**Çözüm**:
- `BaseProvider`'a opsiyonel `send_audio` ekle
- Her iki provider da implemente etsin (Ollama'da no-op olabilir)

---

### P-11 [YÜKSEK] Ollama run_loop ve _stt_listen_loop Task Yönetimi Zayıf

**Dosya**: `core/ollama_provider.py:166-174`
**Tür**: Kararlılık

**Tanım**:
```python
async def run_loop(self):
    # STT listener
    if self._stt_task is None or self._stt_task.done():
        self._stt_task = asyncio.create_task(self._stt_listen_loop())
```

`_stt_listen_loop()` asla `run_loop()`'dan bağımsız olarak durmaz. Eğer `_stt_listen_loop` bir exception fırlatırsa (mikrofon kaybı, ALSA hatası, vs.):
- `self._stt_task.done()` True olur
- `run_loop()` her turda yeni bir `_stt_listen_loop` task'i oluşturur
- Sonsuz "start STT → crash → restart" döngüsü oluşabilir
- Loglara hata basılmaz (exception `_stt_listen_loop` içinde yakalanır)

**Kök Neden**:
- STT loop'unun hata durumları düzgün yönetilmiyor
- Hata sonrası restart limiti yok

**Etki**:
- Mikrofon hatası durumunda sonsuz restart döngüsü
- Tanılaması zor hatalar (crash log'u yok)

**Çözüm**:
- `_stt_listen_loop`'da restart sayacı ekle
- N. hatadan sonra STT'yi tamamen durdur ve kullanıcıya bildir
- Tüm beklenmeyen hatalar `traceback.print_exc()` ile loglanmalı

---

## 5. Thread Güvenliği ve UI — Problem Kataloğu

### P-12 [KRİTİK] StreamingSTT Callback'i Tkinter'ı Background Thread'den Çağırıyor

**Dosya**: `core/streaming_stt.py:125-128` + `main.py:365-387` + `ui.py`
**Tür**: Thread güvenliği / crash

**Tanım**:
StreamingSTT, `_transcription_loop()`'u bir daemon thread'de çalıştırır (threading.Thread). Bu thread'den `_on_stt_text()` callback'i tetiklenir. `_on_stt_text()` şunları yapar:
```python
self.ui.write_log(f"Siz: {text}")       # Tkinter widget manipülasyonu!
self.ui.mark_user_activity(True)         # Tkinter widget manipülasyonu!
from actions.tts import speak_text
speak_text(skill_result, blocking=False) # subprocess/audio çalıştırma
```

Tkinter KESINLIKLE thread-safe değildir. Widget'lar yalnızca main thread'den değiştirilmelidir.

**Kök Neden**:
- `safe_call()` metodu UI'da mevcut (main.py:1013'te kullanılıyor) ama `_on_stt_text()` bunu kullanmıyor
- StreamingSTT tasarımı gereği callback'i kendi thread'inden çağırıyor

**Etki**:
- Rastgele Tkinter crash'leri (segfault, "Tcl_AsyncDelete: async handler deleted by the wrong thread")
- Nadir ama tespiti zor hatalar
- UI donmaları veya yanlış güncellemeler

**Çözüm**:
- `_on_stt_text()` içindeki tüm UI çağrıları `self.ui.safe_call()` ile sarılmalı
- VEYA callback'i asyncio event loop'una schedule et

---

### P-13 [KRİTİK] Ollama STT Loop'unda UI Çağrıları Asyncio Thread'inden Yapılıyor

**Dosya**: `core/ollama_provider.py:511-617`
**Tür**: Thread güvenliği

**Tanım**:
Ollama provider'ın `_stt_listen_loop()` asyncio task'i, arka plan thread'inde (`asyncio-runner`) çalışır. Bu task içinde doğrudan UI çağrıları yapılır:
```python
j.ui.set_mic_level(mic_level)       # line 517 — Tkinter!
j.ui.set_state("THINKING")          # line 600 — Tkinter!
j.ui.write_log(...)                  # line 612 — Tkinter!
j.ui.mark_user_activity(True)        # line 613 — Tkinter!
```

Asyncio thread'i main thread DEĞİLDİR (main.py:1084: `daemon=True`). Tüm bu çağrılar Tkinter'a background thread'den erişir.

**Kök Neden**:
- Provider'lar asyncio thread'inde çalışır
- UI thread güvenliği baştan düşünülmemiş
- `safe_call()` sadece ACA callback'inde kullanılıyor (main.py:1013)

**Etki**:
- Tkinter kilitlenmeleri (nadir ama yıkıcı)
- "invalid command name" hataları
- UI'ın yanlış durum göstermesi

**Çözüm**:
- Tüm UI çağrıları `safe_call()` üzerinden yapılmalı
- VEYA `ui.after()` ile main thread'e schedule edilmeli

---

### P-14 [ORTA] _on_stt_text Skills Routing'i STT Loop'unu Bloke Edebilir

**Dosya**: `core/streaming_stt.py:146-157` + `main.py:375-383`
**Tür**: Performans / blokaj

**Tanım**:
StreamingSTT'nin `_transcription_loop()` callback'i SENKRON çağırır:
```python
self.on_transcription(full_text, is_final)  # Senkron!
```

`_on_stt_text()` içinde:
```python
skill_result = self.skill_manager.route(text)  # SkillEngine route'u senkron!
if skill_result is not None:
    from actions.tts import speak_text
    speak_text(skill_result, blocking=False)  # TTS başlatma
    return
```

`skill_manager.route()` tüm skill'lerin `route()` fonksiyonlarını sırayla dener. Herhangi bir skill yavaş kalırsa (regex, dosya okuma, vs.), tüm STT pipeline'ı bloke olur.

Ayrıca `speak_text()` yeni bir thread başlatır (blocking=False ile) — bu güvenli ama `voice_memory.log_...` gibi ek işlemler eklenirse blokaj artabilir.

**Kök Neden**:
- STT loop'u tek thread'li queue consumer
- Callback'lerin ne kadar süreceği kontrol edilmiyor

**Etki**:
- Ses tanımada gecikme (audio buffer birikir)
- "Audio chunk lost" durumları

**Çözüm**:
- Callback'i asyncio task'e veya ayrı thread'e forward et
- VEYA callback timeout'u ekle (500ms)

---

## 6. TTS Pipeline — Problem Kataloğu

### P-15 [YÜKSEK] EmotionTTS Piper Modu Linux'a Özel (Windows'ta Çalışmaz)

**Dosya**: `core/emotion_tts.py:135-167`
**Tür**: Platform uyumsuzluğu

**Tanım**:
`_speak_piper_emotion()` metodu:
```python
subprocess.run(["aplay", "-q", wav_path], timeout=60)
```
`aplay` yalnızca Linux'ta bulunur. Windows'ta bu satır `FileNotFoundError` fırlatır.

Aynı şekilde `speak_text()` (actions/tts.py'den) blocking=True ile çağrıldığında farklı bir yol izler.

**Kök Neden**:
- Piper TTS engine'i Linux için yazılmış
- EmotionTTS Piper modu Windows'ta test edilmemiş

**Etki**:
- Windows'ta emotion_tts ile konuşma çalışmaz
- `_speak_response` emotion_tts'i dener, başarısız olursa `actions.tts.speak_text` fallback'ine gider (main.py:438-440)

**Çözüm**:
- Windows'ta `aplay` yerine `sounddevice` veya `winsound` kullan
- Veya Piper hariç diğer engine'leri tercih et

---

### P-16 [DÜŞÜK] StreamingTTS Worker Loop'u Hata Yönetimi Eksik

**Dosya**: `core/streaming_tts.py:192-212`
**Tür**: Sağlamlık

**Tanım**:
```python
def _worker_loop(self):
    if self.on_start:
        self.on_start()
    while self._running and not self._buffer.is_cancelled:
        sentence = self._buffer.get(timeout=0.5)
        self._play_sentence(sentence)
    self._fire_done()
```

Eğer `_play_sentence()` içinde bir hata olursa (TTS engine çökmesi, ses kartı hatası):
- Exception yakalanır ve loglanır
- Worker loop sona erer (`_running = False`)
- Ama `StreamingTTS` hâlâ "çalışıyor" gibi görünür (`is_speaking()` True dönebilir)
- Yeni `speak()` çağrısı worker'ı yeniden başlatmaz (sadece queue'ya ekler)

**Kök Neden**:
- Worker loop'u restart mekanizması yok
- Hata sonrası state tutarsızlığı

**Etki**:
- TTS sessizce ölebilir, kullanıcı "konuşmuyor" sanar
- `_buffer.put()` yapılır ama worker çalışmadığı için okunmaz

**Çözüm**:
- Worker crash sonrası otomatik restart
- Veya hata durumunda `on_error` callback'i ile bildirim + restart

---

## 7. Genel Mimari Sorunlar

### P-17 [YÜKSEK] UI State Machine Tutarsız: _jarvis_state Birçok Yerde Doğrudan Set Ediliyor

**Dosya**: `ui.py` (tüm set_state çağrıları) + `core/ollama_provider.py` + `core/gemini_provider.py` + `main.py`
**Tür**: Tasarım

**Tanım**:
`j.ui.set_state("THINKING")`, `j.ui.set_state("LISTENING")`, `j.ui.set_state("ERROR")`, `j.ui.set_state("SPEAKING")` çağrıları kodun en az **15 farklı yerinde** bulunur. State geçişlerinin merkezi bir kontrolü yoktur.

Özellikle:
```python
# ollama_provider.py:565
if getattr(j.ui, "_jarvis_state", "") not in ("THINKING", "SPEAKING"): j.ui.set_state("LISTENING")
```
Bu satır kodun 4 farklı yerinde tekrarlanır (202, 298, 565, 617). Bu bir "guard clause" pattern'idir ama her yere dağılmıştır.

**Kök Neden**:
- State machine'in merkezi bir yöneticisi yok
- Her provider kendi state'ini kendisi yönetiyor

**Etki**:
- State tutarsızlıkları (UI "LISTENING" gösterirken aslında "THINKING")
- Geçişlerde yanıp sönen UI
- Debug'ı zor hatalar

**Çözüm**:
- State machine'ı `jarvis` nesnesine taşı (örn. `set_state()` metodu)
- Geçiş kurallarını tek yerde tanımla (LISTENING→THINKING→SPEAKING→LISTENING)

---

### Önceki Sorunlar (Önceki Oturumda Düzeltildi)
Bu oturumdan önce çözülmüş ve test edilmiş sorunlar:

- ~~**P-00 (VAD Ordering)**: VAD speaking/wake word gate'lerinden ÖNCE çağrılıyordu~~ → **Düzeltildi**: ollama_provider.py:568
- ~~**P-00 (safe_call string)**: safe_call'e string argüman geçiliyordu (method reference yerine)~~ → **Düzeltildi**: main.py:1013
- ~~**P-00 (VAD rate)**: VAD rate parametresi `device_rate` yerine `target_rate` olmalıydı~~ → **Düzeltildi**: ollama_provider.py:569

---

## 8. Onarım Sırası ve Önceliklendirme

Her bir soruna bir öncelik (P0=P-kritik, P1=Yüksek, P2=Orta, P3=Düşük), bir çaba (S/M/L/XL) ve bir bağımlılık zinciri atanmıştır.

### Faz 1: Kritik (P0) — Önce Bunlar

| # | Sorun | Dosya(lar) | Çaba | Bağımlılık |
|---|-------|-----------|------|------------|
| 1 | P-12 (Tkinter Thread) + P-13 (UI Thread) | `main.py`, `ollama_provider.py`, `gemini_provider.py` | **XL** | Yok |
| 2 | P-06 (RNNoise Kullanılmıyor) | `ollama_provider.py`, `gemini_provider.py` | **M** | Yok |
| 3 | P-01 (Çift STT) | `main.py`, `gemini_provider.py` | **S** | Yok |
| 4 | P-09 (Provider Arayüzü) | `main.py`, `provider_base.py`, `ollama_provider.py` | **M** | Yok |

### Faz 2: Yüksek (P1)

| # | Sorun | Dosya(lar) | Çaba | Bağımlılık |
|---|-------|-----------|------|------------|
| 5 | P-02 (Çift VAD) | `main.py` | **S** | Yok |
| 6 | P-03 (StreamingSTT Yönlendirme) | `main.py` | **S** | Faz-1.4 |
| 7 | P-11 (Ollama Task Yönetimi) | `ollama_provider.py` | **M** | Yok |
| 8 | P-17 (UI State Machine) | `main.py`, `ui.py` | **M** | Faz-1.1 |
| 9 | P-15 (EmotionTTS Windows) | `emotion_tts.py` | **S** | Yok |

### Faz 3: Orta (P2)

| # | Sorun | Dosya(lar) | Çaba | Bağımlılık |
|---|-------|-----------|------|------------|
| 10 | P-04 (Provider Geçişi) | `main.py` | **M** | Yok |
| 11 | P-05 (Config Disk I/O) | `ollama_provider.py` | **S** | Yok |
| 12 | P-07 (Gemini VAD Yok) | `gemini_provider.py` | **L** | Faz-2.3 |
| 13 | P-14 (STT Loop Blokaj) | `streaming_stt.py`, `main.py` | **S** | Faz-1.1 |

### Faz 4: Düşük (P3)

| # | Sorun | Dosya(lar) | Çaba | Bağımlılık |
|---|-------|-----------|------|------------|
| 14 | P-08 (PyAudio Leak) | `ollama_provider.py` | **S** | Yok |
| 15 | P-10 (send_audio Soyutlama) | `provider_base.py` | **S** | Yok |
| 16 | P-16 (StreamingTTS Worker) | `streaming_tts.py` | **S** | Yok |

---

## 9. Kabul Kriterleri

### Test Gereksinimleri
Her düzeltme için:
- [ ] Mevcut testler geçiyor (`python -m unittest discover tests -v`)
- [ ] LSP diagnostics clean
- [ ] Manuel smoke test: `python main.py` (Ollama modu, sesli komut: "merhaba")
- [ ] Manuel smoke test: `python main.py` (Gemini modu, sesli komut: "merhaba")

### Faz Bazında Kabul

**Faz 1 Sonu**:
- [ ] Tüm UI çağrıları main thread'den yapılıyor
- [ ] RNNoise en az Ollama modunda aktif
- [ ] Gemini modunda StreamingSTT çalışmıyor
- [ ] Tüm text girişi `send_text()` üzerinden

**Faz 2 Sonu**:
- [ ] Tek VAD instance'ı, aktif olarak kullanılıyor
- [ ] StreamingSTT callback'i doğru provider'a yönleniyor
- [ ] Ollama task crash sonrası max 3 restart, sonra durur
- [ ] UI state geçişleri merkezi olarak yönetiliyor

**Faz 3 Sonu**:
- [ ] Backend geçişi sırasında ses kaybı < 500ms
- [ ] Config diskten sadece değişiklikte okunuyor
- [ ] STT callback'i UI'ı bloke etmiyor

---

## 10. Dosya Referansları ve Etki Analizi

### Değişecek Dosyalar

| Dosya | Değişiklik Kapsamı | Tahmini Satır |
|-------|-------------------|---------------|
| `main.py` | Thread güvenliği, provider arayüzü, VAD cleanup, backend geçişi | +80/-50 |
| `core/ollama_provider.py` | RNNoise, thread güvenliği, config caching, task yönetimi | +60/-20 |
| `core/gemini_provider.py` | Thread güvenliği, opsiyonel VAD | +40/-10 |
| `core/provider_base.py` | send_audio ekle, send_text standardize | +10/-0 |
| `core/streaming_stt.py` | Callback forwarding (opsiyonel) | +15/-5 |
| `core/streaming_tts.py` | Worker restart | +20/-5 |
| `core/emotion_tts.py` | Windows aplay fallback | +15/-3 |
| `core/fahrettin_vad.py` | (dokunulmayacak) | 0 |
| `audio/noise_suppressor.py` | (dokunulmayacak) | 0 |
| `ui.py` | `safe_call` genişletme (opsiyonel) | +10/-0 |

### Etkilenmeyecek Dosyalar
- `core/_skill_engine.py` — skill sistemi bağımsız
- `core/skill_manager.py` — skill sistemi bağımsız
- `core/agent/` — ACA alt sistemi bağımsız
- `actions/*.py` — action modülleri bağımsız
- `core/tool_registry.py` — tool registry bağımsız
- Tüm skill modülleri (`skills/`)
- Tüm test dosyaları
