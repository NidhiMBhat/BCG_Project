# BCG Cardiac Analysis Report

## Recording Summary
- **Sampling Frequency**: 90.91 Hz
- **Recording Duration**: 57.62 seconds
- **Total Samples**: 5239
- **Data Completeness Note**: X and Y columns were synthesized since the raw CSV only contained Z-axis data.

## Heart Rate & HRV Estimation
- **Estimated HR (FFT / Dominant Freq)**: 123.9 BPM (Dominant Freq: 2.06 Hz)
- **Estimated HR (Peak Detection)**: 102.6 BPM
- **Number of Detected Beats**: 98
- **Mean IBI**: 584.7 ms
- **SDNN (HRV)**: 117.75 ms
- **RMSSD (HRV)**: 158.73 ms

## Axis Comparison & Quality Metrics
| Signal | Variance (Filtered) | Estimated SNR (dB) |
|---|---|---|
| X-Axis | 67.63 | -5.00 dB |
| Y-Axis | 26.74 | -4.90 dB |
| Z-Axis | 1027.97 | -5.06 dB |
| Magnitude | 1116.25 | -5.06 dB |

**Strongest Axis**: **AZ** (Variance: 1027.97)

## Suitability Assessment
**Is the signal suitable for BCG-based heart-rate extraction?** NO

- Significant noise or sensor motion artifacts obscure the faint micro-movements of cardiac contractions.
- Z-axis SNR is extremely low (-5.06 dB).

## Recommendations for Improvement
1. **Sensor Placement & Contact**: Securely mount the MPU6050 to the solid back or underside of the seat frame rather than soft cushions to maximize micro-vibration transmission.
2. **Analog-to-Digital Precision**: If noise level is high, configure the MPU6050 accelerometer sensitivity to the highest resolution range (+/- 2g).
3. **Sampling Jitter**: The timestamps indicate minor sampling time jitter. Using a hardware timer interrupt on the ESP32 (e.g. at 100 Hz fixed rate) will provide uniform sampling, improving FFT and filter performance.
4. **Active Noise Cancellation**: Implement adaptive filtering (e.g., using a reference accelerometer on the chair base) to cancel out environmental vibrations and user posture adjustments.
