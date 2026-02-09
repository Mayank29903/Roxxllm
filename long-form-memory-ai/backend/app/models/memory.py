from beanie import Document
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class Memory(Document):
    user_id: str
    memory_type: str  # 'preference', 'fact', 'entity', 'commitment', 'instruction'
    key: str
    value: str
    context: str = ""
    source_conversation_id: Optional[str] = None
    source_turn: int
    confidence: float = 0.0
    importance_score: float = 0.5
    is_active: bool = True
    access_count: int = 0
    last_accessed_turn: int = 0
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    vector_id: str = ""
    
    class Settings:
        name = "memories"