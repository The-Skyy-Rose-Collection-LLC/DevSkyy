# DevSkyy Platform - Deployment Implementation Guide

**Version:** 5.0 Enterprise
**Target:** Production-Ready A-Grade Platform
**Timeline:** 4 Weeks
**Current Status:** B+ (52/100) â†’ Target: A+ (90+/100)

---

## Table of Contents

1. [Quick Start Deployment](#quick-start-deployment)
2. [Week 1: Security Hardening](#week-1-security-hardening)
3. [Week 2: Enterprise Features](#week-2-enterprise-features)
4. [Week 3: Missing Agent Implementations](#week-3-missing-agent-implementations)
5. [Week 4: Testing & Production Launch](#week-4-testing--production-launch)
6. [Environment Configuration](#environment-configuration)
7. [Docker & Kubernetes Setup](#docker--kubernetes-setup)
8. [Database Migrations](#database-migrations)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Monitoring & Alerting](#monitoring--alerting)

---

## Quick Start Deployment

### Prerequisites

- **Python:** 3.11+ (required for enhanced performance)
- **Node.js:** 18.x LTS
- **PostgreSQL:** 13+ or MySQL 8+
- **Redis:** 6.0+
- **Docker:** 20.10+ (optional but recommended)

### Installation

```bash
# Clone repository
git clone https://github.com/SkyyRoseLLC/DevSkyy.git
cd DevSkyy

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (choose one)
pip install --upgrade pip
pip install -e .                  # Core only
pip install -e ".[dev]"           # Development (includes testing)
pip install -e ".[all]"           # All optional dependencies

# Or with uv (faster alternative)
uv pip install -e ".[dev]"
```

### Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

### Run Application

```bash
# Development mode with auto-reload
uvicorn main_enterprise:app --reload --host 127.0.0.1 --port 8000

# Production mode with Uvicorn
uvicorn main_enterprise:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the application:

- **API:** <http://localhost:8000>
- **Docs:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>

---

## Week 1: Security Hardening

### Priority 1: JWT/OAuth2 Authentication

#### 1.1 Install Required Packages

```bash
pip install PyJWT==2.10.1 passlib[bcrypt]==1.7.4 python-multipart==0.0.9
```

#### 1.2 Create JWT Authentication Module

Create `agent/security/jwt_auth.py`:

```python
"""
JWT/OAuth2 Authentication Module
RFC 7519 compliant implementation with refresh token rotation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "your-refresh-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenData(BaseModel):
    """Token payload data"""
    user_id: str
    roles: List[str]
    email: Optional[str] = None


class Token(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenData(BaseModel):
    """Refresh token payload"""
    user_id: str
    jti: str  # JWT ID for token tracking
    family_id: str  # Token family for rotation


class JWTAuthManager:
    """JWT Authentication Manager with refresh token rotation"""

    def __init__(self):
        self.active_refresh_tokens = {}  # In production, use Redis or database
        self.token_families = {}  # Track token families for reuse detection

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def create_access_token(
        self,
        user_id: str,
        roles: List[str],
        email: Optional[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token

        Args:
            user_id: User identifier
            roles: List of user roles
            email: User email (optional)
            expires_delta: Custom expiration time

        Returns:
            Encoded JWT token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode = {
            "sub": user_id,
            "roles": roles,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def create_refresh_token(
        self,
        user_id: str,
        family_id: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create refresh token with rotation support

        Args:
            user_id: User identifier
            family_id: Token family ID (for rotation)

        Returns:
            Dictionary with token and metadata
        """
        jti = str(uuid.uuid4())
        if not family_id:
            family_id = str(uuid.uuid4())

        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "jti": jti,
            "family_id": family_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        encoded_jwt = jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

        # Store active token
        self.active_refresh_tokens[jti] = {
            "user_id": user_id,
            "family_id": family_id,
            "created_at": datetime.utcnow(),
            "used": False
        }

        # Track family
        if family_id not in self.token_families:
            self.token_families[family_id] = []
        self.token_families[family_id].append(jti)

        return {
            "token": encoded_jwt,
            "jti": jti,
            "family_id": family_id
        }

    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """
        Verify and decode JWT token

        Args:
            token: JWT token string
            token_type: "access" or "refresh"

        Returns:
            TokenData object

        Raises:
            HTTPException: If token is invalid
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            secret = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
            payload = jwt.decode(token, secret, algorithms=[ALGORITHM])

            # Verify token type
            if payload.get("type") != token_type:
                raise credentials_exception

            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception

            roles: List[str] = payload.get("roles", [])
            email: Optional[str] = payload.get("email")

            return TokenData(user_id=user_id, roles=roles, email=email)

        except JWTError:
            raise credentials_exception

    def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token
        Implements token rotation and reuse detection

        Args:
            refresh_token: Current refresh token

        Returns:
            New access and refresh tokens

        Raises:
            HTTPException: If refresh token is invalid or reused
        """
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])

            jti = payload.get("jti")
            user_id = payload.get("sub")
            family_id = payload.get("family_id")

            # Check if token exists and hasn't been used
            if jti not in self.active_refresh_tokens:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )

            token_info = self.active_refresh_tokens[jti]

            # Reuse detection - if token already used, invalidate entire family
            if token_info["used"]:
                # Token reuse detected - security breach!
                self._invalidate_token_family(family_id)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token reuse detected. Please login again."
                )

            # Mark token as used
            token_info["used"] = True

            # Create new tokens
            # TODO: Get user roles from database
            roles = ["user"]  # Fetch from database in production

            new_access_token = self.create_access_token(user_id, roles)
            new_refresh_data = self.create_refresh_token(user_id, family_id)

            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_data["token"],
                "token_type": "bearer"
            }

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    def _invalidate_token_family(self, family_id: str):
        """Invalidate entire token family (reuse detection)"""
        if family_id in self.token_families:
            for jti in self.token_families[family_id]:
                if jti in self.active_refresh_tokens:
                    del self.active_refresh_tokens[jti]
            del self.token_families[family_id]

    def revoke_refresh_token(self, refresh_token: str):
        """Manually revoke a refresh token"""
        try:
            payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
            jti = payload.get("jti")

            if jti in self.active_refresh_tokens:
                del self.active_refresh_tokens[jti]
        except JWTError:
            pass  # Token already invalid


# Global instance
jwt_manager = JWTAuthManager()


# Dependency for protected routes
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """
    Dependency to get current user from JWT token
    Use in protected routes: current_user: TokenData = Depends(get_current_user)
    """
    return jwt_manager.verify_token(token, token_type="access")


# Role-based access control dependency
class RoleChecker:
    """
    Dependency for role-based access control

    Usage:
        @app.get("/admin/users")
        async def get_users(user: TokenData = Depends(RoleChecker(["admin"]))):
            ...
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: TokenData = Depends(get_current_user)) -> TokenData:
        if not any(role in self.allowed_roles for role in user.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return user
```

#### 1.3 Add Authentication Endpoints

Add to `main.py`:

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from agent.security.jwt_auth import (
    jwt_manager,
    get_current_user,
    RoleChecker,
    Token,
    TokenData
)

# Authentication endpoints
@app.post("/api/v1/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login

    - **username**: User email or username
    - **password**: User password
    """
    # TODO: Implement user authentication with database
    # This is a placeholder - replace with actual user verification
    user = await verify_user_credentials(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = jwt_manager.create_access_token(
        user_id=user["id"],
        roles=user["roles"],
        email=user["email"]
    )

    refresh_data = jwt_manager.create_refresh_token(user_id=user["id"])

    return {
        "access_token": access_token,
        "refresh_token": refresh_data["token"],
        "token_type": "bearer"
    }


@app.post("/api/v1/auth/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    Implements token rotation for security
    """
    new_tokens = jwt_manager.refresh_access_token(refresh_token)
    return new_tokens


@app.post("/api/v1/auth/logout")
async def logout(
    refresh_token: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Logout user by revoking refresh token"""
    jwt_manager.revoke_refresh_token(refresh_token)
    return {"message": "Successfully logged out"}


@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "roles": current_user.roles
    }


# Example protected endpoint
@app.get("/api/v1/admin/users")
async def get_all_users(admin_user: TokenData = Depends(RoleChecker(["admin"]))):
    """Admin-only endpoint"""
    # TODO: Fetch users from database
    return {"users": []}


# TODO: Implement this function
async def verify_user_credentials(username: str, password: str):
    """
    Verify user credentials against database

    Returns:
        User dict if valid, None otherwise
    """
    # Placeholder implementation
    # In production, query database and verify password
    return {
        "id": "user_123",
        "email": username,
        "roles": ["user", "admin"]
    }
```

#### 1.4 Update Existing Endpoints with Authentication

```python
# Protect existing endpoints
from agent.security.jwt_auth import get_current_user, TokenData

@app.post("/api/v1/ecommerce/products")
async def create_product(
    product: ProductCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create product - requires authentication"""
    # Original implementation
    pass

@app.get("/api/v1/ecommerce/products/{product_id}")
async def get_product(
    product_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get product - requires authentication"""
    pass
```

### Priority 2: AES-256-GCM Encryption

#### 2.1 Create Encryption Module

Create `agent/security/encryption.py`:

```python
"""
AES-256-GCM Encryption Module
NIST SP 800-38D compliant implementation
"""

import os
import base64
from typing import Dict
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import logging

logger = logging.getLogger(__name__)


class AESGCMEncryption:
    """
    AES-256-GCM encryption implementation

    Features:
    - 256-bit AES encryption
    - GCM mode for authenticated encryption
    - Unique nonce per message (CRITICAL for GCM)
    - PBKDF2 key derivation
    """

    def __init__(self, master_key: str = None):
        """
        Initialize encryption with master key

        Args:
            master_key: Base64 encoded 32-byte key (256 bits)
                       If None, reads from environment variable
        """
        if master_key is None:
            master_key = os.getenv("ENCRYPTION_MASTER_KEY")

        if not master_key:
            raise ValueError("Encryption master key not provided")

        # Decode master key
        try:
            self.master_key = base64.b64decode(master_key)
            if len(self.master_key) != 32:
                raise ValueError("Master key must be 32 bytes (256 bits)")
        except Exception as e:
            raise ValueError(f"Invalid master key format: {e}")

    def derive_key(self, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive encryption key using PBKDF2

        Args:
            salt: Random salt (minimum 16 bytes recommended)
            iterations: Number of PBKDF2 iterations

        Returns:
            Derived 32-byte key
        """
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(self.master_key)

    def encrypt(self, plaintext: str, associated_data: bytes = None) -> Dict[str, str]:
        """
        Encrypt plaintext using AES-256-GCM

        Args:
            plaintext: String to encrypt
            associated_data: Optional additional authenticated data

        Returns:
            Dictionary with ciphertext, nonce, tag, and salt (all base64 encoded)

        CRITICAL: Each message MUST use a unique nonce
        """
        try:
            # Generate unique nonce (12 bytes is standard for GCM)
            nonce = os.urandom(12)

            # Generate salt for key derivation
            salt = os.urandom(16)

            # Derive encryption key
            key = self.derive_key(salt)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()

            # Add associated data if provided
            if associated_data:
                encryptor.authenticate_additional_data(associated_data)

            # Encrypt
            ciphertext = encryptor.update(plaintext.encode('utf-8')) + encryptor.finalize()

            # Get authentication tag
            tag = encryptor.tag

            return {
                "ciphertext": base64.b64encode(ciphertext).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "tag": base64.b64encode(tag).decode('utf-8'),
                "salt": base64.b64encode(salt).decode('utf-8')
            }

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(
        self,
        ciphertext: str,
        nonce: str,
        tag: str,
        salt: str,
        associated_data: bytes = None
    ) -> str:
        """
        Decrypt ciphertext using AES-256-GCM

        Args:
            ciphertext: Base64 encoded ciphertext
            nonce: Base64 encoded nonce
            tag: Base64 encoded authentication tag
            salt: Base64 encoded salt
            associated_data: Optional additional authenticated data

        Returns:
            Decrypted plaintext string

        Raises:
            Exception: If decryption or authentication fails
        """
        try:
            # Decode base64 inputs
            ciphertext_bytes = base64.b64decode(ciphertext)
            nonce_bytes = base64.b64decode(nonce)
            tag_bytes = base64.b64decode(tag)
            salt_bytes = base64.b64decode(salt)

            # Derive decryption key
            key = self.derive_key(salt_bytes)

            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(nonce_bytes, tag_bytes),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()

            # Add associated data if provided
            if associated_data:
                decryptor.authenticate_additional_data(associated_data)

            # Decrypt and verify
            plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()

            return plaintext.decode('utf-8')

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Decryption or authentication failed")

    def encrypt_dict(self, data: dict) -> Dict[str, str]:
        """
        Encrypt a dictionary by serializing to JSON

        Args:
            data: Dictionary to encrypt

        Returns:
            Encrypted data dictionary
        """
        import json
        plaintext = json.dumps(data)
        return self.encrypt(plaintext)

    def decrypt_dict(self, encrypted_data: Dict[str, str]) -> dict:
        """
        Decrypt and deserialize to dictionary

        Args:
            encrypted_data: Encrypted data from encrypt_dict

        Returns:
            Original dictionary
        """
        import json
        plaintext = self.decrypt(
            encrypted_data["ciphertext"],
            encrypted_data["nonce"],
            encrypted_data["tag"],
            encrypted_data["salt"]
        )
        return json.loads(plaintext)


# Generate master key (run once, store securely)
def generate_master_key() -> str:
    """
    Generate a new 256-bit master key

    Returns:
        Base64 encoded master key

    Usage:
        key = generate_master_key()
        # Store in environment variable or secrets manager
        # export ENCRYPTION_MASTER_KEY="<key>"
    """
    key = os.urandom(32)  # 256 bits
    return base64.b64encode(key).decode('utf-8')


# Global instance
encryption = None

def get_encryption():
    """Get or create global encryption instance"""
    global encryption
    if encryption is None:
        encryption = AESGCMEncryption()
    return encryption
```

#### 2.2 Replace XOR Encryption

Update any files using XOR encryption:

```python
# OLD (insecure):
def xor_encrypt(data: str, key: str) -> str:
    return ''.join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

# NEW (secure):
from agent.security.encryption import get_encryption

def encrypt_sensitive_data(data: str) -> dict:
    """Encrypt sensitive data using AES-256-GCM"""
    encryption = get_encryption()
    return encryption.encrypt(data)

def decrypt_sensitive_data(encrypted_data: dict) -> str:
    """Decrypt sensitive data"""
    encryption = get_encryption()
    return encryption.decrypt(
        encrypted_data["ciphertext"],
        encrypted_data["nonce"],
        encrypted_data["tag"],
        encrypted_data["salt"]
    )
```

### Priority 3: Input Validation

#### 3.1 Create Validation Schemas

Create `agent/schemas/validation.py`:

```python
"""
Input Validation Schemas
Comprehensive validation for all API inputs
"""

from pydantic import BaseModel, validator, Field, constr, EmailStr
from typing import Optional, List
import re
import html

class ProductCreate(BaseModel):
    """Product creation schema with validation"""

    name: constr(min_length=1, max_length=200) = Field(..., description="Product name")
    description: Optional[str] = Field(None, max_length=10000)
    price: float = Field(..., gt=0, lt=1000000, description="Product price")
    cost: float = Field(..., gt=0, lt=1000000)
    quantity: int = Field(..., ge=0, le=1000000)
    sku: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(None, max_items=20)

    @validator('name', 'description', 'category')
    def sanitize_html(cls, v):
        """Sanitize HTML to prevent XSS"""
        if v is None:
            return v
        # Remove HTML tags
        v = html.escape(v)
        # Remove script tags
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)
        return v.strip()

    @validator('sku')
    def validate_sku(cls, v):
        """Validate SKU format"""
        if v is None:
            return v
        # SKU should be alphanumeric with hyphens
        if not re.match(r'^[A-Z0-9\-]+$', v):
            raise ValueError('SKU must be uppercase alphanumeric with hyphens')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags"""
        if v is None:
            return v
        # Each tag should be reasonable length
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tags must be less than 50 characters')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Silk Evening Dress",
                "description": "Elegant silk dress",
                "price": 299.99,
                "cost": 120.00,
                "quantity": 50,
                "sku": "SED-001",
                "category": "dresses",
                "tags": ["silk", "evening", "luxury"]
            }
        }


class UserCreate(BaseModel):
    """User creation schema"""

    email: EmailStr = Field(..., description="User email")
    password: constr(min_length=8, max_length=100) = Field(..., description="Password")
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)

    @validator('password')
    def validate_password(cls, v):
        """Enforce strong password policy"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
        # Remove non-digit characters
        digits = re.sub(r'\D', '', v)
        if not 10 <= len(digits) <= 15:
            raise ValueError('Phone number must be 10-15 digits')
        return v


class SearchQuery(BaseModel):
    """Search query validation"""

    query: constr(min_length=1, max_length=200)
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)

    @validator('query')
    def sanitize_query(cls, v):
        """Prevent SQL injection in search"""
        # Remove SQL special characters
        v = re.sub(r'[;\'"\\]', '', v)
        return v.strip()
```

#### 3.2 Apply Validation to Endpoints

```python
from agent.schemas.validation import ProductCreate, UserCreate, SearchQuery

@app.post("/api/v1/ecommerce/products")
async def create_product(
    product: ProductCreate,  # Pydantic validation
    current_user: TokenData = Depends(get_current_user)
):
    """Create product with full validation"""
    # Input is already validated by Pydantic
    result = await ecommerce_agent.create_product(product.dict())
    return result
```

### Priority 4: Security Headers

#### 4.1 Add Security Headers Middleware

Add to `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # HSTS - Force HTTPS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
```

---

## Week 2: Enterprise Features

### Implement API Versioning

#### 2.1 Create Version Structure

```bash
mkdir -p agent/api/v1
mkdir -p agent/api/v2
touch agent/api/__init__.py
touch agent/api/v1/__init__.py
touch agent/api/v2/__init__.py
```

#### 2.2 Create V1 Router

Create `agent/api/v1/router.py`:

```python
"""
API Version 1 Router
"""

from fastapi import APIRouter, Depends
from agent.security.jwt_auth import get_current_user, TokenData

v1_router = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={404: {"description": "Not found"}},
)

# Import endpoint modules
from . import products, pricing, inventory, wordpress, marketing

# Include sub-routers
v1_router.include_router(products.router, prefix="/ecommerce/products", tags=["products"])
v1_router.include_router(pricing.router, prefix="/ecommerce/pricing", tags=["pricing"])
v1_router.include_router(inventory.router, prefix="/ecommerce/inventory", tags=["inventory"])
v1_router.include_router(wordpress.router, prefix="/wordpress", tags=["wordpress"])
v1_router.include_router(marketing.router, prefix="/marketing", tags=["marketing"])

@v1_router.get("/")
async def v1_root():
    """API V1 root endpoint"""
    return {
        "version": "1.0.0",
        "status": "active",
        "endpoints": [
            "/api/v1/ecommerce/products",
            "/api/v1/ecommerce/pricing",
            "/api/v1/ecommerce/inventory",
            "/api/v1/wordpress",
            "/api/v1/marketing"
        ]
    }
```

#### 2.3 Add to Main Application

```python
from agent.api.v1.router import v1_router

# Include versioned router
app.include_router(v1_router)
```

### Implement Webhook System

#### 2.4 Create Webhook Manager

Create `agent/webhooks/webhook_manager.py`:

```python
"""
Webhook Management System
RFC 2104 compliant HMAC signatures with retry logic
"""

import asyncio
import hmac
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class WebhookManager:
    """
    Enterprise webhook management

    Features:
    - HMAC-SHA256 signatures
    - Exponential backoff retry
    - Circuit breaker per destination
    - Delivery tracking
    - Idempotency
    """

    def __init__(self):
        self.subscriptions = {}  # In production: use database
        self.delivery_history = []
        self.failed_deliveries = {}

    async def subscribe(
        self,
        url: str,
        events: List[str],
        secret: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Subscribe to webhook events

        Args:
            url: Webhook destination URL
            events: List of event types to subscribe to
            secret: Secret for HMAC signature generation
            metadata: Optional metadata

        Returns:
            Subscription ID
        """
        subscription_id = str(uuid.uuid4())

        self.subscriptions[subscription_id] = {
            "id": subscription_id,
            "url": url,
            "events": events,
            "secret": secret,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat(),
            "active": True,
            "delivery_count": 0,
            "last_delivery": None
        }

        logger.info(f"Webhook subscription created: {subscription_id} for {url}")
        return subscription_id

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe webhook"""
        if subscription_id in self.subscriptions:
            self.subscriptions[subscription_id]["active"] = False
            logger.info(f"Webhook unsubscribed: {subscription_id}")

    def generate_signature(self, payload: dict, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature (RFC 2104)

        Args:
            payload: Webhook payload
            secret: Shared secret

        Returns:
            Hex-encoded signature
        """
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    @retry(
        stop=stop_after_attempt(25),
        wait=wait_exponential(multiplier=1, min=60, max=86400),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def _deliver_webhook(
        self,
        url: str,
        payload: dict,
        signature: str,
        webhook_id: str
    ):
        """
        Deliver webhook with retry logic

        Retry schedule: 25 attempts over ~7 hours
        - Starts at 60 seconds
        - Exponential backoff (doubles each time)
        - Max 24 hours between attempts
        """
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": webhook_id,
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp())),
            "User-Agent": "DevSkyy-Webhooks/1.0"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            return {
                "status_code": response.status_code,
                "response": response.text[:1000]  # Limit response size
            }

    async def deliver_event(
        self,
        event_type: str,
        payload: dict,
        idempotency_key: Optional[str] = None
    ):
        """
        Deliver event to all subscribed webhooks

        Args:
            event_type: Type of event (e.g., "product.created")
            payload: Event payload
            idempotency_key: Optional idempotency key
        """
        webhook_id = idempotency_key or str(uuid.uuid4())

        # Find matching subscriptions
        matching_subs = [
            sub for sub in self.subscriptions.values()
            if sub["active"] and event_type in sub["events"]
        ]

        logger.info(f"Delivering event {event_type} to {len(matching_subs)} webhooks")

        delivery_tasks = []

        for subscription in matching_subs:
            # Generate signature
            signature = self.generate_signature(payload, subscription["secret"])

            # Create delivery task
            task = self._deliver_with_tracking(
                subscription_id=subscription["id"],
                url=subscription["url"],
                payload=payload,
                signature=signature,
                webhook_id=webhook_id,
                event_type=event_type
            )
            delivery_tasks.append(task)

        # Deliver asynchronously
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)

    async def _deliver_with_tracking(
        self,
        subscription_id: str,
        url: str,
        payload: dict,
        signature: str,
        webhook_id: str,
        event_type: str
    ):
        """Deliver webhook with tracking"""
        delivery_record = {
            "webhook_id": webhook_id,
            "subscription_id": subscription_id,
            "url": url,
            "event_type": event_type,
            "attempt_number": 1,
            "started_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        try:
            result = await self._deliver_webhook(url, payload, signature, webhook_id)

            delivery_record.update({
                "status": "success",
                "status_code": result["status_code"],
                "completed_at": datetime.utcnow().isoformat()
            })

            # Update subscription stats
            self.subscriptions[subscription_id]["delivery_count"] += 1
            self.subscriptions[subscription_id]["last_delivery"] = datetime.utcnow().isoformat()

            logger.info(f"Webhook delivered successfully: {subscription_id}")

        except Exception as e:
            delivery_record.update({
                "status": "failed",
                "error": str(e),
                "completed_at": datetime.utcnow().isoformat()
            })

            logger.error(f"Webhook delivery failed: {subscription_id} - {e}")

        finally:
            self.delivery_history.append(delivery_record)

    async def get_delivery_history(
        self,
        subscription_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get webhook delivery history"""
        history = self.delivery_history

        if subscription_id:
            history = [h for h in history if h["subscription_id"] == subscription_id]

        return history[-limit:]

    async def test_webhook(self, subscription_id: str) -> Dict[str, Any]:
        """Send test webhook"""
        if subscription_id not in self.subscriptions:
            raise ValueError("Subscription not found")

        test_payload = {
            "event": "test",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {"message": "This is a test webhook"}
        }

        await self.deliver_event("test", test_payload)

        return {"status": "test_sent", "subscription_id": subscription_id}


# Global instance
webhook_manager = WebhookManager()
```

#### 2.5 Add Webhook Endpoints

```python
from agent.webhooks.webhook_manager import webhook_manager

@app.post("/api/v1/webhooks/subscribe")
async def subscribe_webhook(
    url: str,
    events: List[str],
    secret: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Subscribe to webhook events"""
    subscription_id = await webhook_manager.subscribe(url, events, secret)
    return {"subscription_id": subscription_id}

@app.delete("/api/v1/webhooks/{subscription_id}")
async def unsubscribe_webhook(
    subscription_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Unsubscribe webhook"""
    await webhook_manager.unsubscribe(subscription_id)
    return {"status": "unsubscribed"}

@app.get("/api/v1/webhooks/list")
async def list_webhooks(current_user: TokenData = Depends(get_current_user)):
    """List all webhooks"""
    return {"webhooks": list(webhook_manager.subscriptions.values())}

@app.post("/api/v1/webhooks/{subscription_id}/test")
async def test_webhook(
    subscription_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Send test webhook"""
    result = await webhook_manager.test_webhook(subscription_id)
    return result

@app.get("/api/v1/webhooks/{subscription_id}/deliveries")
async def get_webhook_deliveries(
    subscription_id: str,
    limit: int = 100,
    current_user: TokenData = Depends(get_current_user)
):
    """Get webhook delivery history"""
    history = await webhook_manager.get_delivery_history(subscription_id, limit)
    return {"deliveries": history}
```

---

## Week 3: Missing Agent Implementations

### Social Media Automation Endpoints

Create `agent/api/v1/marketing/social.py`:

```python
"""
Social Media Automation Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from agent.security.jwt_auth import get_current_user, TokenData
from agent.modules.backend.social_media_automation_agent import social_media_agent

router = APIRouter()


class SocialPostCreate(BaseModel):
    """Social media post creation schema"""
    platforms: List[str]  # ["facebook", "instagram", "twitter"]
    content: str
    media_urls: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None
    hashtags: Optional[List[str]] = None


class SocialPostGenerate(BaseModel):
    """AI post generation schema"""
    product_id: Optional[str] = None
    topic: str
    tone: str = "professional"  # professional, casual, friendly, luxury
    platforms: List[str]


@router.post("/schedule")
async def schedule_social_post(
    post: SocialPostCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Schedule social media post"""
    result = await social_media_agent.schedule_post(
        platforms=post.platforms,
        content=post.content,
        media=post.media_urls,
        scheduled_time=post.scheduled_time,
        hashtags=post.hashtags,
        user_id=current_user.user_id
    )
    return result


@router.post("/generate")
async def generate_social_post(
    request: SocialPostGenerate,
    current_user: TokenData = Depends(get_current_user)
):
    """Generate AI-powered social media post"""
    result = await social_media_agent.generate_post(
        product_id=request.product_id,
        topic=request.topic,
        tone=request.tone,
        platforms=request.platforms
    )
    return result


@router.get("/analytics")
async def get_social_analytics(
    platform: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get social media analytics"""
    result = await social_media_agent.get_analytics(
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.user_id
    )
    return result


@router.post("/engage")
async def auto_engage(
    platform: str,
    engagement_type: str,  # "like", "comment", "share"
    target_hashtags: Optional[List[str]] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Automated social media engagement"""
    result = await social_media_agent.auto_engage(
        platform=platform,
        engagement_type=engagement_type,
        target_hashtags=target_hashtags,
        user_id=current_user.user_id
    )
    return result


@router.get("/calendar")
async def get_content_calendar(
    start_date: str,
    end_date: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get social media content calendar"""
    result = await social_media_agent.get_content_calendar(
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.user_id
    )
    return result
```

### Email/SMS Marketing Endpoints

Create `agent/api/v1/marketing/email.py`:

```python
"""
Email/SMS Marketing Automation Endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict

from agent.security.jwt_auth import get_current_user, TokenData
from agent.modules.backend.email_sms_automation_agent import email_sms_agent

router = APIRouter()


class EmailCampaignCreate(BaseModel):
    """Email campaign schema"""
    name: str
    subject: str
    from_name: str
    from_email: EmailStr
    template_id: Optional[str] = None
    html_content: Optional[str] = None
    recipients: List[EmailStr]
    segment_id: Optional[str] = None
    scheduled_time: Optional[str] = None


class SMSCampaignCreate(BaseModel):
    """SMS campaign schema"""
    name: str
    message: str
    recipients: List[str]  # Phone numbers
    scheduled_time: Optional[str] = None


@router.post("/campaign")
async def create_email_campaign(
    campaign: EmailCampaignCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create and send email campaign"""
    result = await email_sms_agent.create_email_campaign(
        name=campaign.name,
        subject=campaign.subject,
        from_name=campaign.from_name,
        from_email=campaign.from_email,
        template_id=campaign.template_id,
        html_content=campaign.html_content,
        recipients=campaign.recipients,
        scheduled_time=campaign.scheduled_time,
        user_id=current_user.user_id
    )
    return result


@router.post("/sms/send")
async def send_sms_campaign(
    campaign: SMSCampaignCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Send SMS campaign"""
    result = await email_sms_agent.send_sms_campaign(
        name=campaign.name,
        message=campaign.message,
        recipients=campaign.recipients,
        scheduled_time=campaign.scheduled_time,
        user_id=current_user.user_id
    )
    return result


@router.get("/analytics")
async def get_email_analytics(
    campaign_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get email marketing analytics"""
    result = await email_sms_agent.get_analytics(
        campaign_id=campaign_id,
        start_date=start_date,
        end_date=end_date,
        user_id=current_user.user_id
    )
    return result


@router.post("/template")
async def create_email_template(
    name: str,
    html_content: str,
    subject: str,
    variables: Optional[Dict] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Create email template"""
    result = await email_sms_agent.create_template(
        name=name,
        html_content=html_content,
        subject=subject,
        variables=variables,
        user_id=current_user.user_id
    )
    return result


@router.post("/ab-test")
async def create_ab_test(
    campaign_name: str,
    variant_a: Dict,
    variant_b: Dict,
    test_size_percent: int = 20,
    current_user: TokenData = Depends(get_current_user)
):
    """Create A/B test for email campaign"""
    result = await email_sms_agent.create_ab_test(
        campaign_name=campaign_name,
        variant_a=variant_a,
        variant_b=variant_b,
        test_size_percent=test_size_percent,
        user_id=current_user.user_id
    )
    return result
```

### Customer Service Endpoints

Create `agent/api/v1/support/tickets.py`:

```python
"""
Customer Service Automation Endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List

from agent.security.jwt_auth import get_current_user, TokenData
from agent.modules.backend.customer_service_agent import customer_service_agent

router = APIRouter()


class TicketCreate(BaseModel):
    """Support ticket creation schema"""
    customer_id: str
    subject: str
    description: str
    priority: str = "medium"  # low, medium, high, urgent
    category: Optional[str] = None


class ChatMessage(BaseModel):
    """Chat message schema"""
    message: str
    customer_id: str
    session_id: Optional[str] = None


@router.post("/ticket")
async def create_support_ticket(
    ticket: TicketCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """Create support ticket"""
    result = await customer_service_agent.create_ticket(
        customer_id=ticket.customer_id,
        subject=ticket.subject,
        description=ticket.description,
        priority=ticket.priority,
        category=ticket.category
    )
    return result


@router.post("/chat")
async def chat_with_bot(
    message: ChatMessage,
    current_user: TokenData = Depends(get_current_user)
):
    """Chat with AI support bot"""
    result = await customer_service_agent.process_chat(
        message=message.message,
        customer_id=message.customer_id,
        session_id=message.session_id
    )
    return result


@router.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get ticket details"""
    result = await customer_service_agent.get_ticket(ticket_id)
    return result


@router.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Resolve support ticket"""
    result = await customer_service_agent.resolve_ticket(
        ticket_id=ticket_id,
        resolution=resolution,
        resolved_by=current_user.user_id
    )
    return result


@router.get("/analytics")
async def get_support_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Get customer service analytics"""
    result = await customer_service_agent.get_analytics(
        start_date=start_date,
        end_date=end_date
    )
    return result
```

---

## Week 4: Testing & Production Launch

### Comprehensive Testing Suite

#### 4.1 Create Test Structure

```bash
mkdir -p tests
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/e2e
touch tests/__init__.py
touch tests/conftest.py
```

#### 4.2 Test Configuration

Create `tests/conftest.py`:

```python
"""
Pytest configuration and fixtures
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main_enterprise import app
from database.db import Base, get_db


# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def test_db():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client"""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user_token(client):
    """Get test user authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "TestPass123!"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(client):
    """Get admin authentication token"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "AdminPass123!"}
    )
    return response.json()["access_token"]
```

#### 4.3 Unit Tests

Create `tests/unit/test_security.py`:

```python
"""
Security module unit tests
"""

import pytest
from agent.security.jwt_auth import JWTAuthManager
from agent.security.encryption import AESGCMEncryption


def test_create_access_token():
    """Test JWT access token creation"""
    jwt_manager = JWTAuthManager()

    token = jwt_manager.create_access_token(
        user_id="user123",
        roles=["user", "admin"],
        email="test@example.com"
    )

    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_access_token():
    """Test JWT access token verification"""
    jwt_manager = JWTAuthManager()

    token = jwt_manager.create_access_token(
        user_id="user123",
        roles=["user"],
        email="test@example.com"
    )

    token_data = jwt_manager.verify_token(token, token_type="access")

    assert token_data.user_id == "user123"
    assert "user" in token_data.roles
    assert token_data.email == "test@example.com"


def test_refresh_token_rotation():
    """Test refresh token rotation"""
    jwt_manager = JWTAuthManager()

    # Create initial refresh token
    refresh_data = jwt_manager.create_refresh_token("user123")
    refresh_token = refresh_data["token"]

    # Refresh the token
    new_tokens = jwt_manager.refresh_access_token(refresh_token)

    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    assert new_tokens["refresh_token"] != refresh_token


def test_token_reuse_detection():
    """Test refresh token reuse detection"""
    jwt_manager = JWTAuthManager()

    refresh_data = jwt_manager.create_refresh_token("user123")
    refresh_token = refresh_data["token"]

    # Use token once
    jwt_manager.refresh_access_token(refresh_token)

    # Try to reuse - should raise exception
    with pytest.raises(HTTPException):
        jwt_manager.refresh_access_token(refresh_token)


def test_aes_encryption_decryption():
    """Test AES-256-GCM encryption/decryption"""
    # Generate test master key
    import base64, os
    master_key = base64.b64encode(os.urandom(32)).decode()

    encryption = AESGCMEncryption(master_key)

    plaintext = "Sensitive data to encrypt"

    # Encrypt
    encrypted = encryption.encrypt(plaintext)

    assert "ciphertext" in encrypted
    assert "nonce" in encrypted
    assert "tag" in encrypted
    assert "salt" in encrypted

    # Decrypt
    decrypted = encryption.decrypt(
        encrypted["ciphertext"],
        encrypted["nonce"],
        encrypted["tag"],
        encrypted["salt"]
    )

    assert decrypted == plaintext


def test_unique_nonces():
    """Test that each encryption uses unique nonce (CRITICAL for GCM)"""
    import base64, os
    master_key = base64.b64encode(os.urandom(32)).decode()

    encryption = AESGCMEncryption(master_key)

    plaintext = "Test message"

    # Encrypt same message multiple times
    encrypted1 = encryption.encrypt(plaintext)
    encrypted2 = encryption.encrypt(plaintext)

    # Nonces must be different
    assert encrypted1["nonce"] != encrypted2["nonce"]
    assert encrypted1["ciphertext"] != encrypted2["ciphertext"]
```

#### 4.4 Integration Tests

Create `tests/integration/test_api.py`:

```python
"""
API integration tests
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_authentication_flow(client):
    """Test complete authentication flow"""
    # Register user (if endpoint exists)
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "TestPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data

    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # Access protected endpoint
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    # Refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200


def test_product_crud(client, test_user_token):
    """Test product CRUD operations"""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Create product
    product_data = {
        "name": "Test Product",
        "description": "Test description",
        "price": 99.99,
        "cost": 50.00,
        "quantity": 100,
        "sku": "TEST-001"
    }

    response = client.post(
        "/api/v1/ecommerce/products",
        json=product_data,
        headers=headers
    )
    assert response.status_code == 200
    product_id = response.json()["product_id"]

    # Get product
    response = client.get(
        f"/api/v1/ecommerce/products/{product_id}",
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Product"


def test_webhook_subscription(client, test_user_token):
    """Test webhook subscription flow"""
    headers = {"Authorization": f"Bearer {test_user_token}"}

    # Subscribe
    response = client.post(
        "/api/v1/webhooks/subscribe",
        json={
            "url": "https://example.com/webhook",
            "events": ["product.created", "order.completed"],
            "secret": "webhook_secret_key"
        },
        headers=headers
    )
    assert response.status_code == 200
    subscription_id = response.json()["subscription_id"]

    # Test webhook
    response = client.post(
        f"/api/v1/webhooks/{subscription_id}/test",
        headers=headers
    )
    assert response.status_code == 200


def test_rbac_authorization(client, test_user_token, admin_token):
    """Test role-based access control"""
    user_headers = {"Authorization": f"Bearer {test_user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # User should not access admin endpoint
    response = client.get("/api/v1/admin/users", headers=user_headers)
    assert response.status_code == 403

    # Admin should access admin endpoint
    response = client.get("/api/v1/admin/users", headers=admin_headers)
    assert response.status_code == 200
```

#### 4.5 Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=agent --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_security.py -v

# Run specific test
pytest tests/unit/test_security.py::test_create_access_token -v
```

---

## Environment Configuration

### Production .env Template

Create `.env.production`:

```bash
# Application
APP_NAME=DevSkyy
APP_ENV=production
DEBUG=false
API_VERSION=1.0.0

# Security
JWT_SECRET_KEY=<generate-strong-secret-512-bits>
JWT_REFRESH_SECRET_KEY=<generate-different-strong-secret>
ENCRYPTION_MASTER_KEY=<generate-using-encryption-script>
API_KEY_SALT=<random-salt-for-api-keys>

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/devskyy_prod
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=<redis-password>

# AI Services
ANTHROPIC_API_KEY=<your-anthropic-key>
OPENAI_API_KEY=<your-openai-key>
GOOGLE_API_KEY=<your-google-key>
MISTRAL_API_KEY=<your-mistral-key>

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=<email>
SMTP_PASSWORD=<password>
FROM_EMAIL=noreply@devskyy.com

# SMS
TWILIO_ACCOUNT_SID=<twilio-sid>
TWILIO_AUTH_TOKEN=<twilio-token>
TWILIO_PHONE_NUMBER=<phone>

# Social Media
FACEBOOK_APP_ID=<app-id>
FACEBOOK_APP_SECRET=<app-secret>
INSTAGRAM_ACCESS_TOKEN=<token>
TWITTER_API_KEY=<key>
TWITTER_API_SECRET=<secret>

# Monitoring
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Feature Flags
ENABLE_WEBHOOKS=true
ENABLE_ML_PREDICTIONS=true
ENABLE_SELF_HEALING=true
ENABLE_BLOCKCHAIN=false

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=30
MAX_REQUESTS_PER_MINUTE=1000

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH
ALLOWED_HEADERS=*

# SSL/TLS
SSL_CERT_PATH=/etc/ssl/certs/cert.pem
SSL_KEY_PATH=/etc/ssl/private/key.pem
```

### Generate Secrets Script

Create `scripts/generate_secrets.py`:

```python
"""
Generate secure secrets for production deployment
"""

import secrets
import base64
import os


def generate_secret(bits=512):
    """Generate cryptographically secure secret"""
    return secrets.token_urlsafe(bits // 8)


def generate_encryption_key():
    """Generate AES-256 master key"""
    key = os.urandom(32)  # 256 bits
    return base64.b64encode(key).decode('utf-8')


def main():
    print("=" * 60)
    print("DevSkyy Production Secrets Generator")
    print("=" * 60)
    print()

    print("JWT_SECRET_KEY=", generate_secret(512))
    print("JWT_REFRESH_SECRET_KEY=", generate_secret(512))
    print("ENCRYPTION_MASTER_KEY=", generate_encryption_key())
    print("API_KEY_SALT=", generate_secret(256))
    print()

    print("=" * 60)
    print("IMPORTANT: Store these secrets securely!")
    print("- Use environment variables or secrets manager")
    print("- Never commit secrets to version control")
    print("- Rotate secrets regularly")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

Run: `python scripts/generate_secrets.py`

---

## Docker & Kubernetes Setup

### Docker Configuration

Create `Dockerfile`:

```dockerfile
# Multi-stage build for DevSkyy Platform
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 devsky && \
    chown -R devsky:devsky /app
USER devsky

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # FastAPI Application
  api:
    build: .
    container_name: devskyy_api
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/devskyy
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - devskyy_network

  # PostgreSQL Database
  db:
    image: postgres:15-alpine
    container_name: devskyy_db
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=devskyy
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - devskyy_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: devskyy_redis
    command: redis-server --requirepass redis_password
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - devskyy_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: devskyy_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped
    networks:
      - devskyy_network

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: devskyy_prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped
    networks:
      - devskyy_network

  # Grafana Dashboards
  grafana:
    image: grafana/grafana:latest
    container_name: devskyy_grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    restart: unless-stopped
    networks:
      - devskyy_network

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  devskyy_network:
    driver: bridge
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devskyy-api
  labels:
    app: devskyy
spec:
  replicas: 3
  selector:
    matchLabels:
      app: devskyy
  template:
    metadata:
      labels:
        app: devskyy
    spec:
      containers:
      - name: api
        image: devskyy/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: devskyy-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: devskyy-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: devskyy-service
spec:
  selector:
    app: devskyy
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: devskyy-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: devskyy-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## CI/CD Pipeline

Create `.github/workflows/deploy.yml`:

```yaml
name: DevSkyy CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"

    - name: Run linters
      run: |
        ruff check .
        black --check .
        mypy .

    - name: Run security checks
      run: |
        bandit -r . -ll
        pip-audit

    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        REDIS_URL: redis://localhost:6379/0
      run: |
        pytest tests/ -v --cov=agent --cov-report=xml --cov-report=term

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Login to Docker Hub
      uses: docker/login-action@v2
      with:
        username: ${{ secrets.DOCKER_USERNAME }}
        password: ${{ secrets.DOCKER_PASSWORD }}

    - name: Build and push
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: devskyy/api:latest,devskyy/api:${{ github.sha }}
        cache-from: type=registry,ref=devskyy/api:latest
        cache-to: type=inline

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Deploy to Kubernetes
      uses: azure/k8s-deploy@v4
      with:
        manifests: |
          k8s/deployment.yaml
        images: |
          devskyy/api:${{ github.sha }}
        kubectl-version: 'latest'
```

---

## Monitoring & Alerting

### Prometheus Configuration

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
  - static_configs:
    - targets: ['alertmanager:9093']

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'devskyy-api'
    static_configs:
    - targets: ['api:8000']
    metrics_path: '/metrics'
```

Create `alerts.yml`:

```yaml
groups:
  - name: devskyy_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (threshold: 5%)"

      - alert: SlowAPIResponse
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API responses"
          description: "95th percentile response time: {{ $value }}s"

      - alert: LowModelAccuracy
        expr: ml_model_accuracy < 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "ML model accuracy dropped"
          description: "Model accuracy: {{ $value }}"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / 1024 / 1024 > 512
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage: {{ $value }}MB"
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, e2e)
- [ ] Security audit complete
- [ ] JWT/OAuth2 implemented
- [ ] AES-256-GCM encryption implemented
- [ ] Input validation on all endpoints
- [ ] Security headers configured
- [ ] API versioning implemented
- [ ] Webhook system implemented
- [ ] Database migrations ready
- [ ] Environment variables configured
- [ ] Secrets generated and stored securely
- [ ] SSL certificates obtained
- [ ] Monitoring configured
- [ ] Alerting rules defined
- [ ] Backup strategy implemented
- [ ] Disaster recovery plan documented

### Post-Deployment

- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Logs being aggregated
- [ ] Alerts functioning
- [ ] Performance monitoring active
- [ ] SSL certificate auto-renewal configured
- [ ] Database backups scheduled
- [ ] Documentation updated
- [ ] Team training complete
- [ ] Incident response plan in place

---

## Support & Resources

### Documentation

- **API Docs:** <https://api.devskyy.com/docs>
- **User Guide:** <https://docs.devskyy.com>
- **Agent Documentation:** See AGENTS.md

### Contact

- **Email:** <support@devskyy.com>
- **Slack:** devskyy.slack.com
- **GitHub:** github.com/SkyyRoseLLC/DevSkyy

---

**Deployment Guide Version:** 1.0.0
**Last Updated:** October 17, 2025
**Status:** Production Ready
