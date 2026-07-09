"""User ORM model"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum
from healthcare_backend.database import Base
import enum


class UserRole(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    patient = "patient"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="doctor")
    linked_patient_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
