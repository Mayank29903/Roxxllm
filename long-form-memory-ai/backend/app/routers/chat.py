from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import json

from app.models.user import User
from app.routers.auth import get_current_user_dependency
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()


class MessageCreate(BaseModel):
    content: str
    conversation_id: Optional[str] = None
    stream: bool = False


class ConversationCreate(BaseModel):
    title: Optional[str] = None


@router.post("/conversations")
async def create_conversation(
    data: ConversationCreate,
    current_user: User = Depends(get_current_user_dependency),
):
    conv = await chat_service.create_conversation(
        user_id=str(current_user.id),
        title=data.title
    )
    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "turn_count": conv.turn_count
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user_dependency),
    limit: int = 100
):
    return await chat_service.get_conversation_history(
        conversation_id=conversation_id,
        user_id=str(current_user.id),
        limit=limit
    )


@router.post("/send")
async def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user_dependency),
):
    if not data.conversation_id:
        conv = await chat_service.create_conversation(str(current_user.id))
        data.conversation_id = str(conv.id)

    if data.stream:
        async def event_gen() -> AsyncGenerator[str, None]:
            async for event in chat_service.process_message(
                user_id=str(current_user.id),
                conversation_id=data.conversation_id,
                content=data.content,
                stream=True
            ):
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_gen(), media_type="text/event-stream")

    else:
        result = None
        async for event in chat_service.process_message(
            user_id=str(current_user.id),
            conversation_id=data.conversation_id,
            content=data.content,
            stream=False
        ):
            result = event
        return result
