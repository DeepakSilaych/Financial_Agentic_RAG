from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import uvicorn
import logging
import asyncio

from server.database import engine
from server import models
from server.routes import chat_router, file_router, ws_router, space_router, auth_router

from fastapi.websockets import WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5175",
        "http://localhost:5175",
        "https://finsight.deepaksilaych.me",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": f"Validation error: {str(exc)}"},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Database error: {str(exc)}"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"General error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


graph_clients = set()


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
                status_code=400,
            )

        # Validate required fields
        required_fields = ["parent_node", "current_node", "text"]
        if not all(field in node_data for field in required_fields):
            return JSONResponse(
                content={"error": f"Missing required fields: {required_fields}"},
                status_code=400,
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
                "node": node_data["current_node"],
            },
            status_code=200,
        )
    except Exception as e:
        logger.error(f"Error in receive_nodes: {str(e)}")
        return JSONResponse(
            content={"error": f"Internal server error: {str(e)}"}, status_code=500
        )


@app.websocket("/ws/graph")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    graph_clients.add(websocket)
    logger.info(f"New graph client connected. Total clients: {len(graph_clients)}")

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        graph_clients.remove(websocket)
        logger.info(
            f"Graph client disconnected. Remaining clients: {len(graph_clients)}"
        )
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        graph_clients.remove(websocket)


# Include routers
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(file_router)
app.include_router(ws_router)
app.include_router(space_router)

if __name__ == "__main__":
    uvicorn.run("backend_server:app", host="0.0.0.0", port=8000)
