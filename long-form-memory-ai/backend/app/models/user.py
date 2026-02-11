from beanie import Document
from pydantic import EmailStr
from datetime import datetime
from typing import Optional, List


class User(Document):
    email: EmailStr
    username: str
    hashed_password: Optional[str] = None  # Optional for OAuth users
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    
    # Firebase/Google authentication fields
    firebase_uid: Optional[str] = None
    auth_provider: Optional[str] = None  # 'email', 'google', 'facebook', etc.
    avatar_url: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    
    class Settings:
        name = "users"
        indexes = [
            # Email uniqueness (for traditional auth)
            [("email", 1)],  # Unique index on email
            # Firebase UID uniqueness (for OAuth)
            [("firebase_uid", 1)],  # Unique index on firebase_uid
            # Auth provider index
            [("auth_provider", 1)],
            # Combined indexes for common queries
            [("email", 1), ("auth_provider", 1)],
            [("firebase_uid", 1), ("auth_provider", 1)],
        ]
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True,
                "auth_provider": "email",
                "email_verified": True,
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }