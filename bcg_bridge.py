#!/usr/bin/env python3
"""
BCG Bridge — CSV Tail → Healthcare Backend
==========================================
This script tails live_bcg_output.csv (written by bcg_live.py) and periodically
computes a scan object from the accumulated BCG data, then POSTs it to the
healthcare backend at http://localhost:8001/scan.

It is COMPLETELY DECOUPLED from bcg_live.py:
  - It does NOT import bcg_live.py
  - It does NOT modify bcg_live.py
  - It does NOT share memory with bcg_live.py
  - If bcg_live.py is not running, the bridge simply waits for new rows

Usage:
    python bcg_bridge.py [--csv live_bcg_output.csv] [--backend http://localhost:8001]

The bridge does nothing unless an active monitoring session exists on the backend.
"""
import os
import sys
import csv
import time
import math
import logging
import argparse
import requests
from collections import deque
from datetime import datetime

try:
    import numpy as np
    from scipy.signal import butter, filtfilt, find_peaks, detrend
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | BRIDGE | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bcg_bridge.log")],
)
logger = logging.getLogger("bcg_bridge")

# ── Constants ─────────────────────────────────────────────────────────────────

SCAN_WINDOW_SECONDS = 10       # Accumulate this many seconds of BCG data per scan
POLL_INTERVAL_SECONDS = 0.5    # How often to check for new CSV rows
MIN_SAMPLES_FOR_SCAN = 80      # Minimum samples needed to compute a meaningful scan

# ── Signal Processing ─────────────────────────────────────────────────────────

def _butter_bandpass(lowcut=0.8, highcut=4.0, fs=100.0, order=4):
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut / nyq, min(highcut, nyq - 0.5) / nyq], btype='band')
    return b, a


def compute_scan_metrics(t_arr, ax_arr, ay_arr, az_arr, occ_arr):
    """
    Compute HR, RR, SDNN, RMSSD, signal quality, and motion from a window of BCG data.
    Returns a dict with all physiological metrics, or None if insufficient data.
    """
    if not HAVE_SCIPY or len(t_arr) < MIN_SAMPLES_FOR_SCAN:
        return None

    try:
        t = np.array(t_arr, dtype=float)
        ax = np.array(ax_arr, dtype=float)
        ay = np.array(ay_arr, dtype=float)
        az = np.array(az_arr, dtype=float)
        occ = np.array(occ_arr, dtype=float)

        # Estimate sampling frequency
        dt = np.median(np.diff(t))
        if dt <= 0:
            return None
        fs = 1.0 / dt

        # Occupancy and motion
        occ_val = int(np.round(np.mean(occ)))
        motion_detected = bool(np.std(az) > 150.0)  # large z-variance = motion

        # Filter
        b, a_coef = _butter_bandpass(0.8, 4.0, fs)

        az_dt = detrend(az)
        az_f = filtfilt(b, a_coef, az_dt)

        # Determine best channel by SQS
        best_f = az_f
        best_raw = az_dt
        for ch_raw in [detrend(ax), detrend(ay)]:
            ch_f = filtfilt(b, a_coef, ch_raw)
            n = len(ch_f)
            freqs = np.fft.rfftfreq(n, d=1.0 / fs)
            mags = np.abs(np.fft.rfft(ch_f))
            cardiac_mask = (freqs >= 0.8) & (freqs <= 3.0)
            noise_mask = (freqs > 4.0) & (freqs <= 12.0)
            cpeak = np.max(mags[cardiac_mask]) if np.any(cardiac_mask) else 0
            nmean = np.mean(mags[noise_mask]) if np.any(noise_mask) else 1e-5
            sqs_ch = cpeak / (nmean + 1e-5)

            best_n = len(best_f)
            bf = np.abs(np.fft.rfft(best_f))
            bfreqs = np.fft.rfftfreq(best_n, d=1.0 / fs)
            bcmask = (bfreqs >= 0.8) & (bfreqs <= 3.0)
            bnmask = (bfreqs > 4.0) & (bfreqs <= 12.0)
            bcpeak = np.max(bf[bcmask]) if np.any(bcmask) else 0
            bnmean = np.mean(bf[bnmask]) if np.any(bnmask) else 1e-5
            sqs_best = bcpeak / (bnmean + 1e-5)

            if sqs_ch > sqs_best:
                best_f = ch_f
                best_raw = ch_raw

        # Signal Quality Score
        n = len(best_f)
        freqs = np.fft.rfftfreq(n, d=1.0 / fs)
        mags = np.abs(np.fft.rfft(best_f))
        cmask = (freqs >= 0.8) & (freqs <= 3.0)
        nmask = (freqs > 4.0) & (freqs <= 12.0)
        cpeak = np.max(mags[cmask]) if np.any(cmask) else 0
        nmean = np.mean(mags[nmask]) if np.any(nmask) else 1e-5
        sqs = cpeak / (nmean + 1e-5)

        if sqs >= 8.0:
            signal_quality = "Excellent"
        elif sqs >= 4.0:
            signal_quality = "Good"
        elif sqs >= 2.0:
            signal_quality = "Moderate"
        else:
            signal_quality = "Poor"

        # FFT-based HR
        dom_freq = freqs[cmask][np.argmax(mags[cmask])] if np.any(cmask) else 1.2
        heart_rate = float(np.clip(dom_freq * 60.0, 45.0, 120.0))

        # Peak-based HRV
        prom = 0.25 * np.std(best_f)
        dist = int(0.25 * fs)
        peaks, _ = find_peaks(best_f, distance=dist, prominence=prom)

        sdnn = 0.0
        rmssd = 0.0
        if len(peaks) >= 3:
            beat_times = t[peaks]
            ibis = np.diff(beat_times) * 1000.0  # ms
            valid = ibis[(ibis >= 300) & (ibis <= 1500)]
            if len(valid) >= 2:
                sdnn = float(np.std(valid))
                rmssd = float(np.sqrt(np.mean(np.diff(valid) ** 2)))

        # Respiration: spectral peak in 0.1–0.5 Hz range
        resp_mask = (freqs >= 0.1) & (freqs <= 0.5)
        if np.any(resp_mask):
            resp_freq = freqs[resp_mask][np.argmax(mags[resp_mask])]
            respiration_rate = float(np.clip(resp_freq * 60.0, 8.0, 25.0))
        else:
            respiration_rate = 15.0

        return {
            "heart_rate": round(heart_rate, 1),
            "signal_quality": signal_quality,
        }
    except Exception as e:
        logger.error(f"Signal processing error: {e}")
        return None


