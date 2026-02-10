# Long-Form Memory System

## Overview
The AI now remembers information from **all previous conversations**, not just the current one. This allows for true long-term memory across conversation sessions.

## How It Works

### 1. Memory Extraction
The system automatically extracts important information from conversations at strategic points:
- **Turn 1**: Captures initial preferences and context
- **Every 5 turns**: Regular memory extraction
- **Every 50 turns**: Comprehensive memory review

### 2. Memory Types
The system categorizes memories into 6 types:
- **preference**: User likes, dislikes, choices (e.g., language preference, communication style)
- **fact**: Personal information, demographics, important facts
- **entity**: Important people, places, organizations mentioned
- **commitment**: Promises, scheduled events, deadlines
- **instruction**: Explicit instructions on how to behave or respond
- **constraint**: Limitations, restrictions, boundaries

### 3. Memory Storage
Memories are stored with:
- `user_id`: Links memory to the user (not a specific conversation)
- `importance_score`: 0.0 to 1.0, higher is more important
- `confidence`: 0.0 to 1.0, how confident we are about this memory
- `source_conversation_id`: Which conversation it came from
- `access_count`: How many times it has been used
- `last_accessed_turn`: When it was last used

### 4. Memory Retrieval
When processing any message:
1. System retrieves the **top 20 most important memories** for the user
2. Memories are sorted by **importance_score** (highest first)
3. Memories from **ALL conversations** are considered, not just the current one
4. These memories are injected as a system message before the conversation

### 5. Cross-Conversation Memory
**This is the key feature**: When you switch to a new conversation in the sidebar, the AI can still access memories from your previous conversations because:
- Memories are stored at the **user level**, not conversation level
- The AI receives relevant memories regardless of which conversation is active
- The memory context is injected before every response

## Example Scenario

### Conversation 1:
```
User: "I prefer to communicate in Kannada"
AI: "Got it! I'll remember that you prefer Kannada."
[Memory extracted: type=preference, key=language, value=Kannada, importance=0.8]
```

### Conversation 2 (New conversation in sidebar):
```
User: "Hello, can you help me with something?"
AI: "Namaskara! Of course, I'd be happy to help!" 
[The AI responds in Kannada because it retrieved the memory from Conversation 1]
```

## Technical Implementation

### Code Changes Made:
1. **memory_service.py**: 
   - Added sorting by `importance_score` in descending order
   - Ensures most important memories are retrieved first

2. **chat_service.py**:
   - Increased memory limit from 10 to 20 memories
   - Added memory access tracking
   - Clarified that memories come from ALL conversations

### Memory Injection:
```python
# Memories are formatted and injected as a system message
system_message = {
    "role": "system", 
    "content": "You have access to the following information from previous conversations with this user:\n"
               "- [PREFERENCE] language: Kannada\n"
               "- [FACT] name: John\n"
               "Use this information naturally when relevant."
}
```

## Debugging

To verify the memory system is working:
1. Check backend logs for "===== ACTIVE MEMORIES =====" sections
2. Look for "===== EXTRACTED X MEMORIES =====" after strategic turns
3. Verify memories are being stored in MongoDB `memories` collection
4. Confirm `active_memories` field in messages contains memory IDs

## Future Improvements

Potential enhancements:
1. **Semantic Search**: Use vector embeddings to find relevant memories based on query similarity
2. **Memory Decay**: Reduce importance of old, unused memories over time
3. **Conflict Resolution**: Handle contradicting memories (e.g., user changed preferences)
4. **Memory Summarization**: Compress memories when reaching storage limits
5. **Explicit Memory Management**: Allow users to view/edit/delete their memories
