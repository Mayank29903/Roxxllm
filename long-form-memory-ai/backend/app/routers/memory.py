
from fastapi import APIRouter, Depends, Body
from typing import Optional

from app.models.user import User
from app.models.memory import Memory
from app.routers.auth import get_current_user_dependency
from app.utils.memory_tester import MemoryTester
from app.core.memory_extractor import MemoryExtractor

router = APIRouter(tags=["memory"])


@router.get("/")
async def get_memories(
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
):
    query = Memory.find(
        Memory.user_id == str(current_user.id),
        Memory.is_active == True
    )

    if memory_type:
        query = query.find(Memory.memory_type == memory_type)

    memories = await query.to_list()

    return [
        {
            "id": str(m.id),
            "type": m.memory_type,
            "key": m.key,
            "value": m.value,
            "confidence": m.confidence,
            "importance": m.importance_score,
            "source_turn": m.source_turn,
            "access_count": m.access_count,
            "created_at": m.created_at.isoformat()
        }
        for m in memories
    ]


@router.post("/test")
async def test_memory_system(
    current_user: User = Depends(get_current_user_dependency),
):
    """
    Test the memory system to ensure it's working correctly.
    Creates test memories and verifies time-based retrieval.
    """
    try:
        tester = MemoryTester()
        results = await tester.run_full_test_suite(str(current_user.id))
        return {
            "success": True,
            "results": results,
            "message": results.get("summary", "Test completed")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Memory test failed"
        }


@router.get("/debug")
async def debug_memory_retrieval(
    hours_ago: Optional[int] = None,
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
):
    """
    Debug endpoint to inspect what memories are being retrieved.
    Useful for troubleshooting memory issues.
    """
    try:
        from app.services.memory_service import MemoryService
        from datetime import datetime
        
        memory_service = MemoryService()
        user_id = str(current_user.id)
        
        # Get different sets of memories
        all_memories = await memory_service.get_user_memories(
            user_id=user_id,
            limit=20,
            sort_by="time_created"
        )
        
        filtered_memories = []
        if hours_ago is not None:
            filtered_memories = await memory_service.get_user_memories(
                user_id=user_id,
                limit=20,
                hours_ago=hours_ago,
                sort_by="time_created"
            )
        
        # Format memories for display
        def format_memory(mem):
            hours_old = (datetime.utcnow() - mem.created_at).total_seconds() / 3600
            return {
                "id": str(mem.id),
                "type": mem.memory_type,
                "key": mem.key,
                "value": mem.value,
                "hours_old": round(hours_old, 1),
                "importance": mem.importance_score,
                "confidence": mem.confidence,
                "access_count": mem.access_count,
                "created_at": mem.created_at.isoformat()
            }
        
        return {
            "user_id": user_id,
            "total_active_memories": len(all_memories),
            "filtered_memories": {
                "hours_ago": hours_ago,
                "count": len(filtered_memories),
                "memories": [format_memory(m) for m in filtered_memories]
            },
            "recent_memories": [format_memory(m) for m in all_memories[:10]],
            "message": "Debug information retrieved successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Debug failed"
        }


@router.post("/test-extraction")
async def test_memory_extraction(
    message: str = Body(..., embed=True),
    turn_number: int = Body(1, embed=True),
    current_user: User = Depends(get_current_user_dependency),
):
    """
    Test memory extraction on a specific message to see what would be extracted.
    Useful for understanding why memories are/aren't being stored.
    """
    try:
        extractor = MemoryExtractor()
        
        # Test extraction decision
        decision = extractor.should_extract(turn_number, message)
        
        result = {
            "message": message,
            "turn_number": turn_number,
            "extraction_decision": decision,
            "extraction_signals": []
        }
        
        # Show what signals were detected
        message_lower = message.lower()
        
        # Check explicit commands
        explicit_commands = ["remember", "don't forget", "this is important", "make a note", "keep in mind"]
        if any(cmd in message_lower for cmd in explicit_commands):
            result["extraction_signals"].append({
                "type": "explicit_command",
                "detected": [cmd for cmd in explicit_commands if cmd in message_lower],
                "priority": "critical"
            })
        
        # Check importance signals
        importance_signals = [
            "my name", "i am", "i'm", "call me", "you can call me",
            "i work at", "i study at", "i go to", "i live in", "i am from"
        ]
        detected_importance = [sig for sig in importance_signals if sig in message_lower]
        if detected_importance:
            result["extraction_signals"].append({
                "type": "importance_signal",
                "detected": detected_importance,
                "priority": "high"
            })
        
        # Check regular signals
        regular_signals = [
            "my favorite", "i like", "i love", "i hate", "i prefer", "i enjoy",
            "my routine", "i usually", "i always", "i never", "i often", "i sometimes"
        ]
        detected_regular = [sig for sig in regular_signals if sig in message_lower]
        if detected_regular:
            result["extraction_signals"].append({
                "type": "regular_signal", 
                "detected": detected_regular,
                "priority": "medium"
            })
        
        # Check fallback conditions
        words = message.split()
        if len(words) >= 20 and any(pronoun in message_lower for pronoun in ["i", "my", "me", "mine"]):
            result["extraction_signals"].append({
                "type": "fallback_heuristic",
                "detected": f"Long message ({len(words)} words) with personal pronouns",
                "priority": "fallback"
            })
        
        # Actually extract memories if should extract
        if decision["should_extract"]:
            try:
                extracted = await extractor.extract_memories(
                    user_message=message,
                    assistant_response="Test response for extraction testing",
                    turn_number=turn_number,
                    extraction_boost=decision.get("extraction_boost", 0.0)
                )
                result["extracted_memories"] = extracted
                result["extraction_success"] = True
            except Exception as e:
                result["extraction_success"] = False
                result["extraction_error"] = str(e)
        else:
            result["extracted_memories"] = []
            result["extraction_success"] = False
        
        return {
            "success": True,
            "result": result,
            "summary": f"Extraction: {'YES' if decision['should_extract'] else 'NO'} (Priority: {decision['priority']})"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Extraction test failed"
        }
