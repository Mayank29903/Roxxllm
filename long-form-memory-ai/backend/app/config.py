from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LongFormMemoryAI"
    DEBUG: bool = False
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017/memory_ai"
    
    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # LLM Configuration
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Memory Configuration
    MAX_CONTEXT_TURNS: int = 10
    MEMORY_TOP_K: int = 5
    MEMORY_CONFIDENCE_THRESHOLD: float = 0.7
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()