"""
Monitoring session state manager.
Tracks which patient is currently being monitored, packet counts, and PPS.
Thread-safe in-memory store — no persistence needed (sessions reset on restart).
"""
import time
import threading
from typing import Optional


class SessionManager:
    def __init__(self):
        self._lock = threading.Lock()
        self._active_patient_id: Optional[int] = None
        self._session_start: Optional[float] = None
        self._packet_count: int = 0
        self._last_packet_time: Optional[float] = None
        self._packets_in_window: list = []  # timestamps for PPS calculation

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def start_session(self, patient_id: int):
        with self._lock:
            self._active_patient_id = patient_id
            self._session_start = time.time()
            self._packet_count = 0
            self._packets_in_window = []
            self._last_packet_time = None

    def stop_session(self):
        with self._lock:
            self._active_patient_id = None
            self._session_start = None
            self._packet_count = 0
            self._packets_in_window = []

    def record_packet(self):
        """Call this each time a raw BCG sample arrives."""
        with self._lock:
            if self._active_patient_id is None:
                return
            now = time.time()
            self._packet_count += 1
            self._last_packet_time = now
            self._packets_in_window.append(now)
            # Keep only last 5 seconds of timestamps
            cutoff = now - 5.0
            self._packets_in_window = [t for t in self._packets_in_window if t >= cutoff]

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active_patient_id is not None

    @property
    def active_patient_id(self) -> Optional[int]:
        with self._lock:
            return self._active_patient_id

    def get_status(self) -> dict:
        with self._lock:
            now = time.time()
            pps = len(self._packets_in_window) / 5.0 if self._packets_in_window else 0.0
            elapsed = (now - self._session_start) if self._session_start else 0.0
            return {
                "active": self._active_patient_id is not None,
                "patient_id": self._active_patient_id,
                "session_start": self._session_start,
                "elapsed_seconds": round(elapsed, 1),
                "packet_count": self._packet_count,
                "packets_per_second": round(pps, 2),
            }


# Singleton instance used across the app
session_manager = SessionManager()
