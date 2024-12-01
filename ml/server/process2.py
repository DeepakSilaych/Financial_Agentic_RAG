from dotenv import load_dotenv
import os
load_dotenv()

import json
import logging
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
import server.models as models
from workflows.rag_e2e import rag_e2e as app
import asyncio

logger = logging.getLogger(__name__)

async def process_message(chat_id: int, message_text: str, websocket, db: Session):
    try:
        if not message_text or not message_text.strip():
            await websocket.send_json({
                'type': 'error',
                'content': 'Message cannot be empty'
            })
            return
        user_message = models.Message(
            chat_id=chat_id,
            content=message_text,
            is_user=True,
            mode="chat"
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)

        await websocket.send_json({
            'type': 'message_received',
            'message_id': user_message.id,
            'message': message_text
        })

        await asyncio.sleep(.1)

        res = app.invoke({"question": message_text})
        response_content = res["answer"]
            
        bot_response = models.Message(
            chat_id=chat_id,
            content=response_content,
            is_user=False,
            mode="chat"
        )
        db.add(bot_response)
        db.commit()
        db.refresh(bot_response)
        
        await websocket.send_json({
            'type': 'response',
            'message_id': bot_response.id,
            'content': response_content
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        await websocket.send_json({
            'type': 'error',
            'content': f"Error processing message: {str(e)}"
        })