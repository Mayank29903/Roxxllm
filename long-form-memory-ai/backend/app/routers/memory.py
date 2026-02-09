from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user_dependency
from app.core.memory_store import MemoryStore

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/")
async def get_memories(
    memory_type: Optional[str] = None,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get user's stored memories."""
    store = MemoryStore()
    memories = store.get_user_memories(
        db=db,
        user_id=current_user.id,
        memory_type=memory_type
    )
    
    return [
        {
            "id": m.id,
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


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Deactivate a memory."""
    from app.models.memory import Memory
    
    memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.user_id == current_user.id
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    store = MemoryStore()
    store.deactivate_memory(db, memory_id)
    
    return {"status": "success", "message": "Memory deactivated"}