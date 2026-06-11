#!/usr/bin/env python3
"""
Upgraded BCG Live Rolling Dashboard (With Simulation Overrides & New Sensor Format)
Author: Antigravity AI
"""

import os
import sys
import time
import math
import argparse
import csv
import threading
from collections import deque
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
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
occupancy_buffer = deque(maxlen=2000)
temp_buffer = deque(maxlen=2000)
humidity_buffer = deque(maxlen=2000)
data_lock = threading.Lock()

# History of recent BPM estimates to track stability
bpm_history = deque(maxlen=15)
stability_flag = "Stable"
running_avg_bpm = 0.0
bpm_std = 0.0

# Global tracking reference link to send commands down to background thread
serial_session = None
current_sim_mode = 'N'  # 'N' = normal, 'B' = bradycardia, 'T' = tachycardia

def clean_line_and_parse(line):
    line = line.strip().replace('"', '')
    if not line:
        return None
    parts = line.split(',')
    # Skip header lines or ESP32 boot log output
    if any(h in parts[0] for h in ['time_ms', 'timestamp', 'az', 'ax', 'ay', 'occupancy', 'temp', 'humidity']):
        return None
    try:
        vals = []
        for p in parts:
            p_clean = p.strip().lower()
            if p_clean in ('nan', 'nanf'):
                vals.append(float('nan'))
            elif p_clean in ('inf', 'inff', '+inf', '+inff'):
                vals.append(float('inf'))
            elif p_clean in ('-inf', '-inff'):
                vals.append(float('-inf'))
            else:
                vals.append(float(p))

        # If the first four axis fields are invalid, skip the line entirely.
        if len(vals) >= 4 and not all(np.isfinite(v) for v in vals[:4]):
            return None

        # Parse based on fields present (Backward compatibility)
        if len(vals) == 1:
            return (time.time() * 1000.0, 0.0, 0.0, vals[0], 1, float('nan'), float('nan'))
        elif len(vals) == 2:
            return (vals[0], 0.0, 0.0, vals[1], 1, float('nan'), float('nan'))
        elif len(vals) == 4:
            return (vals[0], vals[1], vals[2], vals[3], 1, float('nan'), float('nan'))
        elif len(vals) >= 7:
            # Use the occupancy field as an active-high indicator: 1 = present, 0 = empty.
            if not math.isnan(vals[4]):
                occ = int(np.clip(vals[4], 0.0, 1.0))
            else:
                occ = 1  # Fallback baseline default if NaN occurs
                
            return (vals[0], vals[1], vals[2], vals[3], occ, vals[5], vals[6])
    except (ValueError, IndexError):
        pass
    return None

def serial_reader_and_logger(port, baudrate, csv_path):
    global serial_session
    if serial is None:
        print("Error: 'pyserial' is not installed. Falling back to local simulation mode.")
        sim_thread = threading.Thread(target=simulated_data_generator, args=(csv_path,), daemon=True)
        sim_thread.start()
        return
        
    print(f"Connecting to serial port {port} at {baudrate} baud...")
    try:
        serial_session = serial.Serial(port, baudrate, timeout=1.0)
        serial_session.reset_input_buffer()
        print("Serial connection established successfully.")
    except Exception as e:
        print(f"Error opening serial port: {e}. Falling back to local simulation mode.")
        sim_thread = threading.Thread(target=simulated_data_generator, args=(csv_path,), daemon=True)
        sim_thread.start()
        return
        
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    csv_file = open(csv_path, 'a', newline='')
    csv_writer = csv.writer(csv_file)
    if write_header:
        csv_writer.writerow(['time_ms', 'ax', 'ay', 'az', 'occupancy', 'temp', 'humidity'])
        csv_file.flush()
        
    while True:
        try:
            if serial_session.in_waiting > 0:
                line = serial_session.readline().decode('utf-8', errors='ignore')
                parsed = clean_line_and_parse(line)
                if parsed:
                    t_ms, ax, ay, az, occupancy, temp, humidity = parsed
                    csv_writer.writerow([int(t_ms), ax, ay, az, occupancy, temp, humidity])
                    csv_file.flush()
                    
                    with data_lock:
                        time_buffer.append(t_ms / 1000.0)
                        ax_buffer.append(ax)
                        ay_buffer.append(ay)
                        az_buffer.append(az)
                        occupancy_buffer.append(occupancy)
                        temp_buffer.append(temp)
                        humidity_buffer.append(humidity)
        except Exception as e:
            time.sleep(0.1)

