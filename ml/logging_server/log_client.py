import aiohttp
import asyncio
from datetime import datetime
from typing import Any, Dict, Optional
import os
import uuid

class LogClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id = str(uuid.uuid4())
        
    async def log_message(self, 
                         message: str,
                         level: str = "INFO",
                         component: str = "default",
                         question_group_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None):
        """Send a log message to the logging server"""
        log_data = {
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "component": component,
            "session_id": self.session_id,
            "question_group_id": question_group_id,
            "metadata": metadata or {}
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(f"{self.base_url}/log", json=log_data) as response:
                    if response.status != 200:
                        print(f"Failed to send log: {await response.text()}")
                    return await response.json()
            except Exception as e:
                print(f"Error sending log: {str(e)}")
                return None

    async def get_logs(self,
                      session_id: Optional[str] = None,
                      question_group_id: Optional[str] = None,
                      component: Optional[str] = None,
                      level: Optional[str] = None,
                      limit: int = 100):
        """Retrieve logs with filters"""
        params = {
            "session_id": session_id or self.session_id,
            "question_group_id": question_group_id,
            "component": component,
            "level": level,
            "limit": limit
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/logs", params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    return []
            except Exception as e:
                print(f"Error retrieving logs: {str(e)}")
                return []

# Helper function for synchronous logging
def log_message_sync(message: str,
                    level: str = "INFO",
                    component: str = "default",
                    question_group_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None):
    """Synchronous wrapper for log_message"""
    client = LogClient()
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        client.log_message(message, level, component, question_group_id, metadata)
    )
