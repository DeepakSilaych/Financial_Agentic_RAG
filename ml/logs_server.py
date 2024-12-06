import asyncio
import json
from queue import Queue
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configuration
LOGS_HOST = "0.0.0.0"
LOGS_PORT = 6969

graph_clients = set()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/receive_nodes/")
async def receive_nodes(node_data: dict):
    """
    Endpoint to receive single node data, save it to a file, and broadcast to connected WebSocket clients.
    Expected format: 
    {
        "parent_node": "parent1$$parent2",
        "current_node": "node_id",
        "text": "Node description"
    }
    """
    try:
        # Validate input structure
        if not isinstance(node_data, dict):
            return JSONResponse(
                content={"error": "Invalid data format. Expected dictionary"}, 
                status_code=400
            )
            
        # Validate required fields
        required_fields = ['parent_node', 'current_node', 'text', 'text_state'] 
        if not all(field in node_data for field in required_fields):
            return JSONResponse(
                content={"error": f"Missing required fields: {required_fields}"}, 
                status_code=400
            )

        # Save node data to file
        with open("received_nodes.txt", "a") as f:
            f.write(f"{node_data}\n")
        
        # Broadcast to all connected clients
        if graph_clients:
            await asyncio.gather(
                *[client.send_json(node_data) for client in graph_clients]
            )

        return JSONResponse(
            content={
                "message": "Node data saved and sent to clients",
                "clients": len(graph_clients),
                "node": node_data["current_node"]
            },
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
                content={"error": f"Internal server error: {str(e)}"}, 
                status_code=500
        )

@app.websocket("/ws/graph")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    graph_clients.add(websocket)
    print(f"New graph client connected. Total clients: {len(graph_clients)}")
    
    try:
        while True:
            await websocket.receive_text() 
    except WebSocketDisconnect:
        graph_clients.remove(websocket)
        print(f"Graph client disconnected. Remaining clients: {len(graph_clients)}")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        graph_clients.remove(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host=LOGS_HOST, port=LOGS_PORT, log_level="info")