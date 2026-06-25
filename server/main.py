import asyncio
import json
import logging
from typing import List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from server.db import init_db, save_telemetry_batch, save_prediction
from server.processor import BCGProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BCGServer")

app = FastAPI(title="BCG Live Cloud Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Active connections
device_sockets: Set[WebSocket] = set()
client_sockets: Set[WebSocket] = set()

# In-memory processor & write queue
processor = BCGProcessor()
telemetry_write_queue = asyncio.Queue()

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing database...")
    init_db()
    asyncio.create_task(db_writer_worker())
    asyncio.create_task(broadcast_worker())

async def db_writer_worker():
    """Reads telemetry from queue and saves in batches to DB."""
    logger.info("Database writer worker started.")
    batch = []
    while True:
        try:
            try:
                item = await asyncio.wait_for(telemetry_write_queue.get(), timeout=1.0)
                batch.append(item)
                telemetry_write_queue.task_done()
            except asyncio.TimeoutError:
                pass

            if batch and (len(batch) >= 100 or telemetry_write_queue.empty()):
                try:
                    save_telemetry_batch(batch)
                    batch = []
                except Exception as e:
                    logger.error(f"Error saving batch to DB: {e}")
                    batch = []
        except Exception as e:
            logger.error(f"Error in DB writer worker loop: {e}")
            await asyncio.sleep(1.0)

async def broadcast_worker():
    """Periodically processes the rolling window and broadcasts the metrics to client dashboards."""
    logger.info("Broadcaster worker started.")
    while True:
        try:
            await asyncio.sleep(0.1)  # 10 Hz refresh
            
            processed_data = processor.process()
            if processed_data:
                processed_data["type"] = "processed"
                msg = json.dumps(processed_data)
                
                client_tasks = [
                    client.send_text(msg)
                    for client in client_sockets
                ]
                if client_tasks:
                    await asyncio.gather(*client_tasks, return_exceptions=True)
                    
        except Exception as e:
            logger.error(f"Error in broadcast worker loop: {e}")
            await asyncio.sleep(1.0)

@app.websocket("/ws/device")
async def websocket_device(websocket: WebSocket):
    await websocket.accept()
    device_sockets.add(websocket)
    logger.info(f"Edge device connected. Total: {len(device_sockets)}")
    try:
        while True:
            data_str = await websocket.receive_text()
            data = json.loads(data_str)
            
            t_ms = data.get("time_ms")
            ax = data.get("ax", 0.0)
            ay = data.get("ay", 0.0)
            az = data.get("az", 0.0)
            occupancy = data.get("occupancy", 1)
            temp = data.get("temp")
            humidity = data.get("humidity")
            
            if t_ms is not None:
                # Add to processor
                processor.add_sample(t_ms, ax, ay, az, occupancy, temp, humidity)
                
                # Queue for database persistence
                telemetry_write_queue.put_nowait((
                    t_ms, ax, ay, az, occupancy, temp, humidity
                ))
                
                # Broadcast raw point immediately to all client dashboards (e.g. bcg_live.py)
                raw_payload = {
                    "type": "raw",
                    "time_ms": t_ms,
                    "ax": ax,
                    "ay": ay,
                    "az": az,
                    "occupancy": occupancy,
                    "temp": temp,
                    "humidity": humidity
                }
                raw_msg = json.dumps(raw_payload)
                
                client_tasks = [
                    client.send_text(raw_msg)
                    for client in client_sockets
                ]
                if client_tasks:
                    await asyncio.gather(*client_tasks, return_exceptions=True)

    except WebSocketDisconnect:
        logger.info("Edge device disconnected.")
    except Exception as e:
        logger.error(f"Device socket error: {e}")
    finally:
        device_sockets.discard(websocket)

@app.websocket("/ws/client")
async def websocket_client(websocket: WebSocket):
    await websocket.accept()
    client_sockets.add(websocket)
    logger.info(f"Dashboard client connected. Total: {len(client_sockets)}")
    try:
        while True:
            command = await websocket.receive_text()
            logger.info(f"Command received from client: {command}")
            
            relay_tasks = [
                device.send_text(json.dumps({"command": command}))
                for device in device_sockets
            ]
            if relay_tasks:
                await asyncio.gather(*relay_tasks, return_exceptions=True)
                
    except WebSocketDisconnect:
        logger.info("Dashboard client disconnected.")
    except Exception as e:
        logger.error(f"Client socket error: {e}")
    finally:
        client_sockets.discard(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
