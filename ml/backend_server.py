from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Depends, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import uvicorn
import os
import json
from datetime import datetime           
import logging
from typing import List, Optional, Dict, Any
import shutil
import asyncio  

from server.database import SessionLocal, engine
from server import models
from server import schemas
from server import process, process2, process3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
  
# Create database tables
models.Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize FastAPI
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:5175", "http://localhost:5175"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers -------------------------------------------------------------------------------------------------

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

# Database dependency --------------------------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# WebSocket Manager -------------------------------------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, chat_id: int):
        await websocket.accept()
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []
        self.active_connections[chat_id].append(websocket)
        logger.info(f"Client connected to chat {chat_id}")

    def disconnect(self, websocket: WebSocket, chat_id: int):
        if chat_id in self.active_connections:
            if websocket in self.active_connections[chat_id]:
                self.active_connections[chat_id].remove(websocket)
                logger.info(f"Client disconnected from chat {chat_id}")
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]

    async def broadcast(self, message: dict, chat_id: int):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")

manager = ConnectionManager()

@app.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int):
    await manager.connect(websocket, chat_id)
    logger.info(f"Client connected to chat {chat_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"Received data: {data}") 
            message_text = data.get("message", "")
            logger.info(f"Extracted message: {message_text}")  
            db = SessionLocal()
            try:
                if data.get("mode") == "fast":
                    await process.process_message(chat_id, message_text, websocket, db)
                elif data.get("mode") == "creative":
                    await process2.process_message(chat_id, message_text, websocket, db)
                else: 
                    await process3.process_message(chat_id, message_text, websocket, db)
            finally:
                db.close()
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket, chat_id)
        logger.info(f"Client disconnected from chat {chat_id}")
    except Exception as e:
        logger.error(f"Error in websocket endpoint: {str(e)}")
        await websocket.close()

# API endpoints---------------------------------------------------------------------------------------

@app.get("/chats/", response_model=List[schemas.ChatResponse])
def get_chats(db: Session = Depends(get_db)):
    try:
        logger.info("Fetching all chats")
        chats = db.query(models.Chat).all()
        logger.info(f"Found {len(chats)} chats")
        
        chat_responses = []
        for chat in chats:
            try:
                chat_response = schemas.ChatResponse(
                    id=chat.id,
                    title=chat.title,
                    created_at=chat.created_at,
                    messages=[
                        schemas.MessageResponse(
                            id=msg.id,
                            content=msg.content,
                            chat_id=msg.chat_id,
                            mode=msg.mode,
                            research_mode=msg.research_mode,
                            is_user=msg.is_user,
                            timestamp=msg.timestamp,
                            intermediate_questions=[
                                schemas.IntermediateQuestionResponse(
                                    id=q.id,
                                    message_id=q.message_id,
                                    question=q.question,
                                    answer=q.answer,
                                    question_type=q.question_type,
                                    options=json.loads(q.options) if q.options else []
                                )
                                for q in msg.intermediate_questions
                            ]
                        )
                        for msg in chat.messages
                    ]
                )
                chat_responses.append(chat_response)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding options JSON for chat {chat.id}: {e}")
                # Skip the problematic chat but continue with others
                continue
            except Exception as e:
                logger.error(f"Error processing chat {chat.id}: {e}")
                continue
                
        return chat_responses
    except Exception as e:
        logger.error(f"Unexpected error in get_chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/{chat_id}/history", response_model=List[schemas.MessageResponse])
