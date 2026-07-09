"""
BCG Healthcare Backend Configuration
"""
import os
from pathlib import Path

# Project root
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DB_PATH = BASE_DIR / "healthcare.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "bcg-healthcare-jwt-secret-key-2024-change-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours

# App
APP_VERSION = "1.0.0"
APP_NAME = "BCG Healthcare Platform"
BACKEND_PORT = 8001

# Bridge / TCP
TCP_HOST = "192.168.137.150"
TCP_PORT = 5000
LIVE_CSV_PATH = BASE_DIR / "live_bcg_output.csv"

# Scan generation window (seconds of BCG data to aggregate into one scan)
SCAN_WINDOW_SECONDS = 10
