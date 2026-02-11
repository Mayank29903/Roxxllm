
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime
from typing import Optional

from app.models.user import User
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user
)
from app.config import settings
from app.services.firebase_service import firebase_service
from fastapi import HTTPException

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str


class GoogleAuthRequest(BaseModel):
    id_token: str
    access_token: Optional[str] = None
    user_info: dict


class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    user: UserResponse


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    if await User.find_one(User.email == user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await User.find_one(User.username == user_data.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    await user.insert()

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username
        }
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(token: str = Depends(oauth2_scheme)):
    user = await get_current_user(token)
    return {
        "id": str(user.id),
        "email": user.email,
        "username": user.username
    }


@router.post("/google", response_model=Token)
async def login_with_google(google_data: GoogleAuthRequest):
    """Authenticate with Google using Firebase ID token."""
    
    try:
        # Verify Firebase ID token
        firebase_user = await firebase_service.verify_id_token(google_data.id_token)
        
        # Create or update user
        user = await firebase_service.create_or_update_user(
            firebase_user=firebase_user,
            user_info=google_data.user_info
        )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Google authentication error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Google authentication failed"
        )


async def get_current_user_dependency(
    token: str = Depends(oauth2_scheme),
) -> User:
    return await get_current_user(token)