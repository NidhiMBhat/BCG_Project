import math
import numpy as np
from collections import deque
from scipy.signal import butter, filtfilt, find_peaks, detrend

# Try importing CNN classifier
try:
    from inference.cnn_inference import ECGClassifier
except ImportError:
    ECGClassifier = None

class BCGProcessor:
    def __init__(self, window_size=10.0, fs=100.0):
        self.window_size = window_size
        self.fs = fs
        self.max_len = int(window_size * fs)  # 1000 samples for 10s at 100Hz
        
        # Buffers for raw data
        self.time_buffer = deque(maxlen=self.max_len)
        self.ax_buffer = deque(maxlen=self.max_len)
        self.ay_buffer = deque(maxlen=self.max_len)
        self.az_buffer = deque(maxlen=self.max_len)
        self.occupancy_buffer = deque(maxlen=self.max_len)
        self.temp_buffer = deque(maxlen=self.max_len)
        self.humidity_buffer = deque(maxlen=self.max_len)
        
        # Heart rate stability tracking
        self.bpm_history = deque(maxlen=15)
        self.running_avg_bpm = 0.0
        self.bpm_std = 0.0
        self.stability_flag = "Stable"
        
        # Load Classifier
        self.classifier = None
        if ECGClassifier is not None:
            try:
                self.classifier = ECGClassifier()
                print("ECG Rhythm Classifier loaded successfully in backend.")
            except Exception as e:
                print(f"Error loading ECG Rhythm Classifier in backend: {e}")

    def add_sample(self, t_ms, ax, ay, az, occupancy, temp, humidity):
        self.time_buffer.append(t_ms / 1000.0)
        self.ax_buffer.append(ax)
        self.ay_buffer.append(ay)
        self.az_buffer.append(az)
        self.occupancy_buffer.append(occupancy)
        self.temp_buffer.append(temp if temp is not None else float('nan'))
        self.humidity_buffer.append(humidity if humidity is not None else float('nan'))

    def process(self):
        if len(self.time_buffer) < 40:
            return None
            
        t = np.array(self.time_buffer)
        ax = np.array(self.ax_buffer)
        ay = np.array(self.ay_buffer)
        az = np.array(self.az_buffer)
        occ = np.array(self.occupancy_buffer)
        temp = np.array(self.temp_buffer)
        hum = np.array(self.humidity_buffer)
        
        # Remove NaNs
        finite_mask = np.isfinite(t) & np.isfinite(ax) & np.isfinite(ay) & np.isfinite(az)
        if not np.any(finite_mask) or np.sum(finite_mask) < 15:
            return None
            
        t_w = t[finite_mask]
        ax_w = ax[finite_mask]
        ay_w = ay[finite_mask]
        az_w = az[finite_mask]
        occ_w = occ[finite_mask]
        temp_w = temp[finite_mask]
        hum_w = hum[finite_mask]
        
        dt_win = np.median(np.diff(t_w))
        fs = 1.0 / dt_win if dt_win > 0 else self.fs
        
        # Butterworth Bandpass Filter
        nyq = 0.5 * fs
        low_cut = 0.8
        high_cut = min(4.0, nyq - 0.5)
        b, a = butter(4, [low_cut / nyq, high_cut / nyq], btype='band')
        
        # Detrending
        ax_dt, ay_dt, az_dt = detrend(ax_w), detrend(ay_w), detrend(az_w)
        mag_w = np.sqrt(ax_w**2 + ay_w**2 + az_w**2)
        mag_dt = detrend(mag_w)
        
        # Filtering
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
            
            fft_data[ch] = {
                'freqs': fft_freqs.tolist(),
                'mags': fft_mag.tolist(),
                'bpm': float(bpm)
            }
            quality_metrics[ch] = {
                'rms': float(rms),
                'var': float(var),
                'ptp': float(ptp),
                'sqs': float(sqs)
            }
            
        best_channel = max(['ax', 'ay', 'az'], key=lambda c: quality_metrics[c]['sqs'])
        best_sig = signals[best_channel]
        
        current_occ = int(occ_w[-1]) if len(occ_w) > 0 else 1
        current_temp = float(temp_w[-1]) if len(temp_w) > 0 else float('nan')
        current_hum = float(hum_w[-1]) if len(hum_w) > 0 else float('nan')
        
        # Rhythm prediction
        pred_label = "Waiting for Data"
        confidence = 0.0
        required_samples = int(10.0 * fs)
        
        if current_occ == 1 and len(t_w) >= required_samples:
            if self.classifier is not None:
                try:
                    inf_res = self.classifier.predict(best_sig, fs)
                    pred_label = inf_res["prediction"]
                    confidence = float(inf_res["confidence"])
                except Exception as e:
                    print(f"Server classification error: {e}")
        else:
            pred_label = "Waiting for Data"
            confidence = 0.0
            
        # Peak Detection
        peaks_indices = []
        if current_occ == 1:
            prom = 0.25 * np.std(best_sig)
            dist = int(0.22 * fs)
            peaks, _ = find_peaks(best_sig, distance=dist, prominence=prom)
            peaks_indices = peaks.tolist()
            
            current_bpm = fft_data[best_channel]['bpm']
            clamped_bpm = float(np.clip(current_bpm, 60.0, 100.0)) if current_bpm > 0 else 0.0
            if current_bpm > 0:
                self.bpm_history.append(clamped_bpm)
                
            if len(self.bpm_history) >= 5:
                self.running_avg_bpm = float(np.mean(self.bpm_history))
                self.bpm_std = float(np.std(self.bpm_history))
                self.stability_flag = "Stable" if self.bpm_std <= 10.0 else "Arrhythmia Transition Active"
            else:
                self.running_avg_bpm = clamped_bpm
                self.bpm_std = 0.0
                self.stability_flag = "Calculating..."
        else:
            self.running_avg_bpm = 0.0
            self.bpm_std = 0.0
            self.stability_flag = "Monitoring Paused"
            
        # SQS score and confidence score
        best_sqs = quality_metrics[best_channel]['sqs']
        sqs_conf = min(100.0, max(0.0, (best_sqs - 1.0) * 10.0))
        stab_conf = min(100.0, max(0.0, 100.0 - (self.bpm_std * 5.0)))
        confidence_score = float(0.6 * sqs_conf + 0.4 * stab_conf) if current_occ == 1 else 0.0

        # Downsample signals to send a lightweight update (e.g. last 400 points)
        # to visual clients to preserve bandwidth
        view_len = 400
        slice_idx = -view_len
        
        result = {
            "time_w": (t_w[slice_idx:] - t_w[0]).tolist(),
            "ax_dt": ax_dt[slice_idx:].tolist(),
            "ay_dt": ay_dt[slice_idx:].tolist(),
            "az_dt": az_dt[slice_idx:].tolist(),
            "ax_f": ax_f[slice_idx:].tolist(),
            "ay_f": ay_f[slice_idx:].tolist(),
            "az_f": az_f[slice_idx:].tolist(),
            "mag_f": mag_f[slice_idx:].tolist(),
            "peaks_x": (t_w[peaks_indices] - t_w[0]).tolist() if len(peaks_indices) > 0 else [],
            "peaks_y": best_sig[peaks_indices].tolist() if len(peaks_indices) > 0 else [],
            
            "fft_freqs": fft_data[best_channel]['freqs'],
            "fft_mags": fft_data[best_channel]['mags'],
            "fft_mag_freqs": fft_data['magnitude']['freqs'],
            "fft_mag_mags": fft_data['magnitude']['mags'],
            
            "best_channel": best_channel,
            "sqs": best_sqs,
            "confidence_score": confidence_score,
            "rhythm_prediction": pred_label,
            "rhythm_confidence": confidence,
            
            "occupancy": current_occ,
            "temp": current_temp if np.isfinite(current_temp) else None,
            "humidity": current_hum if np.isfinite(current_hum) else None,
            "bpm": self.running_avg_bpm,
            "sampling_rate": float(fs),
            "stability_flag": self.stability_flag
        }
        
        return result
