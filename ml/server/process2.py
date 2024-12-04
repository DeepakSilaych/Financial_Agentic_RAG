from dotenv import load_dotenv
import os
load_dotenv()

import json
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
import server.models as models
from workflows.rag_e2e import rag_e2e as app
import asyncio


async def process_message(chat_id: int, space_id: int, message_text: str, websocket, db: Session):
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


        try:
            if len(db.query(models.Message).filter(models.Message.chat_id == chat_id).all()) == 1:
                chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
                chat.title = message_text
                db.commit()
                db.refresh(chat)
        except Exception as e:
            print(e)
            


        await websocket.send_json({
            'type': 'message_received',
            'message_id': user_message.id,
            'message': message_text
        })



        await asyncio.sleep(.1)

        input_json = {
            "question": message_text,
            "chat_id": chat_id,
            "message_id": user_message.id,
            "space_id": space_id
        }

        res = app.invoke(input_json)
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
            'type': 'bot_response',
            'message_id': bot_response.id,
            'content': response_content
        })
        
    except Exception as e:
        print(e)
        await websocket.send_json({
            'type': 'error',
            'content': f"Error processing message: {str(e)}"
        })