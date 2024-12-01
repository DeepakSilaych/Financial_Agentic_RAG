from fastapi import FastAPI, WebSocket
from typing import List, Dict, Any
from datetime import datetime
import json
import asyncio
from collections import deque
import uvicorn

app = FastAPI()

# In-memory storage using deque with max size
MAX_LOGS = 1000
logs = deque(maxlen=MAX_LOGS)
active_connections: List[WebSocket] = []

async def notify_clients(log_entry: Dict[str, Any]):
    """Send log entry to all connected clients"""
    if active_connections:
        message = json.dumps(log_entry, default=str)
        await asyncio.gather(
            *[connection.send_text(message) for connection in active_connections]
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # Send existing logs to new connection
        for log in logs:
            await websocket.send_text(json.dumps(log, default=str))
        
        # Keep connection alive and handle disconnection
        while True:
            await websocket.receive_text()
    except:
        active_connections.remove(websocket)

@app.post("/log")
async def create_log(log_data: Dict[str, Any]):
    """Create a new log entry and broadcast to all clients"""
    log_entry = {
        "timestamp": datetime.utcnow(),
        "message": log_data.get("message", ""),
        "level": log_data.get("level", "INFO"),
        "component": log_data.get("component", "default"),
        "metadata": log_data.get("metadata", {})
    }
    logs.append(log_entry)
    await notify_clients(log_entry)
    return {"status": "success"}

@app.get("/logs")
def get_logs():
    """Get all logs in memory"""
    return list(logs)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