def simulated_data_generator(csv_path):
    print("Simulated Data Generator running...")
    write_header = not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0
    csv_file = open(csv_path, 'a', newline='')
    csv_writer = csv.writer(csv_file)
    if write_header:
        csv_writer.writerow(['time_ms', 'ax', 'ay', 'az', 'occupancy', 'temp', 'humidity'])
        csv_file.flush()

    start_time = time.time()
    dt = 0.01  # 100 Hz simulation
    
    while True:
        try:
            time.sleep(dt)
            curr_time = time.time()
            t_ms = int((curr_time - start_time) * 1000)
            
            # Decide target BPM based on simulated overrides
            if current_sim_mode == 'B':
                target_bpm = 42.0
            elif current_sim_mode == 'T':
                target_bpm = 145.0
            else:
                target_bpm = 72.0
            
            freq = target_bpm / 60.0
            
            # Occupancy cycle: Present for 45s, Empty for 15s
            cycle_t = (curr_time - start_time) % 60.0
            occupancy = 1 if cycle_t < 45.0 else 0
            
            # BCG simulation
            bcg = 15.0 * np.sin(2 * np.pi * freq * (t_ms / 1000.0)) + \
                  5.0 * np.sin(2 * np.pi * 2 * freq * (t_ms / 1000.0))
            if occupancy == 0:
                bcg = 0.0
                
            ax = -110.0 + bcg * 0.5 + np.random.normal(0, 3.0)
            ay = 95.0 + bcg * 0.3 + np.random.normal(0, 2.0)
            az = 650.0 + bcg * 1.0 + np.random.normal(0, 4.0)
            
            # Temperature and humidity simulation with occasional alert ranges
            if 30.0 < cycle_t < 40.0:
                temp = 36.5  # High Temp alert
                humidity = 82.5  # High Hum alert
            else:
                temp = 29.4 + 0.5 * np.sin(2 * np.pi * (t_ms / 60000.0))
                humidity = 71.2 + 2.0 * np.cos(2 * np.pi * (t_ms / 60000.0))
            
            # Occasional temporary NaNs to check stability
            if 10.0 < cycle_t < 12.0:
                temp = float('nan')
                humidity = float('nan')
                
            csv_writer.writerow([t_ms, ax, ay, az, occupancy, temp, humidity])
            csv_file.flush()
            
            with data_lock:
                time_buffer.append(t_ms / 1000.0)
                ax_buffer.append(ax)
                ay_buffer.append(ay)
                az_buffer.append(az)
                occupancy_buffer.append(occupancy)
                temp_buffer.append(temp)
                humidity_buffer.append(humidity)
        except Exception as e:
            time.sleep(0.1)

