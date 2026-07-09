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
    lowest_heart_rate = Column(Float, nullable=True) # BPM
    highest_heart_rate = Column(Float, nullable=True)# BPM
    signal_quality = Column(String, nullable=True)   # Excellent / Good / Moderate / Poor
    ai_health_score = Column(Float, nullable=True)   # 0-100
    notes = Column(Text, nullable=True)
