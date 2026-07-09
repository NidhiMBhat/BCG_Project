"""Monitoring session routes"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.patient import Patient
from healthcare_backend.auth.dependencies import get_current_user, require_role
from healthcare_backend.models.user import User
from healthcare_backend.services.session import session_manager
from healthcare_backend.services.ai_score import reset_smoothing

router = APIRouter(prefix="/session", tags=["Session"])
logger = logging.getLogger("bcg.session")


@router.post("/start", summary="Start a monitoring session for a patient")
def start_session(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    session_manager.start_session(patient_id)
    reset_smoothing()
    logger.info(f"Monitoring session started: patient={patient_id} by {current_user.username}")
    return {
        "status": "started",
        "patient_id": patient_id,
        "patient_name": patient.name,
        "patient_code": patient.patient_code,
    }


from datetime import datetime
from healthcare_backend.models.monitoring_session import MonitoringSession

@router.post("/stop", summary="Stop the current monitoring session")
def stop_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "doctor"))
):
    prev = session_manager.active_patient_id
    summary = session_manager.stop_session()
    
    if summary and summary["patient_id"]:
        start_dt = datetime.fromtimestamp(summary["start_time"]) if summary["start_time"] else datetime.utcnow()
        session_record = MonitoringSession(
            patient_id=summary["patient_id"],
            start_time=start_dt,
            end_time=datetime.utcnow(),
            lowest_heart_rate=summary["lowest_heart_rate"],
            highest_heart_rate=summary["highest_heart_rate"],
            packet_count=summary["packet_count"]
        )
        db.add(session_record)
        db.commit()
        db.refresh(session_record)
    
    logger.info(f"Monitoring session stopped (was patient={prev}) by {current_user.username}")
    return {"status": "stopped", "previous_patient_id": prev}

@router.get("/patients/{patient_id}/sessions", summary="Get all completed sessions for a patient")
def get_patient_sessions(
    patient_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    sessions = (
        db.query(MonitoringSession)
        .filter(MonitoringSession.patient_id == patient_id)
        .order_by(MonitoringSession.start_time.desc())
        .all()
    )
    # Return as dicts for simple serialization
    return [
        {
            "id": s.id,
            "patient_id": s.patient_id,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "lowest_heart_rate": s.lowest_heart_rate,
            "highest_heart_rate": s.highest_heart_rate,
            "packet_count": s.packet_count
        }
        for s in sessions
    ]

@router.get("/status", summary="Get current session status")
def get_session_status(_: User = Depends(get_current_user)):
    return session_manager.get_status()


from pydantic import BaseModel
class TelemetryData(BaseModel):
    packets_received: int
    current_heart_rate: Optional[float] = None

@router.post("/telemetry", summary="Ingest lightweight telemetry from bridge")
def ingest_telemetry(data: TelemetryData):
    session_manager.record_telemetry(data.packets_received, data.current_heart_rate)
    return {"status": "ok"}
