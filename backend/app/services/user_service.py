import uuid
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_user(
        self, username: str, email: str, password: str, role: str = UserRole.USER.value
    ) -> User:
        # Check if username exists
        if self.get_by_username(username):
            raise ValueError("Username already registered")

        # Check if email exists
        if self.get_by_email(email):
            raise ValueError("Email already registered")

        user = User(
            id=str(uuid.uuid4())[:8],
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def authenticate(self, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def login(self, username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        user = self.authenticate(username, password)
        if not user:
            return None, None

        if not user.is_active:
            raise ValueError("User account is disabled")

        token = create_access_token(data={"sub": user.id})
        return user, token

    def list_users(self, skip: int = 0, limit: int = 100):
        return self.db.query(User).offset(skip).limit(limit).all()

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        user = self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                if key == "password":
                    setattr(user, "hashed_password", get_password_hash(value))
                else:
                    setattr(user, key, value)

        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True
