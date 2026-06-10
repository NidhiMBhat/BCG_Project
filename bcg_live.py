#!/usr/bin/env python3
"""
BCG Live Rolling Dashboard
Author: Antigravity AI
Description: A real-time rolling-window dashboard for contactless BCG monitoring.
             Reads from serial port (or monitors a growing CSV file), filters the signal,
             runs peak detection, and plots ongoing data dynamically.
"""

import os
import sys
import time
import argparse
import threading
from collections import deque
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import butter, filtfilt, find_peaks, detrend

# Dynamic import of serial (fails gracefully if not installed/available)
try:
    import serial
except ImportError:
    serial = None

# Thread-safe queues for sharing data
time_buffer = deque(maxlen=2000)
az_buffer = deque(maxlen=2000)
ax_buffer = deque(maxlen=2000)
ay_buffer = deque(maxlen=2000)
data_lock = threading.Lock()

def clean_line_and_parse(line):
    """
    Cleans a line of raw serial input or CSV line, returning timestamp and az, ax, ay if present.
    """
    line = line.strip().replace('"', '')
    if not line:
        return None
    parts = line.split(',')
    
    # Check if we have numerical values
    try:
        # Check if first item is a header
        if any(hdr in parts[0] for hdr in ['time_ms', 'timestamp', 'az', 'ax', 'ay']):
            return None
        
        vals = [float(p) for p in parts]
        
        # If it's a single value (e.g. just az as in the raw csv prefix)
        if len(vals) == 1:
            return (time.time() * 1000.0, vals[0], 0.0, 0.0)
        # If it's timestamp and az
        elif len(vals) == 2:
            return (vals[0], vals[1], 0.0, 0.0)
        # If it's timestamp, ax, ay, az
        elif len(vals) == 4:
            return (vals[0], vals[1], vals[2], vals[3])
    except ValueError:
        pass
    return None

def serial_reader_thread(port, baudrate):
    """
    Background thread to read data from Serial port.
    """
    if serial is None:
        print("Error: 'pyserial' is not installed. Cannot use serial mode.")
        return
        
    print(f"Connecting to serial port {port} at {baudrate} baud...")
    try:
        ser = serial.Serial(port, baudrate, timeout=1.0)
        # Clear buffer
        ser.reset_input_buffer()
        print("Serial connection established successfully.")
    except Exception as e:
        print(f"Error opening serial port: {e}")
        return
        
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore')
                parsed = clean_line_and_parse(line)
                if parsed:
                    t_ms, az, ax, ay = parsed
                    with data_lock:
                        time_buffer.append(t_ms / 1000.0) # Convert to seconds
                        az_buffer.append(az)
                        # If ax and ay are 0 (missing), we synthesize them
                        if ax == 0.0 and ay == 0.0:
                            np.random.seed(int(t_ms) % 1000)
                            ax_buffer.append(0.25 * az + np.random.normal(0, np.abs(az)*0.05))
                            ay_buffer.append(0.15 * az + np.random.normal(0, np.abs(az)*0.05))
                        else:
                            ax_buffer.append(ax)
                            ay_buffer.append(ay)
        except Exception as e:
            print(f"Serial read error: {e}")
            time.sleep(0.1)

def file_reader_thread(filepath):
    """
    Background thread to monitor a growing CSV file (similar to tail -f).
    """
    print(f"Monitoring growing CSV file: {filepath}")
    
    # Wait for file to exist
    while not os.path.exists(filepath):
        time.sleep(0.5)
        
    with open(filepath, 'r') as f:
        # Read existing file content first
        for line in f:
            parsed = clean_line_and_parse(line)
            if parsed:
                t_ms, az, ax, ay = parsed
                with data_lock:
                    time_buffer.append(t_ms / 1000.0)
                    az_buffer.append(az)
                    if ax == 0.0 and ay == 0.0:
                        ax_buffer.append(0.25 * az)
                        ay_buffer.append(0.15 * az)
                    else:
                        ax_buffer.append(ax)
                        ay_buffer.append(ay)
                        
        # Continually poll for new lines
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.01) # Sleep briefly to wait for new writes
                continue
            parsed = clean_line_and_parse(line)
            if parsed:
                t_ms, az, ax, ay = parsed
                with data_lock:
                    time_buffer.append(t_ms / 1000.0)
                    az_buffer.append(az)
                    if ax == 0.0 and ay == 0.0:
                        # Add a tiny bit of noise to synthesized axes
                        ax_buffer.append(0.25 * az + np.random.normal(0, 5))
                        ay_buffer.append(0.15 * az + np.random.normal(0, 5))
                    else:
                        ax_buffer.append(ax)
                        ay_buffer.append(ay)

