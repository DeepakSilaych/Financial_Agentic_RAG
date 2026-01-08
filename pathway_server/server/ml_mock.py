import asyncio
import logging
from sqlalchemy.orm import Session
from .process_base import BaseMessageProcessor

logger = logging.getLogger(__name__)


class MockMessageProcessor(BaseMessageProcessor):
    def __init__(self, mode):
        super().__init__(mode)

    async def run(
        self, chat_id: int, space_id: int, message_text: str, websocket, db: Session
    ):
        user_message = await self.save_user_message(
            chat_id, message_text, websocket, db
        )
        await asyncio.sleep(0.5)

        await self.handle_response(
            chat_id=chat_id,
            response_content="**API Key Expired**\n\nThe LLM and RAG services are currently unavailable. Please configure valid API keys to enable AI-powered document analysis.\n\nIn the meantime, you can:\n- Upload and manage documents\n- Create and organize spaces\n- Browse your file library",
            websocket=websocket,
            db=db,
            charts=[],
            kpiAnalysis=None,
        )
