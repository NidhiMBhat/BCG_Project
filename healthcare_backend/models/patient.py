"""Patient ORM model"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from healthcare_backend.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    height = Column(Float, nullable=True)   # cm
    weight = Column(Float, nullable=True)   # kg
    blood_group = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
