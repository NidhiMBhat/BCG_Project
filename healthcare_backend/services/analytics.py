"""
Analytics service: compute aggregates, trends, daily/weekly stats,
and generate human-readable summaries + trend badges.
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from healthcare_backend.models.scan import Scan


def get_scans_for_patient(db: Session, patient_id: int, days: int = 7) -> List[Scan]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(Scan)
        .filter(Scan.patient_id == patient_id, Scan.timestamp >= cutoff)
        .order_by(Scan.timestamp.asc())
        .all()
    )


def _avg(values: list) -> Optional[float]:
    v = [x for x in values if x is not None]
    return round(sum(v) / len(v), 2) if v else None


def _trend_badge(values: list, metric: str) -> dict:
    """
    Returns {label, arrow, direction} based on first-half vs second-half average.
    direction: 'up' | 'down' | 'stable'
    """
    v = [x for x in values if x is not None]
    if len(v) < 4:
        return {"label": "Stable", "arrow": "→", "direction": "stable"}

    mid = len(v) // 2
    first_avg = sum(v[:mid]) / mid
    second_avg = sum(v[mid:]) / (len(v) - mid)
    pct_change = (second_avg - first_avg) / (first_avg + 1e-6) * 100.0

    threshold = 3.0  # percent

    # For HR: up = elevated, down = improving (lower)
    # For HRV: up = improving, down = reduced
    # For RR: up = elevated, down = improving
    if metric in ("hr", "rr"):
        if pct_change > threshold:
            return {"label": "Elevated", "arrow": "↑", "direction": "up"}
        elif pct_change < -threshold:
            return {"label": "Improving", "arrow": "↓", "direction": "down"}
        else:
            return {"label": "Stable", "arrow": "→", "direction": "stable"}
    else:  # HRV metrics
        if pct_change > threshold:
            return {"label": "Improving", "arrow": "↑", "direction": "up"}
        elif pct_change < -threshold:
            return {"label": "Reduced", "arrow": "↓", "direction": "down"}
        else:
            return {"label": "Stable", "arrow": "→", "direction": "stable"}


def _daily_averages(scans: List[Scan], attr: str) -> List[dict]:
    """Group scans by calendar day and compute average of `attr`."""
    by_day: dict = {}
    for s in scans:
        day_key = s.timestamp.date().isoformat()
        val = getattr(s, attr, None)
        if val is not None:
            by_day.setdefault(day_key, []).append(val)
    return [
        {"date": d, "value": round(sum(v) / len(v), 2)}
        for d, v in sorted(by_day.items())
    ]


def _weekly_average(scans: List[Scan], attr: str) -> Optional[float]:
    return _avg([getattr(s, attr, None) for s in scans])


def _human_summary(metric: str, badge: dict, avg: Optional[float]) -> str:
    label = badge["label"].lower()
    if metric == "hr":
        if label == "stable":
            return "Heart rate remained stable during the past week."
        elif label == "improving":
            return "Heart rate showed improvement — trending toward a healthier range."
        else:
            return "Heart rate appeared elevated. Consider reviewing activity levels."
    elif metric == "rr":
        if label == "stable":
            return "Respiration remained within a healthy range throughout the week."
        elif label == "improving":
            return "Respiration rate improved compared to earlier sessions."
        else:
            return "Respiration rate showed some elevation — worth monitoring."
    elif metric == "hrv":
        if label == "stable":
            return "HRV remained consistent across all recorded sessions."
        elif label == "improving":
            return "HRV improved compared to previous sessions — a positive sign."
        else:
            return "HRV showed a declining trend. Rest and stress management may help."
    return ""


def compute_analytics(db: Session, patient_id: int) -> dict:
    scans = get_scans_for_patient(db, patient_id, days=7)
    all_scans = db.query(Scan).filter(Scan.patient_id == patient_id).order_by(Scan.timestamp.asc()).all()

    if not scans:
        return {
            "patient_id": patient_id,
            "scan_count": 0,
            "summary": "No scan data available for this patient in the past 7 days.",
            "averages": {},
            "trends": {},
            "daily_hr": [],
            "daily_rr": [],
            "daily_sdnn": [],
            "weekly_hr": None,
            "weekly_rr": None,
            "weekly_sdnn": None,
            "highest_hr": None,
            "lowest_hr": None,
            "hr_summary": "",
            "rr_summary": "",
            "hrv_summary": "",
        }

    hrs = [s.heart_rate for s in scans]
    rrs = [s.respiration_rate for s in scans]
    sdnns = [s.sdnn for s in scans]
    rmssds = [s.rmssd for s in scans]

    hr_badge = _trend_badge(hrs, "hr")
    rr_badge = _trend_badge(rrs, "rr")
    hrv_badge = _trend_badge(sdnns, "hrv")

    avg_hr = _avg(hrs)
    avg_rr = _avg(rrs)
    avg_sdnn = _avg(sdnns)
    avg_rmssd = _avg(rmssds)

    valid_hrs = [h for h in hrs if h is not None]

    return {
        "patient_id": patient_id,
        "scan_count": len(scans),
        "total_scan_count": len(all_scans),
        "averages": {
            "heart_rate": avg_hr,
            "respiration_rate": avg_rr,
            "sdnn": avg_sdnn,
            "rmssd": avg_rmssd,
        },
        "highest_hr": round(max(valid_hrs), 1) if valid_hrs else None,
        "lowest_hr": round(min(valid_hrs), 1) if valid_hrs else None,
        "trends": {
            "hr": hr_badge,
            "rr": rr_badge,
            "hrv": hrv_badge,
        },
        "daily_hr": _daily_averages(scans, "heart_rate"),
        "daily_rr": _daily_averages(scans, "respiration_rate"),
        "daily_sdnn": _daily_averages(scans, "sdnn"),
        "weekly_hr": _weekly_average(scans, "heart_rate"),
        "weekly_rr": _weekly_average(scans, "respiration_rate"),
        "weekly_sdnn": _weekly_average(scans, "sdnn"),
        "hr_summary": _human_summary("hr", hr_badge, avg_hr),
        "rr_summary": _human_summary("rr", rr_badge, avg_rr),
        "hrv_summary": _human_summary("hrv", hrv_badge, avg_sdnn),
        "summary": (
            f"Analysed {len(scans)} scans over the past 7 days. "
            f"Average HR: {avg_hr} BPM. "
            f"Average RR: {avg_rr} br/min. "
            f"Average SDNN: {avg_sdnn} ms."
        ),
    }
