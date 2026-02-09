from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.memory import Memory


class MemoryService:
    """Service layer for memory operations (Beanie-based)."""

    async def create_memory(
        self,
        user_id: str,
        memory_type: str,
        key: str,
        value: str,
        conversation_id: Optional[str],
        turn_number: int,
        confidence: float = 0.5,
        importance: float = 0.5,
        context: str = ""
    ) -> Memory:
        """Create a new memory for a user."""

        memory = Memory(
            user_id=user_id,
            memory_type=memory_type,
            key=key,
            value=value,
            context=context,
            source_conversation_id=conversation_id,
            source_turn=turn_number,
            confidence=confidence,
            importance_score=importance,
            is_active=True,
            created_at=datetime.utcnow()
        )

        await memory.insert()
        return memory

    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Memory]:
        """Get all active memories for a user."""

        query = Memory.find(
            Memory.user_id == user_id,
            Memory.is_active == True
        )

        if memory_type:
            query = query.find(Memory.memory_type == memory_type)

        memories = await query.limit(limit).to_list()
        return memories

    async def search_memories(
        self,
        user_id: str,
        query_text: str,
        top_k: int = 5
    ) -> List[Memory]:
        """
        Placeholder for semantic search.
        This should later be wired to your vector store (FAISS / Chroma).
        """

        memories = await Memory.find(
            Memory.user_id == user_id,
            Memory.is_active == True
        ).limit(top_k).to_list()

        return memories

    async def update_memory(
        self,
        memory_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Memory]:
        """Update an existing memory."""

        memory = await Memory.get(memory_id)
        if not memory or memory.user_id != user_id:
            return None

        allowed_fields = {
            "value",
            "context",
            "confidence",
            "importance_score",
            "is_active",
            "expires_at"
        }

        for field, value in updates.items():
            if field in allowed_fields:
                setattr(memory, field, value)

        memory.updated_at = datetime.utcnow()
        await memory.save()

        return memory

    async def delete_memory(
        self,
        memory_id: str,
        user_id: str
    ) -> bool:
        """Soft delete a memory (mark inactive)."""

        memory = await Memory.get(memory_id)
        if not memory or memory.user_id != user_id:
            return False

        memory.is_active = False
        memory.updated_at = datetime.utcnow()
        await memory.save()

        return True

    async def get_memory_stats(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get memory statistics for a user."""

        memories = await Memory.find(
            Memory.user_id == user_id,
            Memory.is_active == True
        ).to_list()

        stats = {
            "total_memories": len(memories),
            "by_type": {},
            "high_importance_memories": 0
        }

        for mem in memories:
            stats["by_type"].setdefault(mem.memory_type, 0)
            stats["by_type"][mem.memory_type] += 1

            if mem.importance_score >= 0.8:
                stats["high_importance_memories"] += 1

        return stats

    async def refresh_memory_access(
        self,
        memory_id: str,
        user_id: str,
        current_turn: int
    ) -> bool:
        """Update last accessed metadata for a memory."""

        memory = await Memory.get(memory_id)
        if not memory or memory.user_id != user_id:
            return False

        memory.access_count += 1
        memory.last_accessed_turn = current_turn
        memory.updated_at = datetime.utcnow()
        await memory.save()

        return True
