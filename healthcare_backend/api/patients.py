"""Patient CRUD routes"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.patient import Patient
from healthcare_backend.schemas.patient import PatientCreate, PatientOut, PatientUpdate
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User

router = APIRouter(prefix="/patients", tags=["Patients"])
logger = logging.getLogger("bcg.patients")


@router.get("/", response_model=List[PatientOut], summary="List all patients")
def list_patients(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Patient).order_by(Patient.id.asc()).all()


@router.get("/{patient_id}", response_model=PatientOut, summary="Get patient by ID")
def get_patient(patient_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return p


@router.post(
    "/",
    response_model=PatientOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new patient (doctor/admin)",
)
def create_patient(
    data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if db.query(Patient).filter(Patient.patient_code == data.patient_code).first():
        raise HTTPException(status_code=400, detail="Patient code already exists")
    p = Patient(**data.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    logger.info(f"Patient created: {p.patient_code} by user {current_user.username}")
    return p


@router.put("/{patient_id}", response_model=PatientOut, summary="Update patient demographics")
def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    logger.info(f"Patient {patient_id} updated by {current_user.username}")
    return p
