import re

with open("core/ollama_provider.py", "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace from `# ── STT Listen Loop` to the end of the file.
start_idx = content.find("    # ── STT Listen Loop")
if start_idx == -1:
    print("Could not find start index")
    exit(1)

new_content = content[:start_idx] + """    # ── STT Listen Loop ──────────────────────────────────────

    async def _stt_listen_loop(self):
        \"\"\"Main STT loop: PyAudio → STTEngine → input_queue.\"\"\"
        j = self._j()
        import pyaudio
        import numpy as np
        import traceback
        from core.audio_system.stt_engine import get_stt_engine
        
        stt_engine = get_stt_engine()
        if not stt_engine.is_available():
            print("[Ollama STT] UYARI: STT motoru hazir degil!")
            
        p = pyaudio.PyAudio()
        stream = None
        target_rate = 16000
        device_rate = 16000
        
        # Sudo altinda PulseAudio reddedilirse hw dogrudan 44100 veya 48000 Hz isteyebilir.
        for rate in [16000, 48000, 44100]:
            try:
                stream = p.open(
                    format=pyaudio.paInt16, channels=1, rate=rate,
                    input=True, frames_per_buffer=2048,
                )
                device_rate = rate
                print(f"[Ollama STT] PyAudio stream opened at {rate}Hz")
                break
            except Exception as e:
                print(f"[Ollama STT] PyAudio {rate}Hz failed: {e}")
                
        if stream is None:
            print("[Ollama STT] FATAL: Mikrofon baslatilamadi.")
            p.terminate()
            j.ui.write_log("ERR: Mikrofon baslatilamadi. Sesli komut calismayacak.")
            return

        # ── Noise profile ──
        _noise_floor = None
        _noise_frames = []
        FRAME_SIZE = 2048
        
        print("[Ollama STT] Dinleme başladı...")
        _speech_buf = bytearray()
        _silence_start = None
        _is_awake = False
        
        try:
            while self._running:
                cfg = _load_app_config()
                if j._paused or cfg.get("backend_type", "gemini") != "ollama":
                    await asyncio.sleep(0.1)
                    continue

                barge = getattr(j, "barge_in", None)
                try:
                    # Non-blocking read attempts to avoid deadlocks
                    data = stream.read(FRAME_SIZE, exception_on_overflow=False)
                    
                    # ── Downsample if needed ──
                    if device_rate != target_rate:
                        import scipy.signal
                        pcm = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                        samples = int(len(pcm) * target_rate / device_rate)
                        resampled = scipy.signal.resample(pcm, samples)
                        data = resampled.astype(np.int16).tobytes()
                    
                    # ── Feed shared modules ──
                    ww = getattr(j, "wake_word", None)
                    if ww is not None:
                        ww.feed_audio(data)
                    buf = getattr(j, "audio_buffer", None)
                    if buf is not None:
                        buf.write(data)
                    sstt = getattr(j, "streaming_stt_engine", None)
                    if sstt is not None:
                        sstt.feed_audio(data)
                        
                    if barge is not None and barge.is_jarvis_speaking():
                        barge.process_user_audio(data)
                        continue

                    with j._speaking_lock:
                        js = j._is_speaking
                        sc = time.monotonic() - j._last_speech_end < j._speaking_cooldown
                        
                    if js or sc or j.ui.muted:
                        continue
                        
                    # Wake word
                    if ww is not None:
                        if j._wake_word_triggered:
                            _is_awake = True
                            j._wake_word_triggered = False
                        if not _is_awake:
                            continue
                            
                    j.ui.set_state("LISTENING")
                    
                    # VAD (Energy-based fallback)
                    arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                    rms = float(np.sqrt(np.mean(arr ** 2)))
                    
                    if _noise_floor is None:
                        _noise_frames.append(rms)
                        if len(_noise_frames) >= 10:
                            _noise_frames.sort()
                            _noise_floor = _noise_frames[len(_noise_frames) // 4]
                            if _noise_floor < 1.0: _noise_floor = 50.0
                            print(f"[Ollama STT] Noise floor: {_noise_floor:.1f}")
                        is_speech = False
                    else:
                        _noise_floor = _noise_floor * 0.99 + rms * 0.01
                        threshold = _noise_floor + 400.0 if _noise_floor else 2500.0
                        is_speech = rms > threshold
                        
                    if is_speech:
                        _speech_buf.extend(data)
                        _silence_start = None
                    else:
                        if _speech_buf:
                            if _silence_start is None:
                                _silence_start = time.time()
                            elif (time.time() - _silence_start) * 1000 > 500: # 500ms silence
                                audio_bytes = bytes(_speech_buf)
                                _speech_buf = bytearray()
                                _silence_start = None
                                _is_awake = False
                                
                                if len(audio_bytes) < 3200:
                                    continue
                                    
                                j.ui.set_state("THINKING")
                                text = ""
                                try:
                                    text = await asyncio.to_thread(
                                        stt_engine.transcribe, audio_bytes, target_rate
                                    )
                                except Exception as e:
                                    print(f"[Ollama STT] Transcription error: {e}")
                                    
                                if text and text.strip():
                                    text = text.strip()
                                    j._user_initiated = True
                                    j.ui.write_log(f"Siz: {text}")
                                    j.ui.mark_user_activity(True)
                                    print(f"[Ollama STT] {text}")
                                    await self.input_queue.put(text)
                                else:
                                    j.ui.set_state("LISTENING")
                                    
                except OSError as e:
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"[Ollama STT] Loop error: {e}")
                    traceback.print_exc()
                    await asyncio.sleep(0.5)
        except Exception:
            traceback.print_exc()
        finally:
            try:
                if stream:
                    stream.close()
                p.terminate()
            except Exception as e:
                print(f"[Ollama STT] Cleanup error: {e}")
"""

with open("core/ollama_provider.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done")
