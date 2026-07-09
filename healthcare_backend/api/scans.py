"""Scan routes: ingest from bridge, list per patient, detail, update notes"""
import logging
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.scan import Scan
from healthcare_backend.models.patient import Patient
from healthcare_backend.schemas.scan import ScanOut, ScanUpdate, ScanIngest
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User
from healthcare_backend.services.ai_score import compute_ai_score
from healthcare_backend.services.alerts import evaluate_and_create_alerts
from healthcare_backend.services.session import session_manager

router = APIRouter(tags=["Scans"])
logger = logging.getLogger("bcg.scans")


@router.get(
    "/patients/{patient_id}/scans",
    response_model=List[ScanOut],
    summary="Get all scans for a patient",
)
def get_patient_scans(
    patient_id: int,
    start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter to this date (YYYY-MM-DD)"),
    search: Optional[str] = Query(None, description="Search notes"),
    sort: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if not db.query(Patient).filter(Patient.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient not found")

    q = db.query(Scan).filter(Scan.patient_id == patient_id)

    if start_date:
        q = q.filter(Scan.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        q = q.filter(Scan.timestamp <= datetime.combine(end_date, datetime.max.time()))
    if search:
        q = q.filter(Scan.notes.ilike(f"%{search}%"))

    if sort == "asc":
        q = q.order_by(Scan.timestamp.asc())
    else:
        q = q.order_by(Scan.timestamp.desc())

    total = q.count()
    offset = (page - 1) * page_size
    scans = q.offset(offset).limit(page_size).all()
    return scans


@router.get("/scans/{scan_id}", response_model=ScanOut, summary="Get scan details by ID")
def get_scan(scan_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan


@router.put("/scans/{scan_id}/notes", response_model=ScanOut, summary="Update scan notes (doctor/admin)")
def update_scan_notes(
    scan_id: int,
    data: ScanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in ("admin", "doctor"):
        raise HTTPException(status_code=403, detail="Only doctors and admins can edit notes")
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    scan.notes = data.notes
    db.commit()
    db.refresh(scan)
    logger.info(f"Scan {scan_id} notes updated by {current_user.username}")
    return scan


@router.post("/scan", response_model=ScanOut, status_code=201, summary="Ingest a scan from the BCG bridge")
def ingest_scan(data: ScanIngest, db: Session = Depends(get_db)):
    """
    Called by bcg_bridge.py. Does not require user auth (internal bridge call).
    The bridge is responsible for only calling this when a session is active.
    """
    patient_id = data.patient_id
    if not db.query(Patient).filter(Patient.id == patient_id).first():
        raise HTTPException(status_code=404, detail="Patient not found")

    # Compute AI score
    # Retrieve previous scan for smoothing
    prev_scan = (
        db.query(Scan)
        .filter(Scan.patient_id == patient_id)
        .order_by(Scan.timestamp.desc())
        .first()
    )
    prev_score = prev_scan.ai_health_score if prev_scan else None
    prev_conf = prev_scan.ai_confidence if prev_scan else None

    ai = compute_ai_score(
        data.heart_rate, data.respiration_rate, data.sdnn, data.rmssd,
        data.signal_quality, data.motion_detected, prev_score, prev_conf,
    )

    scan = Scan(
        patient_id=patient_id,
        timestamp=data.timestamp or datetime.utcnow(),
        heart_rate=data.heart_rate,
        respiration_rate=data.respiration_rate,
        sdnn=data.sdnn,
        rmssd=data.rmssd,
        motion_detected=data.motion_detected,
        signal_quality=data.signal_quality,
        ai_health_score=ai["ai_health_score"],
        ai_confidence=ai["ai_confidence"],
        risk_level=ai["risk_level"],
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    # Generate alerts
    evaluate_and_create_alerts(db, patient_id, scan.id, {
        "heart_rate": scan.heart_rate,
        "respiration_rate": scan.respiration_rate,
        "sdnn": scan.sdnn,
        "signal_quality": scan.signal_quality,
        "motion_detected": scan.motion_detected,
    })

    session_manager.record_packet()
    logger.info(f"Scan ingested: patient={patient_id} HR={data.heart_rate} score={ai['ai_health_score']}")
    return scan
