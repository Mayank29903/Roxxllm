
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.memory import Memory


class MemoryService:
    """Service layer for memory operations with conflict resolution."""

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
        """
        Create a new memory for a user.
        AUTOMATICALLY DEACTIVATES old memories with the same key to handle preference updates.
        """
        
        print(f"\n🔍 Checking for existing memory: {memory_type}/{key}")
        
        # Find and deactivate any existing memory with the same key and type
        existing_memories = await Memory.find(
            Memory.user_id == user_id,
            Memory.memory_type == memory_type,
            Memory.key == key,
            Memory.is_active == True
        ).to_list()
        
        if existing_memories:
            print(f"🔄 Found {len(existing_memories)} existing memory(ies) for key '{key}'")
            for old_mem in existing_memories:
                print(f"   Deactivating: {old_mem.value} (Turn {old_mem.source_turn})")
                old_mem.is_active = False
                old_mem.updated_at = datetime.utcnow()
                await old_mem.save()
            print(f"✅ Deactivated old memories")
        
        # Create new memory
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
        
        print(f"✅ Created new memory: [{memory_type}] {key} = {value} (Turn {turn_number})")
        
        return memory

    async def get_user_memories(
        self,
        user_id: str,
        memory_type: Optional[str] = None,
        limit: int = 100,
        sort_by: str = "recency"  # "recency" or "importance"
    ) -> List[Memory]:
        """
        Get all active memories for a user, sorted by RECENCY (newest first) by default.
        This ensures LATEST preferences are retrieved first.
        """

        query = Memory.find(
            Memory.user_id == user_id,
            Memory.is_active == True
        )

        if memory_type:
            query = query.find(Memory.memory_type == memory_type)

        # Sort by recency (source_turn descending) or importance
        if sort_by == "recency":
            memories = await query.sort("-source_turn").limit(limit).to_list()
        else:
            memories = await query.sort("-importance_score").limit(limit).to_list()
            
        return memories

    async def search_memories(
        self,
        user_id: str,
        query_text: str,
        current_turn: int = 0,
        top_k: int = 5,
        memory_types: Optional[List[str]] = None
    ) -> List[Memory]:
        """
        Simple keyword-based search for memories with recency prioritization.
        Returns MongoDB Memory objects sorted by recency.
        """
        
        query = Memory.find(
            Memory.user_id == user_id,
            Memory.is_active == True
        )
        
        if memory_types:
            query = query.find({"memory_type": {"$in": memory_types}})
        
        # Get all active memories and sort by recency
        memories = await query.sort("-source_turn").limit(top_k * 2).to_list()
        
        # Simple relevance scoring based on keyword matching
        scored_memories = []
        query_lower = query_text.lower()
        
        for mem in memories:
            score = 0.0
            
            # Check if query keywords appear in memory value or key
            mem_text = f"{mem.key} {mem.value}".lower()
            query_words = query_lower.split()
            
            for word in query_words:
                if len(word) > 2 and word in mem_text:
                    score += 1.0
            
            # Add recency boost (more recent = higher score)
            if current_turn > 0:
                turns_ago = current_turn - mem.source_turn
                recency_boost = max(0, 5 - (turns_ago / 10))  # Decay over time
                score += recency_boost
            
            # Add importance boost
            score += mem.importance_score * 2
            
            scored_memories.append((score, mem))
        
        # Sort by score and return top_k
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [mem for score, mem in scored_memories[:top_k]]
    
    async def refresh_memory_access(
        self,
        memory_id: str,
        user_id: str,
        current_turn: int
    ) -> bool:
        """Update memory access statistics."""
        
        memory = await Memory.get(memory_id)
        if not memory or memory.user_id != user_id:
            return False
        
        memory.access_count += 1
        memory.last_accessed_turn = current_turn
        memory.updated_at = datetime.utcnow()
        await memory.save()
        
        return True

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
    
    async def delete_conversation_memories(
        self,
        conversation_id: str,
        user_id: str
    ) -> int:
        """
        Delete (deactivate) ALL memories associated with a specific conversation.
        Returns the count of memories deleted.
        """
        
        memories = await Memory.find(
            Memory.user_id == user_id,
            Memory.source_conversation_id == conversation_id,
            Memory.is_active == True
        ).to_list()
        
        count = 0
        for mem in memories:
            mem.is_active = False
            mem.updated_at = datetime.utcnow()
            await mem.save()
            count += 1
            print(f"   Deactivated memory: [{mem.memory_type}] {mem.key}: {mem.value}")
        
        return count

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