def main():
    parser = argparse.ArgumentParser(description="Upgraded 3-Axis BCG Live Dashboard")
    parser.add_argument("--mode", type=str, choices=['serial'], default='serial', help="Serial mode connection loop")
    parser.add_argument("--port", type=str, default="COM5", help="Serial port target link channel")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate config setting")
    parser.add_argument("--log_file", type=str, default="live_bcg_output.csv", help="CSV path target backup logs")
    parser.add_argument("--window", type=float, default=10.0, help="Rolling window frame layout size viewport")
    args = parser.parse_args()
    
    # Start reader thread (will fall back to simulation if port is missing/fails)
    thread = threading.Thread(target=serial_reader_and_logger, args=(args.port, args.baud, args.log_file), daemon=True)
    thread.start()
    
    print("Waiting for signal buffers to establish connections...")
    while True:
        with data_lock:
            if len(time_buffer) > 40:
                break
        time.sleep(0.2)
        
    plt.style.use('dark_background')
    
    # Responsive, clean sizing
    fig = plt.figure(figsize=(16, 10))
    fig.canvas.manager.set_window_title("Live Ballistocardiography (BCG) Healthcare-Monitoring Console")
    
    # Establish GridSpec layout: 12 rows, 4 columns
    gs = fig.add_gridspec(12, 4, hspace=0.7, wspace=0.3)
    
    # Top Row Cards (Occupancy, Temp, Humidity, Heart Rate)
    ax_card_occ = fig.add_subplot(gs[0, 0])
    ax_card_temp = fig.add_subplot(gs[0, 1])
    ax_card_hum = fig.add_subplot(gs[0, 2])
    ax_card_bpm = fig.add_subplot(gs[0, 3])
    
    # Plots (Middle / Bottom)
    ax_raw = fig.add_subplot(gs[1:4, 0:3])
    ax_filt = fig.add_subplot(gs[4:7, 0:3])
    ax_fft = fig.add_subplot(gs[7:10, 0:3])
    
    # Side Diagnostic & Alert Panel
    ax_panel = fig.add_subplot(gs[1:10, 3])
    
    # Style cards
    for ax, title, color in [
        (ax_card_occ, "Occupancy Status", "#1abc9c"),
        (ax_card_temp, "Temperature", "#e67e22"),
        (ax_card_hum, "Humidity", "#3498db"),
        (ax_card_bpm, "Heart Rate (BPM)", "#e74c3c")
    ]:
        ax.set_facecolor('#161a22')
        ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
        ax.set_title(title, color=color, fontsize=10, fontweight='bold')
        for spine in ax.spines.values():
            spine.set_color('#2c3e50')
            spine.set_linewidth(1.5)
            
    occ_text = ax_card_occ.text(0.5, 0.45, "INITIALIZING", ha='center', va='center', fontsize=16, fontweight='bold')
    temp_text = ax_card_temp.text(0.5, 0.45, "--.- °C", ha='center', va='center', fontsize=16, fontweight='bold')
    hum_text = ax_card_hum.text(0.5, 0.45, "--.- %", ha='center', va='center', fontsize=16, fontweight='bold')
    bpm_text = ax_card_bpm.text(0.5, 0.45, "--.-", ha='center', va='center', fontsize=16, fontweight='bold')
    
    # Setup Raw Signals Plot
    line_raw_x, = ax_raw.plot([], [], color='#e67e22', alpha=0.5, label='Raw AX')
    line_raw_y, = ax_raw.plot([], [], color='#27ae60', alpha=0.5, label='Raw AY')
    line_raw_z, = ax_raw.plot([], [], color='#2980b9', alpha=0.9, label='Raw AZ')
    ax_raw.legend(loc='upper right', ncol=3, fontsize=9)
    ax_raw.set_title("Raw Accelerometer Channels (Detrended)", color='#f39c12', fontsize=11)
    ax_raw.set_ylabel("Amplitude")
    ax_raw.grid(True, alpha=0.2)
    
    # Setup Filtered Signals Plot
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
    
    # Setup FFT Plot
    line_fft_best, = ax_fft.plot([], [], color='#8e44ad', lw=2.0, label='Best Axis FFT')
    line_fft_mag, = ax_fft.plot([], [], color='#e74c3c', lw=1.0, label='Magnitude FFT')
    ax_fft.axvspan(0.8, 3.0, color='#2ecc71', alpha=0.15, label='Cardiac Band')
    ax_fft.legend(loc='upper right', fontsize=9)
    ax_fft.set_title("FFT Frequency Spectrum", color='#2ecc71', fontsize=11)
    ax_fft.set_xlabel("Frequency (Hz)")
    ax_fft.set_ylabel("Magnitude")
    ax_fft.grid(True, alpha=0.2)
    
    # Setup Side Panel Info Box
    ax_panel.set_facecolor('#161a22')
    ax_panel.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
    for spine in ax_panel.spines.values():
        spine.set_color('#2c3e50')
        spine.set_linewidth(1.5)
    panel_text = ax_panel.text(0.05, 0.95, "", fontsize=9.5, color='#ffffff', va='top', ha='left', fontfamily='monospace', transform=ax_panel.transAxes)
    
    # Control Buttons Handler
    def set_mode_live(event):
        global serial_session, current_sim_mode
        current_sim_mode = 'N'
        if serial_session and serial_session.is_open:
            serial_session.write(b'N')
            print("Command sent: Resuming Live MPU6050 Capture System Monitoring.")

    def set_mode_brady(event):
        global serial_session, current_sim_mode
        current_sim_mode = 'B'
        if serial_session and serial_session.is_open:
            serial_session.write(b'B')
            print("Command sent: Injected Bradycardia Arrhythmia Model Target (42 BPM).")

    def set_mode_tachy(event):
        global serial_session, current_sim_mode
        current_sim_mode = 'T'
        if serial_session and serial_session.is_open:
            serial_session.write(b'T')
            print("Command sent: Injected Tachycardia Arrhythmia Model Target (145 BPM).")

    # Control Buttons Layout
    ax_btn_live = plt.axes([0.15, 0.02, 0.18, 0.035])
    ax_btn_brady = plt.axes([0.40, 0.02, 0.20, 0.035])
    ax_btn_tachy = plt.axes([0.68, 0.02, 0.20, 0.035])

    btn_live = Button(ax_btn_live, 'Resume Live Data', color='#27ae60', hovercolor='#2ecc71')
    btn_brady = Button(ax_btn_brady, 'Simulate Bradycardia', color='#c0392b', hovercolor='#e74c3c')
    btn_tachy = Button(ax_btn_tachy, 'Simulate Tachycardia', color='#d35400', hovercolor='#e67e22')

    btn_live.on_clicked(set_mode_live)
    btn_brady.on_clicked(set_mode_brady)
    btn_tachy.on_clicked(set_mode_tachy)

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
            occ = np.array(occupancy_buffer)
            temp = np.array(temp_buffer)
            hum = np.array(humidity_buffer)
            
        if len(t) < 30:
            return
            
        t_end = t[-1]
        t_start = t_end - args.window
        win = t >= t_start
        
        t_w, ax_w, ay_w, az_w = t[win], ax[win], ay[win], az[win]
        occ_w, temp_w, hum_w = occ[win], temp[win], hum[win]
        
        # Remove any rows with invalid numeric data before processing
        finite_mask = np.isfinite(t_w) & np.isfinite(ax_w) & np.isfinite(ay_w) & np.isfinite(az_w)
        if not np.any(finite_mask):
            return
        t_w = t_w[finite_mask]
        ax_w = ax_w[finite_mask]
        ay_w = ay_w[finite_mask]
        az_w = az_w[finite_mask]
        occ_w = occ_w[finite_mask]
        temp_w = temp_w[finite_mask]
        hum_w = hum_w[finite_mask]
        
        if len(t_w) < 15:
            return
            
        dt_win = np.median(np.diff(t_w))
        if dt_win > 0:
            fs = 1.0 / dt_win
            
        nyq = 0.5 * fs
        low_cut = 0.8
        high_cut = min(4.0, nyq - 0.5)
        b, a = butter(4, [low_cut / nyq, high_cut / nyq], btype='band')
        
        ax_dt, ay_dt, az_dt = detrend(ax_w), detrend(ay_w), detrend(az_w)
        mag_w = np.sqrt(ax_w**2 + ay_w**2 + az_w**2)
        mag_dt = detrend(mag_w)
        
        ax_f = filtfilt(b, a, ax_dt)
        ay_f = filtfilt(b, a, ay_dt)
        az_f = filtfilt(b, a, az_dt)
        mag_f = filtfilt(b, a, mag_dt)
        
        channels = ['ax', 'ay', 'az', 'magnitude']
        signals = {'ax': ax_f, 'ay': ay_f, 'az': az_f, 'magnitude': mag_f}
        
        fft_data = {}
        quality_metrics = {}
        
        for ch in channels:
            sig = signals[ch]
            n = len(sig)
            fft_vals = np.fft.rfft(sig)
            fft_freqs = np.fft.rfftfreq(n, d=1.0/fs)
            fft_mag = np.abs(fft_vals)
            
            mask = (fft_freqs >= 0.5) & (fft_freqs <= 4.0)
            if np.any(mask):
                idx_max = np.argmax(fft_mag[mask])
                dom_freq = fft_freqs[mask][idx_max]
                bpm = dom_freq * 60.0
                cardiac_peak_mag = fft_mag[mask][idx_max]
            else:
                bpm = 0.0
                cardiac_peak_mag = 0.0
                
            rms = np.sqrt(np.mean(sig**2))
            var = np.var(sig)
            ptp = np.ptp(sig)
            
            noise_mask = (fft_freqs > 4.0) & (fft_freqs <= 12.0)
            noise_mean = np.mean(fft_mag[noise_mask]) if np.any(noise_mask) else 1e-5
            sqs = cardiac_peak_mag / (noise_mean + 1e-5)
            
            fft_data[ch] = {'freqs': fft_freqs, 'mags': fft_mag, 'bpm': bpm}
            quality_metrics[ch] = {'rms': rms, 'var': var, 'ptp': ptp, 'sqs': sqs}
            
        best_channel = max(['ax', 'ay', 'az'], key=lambda c: quality_metrics[c]['sqs'])
        best_sig = signals[best_channel]
        
        # Determine Current Occupancy & Environment Data
        current_occ = occ_w[-1] if len(occ_w) > 0 else 1
        current_temp = temp_w[-1] if len(temp_w) > 0 else float('nan')
        current_hum = hum_w[-1] if len(hum_w) > 0 else float('nan')
        
        # Trigger and compile Alerts
        alerts = []
        if not math.isnan(current_temp) and current_temp > 35.0:
            alerts.append("⚠️ High Temperature Alert")
        if not math.isnan(current_hum) and current_hum > 80.0:
            alerts.append("⚠️ High Humidity Alert")
        
        # Occupancy Logic & Peak Detection Pausing
        if current_occ == 1:
            occ_status = "Present"
            occ_text.set_text("PRESENT")
            occ_text.set_color('#2ecc71')  # Active Green
            monitoring_status = "Active"
            
            prom = 0.25 * np.std(best_sig)
            dist = int(0.22 * fs)
            peaks, _ = find_peaks(best_sig, distance=dist, prominence=prom)
            
            peak_bpm = 0.0
            if len(peaks) >= 2:
                beat_times = t_w[peaks]
                ibis = np.diff(beat_times) * 1000.0
                valid_ibis = ibis[(ibis >= 250) & (ibis <= 2000)]
                if len(valid_ibis) >= 1:
                    peak_bpm = 60000.0 / np.mean(valid_ibis)
                    
            current_bpm = fft_data[best_channel]['bpm']
            clamped_bpm = float(np.clip(current_bpm, 60.0, 100.0)) if current_bpm > 0 else 0.0
            if current_bpm > 0:
                bpm_history.append(clamped_bpm)
                
            if len(bpm_history) >= 5:
                running_avg_bpm = np.mean(bpm_history)
                bpm_std = np.std(bpm_history)
                stability_flag = "Stable" if bpm_std <= 10.0 else "Arrhythmia Transition Active"
            else:
                running_avg_bpm = clamped_bpm
                bpm_std = 0.0
                stability_flag = "Calculating..."
                
            bpm_text.set_text(f"{running_avg_bpm:.1f}")
            bpm_text.set_color('#e74c3c')
        else:
            occ_status = "Empty"
            occ_text.set_text("EMPTY")
            occ_text.set_color('#f1c40f')  # Warning/Empty Yellow
            monitoring_status = "Paused"
            peaks = []
            peak_bpm = 0.0
            running_avg_bpm = 0.0
            stability_flag = "Monitoring Paused"
            bpm_text.set_text("PAUSED")
            bpm_text.set_color('#7f8c8d')
            alerts.append("⚠️ Monitoring Paused (No Occupant)")

        # Environment Comfort Classifications
        if math.isnan(current_temp):
            temp_str = "NaN"
            temp_comfort = "Unknown (NaN)"
            temp_text.set_text("--.- °C")
            temp_text.set_color('#7f8c8d')
        else:
            temp_str = f"{current_temp:.1f}°C"
            temp_text.set_text(f"{current_temp:.1f} °C")
            if current_temp < 18.0:
                temp_comfort = "Cold"
                temp_text.set_color('#3498db')
            elif current_temp <= 26.0:
                temp_comfort = "Comfortable"
                temp_text.set_color('#2ecc71')
            elif current_temp <= 32.0:
                temp_comfort = "Warm"
                temp_text.set_color('#f39c12')
            else:
                temp_comfort = "Hot"
                temp_text.set_color('#e74c3c')

        if math.isnan(current_hum):
            hum_str = "NaN"
            hum_comfort = "Unknown (NaN)"
            hum_text.set_text("--.- %")
            hum_text.set_color('#7f8c8d')
        else:
            hum_str = f"{int(current_hum)}%"
            hum_text.set_text(f"{current_hum:.1f} %")
            if current_hum < 30.0:
                hum_comfort = "Low"
                hum_text.set_color('#f39c12')
            elif current_hum <= 60.0:
                hum_comfort = "Normal"
                hum_text.set_color('#2ecc71')
            else:
                hum_comfort = "High"
                hum_text.set_color('#3498db')

        # Format alerts text block
        alert_str = "\n  ".join(alerts) if alerts else "No Active Warnings"
        
        sqs_conf = min(100.0, max(0.0, (quality_metrics[best_channel]['sqs'] - 1.0) * 10.0))
        stab_conf = min(100.0, max(0.0, 100.0 - (bpm_std * 5.0)))
        confidence_score = 0.6 * sqs_conf + 0.4 * stab_conf if current_occ == 1 else 0.0
        
        # Update raw/filtered/FFT plot data
        line_raw_x.set_data(t_w - t_start, ax_dt)
        line_raw_y.set_data(t_w - t_start, ay_dt)
        line_raw_z.set_data(t_w - t_start, az_dt)
        ax_raw.set_xlim(0, args.window)
        min_raw = min(np.min(ax_dt), np.min(ay_dt), np.min(az_dt)) - 100
        max_raw = max(np.max(ax_dt), np.max(ay_dt), np.max(az_dt)) + 100
        ax_raw.set_ylim(min_raw, max_raw)
        
        line_filt_x.set_data(t_w - t_start, ax_f)
        line_filt_y.set_data(t_w - t_start, ay_f)
        line_filt_z.set_data(t_w - t_start, az_f)
        line_filt_mag.set_data(t_w - t_start, mag_f)
        
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
        min_filt = min(np.min(ax_f), np.min(ay_f), np.min(az_f), np.min(mag_f)) - 50
        max_filt = max(np.max(ax_f), np.max(ay_f), np.max(az_f), np.max(mag_f)) + 50
        ax_filt.set_ylim(min_filt, max_filt)
        
        fft_best = fft_data[best_channel]
        fft_mag_data = fft_data['magnitude']
        
        line_fft_best.set_data(fft_best['freqs'], fft_best['mags'])
        line_fft_mag.set_data(fft_mag_data['freqs'], fft_mag_data['mags'])
        ax_fft.set_xlim(0, 5.0)
        ax_fft.set_ylim(0, max(np.max(fft_best['mags']), np.max(fft_mag_data['mags'])) * 1.1 + 5.0)
        
        # Build diagnostics side-panel text layout
        panel_content = (
            f"┌───────────────────────────────────────┐\n"
            f"│            ## System Status           │\n"
            f"└───────────────────────────────────────┘\n"
            f"  Occupancy        : {occ_status}\n"
            f"  Heart Monitoring : {monitoring_status}\n"
            f"  Temperature      : {temp_str}\n"
            f"  Humidity         : {hum_str}\n"
            f"─────────────────────────────────────────\n"
            f"  Sampling rate    : {fs:.1f} Hz\n"
            f"  Best Axis Signal : {best_channel.upper()}\n"
            f"  Integrity (SQS)  : {quality_metrics[best_channel]['sqs']:.2f}\n"
            f"  Confidence Score : {confidence_score:.1f} %\n"
            f"  Rhythm Status    : {stability_flag}\n"
            f"─────────────────────────────────────────\n"
            f"  [Environmental Conditions]\n"
            f"  Temperature Class: {temp_comfort}\n"
            f"  Humidity Class   : {hum_comfort}\n"
            f"─────────────────────────────────────────\n"
            f"  [Active System Alerts]\n"
            f"  {alert_str}\n"
            f"─────────────────────────────────────────\n"
        )
        panel_text.set_text(panel_content)
        
        return (line_raw_x, line_raw_y, line_raw_z, line_filt_x, line_filt_y, line_filt_z, 
                line_filt_mag, peaks_scatter, line_fft_best, line_fft_mag)

    ani = animation.FuncAnimation(fig, update_plot, interval=100, blit=False, cache_frame_data=False)
    plt.show()

if __name__ == "__main__":
    main()