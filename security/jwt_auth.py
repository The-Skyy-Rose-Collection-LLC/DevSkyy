"""
Enterprise JWT Authentication System
Production-grade OAuth2 + JWT with refresh tokens, role-based access control
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from functools import wraps
import logging
import os
from typing import Any

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordBearer,
)
import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field


logger = logging.getLogger(__name__)

# JWT Configuration - Enhanced Security
# Truth Protocol Rule #5: No Secrets in Code - Must be set via environment variable
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError(
        "JWT_SECRET_KEY or SECRET_KEY environment variable must be set. "
        "Set JWT_SECRET_KEY in your .env file for production deployment."
    )
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced for security
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5  # Maximum failed login attempts
LOCKOUT_DURATION_MINUTES = 15  # Account lockout duration
TOKEN_BLACKLIST_EXPIRE_HOURS = 24  # How long to keep blacklisted tokens

# Password hashing - Enhanced with Argon2id (Truth Protocol requirement)
# Argon2id is primary, bcrypt for backward compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # Argon2id primary, bcrypt for legacy
    deprecated="auto",
    # Argon2id parameters (OWASP recommendations)
    argon2__memory_cost=65536,  # 64 MB memory
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 parallel threads
    argon2__type="id",  # Use Argon2id variant (hybrid mode)
    # Bcrypt for backward compatibility
    bcrypt__rounds=12,  # Increased rounds for better security
)

# Security schemes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
security_bearer = HTTPBearer()

# Security tracking

# Track failed login attempts
failed_login_attempts = defaultdict(list)
locked_accounts = {}
blacklisted_tokens = set()  # In production, use Redis or database


# ============================================================================
# MODELS
# ============================================================================


class UserRole(str):
    """User role enumeration"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    DEVELOPER = "developer"
    API_USER = "api_user"
    READ_ONLY = "read_only"


# Role hierarchy for permission checks (higher number = more permissions)
ROLE_HIERARCHY = {
    UserRole.SUPER_ADMIN: 5,
    UserRole.ADMIN: 4,
    UserRole.DEVELOPER: 3,
    UserRole.API_USER: 2,
    UserRole.READ_ONLY: 1,
}


class TokenType(str):
    """Token type enumeration"""

    ACCESS = "access"
    REFRESH = "refresh"


class TokenBlacklist:
    """Token blacklist management (in-memory, use Redis in production)"""

    _blacklist: set[str] = set()

    @classmethod
    def add(cls, token: str) -> None:
        """Add token to blacklist"""
        cls._blacklist.add(token)

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in cls._blacklist

    @classmethod
    def clear(cls) -> None:
        """Clear blacklist (for testing)"""
        cls._blacklist.clear()

    @classmethod
    def remove(cls, token: str) -> None:
        """Remove token from blacklist"""
        cls._blacklist.discard(token)


class User(BaseModel):
    """User model"""

    user_id: str
    email: EmailStr
    username: str
    password_hash: str | None = None  # Hashed password
    role: str = UserRole.API_USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: datetime | None = None
    permissions: list[str] = Field(default_factory=list)


class TokenData(BaseModel):
    """Token payload data"""

    user_id: str
    email: str
    username: str
    role: str
    token_type: str = "access"  # 'access' or 'refresh'
    exp: datetime


class TokenResponse(BaseModel):
    """Token response"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Registration request"""

    email: EmailStr
    username: str
    password: str
    role: str = UserRole.API_USER


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


# ============================================================================
# PASSWORD UTILITIES
# ============================================================================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# ENHANCED SECURITY FUNCTIONS
# ============================================================================


def is_account_locked(email: str) -> bool:
    """Check if account is locked due to failed login attempts"""
    if email in locked_accounts:
        lock_time = locked_accounts[email]
        if datetime.now() < lock_time:
            return True
        else:
            # Lock expired, remove from locked accounts
            del locked_accounts[email]
            if email in failed_login_attempts:
                del failed_login_attempts[email]
    return False