# ── CSV Tailing ───────────────────────────────────────────────────────────────

class CSVTailer:
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._file = None
        self._pos = 0

    def open(self):
        """Open (or seek to end of) the CSV file."""
        if os.path.exists(self.csv_path):
            self._file = open(self.csv_path, "r", newline="")
            # Seek to end so we only pick up new rows
            self._file.seek(0, 2)
            self._pos = self._file.tell()
            logger.info(f"Tailing CSV: {self.csv_path} (starting at byte {self._pos})")
        else:
            logger.warning(f"CSV not found: {self.csv_path} — waiting...")

    def read_new_rows(self):
        """Return list of (t_ms, ax, ay, az, occ) tuples from new rows."""
        rows = []
        if self._file is None:
            # Try to open
            if os.path.exists(self.csv_path):
                self.open()
            return rows

        self._file.seek(self._pos)
        new_data = self._file.read()
        if not new_data:
            return rows
        self._pos = self._file.tell()

        for line in new_data.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 4:
                continue
            try:
                # Skip header
                if any(h in parts[0] for h in ["time_ms", "timestamp", "ax"]):
                    continue
                t_ms = float(parts[0])
                ax = float(parts[1])
                ay = float(parts[2])
                az = float(parts[3])
                occ = int(float(parts[4])) if len(parts) > 4 else 1
                if not all(math.isfinite(v) for v in [t_ms, ax, ay, az]):
                    continue
                rows.append((t_ms, ax, ay, az, occ))
            except (ValueError, IndexError):
                continue
        return rows


# ── Main Bridge Loop ──────────────────────────────────────────────────────────

def check_session(backend_url: str) -> int | None:
    """Check if there's an active monitoring session; return patient_id or None."""
    try:
        r = requests.get(f"{backend_url}/live/status", timeout=2)
        if r.status_code == 200:
            data = r.json()
            if data.get("active"):
                return data.get("patient_id")
    except Exception:
        pass
    return None


def post_telemetry(backend_url: str, packets: int, current_hr: float = None):
    """POST lightweight telemetry to the backend."""
    try:
        payload = {"packets_received": packets, "current_heart_rate": current_hr}
        requests.post(f"{backend_url}/session/telemetry", json=payload, timeout=2)
    except Exception:
        pass


def post_scan(backend_url: str, patient_id: int, metrics: dict, lowest_hr: float, highest_hr: float) -> bool:
    """POST a scan to the backend ingest endpoint (no auth required)."""
    payload = {
        "patient_id": patient_id,
        "timestamp": datetime.utcnow().isoformat(),
        "lowest_heart_rate": lowest_hr,
        "highest_heart_rate": highest_hr,
        **metrics,
    }
    try:
        r = requests.post(f"{backend_url}/scan", json=payload, timeout=5)
        if r.status_code == 201:
            scan = r.json()
            logger.info(
                f"Scan saved: id={scan['id']} patient={patient_id} "
                f"HR={metrics.get('heart_rate')} score={scan.get('ai_health_score')}"
            )
            return True
        else:
            logger.error(f"POST /scan failed: {r.status_code} — {r.text[:200]}")
    except Exception as e:
        logger.error(f"Failed to POST scan: {e}")
    return False


