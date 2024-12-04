from pydantic import BaseModel, ConfigDict
from typing import List, Optional, ForwardRef
from datetime import datetime
import json

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
    options: Optional[str] = None

class IntermediateQuestionCreate(IntermediateQuestionBase):
    message_id: int

class IntermediateQuestionResponse(IntermediateQuestionBase):
    id: int
    message_id: int
    answer: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ChartDataBase(BaseModel):
    chart_type: str  # bar/line/pie
    title: str
    data: str  # Store as JSON string
    description: Optional[str] = None

    def get_data_dict(self) -> dict:
        """Convert data string to dictionary"""
        if isinstance(self.data, str):
            return json.loads(self.data)
        return self.data

class ChartResponse(ChartDataBase):
    id: int
    message_id: int
    
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    timestamp: datetime
    intermediate_questions: List["IntermediateQuestionResponse"] = []
    charts: List[ChartResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class ChatBase(BaseModel):
    title: Optional[str] = "New Chat"
    space_id: int

class ChatCreate(ChatBase):
    pass

class ChatUpdate(BaseModel):
    title: str

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

class SpaceBase(BaseModel):
    name: str
    description: Optional[str] = None

class SpaceCreate(SpaceBase):
    pass

class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class FileBase(BaseModel):
    filename: str
    file_size: int
    space_id: int
    folder_id: Optional[int] = None

class FileCreate(FileBase):
    physical_path: str

class FileResponse(FileBase):
    id: int
    upload_time: datetime
    
    model_config = ConfigDict(from_attributes=True)

class FolderBase(BaseModel):
    name: str
    space_id: int

class FolderCreate(FolderBase):
    pass

class FolderResponse(FolderBase):
    id: int
    files: List[FileResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class SpaceResponse(SpaceBase):
    id: int
    files: List[FileResponse] = []
    folders: List[FolderResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

class NotesBase(BaseModel):
    filename: str
    text: str

class NotesCreate(NotesBase):
    pass

class NotesUpdate(BaseModel):
    filename: Optional[str] = None
    text: Optional[str] = None

class NotesResponse(NotesBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# This is how we handle forward references in Pydantic v2
MessageResponse.model_rebuild()