"""Ollama HTTP API Provider — text-in/text-out, local STT + TTS.

Extracted from main.py to make the provider interface concrete.

MIMARI:
  BaseProvider'dan turer. Sesli asistan pipeline'inin tumunu yonetir:
  - Mikrofon yakalama (orchestrator pipeline uzerinden)
  - VAD (energy-based, RNNoise entegrasyonlu)
  - STT (2 yol: single-shot STTEngine + real-time StreamingSTT)
  - Ollama HTTP Chat (/api/chat) ile LLM yaniti
  - Tool calling (local tool parser ile)
  - TTS (Piper / Edge-TTS / spd-say)

OZELLIKLER:
  keep_alive: "30m" — model 30 dk bellekte kalir.
  num_ctx: otomatik (model boyutuna gore) veya manuel (config).
  Mega-ASR pre-warm: startup'ta background yukleme (configurable)."""
#   num_ctx: otomatik (model boyutuna gore) veya manuel config'den
#   Tool calling: "tool_name(arg1, arg2)" formatinda metin ayristirma
#   RNNoise: gurultu bastirma (varsa)
#
# KONFIGURASYON (config/api_keys.json):
#   backend_type: "ollama"
#   ollama_model: "qwen2.5:7b" (veya auto-select)
#   ollama_num_ctx: 0 (0=auto, >0=manual)
#   ollama_tts_voice: "piper-fahrettin"
#   mega_asr_prewarm: true
# ──────────────────────────────────────────────────────────────

from __future__ import annotations

import os as _os

_DEBUG = _os.environ.get("JARVIS_DEBUG_STT", "").lower() in ("1", "true", "yes")

import asyncio
import datetime
import json
import os
import re
import time
import traceback
from typing import Any

import numpy as np
import scipy.signal

from core.provider_base import BaseProvider
from core.tool_registry import VALID_TOOLS, generate_ollama_tool_help



# RNNoise gürültü bastırma (opsiyonel — kütüphane yoksa bypass)
try:
    import audio.noise_suppressor as _noise_module
    _HAS_RNNOISE = True
except ImportError:
    _HAS_RNNOISE = False


# ── Constants (matches main.py) ──────────────────────────────

FRAME_SIZE = 480       # 30ms @ 16kHz
MIN_SILENCE_MS = 800
SILENCE_TIMEOUT_MS = 5000
NOISE_ADAPT_FRAMES = 30
MAX_ARG_LENGTH = 500
MAX_TOOL_CALL_TOTAL_LENGTH = 2000


# ── Tool Call Parser (extracted from main.py) ────────────────

def parse_local_tool_call(text: str) -> tuple | None:
    """Parse 'tool_name(args)' from Ollama response text.

    Returns (tool_name, parsed_args_dict) or None on failure.
    Uses VALID_TOOLS from tool_registry (single source of truth).
    """
    text = text.strip()
    if len(text) > MAX_TOOL_CALL_TOTAL_LENGTH:
        return None
    match = re.search(
        r'(?:TOOL:\s*)?([a-zA-Z0-9_]+)\((.*)\)',
        text, re.DOTALL | re.IGNORECASE
    )
    if not match:
        return None

    tool_name = match.group(1).strip().lower()
    args_content = match.group(2).strip()

    if tool_name not in VALID_TOOLS:
        print(
            f"[Ollama Tool Call] Bilinmeyen araç algılandı ve reddedildi: "
            f"'{tool_name}' (yanıt: {text[:120]})"
        )
        return None

    try:
        if args_content.startswith('{') and args_content.endswith('}'):
            parsed = json.loads(args_content)
            for k, v in parsed.items():
                if isinstance(v, str) and len(v) > MAX_ARG_LENGTH:
                    return None
            return tool_name, parsed
    except Exception as e:
        print(f"[Ollama Tool Call] JSON parse error (trying fallback): {e}")

    # Fallback: key=value pairs
    try:
        args: dict[str, Any] = {}
        pairs = re.findall(r'(\w+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|(\S+))', args_content)
        for key, v1, v2, v3 in pairs:
            val = v1 or v2 or v3
            if len(val) > MAX_ARG_LENGTH:
                return None
            args[key] = val
        return tool_name, args
    except Exception as e:
        print(f"[Ollama Tool Call] Fallback parse error: {e}")

    return None


