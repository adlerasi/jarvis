# Implementation Plan: Voice Orchestration Layer

**Branch**: `007-voice-orchestration-layer` | **Date**: 2026-06-11 | **Spec**: spec.md

## Summary

Tüm backend'lerde (Gemini/Ollama) ChatGPT-tarzı kesintisiz sesli konuşma deneyimini sağlayan orkestrasyon katmanının eksiklerini tamamla: state yönetimi, ses kuyruğu sınırlandırması, hata yollarının merkezi state'e yönlendirilmesi ve realtime testler.

## Technical Context

**Language**: Python 3.10+ (3.13)
**Testing**: unittest
**Target Platform**: Windows 10/11 (birincil), Linux/macOS (ikincil)
**Constraints**: <500ms barge-in, <10sn ses kuyruğu

## Project Structure

```
main.py              # JarvisLive.set_state() state machine
core/
├── gemini_provider.py  # Queue maxsize, set_state kullanımı
├── ollama_provider.py  # set_state kullanımı mevcut
├── barge_in.py         # BargeInDetector
tests/
├── test_barge_in.py
└── test_smoke.py
```

## Kalan Eksikler (Gap Analysis)

| FR | Açıklama | Durum |
|----|----------|-------|
| FR-001 | Backend bağımsız UX | ✅ Mevcut |
| FR-002 | Araya girme (barge-in) | ✅ Mevcut |
| FR-003 | Merkezi state machine | ✅ P-17 ile yapıldı |
| FR-004 | Hata → set_state() | ✅ main.py:656 düzeltildi |
| FR-005 | Sınırlı ses kuyruğu | ✅ maxsize=200 |
| FR-006 | Mikrofon blokesiz | ✅ Mevcut |
| FR-007 | Otomatik yeniden bağlanma | ✅ Mevcut |
| FR-008 | Amplitude gate | ✅ Mevcut |

**Test**: Realtime barge-in testi, state geçiş testi, queue limit testi
