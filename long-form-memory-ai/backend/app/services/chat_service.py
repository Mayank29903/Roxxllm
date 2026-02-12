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

    def _derive_conversation_title(self, content: str, max_length: int = 60) -> str:
        """Create a compact, readable title from the first user message."""
        cleaned = " ".join((content or "").strip().split())
        if not cleaned:
            return "New Conversation"

        if len(cleaned) <= max_length:
            return cleaned

        truncated = cleaned[:max_length].rstrip()
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        return f"{truncated}..."

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

        # Backfill title from first user message when conversation still has default title.
        # This keeps sidebar titles stable across refreshes, including older chats.
        for conv in conversations:
            if conv.title and conv.title != "New Conversation":
                continue

            first_user_messages = (
                await Message.find(
                    Message.conversation_id == str(conv.id),
                    Message.role == "user"
                )
                .sort("+turn_number")
                .limit(1)
                .to_list()
            )

            if first_user_messages:
                inferred_title = self._derive_conversation_title(first_user_messages[0].content)
                if inferred_title != "New Conversation":
                    conv.title = inferred_title
                    await conv.save()
        
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

        # Use the first user message as conversation "crux" title.
        if conv.turn_count == 0 and (not conv.title or conv.title == "New Conversation"):
            conv.title = self._derive_conversation_title(content)

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
        
        # Enhanced memory retrieval with time-aware access
        print(f"\n===== ENHANCED MEMORY RETRIEVAL FOR TURN {conv.turn_count} =====")
        
        # 1. Get semantically relevant memories based on current message
        relevant_memories = await self.memory_service.search_memories(
            user_id=user_id,
            query_text=content,
            current_turn=conv.turn_count,
            top_k=12  # Increased for better coverage
        )
        print(f"  Semantic search found {len(relevant_memories)} memories")
        
        # 2. Get memories from last 4 hours (addresses the core issue)
        recent_hours_memories = await self.memory_service.get_user_memories(
            user_id=user_id,
            limit=15,
            sort_by="time_created",
            hours_ago=4  # NEW: Get memories from last 4 hours
        )
        print(f"  Last 4 hours: {len(recent_hours_memories)} memories")
        
        # 3. Get memories from last 24 hours for broader context
        last_day_memories = await self.memory_service.get_user_memories(
            user_id=user_id,
            limit=10,
            sort_by="time_created", 
            hours_ago=24
        )
        print(f"  Last 24 hours: {len(last_day_memories)} memories")
        
        # 4. Get the most recent high-importance memories (preferences, instructions)
        recent_important = await self.memory_service.get_user_memories(
            user_id=user_id,
            limit=8,
            sort_by="recency"  # Hybrid sort for cross-conversation awareness
        )
        print(f"  Recent important: {len(recent_important)} memories")

        # 5. Always include a broader set of preferences for cross-chat inference
        preference_memories = await self.memory_service.get_user_memories(
            user_id=user_id,
            memory_type="preference",
            limit=30,  # Reduced but still comprehensive
            sort_by="time_created"  # Changed to time-based for better recall
        )
        print(f"  All preferences: {len(preference_memories)} memories")
        print("=========================================================\n")
        
        # 6. Enhanced merging and prioritization with time-aware deduplication
        memory_map = {}
        
        # Priority order for memory sources (most important first):
        # 1. Recent hours memories (highest priority - addresses the 3-4 hour issue)
        # 2. Last day memories (high priority)
        # 3. Recent important memories (medium-high priority)  
        # 4. Preference memories (medium priority)
        # 5. Semantic search memories (baseline)
        
        priority_groups = [
            (recent_hours_memories, "last_4_hours"),
            (last_day_memories, "last_24_hours"),
            (recent_important, "recent_important"),
            (preference_memories, "preferences"),
            (relevant_memories, "semantic")
        ]
        
        for mem_group, group_name in priority_groups:
            for mem in mem_group:
                key = f"{mem.memory_type}_{mem.key}"
                
                # If memory doesn't exist, add it
                if key not in memory_map:
                    memory_map[key] = mem
                    print(f"  Added {group_name}: [{mem.memory_type}] {mem.key}")
                else:
                    # If memory exists, keep the more recent one by creation time
                    existing = memory_map[key]
                    if mem.created_at > existing.created_at:
                        memory_map[key] = mem
                        print(f"  Updated {group_name}: [{mem.memory_type}] {mem.key} (newer)")
        
        # Convert to list and sort by creation time first, then by source_turn
        def enhanced_sort_key(mem):
            # Primary sort: creation time (most recent first)
            # Secondary sort: turn number (higher = more recent in conversation)
            return (mem.created_at, mem.source_turn)
        
        memories = list(memory_map.values())
        memories.sort(key=enhanced_sort_key, reverse=True)
        
        print(f"\n📋 Final merged memories: {len(memories)} total")
        for i, mem in enumerate(memories[:8]):  # Show top 8 for debugging
            hours_old = (datetime.utcnow() - mem.created_at).total_seconds() / 3600
            print(f"  {i+1}. [{mem.memory_type}] {mem.key}: {mem.value} ({hours_old:.1f}h ago)")
        print("")
        
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

        # Enhanced memory extraction with reliability and fallbacks
        extraction_decision = self.memory_extractor.should_extract(conv.turn_count, content)
        
        if extraction_decision["should_extract"]:
            print(f"\n🧠 MEMORY EXTRACTION STARTED - Priority: {extraction_decision['priority']}")
            print(f"   Reason: {extraction_decision['reason']}")
            print(f"   Force: {extraction_decision.get('force_extraction', False)}")
            
            try:
                # First extraction attempt
                extracted = await self.memory_extractor.extract_memories(
                    user_message=content,
                    assistant_response=full_response,
                    turn_number=conv.turn_count,
                    conversation_history=[{"role": m.role, "content": m.content} for m in history[-5:]],
                    extraction_boost=extraction_decision.get("extraction_boost", 0.0)
                )
                
                # Backup extraction if nothing was extracted but should have been
                if not extracted and extraction_decision.get("priority") in ["critical", "high"]:
                    print("⚠️ NO MEMORIES EXTRACTED - Running backup extraction...")
                    backup_extracted = await self._backup_extraction(
                        user_message=content,
                        assistant_response=full_response,
                        turn_number=conv.turn_count,
                        priority=extraction_decision["priority"]
                    )
                    extracted.extend(backup_extracted)
                
                if extracted:
                    print(f"\n===== EXTRACTED {len(extracted)} MEMORIES =====")
                    memories_stored = 0
                    
                    for mem in extracted:
                        try:
                            # Apply importance boost based on extraction priority
                            if extraction_decision.get("extraction_boost"):
                                mem["importance"] = min(1.0, mem.get('importance', 0.5) + extraction_decision["extraction_boost"])
                            
                            print(f"  [{mem['type']}] {mem['key']}: {mem['value']} (confidence: {mem.get('confidence', 0.5):.2f}, importance: {mem.get('importance', 0.5):.2f})")
                            
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
                                context=f"From conversation turn {conv.turn_count} (priority: {extraction_decision['priority']})"
                            )
                            memories_stored += 1
                            
                        except Exception as mem_error:
                            print(f"  ❌ Failed to store memory [{mem.get('key', 'unknown')}]: {mem_error}")
                    
                    print(f"✅ Successfully stored {memories_stored}/{len(extracted)} memories")
                    print("=========================================\n")
                else:
                    print("📝 No memories found in this turn")
                    
            except Exception as e:
                print(f"❌ Memory extraction failed: {e}")
                # Try emergency fallback extraction for critical cases
                if extraction_decision.get("priority") == "critical":
                    print("🚨 ATTEMPTING EMERGENCY EXTRACTION...")
                    await self._emergency_memory_extraction(
                        user_id=user_id,
                        user_message=content,
                        conversation_id=conversation_id,
                        turn_number=conv.turn_count
                    )

        yield {
            "type": "complete",
            "message": {
                "id": str(assistant_msg.id),
                "content": full_response,
                "turn_number": conv.turn_count,
                "created_at": assistant_msg.created_at.isoformat(),
            },
            "conversation": {
                "id": str(conv.id),
                "title": conv.title,
                "turn_count": conv.turn_count,
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else datetime.utcnow().isoformat(),
            },
            "memory_metadata": {
                "active_memories": active_memory_ids
            }
        }

    async def _backup_extraction(
        self,
        user_message: str,
        assistant_response: str,
        turn_number: int,
        priority: str
    ) -> List[Dict[str, Any]]:
        """
        Backup extraction method for cases where primary extraction fails but 
        we know there should be memories (based on priority signals).
        """
        print(f"🔄 Running backup extraction (priority: {priority})")
        
        # Simpler, more aggressive extraction prompt
        backup_prompt = f"""Extract EVERY important piece of personal information from this conversation:

User said: "{user_message}"
Assistant responded: "{assistant_response[:200]}..."

Look for:
- Name, age, location, work, school
- Preferences, favorites, likes, dislikes  
- Relationships (family, friends)
- Health information, allergies
- Habits, routines, schedules
- Goals, plans, commitments
- ANY personal detail that might be useful later

For each item found, return:
{{
  "type": "preference/fact/entity/habit/goal",
  "key": "specific_identifier", 
  "value": "the_information",
  "confidence": 0.8,
  "importance": 0.7
}}

Return as JSON array. If nothing found, return []."""

        try:
            # Use simpler LLM call for backup
            from app.services.llm_service import LLMService
            llm_service = LLMService()
            
            response = llm_service.generate_response(
                messages=[
                    {"role": "system", "content": "You extract personal information for memory storage."},
                    {"role": "user", "content": backup_prompt}
                ],
                stream=False,
                max_tokens=800,
                temperature=0.1
            )
            
            # Process response
            full_response = ""
            async for event in response:
                if event["type"] in ("token", "final"):
                    full_response += event.get("content", "")
            
            # Parse the response
            import re
            import json
            
            content = re.sub(r'```json\s*', '', full_response)
            content = re.sub(r'```\s*', '', content)
            
            try:
                memories = json.loads(content)
                if isinstance(memories, list):
                    print(f"✅ Backup extraction found {len(memories)} memories")
                    return memories
            except json.JSONDecodeError:
                print("❌ Failed to parse backup extraction JSON")
                
        except Exception as e:
            print(f"❌ Backup extraction failed: {e}")
        
        return []

    async def _emergency_memory_extraction(
        self,
        user_id: str,
        user_message: str,
        conversation_id: str,
        turn_number: int
    ):
        """
        Emergency extraction for critical cases where main extraction failed completely.
        Uses keyword-based detection to ensure important information is not lost.
        """
        print("🚨 EMERGENCY EXTRACTION - Using keyword detection")
        
        emergency_patterns = {
            "name": [r"my name is (\w+)", r"call me (\w+)", r"i'm (\w+)", r"i am (\w+)"],
            "location": [r"i live in ([\w\s]+)", r"from ([\w\s]+)", r"work at ([\w\s]+)"],
            "preference": [r"i like ([\w\s]+)", r"i love ([\w\s]+)", r"favorite ([\w\s]+)"],
            "age": [r"(\d+) years old", r"age (\d+)", r"(\d+)\s?years? old"]
        }
        
        import re
        found_memories = []
        
        for memory_type, patterns in emergency_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, user_message.lower())
                if matches:
                    for match in matches:
                        try:
                            await self.memory_service.create_memory(
                                user_id=user_id,
                                memory_type="fact" if memory_type != "preference" else "preference",
                                key=f"emergency_{memory_type}",
                                value=match.strip(),
                                conversation_id=conversation_id,
                                turn_number=turn_number,
                                confidence=0.6,  # Lower confidence for emergency extraction
                                importance=0.8,  # But high importance to preserve it
                                context=f"Emergency extraction turn {turn_number} - failed main extraction"
                            )
                            found_memories.append(f"{memory_type}: {match}")
                        except Exception as e:
                            print(f"  ❌ Emergency memory creation failed: {e}")
        
        if found_memories:
            print(f"🚨 EMERGENCY EXTRACTION SAVED {len(found_memories)} MEMORIES:")
            for mem in found_memories:
                print(f"   - {mem}")
        else:
            print("🚨 Emergency extraction found no patterns")
