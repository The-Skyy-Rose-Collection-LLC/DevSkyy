"""
Auth0 Integration for DevSkyy Enterprise Platform
Enterprise-grade authentication with Auth0 for unicorn-ready scaling
"""

import os
import json
import httpx
from typing import Dict, List, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta
import logging

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Auth0 Configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "devskyy.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://api.devskyy.com")
AUTH0_ALGORITHMS = ["RS256"]
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")

# Security scheme
security = HTTPBearer()

# ============================================================================
# MODELS
# ============================================================================

class Auth0User(BaseModel):
    """Auth0 user model."""
    sub: str  # User ID
    email: Optional[str] = None
    email_verified: Optional[bool] = False
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    updated_at: Optional[str] = None
    
    # Custom DevSkyy fields
    role: Optional[str] = "user"
    permissions: List[str] = []
    organization: Optional[str] = None
    subscription_tier: Optional[str] = "free"

class TokenPayload(BaseModel):
    """JWT token payload model."""
    sub: str
    aud: List[str]
    iss: str
    exp: int
    iat: int
    scope: Optional[str] = ""
    permissions: List[str] = []
    
    # Auth0 specific fields
    azp: Optional[str] = None  # Authorized party
    gty: Optional[str] = None  # Grant type
    
    # Custom DevSkyy fields
    role: Optional[str] = "user"
    organization: Optional[str] = None

# ============================================================================
# AUTH0 CLIENT
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
        if (self.management_token and self.token_expires_at and 
            datetime.utcnow() < self.token_expires_at - timedelta(minutes=5)):
            return self.management_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self.domain}/oauth/token",
                json={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "audience": f"https://{self.domain}/api/v2/",
                    "grant_type": "client_credentials"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get Auth0 management token"
                )
            
            data = response.json()
            self.management_token = data["access_token"]
            self.token_expires_at = datetime.utcnow() + timedelta(seconds=data["expires_in"])
            
            return self.management_token
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user from Auth0."""
        token = await self.get_management_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to get user from Auth0"
                )
            
            return response.json()
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user in Auth0."""
        token = await self.get_management_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"https://{self.domain}/api/v2/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                json=user_data
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update user in Auth0"
                )
            
            return response.json()
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions from Auth0."""
        token = await self.get_management_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://{self.domain}/api/v2/users/{user_id}/permissions",
                headers={"Authorization": f"Bearer {token}"}
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
        logger.error(f"Failed to get Auth0 public key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )

def verify_jwt_token(token: str) -> TokenPayload:
    """Verify Auth0 JWT token."""
    try:
        # Get public key
        jwks = get_auth0_public_key()
        
        # Decode token header to get key ID
        unverified_header = jwt.get_unverified_header(token)
        key_id = unverified_header.get("kid")
        
        # Find the correct key
        key = None
        for jwk in jwks["keys"]:
            if jwk["kid"] == key_id:
                key = jwk
                break
        
        if not key:
            raise JWTError("Unable to find appropriate key")
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            key,
            algorithms=AUTH0_ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        
        return TokenPayload(**payload)
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Auth0User:
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
            subscription_tier=user_data.get("app_metadata", {}).get("subscription_tier", "free")
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

async def get_current_admin_user(
    current_user: Auth0User = Depends(get_current_user)
) -> Auth0User:
    """Get current user and verify admin permissions."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user

def require_permissions(required_permissions: List[str]):
    """Dependency factory for permission-based access control."""
    def permission_checker(current_user: Auth0User = Depends(get_current_user)) -> Auth0User:
        user_permissions = set(current_user.permissions)
        required_permissions_set = set(required_permissions)
        
        # Check if user has all required permissions
        if not required_permissions_set.issubset(user_permissions):
            missing_permissions = required_permissions_set - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker

def require_scope(required_scope: str):
    """Dependency factory for scope-based access control."""
    def scope_checker(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> TokenPayload:
        token_payload = verify_jwt_token(credentials.credentials)
        
        # Check if token has required scope
        token_scopes = token_payload.scope.split() if token_payload.scope else []
        
        if required_scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required scope '{required_scope}' not found in token"
            )
        
        return token_payload
    
    return scope_checker

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def log_auth_event(
    event_type: str,
    user_id: Optional[str] = None,
    request: Optional[Request] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log authentication events for monitoring."""
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": request.client.host if request else None,
        "user_agent": request.headers.get("user-agent") if request else None,
        "details": details or {}
    }
    
    logger.info(f"AUTH_EVENT: {json.dumps(event_data)}")

def get_auth0_login_url(
    redirect_uri: str,
    state: Optional[str] = None,
    scope: str = "openid profile email"
) -> str:
    """Generate Auth0 login URL."""
    params = {
        "response_type": "code",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "audience": AUTH0_AUDIENCE
    }
    
    if state:
        params["state"] = state
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"https://{AUTH0_DOMAIN}/authorize?{query_string}"

# ============================================================================
# HEALTH CHECK
# ============================================================================

async def auth0_health_check() -> Dict[str, Any]:
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
            except:
                pass
        
        return {
            "status": "healthy" if jwks_healthy else "unhealthy",
            "jwks_endpoint": "healthy" if jwks_healthy else "unhealthy",
            "management_api": "healthy" if management_healthy else "degraded",
            "domain": AUTH0_DOMAIN,
            "audience": AUTH0_AUDIENCE
        }
        
    except Exception as e:
        logger.error(f"Auth0 health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "domain": AUTH0_DOMAIN,
            "audience": AUTH0_AUDIENCE
        }
