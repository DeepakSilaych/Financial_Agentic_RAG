from pydantic import BaseModel, ConfigDict
from typing import List, Optional, ForwardRef
from datetime import datetime

class MessageBase(BaseModel):
    content: str
    mode: Optional[str] = "fast"  # fast/creative/precise
    research_mode: Optional[bool] = False
    is_user: Optional[bool] = True

class MessageCreate(MessageBase):
    chat_id: int

class IntermediateQuestionBase(BaseModel):
    question: str
    question_type: str  # text/single/multi
    options: Optional[List[str]] = None

class IntermediateQuestionCreate(IntermediateQuestionBase):
    message_id: int

class IntermediateQuestionResponse(IntermediateQuestionBase):
    id: int
    message_id: int
    answer: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime
    intermediate_questions: List["IntermediateQuestionResponse"] = []
    
    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    title: Optional[str] = "New Chat"

class ChatCreate(ChatBase):
    pass

class ChatResponse(ChatBase):
    id: int
    created_at: datetime
    messages: List[MessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class FileUploadResponse(BaseModel):
    filename: str
    file_size: int
    upload_time: datetime

class FileListResponse(BaseModel):
    files: List[FileUploadResponse]

# This is how we handle forward references in Pydantic v2
MessageResponse.model_rebuild()