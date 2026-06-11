# Feature Specification: Orkestrasyon Onarımı

## Summary

JARVIS sesli asistanın orkestrasyon, ses pipeline ve chat/provider katmanlarındaki yapısal sorunların tespiti ve onarımı. 17 ayrı sorun kategorize edilmiş, 4 faza bölünmüştür.

## Key Problems

1. **Dual STT Pipeline**: Çift STT (StreamingSTT + provider STT) aynı anda çalışıyor
2. **Dual VAD Instance**: Kullanılmayan VAD engine main.py'de duruyor
3. **Provider Arayüzü Tutarsızlığı**: `send_text` vs `input_queue` çatışması
4. **Thread Unsafety**: Tkinter çağrıları background thread'lerden yapılıyor
5. **RNNoise Kullanılmıyor**: Gürültü bastırma hiçbir provider'da aktif değil
6. **Provider Geçişi Race Condition**: Backend değişiminde kaynak sızıntısı
7. **Config Disk I/O**: Her frame'de config dosyası okunuyor
8. **Zayıf Task Yönetimi**: Ollama STT loop restart döngüsüne girebilir
9. **EmotionTTS Windows Uyumsuz**: `aplay` Linux'a özel
10. **UI State Machine Dağınık**: State geçişleri 15+ yerde kontrolsüz

## Scope

- `main.py`: Thread güvenliği, provider arayüzü, VAD cleanup
- `core/ollama_provider.py`: RNNoise, thread güvenliği, config caching
- `core/gemini_provider.py`: Thread güvenliği, opsiyonel VAD
- `core/provider_base.py`: send_audio soyutlaması
- `core/streaming_stt.py`: Callback forwarding
- `core/streaming_tts.py`: Worker restart
- `core/emotion_tts.py`: Windows aplay fallback

## Out of Scope

- ACA agent sistemi (`core/agent/`)
- Skill sistemi (`core/skill_manager.py`, `core/_skill_engine.py`)
- Action modülleri (`actions/`)
- Test dosyaları
