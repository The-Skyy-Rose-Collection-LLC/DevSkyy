"""
Authentication API Endpoints
JWT/OAuth2 authentication with user management
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from security.jwt_auth import (
    RegisterRequest,
    TokenData,
    TokenResponse,
    User,
    UserRole,
    create_user_tokens,
    get_current_active_user,
    user_manager,
    verify_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """
    Register a new user

    Creates a new user account with the specified email, username, and password.
    Default role is API_USER unless specified.
    """
    try:
        # Check if user already exists
        existing_user = user_manager.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

        # Create user
        user = user_manager.create_user(
            email=request.email, username=request.username, password=request.password, role=request.role
        )

        logger.info(f"New user registered: {user.email}")

        return user

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login and get access token

    Uses OAuth2 password flow. Provide username/email and password.
    Returns access token and refresh token.
    """
    try:
        # Authenticate user with username/email and password
        user = user_manager.authenticate_user(form_data.username, form_data.password)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )

        logger.info(f"User logged in: {user.email} (username: {user.username})")

        # Create tokens
        tokens = create_user_tokens(user)

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token

    Provide refresh token to get a new access token.
    """
    try:
        # Verify refresh token
        token_data = verify_token(refresh_token, token_type="refresh")

        # Get user
        user = user_manager.get_user_by_id(token_data.user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        # Create new tokens
        tokens = create_user_tokens(user)

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: TokenData = Depends(get_current_active_user)):
    """
    Get current user information

    Returns the currently authenticated user's profile.
    """
    user = user_manager.get_user_by_id(current_user.user_id)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_active_user)):
    """
    Logout current user

    In production, this would invalidate the token on the server side.
    For now, it just confirms logout (client should delete the token).
    """
    logger.info(f"User logged out: {current_user.email}")

    return {"message": "Successfully logged out", "user": current_user.email}


# ============================================================================
# USER MANAGEMENT
# ============================================================================


@router.get("/users", response_model=Dict[str, list])
async def list_users(current_user: TokenData = Depends(get_current_active_user)):
    """
    List all users (admin only in production)

    Returns list of all registered users.
    """
    # In production, check if user is admin
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    users = list(user_manager.users.values())

    return {"users": [user.model_dump() for user in users], "count": len(users)}


logger.info("✅ Authentication API endpoints registered")
