from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.core.memory_store import MemoryStore


class MemoryService:
    """Service layer for memory operations."""
    
    def __init__(self):
        self.store = MemoryStore()
    
    async def create_memory(
        self,
        db: Session,
        user_id: int,
        memory_type: str,
        key: str,
        value: str,
        conversation_id: int,
        turn_number: int,
        confidence: float = 0.5,
        importance: float = 0.5,
        context: str = ""
    ) -> Memory:
        """Create a new memory for a user."""
        
        memory_data = {
            "type": memory_type,
            "key": key,
            "value": value,
            "context": context,
            "confidence": confidence,
            "importance": importance
        }
        
        memory = self.store.store_memory(
            db=db,
            user_id=user_id,
            memory_data=memory_data,
            conversation_id=conversation_id,
            turn_number=turn_number
        )
        
        return memory
    
    async def get_user_memories(
        self,
        db: Session,
        user_id: int,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Memory]:
        """Get all memories for a user."""
        
        memories = self.store.get_user_memories(
            db=db,
            user_id=user_id,
            memory_type=memory_type,
            active_only=True
        )
        
        return memories[:limit]
    
    async def search_memories(
        self,
        user_id: int,
        query: str,
        current_turn: int,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search memories using semantic similarity."""
        
        results = self.store.retrieve_relevant_memories(
            user_id=user_id,
            query=query,
            current_turn=current_turn,
            top_k=top_k
        )
        
        return results
    
    async def update_memory(
        self,
        db: Session,
        memory_id: int,
        user_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Memory]:
        """Update an existing memory."""
        
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
        
        if not memory:
            return None
        
        # Update allowed fields
        allowed_fields = ['value', 'context', 'confidence', 'importance_score', 'is_active']
        for field in allowed_fields:
            if field in updates:
                setattr(memory, field, updates[field])
        
        db.commit()
        db.refresh(memory)
        
        return memory
    
    async def delete_memory(
        self,
        db: Session,
        memory_id: int,
        user_id: int
    ) -> bool:
        """Soft delete a memory."""
        
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
        
        if not memory:
            return False
        
        self.store.deactivate_memory(db, memory_id)
        return True
    
    async def get_memory_stats(
        self,
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        
        total_memories = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.is_active == True
        ).count()
        
        type_counts = {}
        for mem_type in ['preference', 'fact', 'entity', 'commitment', 'instruction', 'constraint']:
            count = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.memory_type == mem_type,
                Memory.is_active == True
            ).count()
            if count > 0:
                type_counts[mem_type] = count
        
        high_importance = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.importance_score >= 0.8,
            Memory.is_active == True
        ).count()
        
        return {
            "total_memories": total_memories,
            "by_type": type_counts,
            "high_importance_memories": high_importance
        }
    
    async def refresh_memory_access(
        self,
        db: Session,
        memory_id: int,
        user_id: int,
        current_turn: int
    ) -> bool:
        """Update last accessed time for a memory."""
        
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
        
        if not memory:
            return False
        
        self.store.update_memory_access(db, memory_id, current_turn)
        return True