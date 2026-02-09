from fastapi import APIRouter, Depends
from typing import Optional

from app.models.user import User
from app.models.memory import Memory
from app.routers.auth import get_current_user_dependency

router = APIRouter(prefix="/memory", tags=["memory"])


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
