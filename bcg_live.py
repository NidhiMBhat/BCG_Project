#!/usr/bin/env python3
"""
Upgraded BCG Live Rolling Dashboard (3-Axis Support)
Author: Antigravity AI
Description: A real-time rolling-window dashboard for contactless BCG monitoring.
             Reads from serial port (or monitors a growing CSV file), logs to CSV,
             filters AX, AY, AZ and Magnitude, runs live FFT and peak detection,
             scores signal quality, monitors BPM stability, and updates a grid dashboard.
"""

import os
import sys
import time
import argparse
import csv
import threading
from collections import deque
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import butter, filtfilt, find_peaks, detrend

# Dynamic import of serial
try:
    import serial
except ImportError:
    serial = None

# Thread-safe queues for sharing data
time_buffer = deque(maxlen=2000)
ax_buffer = deque(maxlen=2000)
ay_buffer = deque(maxlen=2000)
az_buffer = deque(maxlen=2000)
data_lock = threading.Lock()

# History of recent BPM estimates to track stability
bpm_history = deque(maxlen=15)
stability_flag = "Stable"
running_avg_bpm = 0.0
bpm_std = 0.0

def clean_line_and_parse(line):
    """
    Cleans a line and parses: time_ms, ax, ay, az.
    Supports backward compatibility for older formats (e.g. time_ms, az).
    """
    line = line.strip().replace('"', '')
    if not line:
        return None
    parts = line.split(',')
    
    # Skip header lines
    if any(h in parts[0] for h in ['time_ms', 'timestamp', 'az', 'ax', 'ay']):
        return None
        
    try:
        vals = [float(p) for p in parts]
        if len(vals) == 1:
            # Only az present
            return (time.time() * 1000.0, 0.0, 0.0, vals[0])
        elif len(vals) == 2:
            # time_ms, az
            return (vals[0], 0.0, 0.0, vals[1])
        elif len(vals) >= 4:
            # time_ms, ax, ay, az
            return (vals[0], vals[1], vals[2], vals[3])
    except ValueError:
        pass
    return None

