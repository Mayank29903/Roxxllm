import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI
from app.config import settings

client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)


class MemoryExtractor:
    """Extracts structured memories from conversation turns using LLM."""
    
    def __init__(self):
        pass
        self.extraction_prompt = """You are a memory extraction system. Analyze the conversation and extract important information that should be remembered for future interactions.

Extract memories in these categories:
1. **preference**: User likes, dislikes, choices (language, style, timing)
2. **fact**: Personal information, demographics, important facts
3. **entity**: Important people, places, organizations mentioned
4. **commitment**: Promises, scheduled events, deadlines
5. **instruction**: Explicit instructions on how to behave or respond
6. **constraint**: Limitations, restrictions, boundaries

Also extract GENERAL PREFERENCE RULES when the user expresses a broad pattern.
Examples:
- "In any anime, my favorite character is the main character" -> preference key: favorite_anime_character_type, value: main character
- "I usually prefer vegetarian food" -> preference key: dietary_preference, value: vegetarian

For each memory found, provide:
- type: One of the categories above
- key: Short semantic identifier (e.g., "language_preference", "call_time")
- value: The specific information to remember
- confidence: 0.0 to 1.0 score
- importance: 0.0 to 1.0 score (how critical this is)

Conversation:
{conversation}

Respond ONLY with a JSON array of memories. If no memories found, return empty array [].
Example:
[
  {{
    "type": "preference",
    "key": "language",
    "value": "Kannada",
    "confidence": 0.95,
    "importance": 0.8
  }}
]"""
    
    async def extract_memories(
        self,
        user_message: str,
        assistant_response: str,
        turn_number: int,
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict[str, Any]]:
        """Extract memories from a conversation turn."""
        
        # Build context
        context = self._build_context(conversation_history, user_message, assistant_response)
        
        try:
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You extract structured memories from conversations."},
                    {"role": "user", "content": self.extraction_prompt.format(conversation=context)}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            print("\n===== MEMORY EXTRACTOR RESPONSE =====")
            print(content)
            print("====================================\n")
            
            # Clean up JSON response
            content = re.sub(r'```json\s*', '', content)
            content = re.sub(r'```\s*', '', content)
            
            memories = json.loads(content)
            
            # Validate and enrich memories
            validated_memories = []
            for mem in memories:
                if self._validate_memory(mem):
                    mem['source_turn'] = turn_number
                    mem['extracted_at'] = datetime.utcnow().isoformat()
                    validated_memories.append(mem)
            
            return validated_memories
            
        except Exception as e:
            print(f"Memory extraction error: {e}")
            return []
    
    def _build_context(
        self,
        history: Optional[List[Dict]],
        current_user_msg: str,
        current_assistant_msg: str
    ) -> str:
        """Build conversation context for extraction."""
        lines = []
        
        if history:
            for msg in history[-5:]:  # Last 5 messages for context
                role = "User" if msg['role'] == 'user' else "Assistant"
                lines.append(f"{role}: {msg['content']}")
        
        lines.append(f"User: {current_user_msg}")
        lines.append(f"Assistant: {current_assistant_msg}")
        
        return "\n".join(lines)
    
    def _validate_memory(self, memory: Dict) -> bool:
        """Validate extracted memory structure."""
        required = ['type', 'key', 'value', 'confidence', 'importance']
        return all(field in memory for field in required)
    
    def should_extract(self, turn_number: int, user_message: Optional[str] = None) -> bool:
        """Determine if we should run extraction on this turn."""
        # Extract on specific turns to balance performance and coverage
        # Turn 1 (initial preferences), then every 5 turns, and every 50th turn
        if turn_number == 1 or turn_number % 5 == 0 or turn_number % 50 == 0:
            return True

        return self._has_memory_signal(user_message)

    def _has_memory_signal(self, user_message: Optional[str]) -> bool:
        """Lightweight heuristic to detect messages likely containing memories."""
        if not user_message:
            return False

        message = user_message.lower()
        signals = [
            "my name", "i am", "i'm", "call me", "you can call me",
            "i go to", "i study", "i work", "i live", "i am from",
            "my favorite", "i like", "i love", "i hate", "i prefer",
            "language", "speak", "remember", "my birthday", "my age"
        ]

        return any(signal in message for signal in signals)