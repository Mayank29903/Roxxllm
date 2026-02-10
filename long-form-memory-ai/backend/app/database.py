from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.user import User
from app.models.chat import Conversation, Message
from app.models.memory import Memory

client = None


async def init_db():
    """Initialize MongoDB connection."""
    global client

    client = client = AsyncIOMotorClient("mongodb://localhost:27017/longform_memory_ai")


    await init_beanie(
        database=client.get_default_database(),
        document_models=[User, Conversation, Message, Memory]
    )


async def close_db():
    """Close MongoDB connection."""
    if client:
        client.close()


def get_db():
    """Get database instance."""
    return client.get_default_database()