from datetime import datetime, timedelta
import logging
import os
import re
import secrets
from typing import Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func


logger = logging.getLogger(__name__)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True))
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String)
    reset_token = Column(String)
    reset_token_expires = Column(DateTime(timezone=True))

    sessions = relationship("UserSession", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token_hash = Column(String, unique=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String)
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="sessions")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    theme = Column(String, default="light")
    notifications_enabled = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)
    dashboard_layout = Column(String, default="default")
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")

    user = relationship("User", back_populates="preferences")


class AuthManager:
    """Comprehensive authentication and user management system."""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(64))
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable must be set for security")
        self.security = HTTPBearer()
        self.engine = None
        self.SessionLocal = None
        # Delay database initialization until needed
        try:
            self.init_database()
        except Exception as e:
            logger.warning(f"Database initialization failed, will retry when needed: {e!s}")
            self._db_initialized = False

    def init_database(self):
        """Initialize PostgreSQL database with secure schema."""
        try:
            if not self.engine:
                self.engine = create_engine(self.database_url)
                self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            self._db_initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize database: {e!s}")
            self._db_initialized = False
            raise

    def get_db(self):
        """Get database session."""
        if not self._db_initialized:
            self.init_database()
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(pattern, email) is not None

    def validate_password(self, password: str) -> dict[str, Any]:
        """Validate password strength."""
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", password):
            errors.append("Password must contain at least one number")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return {"valid": len(errors) == 0, "errors": errors}

    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> dict[str, Any]:
        """Create new user account with validation."""

        # Validate input
        if not self.validate_email(email):
            return {"success": False, "error": "Invalid email format"}

        password_validation = self.validate_password(password)
        if not password_validation["valid"]:
            return {"success": False, "error": password_validation["errors"]}

        db = self.SessionLocal()

        try:
            # Check if user already exists
            existing_user = db.query(User).filter((User.email == email) | (User.username == username)).first()

            if existing_user:
                return {
                    "success": False,
                    "error": "User with this email or username already exists",
                }

            # Hash password and create user
            password_hash = self.hash_password(password)
            verification_token = secrets.token_urlsafe(32)

            new_user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                verification_token=verification_token,
            )

            db.add(new_user)
            db.flush()  # Get user ID

            # Create default preferences
            user_prefs = UserPreference(user_id=new_user.id)
            db.add(user_prefs)

            db.commit()

            return {
                "success": True,
                "user_id": new_user.id,
                "message": "User created successfully",
                "verification_token": verification_token,
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e!s}")
            return {"success": False, "error": "Failed to create user"}
        finally:
            db.close()

    def authenticate_user(
        self, email: str, password: str, ip_address: str = "", user_agent: str = ""
    ) -> dict[str, Any]:
        """Authenticate user and create session."""

        db = self.SessionLocal()

        try:
            # Get user data
            user = db.query(User).filter(User.email == email).first()

            if not user:
                return {"success": False, "error": "Invalid credentials"}

            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.now():
                return {
                    "success": False,
                    "error": "Account temporarily locked due to failed login attempts",
                }

            # Check if account is active
            if not user.is_active:
                return {"success": False, "error": "Account is deactivated"}

            # Verify password
            if not self.verify_password(password, user.password_hash):
                # Increment failed attempts
                user.failed_login_attempts += 1

                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now() + timedelta(minutes=30)

                db.commit()
                return {"success": False, "error": "Invalid credentials"}

            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.now()

            # Create JWT token
            token_payload = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "exp": datetime.utcnow() + timedelta(hours=24),
                "iat": datetime.utcnow(),
            }

            token = jwt.encode(token_payload, self.secret_key, algorithm="HS256")

            # Store session
            token_hash = bcrypt.hashpw(token.encode(), bcrypt.gensalt()).decode()
            expires_at = datetime.now() + timedelta(hours=24)

            new_session = UserSession(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            db.add(new_session)
            db.commit()

            return {
                "success": True,
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 86400,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "email_verified": bool(user.email_verified),
                },
            }

        except Exception as e:
            logger.error(f"Authentication error: {e!s}")
            return {"success": False, "error": "Authentication failed"}
        finally:
            db.close()

    def verify_token(self, token: str) -> dict[str, Any] | None:
        """Verify JWT token and return user data."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])

            # Check if session is still valid
            db = self.SessionLocal()

            try:
                session = (
                    db.query(UserSession)
                    .filter(
                        UserSession.user_id == payload["user_id"],
                        UserSession.expires_at > datetime.now(),
                        UserSession.is_active,
                    )
                    .first()
                )

                if not session:
                    return None

                return payload

            finally:
                db.close()

        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Dependency to get current authenticated user."""
        token = credentials.credentials
        payload = self.verify_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return payload

    def get_user_profile(self, user_id: int) -> dict[str, Any]:
        """Get complete user profile data."""
        db = self.SessionLocal()

        try:
            # Get user data with preferences
            user = db.query(User).filter(User.id == user_id).first()

            if not user:
                return {"error": "User not found"}

            # Get active sessions count
            active_sessions = (
                db.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.expires_at > datetime.now(),
                    UserSession.is_active,
                )
                .count()
            )

            # Get or create preferences
            prefs = user.preferences
            if not prefs:
                prefs = UserPreference(user_id=user_id)
                db.add(prefs)
                db.commit()

            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "email_verified": bool(user.email_verified),
                "active_sessions": active_sessions,
                "preferences": {
                    "theme": prefs.theme,
                    "notifications_enabled": bool(prefs.notifications_enabled),
                    "marketing_emails": bool(prefs.marketing_emails),
                    "dashboard_layout": prefs.dashboard_layout,
                    "timezone": prefs.timezone,
                    "language": prefs.language,
                },
            }

        except Exception as e:
            logger.error(f"Error getting user profile: {e!s}")
            return {"error": "Failed to retrieve profile"}
        finally:
            db.close()

    def logout_user(self, token: str) -> dict[str, Any]:
        """Logout user by invalidating session."""
        payload = self.verify_token(token)
        if not payload:
            return {"success": False, "error": "Invalid token"}

        db = self.SessionLocal()

        try:
            # Deactivate all sessions for this user
            db.query(UserSession).filter(UserSession.user_id == payload["user_id"], UserSession.is_active).update(
                {"is_active": False}
            )

            db.commit()
            return {"success": True, "message": "Logged out successfully"}

        except Exception as e:
            logger.error(f"Logout error: {e!s}")
            return {"success": False, "error": "Logout failed"}
        finally:
            db.close()


# Global auth manager instance (lazy initialization)
_auth_manager = None


def get_auth_manager():
    """Get or create the global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager()
    return _auth_manager


# For backward compatibility
auth_manager = None  # Will be initialized when needed
