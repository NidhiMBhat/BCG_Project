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
        
        self.lowest_heart_rate: Optional[float] = None
        self.highest_heart_rate: Optional[float] = None

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
            self.lowest_heart_rate = None
            self.highest_heart_rate = None

    def stop_session(self) -> Optional[dict]:
        with self._lock:
            if not self._active_patient_id:
                return None
            
            # Capture data to return before clearing
            summary = {
                "patient_id": self._active_patient_id,
                "start_time": self._session_start,
                "packet_count": self._packet_count,
                "lowest_heart_rate": self.lowest_heart_rate,
                "highest_heart_rate": self.highest_heart_rate
            }

            self._active_patient_id = None
            self._session_start = None
            self._packet_count = 0
            self._packets_in_window = []
            self.lowest_heart_rate = None
            self.highest_heart_rate = None
            
            return summary

    def record_telemetry(self, packets_received: int, current_hr: Optional[float]):
        """Call this periodically from the bridge."""
        with self._lock:
            if self._active_patient_id is None:
                return
            now = time.time()
            
            # Record packets for PPS
            self._packet_count += packets_received
            self._last_packet_time = now
            for _ in range(packets_received):
                self._packets_in_window.append(now)
            
            # Keep only last 5 seconds of timestamps for PPS
            cutoff = now - 5.0
            self._packets_in_window = [t for t in self._packets_in_window if t >= cutoff]
            
            # Update HR bounds
            if current_hr is not None and current_hr > 0:
                if self.lowest_heart_rate is None or current_hr < self.lowest_heart_rate:
                    self.lowest_heart_rate = current_hr
                if self.highest_heart_rate is None or current_hr > self.highest_heart_rate:
                    self.highest_heart_rate = current_hr

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
                "lowest_heart_rate": self.lowest_heart_rate,
                "highest_heart_rate": self.highest_heart_rate,
            }


# Singleton instance used across the app
session_manager = SessionManager()

