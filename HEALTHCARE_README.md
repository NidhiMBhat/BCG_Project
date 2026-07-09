# BCG Healthcare Platform

**BCG Healthcare Platform** is an independent application layer built on top of the existing ESP32 → TCP → Python → matplotlib BCG pipeline.

> **IMPORTANT**: The original TCP receiver (`bcg_live.py`) and matplotlib dashboard are **completely unchanged** and remain fully operational. This platform is a separate, additive system that can be stopped at any time without affecting the original workflow.

---

## Architecture

```
ESP32 ──TCP──► bcg_live.py (UNCHANGED)  ──► matplotlib dashboard (UNCHANGED)
                    │
                    │ (writes live_bcg_output.csv — same as always)
                    ▼
             bcg_bridge.py  ←── NEW, reads CSV, computes scans
                    │
                    ▼ POST /scan
             healthcare_backend/  ←── NEW FastAPI on port 8001
                    │
                    ▼ SSE /live + REST
             frontend/  ←── NEW React on port 5174
```

---

## Quick Start

### 1. Install Python Dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy pydantic "python-jose[cryptography]" "passlib[bcrypt]" bcrypt python-multipart aiofiles
```

### 2. Start the Backend

```bash
cd /path/to/BCG_Project
python healthcare_backend/main.py
```

The backend will:
- Initialize `healthcare.db` (SQLite, separate from `bcg_telemetry.db`)
- Seed 5 demo patients + 3 demo users if the database is empty
- Start serving on **http://localhost:8001**
- Swagger docs at **http://localhost:8001/docs**

### 3. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at **http://localhost:5174**

### 4. Start the Bridge (optional, for live scan ingestion)

```bash
python bcg_bridge.py
```

The bridge tails `live_bcg_output.csv` and sends computed scans to the backend whenever a monitoring session is active.

---

## Default Credentials

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Admin |
| `doctor1` | `doctor123` | Doctor |
| `doctor2` | `doctor456` | Doctor |

---

## Project Structure

```
BCG_Project/
├── bcg_live.py              ← ORIGINAL TCP receiver + matplotlib (UNCHANGED)
├── bcg_pipeline.py          ← ORIGINAL offline pipeline (UNCHANGED)
├── bcg_bridge.py            ← NEW: CSV tail → backend bridge
│
├── healthcare_backend/      ← NEW: FastAPI backend
│   ├── main.py              ← App entry point (port 8001)
│   ├── config.py            ← Configuration
│   ├── database.py          ← SQLAlchemy setup
│   ├── models/              ← ORM models (User, Patient, Scan, Alert)
│   ├── schemas/             ← Pydantic schemas
│   ├── auth/                ← JWT + bcrypt auth
│   ├── services/            ← AI scoring, analytics, alerts, session, seeder
│   └── api/                 ← REST routes
│
├── frontend/                ← NEW: React healthcare dashboard
│   ├── src/
│   │   ├── pages/           ← Login, Dashboard, Patients, Live, Analytics, History, Exports, Settings
│   │   ├── components/      ← Sidebar, StatCard, ScanModal, Charts, etc.
│   │   ├── hooks/           ← useAuth, useLive, usePatients, useScans, useAnalytics
│   │   └── utils/           ← api.js, formatters.js, constants.js
│   └── package.json
│
└── healthcare.db            ← NEW: Separate SQLite database (auto-created)
```

---

## REST API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login → JWT token |
| POST | `/auth/register` | Register user (admin only) |
| GET | `/auth/me` | Current user |
| GET | `/patients/` | List patients |
| GET | `/patients/{id}` | Patient detail |
| POST | `/patients/` | Create patient |
| PUT | `/patients/{id}` | Update demographics |
| GET | `/patients/{id}/scans` | Patient scan history (filterable) |
| GET | `/scans/{id}` | Scan detail |
| PUT | `/scans/{id}/notes` | Update scan notes |
| POST | `/scan` | Ingest scan (called by bridge) |
| POST | `/session/start?patient_id=N` | Start monitoring session |
| POST | `/session/stop` | Stop monitoring session |
| GET | `/session/status` | Session state |
| GET | `/live` | SSE live stream |
| GET | `/analytics/{patient_id}` | 7-day analytics |
| GET | `/alerts/` | All alerts |
| GET | `/alerts/{patient_id}` | Patient alerts |
| GET | `/export/csv/{patient_id}` | CSV export |
| GET | `/settings/` | App settings |
| GET | `/health` | Health check |

Full Swagger docs: **http://localhost:8001/docs**

---

## How the Bridge Works

`bcg_bridge.py` is **fully decoupled** from `bcg_live.py`:

1. It watches `live_bcg_output.csv` for new rows (tailing from the end)
2. Every 10 seconds of accumulated BCG data, it computes:
   - Heart Rate (FFT-based)
   - Respiration Rate (spectral)
   - SDNN / RMSSD (peak-based HRV)
   - Signal Quality (SQS ratio)
   - Motion detection (z-variance)
3. It checks if a monitoring session is active via `GET /session/status`
4. If active, it POSTs a scan to `POST /scan`
5. The backend computes AI health score and generates alerts automatically

---

## How to Revert to Original matplotlib Workflow

1. Stop the frontend (`Ctrl+C` in the npm dev terminal)
2. Stop the backend (`Ctrl+C` in the python terminal)
3. Stop the bridge (`Ctrl+C` in the bridge terminal)
4. Run as before: `python bcg_live.py`

**No files were modified.** The original system is completely intact.

---

## Database Seeding

The database is auto-seeded on first launch:
- **5 demo patients** with realistic demographics
- **8–15 scans each**, spread across the past 7 days
- Physiologically consistent values (resting HR ↔ higher HRV, exercise HR ↔ lower HRV)
- Smooth AI health scores (no random oscillations)

To re-seed: delete `healthcare.db` and restart the backend.

---

## AI Health Score Disclaimer

> ⚠️ **AI Health Scores are heuristic demonstrations only.** They are computed using deterministic rules based on heart rate, respiration, HRV, signal quality, and motion. They are NOT medical diagnoses and should NOT be used for clinical decision-making.

---

## Ports

| Service | Port |
|---------|------|
| Original server/ (WebSocket) | 8000 |
| New healthcare backend | **8001** |
| New healthcare frontend | **5174** |
| Original bcg_live.py TCP | 5000 |
