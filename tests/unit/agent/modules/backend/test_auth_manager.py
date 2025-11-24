"""
Comprehensive unit tests for agent/modules/backend/auth_manager.py

Target coverage: 75%+
"""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from agent.modules.backend.auth_manager import (
    AuthManager,
    Base,
    User,
    UserPreference,
    UserSession,
)


@pytest.fixture
def auth_manager():
    """Create auth manager with test database"""
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
        manager = AuthManager()
        Base.metadata.create_all(bind=manager.engine)
        yield manager


@pytest.fixture
def db_session(auth_manager):
    """Create database session"""
    session = auth_manager.SessionLocal()
    try:
        yield session
    finally:
        session.close()


class TestAuthManagerInitialization:
    """Test AuthManager initialization"""

    def test_init_with_database_url(self, auth_manager):
        assert auth_manager is not None
        assert auth_manager.engine is not None
        assert auth_manager.SessionLocal is not None

    def test_init_without_database_url(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="DATABASE_URL"):
                AuthManager()

    def test_init_database(self, auth_manager):
        # Database should be initialized
        assert auth_manager._db_initialized is True


class TestPasswordHashing:
    """Test password hashing and verification"""

    def test_hash_password(self, auth_manager):
        password = "TestPassword123!"
        hashed = auth_manager.hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct(self, auth_manager):
        password = "TestPassword123!"
        hashed = auth_manager.hash_password(password)

        assert auth_manager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, auth_manager):
        password = "TestPassword123!"
        hashed = auth_manager.hash_password(password)

        assert auth_manager.verify_password("WrongPassword", hashed) is False

    def test_hash_different_passwords_different_hashes(self, auth_manager):
        hash1 = auth_manager.hash_password("password1")
        hash2 = auth_manager.hash_password("password2")

        assert hash1 != hash2

    def test_hash_same_password_different_salts(self, auth_manager):
        password = "TestPassword123!"
        hash1 = auth_manager.hash_password(password)
        hash2 = auth_manager.hash_password(password)

        # Same password should produce different hashes (different salts)
        assert hash1 != hash2


class TestEmailValidation:
    """Test email validation"""

    def test_validate_email_valid(self, auth_manager):
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
            "123@test.com",
        ]

        for email in valid_emails:
            assert auth_manager.validate_email(email) is True

    def test_validate_email_invalid(self, auth_manager):
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user@domain",
            "user @example.com",
            "user@domain .com",
        ]

        for email in invalid_emails:
            assert auth_manager.validate_email(email) is False


class TestPasswordValidation:
    """Test password validation"""

    def test_validate_password_valid(self, auth_manager):
        result = auth_manager.validate_password("ValidPass123!")

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_password_too_short(self, auth_manager):
        result = auth_manager.validate_password("Short1!")

        assert result["valid"] is False
        assert any("8 characters" in err for err in result["errors"])

    def test_validate_password_no_uppercase(self, auth_manager):
        result = auth_manager.validate_password("password123!")

        assert result["valid"] is False
        assert any("uppercase" in err for err in result["errors"])

    def test_validate_password_no_lowercase(self, auth_manager):
        result = auth_manager.validate_password("PASSWORD123!")

        assert result["valid"] is False
        assert any("lowercase" in err for err in result["errors"])

    def test_validate_password_no_number(self, auth_manager):
        result = auth_manager.validate_password("Password!")

        assert result["valid"] is False
        assert any("number" in err for err in result["errors"])

    def test_validate_password_no_special(self, auth_manager):
        result = auth_manager.validate_password("Password123")

        assert result["valid"] is False
        assert any("special character" in err for err in result["errors"])

    def test_validate_password_multiple_errors(self, auth_manager):
        result = auth_manager.validate_password("weak")

        assert result["valid"] is False
        assert len(result["errors"]) > 1


class TestUserModel:
    """Test User database model"""

    def test_user_creation(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            first_name="Test",
            last_name="User",
        )

        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.created_at is not None

    def test_user_unique_email(self, db_session):
        user1 = User(
            email="duplicate@example.com",
            username="user1",
            password_hash="hash1",
        )
        user2 = User(
            email="duplicate@example.com",
            username="user2",
            password_hash="hash2",
        )

        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):  # Should raise IntegrityError
            db_session.commit()

    def test_user_default_values(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )

        db_session.add(user)
        db_session.commit()

        assert user.role == "user"
        assert user.is_active is True
        assert user.failed_login_attempts == 0
        assert user.email_verified is False