def main():
    parser = argparse.ArgumentParser(description="BCG Real-time Rolling Dashboard")
    parser.add_argument("--mode", type=str, choices=['serial', 'file'], default='file',
                        help="Data source mode: 'serial' or 'file'")
    parser.add_argument("--port", type=str, default="COM5", help="Serial port name (for serial mode)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate (for serial mode)")
    parser.add_argument("--file", type=str, default="bcg_data.csv", help="CSV file path (for file mode)")
    parser.add_argument("--window", type=float, default=10.0, help="Rolling window size in seconds")
    args = parser.parse_args()
    
    # Start the data collection thread
    if args.mode == 'serial':
        if serial is None:
            print("Error: pyserial is required for serial mode. Run: pip install pyserial")
            sys.exit(1)
        thread = threading.Thread(target=serial_reader_thread, args=(args.port, args.baud), daemon=True)
    else:
        thread = threading.Thread(target=file_reader_thread, args=(args.file,), daemon=True)
        
    thread.start()
    
    # Wait for some initial data
    print("Waiting for data stream to initialize...")
    while True:
        with data_lock:
            if len(time_buffer) > 50:
                break
        time.sleep(0.2)
        
    print("Initializing rolling dashboard window...")
    
    # Setup live matplotlib figure
    plt.style.use('dark_background')
    fig, (ax_raw, ax_filt, ax_info) = plt.subplots(3, 1, figsize=(10, 8), 
                                                   gridspec_kw={'height_ratios': [2, 2, 1]})
    fig.canvas.manager.set_window_title("Live Ballistocardiography (BCG) Dashboard")
    
    # Line objects
    line_raw_z, = ax_raw.plot([], [], color='#7f8c8d', lw=1.5, label='Raw z-axis')
    line_filt_z, = ax_filt.plot([], [], color='#2980b9', lw=2, label='Filtered z-axis (BCG)')
    peaks_scatter, = ax_filt.plot([], [], 'ro', markersize=6, label='Detected Beats')
    
    # Customize subplots
    ax_raw.set_title("Raw Accelerometer (z-axis)", color='#f39c12', fontsize=12)
    ax_raw.set_ylabel("Amplitude")
    ax_raw.grid(True, alpha=0.2)
    ax_raw.legend(loc='upper right')
    
    ax_filt.set_title("Filtered BCG Signal (0.8 - 15 Hz Bandpass) & Peak Detection", color='#3498db', fontsize=12)
    ax_filt.set_ylabel("Amplitude")
    ax_filt.grid(True, alpha=0.2)
    ax_filt.legend(loc='upper right')
    
    # Text info panel
    ax_info.axis('off')
    info_text = ax_info.text(0.05, 0.5, "", fontsize=14, color='#2ecc71', va='center', fontfamily='monospace')
    
    # Design Butterworth filter
    # Pre-estimate fs from initial data
    with data_lock:
        dt = np.median(np.diff(list(time_buffer)))
        fs = 1.0 / dt if dt > 0 else 100.0
        
    nyq = 0.5 * fs
    b, a = butter(4, [0.8 / nyq, 15.0 / nyq], btype='band')
    
    def update_plot(frame):
        nonlocal fs, b, a
        
        with data_lock:
            # Copy data from buffers
            t = np.array(time_buffer)
            z = np.array(az_buffer)
            
        if len(t) < 50:
            return line_raw_z, line_filt_z, peaks_scatter
            
        # Select rolling window (last N seconds)
        t_end = t[-1]
        t_start = t_end - args.window
        window_mask = t >= t_start
        
        t_win = t[window_mask]
        z_win = z[window_mask]
        
        if len(t_win) < 30:
            return line_raw_z, line_filt_z, peaks_scatter
            
        # Re-estimate fs on the current window
        dt_win = np.median(np.diff(t_win))
        if dt_win > 0:
            fs = 1.0 / dt_win
            
        # Update filter design dynamically if sampling rate changes
        nyq = 0.5 * fs
        low_cut = 0.8
        high_cut = min(15.0, nyq - 0.5) # ensure highcut is below Nyquist
        b, a = butter(4, [low_cut / nyq, high_cut / nyq], btype='band')
        
        # Detrend and filter
        z_detrended = detrend(z_win)
        z_filtered = filtfilt(b, a, z_detrended)
        
        # Peak detection on filtered signal
        prom = 0.3 * np.std(z_filtered)
        dist = int(0.45 * fs)
        peaks, _ = find_peaks(z_filtered, distance=dist, prominence=prom)
        
        # Estimate BPM and HRV
        bpm_str = "Calculating..."
        hrv_str = "Calculating..."
        if len(peaks) >= 2:
            beat_times = t_win[peaks]
            ibis = np.diff(beat_times) * 1000.0
            
            # Filter physiological range: 400 - 1500 ms
            valid_ibis = ibis[(ibis >= 400) & (ibis <= 1500)]
            if len(valid_ibis) >= 2:
                mean_ibi = np.mean(valid_ibis)
                bpm = 60000.0 / mean_ibi
                sdnn = np.std(valid_ibis)
                rmssd = np.sqrt(np.mean(np.diff(valid_ibis)**2))
                
                bpm_str = f"{bpm:.1f} BPM"
                hrv_str = f"SDNN: {sdnn:.1f} ms | RMSSD: {rmssd:.1f} ms"
                
        # Update lines
        line_raw_z.set_data(t_win - t_start, z_win)
        line_filt_z.set_data(t_win - t_start, z_filtered)
        
        if len(peaks) > 0:
            peaks_scatter.set_data(t_win[peaks] - t_start, z_filtered[peaks])
        else:
            peaks_scatter.set_data([], [])
            
        # Adjust axes limits
        ax_raw.set_xlim(0, args.window)
        ax_filt.set_xlim(0, args.window)
        
        ax_raw.set_ylim(np.min(z_win) - 100, np.max(z_win) + 100)
        ax_filt.set_ylim(np.min(z_filtered) - 50, np.max(z_filtered) + 50)
        
        # Update info text
        status_text = (
            f"LIVE STATISTICS (Rolling {args.window}s Window)\n"
            f"-----------------------------------------\n"
            f"Sampling Frequency (fs) : {fs:.2f} Hz\n"
            f"Estimated Heart Rate    : {bpm_str}\n"
            f"Heart Rate Variability  : {hrv_str}\n"
            f"Beats Detected (Window) : {len(peaks)}\n"
        )
        info_text.set_text(status_text)
        
        return line_raw_z, line_filt_z, peaks_scatter

    ani = animation.FuncAnimation(fig, update_plot, interval=100, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
