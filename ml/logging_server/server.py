from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
from datetime import datetime, timezone
import json
import asyncio
from collections import deque, defaultdict
import uvicorn
import os
from pathlib import Path

app = FastAPI()

# Get the current directory
current_dir = Path(__file__).parent
static_dir = current_dir / "static"

# Mount static files
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# In-memory storage using defaultdict and deque
MAX_LOGS_PER_GROUP = 1000
logs_by_group = defaultdict(lambda: deque(maxlen=MAX_LOGS_PER_GROUP))
active_connections: List[WebSocket] = []

def get_group_key(log_data: Dict[str, Any]) -> str:
    """Generate a group key based on metadata"""
    # Try to get question_id first
    question_id = log_data.get("question_id")
    if question_id:
        return f"question_{question_id}"
    
    # Try track next
    track = log_data.get("track")
    if track:
        return f"track_{track}"
    
    # Try component
    component = log_data.get("component")
    if component and component != "default":
        return f"component_{component}"
    
    # Fallback to system
    return "system_general"

def format_group_title(group_key: str) -> str:
    """Format the group key into a readable title"""
    category, identifier = group_key.split('_', 1)
    if category == "question":
        return f"Question {identifier}"
    elif category == "track":
        return f"Track: {identifier}"
    elif category == "component":
        return f"Component: {identifier}"
    else:
        return "System Logs"

async def broadcast_log(log_entry: Dict[str, Any], group_key: str):
    """Send log entry to all connected clients"""
    if active_connections:
        message = json.dumps({
            "log": log_entry,
            "group_key": group_key,
            "group_title": format_group_title(group_key)
        }, default=str)
        failed_connections = []
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Failed to send to client: {str(e)}")
                failed_connections.append(connection)
        
        # Remove failed connections
        for failed in failed_connections:
            if failed in active_connections:
                active_connections.remove(failed)

@app.get("/", response_class=HTMLResponse)
async def get_home():
    """Serve the HTML interface"""
    html_file = static_dir / "index.html"
    return html_file.read_text()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    print(f"New client connected. Total connections: {len(active_connections)}")
    try:
        # Send existing logs to new connection
        for group_key, group_logs in logs_by_group.items():
            for log in group_logs:
                try:
                    await websocket.send_text(json.dumps({
                        "log": log,
                        "group_key": group_key,
                        "group_title": format_group_title(group_key)
                    }, default=str))
                except Exception as e:
                    print(f"Error sending existing log: {str(e)}")
                    break
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                await websocket.receive_text()
            except Exception as e:
                print(f"WebSocket error: {str(e)}")
                break
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
            print(f"Client disconnected. Remaining connections: {len(active_connections)}")

@app.post("/log")
async def create_log(log_data: Dict[str, Any]):
    """Create a new log entry and broadcast to all clients"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": log_data.get("message", ""),
        "level": log_data.get("level", "INFO"),
        "component": log_data.get("component", "default"),
        "question_id": log_data.get("question_id"),
        "track": log_data.get("track"),
        "metadata": {
            k: v for k, v in log_data.items() 
            if k not in ["message", "level", "component", "question_id", "track"]
        }
    }
    
    group_key = get_group_key(log_data)
    logs_by_group[group_key].append(log_entry)
    await broadcast_log(log_entry, group_key)
    return {"status": "success", "group": group_key}

@app.get("/logs")
def get_logs():
    """Get all logs grouped by category"""
    return {
        group_key: {
            "title": format_group_title(group_key),
            "logs": list(logs)
        }
        for group_key, logs in logs_by_group.items()
    }

if __name__ == "__main__":
    print("Starting logging server...")
    print("View logs at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
