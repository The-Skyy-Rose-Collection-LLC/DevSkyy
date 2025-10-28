"""
JWT Authentication Module (RFC 7519 Compliant)
Implements OAuth2 with access + refresh token rotation
Author: DevSkyy Enterprise Team
Date: October 26, 2025
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List, Any
import jwt
from jwt import PyJWTError
from pydantic import BaseModel, Field, EmailStr, validator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION (RFC 7519 Section 4.1.4: Expiration Time)
# ============================================================================

class JWTSettings:
    """JWT configuration following RFC 7519 standards"""
    
    SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    REFRESH_SECRET_KEY: str = os.getenv("JWT_REFRESH_SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"  # HMAC SHA-256 (RFC 7518)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # Longer-lived refresh tokens
    
    def __init__(self):
        if len(self.SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters (256 bits)")
        if len(self.REFRESH_SECRET_KEY) < 32:
            raise ValueError("JWT_REFRESH_SECRET_KEY must be at least 32 characters")

settings = JWTSettings()

# ============================================================================
# PASSWORD HASHING (PBKDF2 via passlib/bcrypt)
# ============================================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # NIST recommendation: 10-12 rounds
)

# ============================================================================
# RBAC ROLES (5-Role Hierarchy per CLAUDE.md)
# ============================================================================

from enum import Enum

class UserRole(str, Enum):
    """
    User roles for RBAC (Role-Based Access Control).

    Hierarchy (highest to lowest):
    - SUPER_ADMIN: Full system access, user management
    - ADMIN: Brand management, workflow execution
    - DEVELOPER: API access, code generation, content creation
    - API_USER: Limited API access, read/write operations
    - READ_ONLY: View-only access

    Citation: CLAUDE.md Section 3 (RBAC Requirements)
    """
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DEVELOPER = "developer"
    API_USER = "api_user"
    READ_ONLY = "read_only"


ROLE_HIERARCHY = {
    UserRole.SUPER_ADMIN: 5,
    UserRole.ADMIN: 4,
    UserRole.DEVELOPER: 3,
    UserRole.API_USER: 2,
    UserRole.READ_ONLY: 1,
}


def has_permission(user_role: UserRole, required_role: UserRole) -> bool:
    """
    Determine whether a user's role meets or exceeds a required role.
    
    Parameters:
        user_role (UserRole): The user's current role.
        required_role (UserRole): The minimum role required to perform an action.
    
    Returns:
        True if `user_role` has equal or higher privilege than `required_role`, False otherwise.
    """
    return ROLE_HIERARCHY[user_role] >= ROLE_HIERARCHY[required_role]


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class TokenData(BaseModel):
    """Token payload (RFC 7519 Section 4: Claims)"""
    sub: str  # Subject (user ID)
    exp: datetime  # Expiration Time
    iat: datetime  # Issued At
    roles: List[str] = []  # User roles (RBAC)
    scopes: List[str] = []  # OAuth2 scopes
    jti: str = Field(default_factory=lambda: secrets.token_urlsafe(16))  # JWT ID (unique identifier)

class AccessToken(BaseModel):
    """Access token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class RefreshTokenRequest(BaseModel):
    """Refresh token request payload"""
    refresh_token: str

class UserCredentials(BaseModel):
    """User login credentials"""
    username: str
    password: str

class UserResponse(BaseModel):
    """User response (no password)"""
    id: int
    username: str
    email: EmailStr
    is_active: bool
    roles: List[str]

# ============================================================================
# TOKEN OPERATIONS
# ============================================================================

