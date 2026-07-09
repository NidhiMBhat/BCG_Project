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
    return alert


def evaluate_and_create_alerts(db: Session, patient_id: int, scan_id: int, scan_data: dict) -> list:
    """
    Evaluate a scan dict and generate any applicable alerts.
    Returns list of Alert ORM objects created.
    """
    alerts_created = []
    hr = scan_data.get("heart_rate")
    rr = scan_data.get("respiration_rate")
    sdnn = scan_data.get("sdnn")
    signal_quality = (scan_data.get("signal_quality") or "").lower()
    motion = scan_data.get("motion_detected", False)

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

    if motion:
        a = _save_alert(db, patient_id, scan_id, "info", "Motion artifact detected during scan — results may be less accurate")
        alerts_created.append(a)

    if sdnn is not None and sdnn < 20:
        a = _save_alert(db, patient_id, scan_id, "warning", f"Low HRV (SDNN): {sdnn:.1f} ms — may indicate autonomic stress")
        alerts_created.append(a)

    if rr is not None and (rr < 10 or rr > 22):
        a = _save_alert(db, patient_id, scan_id, "warning", f"Abnormal Respiration Rate: {rr:.1f} breaths/min")
        alerts_created.append(a)

    return alerts_created