def main():
    parser = argparse.ArgumentParser(description="BCG Bridge — CSV tail to Healthcare Backend")
    parser.add_argument("--csv", default="live_bcg_output.csv", help="Path to live CSV file")
    parser.add_argument("--backend", default="http://localhost:8001", help="Healthcare backend URL")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("BCG Bridge starting")
    logger.info(f"  CSV source : {args.csv}")
    logger.info(f"  Backend    : {args.backend}")
    logger.info("=" * 60)
    logger.info("Bridge is fully decoupled from bcg_live.py — safe to run alongside it.")

    tailer = CSVTailer(args.csv)
    tailer.open()

    # Rolling window buffers (10 seconds at ~100Hz = ~1000 samples)
    t_buf = deque()
    ax_buf = deque()
    ay_buf = deque()
    az_buf = deque()
    occ_buf = deque()

    window_start_time = time.time()
    packets_received = 0
    backend_ok = False
    
    # Session tracking variables
    current_patient_id = None
    lowest_hr = None
    highest_hr = None
    sq_history = deque(maxlen=3)

    while True:
        try:
            # 1. Read new CSV rows
            new_rows = tailer.read_new_rows()
            new_packets = 0
            for (t_ms, ax, ay, az, occ) in new_rows:
                t_buf.append(t_ms / 1000.0)
                ax_buf.append(ax)
                ay_buf.append(ay)
                az_buf.append(az)
                occ_buf.append(occ)
                packets_received += 1
                new_packets += 1

            # 3. Check for active session
            patient_id = check_session(args.backend)
            if patient_id != current_patient_id:
                # If session stopped, flush the remaining buffer to a final scan
                if current_patient_id is not None and len(t_buf) >= MIN_SAMPLES_FOR_SCAN:
                    logger.info("Session stopped. Flushing remaining buffer to a final scan.")
                    metrics = compute_scan_metrics(
                        list(t_buf), list(ax_buf), list(ay_buf), list(az_buf), list(occ_buf)
                    )
                    if metrics:
                        # Fallback quality if history exists
                        if len(sq_history) > 0:
                            metrics["signal_quality"] = sq_history[0]
                        post_scan(args.backend, current_patient_id, metrics, lowest_hr, highest_hr)

                # Session changed or reset
                current_patient_id = patient_id
                lowest_hr = None
                highest_hr = None
                sq_history.clear()
                t_buf.clear()
                ax_buf.clear()
                ay_buf.clear()
                az_buf.clear()
                occ_buf.clear()
                window_start_time = time.time()
            
            # Post telemetry if we read new rows
            if new_packets > 0 and current_patient_id:
                # estimate current HR if we have enough data (rough fast calc)
                temp_hr = None
                if len(t_buf) >= MIN_SAMPLES_FOR_SCAN:
                    m = compute_scan_metrics(list(t_buf), list(ax_buf), list(ay_buf), list(az_buf), list(occ_buf))
                    if m:
                        temp_hr = m.get("heart_rate")
                        if temp_hr:
                            if lowest_hr is None or temp_hr < lowest_hr: lowest_hr = temp_hr
                            if highest_hr is None or temp_hr > highest_hr: highest_hr = temp_hr
                post_telemetry(args.backend, new_packets, temp_hr)

            # 2. Check if we've accumulated a full scan window
            elapsed = time.time() - window_start_time
            if elapsed >= SCAN_WINDOW_SECONDS and len(t_buf) >= MIN_SAMPLES_FOR_SCAN:
                if current_patient_id:
                    metrics = compute_scan_metrics(
                        list(t_buf), list(ax_buf), list(ay_buf), list(az_buf), list(occ_buf)
                    )
                    if metrics:
                        # Apply Hysteresis to Signal Quality
                        sq_history.append(metrics["signal_quality"])
                        # Only change quality if it has been consistently different
                        if len(sq_history) == sq_history.maxlen and len(set(sq_history)) == 1:
                            # stable
                            pass
                        else:
                            # fallback to previous or most common
                            metrics["signal_quality"] = sq_history[0] if len(sq_history) > 0 else "Good"

                        post_scan(args.backend, current_patient_id, metrics, lowest_hr, highest_hr)
                    else:
                        logger.warning("Insufficient signal quality for scan — skipping window.")
                else:
                    logger.debug("No active monitoring session — scan window discarded.")

                # Reset window
                t_buf.clear()
                ax_buf.clear()
                ay_buf.clear()
                az_buf.clear()
                occ_buf.clear()
                window_start_time = time.time()

            # Log status periodically
            if packets_received % 500 == 0 and packets_received > 0:
                logger.info(f"Packets tailed so far: {packets_received}, buffer: {len(t_buf)} samples")

        except KeyboardInterrupt:
            logger.info("Bridge stopped by user.")
            break
        except Exception as e:
            logger.error(f"Bridge loop error: {e}")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
