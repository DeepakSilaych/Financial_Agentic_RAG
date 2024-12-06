from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, File, UploadFile, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import os
from fastapi import HTTPException

from . import schemas
from .database import get_db, SessionLocal
from .websocket import manager
from . import chat_handler, file_handler
from . import process, process4
from . import models

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create routers
space_router = APIRouter(prefix="/spaces", tags=["space"])
chat_router = APIRouter(prefix="/spaces/{space_id}/chats", tags=["chat"])
file_router = APIRouter(prefix="/spaces", tags=["files"])
ws_router = APIRouter(tags=["websocket"])

# Space routes
@space_router.get("/", response_model=List[schemas.SpaceResponse])
def get_spaces(db: Session = Depends(get_db)):
    spaces = db.query(models.Space).all()
    return spaces

@space_router.post("/", response_model=schemas.SpaceResponse)
def create_space(space: schemas.SpaceCreate, db: Session = Depends(get_db)):
    db_space = models.Space(**space.model_dump())
    db.add(db_space)
    db.commit()
    db.refresh(db_space)
    return db_space

@space_router.get("/{space_id}", response_model=schemas.SpaceResponse)
def get_space(space_id: int, db: Session = Depends(get_db)):
    space = db.query(models.Space).filter(models.Space.id == space_id).first()
    if space is None:
        raise HTTPException(status_code=404, detail="Space not found")
    return space

@space_router.patch("/{space_id}", response_model=schemas.SpaceResponse)
def update_space(space_id: int, space: schemas.SpaceUpdate, db: Session = Depends(get_db)):
    db_space = db.query(models.Space).filter(models .Space.id == space_id).first()
    if db_space is None:
        raise HTTPException(status_code=404, detail="Space not found")
    
    update_data = space.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_space, field, value)
    
    db.commit()
    db.refresh(db_space)
    return db_space

@space_router.delete("/{space_id}")
def delete_space(space_id: int, db: Session = Depends(get_db)):
    db_space = db.query(models.Space).filter(models.Space.id == space_id).first()
    if db_space is None:
        raise HTTPException(status_code=404, detail="Space not found")
    
    db.delete(db_space)
    db.commit()
    return {"message": "Space deleted successfully"}

# WebSocket routes
@ws_router.websocket("/ws/{space_id}/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, space_id: int, chat_id: int):
    db = SessionLocal()
    try:
        # Verify space and chat exist
        chat = db.query(models.Chat).filter(
            models.Chat.id == chat_id,
            models.Chat.space_id == space_id
        ).first()
        
        if not chat:
            await websocket.close(code=4004, reason="Chat not found")
            return
            
        await manager.connect(websocket, chat_id)
        logger.info(f"Client connected to chat {chat_id} in space {space_id}")
        
        try:
            while True:
                data = await websocket.receive_json()
                logger.info(f"Received data: {data}") 
                message_text = data.get("message", "")
                logger.info(f"Extracted message: {message_text}")  
                
                try:
                    if data.get("mode") == "yalalalafda":
                        await process.process_message(chat_id, space_id, message_text, websocket, db)
                    else:   
                        processor = process4.MessageProcessor(data.get("mode"))
                        await processor.run(chat_id=chat_id, space_id=space_id, message_text=message_text, websocket=websocket, db=db)

                except Exception as e:  
                    logger.error(f"Error processing message: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Failed to process message"
                    })
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket, chat_id)
            logger.info(f"Client disconnected from chat {chat_id}")
        except Exception as e:
            logger.error(f"Error in websocket endpoint: {str(e)}")
            manager.disconnect(websocket, chat_id)
    finally:
        db.close()

# Chat routes
@chat_router.get("/", response_model=List[schemas.ChatResponse])
def get_chats(space_id: int, db: Session = Depends(get_db)):
    # Verify space exists
    space = db.query(models.Space).filter(models.Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    return db.query(models.Chat).filter(models.Chat.space_id == space_id).all()

@chat_router.get("/{chat_id}", response_model=schemas.ChatResponse)
def get_chat(space_id: int, chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(
        models.Chat.id == chat_id,
        models.Chat.space_id == space_id
    ).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@chat_router.get("/{chat_id}/history", response_model=List[schemas.MessageResponse])
def get_chat_history(space_id: int, chat_id: int, db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages

@chat_router.post("/", response_model=schemas.ChatResponse)
def create_chat(space_id: int, chat: schemas.ChatCreate, db: Session = Depends(get_db)):
    # Verify space exists
    space = db.query(models.Space).filter(models.Space.id == space_id).first()
    if not space:
        raise HTTPException(status_code=404, detail="Space not found")
    
    db_chat = models.Chat(**chat.model_dump())
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    return db_chat

@chat_router.patch("/{chat_id}")
def update_chat(space_id: int, chat_id: int, chat: schemas.ChatUpdate, db: Session = Depends(get_db)):
    db_chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
    if db_chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    update_data = chat.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_chat, field, value)
    
    db.commit()
    db.refresh(db_chat)
    return db_chat

# File routes
@file_router.get("/{space_id}/files/{path:path}")
async def list_files(space_id: int, path: str):
    """List files and folders in the specified path"""
    try:
        items = file_handler.list_items(space_id, path)
        return items
    except Exception as e:
        logger.error(f"Error listing items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_router.post("/{space_id}/files/{path:path}")
async def create_folder(
    space_id: int,
    path: str,
    name: str = Body(..., embed=True)
):
    """Create a new folder at the specified path"""
    try:
        folder_info = file_handler.create_folder(space_id, path, name)
        return folder_info
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_router.delete("/{space_id}/files/{path:path}")
async def delete_item(
    space_id: int,
    path: str,
    name: str = Body(...)
):
    """Delete a file or folder at the specified path"""
    try:
        success = file_handler.delete_item(space_id, path, name)
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=500, detail="Failed to delete item")
    except Exception as e:
        logger.error(f"Error deleting item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_router.post("/{space_id}/files/{path:path}/upload")
async def upload_file(
    space_id: int,
    path: str,
    file: UploadFile = File(..., description="File to upload")
):
    """Upload a file to the specified path"""
    try:
        # Normalize the path
        normalized_path = path.rstrip('/')
        if normalized_path == "":
            normalized_path = "/"
            
        file_info = await file_handler.save_upload_file(file, space_id, normalized_path)
        return file_info
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_router.get("/{space_id}/files/{filename}")
async def serve_file(space_id: int, filename: str):
    """Serve a file directly"""
    try:
        space_dir = file_handler.get_space_dir(space_id)
        file_path = os.path.join(space_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(file_path)
    except Exception as e:
        logger.error(f"Error serving file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@file_router.get("/{space_id}/file/download")
async def download_file(space_id: int, path: str):
    """Download a file with attachment disposition"""
    try:
        space_dir = file_handler.get_space_dir(space_id)
        file_path = os.path.join(space_dir, path)
        file_name = os.path.basename(file_path)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        return FileResponse(
            file_path,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))