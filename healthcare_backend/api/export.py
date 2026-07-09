"""CSV Export routes"""
import csv
import io
import logging
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.scan import Scan
from healthcare_backend.models.patient import Patient
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User

router = APIRouter(prefix="/export", tags=["Export"])
logger = logging.getLogger("bcg.export")


@router.get("/csv/{patient_id}", summary="Export patient scans as CSV (MATLAB/Excel/Python compatible)")
def export_csv(
    patient_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    q = db.query(Scan).filter(Scan.patient_id == patient_id)
    if start_date:
        q = q.filter(Scan.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        q = q.filter(Scan.timestamp <= datetime.combine(end_date, datetime.max.time()))
    scans = q.order_by(Scan.timestamp.asc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "scan_id", "patient_id", "patient_code", "patient_name",
        "timestamp", "heart_rate_bpm", "lowest_heart_rate_bpm", "highest_heart_rate_bpm",
        "signal_quality", "ai_health_score", "notes",
    ])

    for s in scans:
        writer.writerow([
            s.id, patient_id, patient.patient_code, patient.name,
            s.timestamp.isoformat(),
            s.heart_rate, s.lowest_heart_rate, s.highest_heart_rate,
            s.signal_quality,
            s.ai_health_score,
            (s.notes or "").replace("\n", " "),
        ])

    output.seek(0)
    filename = f"BCG_{patient.patient_code}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    logger.info(f"CSV export: patient={patient_id} scans={len(scans)} by {current_user.username}")

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
