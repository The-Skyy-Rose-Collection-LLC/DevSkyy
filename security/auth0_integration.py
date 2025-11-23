from datetime import datetime, timedelta
from functools import lru_cache
import json
import logging
import os
from typing import Any
from urllib.parse import quote_plus, urlencode

from authlib.integrations.httpx_client import AsyncOAuth2Client
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from jose import JWTError, jwt
from jose.backends import RSAKey
from pydantic import BaseModel

from security.log_sanitizer import sanitize_for_log


"""
Auth0 Integration for DevSkyy Enterprise Platform
Enterprise-grade authentication with Auth0 for unicorn-ready scaling
Adapted from Flask to FastAPI with JWT token integration
"""

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# HTTP timeout for external API requests (per enterprise best practices)
HTTP_TIMEOUT = 15  # seconds

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "devskyy.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://api.devskyy.com")
AUTH0_ALGORITHMS = ["RS256"]
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")

# DevSkyy JWT Configuration (for hybrid authentication)
DEVSKYY_SECRET_KEY = os.getenv("SECRET_KEY")
DEVSKYY_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# OAuth2 Configuration
AUTH0_AUTHORIZATION_URL = f"https://{AUTH0_DOMAIN}/authorize"
AUTH0_TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"
AUTH0_USERINFO_URL = f"https://{AUTH0_DOMAIN}/userinfo"
AUTH0_LOGOUT_URL = f"https://{AUTH0_DOMAIN}/v2/logout"

# Security scheme
security = HTTPBearer()

# ============================================================================
# MODELS
# ============================================================================


class Auth0User(BaseModel):
    """Auth0 user model."""

    sub: str  # User ID
    email: str | None = None
    email_verified: bool | None = False
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None
    locale: str | None = None
    updated_at: str | None = None

    # Custom DevSkyy fields
    role: str | None = "user"
    permissions: list[str] = []
    organization: str | None = None
    subscription_tier: str | None = "free"


class TokenPayload(BaseModel):
    """JWT token payload model."""

    sub: str
    aud: list[str]
    iss: str
    exp: int
    iat: int
    scope: str | None = ""
    permissions: list[str] = []

    # Auth0 specific fields
    azp: str | None = None  # Authorized party
    gty: str | None = None  # Grant type

    # Custom DevSkyy fields
    role: str | None = "user"
    organization: str | None = None


# ============================================================================
# OAUTH2 CLIENT & SESSION MANAGEMENT
# ============================================================================


class Auth0OAuth2Client:
    """Auth0 OAuth2 client for FastAPI integration."""

    def __init__(self):
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.domain = AUTH0_DOMAIN

        # OAuth2 client configuration
        self.oauth_client = AsyncOAuth2Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_endpoint=AUTH0_TOKEN_URL,
            authorization_endpoint=AUTH0_AUTHORIZATION_URL,
        )

    def get_authorization_url(self, redirect_uri: str, state: str | None = None) -> str:
        """Generate Auth0 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "audience": AUTH0_AUDIENCE,
        }

        if state:
            params["state"] = state

        query_string = urlencode(params, quote_via=quote_plus)
        return f"{AUTH0_AUTHORIZATION_URL}?{query_string}"

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                AUTH0_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to exchange code for token: {response.text}",
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Get user information from Auth0."""
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(AUTH0_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get user info from Auth0"
                )

            return response.json()

    def get_logout_url(self, return_to: str) -> str:
        """Generate Auth0 logout URL."""
        params = {"returnTo": return_to, "client_id": self.client_id}

        query_string = urlencode(params, quote_via=quote_plus)
        return f"{AUTH0_LOGOUT_URL}?{query_string}"


# Global OAuth2 client instance
auth0_oauth_client = Auth0OAuth2Client()

# ============================================================================
# AUTH0 MANAGEMENT CLIENT
# ============================================================================


