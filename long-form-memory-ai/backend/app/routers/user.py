from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User
from app.models.memory import Memory
from app.models.chat import Conversation, Message
from app.routers.auth import get_current_user_dependency

router = APIRouter(prefix="/user", tags=["user"])

@router.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(current_user: User = Depends(get_current_user_dependency)):
    user_id = str(current_user.id)
    # Delete all memories
    await Memory.find(Memory.user_id == user_id).delete()
    # Delete all conversations
    await Conversation.find(Conversation.user_id == user_id).delete()
    # Delete all messages in those conversations
    await Message.find({"conversation_id": {"$in": [c.id async for c in Conversation.find(Conversation.user_id == user_id)]}}).delete()
    # Delete user
    await current_user.delete()
    return None
