from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from server.database import Base
from datetime import datetime

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    mode = Column(String, default="fast")
    research_mode = Column(Boolean, default=False)
    is_user = Column(Boolean, default=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    chat = relationship("Chat", back_populates="messages")
    intermediate_questions = relationship("IntermediateQuestion", back_populates="message", cascade="all, delete-orphan")

class IntermediateQuestion(Base):
    __tablename__ = "intermediate_questions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    question = Column(Text)
    answer = Column(Text, nullable=True)
    question_type = Column(String, default="text") 
    options = Column(Text, nullable=True)  

    message = relationship("Message", back_populates="intermediate_questions")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    file_size = Column(Integer)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=True)

    chat = relationship("Chat")