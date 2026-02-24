import pytest
from sqlalchemy.orm import Session

from app.core.auth import get_password_hash, verify_password
from app.core.database import Base, SessionLocal, engine
from app.models.user import User, UserRole
from app.services.user_service import UserService


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestAuthentication:
    """Test user authentication flow."""

    def test_password_hash_and_verify(self):
        """Test password hashing and verification."""
        password = "test_password_123"
        hashed = get_password_hash(password)

        # Hash should be different from plain password
        assert hashed != password

        # Verify should return True for correct password
        assert verify_password(password, hashed) is True

        # Verify should return False for incorrect password
        assert verify_password("wrong_password", hashed) is False

    def test_password_hash_with_unicode(self):
        """Test password hashing with unicode characters."""
        password = "密码123@#$%^"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_password_hash_with_long_password(self):
        """Test password hashing with long password (>72 bytes)."""
        password = "a" * 100
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_create_user(self, db: Session):
        """Test user creation."""
        user_service = UserService(db)

        user = user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.USER.value
        assert user.is_active is True
        assert user.hashed_password != "password123"

    def test_create_duplicate_username(self, db: Session):
        """Test creating user with duplicate username."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser", email="test1@example.com", password="password123"
        )

        with pytest.raises(ValueError, match="Username already registered"):
            user_service.create_user(
                username="testuser", email="test2@example.com", password="password456"
            )

    def test_create_duplicate_email(self, db: Session):
        """Test creating user with duplicate email."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser1", email="test@example.com", password="password123"
        )

        with pytest.raises(ValueError, match="Email already registered"):
            user_service.create_user(
                username="testuser2", email="test@example.com", password="password456"
            )

    def test_authenticate_success(self, db: Session):
        """Test successful authentication."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        authenticated = user_service.authenticate("testuser", "password123")

        assert authenticated is not None
        assert authenticated.username == "testuser"

    def test_authenticate_wrong_password(self, db: Session):
        """Test authentication with wrong password."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        authenticated = user_service.authenticate("testuser", "wrongpassword")

        assert authenticated is None

    def test_authenticate_nonexistent_user(self, db: Session):
        """Test authentication with non-existent user."""
        user_service = UserService(db)

        authenticated = user_service.authenticate("nonexistent", "password")

        assert authenticated is None

    def test_login_success(self, db: Session):
        """Test successful login."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        user, token = user_service.login("testuser", "password123")

        assert user is not None
        assert token is not None
        assert user.username == "testuser"
        assert isinstance(token, str)
        assert len(token) > 0

    def test_login_wrong_password(self, db: Session):
        """Test login with wrong password."""
        user_service = UserService(db)

        user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        user, token = user_service.login("testuser", "wrongpassword")

        assert user is None
        assert token is None

    def test_login_inactive_user(self, db: Session):
        """Test login with inactive user."""
        user_service = UserService(db)

        user = user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Deactivate user
        user.is_active = False
        db.commit()

        with pytest.raises(ValueError, match="User account is disabled"):
            user_service.login("testuser", "password123")

    def test_register_and_login_flow(self, db: Session):
        """Test complete register and login flow."""
        user_service = UserService(db)

        # Register
        user = user_service.create_user(
            username="testuser", email="test@example.com", password="password123"
        )

        # Login immediately after registration
        logged_in_user, token = user_service.login("testuser", "password123")

        assert logged_in_user is not None
        assert token is not None
        assert logged_in_user.id == user.id
        assert logged_in_user.username == user.username
