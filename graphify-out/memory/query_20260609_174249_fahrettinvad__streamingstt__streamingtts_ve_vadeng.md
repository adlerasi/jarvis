---
type: "query"
date: "2026-06-09T17:42:49.321160+00:00"
question: "FahrettinVAD, StreamingSTT, StreamingTTS ve VADEngine arasindaki gercek kod baglantilari nedir?"
contributor: "graphify"
source_nodes: ["FahrettinVAD", "VADEngine", "StreamingTTS", "StreamingSTT", "JarvisLive"]
---

# Q: FahrettinVAD, StreamingSTT, StreamingTTS ve VADEngine arasindaki gercek kod baglantilari nedir?

## Answer

Ses isleme zinciri 4 dosyaya yayilmis: core/fahrettin_vad.py (193 satir) → core/vad_engine.py (325 satir) → core/streaming_stt.py (300 satir) → core/streaming_tts.py (230 satir). Zincir jarvislive (main.py L174) tarafindan _asimilasyon_init() (L204) ile baslatiliyor. Hicbirinin testi yok.

## Source Nodes

- FahrettinVAD
- VADEngine
- StreamingTTS
- StreamingSTT
- JarvisLive