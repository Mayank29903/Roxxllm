from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LongFormMemoryAI"
    DEBUG: bool = False

    # MongoDB
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017/longform_memory_ai",
        alias="MONGODB_URL"
    )

    # Redis (optional)
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL"
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # ===== LLM CONFIGURATION =====
    LLM_PROVIDER: str = Field(default="openrouter")

    OPENROUTER_API_KEY: str = Field(default="", alias="OPENROUTER_API_KEY")

    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # OpenRouter model name
    LLM_MODEL: str = "openai/gpt-4o-mini"

    # Gemini (direct API)
    GEMINI_API_KEY: str = Field(default="", alias="GEMINI_API_KEY")
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta"
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Memory Configuration
    MAX_CONTEXT_TURNS: int = 10
    MEMORY_TOP_K: int = 5
    MEMORY_CONFIDENCE_THRESHOLD: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        populate_by_name=True,
        extra="ignore"
    )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
