"""
Deterministic AI Health Score computation.

Heuristic-only — NOT a medical diagnosis.
Scores evolve smoothly and avoid dramatic oscillations.
"""
from typing import Optional

# Smoothing state (module-level, used for live scan smoothing)
_last_score: Optional[float] = None

SMOOTHING_ALPHA = 0.2  # lower = smoother


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def compute_ai_score(
    heart_rate: Optional[float],
    signal_quality: Optional[str],
    previous_score: Optional[float] = None,
) -> dict:
    """
    Returns a dict with:
      ai_health_score   : 0-100
    """
    global _last_score

    # --- Base score from heart rate ---
    hr = heart_rate or 72.0
    if 60 <= hr <= 90:
        hr_score = 96.0
    elif 55 <= hr < 60 or 90 < hr <= 100:
        hr_score = 88.0
    elif 50 <= hr < 55 or 100 < hr <= 110:
        hr_score = 75.0
    else:
        hr_score = 60.0

    # --- Signal quality modifier ---
    sq = (signal_quality or "Good").lower()
    if sq == "excellent":
        sq_mod = 1.0
    elif sq == "good":
        sq_mod = 0.98
    elif sq == "moderate":
        sq_mod = 0.90
    else:
        sq_mod = 0.70

    # --- Raw score ---
    raw_score = hr_score * sq_mod
    raw_score = _clamp(raw_score, 0.0, 100.0)

    # --- Smooth with previous ---
    ref_prev = previous_score if previous_score is not None else _last_score
    if ref_prev is not None:
        smooth_score = ref_prev + SMOOTHING_ALPHA * (raw_score - ref_prev)
    else:
        smooth_score = raw_score
    smooth_score = _clamp(smooth_score, 0.0, 100.0)

    _last_score = smooth_score

    return {
        "ai_health_score": round(smooth_score, 1),
    }


def reset_smoothing():
    """Reset smoothing state when a new monitoring session starts."""
    global _last_score
    _last_score = None

