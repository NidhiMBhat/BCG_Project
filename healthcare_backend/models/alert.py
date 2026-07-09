"""Alert ORM model"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from healthcare_backend.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=True)
    severity = Column(String, nullable=False)   # info / warning / critical
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
