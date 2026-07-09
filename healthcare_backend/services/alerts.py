"""
Alert generation from scan data.
Produces soft clinical alerts — NOT for real clinical use.
"""
from typing import Optional
from sqlalchemy.orm import Session
from healthcare_backend.models.alert import Alert
import logging

logger = logging.getLogger("bcg.alerts")


def _save_alert(db: Session, patient_id: int, scan_id: Optional[int], severity: str, message: str):
    alert = Alert(patient_id=patient_id, scan_id=scan_id, severity=severity, message=message)
    db.add(alert)
    db.commit()
    logger.info(f"Alert [{severity}] patient={patient_id}: {message}")
    
    # Simulate sending an email alert
    if severity in ("warning", "critical"):
        logger.info(f"📧 [SIMULATED EMAIL] To: doctors@bcg.clinic | Subject: {severity.upper()} Alert for Patient {patient_id} | Body: {message}")
        
    return alert


def evaluate_and_create_alerts(db: Session, patient_id: int, scan_id: int, scan_data: dict) -> list:
    """
    Evaluate a scan dict and generate any applicable alerts.
    Returns list of Alert ORM objects created.
    """
    alerts_created = []
    hr = scan_data.get("heart_rate")
    signal_quality = (scan_data.get("signal_quality") or "").lower()

    if hr is not None:
        if hr > 100:
            a = _save_alert(db, patient_id, scan_id, "warning", f"High Heart Rate: {hr:.1f} BPM")
            alerts_created.append(a)
        elif hr < 55:
            a = _save_alert(db, patient_id, scan_id, "warning", f"Low Heart Rate: {hr:.1f} BPM")
            alerts_created.append(a)

    if signal_quality in ("poor", ""):
        a = _save_alert(db, patient_id, scan_id, "info", "Poor Signal Quality detected during scan")
        alerts_created.append(a)

    return alerts_created
