"""
Camera Capture — OpenCV ile kamera yönetimi.
Fotoğraf çekme, video akışı, yüz tespiti.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

import traceback

__all__ = ["CameraCapture", "create_camera_capture"]

BASE_DIR = Path(__file__).resolve().parent.parent
_CAPTURE_DIR = BASE_DIR / "captures"


class CameraCapture:
    """
    OpenCV tabanlı kamera yönetimi.

    Özellikler:
    - Fotoğraf çekme
    - Video kaydı (opsiyonel)
    - Otomatik bellek yönetimi
    - Çoklu kamera desteği
    """

    def __init__(self, camera_id: int = 0, width: int = 640, height: int = 480):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self._cap = None
        self._is_open = False
        _CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def open(self) -> bool:
        """Open camera connection."""
        if self._is_open:
            return True
        try:
            import cv2
            self._cap = cv2.VideoCapture(self.camera_id)
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

            if not self._cap.isOpened():
                print(f"[Camera] Kamera {self.camera_id} acilamadi")
                return False

            # Warm-up: read a few frames to let camera stabilize
            for _ in range(5):
                self._cap.read()

            self._is_open = True
            print(f"[Camera] Kamera {self.camera_id} acildi ({self.width}x{self.height})")
            return True
        except ImportError:
            print("[Camera] OpenCV (cv2) kurulu degil. pip install opencv-python")
            return False
        except Exception:
            traceback.print_exc()
            return False

    def close(self):
        """Release camera."""
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                traceback.print_exc()
        self._is_open = False
        self._cap = None
        print("[Camera] Kamera kapatildi")

    # ── Capture ──────────────────────────────────────────────────────────────

    def capture(self) -> Optional[bytes]:
        """
        Take a photo and return JPEG bytes.

        Returns:
            JPEG image bytes or None on failure.
        """
        if not self._is_open and not self.open():
            return None

        try:
            import cv2
            ret, frame = self._cap.read()
            if not ret or frame is None:
                print("[Camera] Goruntu alinamadi")
                return None

            # Encode to JPEG
            success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not success:
                return None

            return buffer.tobytes()
        except Exception:
            traceback.print_exc()
            return None

    def capture_to_file(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Take a photo and save to file.

        Args:
            filename: Output filename (default: auto-generated)

        Returns:
            File path or None.
        """
        img_bytes = self.capture()
        if img_bytes is None:
            return None

        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"

        file_path = _CAPTURE_DIR / filename
        try:
            file_path.write_bytes(img_bytes)
            print(f"[Camera] Fotograf kaydedildi: {file_path}")
            return str(file_path)
        except Exception:
            traceback.print_exc()
            return None

    # ── Info ─────────────────────────────────────────────────────────────────

    @property
    def is_open(self) -> bool:
        return self._is_open

    def get_stats(self) -> dict[str, Any]:
        return {
            "camera_id": self.camera_id,
            "resolution": f"{self.width}x{self.height}",
            "is_open": self._is_open,
            "capture_dir": str(_CAPTURE_DIR),
        }


# ── Factory ──────────────────────────────────────────────────────────────────


def create_camera_capture(camera_id: int = 0) -> CameraCapture:
    """Create a CameraCapture instance."""
    return CameraCapture(camera_id=camera_id)
