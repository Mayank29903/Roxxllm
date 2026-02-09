from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.core.memory_store import MemoryStore


class MemoryRetriever:
    """Orchestrates memory retrieval for inference."""
    
    def __init__(self):
        self.store = MemoryStore()
    
    async def retrieve_for_inference(
        self,
        db: Session,
        user_id: int,
        current_message: str,
        conversation_id: int,
        current_turn: int,
        recent_context: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Retrieve relevant memories for the current inference context.
        
        Returns:
            Dictionary with retrieved memories and metadata
        """
        
        # 1. Semantic search with current message
        semantic_memories = self.store.retrieve_relevant_memories(
            user_id=user_id,
            query=current_message,
            current_turn=current_turn,
            top_k=settings.MEMORY_TOP_K
        )
        
        # 2. Check for specific memory types based on intent
        intent_memories = await self._retrieve_by_intent(
            user_id=user_id,
            message=current_message,
            current_turn=current_turn
        )
        
        # 3. Get critical high-importance memories (always include these)
        critical_memories = self._get_critical_memories(
            db=db,
            user_id=user_id,
            current_turn=current_turn
        )
        
        # 4. Merge and deduplicate
        all_memories = self._merge_memories(
            semantic_memories,
            intent_memories,
            critical_memories
        )
        
        # 5. Format for prompt injection
        formatted_memories = self._format_for_prompt(all_memories)
        
        # 6. Update access stats
        for mem in all_memories:
            if 'db_id' in mem:
                self.store.update_memory_access(db, mem['db_id'], current_turn)
        
        return {
            'memories': formatted_memories,
            'raw_memories': all_memories,
            'count': len(all_memories),
            'retrieval_metadata': {
                'semantic_count': len(semantic_memories),
                'intent_count': len(intent_memories),
                'critical_count': len(critical_memories),
                'current_turn': current_turn
            }
        }
    
    async def _retrieve_by_intent(
        self,
        user_id: int,
        message: str,
        current_turn: int
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on detected intent."""
        
        # Simple keyword-based intent detection
        intents = []
        message_lower = message.lower()
        
        # Time-related queries
        if any(word in message_lower for word in ['when', 'time', 'schedule', 'tomorrow', 'today']):
            intents.append('commitment')
        
        # Preference-related
        if any(word in message_lower for word in ['prefer', 'like', 'want', 'need']):
            intents.append('preference')
        
        # Personal info
        if any(word in message_lower for word in ['who', 'where', 'what about']):
            intents.append('fact')
            intents.append('entity')
        
        if not intents:
            return []
        
        return self.store.retrieve_relevant_memories(
            user_id=user_id,
            query=message,
            current_turn=current_turn,
            top_k=3,
            memory_types=intents
        )
    
    def _get_critical_memories(
        self,
        db: Session,
        user_id: int,
        current_turn: int
    ) -> List[Dict[str, Any]]:
        """Get high-importance memories that should always be considered."""
        from app.models.memory import Memory
        
        critical = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.is_active == True,
            Memory.importance_score >= 0.8,
            Memory.last_accessed_turn < current_turn - 10  # Haven't been used recently
        ).limit(2).all()
        
        return [{
            'db_id': m.id,
            'content': f"{m.memory_type}: {m.key} - {m.value}",
            'metadata': {
                'memory_type': m.memory_type,
                'key': m.key,
                'turn_number': m.source_turn,
                'importance': m.importance_score
            },
            'final_score': m.importance_score
        } for m in critical]
    
    def _merge_memories(self, *memory_lists: List[Dict]) -> List[Dict]:
        """Merge memory lists and remove duplicates."""
        seen = set()
        merged = []
        
        for mem_list in memory_lists:
            for mem in mem_list:
                mem_id = mem.get('vector_id') or mem.get('db_id')
                if mem_id and mem_id not in seen:
                    seen.add(mem_id)
                    merged.append(mem)
        
        # Sort by final score
        merged.sort(key=lambda x: x.get('final_score', 0), reverse=True)
        return merged[:settings.MEMORY_TOP_K + 2]  # Slightly more for safety
    
    def _format_for_prompt(self, memories: List[Dict]) -> str:
        """Format memories for inclusion in LLM prompt."""
        if not memories:
            return ""
        
        lines = ["[Relevant Context from Previous Conversations]"]
        
        for i, mem in enumerate(memories, 1):
            content = mem.get('content', '')
            mem_type = mem.get('metadata', {}).get('memory_type', 'info')
            
            # Clean up content for prompt
            clean_content = content.split(' - ', 1)[-1] if ' - ' in content else content
            
            lines.append(f"{i}. [{mem_type.upper()}] {clean_content}")
        
        lines.append("[End Context]")
        
        return "\n".join(lines)