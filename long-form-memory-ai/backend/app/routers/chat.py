from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, AsyncGenerator
import json
import asyncio

from app.database import get_db
from app.models.user import User
from app.routers.auth import get_current_user_dependency
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


class MessageCreate(BaseModel):
    content: str
    conversation_id: Optional[int] = None
    stream: bool = False


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    turn_number: int
    created_at: str
    active_memories: Optional[List[str]] = None


@router.post("/conversations")
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conv = await chat_service.create_conversation(
        db=db,
        user_id=current_user.id,
        title=data.title
    )
    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "turn_count": conv.turn_count
    }


@router.get("/conversations")
async def list_conversations(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """List user's conversations."""
    from app.models.chat import Conversation
    
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "title": c.title,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "turn_count": c.turn_count
        }
        for c in conversations
    ]


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """Get conversation messages."""
    messages = await chat_service.get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        limit=limit
    )
    return messages


@router.post("/send")
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Send a message and get response."""
    
    # Create conversation if not provided
    if not data.conversation_id:
        conv = await chat_service.create_conversation(db, current_user.id)
        data.conversation_id = conv.id
    
    if data.stream:
        async def event_generator() -> AsyncGenerator[str, None]:
            async for event in chat_service.process_message(
                db=db,
                user_id=current_user.id,
                conversation_id=data.conversation_id,
                content=data.content,
                stream=True
            ):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
    else:
        result = None
        async for event in chat_service.process_message(
            db=db,
            user_id=current_user.id,
            conversation_id=data.conversation_id,
            content=data.content,
            stream=False
        ):
            result = event
        
        return result