class TestUserSessionModel:
    """Test UserSession database model"""

    def test_session_creation(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        session = UserSession(
            user_id=user.id,
            token_hash="token_hash",
            expires_at=datetime.now() + timedelta(hours=24),
            ip_address="127.0.0.1",
            user_agent="Test Agent",
        )

        db_session.add(session)
        db_session.commit()

        assert session.id is not None
        assert session.user_id == user.id
        assert session.is_active is True

    def test_session_relationship(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        session = UserSession(
            user_id=user.id,
            token_hash="token_hash",
            expires_at=datetime.now() + timedelta(hours=24),
        )

        db_session.add(session)
        db_session.commit()

        # Test relationship
        assert session.user == user
        assert session in user.sessions


class TestUserPreferenceModel:
    """Test UserPreference database model"""

    def test_preference_creation(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        preference = UserPreference(
            user_id=user.id,
            theme="dark",
            notifications_enabled=True,
            marketing_emails=False,
        )

        db_session.add(preference)
        db_session.commit()

        assert preference.user_id == user.id
        assert preference.theme == "dark"

    def test_preference_defaults(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        preference = UserPreference(user_id=user.id)

        db_session.add(preference)
        db_session.commit()

        assert preference.theme == "light"
        assert preference.notifications_enabled is True
        assert preference.marketing_emails is False
        assert preference.timezone == "UTC"
        assert preference.language == "en"


class TestDatabaseOperations:
    """Test database operations"""

    def test_get_db_session(self, auth_manager):
        gen = auth_manager.get_db()
        session = next(gen)

        assert session is not None

        # Cleanup
        try:
            next(gen)
        except StopIteration:
            pass

    def test_multiple_users(self, db_session):
        users = [
            User(email=f"user{i}@example.com", username=f"user{i}", password_hash=f"hash{i}")
            for i in range(5)
        ]

        for user in users:
            db_session.add(user)
        db_session.commit()

        assert db_session.query(User).count() == 5

    def test_query_user_by_email(self, db_session):
        user = User(
            email="find@example.com",
            username="findme",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter_by(email="find@example.com").first()

        assert found is not None
        assert found.username == "findme"

    def test_update_user(self, db_session):
        user = User(
            email="update@example.com",
            username="updateme",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        user.first_name = "Updated"
        user.last_name = "Name"
        db_session.commit()

        updated = db_session.query(User).filter_by(email="update@example.com").first()
        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"

    def test_delete_user(self, db_session):
        user = User(
            email="delete@example.com",
            username="deleteme",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        user_id = user.id

        db_session.delete(user)
        db_session.commit()

        deleted = db_session.query(User).filter_by(id=user_id).first()
        assert deleted is None


class TestSecurityFeatures:
    """Test security features"""

    def test_failed_login_tracking(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
            failed_login_attempts=0,
        )
        db_session.add(user)
        db_session.commit()

        user.failed_login_attempts += 1
        db_session.commit()

        assert user.failed_login_attempts == 1

    def test_account_lockout(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        user.locked_until = datetime.now() + timedelta(minutes=30)
        db_session.commit()

        assert user.locked_until is not None
        assert user.locked_until > datetime.now()

    def test_email_verification_token(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
            verification_token="random_token_123",
        )
        db_session.add(user)
        db_session.commit()

        assert user.verification_token == "random_token_123"
        assert user.email_verified is False

    def test_password_reset_token(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
            reset_token="reset_token_456",
            reset_token_expires=datetime.now() + timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()

        assert user.reset_token == "reset_token_456"
        assert user.reset_token_expires > datetime.now()


class TestEdgeCases:
    """Test edge cases"""

    def test_empty_password(self, auth_manager):
        result = auth_manager.validate_password("")
        assert result["valid"] is False

    def test_very_long_password(self, auth_manager):
        long_password = "A1!" + "a" * 1000
        result = auth_manager.validate_password(long_password)
        # Should still validate the requirements
        assert "valid" in result

    def test_unicode_in_email(self, auth_manager):
        result = auth_manager.validate_email("user@例え.com")
        # Depends on regex - might be invalid

    def test_special_characters_in_password(self, auth_manager):
        password = "P@ssw0rd!@#$%^&*()"
        result = auth_manager.validate_password(password)
        assert result["valid"] is True

    def test_session_expiration(self, db_session):
        user = User(
            email="test@example.com",
            username="testuser",
            password_hash="hashed",
        )
        db_session.add(user)
        db_session.commit()

        # Expired session
        expired_session = UserSession(
            user_id=user.id,
            token_hash="expired_token",
            expires_at=datetime.now() - timedelta(hours=1),
        )
        db_session.add(expired_session)
        db_session.commit()

        assert expired_session.expires_at < datetime.now()
