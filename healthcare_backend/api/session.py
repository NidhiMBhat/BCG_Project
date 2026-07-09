"""Monitoring session routes"""
import logging
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


@router.post("/stop", summary="Stop the current monitoring session")
def stop_session(current_user: User = Depends(require_role("admin", "doctor"))):
    prev = session_manager.active_patient_id
    session_manager.stop_session()
    logger.info(f"Monitoring session stopped (was patient={prev}) by {current_user.username}")
    return {"status": "stopped", "previous_patient_id": prev}


@router.get("/status", summary="Get current session status")
def get_session_status(_: User = Depends(get_current_user)):
    return session_manager.get_status()
