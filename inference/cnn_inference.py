#!/usr/bin/env python3
"""
CNN Inference Module for Heart Rhythm Classification
Author: Antigravity AI
"""

import os
import numpy as np
import scipy.signal as signal
import tensorflow as tf

class ECGClassifier:
    def __init__(self, model_path=None):
        if model_path is None:
            # Default path relative to this script
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'cnn_model.keras'))
        
        print(f"Loading CNN model from: {model_path}")
        self.model = tf.keras.models.load_model(model_path)
        self.classes = {0: "Bradycardia", 1: "Normal", 2: "Tachycardia"}
        
    def predict(self, raw_window_signal, fs):
        """
        Input:
            raw_window_signal: numpy array of the 10-second signal window
            fs: float, sampling rate of the signal
        Output:
            dict containing:
                "prediction": "Bradycardia" | "Normal" | "Tachycardia"
                "confidence": float (0.0 to 100.0)
        """
        # 1. Resample to 100 Hz (1000 samples)
        # 10 seconds of data should be resampled to 1000 samples
        target_samples = 1000
        if len(raw_window_signal) != target_samples:
            sig_resampled = signal.resample(raw_window_signal, target_samples)
        else:
            sig_resampled = raw_window_signal
            
        # 2. Standardize identically to training
        std = np.std(sig_resampled)
        if std > 0:
            sig_standardized = (sig_resampled - np.mean(sig_resampled)) / std
        else:
            sig_standardized = sig_resampled - np.mean(sig_resampled)
            
        # 3. Shape input for Conv1D: (1, 1000, 1)
        input_data = np.expand_dims(sig_standardized, axis=(0, -1))
        
        # 4. Predict
        probs = self.model.predict(input_data, verbose=0)[0]
        class_idx = int(np.argmax(probs))
        confidence = float(probs[class_idx]) * 100.0
        
        return {
            "prediction": self.classes[class_idx],
            "confidence": round(confidence, 2)
        }

if __name__ == "__main__":
    # Test classifier with a dummy signal
    classifier = ECGClassifier()
    dummy_signal = np.sin(2 * np.pi * 1.2 * np.linspace(0, 10, 1000))  # 1.2 Hz normal heart rate (72 BPM)
    result = classifier.predict(dummy_signal, 100.0)
    print("Test prediction result:", result)
