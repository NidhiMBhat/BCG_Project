# 3-Axis BCG Signal Processing Report

## Recording Overview
- **Sampling Frequency**: 90.91 Hz
- **Duration**: 57.62 seconds
- **Total Samples**: 5239

## Channel Heart Rate Estimates
| Channel | FFT BPM | Peak Detection BPM |
|---|---|---|
| AX | 108.3 | 84.8 |
| AY | 108.3 | 83.7 |
| AZ | 123.9 | 85.8 |
| MAGNITUDE | 123.9 | 88.8 |

## Signal Quality Metrics (SQS)
| Channel | RMS | Variance | Peak-to-Peak | FFT Peak Mag | Quality Score (SQS) |
|---|---|---|---|---|---|
| AX | 3.70 | 13.66 | 25.86 | 2285.15 | 15.42 |
| AY | 2.31 | 5.35 | 16.44 | 1461.61 | 15.51 |
| AZ | 14.41 | 207.51 | 97.24 | 8551.25 | 15.23 |
| MAGNITUDE | 15.01 | 225.27 | 101.68 | 8924.68 | 15.22 |

**Automatically Determined Best Channel**: **AY** (Quality Score: 15.51)

## HRV Analysis (Best Channel)
- **Beats Detected**: 80
- **Mean IBI**: 716.5 ms
- **SDNN**: 178.74 ms
- **RMSSD**: 235.82 ms

## Signal Suitability Verdict
**Suitable for BCG HR Extraction**: YES
- The quality score is sufficient, and heartbeat intervals show clear physiological peaks.
