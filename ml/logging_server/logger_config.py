from datetime import datetime
import json
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import os
from motor.motor_asyncio import AsyncIOMotorClient

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "pathway_logs"

class LogEntry(BaseModel):
    level: str
    message: str
    timestamp: Optional[datetime] = None
    component: str
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    question_group_id: Optional[str] = None

class LoggingConfig:
    def __init__(self):
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.db = self.mongo_client[DB_NAME]
        self.logs_collection = self.db["logs"]
        
    async def setup_indexes(self):
        """Create indexes for efficient querying"""
        await self.logs_collection.create_index([
            ("timestamp", -1),
            ("session_id", 1),
            ("question_group_id", 1)
        ])
        await self.logs_collection.create_index([("component", 1)])
        await self.logs_collection.create_index([("level", 1)])

    async def log_entry(self, entry: LogEntry):
        """Log an entry to MongoDB"""
        log_data = entry.dict()
        if not log_data.get("timestamp"):
            log_data["timestamp"] = datetime.utcnow()
        
        try:
            await self.logs_collection.insert_one(log_data)
            logger.info(f"Logged entry: {json.dumps(log_data, default=str)}")
        except Exception as e:
            logger.error(f"Failed to log entry: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to log entry")

    async def get_logs(self, 
                      session_id: Optional[str] = None,
                      question_group_id: Optional[str] = None,
                      component: Optional[str] = None,
                      level: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      limit: int = 100):
        """Retrieve logs with various filters"""
        query = {}
        if session_id:
            query["session_id"] = session_id
        if question_group_id:
            query["question_group_id"] = question_group_id
        if component:
            query["component"] = component
        if level:
            query["level"] = level
        if start_time or end_time:
            query["timestamp"] = {}
            if start_time:
                query["timestamp"]["$gte"] = start_time
            if end_time:
                query["timestamp"]["$lte"] = end_time

        cursor = self.logs_collection.find(query)
        cursor.sort("timestamp", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        try:
            result = await self.logs_collection.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )
            logger.info(f"Cleaned up {result.deleted_count} old log entries")
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {str(e)}")
