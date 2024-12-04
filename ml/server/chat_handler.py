from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import List, Dict, Any
from datetime import datetime
import json

from . import models, schemas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_chats(db: Session) -> List[Dict[str, Any]]:
    try:
        logger.info("Fetching all chats")
        chats = db.query(models.Chat).all()
        logger.info(f"Found {len(chats)} chats")
        
        chat_responses = []
        for chat in chats:
            try:
                chat_response = {
                    "id": chat.id,
                    "title": chat.title,
                    "created_at": chat.created_at,
                    "messages": [
                        {
                            "id": msg.id,
                            "content": msg.content,
                            "chat_id": msg.chat_id,
                            "mode": msg.mode,
                            "research_mode": msg.research_mode,
                            "is_user": msg.is_user,
                            "timestamp": msg.timestamp,
                            "intermediate_questions": [
                                {
                                    "id": q.id,
                                    "message_id": q.message_id,
                                    "question": q.question,
                                    "answer": q.answer,
                                    "question_type": q.question_type,
                                    "options": json.loads(q.options) if q.options else []
                                }
                                for q in msg.intermediate_questions
                            ]
                        }
                        for msg in chat.messages
                    ]
                }
                chat_responses.append(chat_response)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding options JSON for chat {chat.id}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing chat {chat.id}: {e}")
                continue
                
        return chat_responses
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_all_chats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_chat_by_id(chat_id: int, db: Session) -> Dict[str, Any]:
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        return {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "messages": [
                {
                    "id": msg.id,
                    "content": msg.content,
                    "chat_id": msg.chat_id,
                    "mode": msg.mode,
                    "research_mode": msg.research_mode,
                    "is_user": msg.is_user,
                    "timestamp": msg.timestamp,
                    "intermediate_questions": [
                        {
                            "id": q.id,
                            "message_id": q.message_id,
                            "question": q.question,
                            "answer": q.answer,
                            "question_type": q.question_type,
                            "options": json.loads(q.options) if q.options else []
                        }
                        for q in msg.intermediate_questions
                    ],
                    "charts": [
                        {
                            "id": c.id,
                            "message_id": c.message_id,
                            "chart_type": c.chart_type,
                            "title": c.title,
                            "data": json.loads(c.data) if isinstance(c.data, str) else c.data,
                            "description": c.description
                        }
                        for c in msg.charts
                    ] if msg.charts else []
                }
                for msg in chat.messages
            ]
        }
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON data for chat {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat data")
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_chat_by_id: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_chat_history(chat_id: int, db: Session) -> List[Dict[str, Any]]:
    try:
        chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
            
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "chat_id": msg.chat_id,
                "mode": msg.mode,
                "research_mode": msg.research_mode,
                "is_user": msg.is_user,
                "timestamp": msg.timestamp,
                "intermediate_questions": [
                    {
                        "id": q.id,
                        "message_id": q.message_id,
                        "question": q.question,
                        "answer": q.answer,
                        "question_type": q.question_type,
                        "options": json.loads(q.options) if q.options else []
                    }
                    for q in msg.intermediate_questions
                ],
                "charts": [
                    {
                        "id": c.id,
                        "message_id": c.message_id,
                        "chart_type": c.chart_type,
                        "title": c.title,
                        "data": json.loads(c.data) if isinstance(c.data, str) else c.data,
                        "description": c.description
                    }
                    for c in msg.charts
                ] if msg.charts else []
            }
            for msg in chat.messages
        ]
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON data in chat history {chat_id}: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat history")
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_chat_history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def create_new_chat(chat: schemas.ChatCreate, db: Session) -> Dict[str, Any]:
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

def update_chat(db: Session, chat_id: int, chat: schemas.ChatUpdate):
    try:
        db_chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
        if not db_chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        db_chat.title = chat.title
        db.commit()
        db.refresh(db_chat)
        return db_chat
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logger.error(f"Error updating chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
