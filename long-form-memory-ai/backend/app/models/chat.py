from beanie import Document
from datetime import datetime
from typing import Optional, List, Dict, Any


class Conversation(Document):
    user_id: str  # MongoDB uses string IDs
    title: str = "New Conversation"
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    turn_count: int = 0
    
    class Settings:
        name = "conversations"


class Message(Document):
    conversation_id: str
    turn_number: int
    role: str  # 'user' or 'assistant'
    content: str
    created_at: datetime = datetime.utcnow()
    extracted_memories: List[str] = []
    active_memories: List[str] = []
    
    class Settings:
        name = "messages"