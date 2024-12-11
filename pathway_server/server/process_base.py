import json
import asyncio
import logging
from sqlalchemy.orm import Session
from fastapi import WebSocketDisconnect
import server.models as models

logger = logging.getLogger(__name__)


class BaseMessageProcessor:
    def __init__(self, mode):
        self.mode = mode

    async def check_chat_exists(self, chat_id: int, space_id: int, db: Session):
        try:
            chat = (
                db.query(models.Chat)
                .filter(models.Chat.id == chat_id, models.Chat.space_id == space_id)
                .first()
            )
            if not chat:
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking chat existence: {str(e)}")
            return False
        return True

    async def validate_message(self, message_data: dict, websocket) -> bool:
        """Validate incoming message data"""
        message_text = message_data.get("content", "").strip()
        if not message_text:
            await websocket.send_json(
                {"type": "error", "content": "Message cannot be empty"}
            )
            return False
        return True

    async def save_user_message(
        self, chat_id: int, message_text: str, websocket, db: Session
    ):
        """Save user message to database and handle initial setup"""
        logger.info(f"Saving user message for chat {chat_id}")
        if not message_text or not message_text.strip():
            await websocket.send_json(
                {"type": "error", "content": "Message cannot be empty"}
            )
            return None

        user_message = models.Message(
            chat_id=chat_id, content=message_text.strip(), is_user=True, mode=self.mode
        )

        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        logger.info(f"User message saved with id: {user_message.id}")

        await websocket.send_json(
            {
                "type": "message_received",
                "message_id": user_message.id,
                "message": message_text,
            }
        )

        try:
            if (
                len(
                    db.query(models.Message)
                    .filter(models.Message.chat_id == chat_id)
                    .all()
                )
                == 1
            ):
                chat = db.query(models.Chat).filter(models.Chat.id == chat_id).first()
                chat.title = message_text
                db.commit()
                db.refresh(chat)
                logger.info(f"Updated chat {chat_id} title to: {message_text}")
        except Exception as e:
            logger.error(f"Error updating chat title: {str(e)}")
        return user_message

    async def handle_intermediate_message(
        self, chat_id: int, question: dict, websocket, db: Session
    ):
        """Handle intermediate/clarification messages and responses"""
        logger.info(f"Handling intermediate message for chat {chat_id}")

        intermediate_message = models.Message(
            chat_id=chat_id, content=question["question"], is_user=False, mode=self.mode
        )
        db.add(intermediate_message)
        db.commit()
        db.refresh(intermediate_message)
        logger.info(f"Intermediate message saved with id: {intermediate_message.id}")

        await websocket.send_json(
            {
                "type": "clarification",
                "message_id": intermediate_message.id,
                "question": question["question"],
                "options": question.get("options", []),
            }
        )

        try:
            while True:
                response = await websocket.receive_json()
                if response["type"] == "clarification_response":
                    intermediate_message.answer = response["answer"]
                    db.commit()
                    db.refresh(intermediate_message)
                    logger.info(
                        f"Received clarification response: {response['answer']}"
                    )
                    return response["answer"]
        except WebSocketDisconnect:
            logger.warning(
                "WebSocket disconnected while waiting for clarification response"
            )

        return

    async def handle_response(
        self,
        chat_id: int,
        response_content: str,
        websocket,
        db: Session,
        charts=None,
        kpiAnalysis=None,
    ):
        """Save and send the final response"""
        import json

        logger.info(f"Handling response for chat {chat_id}")

        response_message = models.Message(
            chat_id=chat_id, content=response_content, is_user=False, mode=self.mode
        )
        db.add(response_message)
        db.commit()
        db.refresh(response_message)

        # Add charts if provided
        if charts:
            for chart_data in charts:
                chart = models.Chart(
                    message_id=response_message.id,
                    chart_type=chart_data["chart_type"],
                    title=chart_data.get("title", "Untitled Chart"),
                    data=json.dumps(chart_data["data"]),  # Convert dict to JSON string
                    description=None,  # Optional field
                )
                db.add(chart)
            db.commit()

        if kpiAnalysis:
            kpiAnalysisObj = models.KPIAnalysis(
                message_id=response_message.id,
                data=kpiAnalysis,
            )
            db.add(kpiAnalysisObj)
            db.commit()

        logger.info(f"Response message saved with id: {response_message.id}")

        await websocket.send_json(
            {
                "type": "response",
                "message_id": response_message.id,
                "content": response_content,
                "charts": charts if charts else [],
                "kpi_analysis": [{"data": kpiAnalysis}],
            }
        )

        return response_message
