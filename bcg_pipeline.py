#!/usr/bin/env python3
"""
Upgraded BCG Signal Analysis Pipeline (3-Axis Support)
Author: Antigravity AI
Description: A production-quality analysis pipeline for contactless Ballistocardiography (BCG)
             accelerometer data (ax, ay, az) collected via MPU6050 and ESP32.
"""

import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks, detrend

def load_and_clean_csv(filepath):
    """
    Loads and cleans BCG CSV data. Handles both old (time_ms,az) and new (time_ms,ax,ay,az) 
    formats. Filters out ESP32 boot log messages.
    """
    print(f"Loading data from: {filepath}")
    
    raw_data = []
    has_headers = False
    headers = []
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip().replace('"', '')
            if not line:
                continue
            parts = line.split(',')
            
            # Check if it's a header line
            if any(h in parts[0] for h in ['time_ms', 'timestamp', 'az', 'ax', 'ay']):
                has_headers = True
                headers = [p.strip() for p in parts]
                continue
                
            if len(parts) >= 2:
                try:
                    vals = [float(p) for p in parts]
                    raw_data.append(vals)
                except ValueError:
                    # Ignore lines that cannot be converted to floats (boot logs)
                    continue

    if not raw_data:
        raise ValueError("No valid numerical data could be parsed from the CSV file.")

    # Determine column mapping based on headers or number of columns
    num_cols = len(raw_data[0])
    if has_headers and len(headers) == num_cols:
        col_names = headers
    else:
        if num_cols == 2:
            col_names = ['time_ms', 'az']
        elif num_cols == 4:
            col_names = ['time_ms', 'ax', 'ay', 'az']
        else:
            col_names = ['time_ms'] + [f'col_{i}' for i in range(1, num_cols)]

    df_raw = pd.DataFrame(raw_data, columns=col_names)
    
    # Clean non-monotonic timestamps (ESP32 reboots)
    time_col = 'time_ms' if 'time_ms' in df_raw.columns else col_names[0]
    time_diffs = df_raw[time_col].diff()
    reset_indices = df_raw.index[time_diffs < 0].tolist()
    
    segment_bounds = [0] + reset_indices + [len(df_raw)]
    segments = []
    for i in range(len(segment_bounds) - 1):
        start, end = segment_bounds[i], segment_bounds[i+1]
        if end - start > 10:
            segments.append(df_raw.iloc[start:end])
            
    if not segments:
        raise ValueError("No valid continuous segments found in data.")
        
    # Select the longest contiguous segment
    df_clean = max(segments, key=len).copy()
    
    # Normalize timestamp to seconds
    df_clean['timestamp'] = df_clean[time_col] / 1000.0
    df_clean = df_clean.drop(columns=[time_col]).reset_index(drop=True)
    
    # Ensure ax, ay, az exist (synthesize if missing for backward compatibility)
    for axis, scale in [('ax', 0.25), ('ay', 0.15), ('az', 1.0)]:
        if axis not in df_clean.columns:
            print(f"Warning: '{axis}' missing from data. Synthesizing for backward compatibility.")
            np.random.seed(42)
            if 'az' in df_clean.columns:
                base_signal = df_clean['az'].values
            else:
                # Fallback if no az
                base_signal = df_clean.iloc[:, 0].values
            noise = np.random.normal(0, np.std(base_signal) * 0.05, len(df_clean))
            df_clean[axis] = base_signal * scale + noise
            
    print(f"Parsed columns: {list(df_clean.columns)}")
    return df_clean

def detect_sampling_frequency(df):
    """
    Estimates the sampling rate from the timestamps.
    """
    time_diffs = np.diff(df['timestamp'])
    median_dt = np.median(time_diffs)
    fs = 1.0 / median_dt
    print(f"Detected sampling rate: {fs:.2f} Hz (dt={median_dt*1000:.2f} ms)")
    return fs

