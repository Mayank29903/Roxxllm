from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime
from fastapi import HTTPException
from app.models.chat import Conversation, Message
from app.services.llm_service import LLMService
from app.services.memory_service import MemoryService
from app.core.memory_extractor import MemoryExtractor
from app.core.memory_reasoner import MemoryReasoner


class ChatService:
    def __init__(self):
        self.llm_service = LLMService()
        self.memory_service = MemoryService()
        self.memory_extractor = MemoryExtractor()
        self.memory_reasoner = MemoryReasoner()

    def _format_memories_for_context(self, memories: List[Any]) -> str:
        """
        Format memories for injection into LLM context.
        Prioritizes recent preferences and facts.
        """
        if not memories:
            return ""
        
        lines = ["You have access to the following information from previous conversations with this user:"]
        lines.append("")
        
        # Group memories by type for better organization
        grouped = {}
        for mem in memories:
            # All memories are now Memory objects
            mem_type = mem.memory_type
            key = mem.key
            value = mem.value
            
            if mem_type not in grouped:
                grouped[mem_type] = []
            grouped[mem_type].append(f"{key}: {value}")
        
        # Format by priority: preferences first (most recent), then facts, etc.
        priority_order = ['preference', 'instruction', 'fact', 'entity', 'commitment', 'constraint']
        
        for mem_type in priority_order:
            if mem_type in grouped:
                lines.append(f"**{mem_type.upper()}S:**")
                for item in grouped[mem_type]:
                    lines.append(f"  • {item}")
                lines.append("")
        
        # Add any other types not in priority list
        for mem_type, items in grouped.items():
            if mem_type not in priority_order:
                lines.append(f"**{mem_type.upper()}:**")
                for item in items:
                    lines.append(f"  • {item}")
                lines.append("")
        
        lines.append("IMPORTANT: Use the most recent preferences. If preferences conflict, the user's latest stated preference takes priority.")
        lines.append("Use this information naturally when relevant. Don't mention you have this context unless asked.")
        
        return "\n".join(lines)

    def _build_system_context(self) -> str:
        now = datetime.now().astimezone()
        date_str = now.strftime("%A, %Y-%m-%d")
        time_str = now.strftime("%H:%M:%S %Z")
        iso_str = now.isoformat()

        return (
            "You are a helpful assistant with long-term memory. "
            "Use stored memories and logical inference to answer personal questions when possible. "
            "If a preference implies a specific choice, infer it using common knowledge. "
            "If uncertain, ask a brief clarifying question instead of guessing.\n\n"
            f"Current date/time: {date_str} {time_str} (ISO: {iso_str}). "
            "Use this for questions like today/tomorrow/yesterday or current time."
        )

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
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a conversation and ALL its associated memories.
        This ensures memories from deleted conversations don't leak into other chats.
        """
        
        # 1. Verify ownership
        conv = await Conversation.get(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        print(f"\n🗑️ Deleting conversation {conversation_id} and its memories...")
        
        # 2. Delete all memories associated with this conversation
        memories_deleted = await self.memory_service.delete_conversation_memories(
            conversation_id=conversation_id,
            user_id=user_id
        )
        print(f"   Deleted {memories_deleted} memories")
        
        # 3. Delete all messages in the conversation
        messages = await Message.find(Message.conversation_id == conversation_id).to_list()
        for msg in messages:
            await msg.delete()
        print(f"   Deleted {len(messages)} messages")
        
        # 4. Delete the conversation itself
        await conv.delete()
        print(f"✅ Conversation deleted successfully")
        
        return True

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

        # Retrieve relevant memories using BOTH semantic search AND recency
        # This ensures latest preferences are always considered
        
        # 1. Get semantically relevant memories based on current message
        relevant_memories = await self.memory_service.search_memories(
            user_id=user_id,
            query_text=content,
            current_turn=conv.turn_count,
            top_k=8
        )
        
        # 2. Also get the most recent high-importance memories (preferences, instructions)
        recent_important = await self.memory_service.get_user_memories(
            user_id=user_id,
            limit=10,
            sort_by="recency"  # Sort by recency to get latest preferences
        )

        # 2b. Always include a broader set of preferences for cross-chat inference
        preference_memories = await self.memory_service.get_user_memories(
            user_id=user_id,
            memory_type="preference",
            limit=50,
            sort_by="recency"
        )
        
        # 3. Merge and deduplicate (both are Memory objects now)
        memory_map = {}
        
        # Add recent important memories first
        for mem in recent_important:
            key = f"{mem.memory_type}_{mem.key}"
            if key not in memory_map:
                memory_map[key] = mem

        # Add broader preference memories next (supports inference across chats)
        for mem in preference_memories:
            key = f"{mem.memory_type}_{mem.key}"
            if key not in memory_map:
                memory_map[key] = mem
        
        # Add semantically relevant memories, preferring more recent ones
        for mem in relevant_memories:
            key = f"{mem.memory_type}_{mem.key}"
            # Only add if not already present or if this one is more recent
            if key not in memory_map or mem.source_turn > memory_map[key].source_turn:
                memory_map[key] = mem
        
        # Convert to list and sort by source_turn (most recent first)
        memories = list(memory_map.values())
        memories.sort(key=lambda x: x.source_turn, reverse=True)
        
        active_memory_ids = [str(m.id) for m in memories]
        
        # REASONING LAYER: Check if we can infer answers from memories
        # This enables the system to answer questions about things not explicitly stated
        inference_result = None
        if memories:
            print("\n===== CHECKING FOR INFERENCE OPPORTUNITIES =====")
            # Convert Message objects to dictionaries for reasoner
            history_dicts = [
                {"role": m.role, "content": m.content}
                for m in history[-5:] if history
            ]
            inference_result = await self.memory_reasoner.reason_over_memories(
                user_query=content,
                memories=memories,
                conversation_history=history_dicts,
                user_id=user_id
            )
            
            if inference_result["should_use"] and inference_result["inferred_answer"]:
                print(f"✓ Inference found with confidence {inference_result['confidence']:.2f}")
                print(f"  Answer: {inference_result['inferred_answer']}")
                print(f"  Reasoning: {inference_result['inference_chain']}")
                # Add inference hint to memories context for the LLM
                inference_hint = f"\n\n[INFERENCE OPPORTUNITY]: Based on the user's preferences and facts, we can infer that: {inference_result['inferred_answer']}\nReasoning: {inference_result['inference_chain']}\nPlease use this inference naturally in your response if relevant to the user's question."
            else:
                print(f"✗ No confident inference possible (confidence: {inference_result['confidence']:.2f})")
                inference_hint = None
            print("=================================================\n")
        else:
            inference_hint = None
        
        system_context = self._build_system_context()

        # Format memories and inject into context if any exist
        if memories:
            memory_context = self._format_memories_for_context(memories)
            if inference_hint:
                memory_context += inference_hint
            messages = [
                {"role": "system", "content": system_context},
                {"role": "system", "content": memory_context}
            ] + messages
        else:
            messages = [
                {"role": "system", "content": system_context}
            ] + messages
            
            print("\n===== ACTIVE MEMORIES (Sorted by Recency) =====")
            for m in memories[:10]:  # Show top 10
                print(f"  Turn {m.source_turn}: [{m.memory_type}] {m.key}: {m.value}")
            print("===============================================\n")

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

        # Update memory access statistics for the memories that were used
        if active_memory_ids:
            for memory_id in active_memory_ids:
                await self.memory_service.refresh_memory_access(
                    memory_id=memory_id,
                    user_id=user_id,
                    current_turn=conv.turn_count
                )

        # Extract and store memories from this conversation turn
        if self.memory_extractor.should_extract(conv.turn_count, content):
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