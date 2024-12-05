# process_base.py
import json
import asyncio
import logging
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
import server.models as models

logger = logging.getLogger(__name__)

class BaseMessageProcessor:
    def __init__(self, mode="fast"):
        self.mode = mode

    async def process_message(self, chat_id: int, space_id: int, message_data: dict, websocket, db: Session):
        """Main message processing method to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_message")

    async def validate_message(self, message_data: dict, websocket) -> bool:
        """Validate incoming message data"""
        message_text = message_data.get('content', '').strip()
        if not message_text:
            await websocket.send_json({
                'type': 'error',
                'content': 'Message cannot be empty'
            })
            return False
        return True

    async def save_user_message(self, chat_id: int, message_data: dict, db: Session):
        """Save user message to database"""
        user_message = models.Message(
            chat_id=chat_id,
            content=message_data.get('content', '').strip(),
            is_user=message_data.get('is_user', True),
            mode=message_data.get('mode', self.mode),
            research_mode=message_data.get('research_mode', False)
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        return user_message

    async def update_chat_title(self, chat_id: int, message_text: str, db: Session):
        """Update chat title if this is the first message"""
        try:
            if len(db.query(models.Message).filter(models.Message.chat_id == chat_id).all()) == 1:
                chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
                chat.title = message_text
                db.commit()
                db.refresh(chat)
        except Exception as e:
            logger.error(f"Error updating chat title: {str(e)}")

    async def send_message_received(self, websocket, message_id: int, message_text: str):
        """Send message received acknowledgment"""
        await websocket.send_json({
            'type': 'message_received',
            'message_id': message_id,
            'message': message_text
        })

    async def save_bot_message(self, chat_id: int, content: str, db: Session, mode: str = None, intermediate_questions=None):
        """Save bot message to database"""
        bot_message = models.Message(
            chat_id=chat_id,
            content=content,
            is_user=False,
            mode=mode or self.mode
        )

        if intermediate_questions:
            for q in intermediate_questions:
                intermediate_q = models.IntermediateQuestion(
                    question=q['question'],
                    question_type=q.get('question_type', 'text'),
                    options=json.dumps(q.get('options')) if q.get('options') else None
                )
                bot_message.intermediate_questions.append(intermediate_q)

        db.add(bot_message)
        db.commit()
        db.refresh(bot_message)
        return bot_message

    async def send_bot_response(self, websocket, message_id: int, content: str, response_type='bot_response', **kwargs):
        """Send bot response to client"""
        response = {
            'type': response_type,
            'message_id': message_id,
            'content': content,
            **kwargs
        }
        await websocket.send_json(response)

    async def send_clarification(self, websocket, message_id: int, question: str, options=None):
        """Send clarification question"""
        await websocket.send_json({
            'type': 'clarification',
            'message_id': message_id,
            'content': question,
            'question': question,
            'options': options
        })