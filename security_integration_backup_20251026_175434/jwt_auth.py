from datetime import datetime, timedelta, timezone
import os

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from agent.security_manager import security_manager
from collections import defaultdict
from passlib.context import CryptContext
from typing import Any, Dict, List, Optional
import jwt
import logging

"""
Enterprise JWT Authentication System
Production-grade OAuth2 + JWT with refresh tokens, role-based access control
"""

logger = logging.getLogger(__name__)

# JWT Configuration - Enhanced Security
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", os.getenv("SECRET_KEY", "INSECURE_DEFAULT_CHANGE_ME")
)
JWT_ALGORITHM =  "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced for security
REFRESH_TOKEN_EXPIRE_DAYS = 7
MAX_LOGIN_ATTEMPTS = 5  # Maximum failed login attempts
LOCKOUT_DURATION_MINUTES = 15  # Account lockout duration
TOKEN_BLACKLIST_EXPIRE_HOURS = 24  # How long to keep blacklisted tokens

# Password hashing - Enhanced
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
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

class User(BaseModel):
    """User model"""

    user_id: str
    email: EmailStr
    username: str
    password_hash: Optional[str] = None  # Hashed password
    role: str = UserRole.API_USER
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    permissions: List[str] = Field(default_factory=list)

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
    failed_login_attempts[email] = [
        attempt for attempt in failed_login_attempts[email] if attempt > hour_ago
    ]

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
    if email in locked_accounts:
        del locked_accounts[email]

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
    token_age = (
        datetime.now() - token_data.exp + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    if token_age > timedelta(hours=TOKEN_BLACKLIST_EXPIRE_HOURS):
        logger.warning(f"⚠️ Suspiciously old token used: {token_data.email}")
        return False

    return True

# ============================================================================
# JWT TOKEN UTILITIES
# ============================================================================

def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
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
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "access",
        }
    )

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a new refresh token

    Args:
        data: Token payload data

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "token_type": "refresh",
        }
    )

    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
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

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_active_user)) -> TokenData:
        if user.role not in self.allowed_roles:
            logger.warning(
                f"User {user.email} with role {user.role} denied access. Required: {self.allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden. Required role: {self.allowed_roles}",
            )
        return user

# Predefined role checkers
require_super_admin = RoleChecker([UserRole.SUPER_ADMIN])
require_admin = RoleChecker([UserRole.SUPER_ADMIN, UserRole.ADMIN])
require_developer = RoleChecker(
    [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.DEVELOPER]
)
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
    ) -> Dict[str, Any]:
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
        self.users: Dict[str, User] = {}
        self.email_index: Dict[str, str] = {}  # email -> user_id
        self.username_index: Dict[str, str] = {}  # username -> user_id

        # Create default admin user
        self._create_default_users()

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Optional[User]:
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
        # Super admin with default password
        admin_user = User(
            user_id="admin_001",
            email="admin@devskyy.com",
            username="admin",
            password_hash=self.hash_password("admin123"),  # Default password: admin123
            role=UserRole.SUPER_ADMIN,
            permissions=["*"],
        )
        self.users[admin_user.user_id] = admin_user
        self.email_index[admin_user.email] = admin_user.user_id
        self.username_index[admin_user.username] = admin_user.user_id

        # API user with default password
        api_user = User(
            user_id="api_001",
            email="api@devskyy.com",
            username="api_user",
            password_hash=self.hash_password("api123"),  # Default password: api123
            role=UserRole.API_USER,
            permissions=["read", "write", "execute"],
        )
        self.users[api_user.user_id] = api_user
        self.email_index[api_user.email] = api_user.user_id
        self.username_index[api_user.username] = api_user.user_id

        logger.info(f"Created {len(self.users)} default users")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self.email_index.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        user_id = self.username_index.get(username)
        if user_id:
            return self.users.get(user_id)
        return None

    def create_user(
        self, email: str, username: str, password: str, role: str = UserRole.API_USER
    ) -> User:
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

        logger.info(
            f"Created new user: {email} (username: {username}) with role {role}"
        )

        return user

# Global user manager instance
user_manager = UserManager()

logger.info("🔐 Enterprise JWT Authentication System initialized")
