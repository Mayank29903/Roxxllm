from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, chat, memory


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Long-Form Memory AI...")
    await init_db()
    print("MongoDB connected!")
    yield
    # Shutdown
    print("Shutting down...")
    await close_db()


app = FastAPI(
    title="Long-Form Memory AI",
    description="Real-time long-form memory system for AI conversations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(memory.router)


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
    return {"status": "healthy", "database": "mongodb"}