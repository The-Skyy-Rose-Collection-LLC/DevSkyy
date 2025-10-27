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
    FastAPI dependency to verify JWT token on every protected endpoint
    
    Usage in endpoints:
        @app.get("/protected")
        async def protected_endpoint(current_user: Dict = Depends(get_current_user)):
            return {"user_id": current_user["sub"]}
    """
    return verify_access_token(token)

async def get_current_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    FastAPI dependency for admin-only endpoints (RBAC)
    """
    if "admin" not in current_user.get("roles", []):
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
    Authenticate user credentials
    
    TODO: Replace with actual database lookup
    This is a stub - implement by querying User table from database
    
    Args:
        username: Username
        password: Plaintext password
        
    Returns:
        User dict if credentials valid, None otherwise
    """
    # STUB: In production, query database:
    # user = await db.query(User).filter(User.username == username).first()
    # if user and verify_password(password, user.hashed_password):
    #     return {"id": user.id, "username": user.username, "roles": user.roles}
    # return None
    
    logger.warning("authenticate_user() is a stub - implement database lookup")
    return None

async def login(credentials: UserCredentials) -> AccessToken:
    """
    Login endpoint - authenticate and return tokens
    
    Args:
        credentials: Username and password
        
    Returns:
        AccessToken with access_token, refresh_token, expires_in
        
    Raises:
        HTTPException: If credentials invalid
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
    Refresh endpoint - exchange refresh token for new access token
    
    Args:
        request: RefreshTokenRequest with refresh_token
        
    Returns:
        New AccessToken pair
        
    Citation: RFC 6749 Section 6 (Refreshing an Access Token)
    """
    payload = verify_refresh_token(request.refresh_token)
    user_id = payload["sub"]
    
    # TODO: Retrieve user roles from database
    roles = []  # STUB
    
    access_token = create_access_token(user_id=user_id, roles=roles)
    # Issue new refresh token (rotating refresh token strategy)
    new_refresh_token = create_refresh_token(user_id=user_id)
    
    return AccessToken(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
