# Comprehensive User Guide

Welcome to the BCG Healthcare Platform. This guide outlines how to operate the monitoring tools and navigate the web dashboard.

## 1. Web Dashboard (Frontend)

The web dashboard is the primary interface for managing patients and reviewing clinical data.

### Authentication
- **Default Admin:** `admin` / `admin123`
- **Default Doctors:** `doctor1` / `doctor123` | `doctor2` / `doctor456`

### Patients Page
- View a list of all registered patients.
- Click on a patient to view their **Patient Details**, which includes:
  - **Demographics** (Age, Weight, Medical History).
  - **Session History:** A log of all completed monitoring sessions, including start/end times, heart rate ranges, and packet counts.
  - **Charts:** Historical AI Score and Heart Rate trends over the last 7 days.

### Live Monitoring
- Go to the **Live** tab to start monitoring a patient.
- Select a patient from the dropdown and click **Start Monitoring**.
- The page will connect to the backend and display live metrics (Heart Rate, SQS, Temperature, Humidity).
- Click **Stop Monitoring** to flush the final data and save the session to the database.

### Analytics & Exports
- **Analytics:** Compare heart rate and signal quality across different patients to identify anomalies.
- **Exports:** Download a CSV file containing all granular scan data for a specific patient over a selected date range.

---

## 2. Local Dashboard & Simulation (`bcg_live.py`)

When you run `python bcg_live.py`, a Matplotlib dashboard appears. This is useful for localized debugging and hardware monitoring.

### Simulation Controls
At the bottom of the window, you will find three buttons:
- **Resume Live Data:** Returns the system to normal tracking.
- **Simulate Bradycardia:** Forces the simulated heart rate down to 42 BPM.
- **Simulate Tachycardia:** Forces the simulated heart rate up to 145 BPM.

### Email Alerts
Clicking the Bradycardia or Tachycardia buttons triggers an emergency alert.
To enable real email delivery for these alerts:
1. Open `bcg_live.py` and locate the `send_alert_email` function (around line 70).
2. Generate a **16-character App Password** from your Google Account Security settings.
3. Paste the App Password into the `password` variable.
4. Restart `bcg_live.py`.

---

## 3. Backend Alerting System

The backend (`healthcare_backend`) runs an independent alerting system. 
- During an active session on the web dashboard, if the `bcg_bridge.py` posts a scan with a Heart Rate **> 100 BPM** or **< 55 BPM**, the backend will automatically generate a Warning Alert.
- These alerts are saved in the database and a simulated email log is printed directly to the backend terminal (`main.py`).
