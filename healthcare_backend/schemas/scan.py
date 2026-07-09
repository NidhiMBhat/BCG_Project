"""Scan Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ScanIngest(BaseModel):
    """Posted by bcg_bridge.py when a new scan window is ready."""
    patient_id: int
    timestamp: Optional[datetime] = None
    heart_rate: Optional[float] = None
    lowest_heart_rate: Optional[float] = None
    highest_heart_rate: Optional[float] = None
    signal_quality: str = "Good"


class ScanCreate(BaseModel):
    patient_id: int
    timestamp: Optional[datetime] = None
    heart_rate: Optional[float] = None
    lowest_heart_rate: Optional[float] = None
    highest_heart_rate: Optional[float] = None
    signal_quality: str = "Good"
    ai_health_score: Optional[float] = None
    notes: Optional[str] = None


class ScanUpdate(BaseModel):
    notes: Optional[str] = None


class ScanOut(BaseModel):
    id: int
    patient_id: int
    timestamp: datetime
    heart_rate: Optional[float]
    lowest_heart_rate: Optional[float]
    highest_heart_rate: Optional[float]
    signal_quality: Optional[str]
    ai_health_score: Optional[float]
    notes: Optional[str]

    model_config = {"from_attributes": True}
