#!/usr/bin/env python3
"""
BCG Healthcare Platform — FastAPI Backend
==========================================
Port: 8001
Docs: http://localhost:8001/docs

Run with:
    python healthcare_backend/main.py
or:
    uvicorn healthcare_backend.main:app --host 0.0.0.0 --port 8001 --reload
"""
import logging
import sys
import os

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from healthcare_backend.config import APP_NAME, APP_VERSION, BACKEND_PORT
from healthcare_backend.database import init_db, SessionLocal
from healthcare_backend.services.seeder import seed_database

# Routers
from healthcare_backend.api.auth import router as auth_router
from healthcare_backend.api.patients import router as patients_router
from healthcare_backend.api.scans import router as scans_router
from healthcare_backend.api.session import router as session_router
from healthcare_backend.api.live import router as live_router
from healthcare_backend.api.analytics import router as analytics_router
from healthcare_backend.api.alerts import router as alerts_router
from healthcare_backend.api.export import router as export_router
from healthcare_backend.api.settings import router as settings_router
from healthcare_backend.api.stream import router as stream_router

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("healthcare_backend.log"),
    ],
)
logger = logging.getLogger("bcg.main")

# ── App ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "BCG Healthcare Platform — Independent application layer over the existing ESP32 → TCP → Python pipeline.\n\n"
        "**Note**: This is a demonstration system. AI health scores are heuristic estimates and NOT medical diagnoses.\n\n"
        "Default credentials:\n"
        "- `admin` / `admin123` (Admin)\n"
        "- `doctor1` / `doctor123` (Doctor)\n"
        "- `doctor2` / `doctor456` (Doctor)\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(scans_router)
app.include_router(session_router)
app.include_router(live_router)
app.include_router(analytics_router)
app.include_router(alerts_router)
app.include_router(export_router)
app.include_router(settings_router)
app.include_router(stream_router, prefix="/api/live", tags=["stream"])

# ── Startup ──────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {APP_NAME} v{APP_VERSION} on port {BACKEND_PORT}")
    init_db()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    logger.info("Backend ready. Swagger: http://localhost:8001/docs")


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
        "docs": "http://localhost:8001/docs",
    }


@app.get("/health", tags=["Health"], summary="Detailed health check")
def health():
    import os
    from healthcare_backend.config import DB_PATH
    from healthcare_backend.services.session import session_manager
    return {
        "status": "healthy",
        "database": "ok" if os.path.exists(DB_PATH) else "missing",
        "session": session_manager.get_status(),
    }


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "healthcare_backend.main:app",
        host="0.0.0.0",
        port=BACKEND_PORT,
        reload=False,
        log_level="info",
    )
