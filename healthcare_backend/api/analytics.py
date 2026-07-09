"""Analytics routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User
from healthcare_backend.services.analytics import compute_analytics

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/{patient_id}", summary="Get analytics for a patient (last 7 days)")
def get_analytics(
    patient_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return compute_analytics(db, patient_id)
