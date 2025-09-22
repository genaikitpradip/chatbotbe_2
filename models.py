

# from pydantic import BaseModel, Field
# from typing import Optional, List, Any
# from datetime import datetime
# from enum import Enum

# class Reference(BaseModel):
#     title: str
#     url: str
#     snippet: str

# class MessageRole(str, Enum):
#     USER = "user"
#     ASSISTANT = "assistant"
#     SYSTEM = "system"  # ✅ ADD THIS LINE

# class FileInfo(BaseModel):
#     filename: str
#     type: str
#     url: str
#     size: int

# class Message(BaseModel):
#     chat_id: str
#     role: MessageRole
#     content: str
#     references: Optional[List[Reference]] = None  # ✅ Make optional
#     file: Optional[FileInfo] = None
#     timestamp: datetime = Field(default_factory=datetime.utcnow)
#     owner_id: Optional[str] = None   # <-- NEW

# class Chat(BaseModel):
#     id: str = Field(default_factory=lambda: "", alias="_id")
#     title: str
#     created_at: datetime = Field(default_factory=datetime.utcnow)
#     updated_at: datetime = Field(default_factory=datetime.utcnow)
#     message_count: int = 0
#     owner_id: Optional[str] = None   # <-- NEW

#     class Config:
#         populate_by_name = True

# class ChatCreate(BaseModel):
#     title: Optional[str] = "New Chat"

# class ChatRename(BaseModel):
#     title: str

# class MessageCreate(BaseModel):
#     content: str
#     original_content: Optional[str] = None
#     web_search_results: Optional[str] = None  # ✅ NEW

# class ChatResponse(BaseModel):
#     chat_id: str
#     message: Message
#     response: Message

# class ChatListResponse(BaseModel):
#     chats: List[Chat]

# class ChatHistoryResponse(BaseModel):
#     chat: Chat
#     messages: List[Message]

# class MessageRequest(BaseModel):
#     question: str


# class SearchQuery(BaseModel):
#     query: str

# class TTSRequest(BaseModel):
#     text: str
#     voice: str = "nova"
#     model: str = "tts-hd"
    


from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ---------- Auth / User ----------

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    name: Optional[str] = None

class UserLogin(UserBase):
    password: str

class UserPublic(UserBase):
    id: str = Field(alias="_id")
    name: Optional[str] = None
    created_at: datetime

    class Config:
        populate_by_name = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---------- Web search references ----------

class Reference(BaseModel):
    title: str
    url: str
    snippet: str

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class FileInfo(BaseModel):
    filename: str
    type: str
    url: str
    size: int

class Message(BaseModel):
    chat_id: str
    role: MessageRole
    content: str
    references: Optional[List[Reference]] = None
    file: Optional[FileInfo] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    owner_id: str  # REQUIRED now

class Chat(BaseModel):
    id: str = Field(default_factory=lambda: "", alias="_id")
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    owner_id: str  # REQUIRED now

    class Config:
        populate_by_name = True

class ChatCreate(BaseModel):
    title: Optional[str] = "New Chat"

class ChatRename(BaseModel):
    title: str

class MessageCreate(BaseModel):
    content: str
    original_content: Optional[str] = None
    web_search_results: Optional[str] = None

class ChatResponse(BaseModel):
    chat_id: str
    message: Message
    response: Message

class ChatListResponse(BaseModel):
    chats: List[Chat]

class ChatHistoryResponse(BaseModel):
    chat: Chat
    messages: List[Message]

class MessageRequest(BaseModel):
    question: str

class SearchQuery(BaseModel):
    query: str

# class TTSRequest(BaseModel):
    # text: str
    # voice: str = "nova"
    # model: str = "tts-hd"

# Pydantic model for TTS request
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    voice_id: str = Field(default="JBFqnCBsd6RMkjVDRZzb")  # your default
    model_id: str = Field(default="eleven_multilingual_v2")
    output_format: str = Field(default="mp3_44100_128")   # keep mp3 defaults
