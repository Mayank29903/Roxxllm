import openai
from typing import List, Dict, Any, AsyncGenerator
from app.config import settings


class LLMService:
    """Handles LLM interactions with memory injection."""
    
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        memory_context: str = "",
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """Generate response with optional memory context."""
        
        # Build system prompt with memory
        system_content = """You are a helpful AI assistant with long-term memory. 
Use the provided context from previous conversations naturally without explicitly mentioning it unless necessary.
Be concise, helpful, and maintain continuity with previous interactions."""

        if memory_context:
            system_content += f"\n\n{memory_context}"
        
        # Prepare messages
        api_messages = [{"role": "system", "content": system_content}]
        api_messages.extend(messages)
        
        if stream:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=api_messages,
                stream=True,
                temperature=0.7,
                max_tokens=1000
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        else:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1000
            )
            yield response.choices[0].message.content
    
    def build_conversation_messages(
        self,
        recent_history: List[Dict],
        current_message: str,
        max_turns: int = None
    ) -> List[Dict[str, str]]:
        """Build message list from history."""
        if max_turns is None:
            max_turns = settings.MAX_CONTEXT_TURNS
        
        messages = []
        
        # Add recent history (limited to prevent token overflow)
        for msg in recent_history[-max_turns:]:
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # Add current message
        messages.append({"role": "user", "content": current_message})
        
        return messages