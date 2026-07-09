"""Alert Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    patient_id: int
    scan_id: Optional[int]
    severity: str
    message: str
    created_at: datetime

    model_config = {"from_attributes": True}
