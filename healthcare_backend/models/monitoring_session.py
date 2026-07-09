from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from healthcare_backend.database import Base

class MonitoringSession(Base):
    __tablename__ = "monitoring_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    lowest_heart_rate = Column(Float, nullable=True)
    highest_heart_rate = Column(Float, nullable=True)
    packet_count = Column(Integer, default=0)

    # Relationships
    patient = relationship("Patient")
