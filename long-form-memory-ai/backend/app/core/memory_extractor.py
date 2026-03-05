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
        self.extraction_prompt = """You are a long-term memory extraction system. Extract only durable personal information that is likely to remain useful across future conversations.

Keep only stable and user-centric memories, such as:
- identity/background (name, work, studies, city, relationships)
- lasting preferences (food, media tastes, language, routines)
- long-term commitments/goals
- explicit long-term assistant behavior preferences

Extract memories in these categories:
1. **preference**: User likes, dislikes, choices, favorites (language, style, timing, entertainment, food, etc.)
2. **fact**: Personal information, demographics, background, education, work, family details
3. **entity**: Important people, places, organizations, brands, specific items mentioned
4. **commitment**: Promises, scheduled events, deadlines, plans, intentions
5. **instruction**: Explicit instructions on how to behave or respond
6. **constraint**: Limitations, restrictions, boundaries, things to avoid
7. **habit**: Routines, patterns, regular behaviors (e.g., "I usually wake up at 7am")
8. **opinion**: Strong feelings, beliefs, values, perspectives on topics
9. **temporary_state**: Current situations, moods, ongoing projects (may be less permanent)
10. **goal**: Aspirations, targets, things user wants to achieve

DETAILED EXTRACTION RULES:
- Extract BOTH specific and general preferences
- Capture numbers, quantities, time references
- Note emotional reactions (likes, hates, loves, fears)
- Remember context around preferences (e.g., "only on weekends", "when I'm stressed")
- Extract relationships and social connections
- Capture ANY pattern or routine the user mentions
- Note professional/educational background details
- Extract health information, dietary restrictions, allergies
- Remember entertainment preferences in detail

DO NOT EXTRACT:
- one-off task instructions tied to the current query (e.g., "put all code in main", "answer in bullet points")
- transient formatting requests, coding-output constraints, or short-lived workflow directions
- content that is not about the user's personal profile/preferences
- duplicate variants of the same preference/fact with different keys

GENERAL PREFERENCE PATTERN EXAMPLES:
- "In any anime, my favorite character is the main character" -> preference: favorite_anime_character_type = main character
- "I usually prefer vegetarian food but eat meat on weekends" -> preference: dietary_preference = vegetarian, constraint: dietary_exception = meat_on_weekends
- "I wake up at 7am on weekdays" -> habit: wake_up_weekday_time = 7am
- "My sister works at Google" -> entity: sister_workplace = Google, fact: has_sister = yes

For each memory found, provide:
- type: One of the categories above
- key: Specific, semantic identifier (e.g., "favorite_movie_genre", "sister_name")
- value: The exact information to remember (include numbers, names, specifics)
- confidence: 0.0 to 1.0 score (how certain you are this is correct)
- importance: 0.0 to 1.0 score (how critical this is for future conversations)

Conversation:
{conversation}

Respond ONLY with a JSON array of memories. If no memories found, return empty array [].
Example:
[
  {{
    "type": "preference",
    "key": "language_preference",
    "value": "Kannada",
    "confidence": 0.95,
    "importance": 0.8
  }},
  {{
    "type": "habit",
    "key": "morning_routine",
    "value": "wakes up at 7am on weekdays",
    "confidence": 0.9,
    "importance": 0.6
  }}
]"""
    
    async def extract_memories(
        self,
        user_message: str,
        assistant_response: str,
        turn_number: int,
        conversation_history: Optional[List[Dict]] = None,
        extraction_boost: float = 0.0
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
                    mem["type"] = str(mem.get("type", "")).strip().lower()
                    mem["key"] = str(mem.get("key", "")).strip().lower().replace(" ", "_")
                    mem["value"] = str(mem.get("value", "")).strip()
                    mem["confidence"] = float(mem.get("confidence", 0.0))
                    mem["importance"] = float(mem.get("importance", 0.0))
                    mem['source_turn'] = turn_number
                    mem['extracted_at'] = datetime.utcnow().isoformat()
                    
                    # Apply extraction boost to importance
                    if extraction_boost > 0:
                        mem['importance'] = min(1.0, mem.get('importance', 0.5) + extraction_boost)
                        print(f"   Applied extraction boost +{extraction_boost:.1f} to [{mem['type']}] {mem['key']}")

                    if self._is_useful_memory(mem):
                        validated_memories.append(mem)
            
            # Special handling: If extraction was forced but nothing was found, try minimal extraction
            if extraction_boost >= 1.5 and not validated_memories:
                print("   🚨 HIGH PRIORITY EXTRACTION YIELDED NOTHING - ATTEMPTING MINIMAL EXTRACTION")
                minimal_memories = await self._minimal_extraction(
                    user_message, assistant_response, turn_number, extraction_boost
                )
                validated_memories.extend(minimal_memories)
            
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

    def _normalize_text(self, value: str) -> str:
        return re.sub(r"\s+", " ", (value or "").strip().lower())

    def _is_task_specific_memory(self, memory: Dict[str, Any]) -> bool:
        blob = self._normalize_text(
            f"{memory.get('type', '')} {memory.get('key', '')} {memory.get('value', '')}"
        )
        task_specific_markers = [
            "main function",
            "single file",
            "full code",
            "write code",
            "coding style",
            "output format",
            "response format",
            "this task",
            "this question",
            "for this prompt",
            "assistant response",
            "factorial",
            "cpp",
            "c++",
            "python code",
            "java code",
        ]
        return any(marker in blob for marker in task_specific_markers)

    def _is_useful_memory(self, memory: Dict[str, Any]) -> bool:
        mem_type = self._normalize_text(memory.get("type", ""))
        key = self._normalize_text(memory.get("key", ""))
        value = self._normalize_text(memory.get("value", ""))
        confidence = float(memory.get("confidence", 0.0))
        importance = float(memory.get("importance", 0.0))

        if not mem_type or not key or not value:
            return False

        if len(value) < 2:
            return False

        if value in {"yes", "no", "ok", "none", "na", "n/a"}:
            return False

        # Keep strong memories only.
        if confidence < 0.6 or importance < 0.55:
            return False

        if self._is_task_specific_memory(memory):
            return False

        if mem_type in {"temporary_state"}:
            return False

        return True
    
    def should_extract(self, turn_number: int, user_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Enhanced extraction logic with multiple priority levels.
        Returns detailed extraction decision with reasons.
        """
        if not user_message:
            return {"should_extract": False, "reason": "no_message", "priority": "none"}
        
        result = {
            "should_extract": False,
            "reason": "",
            "priority": "none",
            "force_extraction": False,
            "extraction_boost": 0.0
        }
        
        message_lower = user_message.lower()
        
        # PRIORITY 1: EXPLICIT MEMORY COMMANDS (Highest Priority)
        explicit_commands = ["remember", "don't forget", "this is important", "make a note", "keep in mind"]
        if any(cmd in message_lower for cmd in explicit_commands):
            result.update({
                "should_extract": True,
                "reason": "explicit_memory_command",
                "priority": "critical",
                "force_extraction": True,
                "extraction_boost": 2.0
            })
            print(f"🚨 EXPLICIT MEMORY COMMAND DETECTED: '{user_message[:50]}...'")
            return result
        
        # PRIORITY 2: HIGH-IMPORTANCE SIGNALS
        importance_signals = [
            "my name", "i am", "i'm", "call me", "you can call me",
            "i work at", "i study at", "i go to", "i live in", "i am from",
            "allergic to", "i have a", "my medical", "health condition",
            "emergency contact", "important", "crucial", "critical"
        ]
        
        if any(signal in message_lower for signal in importance_signals):
            result.update({
                "should_extract": True,
                "reason": "high_importance_signal",
                "priority": "high",
                "extraction_boost": 1.5
            })
            print(f"⚡ HIGH IMPORTANCE SIGNAL: '{user_message[:50]}...'")
            return result
        
        # PRIORITY 3: REGULAR MEMORY SIGNALS
        if self._has_memory_signal(user_message):
            result.update({
                "should_extract": True,
                "reason": "memory_signal_detected",
                "priority": "medium",
                "extraction_boost": 1.0
            })
            return result
        
        # PRIORITY 4: FREQUENCY-BASED EXTRACTION (light background coverage)
        if turn_number == 1 or turn_number % 5 == 0:
            result.update({
                "should_extract": True,
                "reason": "frequency_based",
                "priority": "low",
                "extraction_boost": 0.3
            })
            print(f"🔄 FREQUENCY EXTRACTION: Turn {turn_number}")
            return result
        
        
        result["reason"] = "no_memory_signal"
        return result

    def _has_memory_signal(self, user_message: Optional[str]) -> bool:
        """Enhanced heuristic to detect messages likely containing memories."""
        if not user_message:
            return False

        message = user_message.lower()
        
        # Expanded signal list for better memory capture
        signals = [
            # Personal identity
            "my name", "i am", "i'm", "call me", "you can call me",
            # Location and background  
            "i go to", "i study", "i work", "i live", "i am from", "i was born",
            # Preferences (expanded)
            "my favorite", "i like", "i love", "i hate", "i prefer", "i enjoy",
            "i don't like", "i dislike", "i'm not a fan", "not my favorite",
            # Demographics
            "language", "speak", "remember", "my birthday", "my age", "years old",
            # Lifestyle and habits
            "i usually", "i always", "i never", "i often", "i sometimes",
            "my routine", "my schedule", "i wake up", "i go to bed",
            # Relationships and social
            "my friend", "my family", "my brother", "my sister", "my parents",
            "my partner", "my boyfriend", "my girlfriend",
            # Interests and hobbies
            "i play", "i watch", "i read", "i listen", "collect", "hobby",
            "i'm interested in", "passion", "my hobby",
            # Food and dietary
            "i eat", "i cook", "vegetarian", "vegan", "diet", "allergic",
            # Long-term goals
            "my goal", "i want to become", "i want to achieve", "long term"
        ]

        return any(signal in message for signal in signals)

    async def _minimal_extraction(
        self,
        user_message: str,
        assistant_response: str,
        turn_number: int,
        extraction_boost: float
    ) -> List[Dict[str, Any]]:
        """
        Minimal extraction as a last resort for high-priority cases.
        Only extracts the most obvious and important information.
        """
        message_lower = user_message.lower()
        minimal_memories = []
        
        # Basic pattern matching for critical information
        import re
        
        patterns = [
            # Name
            (r"my name is (\w+)", "fact", "name"),
            (r"call me (\w+)", "preference", "preferred_name"),
            (r"i'm (\w+)", "fact", "stated_name"),
            
            # Work/Study
            (r"i work at ([\w\s]+)", "fact", "workplace"),
            (r"i study at ([\w\s]+)", "fact", "school"),
            (r"i go to ([\w\s]+)", "fact", "institution"),
            
            # Location
            (r"i live in ([\w\s]+)", "fact", "location"),
            (r"from ([\w\s]+)", "fact", "origin"),
            
            # Age
            (r"(\d+) years? old", "fact", "age"),
            (r"age (\d+)", "fact", "age"),
            
            # Strong preferences
            (r"i love ([\w\s]+)", "preference", "loves"),
            (r"i hate ([\w\s]+)", "preference", "hates"),
            (r"favorite ([\w\s]+) is ([\w\s]+)", "preference", lambda m: f"favorite_{m.group(1)}"),
        ]
        
        for pattern, mem_type, key in patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                for match in matches:
                    # Handle dynamic keys
                    if callable(key):
                        key = key(match)
                    elif isinstance(match, tuple):
                        key = key
                        match = match[0]
                    
                    memory = {
                        "type": mem_type,
                        "key": key,
                        "value": match.strip(),
                        "confidence": 0.8,  # High confidence for pattern matching
                        "importance": min(1.0, 0.7 + extraction_boost),  # Boost based on priority
                    }
                    minimal_memories.append(memory)
                    print(f"   🎯 Minimal extraction: [{mem_type}] {key} = {match}")
        
        return minimal_memories

