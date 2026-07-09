"""Scan ORM model"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from healthcare_backend.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    heart_rate = Column(Float, nullable=True)        # BPM
    respiration_rate = Column(Float, nullable=True)  # breaths/min
    sdnn = Column(Float, nullable=True)              # ms
    rmssd = Column(Float, nullable=True)             # ms
    motion_detected = Column(Boolean, default=False)
    signal_quality = Column(String, nullable=True)   # Excellent / Good / Moderate / Poor
    ai_health_score = Column(Float, nullable=True)   # 0-100
    ai_confidence = Column(Float, nullable=True)     # 0-100
    risk_level = Column(String, nullable=True)       # Low / Medium / High
    notes = Column(Text, nullable=True)
