from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.chat import Conversation, Message
from app.models.memory import Memory
from app.core.memory_extractor import MemoryExtractor
from app.core.retriever import MemoryRetriever
from app.services.llm_service import LLMService


class ChatService:
    """Orchestrates chat with long-form memory."""
    
    def __init__(self):
        self.memory_extractor = MemoryExtractor()
        self.memory_retriever = MemoryRetriever()
        self.llm_service = LLMService()
    
    async def create_conversation(self, db: Session, user_id: int, title: str = None) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            user_id=user_id,
            title=title or "New Conversation"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv
    
    async def process_message(
        self,
        db: Session,
        user_id: int,
        conversation_id: int,
        content: str,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a message with full memory pipeline."""
        
        # Get conversation
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Increment turn count
        current_turn = conv.turn_count + 1
        conv.turn_count = current_turn
        
        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            turn_number=current_turn,
            role="user",
            content=content
        )
        db.add(user_msg)
        db.commit()
        
        # 1. RETRIEVE relevant memories
        recent_history = self._get_recent_history(db, conversation_id, limit=10)
        
        retrieval_result = await self.memory_retriever.retrieve_for_inference(
            db=db,
            user_id=user_id,
            current_message=content,
            conversation_id=conversation_id,
            current_turn=current_turn,
            recent_context=recent_history
        )
        
        memory_context = retrieval_result['memories']
        
        # 2. GENERATE response with memory
        messages = self.llm_service.build_conversation_messages(recent_history, content)
        
        full_response = ""
        
        async for chunk in self.llm_service.generate_response(
            messages=messages,
            memory_context=memory_context,
            stream=stream
        ):
            full_response += chunk
            if stream:
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "turn_number": current_turn
                }
        
        # Save assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            turn_number=current_turn,
            role="assistant",
            content=full_response,
            active_memories=[m.get('vector_id') or m.get('db_id') for m in retrieval_result['raw_memories']]
        )
        db.add(assistant_msg)
        db.commit()
        
        # 3. EXTRACT new memories (async, non-blocking for response)
        if self.memory_extractor.should_extract(current_turn):
            extracted = await self.memory_extractor.extract_memories(
                user_message=content,
                assistant_response=full_response,
                turn_number=current_turn,
                conversation_history=recent_history
            )
            
            # Store extracted memories
            for mem_data in extracted:
                from app.core.memory_store import MemoryStore
                store = MemoryStore()
                memory = store.store_memory(
                    db=db,
                    user_id=user_id,
                    memory_data=mem_data,
                    conversation_id=conversation_id,
                    turn_number=current_turn
                )
                assistant_msg.extracted_memories.append(memory.id)
            
            db.commit()
        
        # Final response metadata
        yield {
            "type": "complete",
            "message": {
                "id": assistant_msg.id,
                "content": full_response,
                "turn_number": current_turn,
                "created_at": assistant_msg.created_at.isoformat()
            },
            "memory_metadata": {
                "retrieved_count": retrieval_result['count'],
                "extracted_count": len(assistant_msg.extracted_memories),
                "active_memories": [
                    {
                        "type": m.get('metadata', {}).get('memory_type'),
                        "content": m.get('content', '')[:100] + "..."
                    }
                    for m in retrieval_result['raw_memories']
                ]
            }
        }
    
    def _get_recent_history(self, db: Session, conversation_id: int, limit: int = 10) -> List[Dict]:
        """Get recent message history."""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.turn_number.desc()).limit(limit).all()
        
        return [
            {"role": msg.role, "content": msg.content, "turn": msg.turn_number}
            for msg in reversed(messages)
        ]
    
    async def get_conversation_history(
        self,
        db: Session,
        conversation_id: int,
        user_id: int,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get full conversation history."""
        conv = db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
        
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.turn_number).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "turn_number": msg.turn_number,
                "created_at": msg.created_at.isoformat(),
                "active_memories": msg.active_memories
            }
            for msg in messages
        ]