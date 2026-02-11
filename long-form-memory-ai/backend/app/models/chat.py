from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, List


class Conversation(Document):
    user_id: str
    title: str = "New Conversation"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    turn_count: int = 0

    class Settings:
        name = "conversations"


class Message(Document):
    conversation_id: str
    turn_number: int
    role: str  # 'user' or 'assistant'
    content: str

    created_at: datetime = Field(default_factory=datetime.utcnow)

    extracted_memories: List[str] = Field(default_factory=list)
    active_memories: List[str] = Field(default_factory=list)

    class Settings:
        name = "messages"
