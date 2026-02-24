from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.auth import get_admin_user, get_current_user, get_current_user_required
from app.core.database import get_db
from app.models.user import User
from app.services.user_service import UserService

router = APIRouter()


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


@router.post("/register", response_model=LoginResponse, tags=["Auth"])
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    user_service = UserService(db)

    try:
        user = user_service.create_user(
            username=data.username, email=data.email, password=data.password
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    _, access_token = user_service.login(data.username, data.password)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.post("/login", response_model=LoginResponse, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username and password"""
    user_service = UserService(db)

    try:
        user, token = user_service.login(form_data.username, form_data.password)
    except ValueError as e:
        raise HTTPException(403, str(e))

    if not user or not token:
        raise HTTPException(401, "Incorrect username or password")

    return LoginResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
    )


@router.get("/me", response_model=UserResponse, tags=["Auth"])
async def get_me(user: User = Depends(get_current_user_required)):
    """Get current user info"""
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )


@router.put("/me", response_model=UserResponse, tags=["Auth"])
async def update_me(
    data: UserUpdate, user: User = Depends(get_current_user_required), db: Session = Depends(get_db)
):
    """Update current user info"""
    user_service = UserService(db)

    update_data = data.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(400, "No data to update")

    updated_user = user_service.update_user(user.id, **update_data)

    return UserResponse(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        role=updated_user.role,
        is_active=updated_user.is_active,
    )


@router.get("/users", tags=["Auth"])
async def list_users(user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """List all users (admin only)"""
    user_service = UserService(db)
    users = user_service.list_users()

    return {
        "code": 200,
        "data": {
            "items": [
                UserResponse(
                    id=u.id, username=u.username, email=u.email, role=u.role, is_active=u.is_active
                ).dict()
                for u in users
            ]
        },
    }