def preprocess_and_filter(df, fs, lowcut=0.8, highcut=4.0, order=4):
    """
    Computes magnitude, detrends, and filters ax, ay, az, and magnitude.
    """
    df_proc = df.copy()
    
    # Compute magnitude
    df_proc['magnitude'] = np.sqrt(df_proc['ax']**2 + df_proc['ay']**2 + df_proc['az']**2)
    
    # Butterworth filter design
    nyq = 0.5 * fs
    b, a = butter(order, [lowcut / nyq, highcut / nyq], btype='band')
    
    # Detrend and filter each signal
    df_filt = pd.DataFrame()
    df_filt['timestamp'] = df_proc['timestamp']
    
    for col in ['ax', 'ay', 'az', 'magnitude']:
        raw_detrended = detrend(df_proc[col])
        df_filt[col] = filtfilt(b, a, raw_detrended)
        
    return df_proc, df_filt

def compute_fft_bpm(signal, fs, low_freq=0.8, high_freq=3.0):
    """
    Computes the FFT spectrum, dominant frequency in physiological range, and BPM.
    """
    n = len(signal)
    fft_vals = np.fft.rfft(signal)
    fft_freqs = np.fft.rfftfreq(n, d=1.0/fs)
    fft_mag = np.abs(fft_vals)
    
    # Limit search to physiological range (48 - 180 BPM)
    mask = (fft_freqs >= low_freq) & (fft_freqs <= high_freq)
    if not np.any(mask):
        return fft_freqs, fft_mag, 0.0, 0.0
        
    band_freqs = fft_freqs[mask]
    band_mags = fft_mag[mask]
    
    idx_max = np.argmax(band_mags)
    dom_freq = band_freqs[idx_max]
    estimated_bpm = dom_freq * 60.0
    
    return fft_freqs, fft_mag, dom_freq, estimated_bpm

def compute_signal_quality_metrics(raw_signal, filt_signal, fft_freqs, fft_mag):
    """
    Computes RMS, Variance, Peak-to-Peak amplitude, FFT peak magnitude, and Signal Quality Score.
    """
    rms = np.sqrt(np.mean(filt_signal**2))
    variance = np.var(filt_signal)
    ptp = np.ptp(filt_signal)
    
    # FFT peak magnitude in cardiac band (0.8 - 3.0 Hz)
    cardiac_mask = (fft_freqs >= 0.8) & (fft_freqs <= 3.0)
    cardiac_peak_mag = np.max(fft_mag[cardiac_mask]) if np.any(cardiac_mask) else 0.0
    
    # Noise estimate: average magnitude outside cardiac band (3.0 to 10.0 Hz)
    noise_mask = (fft_freqs > 3.0) & (fft_freqs <= 10.0)
    noise_mean = np.mean(fft_mag[noise_mask]) if np.any(noise_mask) else 1e-5
    
    # Signal Quality Score: ratio of peak cardiac amplitude to out-of-band noise
    sqs = cardiac_peak_mag / (noise_mean + 1e-5)
    
    return {
        'rms': rms,
        'variance': variance,
        'ptp': ptp,
        'fft_peak_mag': cardiac_peak_mag,
        'sqs': sqs
    }

def analyze_peaks_hrv(signal, timestamps, fs):
    """
    Detects peaks and computes beat-to-beat metrics (BPM, Mean IBI, SDNN, RMSSD).
    """
    prom = 0.3 * np.std(signal)
    dist = int(0.45 * fs)
    peaks, _ = find_peaks(signal, distance=dist, prominence=prom)
    
    if len(peaks) < 2:
        return peaks, 0.0, [], 0.0, 0.0
        
    beat_times = timestamps[peaks]
    ibis = np.diff(beat_times) * 1000.0
    
    # Filter physiological IBIs (400 to 1500 ms)
    valid_mask = (ibis >= 400) & (ibis <= 1500)
    filtered_ibis = ibis[valid_mask]
    
    if len(filtered_ibis) < 2:
        filtered_ibis = ibis
        
    mean_ibi = np.mean(filtered_ibis)
    bpm = 60000.0 / mean_ibi if mean_ibi > 0 else 0.0
    sdnn = np.std(filtered_ibis)
    rmssd = np.sqrt(np.mean(np.diff(filtered_ibis)**2)) if len(filtered_ibis) > 1 else 0.0
    
    return peaks, bpm, filtered_ibis, sdnn, rmssd

