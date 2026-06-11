import asyncio
from core.ollama_provider import OllamaProvider
import threading

class MockUI:
    muted = False
    _jarvis_state = "IDLE"
    def write_log(self, msg): print(f"[UI LOG] {msg}")
    def write_debug(self, msg, level="DEBUG"): print(f"[UI DEBUG] {msg}")
    def set_state(self, state): self._jarvis_state = state; print(f"[UI STATE] {state}")
    def mark_user_activity(self, active): pass

class MockJarvis:
    def __init__(self):
        self.ui = MockUI()
        self._paused = False
        self._speaking_lock = threading.Lock()
        self._is_speaking = False
        self._last_speech_end = 0
        self._speaking_cooldown = 1.0
        self.wake_word = None
        self.audio_buffer = None
        self.barge_in = None
        self._wake_word_triggered = False
        self._user_initiated = False

async def main():
    j = MockJarvis()
    p = OllamaProvider()
    await p.start(j)
    
    # Run the run_loop but in a task so we can stop it after 15 seconds
    print("OllamaProvider started! Please speak into the microphone for the next 15 seconds!")
    loop_task = asyncio.create_task(p.run_loop())
    
    await asyncio.sleep(15)
    
    print("Stopping...")
    await p.stop()
    loop_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
