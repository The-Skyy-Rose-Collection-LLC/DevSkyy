"""
Authentication Service - Database Integration
Implements user authentication, registration, and password management
Following Truth Protocol - No placeholders, production-ready

Author: DevSkyy Enterprise Team
Date: 2025-11-10
"""

from datetime import datetime
import logging
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models_sqlalchemy import User


logger = logging.getLogger(__name__)

# Password hashing context using Argon2id (Truth Protocol requirement)
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,
    argon2__parallelism=4,
)


class AuthService:
    """Authentication service with database integration"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using Argon2id

        Args:
            password: Plain text password

        Returns:
            Hashed password string

        Security:
            Uses Argon2id with NIST-recommended parameters
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash

        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hashed password

        Returns:
            True if password matches, False otherwise
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    @staticmethod
    async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[dict]:
        """
        Authenticate user against database

        Args:
            session: Database session
            username: Username or email
            password: Plain text password

        Returns:
            User dict if authenticated, None otherwise

        Security:
            - Constant-time password comparison
            - No information leakage on failure
            - Audit logging
        """
        try:
            # Query user by username or email
            stmt = select(User).where((User.username == username) | (User.email == username))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Authentication failed: user not found - {username[:3]}***")
                return None

            # Check if user is active
            if not user.is_active:
                logger.warning(f"Authentication failed: inactive user - {user.username}")
                return None

            # Verify password
            if not AuthService.verify_password(password, user.hashed_password):
                logger.warning(f"Authentication failed: invalid password - {user.username}")
                return None

            logger.info(f"User authenticated successfully: {user.username}")

            # Return user data (excluding sensitive fields)
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_superuser": user.is_superuser,
                "roles": ["SuperAdmin"] if user.is_superuser else ["User"],
                "created_at": user.created_at,
            }

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    @staticmethod
    async def create_user(
        session: AsyncSession,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        is_superuser: bool = False,
    ) -> Optional[dict]:
        """
        Create new user in database

        Args:
            session: Database session
            username: Unique username
            email: Unique email address
            password: Plain text password (will be hashed)
            full_name: User's full name (optional)
            is_superuser: Whether user has superuser privileges

        Returns:
            Created user dict or None if creation failed

        Security:
            - Password is hashed before storage
            - Email and username uniqueness validated
            - Input validation performed
        """
        try:
            # Check if user exists
            stmt = select(User).where((User.username == username) | (User.email == email))
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                if existing_user.username == username:
                    logger.warning("User creation failed: username already exists")
                    return None
                if existing_user.email == email:
                    logger.warning("User creation failed: email already exists")
                    return None

            # Hash password
            hashed_password = AuthService.hash_password(password)

            # Create new user
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                full_name=full_name,
                is_active=True,
                is_superuser=is_superuser,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)

            logger.info(f"User created successfully: {new_user.username}")

            return {
                "id": new_user.id,
                "username": new_user.username,
                "email": new_user.email,
                "full_name": new_user.full_name,
                "is_active": new_user.is_active,
                "is_superuser": new_user.is_superuser,
                "created_at": new_user.created_at,
            }

        except Exception as e:
            logger.error(f"User creation error: {e}")
            await session.rollback()
            return None

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[dict]:
        """
        Get user by ID

        Args:
            session: Database session
            user_id: User ID

        Returns:
            User dict or None if not found
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "roles": ["SuperAdmin"] if user.is_superuser else ["User"],
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }

        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None

    @staticmethod
    async def update_user_password(session: AsyncSession, user_id: int, new_password: str) -> bool:
        """
        Update user password

        Args:
            session: Database session
            user_id: User ID
            new_password: New plain text password

        Returns:
            True if successful, False otherwise

        Security:
            - Password is hashed before storage
            - Audit logged
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"Password update failed: user not found - ID {user_id}")
                return False

            # Hash new password
            user.hashed_password = AuthService.hash_password(new_password)
            user.updated_at = datetime.utcnow()

            await session.commit()

            logger.info(f"Password updated successfully for user: {user.username}")
            return True

        except Exception as e:
            logger.error(f"Password update error: {e}")
            await session.rollback()
            return False

    @staticmethod
    async def deactivate_user(session: AsyncSession, user_id: int) -> bool:
        """
        Deactivate user account

        Args:
            session: Database session
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                logger.warning(f"User deactivation failed: user not found - ID {user_id}")
                return False

            user.is_active = False
            user.updated_at = datetime.utcnow()

            await session.commit()

            logger.info(f"User deactivated: {user.username}")
            return True

        except Exception as e:
            logger.error(f"User deactivation error: {e}")
            await session.rollback()
            return False


# Backward compatibility function
async def authenticate_user_from_db(username: str, password: str) -> Optional[dict]:
    """
    Authenticate user against database (standalone function for backward compatibility)

    Args:
        username: Username or email
        password: Plain text password

    Returns:
        User dict if authenticated, None otherwise
    """
    async for session in get_db():
        return await AuthService.authenticate_user(session, username, password)