class Auth0Client:
    """Auth0 Management API client."""

    def __init__(self):
        self.domain = AUTH0_DOMAIN
        self.client_id = AUTH0_CLIENT_ID
        self.client_secret = AUTH0_CLIENT_SECRET
        self.management_token = None
        self.token_expires_at = None

    async def get_management_token(self) -> str:
        """Get Auth0 Management API token."""
        if (
            self.management_token
            and self.token_expires_at
            and datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)
        ):
            return self.management_token

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.post(
                f"https://{self.domain}/oauth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"https://{self.domain}/api/v2/",
                    "grant_type": "client_credentials",
                },
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get Auth0 management token"
                )

            data = response.json()
            self.management_token = data["access_token"]
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])

            return self.management_token

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user from Auth0."""
        token = await self.get_management_token()

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}", headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 404:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user from Auth0"
                )

            return response.json()

    async def update_user(self, user_id: str, user_data: dict[str, Any]) -> dict[str, Any]:
        """Update user in Auth0."""
        token = await self.get_management_token()

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.patch(
                f"https://{self.domain}/api/v2/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=user_data,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user in Auth0"
                )

            return response.json()

    async def get_user_permissions(self, user_id: str) -> list[str]:
        """Get user permissions from Auth0."""
        token = await self.get_management_token()

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            response = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}/permissions",
                headers={"Authorization": f"Bearer {token}"},
            )

            if response.status_code != 200:
                return []

            permissions_data = response.json()
            return [perm["permission_name"] for perm in permissions_data]


# Global Auth0 client instance
auth0_client = Auth0Client()

# ============================================================================
# JWT VERIFICATION
# ============================================================================


@lru_cache(maxsize=1)
def get_auth0_public_key():
    """Get Auth0 public key for JWT verification."""
    try:
        response = httpx.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to get Auth0 public key: {sanitize_for_log(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service unavailable"
        )


def verify_jwt_token(token: str) -> TokenPayload:
    """Verify Auth0 JWT token with proper key conversion."""
    try:
        # Get public key
        jwks = get_auth0_public_key()

        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")

        if not key_id:
            raise JWTError("Token missing key ID")

        # Find the correct key
        jwk = None
        for key in jwks["keys"]:
            if key["kid"] == key_id:
                jwk = key
                break

        if not jwk:
            raise JWTError("Unable to find appropriate key")

        # Convert JWK to RSA key for verification
        # The jose library expects the key in a specific format
        rsa_key = RSAKey(jwk, algorithm="RS256")

        # Verify and decode token
        payload = jwt.decode(
            token, rsa_key, algorithms=AUTH0_ALGORITHMS, audience=AUTH0_AUDIENCE, issuer=f"https://{AUTH0_DOMAIN}/"
        )

        return TokenPayload(**payload)

    except JWTError as e:
        logger.warning(f"JWT verification failed: {sanitize_for_log(str(e))}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {sanitize_for_log(str(e))}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service error")


# ============================================================================
# DEPENDENCIES
# ============================================================================


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Auth0User:
    """Get current authenticated user."""
    # Verify token
    token_payload = verify_jwt_token(credentials.credentials)

    # Get user details from Auth0
    try:
        user_data = await auth0_client.get_user(token_payload.sub)

        # Get user permissions
        permissions = await auth0_client.get_user_permissions(token_payload.sub)

        # Create user object
        user = Auth0User(
            sub=token_payload.sub,
            email=user_data.get("email"),
            email_verified=user_data.get("email_verified", False),
            name=user_data.get("name"),
            given_name=user_data.get("given_name"),
            family_name=user_data.get("family_name"),
            picture=user_data.get("picture"),
            locale=user_data.get("locale"),
            updated_at=user_data.get("updated_at"),
            permissions=permissions,
            role=user_data.get("app_metadata", {}).get("role", "user"),
            organization=user_data.get("app_metadata", {}).get("organization"),
            subscription_tier=user_data.get("app_metadata", {}).get("subscription_tier", "free"),
        )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user information")


async def get_current_admin_user(current_user: Auth0User = Depends(get_current_user)) -> Auth0User:
    """Get current user and verify admin permissions."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    return current_user


def require_permissions(required_permissions: list[str]):
    """Dependency factory for permission-based access control."""

    def permission_checker(current_user: Auth0User = Depends(get_current_user)) -> Auth0User:
        user_permissions = set(current_user.permissions)
        required_permissions_set = set(required_permissions)

        # Check if user has all required permissions
        if not required_permissions_set.issubset(user_permissions):
            missing_permissions = required_permissions_set - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}",
            )

        return current_user

    return permission_checker


