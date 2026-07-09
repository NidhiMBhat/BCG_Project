"""Alert routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User
from healthcare_backend.models.alert import Alert
from healthcare_backend.schemas.alert import AlertOut

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertOut], summary="List all alerts (optionally filter by patient)")
def list_alerts(
    patient_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Alert).order_by(Alert.created_at.desc())
    if patient_id:
        q = q.filter(Alert.patient_id == patient_id)
    return q.limit(limit).all()


@router.get("/{patient_id}", response_model=List[AlertOut], summary="Get alerts for a specific patient")
def get_patient_alerts(
    patient_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(Alert)
        .filter(Alert.patient_id == patient_id)
        .order_by(Alert.created_at.desc())
        .limit(100)
        .all()
    )
