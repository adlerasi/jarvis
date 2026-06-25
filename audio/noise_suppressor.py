"""
audio/noise_suppressor.py
JARVIS RNNoise gerçek zamanlı gürültü bastırma modülü.
Cross-platform (Windows/Linux/macOS), thread-safe, fallback'li.

RNNoise C kütüphanesini ctypes ile sarar.
Beklenen format:
  - Sample rate: 48 kHz
  - Frame size: 480 sample (10 ms)
  - Input: int16 numpy array (mono)
  - Output: int16 numpy array (mono)
"""

from __future__ import annotations

import ctypes
import logging
import platform
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)


class NoiseSuppressor:
    """RNNoise gürültü bastırıcı.

    Kullanım:
        ns = NoiseSuppressor(sample_rate=48000)
        if ns.enabled:
            clean = ns.process_frame(noisy_int16_frame)   # (480,) int16
        # veya 16kHz için:
        clean = ns.process_16khz(noisy_int16_frame_16k)   # (480,) int16
    """

    # RNNoise sabitleri
    SAMPLE_RATE: int = 48000
    FRAME_SIZE: int = 480  # 10 ms @ 48 kHz
    SUPPORTED_RATES: tuple[int, ...] = (48000, 44100, 22050, 16000)

    def __init__(
        self,
        sample_rate: int = 48000,
        enabled: bool = True,
        lib_dir: str | Path | None = None,
    ):
        self.sample_rate: int = sample_rate
        self._native_mode: bool = sample_rate == self.SAMPLE_RATE
        self.enabled: bool = enabled and sample_rate in self.SUPPORTED_RATES
        self._lib_dir: str | Path | None = lib_dir
        self._lib: ctypes.CDLL | None = None
        self._state: ctypes.c_void_p | None = None
        self._vad_prob: float = 0.0
        self._init_attempted: bool = False

        if not self.enabled:
            logger.warning(
                "[RNNoise] Devre dışı veya desteklenmeyen sample rate: %s Hz. "
                "Bypass modu aktif. Gürültü bastırma yapılmayacak.",
                sample_rate,
            )

    # ── Lazy Initialization ─────────────────────────────────────────────────

    def _ensure_loaded(self) -> bool:
        """Deferred RNNoise library load — called on first process_frame call."""
        if self._init_attempted:
            return self.enabled and self._lib is not None
        self._init_attempted = True
        if not self.enabled:
            return False
        try:
            self._lib = self._load_library(self._lib_dir)
            self._state = self._lib.rnnoise_create(None)
            if not self._state:
                raise RuntimeError("rnnoise_create NULL döndürdü.")
            logger.info("[RNNoise] Gürültü bastırma başarıyla yüklendi (lazy).")
            return True
        except Exception as exc:
            logger.error("[RNNoise] Yükleme hatası: %s. Bypass moduna geçiliyor.", exc)
            self.enabled = False
            self._cleanup()
            return False

    # ── Kütüphane Yükleme ──────────────────────────────────────────────────

    def _load_library(self, lib_dir: str | Path | None) -> ctypes.CDLL:
        system = platform.system()

        if lib_dir is None:
            lib_dir = Path(__file__).parent / "lib"
        else:
            lib_dir = Path(lib_dir)

        candidates: list[Path] = []
        if system == "Windows":
            candidates = [
                lib_dir / "rnnoise.dll",
                lib_dir / "rnnoise_x64.dll",
            ]
        elif system == "Darwin":
            candidates = [
                lib_dir / "librnnoise.dylib",
                lib_dir / "librnnoise.0.dylib",
            ]
        else:  # Linux ve diğer Unix
            candidates = [
                lib_dir / "librnnoise.so",
                lib_dir / "librnnoise.so.0",
                Path("/usr/local/lib/librnnoise.so"),
                Path("/usr/lib/librnnoise.so"),
                Path("/usr/lib/x86_64-linux-gnu/librnnoise.so"),
                Path("/usr/lib/aarch64-linux-gnu/librnnoise.so"),
            ]

        lib: ctypes.CDLL | None = None
        for candidate in candidates:
            if candidate.exists():
                try:
                    lib = ctypes.CDLL(str(candidate))
                    logger.debug("[RNNoise] Kütüphane yüklendi: %s", candidate)
                    break
                except OSError:
                    continue

        if lib is None:
            raise RuntimeError(
                f"RNNoise kütüphanesi bulunamadı. Aranan yerler: {candidates}. "
                f"Lütfen 'python scripts/install_rnnoise.py' çalıştırın veya "
                f"sistem paket yöneticisiyle kurun."
            )

        # Fonksiyon imzaları
        lib.rnnoise_create.argtypes = [ctypes.c_void_p]
        lib.rnnoise_create.restype = ctypes.c_void_p

        lib.rnnoise_destroy.argtypes = [ctypes.c_void_p]
        lib.rnnoise_destroy.restype = None

        lib.rnnoise_process_frame.argtypes = [
            ctypes.c_void_p,  # DenoiseState
            ctypes.POINTER(ctypes.c_float),  # out (clean)
            ctypes.POINTER(ctypes.c_float),  # in (noisy)
        ]
        lib.rnnoise_process_frame.restype = ctypes.c_float  # VAD prob

        return lib

    # ── İşleme ──────────────────────────────────────────────────────────────

    def process_frame(self, pcm_int16: np.ndarray) -> np.ndarray:
        """Tek bir 480-sample'lık (10 ms) int16 frame'i temizler.

        Args:
            pcm_int16: (480,) şeklinde int16 numpy array, 48 kHz.

        Returns:
            (480,) şeklinde int16 temizlenmiş numpy array.
        """
        if not self.enabled:
            return pcm_int16

        if not self._ensure_loaded():
            return pcm_int16

        if len(pcm_int16) != self.FRAME_SIZE:
            raise ValueError(
                f"Frame boyutu {self.FRAME_SIZE} olmalı, gelen: {len(pcm_int16)}"
            )

        # int16 -> float32 (-1.0 .. 1.0 aralığında)
        in_float = pcm_int16.astype(np.float32) / 32768.0
        out_float = np.zeros(self.FRAME_SIZE, dtype=np.float32)

        # C fonksiyonu çağrımı
        self._vad_prob = self._lib.rnnoise_process_frame(
            self._state,
            out_float.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            in_float.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        )

        # float32 -> int16
        return (out_float * 32768.0).astype(np.int16)

    def process_16khz(self, pcm_int16_16k: np.ndarray) -> np.ndarray:
        """16 kHz'deki 480-sample (30ms) frame'i temizler.

        Dahili olarak 48 kHz'e upsampling yapar, RNNoise ile işler,
        sonra 16 kHz'e downsampling yapar.

        Args:
            pcm_int16_16k: (480,) şeklinde int16 numpy array, 16 kHz.

        Returns:
            (480,) şeklinde int16 temizlenmiş numpy array, 16 kHz.
        """
        if not self.enabled:
            return pcm_int16_16k

        if not self._ensure_loaded():
            return pcm_int16_16k

        in_float = pcm_int16_16k.astype(np.float32) / 32768.0
        upsampled = np.repeat(in_float, 3)

        # 1440 sample = 3 RNNoise frame (480 * 3)
        frame_out = np.zeros(1440, dtype=np.float32)
        for i in range(3):
            chunk = upsampled[i * 480 : (i + 1) * 480]
            chunk_out = np.zeros(480, dtype=np.float32)
            self._vad_prob = self._lib.rnnoise_process_frame(
                self._state,
                chunk_out.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
                chunk.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
            )
            frame_out[i * 480 : (i + 1) * 480] = chunk_out

        # 48 kHz -> 16 kHz (decimate: her 3'te bir al)
        downsampled = frame_out[::3]

        return (downsampled * 32768.0).astype(np.int16)

    def process_stream(
        self,
        audio_float32: np.ndarray,
        original_rate: int | None = None,
    ) -> np.ndarray:
        """Uzun bir float32 audio buffer'ını frame frame temizler.

        Args:
            audio_float32: (N,) şeklinde float32 numpy array, mono.
            original_rate: Kaynak sample rate. 48 kHz değilse bypass.

        Returns:
            (N,) şeklinde float32 temizlenmiş numpy array.
        """
        if not self.enabled:
            return audio_float32

        if not self._ensure_loaded():
            return audio_float32

        if original_rate and original_rate != self.SAMPLE_RATE:
            logger.warning(
                "[RNNoise] %d Hz ses bypass ediliyor (sadece 48 kHz desteklenir).",
                original_rate,
            )
            return audio_float32

        # float32 -> int16
        pcm = (audio_float32 * 32767.0).astype(np.int16)
        n = len(pcm)

        # FRAME_SIZE katı olacak şekilde padding
        remainder = n % self.FRAME_SIZE
        if remainder != 0:
            pad_len = self.FRAME_SIZE - remainder
            pcm = np.pad(pcm, (0, pad_len), mode="constant")

        frames = pcm.reshape(-1, self.FRAME_SIZE)
        clean_frames = np.stack([self.process_frame(f) for f in frames], axis=0)
        clean = clean_frames.flatten()[:n]

        # int16 -> float32
        return clean.astype(np.float32) / 32767.0

    @property
    def vad_probability(self) -> float:
        """Son işlenen frame'in Voice Activity Detection olasılığı (0.0 - 1.0)."""
        return float(self._vad_prob)

    # ── Temizlik ────────────────────────────────────────────────────────────

    def _cleanup(self) -> None:
        if self._lib and self._state:
            try:
                self._lib.rnnoise_destroy(self._state)
            except Exception:
                pass
        self._state = None
        self._lib = None

    def __del__(self):
        self._cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()
        return False
