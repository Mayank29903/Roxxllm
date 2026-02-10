from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from fastapi import HTTPException
from app.models.chat import Conversation, Message
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.core.memory_extractor import MemoryExtractor


class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.memory_extractor = MemoryExtractor()

    def _format_memories_for_context(self, memories: List[Any]) -> str:
        """Format memories for injection into LLM context."""
        if not memories:
            return ""
        
        lines = ["You have access to the following information from previous conversations with this user:"]
        lines.append("")
        
        for mem in memories:
            lines.append(f"- [{mem.memory_type.upper()}] {mem.key}: {mem.value}")
        
        lines.append("")
        lines.append("Use this information naturally when relevant to the conversation. Don't mention that you have access to this context unless directly asked.")
        
        return "\n".join(lines)

    async def create_conversation(
        self,
        user_id: str,
        title: str = None
    ) -> Conversation:
        conv = Conversation(
            user_id=user_id,
            title=title or "New Conversation"
        )
        await conv.insert()
        return conv

    async def get_user_conversations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a user."""
        conversations = (
            await Conversation.find(Conversation.user_id == user_id)
            .sort("-created_at")
            .limit(limit)
            .to_list()
        )
        
        return [
            {
                "id": str(conv.id),
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else conv.created_at.isoformat(),
                "turn_count": conv.turn_count
            }
            for conv in conversations
        ]

    async def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:

        conv = await Conversation.get(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = (
            await Message.find(Message.conversation_id == conversation_id)
            .sort("+turn_number")
            .limit(limit)
            .to_list()
        )

        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "turn_number": m.turn_number,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]

    async def process_message(
        self,
        user_id: str,
        conversation_id: str,
        content: str,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:

        print("\n===== CHAT INPUT =====")
        print("User:", user_id)
        print("Conversation:", conversation_id)
        print("Message:", content)
        print("Stream:", stream)
        print("======================\n")

        conv = await Conversation.get(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")

        conv.turn_count += 1
        conv.updated_at = datetime.utcnow()
        await conv.save()

        # Save user message
        user_msg = Message(
            conversation_id=conversation_id,
            turn_number=conv.turn_count,
            role="user",
            content=content
        )
        await user_msg.insert()

        # Build history
        history = await Message.find(
            Message.conversation_id == conversation_id
        ).sort("+turn_number").to_list()

        messages = [
            {"role": m.role, "content": m.content}
            for m in history
        ]

        # Retrieve relevant memories from ALL past conversations (not just current one)
        memories = await self.memory_service.get_user_memories(
            user_id=user_id,
            limit=20
        )
        
        active_memory_ids = []
        
        # Format memories and inject into context if any exist
        if memories:
            memory_context = self._format_memories_for_context(memories)
            # Inject memory context as a system message before the conversation
            messages = [
                {"role": "system", "content": memory_context}
            ] + messages
            active_memory_ids = [str(m.id) for m in memories]
            
            print("\n===== ACTIVE MEMORIES =====")
            for m in memories:
                print(f"  [{m.memory_type}] {m.key}: {m.value}")
            print("===========================\n")

        print("\n===== CONTEXT TO LLM =====")
        for m in messages:
            print(m)
        print("=========================\n")

        full_response = ""

        async for event in self.llm_service.generate_response(
            messages=messages,
            stream=stream
        ):
            print("LLM EVENT:", event)

            if event["type"] in ("token", "final"):
                chunk = event.get("content", "")
                full_response += chunk

                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk
                    }

            elif event["type"] == "error":
                yield event
                return

        print("\n===== FINAL RESPONSE =====")
        print(full_response)
        print("==========================\n")

        assistant_msg = Message(
            conversation_id=conversation_id,
            turn_number=conv.turn_count,
            role="assistant",
            content=full_response,
            active_memories=active_memory_ids
        )
        await assistant_msg.insert()

        # Extract and store memories from this conversation turn
        if self.memory_extractor.should_extract(conv.turn_count):
            try:
                extracted = await self.memory_extractor.extract_memories(
                    user_message=content,
                    assistant_response=full_response,
                    turn_number=conv.turn_count,
                    conversation_history=[{"role": m.role, "content": m.content} for m in history[-5:]]
                )
                
                if extracted:
                    print(f"\n===== EXTRACTED {len(extracted)} MEMORIES =====")
                    for mem in extracted:
                        print(f"  [{mem['type']}] {mem['key']}: {mem['value']}")
                        # Store in database
                        await self.memory_service.create_memory(
                            user_id=user_id,
                            memory_type=mem['type'],
                            key=mem['key'],
                            value=mem['value'],
                            conversation_id=conversation_id,
                            turn_number=conv.turn_count,
                            confidence=mem.get('confidence', 0.5),
                            importance=mem.get('importance', 0.5),
                            context=f"From conversation turn {conv.turn_count}"
                        )
                    print("=========================================\n")
            except Exception as e:
                print(f"Memory extraction failed: {e}")

        yield {
            "type": "complete",
            "message": {
                "id": str(assistant_msg.id),
                "content": full_response,
                "turn_number": conv.turn_count,
                "created_at": assistant_msg.created_at.isoformat(),
            },
            "memory_metadata": {
                "active_memories": active_memory_ids
            }
        }