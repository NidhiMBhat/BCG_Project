# BCG Healthcare Platform

An end-to-end Ballistocardiography (BCG) monitoring system designed for real-time patient heart-rate and respiratory analysis. This platform captures live sensor data (via ESP32), processes it with signal filtering and AI heuristics, and visualizes it through both a localized Matplotlib dashboard and a modern web application.

## System Architecture

The platform is decoupled into four main components:

1. **Live Capture & Dashboard (`bcg_live.py`)**
   - Connects to a live ESP32 TCP server or runs in simulation mode.
   - Filters and displays raw BCG signals, Fast Fourier Transform (FFT) spectrum, and vital metrics via a Matplotlib GUI.
   - Logs incoming data to `live_bcg_output.csv`.
   - Exposes a live MJPEG camera feed on port 8002.
   - Supports injecting Arrhythmia simulations (Tachycardia / Bradycardia) and dispatching SMTP email alerts.

2. **Backend Bridge (`bcg_bridge.py`)**
   - Runs in the background and continuously tails the `live_bcg_output.csv` file.
   - Aggregates data into 10-second windows and calculates detailed physiological metrics (Heart Rate, Respiration Rate, Signal Quality Score, AI Health Score).
   - Syncs the calculated scans to the FastAPI backend when a monitoring session is active.

3. **FastAPI Backend (`healthcare_backend/`)**
   - REST API running on port 8001 (`http://localhost:8001`).
   - Manages SQLite database persistence for Patients, Scans, Monitoring Sessions, and Alerts.
   - Exposes endpoints for the React frontend.

4. **React Frontend (`frontend/`)**
   - Vite + React web application running on port 5174.
   - Provides an intuitive UI for doctors and admins to manage patients, view live monitoring telemetry, review session history, analyze trends, and export data.

## Getting Started

### 1. Start the Backend Server
```bash
python healthcare_backend/main.py
```
*(The backend runs on `http://0.0.0.0:8001`)*

### 2. Start the Frontend Web App
```bash
cd frontend
npm install
npm run dev
```
*(The frontend runs on `http://localhost:5174`)*

### 3. Start the Live Sensor Capture (or Simulator)
```bash
python bcg_live.py
```
*(This opens the local Matplotlib dashboard and begins writing to `live_bcg_output.csv`)*

### 4. Start the Bridge 
```bash
python bcg_bridge.py
```
*(This bridges the CSV data to the backend API)*
