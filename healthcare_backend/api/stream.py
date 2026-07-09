import asyncio
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()
logger = logging.getLogger("bcg.stream")

async def mjpeg_proxy(request: Request):
    try:
        timeout = httpx.Timeout(connect=2.0, read=None, write=5.0, pool=5.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            # Connect to the bcg_live.py MJPEG server on port 8002
            async with client.stream('GET', 'http://127.0.0.1:8002/cam.mjpg') as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    if await request.is_disconnected():
                        return
                    yield chunk
    except (asyncio.CancelledError, BrokenPipeError, ConnectionResetError):
        return
    except httpx.RequestError as exc:
        logger.warning("MJPEG upstream unavailable: %r", exc)
        return

@router.get("/matplotlib-stream")
async def get_matplotlib_stream(request: Request):
    """
    Proxies the MJPEG stream from the standalone bcg_live.py matplotlib window.
    """
    return StreamingResponse(
        mjpeg_proxy(request), 
        media_type="multipart/x-mixed-replace; boundary=--jpgboundary"
    )