def require_scope(required_scope: str):
    """Dependency factory for scope-based access control."""

    def scope_checker(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenPayload:
        token_payload = verify_jwt_token(credentials.credentials)

        # Check if token has required scope
        token_scopes = token_payload.scope.split() if token_payload.scope else []

        if required_scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=f"Required scope '{required_scope}' not found in token"
            )

        return token_payload

    return scope_checker


# ============================================================================
# JWT TOKEN INTEGRATION (DevSkyy + Auth0 Hybrid)
# ============================================================================


def create_devskyy_jwt_token(user_data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create DevSkyy JWT token with Auth0 user data."""
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=30)

    # Create payload with Auth0 user data
    payload = {
        "sub": user_data.get("sub"),  # Auth0 user ID
        "email": user_data.get("email"),
        "name": user_data.get("name"),
        "picture": user_data.get("picture"),
        "email_verified": user_data.get("email_verified", False),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "devskyy-platform",
        "aud": "devskyy-api",
        "token_type": "access",
        "auth_provider": "auth0",
    }

    # Ensure secret key is properly formatted
    secret_key = DEVSKYY_SECRET_KEY
    if not secret_key:
        raise ValueError("DEVSKYY_SECRET_KEY is not configured")

    # Sign with DevSkyy secret key for compatibility
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=DEVSKYY_JWT_ALGORITHM)
    return encoded_jwt


def create_devskyy_refresh_token(user_data: dict[str, Any]) -> str:
    """Create DevSkyy refresh token."""
    expire = datetime.utcnow() + timedelta(days=30)

    payload = {
        "sub": user_data.get("sub"),
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "iss": "devskyy-platform",
        "aud": "devskyy-api",
        "token_type": "refresh",
        "auth_provider": "auth0",
    }

    # Ensure secret key is properly formatted
    secret_key = DEVSKYY_SECRET_KEY
    if not secret_key:
        raise ValueError("DEVSKYY_SECRET_KEY is not configured")

    encoded_jwt = jwt.encode(payload, secret_key, algorithm=DEVSKYY_JWT_ALGORITHM)
    return encoded_jwt


def verify_devskyy_jwt_token(token: str) -> dict[str, Any]:
    """Verify DevSkyy JWT token (compatible with existing system)."""
    try:
        # Ensure secret key is properly formatted
        secret_key = DEVSKYY_SECRET_KEY
        if not secret_key:
            raise ValueError("DEVSKYY_SECRET_KEY is not configured")

        # Verify JWT signature, audience, issuer, and expiration
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[DEVSKYY_JWT_ALGORITHM],
            audience="devskyy-api",
            issuer="devskyy-platform",
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
                "require_exp": True,
                "require_aud": True,
                "require_iss": True,
            },
        )
        return payload
    except JWTError as e:
        logger.warning(f"DevSkyy JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


async def log_auth_event(
    event_type: str,
    user_id: str | None = None,
    request: Request | None = None,
    details: dict[str, Any] | None = None,
):
    """Log authentication events for monitoring."""
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None,
        "details": details or {},
    }

    logger.info(f"AUTH_EVENT: {json.dumps(event_data)}")


def get_auth0_login_url(redirect_uri: str, state: str | None = None, scope: str = "openid profile email") -> str:
    """Generate Auth0 login URL."""
    params = {
        "response_type": "code",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "audience": AUTH0_AUDIENCE,
    }

    if state:
        params["state"] = state

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://{AUTH0_DOMAIN}/authorize?{query_string}"


# ============================================================================
# HEALTH CHECK
# ============================================================================


async def auth0_health_check() -> dict[str, Any]:
    """Check Auth0 service health."""
    try:
        # Test JWKS endpoint
        response = httpx.get(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json", timeout=5.0)
        jwks_healthy = response.status_code == 200

        # Test Management API (if credentials available)
        management_healthy = False
        if AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET:
            try:
                await auth0_client.get_management_token()
                management_healthy = True
            except Exception as e:
                logger.warning(f"Handled exception: {e}")

        return {
            "status": "healthy" if jwks_healthy else "unhealthy",
            "jwks_endpoint": "healthy" if jwks_healthy else "unhealthy",
            "management_api": "healthy" if management_healthy else "degraded",
            "domain": AUTH0_DOMAIN,
            "audience": AUTH0_AUDIENCE,
        }

    except Exception as e:
        logger.error(f"Auth0 health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "domain": AUTH0_DOMAIN, "audience": AUTH0_AUDIENCE}