def hash_password(password: str) -> str:
    """
    Hash password using bcrypt (PBKDF2 via passlib)
    
    Args:
        password: Plaintext password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plaintext password
        hashed_password: Hashed password from DB
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(
    user_id: str,
    roles: List[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token (RFC 7519)
    
    Args:
        user_id: User ID (subject claim)
        roles: User roles for RBAC
        expires_delta: Custom expiration (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)
        
    Returns:
        Encoded JWT token
        
    Citation: RFC 7519 Section 3.1 (Header), Section 4.1 (Registered Claim Names)
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": exp,
        "roles": roles,
        "type": "access",
        "jti": secrets.token_urlsafe(16)
    }
    
    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.info(f"Access token created for user {user_id}, expires: {exp}")
    return token

def create_refresh_token(user_id: str) -> str:
    """
    Create JWT refresh token (RFC 7519)
    Refresh tokens are longer-lived and used to obtain new access tokens
    
    Args:
        user_id: User ID (subject claim)
        
    Returns:
        Encoded refresh token
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": exp,
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)
    }
    
    token = jwt.encode(
        payload,
        settings.REFRESH_SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    logger.info(f"Refresh token created for user {user_id}, expires: {exp}")
    return token

def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT access token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type (expected 'access')"
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID (sub claim)"
            )
        
        return payload
    
    except PyJWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT refresh token
    
    Args:
        token: Refresh token to verify
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.REFRESH_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type (expected 'refresh')"
            )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID"
            )
        
        return payload
    
    except PyJWTError as e:
        logger.warning(f"Refresh token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

# ============================================================================
# FASTAPI DEPENDENCIES
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Resolve and validate the current user from the request's access token.
    
    Returns:
        dict: Decoded JWT payload containing the authenticated user's claims (e.g., `sub`, `roles`, `exp`, `iat`, `jti`).
    """
    return verify_access_token(token)

def require_role(required_role: UserRole):
    """
    Create a FastAPI dependency that enforces a minimum user role according to the RBAC hierarchy.
    
    Parameters:
        required_role (UserRole): Minimum role required to access the protected endpoint.
    
    Returns:
        Callable: A FastAPI dependency function that resolves the current user (via get_current_user), determines the user's highest role (defaults to `UserRole.READ_ONLY` when no valid roles are present), and raises HTTPException(status_code=403) if the user's role level is lower than `required_role`. On success, the dependency returns the `current_user` dict.
    """
    async def role_checker(current_user: Dict = Depends(get_current_user)) -> Dict[str, Any]:
        """
        Enforces that the current user has at least the required role and returns the user's decoded payload.
        
        Parameters:
        	current_user (Dict): Decoded user payload (JWT claims) — may include a "roles" list of role names.
        
        Returns:
        	Dict[str, Any]: The same `current_user` payload when the user has sufficient permissions.
        
        Raises:
        	HTTPException: 403 Forbidden if the user's highest role does not meet the required role.
        """
        user_roles = current_user.get("roles", [])

        # If no roles, default to READ_ONLY
        if not user_roles:
            user_role = UserRole.READ_ONLY
        else:
            # Get highest role from user's roles
            user_role_levels = [
                ROLE_HIERARCHY.get(UserRole(role), 0)
                for role in user_roles
                if role in [r.value for r in UserRole]
            ]

            if not user_role_levels:
                user_role = UserRole.READ_ONLY
            else:
                # Find role with highest level
                max_level = max(user_role_levels)
                user_role = next(
                    role for role, level in ROLE_HIERARCHY.items()
                    if level == max_level
                )

        # Check permission
        if not has_permission(user_role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_role.value}, Current: {user_role.value}"
            )

        return current_user

    return role_checker


async def get_current_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Dependency that enforces admin-level access for the resolved current user.
    
    Deprecated: Use require_role(UserRole.ADMIN) instead.
    
    Returns:
        dict: The current user dictionary as returned by `get_current_user`.
    
    Raises:
        fastapi.HTTPException: HTTP 403 if the current user does not have `admin` or `super_admin` role.
    """
    user_roles = current_user.get("roles", [])

    # Check if user has admin or super_admin role
    if not any(role in ["admin", "super_admin"] for role in user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user

async def require_scope(required_scope: str):
    """
    FastAPI dependency factory for OAuth2 scope validation
    
    Usage:
        @app.get("/api")
        async def endpoint(
            current_user: Dict = Depends(get_current_user),
            _: None = Depends(require_scope("api:read"))
        ):
            pass
    """
    async def scope_checker(current_user: Dict = Depends(get_current_user)):
        if required_scope not in current_user.get("scopes", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return current_user
    
    return scope_checker

# ============================================================================
# EXPORTED FUNCTIONS FOR API ENDPOINTS
# ============================================================================

async def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user credentials against the application's user store.
    
    This function is a placeholder and currently always returns None to fail closed; replace its body with a database-backed lookup that verifies the supplied password (e.g., using verify_password) and returns a user dictionary on success.
    
    Args:
        username (str): The username to authenticate.
        password (str): The plaintext password to verify.
    
    Returns:
        Optional[Dict[str, Any]]: A dictionary with user information (e.g., id, username, email, roles) if authentication succeeds, `None` otherwise.
    """
    logger.error(
        "authenticate_user() not integrated with database. "
        "See function docstring for implementation example. "
        "Refusing authentication for security."
    )
    # Intentionally return None to fail closed (secure by default)
    # Do not authenticate without proper database integration
    return None

async def login(credentials: UserCredentials) -> AccessToken:
    """
    Authenticate user credentials and return new access and refresh tokens.
    
    Parameters:
        credentials (UserCredentials): Login credentials containing `username` and `password`.
    
    Returns:
        AccessToken: Contains `access_token`, `refresh_token`, `token_type` ("bearer"), and `expires_in` (seconds until the access token expires).
    
    Raises:
        HTTPException: If the provided credentials are invalid (401 Unauthorized).
    """
    user = await authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(
        user_id=user["id"],
        roles=user.get("roles", [])
    )
    refresh_token = create_refresh_token(user_id=user["id"])
    
    return AccessToken(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    )

async def refresh(request: RefreshTokenRequest) -> AccessToken:
    """
    Exchange a refresh token for a new access token and a rotated refresh token.
    
    Parameters:
        request (RefreshTokenRequest): Payload containing the `refresh_token` to verify.
    
    Returns:
        AccessToken: Model containing the new `access_token`, rotated `refresh_token`, and `expires_in` (seconds).
    
    Notes:
        Roles are taken from the decoded refresh token payload; in production, the authoritative role set should be reloaded from the database if up-to-date role enforcement is required.
    """
    payload = verify_refresh_token(request.refresh_token)
    user_id = payload["sub"]

    # Retrieve roles from token payload (preserved from login)
    # In production, consider querying database to get latest roles
    roles = payload.get("roles", [UserRole.READ_ONLY.value])

    access_token = create_access_token(user_id=user_id, roles=roles)
    # Issue new refresh token (rotating refresh token strategy)
    new_refresh_token = create_refresh_token(user_id=user_id)

    logger.info(f"Tokens refreshed for user {user_id}")

    return AccessToken(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )