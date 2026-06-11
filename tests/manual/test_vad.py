import asyncio
from core.ollama_provider import OllamaProvider

import contextlib

class MockUI:
    muted = False
    _jarvis_state = "LISTENING"
    def write_log(self, msg):
        print(f"[UI LOG] {msg}", flush=True)
    def set_state(self, state):
        pass
    def mark_user_activity(self, b):
        pass

class MockJarvis:
    ui = MockUI()
    _is_speaking = False
    _paused = False
    barge_in = None
    wake_word = None
    _speaking_lock = contextlib.nullcontext()
    _last_speech_end = 0.0
    _speaking_cooldown = 1.0
    _user_initiated = False

async def main():
    p = OllamaProvider()
    j = MockJarvis()
    p.j = j
    await p.start(j)
    
    # Run _stt_listen_loop
    task = asyncio.create_task(p._stt_listen_loop())
    print("VAD TEST STARTED. SPEAK NOW.", flush=True)
    
    # Wait for 5 seconds to let STT loop run
    print("Waiting 5 seconds for VAD to process audio...", flush=True)
    await asyncio.sleep(5)
        
    await p.stop()

if __name__ == "__main__":
    asyncio.run(main())
