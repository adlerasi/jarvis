import asyncio
from core.ollama_provider import OllamaProvider

class MockUI:
    muted = False
    _jarvis_state = "IDLE"
    def write_log(self, msg): print(f"[UI LOG] {msg}")
    def set_state(self, state): self._jarvis_state = state; print(f"[UI STATE] {state}")
    def mark_user_activity(self, active): pass

class MockJarvis:
    def __init__(self):
        import threading
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

async def main():
    j = MockJarvis()
    p = OllamaProvider()
    
    print("Starting OllamaProvider...")
    await p.start(j)
    
    print("Simulating user input into queue (bypassing microphone STT)...")
    await p.input_queue.put("merhaba, adın ne?")
    
    print("Waiting for OllamaProvider to process the audio (LLM)...")
    response = await p.process_audio()
    print(f"\n--- LLM RESPONSE ---\n{response}\n--------------------")
    
    await p.stop()

if __name__ == "__main__":
    asyncio.run(main())
