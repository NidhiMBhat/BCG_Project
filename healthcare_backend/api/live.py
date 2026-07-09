"""
Live SSE (Server-Sent Events) endpoint for real-time scan streaming.
The bridge pushes data via /scan; this streams the latest state to the frontend.
"""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from healthcare_backend.database import get_db
from healthcare_backend.models.scan import Scan
from healthcare_backend.services.session import session_manager

router = APIRouter(tags=["Live"])
logger = logging.getLogger("bcg.live")


@router.get("/live", summary="SSE stream of live monitoring state")
async def live_stream():
    """
    Server-Sent Events endpoint. Frontend connects here to receive
    real-time updates about the current monitoring session and latest scan.
    """
    async def event_generator():
        from healthcare_backend.database import SessionLocal
        while True:
            try:
                db = SessionLocal()
                status = session_manager.get_status()
                latest_scan = None

                if status["patient_id"]:
                    scan = (
                        db.query(Scan)
                        .filter(Scan.patient_id == status["patient_id"])
                        .order_by(Scan.timestamp.desc())
                        .first()
                    )
                    if scan:
                        latest_scan = {
                            "id": scan.id,
                            "patient_id": scan.patient_id,
                            "timestamp": scan.timestamp.isoformat(),
                            "heart_rate": scan.heart_rate,
                            "lowest_heart_rate": scan.lowest_heart_rate,
                            "highest_heart_rate": scan.highest_heart_rate,
                            "signal_quality": scan.signal_quality,
                            "ai_health_score": scan.ai_health_score,
                        }
                db.close()

                payload = json.dumps({"session": status, "latest_scan": latest_scan})
                yield f"data: {payload}\n\n"
            except Exception as e:
                logger.error(f"SSE error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            finally:
                try:
                    db.close()
                except Exception:
                    pass

            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/live/status", summary="Get current live session status (JSON)")
def live_status():
    return session_manager.get_status()