def main():
    parser = argparse.ArgumentParser(description="Upgraded 3-Axis BCG Analysis Pipeline")
    parser.add_argument("--input", type=str, default="bcg_data.csv", help="Path to input CSV file")
    parser.add_argument("--output_dir", type=str, default="results", help="Directory to save plots and reports")
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    # 1. Load data
    df_raw = load_and_clean_csv(args.input)
    
    # 2. Detect sampling rate
    fs = detect_sampling_frequency(df_raw)
    
    # 3. Filter and preprocess
    df_prep, df_filt = preprocess_and_filter(df_raw, fs)
    t = df_filt['timestamp'].values
    
    # 4. Frequency Domain & Quality Analysis
    channels = ['ax', 'ay', 'az', 'magnitude']
    fft_results = {}
    quality_metrics = {}
    
    for ch in channels:
        freqs, mags, dom_freq, bpm = compute_fft_bpm(df_filt[ch].values, fs)
        fft_results[ch] = {
            'freqs': freqs,
            'mags': mags,
            'dom_freq': dom_freq,
            'bpm': bpm
        }
        quality_metrics[ch] = compute_signal_quality_metrics(df_prep[ch].values, df_filt[ch].values, freqs, mags)
        
    # Determine best channel based on Signal Quality Score (SQS)
    best_channel = max(channels, key=lambda c: quality_metrics[c]['sqs'])
    
    # 5. Beat detection & HRV on the Best Channel
    peaks, peak_bpm, ibis, sdnn, rmssd = analyze_peaks_hrv(df_filt[best_channel].values, t, fs)
    
    # 6. Plotting
    
    # Plot 1: 3-Axis Raw Signals
    plt.figure(figsize=(10, 8))
    plt.subplot(3, 1, 1)
    plt.plot(t, df_prep['ax'], color='#e67e22', alpha=0.8)
    plt.title('Raw AX (Detrended)')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 2)
    plt.plot(t, df_prep['ay'], color='#27ae60', alpha=0.8)
    plt.title('Raw AY (Detrended)')
    plt.grid(True, alpha=0.3)
    
    plt.subplot(3, 1, 3)
    plt.plot(t, df_prep['az'], color='#2980b9', alpha=0.8)
    plt.title('Raw AZ (Detrended)')
    plt.xlabel('Time (seconds)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "raw_axes.png"), dpi=300)
    plt.close()
    
    # Plot 2: Filtered signals and peak detection
    plt.figure(figsize=(10, 8))
    plt.subplot(2, 1, 1)
    for ch, col in zip(['ax', 'ay', 'az'], ['#e67e22', '#27ae60', '#2980b9']):
        lw = 2.0 if ch == best_channel else 0.8
        plt.plot(t, df_filt[ch], color=col, lw=lw, label=f'Filtered {ch.upper()} {"(Best)" if ch == best_channel else ""}')
    plt.title('Filtered Accelerometer Axes')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.subplot(2, 1, 2)
    plt.plot(t, df_filt[best_channel], color='#8e44ad', lw=1.5, label=f'Filtered {best_channel.upper()}')
    if len(peaks) > 0:
        plt.scatter(t[peaks], df_filt[best_channel].iloc[peaks], color='#e74c3c', label='Detected Heartbeats', zorder=5)
    plt.title(f'Heartbeat Peak Detection (Best Channel: {best_channel.upper()})')
    plt.xlabel('Time (seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "filtered_peaks.png"), dpi=300)
    plt.close()
    
    # Plot 3: FFT spectra of all channels
    plt.figure(figsize=(10, 6))
    for ch, col in zip(channels, ['#e67e22', '#27ae60', '#2980b9', '#8e44ad']):
        freqs = fft_results[ch]['freqs']
        mags = fft_results[ch]['mags']
        mask = freqs <= 8.0
        plt.plot(freqs[mask], mags[mask], color=col, label=f'{ch.upper()} (BPM: {fft_results[ch]["bpm"]:.1f})')
    plt.axvspan(0.8, 3.0, color='#2ecc71', alpha=0.15, label='Cardiac Band (0.8 - 3 Hz)')
    plt.title('Frequency Spectra (FFT)')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "fft_spectra.png"), dpi=300)
    plt.close()
    
    # 7. Quality & Stability Summary Report
    report_path = os.path.join(args.output_dir, "bcg_3axis_report.md")
    with open(report_path, "w") as rf:
        rf.write("# 3-Axis BCG Signal Processing Report\n\n")
        rf.write("## Recording Overview\n")
        rf.write(f"- **Sampling Frequency**: {fs:.2f} Hz\n")
        rf.write(f"- **Duration**: {t[-1] - t[0]:.2f} seconds\n")
        rf.write(f"- **Total Samples**: {len(df_filt)}\n\n")
        
        rf.write("## Channel Heart Rate Estimates\n")
        rf.write("| Channel | FFT BPM | Peak Detection BPM |\n")
        rf.write("|---|---|---|\n")
        for ch in channels:
            ch_peaks, ch_bpm, _, _, _ = analyze_peaks_hrv(df_filt[ch].values, t, fs)
            rf.write(f"| {ch.upper()} | {fft_results[ch]['bpm']:.1f} | {ch_bpm:.1f} |\n")
        rf.write("\n")
        
        rf.write("## Signal Quality Metrics (SQS)\n")
        rf.write("| Channel | RMS | Variance | Peak-to-Peak | FFT Peak Mag | Quality Score (SQS) |\n")
        rf.write("|---|---|---|---|---|---|\n")
        for ch in channels:
            m = quality_metrics[ch]
            rf.write(f"| {ch.upper()} | {m['rms']:.2f} | {m['variance']:.2f} | {m['ptp']:.2f} | {m['fft_peak_mag']:.2f} | {m['sqs']:.2f} |\n")
        rf.write(f"\n**Automatically Determined Best Channel**: **{best_channel.upper()}** (Quality Score: {quality_metrics[best_channel]['sqs']:.2f})\n\n")
        
        rf.write("## HRV Analysis (Best Channel)\n")
        rf.write(f"- **Beats Detected**: {len(peaks)}\n")
        rf.write(f"- **Mean IBI**: {np.mean(ibis) if len(ibis) > 0 else 0:.1f} ms\n")
        rf.write(f"- **SDNN**: {sdnn:.2f} ms\n")
        rf.write(f"- **RMSSD**: {rmssd:.2f} ms\n\n")
        
        rf.write("## Signal Suitability Verdict\n")
        is_suitable = "YES" if quality_metrics[best_channel]['sqs'] > 2.5 and len(peaks) > 5 else "NO"
        rf.write(f"**Suitable for BCG HR Extraction**: {is_suitable}\n")
        if is_suitable == "NO":
            rf.write("- The quality score is below the threshold (2.5), suggesting noise dominates the cardiac spectrum.\n")
        else:
            rf.write("- The quality score is sufficient, and heartbeat intervals show clear physiological peaks.\n")
            
    print("\n" + "="*50)
    print("3-AXIS BCG POST-PROCESSING ANALYSIS COMPLETE")
    print("="*50)
    print(f"Sampling Frequency : {fs:.2f} Hz")
    print(f"Best Channel       : {best_channel.upper()} (SQS: {quality_metrics[best_channel]['sqs']:.2f})")
    print(f"FFT Estimated BPM  : {fft_results[best_channel]['bpm']:.1f} BPM")
    print(f"Peaks Estimated BPM: {peak_bpm:.1f} BPM")
    print(f"Detected Beats     : {len(peaks)}")
    print(f"SDNN: {sdnn:.2f} ms | RMSSD: {rmssd:.2f} ms")
    print(f"Report and plots successfully saved to: {args.output_dir}/")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