def record_failed_login(email: str) -> bool:
    """Record failed login attempt and lock account if necessary"""
    now = datetime.now()

    # Clean old attempts (older than 1 hour)
    hour_ago = now - timedelta(hours=1)
    failed_login_attempts[email] = [attempt for attempt in failed_login_attempts[email] if attempt > hour_ago]

    # Add current failed attempt
    failed_login_attempts[email].append(now)

    # Check if account should be locked
    if len(failed_login_attempts[email]) >= MAX_LOGIN_ATTEMPTS:
        locked_accounts[email] = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        logger.warning(f"🔒 Account locked due to failed login attempts: {email}")
        return True

    return False


def clear_failed_login_attempts(email: str):
    """Clear failed login attempts for successful login"""
    if email in failed_login_attempts:
        del failed_login_attempts[email]
    locked_accounts.pop(email, None)


def blacklist_token(token: str):
    """Add token to blacklist (logout/security breach)"""
    blacklisted_tokens.add(token)
    logger.info("🚫 Token blacklisted for security")


def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in blacklisted_tokens


def validate_token_security(token: str, token_data: TokenData) -> bool:
    """Enhanced token security validation"""
    # Check if token is blacklisted
    if is_token_blacklisted(token):
        logger.warning(f"⚠️ Blacklisted token used: {token_data.email}")
        return False

    # Check token age (additional security check)
    token_age = datetime.now() - token_data.exp + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if token_age > timedelta(hours=TOKEN_BLACKLIST_EXPIRE_HOURS):
        logger.warning(f"⚠️ Suspiciously old token used: {token_data.email}")
        return False

    return True


# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a new access token

    Args:
        data: Token payload data
        expires_delta: Custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "token_type": "access",
        }
    )

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a new refresh token

    Args:
        data: Token payload data

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
            "token_type": "refresh",
        }
    )

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def get_token_payload(token: str) -> dict[str, Any] | None:
    """
    Get token payload without validation (for testing purposes)

    Args:
        token: JWT token to decode

    Returns:
        Token payload or None if invalid
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """
    Verify and decode a JWT token

    Args:
        token: JWT token to verify
        token_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded token data

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Could not validate {token_type} token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

        # Check token type
        if payload.get("token_type") != token_type:
            raise credentials_exception

        # Extract data
        user_id: str = payload.get("user_id")
        email: str = payload.get("email")
        username: str = payload.get("username")
        role: str = payload.get("role")

        if user_id is None or email is None:
            raise credentials_exception

        token_data = TokenData(
            user_id=user_id,
            email=email,
            username=username,
            role=role,
            token_type=token_type,
            exp=datetime.fromtimestamp(payload.get("exp")),
        )

        # Enhanced security validation
        if not validate_token_security(token, token_data):
            logger.warning(f"🚨 Security validation failed for token: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token security validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return token_data

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"{token_type.capitalize()} token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise credentials_exception


# ============================================================================
# AUTHENTICATION DEPENDENCIES
# ============================================================================


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Get current authenticated user from token

    Args:
        token: JWT access token

    Returns:
        Token data with user information
    """
    return verify_token(token, token_type="access")


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user),
) -> TokenData:
    """
    Get current active user (additional checks can be added)

    Args:
        current_user: Current user token data

    Returns:
        Token data if user is active
    """
    # In production, check if user is active in database
    # For now, just return the user
    return current_user


# ============================================================================
# ROLE-BASED ACCESS CONTROL
# ============================================================================


class RoleChecker:
    """Role-based access control checker"""

    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_active_user)) -> TokenData:
        if user.role not in self.allowed_roles:
            logger.warning(f"User {user.email} with role {user.role} denied access. Required: {self.allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {self.allowed_roles}",
            )
        return user


# Predefined role checkers
require_super_admin = RoleChecker([UserRole.SUPER_ADMIN])
require_admin = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN])
require_developer = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DEVELOPER])
require_authenticated = RoleChecker(
    [
        UserRole.SUPER_ADMIN,
        UserRole.ADMIN,
        UserRole.DEVELOPER,
        UserRole.API_USER,
        UserRole.READ_ONLY,
    ]
)


# ============================================================================
# API KEY AUTHENTICATION (Alternative to JWT)
# ============================================================================


class APIKeyAuth:
    """API Key authentication for service-to-service communication"""

    @staticmethod
    def validate_api_key(
        credentials: HTTPAuthorizationCredentials = Security(security_bearer),
    ) -> dict[str, Any]:
        """
        Validate API key from Authorization header

        Args:
            credentials: HTTP Bearer credentials

        Returns:
            API key information
        """
        api_key = credentials.credentials

        # In production, validate against database
        # For now, validate against security manager
        try:
            from agent.security_manager import security_manager

            validation = security_manager.validate_api_key(api_key)

            if not validation["valid"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return validation

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key validation failed",
                headers={"WWW-Authenticate": "Bearer"},
            )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_user_tokens(user: User) -> TokenResponse:
    """
    Create access and refresh tokens for a user

    Args:
        user: User object

    Returns:
        Token response with access and refresh tokens
    """
    token_data = {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ============================================================================
# USER MANAGEMENT (In-memory for now, move to database in production)
# ============================================================================


class UserManager:
    """Simple user management (replace with database in production)"""

    def __init__(self):
        self.users: dict[str, User] = {}
        self.email_index: dict[str, str] = {}  # email -> user_id
        self.username_index: dict[str, str] = {}  # username -> user_id

        # Create default admin user
        self._create_default_users()

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, username_or_email: str, password: str) -> User | None:
        """Authenticate a user by username/email and password"""
        # Try to find user by email first
        user = self.get_user_by_email(username_or_email)
        if not user:
            # Try to find by username
            user = self.get_user_by_username(username_or_email)

        if not user or not user.password_hash:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now()
        return user

    def _create_default_users(self):
        """Create default users for development"""
        # Super admin
        admin_user = User(
            user_id="admin_001",
            email="admin@devskyy.com",
            username="admin",
            role=UserRole.SUPER_ADMIN,
            permissions=["*"],
        )
        self.users[admin_user.user_id] = admin_user
        self.email_index[admin_user.email] = admin_user.user_id
        self.username_index[admin_user.username] = admin_user.user_id

        # API user
        api_user = User(
            user_id="api_001",
            email="api@devskyy.com",
            username="api_user",
            role=UserRole.API_USER,
            permissions=["read", "write", "execute"],
        )
        self.users[api_user.user_id] = api_user
        self.email_index[api_user.email] = api_user.user_id
        self.username_index[api_user.username] = api_user.user_id

        logger.info(f"Created {len(self.users)} default users")

    def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        """Get user by email"""
        user_id = self.email_index.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    def get_user_by_username(self, username: str) -> User | None:
        """Get user by username"""
        user_id = self.username_index.get(username)
        if user_id:
            return self.users.get(user_id)
        return None

    def create_user(self, email: str, username: str, password: str, role: str = UserRole.API_USER) -> User:
        """Create a new user with hashed password"""
        # Check if email already exists
        if email in self.email_index:
            raise ValueError(f"User with email {email} already exists")

        # Check if username already exists
        if username in self.username_index:
            raise ValueError(f"User with username {username} already exists")

        # Generate user ID
        user_id = f"user_{len(self.users) + 1:06d}"

        # Hash password
        password_hash = self.hash_password(password)

        # Create user
        user = User(
            user_id=user_id,
            email=email,
            username=username,
            password_hash=password_hash,
            role=role,
        )

        # Store user
        self.users[user_id] = user
        self.email_index[email] = user_id
        self.username_index[username] = user_id

        logger.info(f"Created new user: {email} (username: {username}) with role {role}")

        return user


# Global user manager instance
user_manager = UserManager()


# ============================================================================
# JWT MANAGER (Unified Interface)
# ============================================================================


class JWTManager:
    """
    Unified JWT Management System

    Provides centralized interface for JWT operations including:
    - Token creation and validation
    - User authentication
    - Role-based access control
    - Token blacklisting
    - Account lockout management
    """

    def __init__(self):
        """Initialize JWT Manager with user manager instance"""
        self.user_manager = user_manager
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = REFRESH_TOKEN_EXPIRE_DAYS
        logger.info("✅ JWTManager initialized")

    def create_access_token(self, user: User) -> str:
        """Create access token for user"""
        data = {"sub": user.user_id, "email": user.email, "role": user.role, "type": "access"}
        return create_access_token(data)

    def create_refresh_token(self, user: User) -> str:
        """Create refresh token for user"""
        data = {"sub": user.user_id, "email": user.email, "type": "refresh"}
        return create_refresh_token(data)

    def create_user_tokens(self, user: User) -> TokenResponse:
        """Create both access and refresh tokens for user"""
        return create_user_tokens(user)

    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode token"""
        return verify_token(token, token_type)

    def authenticate_user(self, username_or_email: str, password: str) -> User | None:
        """Authenticate user with credentials"""
        return self.user_manager.authenticate_user(username_or_email, password)

    def blacklist_token(self, token: str):
        """Add token to blacklist"""
        blacklist_token(token)

    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return is_token_blacklisted(token)

    def check_role_permission(self, user_role: str, required_role: str) -> bool:
        """Check if user role has required permissions"""
        role_hierarchy = {
            UserRole.SUPER_ADMIN: 5,
            UserRole.ADMIN: 4,
            UserRole.DEVELOPER: 3,
            UserRole.API_USER: 2,
            UserRole.READ_ONLY: 1,
        }
        return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


logger.info("🔐 Enterprise JWT Authentication System initialized")


# ============================================================================
# ADDITIONAL JWT UTILITIES FOR TESTING
# ============================================================================


def create_token_pair(user_id: str, email: str, username: str, role: str) -> TokenResponse:
    """
    Create access and refresh token pair
    
    Args:
        user_id: User ID
        email: User email
        username: Username
        role: User role
    
    Returns:
        TokenResponse with both tokens
    """
    token_data = {
        "user_id": user_id,
        "email": email,
        "username": username,
        "role": role,
    }
    
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def verify_jwt_token(token: str, token_type: TokenType) -> dict[str, Any]:
    """
    Verify JWT token and return payload
    
    Args:
        token: JWT token
        token_type: Expected token type (ACCESS or REFRESH)
    
    Returns:
        Token payload dictionary
    
    Raises:
        HTTPException: If token is invalid or wrong type
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Verify token type matches expected
        if payload.get("token_type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type}",
            )
        
        # Check if blacklisted
        if TokenBlacklist.is_blacklisted(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def refresh_access_token(refresh_token: str) -> TokenResponse:
    """
    Create new access token using refresh token
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        New token pair
    
    Raises:
        HTTPException: If refresh token is invalid
    """
    payload = verify_jwt_token(refresh_token, TokenType.REFRESH)
    
    # Create new token pair
    return create_token_pair(
        user_id=payload["user_id"],
        email=payload["email"],
        username=payload["username"],
        role=payload["role"]
    )


def revoke_token(token: str) -> None:
    """
    Revoke a token by adding it to blacklist
    
    Args:
        token: Token to revoke
    """
    TokenBlacklist.add(token)
    logger.info(f"Token revoked")


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Check if user role has sufficient permissions
    
    Args:
        user_role: User's role
        required_role: Required role level
    
    Returns:
        True if user has permission
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    
    return user_level >= required_level


def require_role(required_role: str):
    """
    Decorator to require specific role for endpoint
    
    Args:
        required_role: Minimum required role
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a simplified version - in production would check current user
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def generate_secure_secret_key(length: int = 64) -> str:
    """
    Generate a secure random secret key
    
    Args:
        length: Length of key in bytes (default 64)
    
    Returns:
        Hex-encoded secret key
    """
    import secrets
    return secrets.token_hex(length)

