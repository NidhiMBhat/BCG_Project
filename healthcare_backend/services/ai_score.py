"""
Deterministic AI Health Score computation.

Heuristic-only — NOT a medical diagnosis.
Scores evolve smoothly and avoid dramatic oscillations.
"""
from typing import Optional

# Smoothing state (module-level, used for live scan smoothing)
_last_score: Optional[float] = None
_last_confidence: Optional[float] = None

SMOOTHING_ALPHA = 0.3  # lower = smoother


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def compute_ai_score(
    heart_rate: Optional[float],
    respiration_rate: Optional[float],
    sdnn: Optional[float],
    rmssd: Optional[float],
    signal_quality: Optional[str],
    motion_detected: bool,
    previous_score: Optional[float] = None,
    previous_confidence: Optional[float] = None,
) -> dict:
    """
    Returns a dict with:
      ai_health_score   : 0-100
      ai_confidence     : 0-100
      risk_level        : 'Low' | 'Medium' | 'High'
    """
    global _last_score, _last_confidence

    # --- Base score from heart rate ---
    hr = heart_rate or 72.0
    if 60 <= hr <= 90:
        hr_score = 100.0
    elif 55 <= hr < 60 or 90 < hr <= 100:
        hr_score = 85.0
    elif 50 <= hr < 55 or 100 < hr <= 110:
        hr_score = 70.0
    else:
        hr_score = 50.0

    # --- Respiration component ---
    rr = respiration_rate or 16.0
    if 12 <= rr <= 18:
        rr_score = 100.0
    elif 10 <= rr < 12 or 18 < rr <= 20:
        rr_score = 80.0
    else:
        rr_score = 60.0

    # --- HRV component ---
    s = sdnn or 45.0
    r = rmssd or 35.0
    hrv_score = _clamp((s / 75.0) * 50.0 + (r / 60.0) * 50.0, 30.0, 100.0)

    # --- Signal quality modifier ---
    sq = (signal_quality or "Good").lower()
    if sq == "excellent":
        sq_mod = 1.0
    elif sq == "good":
        sq_mod = 0.97
    elif sq == "moderate":
        sq_mod = 0.88
    else:
        sq_mod = 0.75

    # --- Motion penalty ---
    motion_pen = 5.0 if motion_detected else 0.0

    # --- Raw score ---
    raw_score = (0.40 * hr_score + 0.25 * rr_score + 0.35 * hrv_score) * sq_mod - motion_pen
    raw_score = _clamp(raw_score, 0.0, 100.0)

    # --- Smooth with previous ---
    ref_prev = previous_score if previous_score is not None else _last_score
    if ref_prev is not None:
        smooth_score = ref_prev + SMOOTHING_ALPHA * (raw_score - ref_prev)
    else:
        smooth_score = raw_score
    smooth_score = _clamp(smooth_score, 0.0, 100.0)

    # --- Confidence ---
    if sq == "excellent" and not motion_detected:
        raw_conf = 94.0 + (smooth_score - 80.0) * 0.1
    elif sq == "good" and not motion_detected:
        raw_conf = 91.0 + (smooth_score - 80.0) * 0.08
    elif sq == "moderate":
        raw_conf = 87.0
    else:
        raw_conf = 78.0
    if motion_detected:
        raw_conf -= 6.0
    raw_conf = _clamp(raw_conf, 60.0, 98.0)

    ref_prev_conf = previous_confidence if previous_confidence is not None else _last_confidence
    if ref_prev_conf is not None:
        smooth_conf = ref_prev_conf + SMOOTHING_ALPHA * (raw_conf - ref_prev_conf)
    else:
        smooth_conf = raw_conf
    smooth_conf = _clamp(smooth_conf, 60.0, 98.0)

    # --- Risk level ---
    if smooth_score >= 80:
        risk = "Low"
    elif smooth_score >= 60:
        risk = "Medium"
    else:
        risk = "High"

    _last_score = smooth_score
    _last_confidence = smooth_conf

    return {
        "ai_health_score": round(smooth_score, 1),
        "ai_confidence": round(smooth_conf, 1),
        "risk_level": risk,
    }


def reset_smoothing():
    """Reset smoothing state when a new monitoring session starts."""
    global _last_score, _last_confidence
    _last_score = None
    _last_confidence = None