async def get_chat_history(chat_id: int, db: Session = Depends(get_db)):
    try:
        logger.info(f"Fetching chat history for chat {chat_id}")
        
        # Check if chat exists, create if not
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            logger.info(f"Chat {chat_id} not found, creating new chat")
            chat = models.Chat(id=chat_id, title="New Chat")
            db.add(chat)
            try:
                db.commit()
                db.refresh(chat)
            except SQLAlchemyError as e:
                logger.error(f"Error creating chat: {e}")
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")
        
        # Get messages
        messages = db.query(models.Message).filter(
            models.Message.chat_id == chat_id
        ).order_by(models.Message.timestamp.asc()).all()
        
        logger.info(f"Found {len(messages)} messages in chat {chat_id}")
        return [schemas.MessageResponse.model_validate(msg) for msg in messages]
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_chat_history: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_chat_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chats/{chat_id}", response_model=schemas.ChatResponse)
def get_chat(chat_id: int, db: Session = Depends(get_db)):
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        return schemas.ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            messages=[
                schemas.MessageResponse(
                    id=msg.id,
                    content=msg.content,
                    chat_id=msg.chat_id,
                    mode=msg.mode,
                    research_mode=msg.research_mode,
                    is_user=msg.is_user,
                    timestamp=msg.timestamp,
                    intermediate_questions=[
                        schemas.IntermediateQuestionResponse(
                            id=q.id,
                            message_id=q.message_id,
                            question=q.question,
                            answer=q.answer,
                            question_type=q.question_type,
                            options=json.loads(q.options) if q.options else []
                        )
                        for q in msg.intermediate_questions
                    ]
                )
                for msg in chat.messages
            ]
        )
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding options JSON for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat data")
    except Exception as e:
        logger.error(f"Error retrieving chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chats/", response_model=schemas.ChatResponse)
def create_chat(chat: schemas.ChatCreate = Body(default=None), db: Session = Depends(get_db)):
    try:
        logger.info("Creating new chat")
        if chat is None:
            chat = schemas.ChatCreate(title="New Chat")
        db_chat = models.Chat(**chat.model_dump())
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        logger.info(f"Created chat {db_chat.id}")
        return schemas.ChatResponse.model_validate(db_chat)
    except SQLAlchemyError as e:
        logger.error(f"Database error in create_chat: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in create_chat: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/files/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Generate safe filename to prevent path traversal
        filename = os.path.basename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            counter = 1
            name, ext = os.path.splitext(filename)
            while os.path.exists(file_path):
                filename = f"{name}_{counter}{ext}"
                file_path = os.path.join(UPLOAD_DIR, filename)
                counter += 1
        
        # Save the file using chunks to handle large files
        with open(file_path, "wb") as f:
            CHUNK_SIZE = 1024 * 1024  # 1MB chunks
            while chunk := await file.read(CHUNK_SIZE):
                f.write(chunk)
        
        # Get file info
        stats = os.stat(file_path)
        file_ext = os.path.splitext(filename)[1][1:].lower()
        
        return {
            "name": filename,
            "size": stats.st_size,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "lastModified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
            "owner": "Current User",
            "tag": file_ext,
            "url": f"/files/{filename}"
        }
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/")
async def list_files():
    try:
        files = []
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                stats = os.stat(file_path)
                file_ext = os.path.splitext(filename)[1][1:].lower()
                files.append({
                    "name": filename,
                    "size": stats.st_size,
                    "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                    "lastModified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    "owner": "Current User",
                    "tag": file_ext,
                    "url": f"/files/{filename}"
                })
        return sorted(files, key=lambda x: x["lastModified"], reverse=True)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def download_file(filename: str):
    try:
        # Prevent path traversal
        filename = os.path.basename(filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get file extension and set appropriate content type
        file_ext = os.path.splitext(filename)[1][1:].lower()
        content_type = None
        
        if file_ext == 'pdf':
            content_type = 'application/pdf'
        elif file_ext in ['jpg', 'jpeg']:
            content_type = 'image/jpeg'
        elif file_ext == 'png':
            content_type = 'image/png'
        elif file_ext == 'gif':
            content_type = 'image/gif'
        
        # Return file with proper content type
        return FileResponse(
            file_path,
            filename=filename,
            media_type=content_type,
            headers={
                "Cache-Control": "no-cache",
                "Content-Disposition": f"inline; filename={filename}"
            }
        )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    try:
        # Prevent path traversal
        filename = os.path.basename(filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        os.remove(file_path)
        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("backend_server:app", host="0.0.0.0", port=8000, reload=False)