"""
Memory Reasoner Module
Performs inference and logical deduction over stored memories to answer questions
the user hasn't explicitly answered before.

Example:
- User says: "I love Main characters in anime"
- System stores: fact[favorite_anime_character_type] = "Main character"
- User asks: "Who's your favorite character in AOT?"
- Reasoner infers: Since user loves main characters, and Eren is the main character of AOT,
  the answer should involve Eren (or the main character concept)
"""

from typing import List, Dict, Any, Optional
from app.services.llm_service import LLMService
from app.models.memory import Memory


class MemoryReasoner:
    """
    Performs semantic reasoning over memory store to infer answers to questions.
    """
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def reason_over_memories(
        self,
        user_query: str,
        memories: List[Memory],
        conversation_history: List[Dict[str, str]],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Analyze user query against memories and perform inference reasoning.
        
        Returns:
        {
            "has_direct_answer": bool,  # True if exact match found in memories
            "has_inference": bool,       # True if inference can be made
            "inference_chain": str,      # Logical reasoning explanation
            "inferred_answer": str,      # The inferred answer if possible
            "confidence": float,         # 0-1 confidence in the inference
            "sources": List[str],        # Memory sources used for inference
            "should_use": bool           # Whether system should use this inference in response
        }
        """
        
        print("\n===== MEMORY REASONING ANALYSIS =====")
        print(f"Query: {user_query}")
        print(f"Available memories: {len(memories)}")
        
        if not memories:
            print("No memories available for reasoning")
            return {
                "has_direct_answer": False,
                "has_inference": False,
                "inference_chain": "",
                "inferred_answer": "",
                "confidence": 0.0,
                "sources": [],
                "should_use": False
            }
        
        # First check if there's a direct memory match
        direct_match = self._find_direct_match(user_query, memories)
        if direct_match:
            print(f"Direct match found: {direct_match['memory'].key} = {direct_match['memory'].value}")
            return {
                "has_direct_answer": True,
                "has_inference": False,
                "inference_chain": f"Direct match in stored memories",
                "inferred_answer": str(direct_match['memory'].value),
                "confidence": 0.95,
                "sources": [f"{direct_match['memory'].memory_type}:{direct_match['memory'].key}"],
                "should_use": True
            }
        
        # Quick check: Is this query even memory-related?
        # Skip inference for general requests unrelated to the user
        if not self._is_query_memory_relevant(user_query, memories):
            print("Query not memory-related. Skipping inference reasoning.")
            return {
                "has_direct_answer": False,
                "has_inference": False,
                "inference_chain": "Query is not memory-related",
                "inferred_answer": "",
                "confidence": 0.0,
                "sources": [],
                "should_use": False
            }
        
        # If no direct match, try inference reasoning
        print("No direct match found. Attempting inference...")
        
        inference_result = await self._perform_inference(
            user_query=user_query,
            memories=memories,
            conversation_history=conversation_history
        )
        
        print(f"Inference result: confidence={inference_result['confidence']:.2f}, should_use={inference_result['should_use']}")
        print("=====================================\n")
        
        return inference_result
    
    def _find_direct_match(self, query: str, memories: List[Memory]) -> Optional[Dict[str, Any]]:
        """
        Check if query directly matches a stored memory.
        """
        query_lower = query.lower()
        
        for mem in memories:
            key_lower = str(mem.key).lower()
            # Direct key match
            if key_lower in query_lower or query_lower in key_lower:
                return {"memory": mem, "match_type": "key"}
        
        return None

    
    def _is_query_memory_relevant(self, user_query: str, memories: List[Memory]) -> bool:
        """
        Quick heuristic: Is this query asking about personal information?
        Skip reasoning for generic requests like "give me 200 movies" or "write code"
        """
        query_lower = user_query.lower()
        
        # Keywords that suggest a memory-related query
        memory_signals = [
            "my", "i", "me", "mine",
            "favorite", "like", "prefer", "love", "hate",
            "name", "age", "school", "work", "job", "hobbies",
            "character", "show", "movie", "book", "artist",
            "what.*about.*me", "tell.*about.*me", "you.*know",
            "do you remember", "remember me", "knowledge"
        ]
        
        # Check if any memory signal appears in query
        for signal in memory_signals:
            if signal in query_lower:
                return True
        
        # Also check if any memory key appears in the query
        for mem in memories[:5]:  # Check first 5 memories
            if str(mem.key).lower() in query_lower:
                return True
            # Check if memory value might be referenced
            if str(mem.value).lower() in query_lower:
                return True
        
        return False
    
    async def _perform_inference(
        self,
        user_query: str,
        memories: List[Memory],
        conversation_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Use LLM to perform inference reasoning over memories.
        """
        
        # Format memories for analysis
        memory_text = self._format_memories_for_reasoning(memories)
        
        # Build the reasoning prompt
        reasoning_prompt = self._build_reasoning_prompt(
            user_query=user_query,
            memories_text=memory_text,
            conversation_history=conversation_history
        )
        
        print(f"\nCalling LLM for inference reasoning...")
        
        try:
            # Call LLM for reasoning
            response = await self.llm_service.generate_response(
                messages=[
                    {"role": "system", "content": reasoning_prompt},
                    {"role": "user", "content": user_query}
                ],
                stream=False,
                max_tokens=500,
                temperature=0.2
            )
            
            # Process the streaming response
            full_response = ""
            async for event in response:
                if event["type"] == "token":
                    full_response += event.get("content", "")
                elif event["type"] == "final":
                    full_response += event.get("content", "")
            
            # Parse LLM reasoning response
            reasoning_analysis = self._parse_reasoning_response(
                llm_response=full_response,
                user_query=user_query
            )
            
            return reasoning_analysis
            
        except Exception as e:
            print(f"Error during LLM inference: {e}")
            return {
                "has_direct_answer": False,
                "has_inference": False,
                "inference_chain": f"Reasoning failed: {str(e)}",
                "inferred_answer": "",
                "confidence": 0.0,
                "sources": [],
                "should_use": False
            }
    
    def _format_memories_for_reasoning(self, memories: List[Memory]) -> str:
        """
        Format memories in a structured way for reasoning analysis.
        """
        lines = []
        
        # Group by type
        grouped = {}
        for mem in memories:
            if mem.memory_type not in grouped:
                grouped[mem.memory_type] = []
            grouped[mem.memory_type].append(mem)
        
        for mem_type, mems in grouped.items():
            lines.append(f"\n{mem_type.upper()}S:")
            for mem in mems:
                lines.append(f"  - {mem.key}: {mem.value} (source: turn {mem.source_turn})")
        
        return "\n".join(lines)
    
    def _build_reasoning_prompt(
        self,
        user_query: str,
        memories_text: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Build a system prompt that guides the LLM through reasoning logic.
        """
        
        # Build recent context safely
        recent_context_lines = []
        if conversation_history:
            for m in conversation_history[-3:]:
                if isinstance(m, dict) and 'role' in m and 'content' in m:
                    role = m['role'].upper()
                    content = m['content'][:100]
                    recent_context_lines.append(f"{role}: {content}")
        
        recent_context = "\n".join(recent_context_lines) if recent_context_lines else "No recent context"
        
        prompt = f"""You are an expert at logical reasoning over user preferences and facts.

Your task is to analyze whether the user's question can be INFERRED from their stored memories, even if they haven't explicitly stated the answer.

STRICT RULES:
1. ONLY infer if there is a clear logical chain from stored facts to the question
2. You MAY use common world knowledge to connect a stored preference to a specific instance
3. If a memory expresses a GENERAL preference (e.g., favorite character type), apply it to general queries about favorites
4. If the user asks about a specific series/film, map the general preference to that series using common knowledge
5. DO NOT make assumptions or fill in gaps that aren't supported by memories or common knowledge
6. If uncertain, explicitly say you cannot make a confident inference
7. Be specific about WHY you can or cannot make the inference

USER'S STORED MEMORIES:
{memories_text}

RECENT CONVERSATION CONTEXT:
{recent_context}

USER'S QUESTION:
{user_query}

EXAMPLE:
- Memory: preference favorite_anime_character_type = "main character"
- Question: "Who is my favorite character in Black Clover?"
- Inference: The user prefers main characters; the main character of Black Clover is Asta.

Now analyze:
1. Can you find the DIRECT ANSWER in memories? (Yes/No)
2. If not, can you INFER the answer from logical relationships between memories? (Yes/No)
3. What is the REASONING CHAIN? (Step by step logic)
4. What is your CONFIDENCE LEVEL? (0-1)
5. What is the INFERRED ANSWER if applicable?
6. Which MEMORY SOURCES support this inference?

Format your response as:
DIRECT_ANSWER: [yes/no]
INFERENCE_POSSIBLE: [yes/no]
REASONING_CHAIN: [explanation]
CONFIDENCE: [0.0-1.0]
INFERRED_ANSWER: [answer or "N/A"]
SOURCES: [list of memory keys used]
EXPLANATION: [brief explanation of why or why not]"""
        
        return prompt
    
    def _parse_reasoning_response(
        self,
        llm_response: str,
        user_query: str
    ) -> Dict[str, Any]:
        """
        Parse the LLM's reasoning response into structured data.
        """
        
        # Extract fields from the response
        result = {
            "has_direct_answer": False,
            "has_inference": False,
            "inference_chain": "",
            "inferred_answer": "",
            "confidence": 0.0,
            "sources": [],
            "should_use": False
        }
        
        lines = llm_response.split('\n')
        
        try:
            for line in lines:
                line = line.strip()
                
                if line.startswith("DIRECT_ANSWER:"):
                    result["has_direct_answer"] = "yes" in line.lower()
                
                elif line.startswith("INFERENCE_POSSIBLE:"):
                    result["has_inference"] = "yes" in line.lower()
                
                elif line.startswith("REASONING_CHAIN:"):
                    result["inference_chain"] = line.replace("REASONING_CHAIN:", "").strip()
                
                elif line.startswith("CONFIDENCE:"):
                    try:
                        conf_str = line.replace("CONFIDENCE:", "").strip()
                        result["confidence"] = float(conf_str)
                    except ValueError:
                        result["confidence"] = 0.0
                
                elif line.startswith("INFERRED_ANSWER:"):
                    answer = line.replace("INFERRED_ANSWER:", "").strip()
                    if answer.lower() != "n/a":
                        result["inferred_answer"] = answer
                
                elif line.startswith("SOURCES:"):
                    sources_str = line.replace("SOURCES:", "").strip()
                    result["sources"] = [s.strip() for s in sources_str.split(',') if s.strip()]
                
                elif line.startswith("EXPLANATION:"):
                    # Could store this for debugging
                    pass
            
            # Determine if we should use this inference
            # Only use if:
            # 1. We have an inference (not direct answer) OR we have direct answer
            # 2. Confidence is reasonably high (>= 0.6)
            # 3. We have sources to support it
            if result["inferred_answer"] and result["confidence"] >= 0.6:
                result["should_use"] = True
            elif result["has_direct_answer"]:
                result["should_use"] = True
        
        except Exception as e:
            print(f"Error parsing reasoning response: {e}")
        
        return result
