from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, chat, memory, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    Handles database startup and shutdown.
    """
    # Startup
    await init_db()
    print("MongoDB connected")

    yield

    # Shutdown
    await close_db()
    print("MongoDB connection closed")


app = FastAPI(
    title="Long-Form Memory AI",
    description="Real-time long-form memory system for AI conversations",
    version="1.0.0",
    lifespan=lifespan
)

# Parse CORS origins from config
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(memory.router, prefix="/memory", tags=["memory"])
app.include_router(user.router, prefix="/user", tags=["user"])


@app.get("/")
async def root():
    return {
        "message": "Long-Form Memory AI API",
        "version": "1.0.0",
        "features": [
            "User Authentication",
            "Long-form Memory (1000+ turns)",
            "RAG-based Retrieval",
            "Real-time Streaming",
            "MongoDB Database"
        ]
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "mongodb"
    }