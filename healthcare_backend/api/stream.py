from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

async def mjpeg_proxy():
    try:
        async with httpx.AsyncClient() as client:
            # Connect to the bcg_live.py MJPEG server on port 8002
            async with client.stream('GET', 'http://127.0.0.1:8002/cam.mjpg') as response:
                async for chunk in response.aiter_bytes():
                    yield chunk
    except httpx.RequestError as exc:
        # Yield a broken image or gracefully stop if backend is not running
        print(f"Error proxying MJPEG: {exc}")
        return

@router.get("/matplotlib-stream")
async def get_matplotlib_stream():
    """
    Proxies the MJPEG stream from the standalone bcg_live.py matplotlib window.
    """
    return StreamingResponse(
        mjpeg_proxy(), 
        media_type="multipart/x-mixed-replace; boundary=--jpgboundary"
    )
