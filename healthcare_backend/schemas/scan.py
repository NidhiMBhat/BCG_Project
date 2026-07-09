"""Scan Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScanIngest(BaseModel):
    """Posted by bcg_bridge.py when a new scan window is ready."""
    patient_id: int
    timestamp: Optional[datetime] = None
    heart_rate: Optional[float] = None
    respiration_rate: Optional[float] = None
    sdnn: Optional[float] = None
    rmssd: Optional[float] = None
    motion_detected: bool = False
    signal_quality: str = "Good"


class ScanCreate(BaseModel):
    patient_id: int
    timestamp: Optional[datetime] = None
    heart_rate: Optional[float] = None
    respiration_rate: Optional[float] = None
    sdnn: Optional[float] = None
    rmssd: Optional[float] = None
    motion_detected: bool = False
    signal_quality: str = "Good"
    ai_health_score: Optional[float] = None
    ai_confidence: Optional[float] = None
    risk_level: Optional[str] = None
    notes: Optional[str] = None


class ScanUpdate(BaseModel):
    notes: Optional[str] = None


class ScanOut(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    heart_rate: Optional[float]
    respiration_rate: Optional[float]
    sdnn: Optional[float]
    rmssd: Optional[float]
    motion_detected: bool
    signal_quality: Optional[str]
    ai_health_score: Optional[float]
    ai_confidence: Optional[float]
    risk_level: Optional[str]
    notes: Optional[str]

    model_config = {"from_attributes": True}
