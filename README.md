# Contactless Ballistocardiography (BCG) Monitoring System

A contactless, accelerometer-based heart-rate (BPM) and Heart Rate Variability (HRV) analysis pipeline and real-time dashboard designed for an MPU6050 accelerometer connected to an ESP32.

---

## 🛠️ Hardware Requirements & Configuration

For reliable BCG extraction, the ESP32 firmware should be configured as follows:
1. **Accelerometer Scale**: Set to $\pm$ 2g range to maximize measurement resolution:
   ```cpp
   mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_2);
   ```
2. **Digital Low-Pass Filter (DLPF)**: Enable the on-chip low-pass filter at 10 Hz (or 5 Hz) to suppress high-frequency electronic noise:
   ```cpp
   mpu.setDLPFMode(MPU6050_DLPF_BW_10);
   ```
3. **Sampling Rate**: Sample at a fixed **100 Hz rate** using a `micros()` loop to ensure uniform time intervals.
4. **Mechanical Coupling**: Mount the MPU6050 accelerometer **rigidly** to the solid frame or underside of the seat back/panel. Avoid mounting on soft fabrics or cushions which dampen micro-vibrations.

---

## 🚀 Getting Started

### 1. Installation
Install the necessary Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Post-Hoc Analysis (`bcg_pipeline.py`)
Processes a completed recording CSV file, designs a 0.8–4.0 Hz Butterworth bandpass filter, performs FFT frequency analysis, calculates HRV metrics, evaluates the best axis based on a Signal Quality Score (SQS), and exports plots.

**Run command**:
```bash
python bcg_pipeline.py --input bcg_data.csv --output_dir results/
```

This generates:
* `results/raw_axes.png` - Visualizes AX, AY, and AZ signals.
* `results/filtered_peaks.png` - Plots filtered axes and highlights detected beats on the best channel.
* `results/fft_spectra.png` - Frequency spectra for all channels.
* `results/bcg_3axis_report.md` - Complete quality analysis and heart rate statistics.

---

## 📊 Live Rolling Dashboard (`bcg_live.py`)

The dynamic dashboard updates a 2x2 grid in real-time, showing raw signals, filtered channels, active FFT spectra, and rolling diagnostics.

### Mode A: Monitor a Growing CSV (Simulation / Live Logging)
If you are logging raw serial data into a CSV in the background:
```bash
python bcg_live.py --mode file --file bcg_data.csv --window 10
```

### Mode B: Direct Serial Connection
Connect directly to the live ESP32 serial stream (does not require external logger scripts). It will stream the data, run the visualizer, and simultaneously log raw readings to a CSV in the background:
```bash
python bcg_live.py --mode serial --port COM5 --baud 115200 --window 10 --log_file live_bcg_output.csv
```

---

## 📁 Repository Structure

* [bcg_pipeline.py](file:///Users/shash/Downloads/IoT/BCG_Project/bcg_pipeline.py) - Post-hoc diagnostic analysis script.
* [bcg_live.py](file:///Users/shash/Downloads/IoT/BCG_Project/bcg_live.py) - Live rolling dashboard.
* [process.py](file:///Users/shash/Downloads/IoT/BCG_Project/process.py) - Basic background serial logging script.
* [requirements.txt](file:///Users/shash/Downloads/IoT/BCG_Project/requirements.txt) - Python package dependencies.
* `.gitignore` - Standard configuration ignoring compiled cache and local logs.