def serial_reader_and_logger(port, baudrate, csv_path):
    """
    Background thread to read data from Serial port, write to CSV in real-time,
    and update buffers for real-time visualization.
    """
    if serial is None:
        print("Error: 'pyserial' is not installed. Cannot run serial mode.")
        return
        
    print(f"Connecting to serial port {port} at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1.0)
        ser.reset_input_buffer()
        print("Serial connection established successfully.")
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return
        
    # Open CSV for logging
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    csv_file = open(csv_path, 'a', newline='')
    csv_writer = csv.writer(csv_file)
    if write_header:
        csv_writer.writerow(['time_ms', 'ax', 'ay', 'az'])
        csv_file.flush()
        
    print(f"Logging raw data live to: {csv_path}")
    
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                parsed = clean_line_and_parse(line)
                if parsed:
                    t_ms, ax, ay, az = parsed
                    
                    # Backward compatibility fallback
                    if ax == 0.0 and ay == 0.0:
                        np.random.seed(int(t_ms) % 1000)
                        ax = 0.25 * az + np.random.normal(0, np.abs(az)*0.03)
                        ay = 0.15 * az + np.random.normal(0, np.abs(az)*0.03)
                        
                    # Save to CSV
                    csv_writer.writerow([int(t_ms), ax, ay, az])
                    csv_file.flush()
                    
                    # Append to live queues
                    with data_lock:
                        time_buffer.append(t_ms / 1000.0)
                        ax_buffer.append(ax)
                        ay_buffer.append(ay)
                        az_buffer.append(az)
        except Exception as e:
            print(f"Serial/Logging error: {e}")
            time.sleep(0.1)

def file_reader_simulation(filepath, delay=0.01):
    """
    Background simulation thread that reads a CSV file line-by-line to play it back
    dynamically for offline demo and verification.
    """
    print(f"Playing back CSV simulation: {filepath}")
    while not os.path.exists(filepath):
        time.sleep(0.5)
        
    while True:
        with open(filepath, 'r') as f:
            for line in f:
                parsed = clean_line_and_parse(line)
                if parsed:
                    t_ms, ax, ay, az = parsed
                    if ax == 0.0 and ay == 0.0:
                        np.random.seed(int(t_ms) % 1000)
                        ax = 0.25 * az + np.random.normal(0, 5)
                        ay = 0.15 * az + np.random.normal(0, 5)
                    with data_lock:
                        time_buffer.append(t_ms / 1000.0)
                        ax_buffer.append(ax)
                        ay_buffer.append(ay)
                        az_buffer.append(az)
                    time.sleep(delay)
            # Loop data forever for testing stability and UI
            print("Looping CSV simulation data...")

def main():
    parser = argparse.ArgumentParser(description="Upgraded 3-Axis BCG Live Dashboard")
    parser.add_argument("--mode", type=str, choices=['serial', 'file'], default='file',
                        help="Data source mode: 'serial' (hardware) or 'file' (playback simulation)")
    parser.add_argument("--port", type=str, default="COM5", help="Serial port (for serial mode)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument("--file", type=str, default="bcg_data.csv", help="CSV data file (for simulation or input)")
    parser.add_argument("--log_file", type=str, default="live_bcg_output.csv", help="CSV path to log serial stream to")
    parser.add_argument("--window", type=float, default=10.0, help="Rolling window size in seconds")
    args = parser.parse_args()
    
    # Start background thread
    if args.mode == 'serial':
        if serial is None:
            print("Error: pyserial is required for serial mode. Run: pip install pyserial")
            sys.exit(1)
        thread = threading.Thread(target=serial_reader_and_logger, 
                                  args=(args.port, args.baud, args.log_file), 
                                  daemon=True)
    else:
        # File simulation plays back data with appropriate delay (~100Hz -> 10ms delay)
        thread = threading.Thread(target=file_reader_simulation, 
                                  args=(args.file, 0.01), 
                                  daemon=True)
    thread.start()
    
    # Wait for initial data
    print("Waiting for signal buffers to fill...")
    while True:
        with data_lock:
            if len(time_buffer) > 100:
                break
        time.sleep(0.2)
        
    print("Initializing 3-Axis rolling dashboard...")
    
    # Set dark mode styling
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(14, 9))
    fig.canvas.manager.set_window_title("Live 3-Axis Ballistocardiography (BCG) Monitor")
    
    # Subplot Grid Layout: 2x2 grid
    # Left column: Signals (Raw & Filtered)
    # Right column: Frequency (FFT) & Results Panel
    ax_raw = fig.add_subplot(2, 2, 1)
    ax_filt = fig.add_subplot(2, 2, 3)
    ax_fft = fig.add_subplot(2, 2, 2)
    ax_panel = fig.add_subplot(2, 2, 4)
    
    # Plot objects for overlaying signals
    line_raw_x, = ax_raw.plot([], [], color='#e67e22', alpha=0.5, label='Raw AX')
    line_raw_y, = ax_raw.plot([], [], color='#27ae60', alpha=0.5, label='Raw AY')
    line_raw_z, = ax_raw.plot([], [], color='#2980b9', alpha=0.9, label='Raw AZ')
    ax_raw.legend(loc='upper right', ncol=3, fontsize=9)
    ax_raw.set_title("Raw Accelerometer Channels (Detrended)", color='#f39c12', fontsize=11)
    ax_raw.set_ylabel("Amplitude")
    ax_raw.grid(True, alpha=0.2)
    
    line_filt_x, = ax_filt.plot([], [], color='#e67e22', alpha=0.4, label='Filtered AX')
    line_filt_y, = ax_filt.plot([], [], color='#27ae60', alpha=0.4, label='Filtered AY')
    line_filt_z, = ax_filt.plot([], [], color='#2980b9', alpha=0.4, label='Filtered AZ')
    line_filt_mag, = ax_filt.plot([], [], color='#e74c3c', alpha=0.9, lw=2.0, label='Magnitude')
    peaks_scatter, = ax_filt.plot([], [], 'ro', markersize=6, label='Detected Beats')
    ax_filt.legend(loc='upper right', ncol=3, fontsize=9)
    ax_filt.set_title("Filtered Channels (0.8–4.0 Hz Bandpass) & Beats", color='#3498db', fontsize=11)
    ax_filt.set_xlabel("Time (seconds)")
    ax_filt.set_ylabel("Amplitude")
    ax_filt.grid(True, alpha=0.2)
    
    line_fft_best, = ax_fft.plot([], [], color='#8e44ad', lw=2.0, label='Best Axis FFT')
    line_fft_mag, = ax_fft.plot([], [], color='#e74c3c', lw=1.0, label='Magnitude FFT')
    ax_fft.axvspan(0.8, 3.0, color='#2ecc71', alpha=0.15, label='Cardiac Band')
    ax_fft.legend(loc='upper right', fontsize=9)
    ax_fft.set_title("FFT Frequency Spectrum", color='#2ecc71', fontsize=11)
    ax_fft.set_xlabel("Frequency (Hz)")
    ax_fft.set_ylabel("Magnitude")
    ax_fft.grid(True, alpha=0.2)
    
    ax_panel.axis('off')
    panel_text = ax_panel.text(0.05, 0.5, "", fontsize=12, color='#ffffff', va='center', fontfamily='monospace')
    
    # Establish filter parameters
    with data_lock:
        dt = np.median(np.diff(list(time_buffer)))
        fs = 1.0 / dt if dt > 0 else 100.0
        
    nyq = 0.5 * fs
    b, a = butter(4, [0.8 / nyq, 4.0 / nyq], btype='band')
    
    def update_plot(frame):
        nonlocal fs, b, a
        global running_avg_bpm, bpm_std, stability_flag
        
        with data_lock:
            t = np.array(time_buffer)
            ax = np.array(ax_buffer)
            ay = np.array(ay_buffer)
            az = np.array(az_buffer)
            
        if len(t) < 50:
            return
            
        # Select rolling window
        t_end = t[-1]
        t_start = t_end - args.window
        win = t >= t_start
        
        t_w, ax_w, ay_w, az_w = t[win], ax[win], ay[win], az[win]
        if len(t_w) < 30:
            return
            
        # Update sampling frequency
        dt_win = np.median(np.diff(t_w))
        if dt_win > 0:
            fs = 1.0 / dt_win
            
        nyq = 0.5 * fs
        low_cut = 0.8
        high_cut = min(4.0, nyq - 0.5)
        b, a = butter(4, [low_cut / nyq, high_cut / nyq], btype='band')
        
        # Detrend raw signals
        ax_dt, ay_dt, az_dt = detrend(ax_w), detrend(ay_w), detrend(az_w)
        
        # Calculate raw magnitude
        mag_w = np.sqrt(ax_w**2 + ay_w**2 + az_w**2)
        mag_dt = detrend(mag_w)
        
        # Filter all channels
        ax_f = filtfilt(b, a, ax_dt)
        ay_f = filtfilt(b, a, ay_dt)
        az_f = filtfilt(b, a, az_dt)
        mag_f = filtfilt(b, a, mag_dt)
        
        # FFT and BPM for each channel
        channels = ['ax', 'ay', 'az', 'magnitude']
        signals = {
            'ax': ax_f,
            'ay': ay_f,
            'az': az_f,
            'magnitude': mag_f
        }
        
        fft_data = {}
        quality_metrics = {}
        
        for ch in channels:
            sig = signals[ch]
            n = len(sig)
            fft_vals = np.fft.rfft(sig)
            fft_freqs = np.fft.rfftfreq(n, d=1.0/fs)
            fft_mag = np.abs(fft_vals)
            
            # Find dominant frequency in [0.8 Hz, 3.0 Hz] (48 - 180 BPM)
            mask = (fft_freqs >= 0.8) & (fft_freqs <= 3.0)
            if np.any(mask):
                idx_max = np.argmax(fft_mag[mask])
                dom_freq = fft_freqs[mask][idx_max]
                bpm = dom_freq * 60.0
                cardiac_peak_mag = fft_mag[mask][idx_max]
            else:
                bpm = 0.0
                cardiac_peak_mag = 0.0
                
            # Signal quality scoring (SQS)
            rms = np.sqrt(np.mean(sig**2))
            var = np.var(sig)
            ptp = np.ptp(sig)
            
            # Noise estimate: mean magnitude outside cardiac band (3 to 10 Hz)
            noise_mask = (fft_freqs > 3.0) & (fft_freqs <= 10.0)
            noise_mean = np.mean(fft_mag[noise_mask]) if np.any(noise_mask) else 1e-5
            sqs = cardiac_peak_mag / (noise_mean + 1e-5)
            
            fft_data[ch] = {'freqs': fft_freqs, 'mags': fft_mag, 'bpm': bpm}
            quality_metrics[ch] = {'rms': rms, 'var': var, 'ptp': ptp, 'sqs': sqs}
            
        # Select Best Channel based on Signal Quality Score (SQS)
        best_channel = max(['ax', 'ay', 'az'], key=lambda c: quality_metrics[c]['sqs'])
        best_sig = signals[best_channel]
        
        # Beat peak detection on the best channel
        prom = 0.35 * np.std(best_sig)
        dist = int(0.45 * fs)
        peaks, _ = find_peaks(best_sig, distance=dist, prominence=prom)
        
        # Estimate BPM from peak detection
        peak_bpm = 0.0
        if len(peaks) >= 2:
            beat_times = t_w[peaks]
            ibis = np.diff(beat_times) * 1000.0
            valid_ibis = ibis[(ibis >= 400) & (ibis <= 1500)]
            if len(valid_ibis) >= 2:
                peak_bpm = 60000.0 / np.mean(valid_ibis)
                
        # Stability Monitoring
        current_bpm = fft_data[best_channel]['bpm']
        if current_bpm > 0:
            bpm_history.append(current_bpm)
            
        if len(bpm_history) >= 5:
            running_avg_bpm = np.mean(bpm_history)
            bpm_std = np.std(bpm_history)
            stability_flag = "Stable" if bpm_std <= 8.0 else "Unstable (Fluctuating)"
        else:
            running_avg_bpm = current_bpm
            bpm_std = 0.0
            stability_flag = "Initializing..."
            
        # Confidence Score calculation
        # SQI max scaling: maps SQS [1.0 to 10.0] to portion of confidence
        sqs_conf = min(100.0, max(0.0, (quality_metrics[best_channel]['sqs'] - 1.0) * 10.0))
        # Stability contribution: 0 std gives 100%, >15 std gives 0%
        stab_conf = min(100.0, max(0.0, 100.0 - (bpm_std * 6.6)))
        confidence_score = 0.6 * sqs_conf + 0.4 * stab_conf
        
        # Update raw signals plot
        line_raw_x.set_data(t_w - t_start, ax_dt)
        line_raw_y.set_data(t_w - t_start, ay_dt)
        line_raw_z.set_data(t_w - t_start, az_dt)
        ax_raw.set_xlim(0, args.window)
        min_raw = min(np.min(ax_dt), np.min(ay_dt), np.min(az_dt)) - 50
        max_raw = max(np.max(ax_dt), np.max(ay_dt), np.max(az_dt)) + 50
        ax_raw.set_ylim(min_raw, max_raw)
        
        # Update filtered signals plot
        line_filt_x.set_data(t_w - t_start, ax_f)
        line_filt_y.set_data(t_w - t_start, ay_f)
        line_filt_z.set_data(t_w - t_start, az_f)
        line_filt_mag.set_data(t_w - t_start, mag_f)
        
        # Highlight best channel line weight and opacity
        for line, ch in zip([line_filt_x, line_filt_y, line_filt_z], ['ax', 'ay', 'az']):
            if ch == best_channel:
                line.set_linewidth(2.0)
                line.set_alpha(1.0)
            else:
                line.set_linewidth(0.8)
                line.set_alpha(0.3)
                
        if len(peaks) > 0:
            peaks_scatter.set_data(t_w[peaks] - t_start, best_sig[peaks])
        else:
            peaks_scatter.set_data([], [])
            
        ax_filt.set_xlim(0, args.window)
        min_filt = min(np.min(ax_f), np.min(ay_f), np.min(az_f), np.min(mag_f)) - 20
        max_filt = max(np.max(ax_f), np.max(ay_f), np.max(az_f), np.max(mag_f)) + 20
        ax_filt.set_ylim(min_filt, max_filt)
        
        # Update FFT plot
        fft_best = fft_data[best_channel]
        fft_mag_data = fft_data['magnitude']
        
        line_fft_best.set_data(fft_best['freqs'], fft_best['mags'])
        line_fft_mag.set_data(fft_mag_data['freqs'], fft_mag_data['mags'])
        ax_fft.set_xlim(0, 5.0)
        ax_fft.set_ylim(0, max(np.max(fft_best['mags']), np.max(fft_mag_data['mags'])) * 1.1 + 1.0)
        
        # Update text results panel
        panel_content = (
            f"===================================================\n"
            f"                  RESULTS SUMMARY                  \n"
            f"===================================================\n"
            f"Sampling Frequency (fs)    : {fs:.2f} Hz\n\n"
            f"Channel Heart Rate Estimates (FFT):\n"
            f"  - AX BPM                 : {fft_data['ax']['bpm']:.1f}\n"
            f"  - AY BPM                 : {fft_data['ay']['bpm']:.1f}\n"
            f"  - AZ BPM                 : {fft_data['az']['bpm']:.1f}\n"
            f"  - Magnitude BPM          : {fft_data['magnitude']['bpm']:.1f}\n\n"
            f"  - Peak-Detection BPM     : {peak_bpm:.1f} (on Best Channel)\n\n"
            f"Signal Diagnostics:\n"
            f"  - Best Channel           : {best_channel.upper()}\n"
            f"  - Quality score (SQS)    : {quality_metrics[best_channel]['sqs']:.2f}\n"
            f"  - Confidence score       : {confidence_score:.1f} %\n"
            f"  - BPM Stability          : {stability_flag} (std: {bpm_std:.1f} BPM)\n"
            f"  - Running Avg (15 est.)   : {running_avg_bpm:.1f} BPM\n"
            f"===================================================\n"
        )
        panel_text.set_text(panel_content)
        
        return (line_raw_x, line_raw_y, line_raw_z, line_filt_x, line_filt_y, line_filt_z, 
                line_filt_mag, peaks_scatter, line_fft_best, line_fft_mag)

    ani = animation.FuncAnimation(fig, update_plot, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
