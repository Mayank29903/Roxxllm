from beanie import Document
from pydantic import EmailStr
from datetime import datetime
from typing import Optional, List


class User(Document):
    email: EmailStr
    username: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    updated_at: Optional[datetime] = None
    
    class Settings:
        name = "users"
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True
            }
        }