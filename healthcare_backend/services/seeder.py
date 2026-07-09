"""
Database seeder: populate 5 demo patients with physiologically realistic scans.
Runs once on first launch if patients table is empty.
"""
import random
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from healthcare_backend.models.patient import Patient
from healthcare_backend.models.scan import Scan
from healthcare_backend.models.user import User
from healthcare_backend.models.alert import Alert
from healthcare_backend.auth.password import hash_password
from healthcare_backend.services.ai_score import compute_ai_score
import logging

logger = logging.getLogger("bcg.seeder")

DEMO_PATIENTS = [
    {"patient_code": "BCG-001", "name": "user1", "age": 20, "gender": "Male",   "height": 175.0, "weight": 72.0, "blood_group": "B+"},
    {"patient_code": "BCG-002", "name": "user2", "age": 20, "gender": "Female", "height": 162.0, "weight": 58.0, "blood_group": "O+"},
    {"patient_code": "BCG-003", "name": "user3", "age": 20, "gender": "Male",   "height": 170.0, "weight": 85.0, "blood_group": "A+"},
    {"patient_code": "BCG-004", "name": "user4", "age": 45, "gender": "Female", "height": 158.0, "weight": 63.0, "blood_group": "AB-"},
    {"patient_code": "BCG-005", "name": "user5", "age": 50, "gender": "Male",   "height": 182.0, "weight": 78.0, "blood_group": "O-"},
    {"patient_code": "BCG-006", "name": "user6", "age": 50, "gender": "Female", "height": 165.0, "weight": 65.0, "blood_group": "B-"},
]

DEMO_USERS = [
    {"username": "admin",   "password": "admin123",   "role": "admin"},
    {"username": "doctor1", "password": "doctor123",  "role": "doctor"},
    {"username": "doctor2", "password": "doctor456",  "role": "doctor"},
]

SIGNAL_QUALITIES = ["Excellent", "Excellent", "Good", "Good", "Good", "Moderate"]


def _rng_seed(patient_idx: int) -> random.Random:
    """Per-patient seeded RNG for reproducible demo data."""
    return random.Random(42 + patient_idx * 17)


def _gen_scan(rng: random.Random, patient_id: int, ts: datetime, prev_score=None) -> Scan:
    """Generate one realistic scan for a patient."""
    # Determine scenario type: resting vs mild activity
    scenario = rng.choices(["resting", "mild", "post_exercise"], weights=[0.55, 0.30, 0.15])[0]

    if scenario == "resting":
        hr = rng.uniform(58, 72)
    elif scenario == "mild":
        hr = rng.uniform(70, 88)
    else:  # post_exercise
        hr = rng.uniform(84, 96)

    # Add slight physiological noise
    hr += rng.gauss(0, 1.5)

    hr = max(55, min(100, hr))

    signal_quality = rng.choice(SIGNAL_QUALITIES)

    ai = compute_ai_score(hr, signal_quality, prev_score)

    notes_pool = [
        None, None, None,
        "Baseline recording.",
        "Patient appeared relaxed.",
        "Post-meal session.",
        "Patient reported mild fatigue.",
        "Calibration run.",
        "Good cooperation from patient.",
        "Slight movement noted.",
    ]
    notes = rng.choice(notes_pool)
    if scenario == "post_exercise":
        notes = "Post exercise — elevated HR expected."

    return Scan(
        patient_id=patient_id,
        timestamp=ts,
        heart_rate=round(hr, 1),
        signal_quality=signal_quality,
        ai_health_score=ai["ai_health_score"],
        notes=notes,
    )


def _spread_timestamps(rng: random.Random, n: int) -> list:
    """Return n datetimes spread across the last 7 days, ordered chronologically."""
    now = datetime.utcnow()
    delta_seconds = 7 * 24 * 3600
    offsets = sorted([rng.uniform(0, delta_seconds) for _ in range(n)])
    return [now - timedelta(seconds=delta_seconds - o) for o in offsets]


def seed_database(db: Session):
    """Seed demo users, patients, and scans if the DB is empty."""
    if db.query(User).count() > 0:
        logger.info("Database already seeded — skipping.")
        return

    logger.info("Seeding demo data into database...")

    # Create users
    for u in DEMO_USERS:
        user = User(username=u["username"], password_hash=hash_password(u["password"]), role=u["role"])
        db.add(user)
    db.commit()

    # Create patients + scans
    for idx, pd_data in enumerate(DEMO_PATIENTS):
        patient = Patient(**pd_data)
        db.add(patient)
        db.flush()  # get patient.id

        rng = _rng_seed(idx)
        n_scans = rng.randint(8, 15)
        timestamps = _spread_timestamps(rng, n_scans)

        prev_score = None
        for ts in timestamps:
            scan = _gen_scan(rng, patient.id, ts, prev_score)
            db.add(scan)
            db.flush()
            prev_score = scan.ai_health_score

            # Occasionally generate an alert
            if scan.heart_rate and scan.heart_rate > 92:
                alert = Alert(
                    patient_id=patient.id,
                    scan_id=scan.id,
                    severity="warning",
                    message=f"High Heart Rate: {scan.heart_rate:.1f} BPM during session.",
                )
                db.add(alert)

    db.commit()
    logger.info(f"Seeded {len(DEMO_PATIENTS)} demo patients with scans and {len(DEMO_USERS)} users.")
    logger.info("Default credentials: admin/admin123, doctor1/doctor123, doctor2/doctor456")