# ── Helpers (moved from main.py) ─────────────────────────────

def _load_app_config() -> dict:
    """Config JSON dosyasini yukler (lazy import)."""
    from app_config import load_app_config
    return load_app_config()


def _load_memory() -> dict:
    """Kullanici bellegini yukler (lazy import)."""
    from memory.memory_manager import load_memory
    return load_memory()


def _format_memory_for_prompt(mem: dict) -> str:
    """Bellegi LLM prompt'una formatlar (lazy import)."""
    from memory.memory_manager import format_memory_for_prompt
    return format_memory_for_prompt(mem)


def _load_system_prompt() -> str:
    """Sistem prompt'unu yukler (lazy import)."""
    from main import load_system_prompt
    return load_system_prompt()


# ── Ollama Provider ──────────────────────────────────────────

class OllamaProvider(BaseProvider):

    @property
    def name(self) -> str:
        """Provider adi: 'ollama'."""
        return "ollama"

    MAX_STT_RESTARTS = 5

    def __init__(self) -> None:
        """OllamaProvider baslatir."""
        super().__init__()
        self.input_queue: asyncio.Queue = asyncio.Queue()
        self._audio_queue: asyncio.Queue = asyncio.Queue(maxsize=500)  # 16kHz PCM from orchestrator
        self._stt_task: asyncio.Task | None = None
        self._history: list[dict[str, str]] = []
        self._ollama_warned_quality = False
        self._running = False
        self._cached_config: dict = {}
        self._config_last_refresh: float = 0.0
        self._stt_restart_count: int = 0
        self._warmup_done: bool = False
        self._llm: Any = None  # lazy-loaded LocalLLM instance

    def feed_audio(self, data: bytes) -> None:
        """Called from orchestrator's audio pipeline (16kHz PCM, background thread)."""
        try:
            self._audio_queue.put_nowait(data)
        except asyncio.QueueFull:
            pass

    def _get_llm(self) -> Any:
        """Lazy-load LocalLLM instance."""
        if self._llm is None:
            try:
                from core.local_llm import LocalLLM
                self._llm = LocalLLM()
            except Exception:
                self._llm = object()  # sentinel — don't retry
        return self._llm if not isinstance(self._llm, type(object)) else None

    def _get_config(self) -> dict:
        """Config'den Ollama ayarlarini okur (1 sn cache)."""
        now = time.monotonic()
        if now - self._config_last_refresh > 1.0:
            self._cached_config = _load_app_config()
            self._config_last_refresh = now
        return self._cached_config

    def _get_num_ctx(self) -> int:
        """Context penceresi boyutunu otomatik veya manuel belirler.

        Config'de ollama_num_ctx > 0 ise manuel değer kullanılır.
        0 (veya eksik) ise model adındaki parametre sayısından
        otomatik seçim yapılır — sesli asistanda TTFT'yi ~1-2s
        tutacak değerler seçilir.
        """
        cfg = self._get_config()
        manual = cfg.get("ollama_num_ctx", 0)
        if manual > 0:
            return manual

        model = self._get_model_name().lower()
        import re as _re
        m = _re.search(r'(\d+\.?\d*)(?=[b])', model)
        if m:
            size = float(m.group(1))
            if size <= 3:
                return 4096
            elif size <= 9:
                return 8192
            else:
                return 16384
        return 8192

    async def _warmup(self):
        """One-shot model warm-up. Runs exactly once per process lifetime."""
        if self._warmup_done:
            return
        self._warmup_done = True
        j = self._j()
        import httpx
        cfg = self._get_config()
        warmup_model = self._get_model_name()
        if not warmup_model:
            return
        j.ui.safe_call(j.ui.write_log, f"SYS: Model yükleniyor ({warmup_model})...")
        j.set_state("THINKING")
        try:
            num_ctx = self._get_num_ctx()
            warmup_opts = {"num_ctx": num_ctx} if num_ctx else {}
            async with httpx.AsyncClient(timeout=120.0) as client:
                await client.post(
                    "http://localhost:11434/api/chat",
                    json={
                        "model": warmup_model,
                        "messages": [],
                        "keep_alive": "30m",
                        "options": warmup_opts,
                    },
                )
            print(f"[Ollama] Warm-up tamamlandı: {warmup_model} (ctx={num_ctx})")
        except Exception as e:
            print(f"[Ollama] Warm-up hata (önemsiz): {e}")

    async def start(self, jarvis: Any) -> None:
        """Ollama provider'ini baslatir, STT pipeline'ini kurar."""
        await super().start(jarvis)
        self._history = []
        self._ollama_warned_quality = False
        self._running = True
        self._stt_restart_count = 0  # reset restart counter on provider restart
        await self._warmup()  # warm-up once per provider lifecycle

    async def stop(self):
        """Ollama provider'ini durdurur, kaynaklari temizler."""
        self._running = False
        if self._stt_task is not None and not self._stt_task.done():
            self._stt_task.cancel()
            try:
                await self._stt_task
            except (asyncio.CancelledError, Exception):
                pass
            self._stt_task = None

    async def send_text(self, text: str) -> None:
        """Put text into the Ollama processing queue."""
        await self.input_queue.put(text)

    # ── Main processing loop ─────────────────────────────────

    async def run_loop(self):
        """Main Ollama loop — STT + HTTP chat + TTS."""
        j = self._j()
        import httpx

        # Always start STT listener — Ollama handles its own microphone capture
        # for STT independent of the shared audio pipeline.
        if self._stt_task is None or self._stt_task.done():
            if self._stt_restart_count >= self.MAX_STT_RESTARTS:
                print(f"[Ollama] STT {self.MAX_STT_RESTARTS} kez yeniden baslatildi, durduruluyor.")
                j.ui.safe_call(j.ui.write_log, "ERR: Ses tanima surekli hata veriyor, durduruldu.")
                j.set_state("ERROR")
                self._running = False
                raise RuntimeError(
                    f"STT {self.MAX_STT_RESTARTS} kez yeniden baslatildi — ses tanima devre disi."
                )
            self._stt_restart_count += 1
            self._stt_task = asyncio.create_task(self._stt_listen_loop())

        if not self._history:
            self._history = []

        # ── Proactive voice start ──
        pv = getattr(j, "proactive_voice", None)
        if pv is not None:
            try:
                pv.start()
            except Exception as e:
                print(f"[Ollama] Proactive voice start error: {e}")

        if getattr(j.ui, "_jarvis_state", "") not in ("THINKING", "SPEAKING"):
            j.set_state("LISTENING")
        j.ui.safe_call(j.ui.write_log, "SYS: JARVIS yerel modda hazır. Dinliyorum...")

        while self._running:
            cfg = self._get_config()
            if cfg.get("backend_type", "gemini") != "ollama":
                break

            if j._paused:
                await asyncio.sleep(0.5)
                continue

            try:
                text = await asyncio.wait_for(self.input_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            # Voice memory log
            vm = getattr(j, "voice_memory", None)
            if vm is not None:
                try:
                    vm.log_user(text)
                except Exception as e:
                    print(f"[Ollama] Voice memory error: {e}")

            j.set_state("THINKING")

            # Thinking aloud
            ta = getattr(j, "thinking_aloud", None)
            if ta is not None:
                try:
                    ta.start("processing")
                except Exception as e:
                    print(f"[Ollama] Thinking aloud error: {e}")

            # ── Build system prompt ──
            mem_data = _load_memory()
            mem_str = _format_memory_for_prompt(mem_data)
            sys_p = _load_system_prompt()
            now = datetime.datetime.now()
            time_ctx = f"[ŞU ANKİ ZAMAN]\n{now.strftime('%A, %d %B %Y — %H:%M')}\n\n"

            transcript_str = ""
            tr = getattr(j, "transcript", None)
            if tr is not None:
                try:
                    transcript_str = tr.get_formatted(n=5)
                except Exception as e:
                    print(f"[Ollama] Transcript error: {e}")

            parts = [time_ctx]
            if mem_str:
                parts.append(mem_str + "\n\n")
            if transcript_str:
                parts.append(transcript_str + "\n\n")
            # Strip example conversations for small local models
            sys_p = self._trim_system_prompt(sys_p)
            parts.append(sys_p)
            system_instruction = "\n".join(parts)

            # Use tool_registry for Ollama tool help (single source of truth)
            system_instruction += generate_ollama_tool_help()

            messages = [{"role": "system", "content": system_instruction}]
            messages.extend(self._history[-10:])  # fewer history entries for small models
            messages.append({"role": "user", "content": text})

            ollama_model = self._get_model_name()
            if not ollama_model:
                j.ui.safe_call(j.ui.write_log, "ERR: Ollama modeli secilmemis.")
                j.set_state("ERROR")
                continue

            print(f"[Ollama] Model: {ollama_model}")

            # ── Send to Ollama API (with fallback) ──
            response_text = ""
            try:
                response_text = await self._ollama_chat(
                    ollama_model, messages, j
                )
            except Exception as e:
                err_detail = f"{type(e).__name__}: {e}"
                print(f"[Ollama] Hata (1. deneme): {err_detail}")
                # Retry with minimal context – strip history, memory, transcript
                if len(messages) > 1:
                    fallback = [messages[0]]  # only system prompt
                    fallback.append({"role": "user", "content": text})
                    try:
                        print("[Ollama] Kisa prompt ile tekrar deneniyor...")
                        j.ui.safe_call(j.ui.write_log, "WARN: Ollama yavaş, kısa prompt ile tekrar deneniyor...")
                        response_text = await self._ollama_chat(
                            ollama_model, fallback, j
                        )
                    except Exception as e2:
                        err_detail2 = f"{type(e2).__name__}: {e2}"
                        print(f"[Ollama] Hata (2. deneme): {err_detail2}")
                        j.ui.safe_call(j.ui.write_log, f"ERR: Ollama yanit veremiyor — {err_detail2[:120]}")
                        j.set_state("ERROR")
                        continue
                else:
                    j.ui.safe_call(j.ui.write_log, f"ERR: Ollama yanit veremiyor — {err_detail[:120]}")
                    j.set_state("ERROR")
                    continue

            print(f"[Ollama] Yanit uzunlugu: {len(response_text)} chars")

            # Clean <think> blocks from reasoning models
            response_text = re.sub(
                r"<think>[\s\S]*?</think>", "", response_text,
                flags=re.IGNORECASE
            ).strip()

            if not response_text:
                j.ui.safe_call(j.ui.write_log, "WARN: Model bos yanit verdi, tekrar bekliyorum.")
                if getattr(j.ui, "_jarvis_state", "") not in ("THINKING", "SPEAKING"):
                    j.set_state("LISTENING")
                continue

            # ── Check for tool calls ──
            tool_call = parse_local_tool_call(response_text)
            if tool_call:
                tool_name, tool_args = tool_call
                print(f"[Ollama Tool Call] detected: {tool_name} with {tool_args}")
                j.ui.safe_call(j.ui.write_log, f"SYS: Araç çalıştırılıyor — {tool_name}")

                # LocalFunctionCall adapter → _execute_tool
                class LocalFunctionCall:
                    def __init__(self, name, args) -> None:
                        """LocalFunctionCall baslatir."""
                        self.id = "local_call"
                        self.name = name
                        self.args = args

                try:
                    result_response = await j._execute_tool(
                        LocalFunctionCall(tool_name, tool_args)
                    )
                    result_text = result_response.response.get("result", "Tamamlandı.")
                except Exception as e:
                    result_text = f"Hata: {e}"

                self._history.append({"role": "user", "content": text})
                self._history.append({"role": "assistant", "content": response_text})
                tool_result_prompt = (
                    f"[ARAÇ SONUCU] {result_text}\n"
                    f"Lütfen kullanıcıya bunu Türkçe olarak açıkla."
                )
                self._history.append({"role": "user", "content": tool_result_prompt})

                messages = [{"role": "system", "content": system_instruction}]
                messages.extend(self._history[-10:])  # fewer history entries for small models

                response_text = ""
                try:
                    j.set_state("THINKING")
                    response_text = await self._ollama_chat(
                        ollama_model, messages, j
                    )
                    # Clean <think> blocks
                    response_text = re.sub(
                        r"<think>[\s\S]*?</think>", "", response_text,
                        flags=re.IGNORECASE
                    ).strip()
                except Exception as e:
                    err_detail = f"{type(e).__name__}: {e}"
                    print(f"[Ollama Tool Follow-up] Hata: {err_detail}")
                    # Retry without history
                    if len(messages) > 1:
                        fallback = [messages[0], {"role": "user", "content": tool_result_prompt}]
                        try:
                            print("[Ollama Tool Follow-up] Kisa prompt ile tekrar deneniyor...")
                            response_text = await self._ollama_chat(
                                ollama_model, fallback, j
                            )
                            response_text = re.sub(
                                r"<think>[\s\S]*?</think>", "", response_text,
                                flags=re.IGNORECASE
                            ).strip()
                            if not response_text:
                                raise ValueError("Empty response after retry")
                        except Exception as e2:
                            err_detail2 = f"{type(e2).__name__}: {e2}"
                            print(f"[Ollama Tool Follow-up] Hata (2. deneme): {err_detail2}")
                            j.ui.safe_call(j.ui.write_log, f"ERR: Ollama arac sonrasi yanit veremiyor — {err_detail2[:120]}")
                            j.set_state("ERROR")
                            continue
                    else:
                        j.ui.safe_call(j.ui.write_log, f"ERR: Ollama arac sonrasi yanit veremiyor — {err_detail[:120]}")
                        j.set_state("ERROR")
                        continue

                j.ui.safe_call(j.ui.write_log, f"JARVIS: {response_text}")
                await j._speak_response(response_text)

            else:
                self._history.append({"role": "user", "content": text})
                self._history.append({"role": "assistant", "content": response_text})
                j.ui.safe_call(j.ui.write_log, f"JARVIS: {response_text}")
                await j._speak_response(response_text)

    def _get_model_name(self) -> str:
        """Get model name with auto-select fallback.

        Sirasiyla:
        1. LocalLLM.current_model (runtime secimi)
        2. Config'deki ollama_model (manuel)
        3. auto_select_ollama_model() (sistem kaynagi bazli)
        4. qwen2.5:1.5b (hardcoded fallback)
        """
        llm = self._get_llm()
        if llm is not None:
            name = llm.current_model
            if name:
                return name
        cfg = self._get_config()
        name = cfg.get("ollama_model", "")
        if name:
            return name
        from app_config import auto_select_ollama_model
        return auto_select_ollama_model() or "qwen2.5:1.5b"

    # ── Prompt trimming ─────────────────────────────────────

    @staticmethod
    def _trim_system_prompt(prompt: str) -> str:
        """Strip example conversations – they bloat context for small local models."""
        marker = "ÖRNEK KONUŞMALAR:"
        idx = prompt.find(marker)
        if idx != -1:
            prompt = prompt[:idx].rstrip()
        return prompt

    # ── Ollama HTTP Chat ─────────────────────────────────────

    async def _ollama_chat(
        self, model: str, messages: list, j: Any
    ) -> str:
        """Send messages to Ollama API, return response text."""
        import httpx

        response_text = ""
        timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=10.0)
        num_ctx = self._get_num_ctx()
        chat_opts = {"num_ctx": num_ctx} if num_ctx else {}
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST", "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "keep_alive": "30m",
                    "options": chat_opts,
                },
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise Exception(
                        f"HTTP {resp.status_code}: {body.decode()[:200]}"
                    )

                # Chunked NDJSON reading
                buf = b""
                async for raw_bytes in resp.aiter_bytes():
                    buf += raw_bytes
                    while b"\n" in buf:
                        line_b, buf = buf.split(b"\n", 1)
                        line = line_b.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                response_text += content
                                # Quality warning for small models
                                if any(
                                    w in content.lower()
                                    for w in ["probability", "threshold", "confidence"]
                                ):
                                    if not self._ollama_warned_quality:
                                        self._ollama_warned_quality = True
                                        j.ui.safe_call(j.ui.write_log, "WARN: Mevcut Ollama modeli bazi isteklerde yetersiz kaliyor. Ayarlardan daha buyuk bir model secin (7B+).")
                            done = data.get("done", False)
                            if done:
                                done_reason = data.get("done_reason", "")
                                if done_reason and done_reason not in ("stop", ""):
                                    j.ui.safe_call(j.ui.write_debug, f"Ollama done_reason: {done_reason}", level="WARN")
                        except json.JSONDecodeError:
                            # Partial/incomplete NDJSON chunk — expected during streaming
                            pass
        return response_text

    # ── STT Listen Loop ──────────────────────────────────────

    async def _stt_listen_loop(self):
        """Read 16kHz PCM from orchestrator queue → VAD → STT → input_queue."""
        j = self._j()
        import numpy as np
        import traceback
        from core.audio_system.stt_engine import get_stt_engine

        stt_engine = get_stt_engine()
        if not stt_engine.is_available():
            print("[Ollama STT] UYARI: STT motoru hazir degil!")

        _noise_floor = None
        _noise_frames = []
        FRAME_SIZE = 2048

        print("[Ollama STT] Dinleme başladı (orchestrator pipeline)...")
        _speech_buf = bytearray()
        _silence_start = None
        _is_awake = False

        try:
            while self._running:
                cfg = _load_app_config()
                if j._paused or cfg.get("backend_type", "gemini") != "ollama":
                    await asyncio.sleep(0.1)
                    continue

                # Read 16kHz audio from orchestrator pipeline (non-blocking)
                try:
                    data = await asyncio.wait_for(
                        self._audio_queue.get(), timeout=0.05
                    )
                except asyncio.TimeoutError:
                    continue

                ww = getattr(j, "wake_word", None)

                if j.ui.muted:
                    continue

                # Barge-in: skip if JARVIS is speaking
                barge = getattr(j, "barge_in", None)
                if barge is not None and barge.is_jarvis_speaking():
                    continue

                with j._speaking_lock:
                    js = j._is_speaking
                    sc = time.monotonic() - j._last_speech_end < j._speaking_cooldown
                if js or sc:
                    continue

                # Wake word
                if ww is not None:
                    if j._wake_word_triggered:
                        _is_awake = True
                        j._wake_word_triggered = False
                    if not _is_awake:
                        continue

                j.ui.set_state("LISTENING")

                # VAD (Energy-based)
                arr = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                rms = float(np.sqrt(np.mean(arr ** 2)))

                if _noise_floor is None:
                    _noise_frames.append(rms)
                    if len(_noise_frames) >= 10:
                        _noise_frames.sort()
                        _noise_floor = _noise_frames[len(_noise_frames) // 4]
                        if _noise_floor < 1.0:
                            _noise_floor = 50.0
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
                        elif (time.time() - _silence_start) * 1000 > 500:
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
                                    stt_engine.transcribe, audio_bytes, 16000
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

        except Exception:
            traceback.print_exc()
        finally:
            print("[Ollama STT] Listen loop ended.")
