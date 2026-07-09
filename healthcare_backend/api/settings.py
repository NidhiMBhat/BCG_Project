"""Settings / status routes"""
from fastapi import APIRouter, Depends
from healthcare_backend.auth.dependencies import get_current_user
from healthcare_backend.models.user import User
from healthcare_backend.config import APP_VERSION, APP_NAME, TCP_HOST, TCP_PORT, DB_PATH
from healthcare_backend.services.session import session_manager
import os

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", summary="Get application settings and status")
def get_settings(_: User = Depends(get_current_user)):
    db_exists = os.path.exists(DB_PATH)
    session = session_manager.get_status()
    return {
        "app_name": APP_NAME,
        "app_version": APP_VERSION,
        "backend_port": 8001,
        "tcp_host": TCP_HOST,
        "tcp_port": TCP_PORT,
        "database_path": str(DB_PATH),
        "database_exists": db_exists,
        "database_size_mb": round(os.path.getsize(DB_PATH) / 1024 / 1024, 2) if db_exists else 0,
        "monitoring_active": session["active"],
        "active_patient_id": session["patient_id"],
        "packet_count": session["packet_count"],
        "packets_per_second": session["packets_per_second"],
        "sampling_interval_seconds": 10,
    }
