"""Patient Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PatientCreate(BaseModel):
    patient_code: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_group: Optional[str] = None


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    blood_group: Optional[str] = None


class PatientOut(BaseModel):
    id: int
    patient_code: str
    name: str
    age: Optional[int]
    gender: Optional[str]
    height: Optional[float]
    weight: Optional[float]
    blood_group: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
