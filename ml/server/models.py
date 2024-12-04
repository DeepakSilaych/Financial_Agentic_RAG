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
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    space = relationship("Space", back_populates="chats")

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
    charts = relationship("Chart", back_populates="message", cascade="all, delete-orphan")
    nodes = relationship("Nodes", back_populates="message", cascade="all, delete-orphan")

class IntermediateQuestion(Base):
    __tablename__ = "intermediate_questions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    question = Column(Text)
    answer = Column(Text, nullable=True)
    question_type = Column(String, default="text") 
    options = Column(Text, nullable=True)  

    message = relationship("Message", back_populates="intermediate_questions")

class Chart(Base):
    __tablename__ = "charts"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    chart_type = Column(String, nullable=False)  # bar/line/pie
    title = Column(String, nullable=False)
    data = Column(Text, nullable=False)  # JSON string of chart data
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("Message", back_populates="charts")

class Nodes(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    parent_node = Column(String, nullable=True)
    current_node = Column(String, nullable=False)
    child_node = Column(String, nullable=True)
    text = Column(String, nullable=False)
    message_id = Column(Integer, ForeignKey("messages.id"))

    message = relationship("Message", back_populates="nodes")

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_size = Column(Integer)
    upload_time = Column(DateTime(timezone=True), server_default=func.now())
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
    physical_path = Column(String, nullable=False)  # Actual file location

    space = relationship("Space", back_populates="files")
    folder = relationship("Folder", back_populates="files")

class Folder(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    space_id = Column(Integer, ForeignKey("spaces.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    space = relationship("Space", back_populates="folders")
    files = relationship("File", back_populates="folder")

class Notes(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Space(Base):
    __tablename__ = "spaces"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    chats = relationship("Chat", back_populates="space", cascade="all, delete-orphan")
    files = relationship("File", back_populates="space", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="space", cascade="all, delete-orphan")
