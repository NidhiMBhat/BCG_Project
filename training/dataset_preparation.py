#!/usr/bin/env python3
"""
MIT-BIH Dataset Preparation for Heart Rhythm Classification
Author: Antigravity AI
"""

import os
import numpy as np
import scipy.signal as signal
import wfdb

# MIT-BIH Arrhythmia Database record list
MIT_BIH_RECORDS = [
    '100', '101', '102', '103', '104', '105', '106', '107', '108', '109',
    '111', '112', '113', '114', '115', '116', '117', '118', '119', '121',
    '122', '123', '124', '200', '201', '202', '203', '205', '207', '208',
    '209', '210', '212', '213', '214', '215', '217', '219', '220', '221',
    '222', '223', '228', '230', '231', '232', '233', '234'
]

# We will use the first 35 records to ensure a fast yet diverse download and balanced classes
RECORDS_TO_USE = MIT_BIH_RECORDS[:35]

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    print(f"Starting MIT-BIH dataset preparation. Saving outputs to: {DATA_DIR}")
    
    X_list = []
    y_list = []
    
    for i, record_name in enumerate(RECORDS_TO_USE):
        print(f"[{i+1}/{len(RECORDS_TO_USE)}] Loading record {record_name} from PhysioNet...")
        try:
            # Load record signal and annotations directly from PhysioNet mitdb
            record = wfdb.rdrecord(record_name, pn_dir='mitdb')
            annotation = wfdb.rdann(record_name, 'atr', pn_dir='mitdb')
            
            # Use channel 0 (usually MLII / Lead II)
            sig = record.p_signal[:, 0]
            fs = record.fs  # 360 Hz
            
            # Filter signal to remove baseline wander and powerline noise
            # Lowpass filtering at 40 Hz and Highpass filtering at 0.5 Hz (similar to standard ECG processing)
            nyq = 0.5 * fs
            b, a = signal.butter(4, [0.5 / nyq, 40.0 / nyq], btype='band')
            sig_filtered = signal.filtfilt(b, a, sig)
            
            # Segment into 10-second windows (non-overlapping)
            window_duration = 10  # seconds
            samples_per_window = int(window_duration * fs)  # 3600 samples
            num_windows = len(sig_filtered) // samples_per_window
            
            # Beat indices in samples
            beat_samples = np.array(annotation.sample)
            
            for w in range(num_windows):
                start_sample = w * samples_per_window
                end_sample = start_sample + samples_per_window
                
                # Extract signal window
                sig_window = sig_filtered[start_sample:end_sample]
                
                # Resample to 100 Hz (1000 samples)
                sig_resampled = signal.resample(sig_window, 1000)
                
                # Standardize signal window (zero mean, unit variance)
                std = np.std(sig_resampled)
                if std > 0:
                    sig_standardized = (sig_resampled - np.mean(sig_resampled)) / std
                else:
                    sig_standardized = sig_resampled - np.mean(sig_resampled)
                
                # Count beats in this 10-second window
                beats_in_window = np.sum((beat_samples >= start_sample) & (beat_samples < end_sample))
                
                # Calculate BPM: beats in 10s * 6
                bpm = beats_in_window * 6.0
                
                # Labels: 0 = Bradycardia (<60 BPM), 1 = Normal (60-100 BPM), 2 = Tachycardia (>100 BPM)
                if bpm < 60.0:
                    label = 0
                elif bpm <= 100.0:
                    label = 1
                else:
                    label = 2
                    
                X_list.append(sig_standardized)
                y_list.append(label)
                
        except Exception as e:
            print(f"Error loading record {record_name}: {e}")
            
    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    
    # Reshape X to (number_of_windows, 1000, 1)
    X = np.expand_dims(X, axis=-1)
    
    print(f"\nDataset Preparation Complete!")
    print(f"Total samples: {len(X)}")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    
    # Class distribution
    unique, counts = np.unique(y, return_counts=True)
    class_map = {0: "Bradycardia", 1: "Normal", 2: "Tachycardia"}
    for u, c in zip(unique, counts):
        print(f"  Class {u} ({class_map[u]}): {c} samples ({c/len(y)*100:.2f}%)")
        
    # Save the processed dataset
    np.save(os.path.join(DATA_DIR, 'X.npy'), X)
    np.save(os.path.join(DATA_DIR, 'y.npy'), y)
    print("Files X.npy and y.npy saved successfully in /data folder.")

if __name__ == "__main__":
    main()
