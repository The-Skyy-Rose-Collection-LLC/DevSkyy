import base64
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import aiohttp
from cryptography.fernet import Fernet

from api_integration.discovery_engine import AuthenticationType
from infrastructure.redis_manager import redis_manager


"""
API Authentication & Rate Limiting Manager
Standardized authentication handling and intelligent rate limiting for fashion e-commerce APIs
Supports OAuth2, API keys, JWT, and custom authentication methods
"""

logger = logging.getLogger(__name__)


class TokenStatus(Enum):
    """Token status enumeration"""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    PENDING = "pending"


@dataclass
class AuthCredentials:
    """Authentication credentials storage"""

    api_id: str
    auth_type: AuthenticationType
    credentials: dict[str, Any]
    expires_at: datetime | None = None
    refresh_token: str | None = None
    scopes: list[str] = None
    created_at: datetime = None
    last_used: datetime = None
    usage_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.scopes is None:
            self.scopes = []

    def is_expired(self) -> bool:
        """Check if credentials are expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage"""
        data = asdict(self)
        data["auth_type"] = self.auth_type.value
        if self.expires_at:
            data["expires_at"] = self.expires_at.isoformat()
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.last_used:
            data["last_used"] = self.last_used.isoformat()
        return data


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""

    api_id: str
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int
    window_size: int = 60  # seconds

    def get_limit_for_window(self, window_type: str) -> int:
        """Get rate limit for specific window type"""
        limits = {
            "second": self.requests_per_second,
            "minute": self.requests_per_minute,
            "hour": self.requests_per_hour,
            "day": self.requests_per_day,
        }
        return limits.get(window_type, self.requests_per_minute)


class AuthenticationManager:
    """Manages API authentication and credentials"""

    def __init__(self):
        self.credentials_store: dict[str, AuthCredentials] = {}
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # OAuth2 flow storage
        self.oauth_states: dict[str, dict[str, Any]] = {}

        logger.info("Authentication Manager initialized")

    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for credential storage"""
        # In production, this should be stored securely (e.g., AWS KMS, Azure Key Vault)
        return Fernet.generate_key()

    async def store_credentials(
        self,
        api_id: str,
        auth_type: AuthenticationType,
        credentials: dict[str, Any],
        expires_at: datetime | None = None,
        scopes: list[str] | None = None,
    ) -> bool:
        """Store API credentials securely"""

        try:
            # Encrypt sensitive credentials
            encrypted_credentials = self._encrypt_credentials(credentials)

            auth_creds = AuthCredentials(
                api_id=api_id,
                auth_type=auth_type,
                credentials=encrypted_credentials,
                expires_at=expires_at,
                scopes=scopes or [],
            )

            # Store in memory
            self.credentials_store[api_id] = auth_creds

            # Cache in Redis
            cache_key = f"auth_credentials:{api_id}"
            await redis_manager.set(
                cache_key,
                auth_creds.to_dict(),
                ttl=86400,  # 24 hours
                prefix="api_auth",
            )

            logger.info(f"Stored credentials for API: {api_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing credentials for {api_id}: {e}")
            return False

    async def get_credentials(self, api_id: str) -> AuthCredentials | None:
        """Get API credentials"""

        # Check memory first
        if api_id in self.credentials_store:
            creds = self.credentials_store[api_id]
            if not creds.is_expired():
                return creds

        # Check Redis cache
        try:
            cache_key = f"auth_credentials:{api_id}"
            cached_data = await redis_manager.get(cache_key, prefix="api_auth")

            if cached_data:
                # Reconstruct AuthCredentials object
                cached_data["auth_type"] = AuthenticationType(cached_data["auth_type"])
                if cached_data.get("expires_at"):
                    cached_data["expires_at"] = datetime.fromisoformat(cached_data["expires_at"])
                if cached_data.get("created_at"):
                    cached_data["created_at"] = datetime.fromisoformat(cached_data["created_at"])
                if cached_data.get("last_used"):
                    cached_data["last_used"] = datetime.fromisoformat(cached_data["last_used"])

                creds = AuthCredentials(**cached_data)

                if not creds.is_expired():
                    self.credentials_store[api_id] = creds
                    return creds

        except Exception as e:
            logger.error(f"Error retrieving credentials for {api_id}: {e}")

        return None

    def _encrypt_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """Encrypt sensitive credential data"""

        encrypted_creds = {}
        sensitive_fields = [
            "api_key",
            "client_secret",
            "access_token",
            "refresh_token",
            "password",
        ]

        for key, value in credentials.items():
            if key in sensitive_fields and isinstance(value, str):
                encrypted_creds[key] = self.cipher_suite.encrypt(value.encode()).decode()
            else:
                encrypted_creds[key] = value

        return encrypted_creds

    def _decrypt_credentials(self, encrypted_credentials: dict[str, Any]) -> dict[str, Any]:
        """Decrypt credential data"""

        decrypted_creds = {}
        sensitive_fields = [
            "api_key",
            "client_secret",
            "access_token",
            "refresh_token",
            "password",
        ]

        for key, value in encrypted_credentials.items():
            if key in sensitive_fields and isinstance(value, str):
                try:
                    decrypted_creds[key] = self.cipher_suite.decrypt(value.encode()).decode()
                except Exception:
                    # If decryption fails, assume it's already decrypted
                    decrypted_creds[key] = value
            else:
                decrypted_creds[key] = value

        return decrypted_creds

    async def get_auth_headers(self, api_id: str) -> dict[str, str]:
        """Get authentication headers for API request"""

        credentials = await self.get_credentials(api_id)
        if not credentials:
            return {}

        decrypted_creds = self._decrypt_credentials(credentials.credentials)

        if credentials.auth_type == AuthenticationType.API_KEY:
            return await self._get_api_key_headers(decrypted_creds)
        elif credentials.auth_type == AuthenticationType.BEARER_TOKEN:
            return await self._get_bearer_token_headers(decrypted_creds)
        elif credentials.auth_type == AuthenticationType.OAUTH2:
            return await self._get_oauth2_headers(decrypted_creds)
        elif credentials.auth_type == AuthenticationType.JWT:
            return await self._get_jwt_headers(decrypted_creds)
        elif credentials.auth_type == AuthenticationType.BASIC_AUTH:
            return await self._get_basic_auth_headers(decrypted_creds)

        return {}

    async def _get_api_key_headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Get API key authentication headers"""

        api_key = credentials.get("api_key")
        header_name = credentials.get("header_name", "X-API-Key")

        if api_key:
            return {header_name: api_key}

        return {}

    async def _get_bearer_token_headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Get Bearer token authentication headers"""

        access_token = credentials.get("access_token")

        if access_token:
            return {"Authorization": f"Bearer {access_token}"}

        return {}

    async def _get_oauth2_headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Get OAuth2 authentication headers"""

        access_token = credentials.get("access_token")

        if access_token:
            return {"Authorization": f"Bearer {access_token}"}

        return {}

    async def _get_jwt_headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Get JWT authentication headers"""

        jwt_token = credentials.get("jwt_token")

        if jwt_token:
            return {"Authorization": f"Bearer {jwt_token}"}

        return {}

    async def _get_basic_auth_headers(self, credentials: dict[str, Any]) -> dict[str, str]:
        """Get Basic authentication headers"""

        username = credentials.get("username")
        password = credentials.get("password")

        if username and password:
            auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {auth_string}"}

        return {}

    async def initiate_oauth2_flow(
        self,
        api_id: str,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        authorization_url: str,
    ) -> tuple[str, str]:
        """Initiate OAuth2 authorization flow"""

        # Generate state parameter for security
        state = secrets.token_urlsafe(32)

        # Store OAuth2 flow data
        self.oauth_states[state] = {
            "api_id": api_id,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scopes": scopes,
            "created_at": datetime.now(),
        }

        # Build authorization URL
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "response_type": "code",
        }

        auth_url = f"{authorization_url}?{urlencode(params)}"

        logger.info(f"Initiated OAuth2 flow for API: {api_id}")
        return auth_url, state

    async def complete_oauth2_flow(
        self, state: str, authorization_code: str, token_url: str, client_secret: str
    ) -> bool:
        """Complete OAuth2 authorization flow"""

        if state not in self.oauth_states:
            logger.error(f"Invalid OAuth2 state: {state}")
            return False

        oauth_data = self.oauth_states[state]

        try:
            # Exchange authorization code for access token
            token_data = {
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": oauth_data["redirect_uri"],
                "client_id": oauth_data["client_id"],
                "client_secret": client_secret,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=token_data) as response:
                    if response.status == 200:
                        token_response = await response.json()

                        # Store credentials
                        expires_at = None
                        if "expires_in" in token_response:
                            expires_at = datetime.now() + timedelta(seconds=token_response["expires_in"])

                        await self.store_credentials(
                            api_id=oauth_data["api_id"],
                            auth_type=AuthenticationType.OAUTH2,
                            credentials={
                                "access_token": token_response.get("access_token"),
                                "refresh_token": token_response.get("refresh_token"),
                                "token_type": token_response.get("token_type", "Bearer"),
                            },
                            expires_at=expires_at,
                            scopes=oauth_data["scopes"],
                        )

                        # Clean up OAuth state
                        del self.oauth_states[state]

                        logger.info(f"Completed OAuth2 flow for API: {oauth_data['api_id']}")
                        return True
                    else:
                        logger.error(f"OAuth2 token exchange failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error completing OAuth2 flow: {e}")
            return False

    async def refresh_oauth2_token(self, api_id: str, token_url: str, client_id: str, client_secret: str) -> bool:
        """Refresh OAuth2 access token"""

        credentials = await self.get_credentials(api_id)
        if not credentials or credentials.auth_type != AuthenticationType.OAUTH2:
            return False

        decrypted_creds = self._decrypt_credentials(credentials.credentials)
        refresh_token = decrypted_creds.get("refresh_token")

        if not refresh_token:
            return False

        try:
            token_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(token_url, data=token_data) as response:
                    if response.status == 200:
                        token_response = await response.json()

                        # Update credentials
                        expires_at = None
                        if "expires_in" in token_response:
                            expires_at = datetime.now() + timedelta(seconds=token_response["expires_in"])

                        await self.store_credentials(
                            api_id=api_id,
                            auth_type=AuthenticationType.OAUTH2,
                            credentials={
                                "access_token": token_response.get("access_token"),
                                "refresh_token": token_response.get("refresh_token", refresh_token),
                                "token_type": token_response.get("token_type", "Bearer"),
                            },
                            expires_at=expires_at,
                            scopes=credentials.scopes,
                        )

                        logger.info(f"Refreshed OAuth2 token for API: {api_id}")
                        return True
                    else:
                        logger.error(f"OAuth2 token refresh failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Error refreshing OAuth2 token: {e}")
            return False


class RateLimitManager:
    """Manages API rate limiting and quota tracking"""

    def __init__(self):
        self.rate_limits: dict[str, RateLimitRule] = {}
        self.request_history: dict[str, list[float]] = {}

        # Default rate limits for different API categories
        self.default_limits = {
            "free": RateLimitRule("default", 1, 60, 1000, 10000, 10),
            "premium": RateLimitRule("default", 10, 600, 10000, 100000, 50),
            "enterprise": RateLimitRule("default", 50, 3000, 50000, 500000, 100),
        }

        logger.info("Rate Limit Manager initialized")

    async def set_rate_limit(self, api_id: str, rate_limit: RateLimitRule):
        """Set rate limit for specific API"""

        self.rate_limits[api_id] = rate_limit

        # Cache in Redis
        cache_key = f"rate_limit:{api_id}"
        await redis_manager.set(cache_key, asdict(rate_limit), ttl=86400, prefix="api_limits")  # 24 hours

        logger.info(f"Set rate limit for API: {api_id}")

    async def get_rate_limit(self, api_id: str) -> RateLimitRule | None:
        """Get rate limit for API"""

        # Check memory first
        if api_id in self.rate_limits:
            return self.rate_limits[api_id]

        # Check Redis cache
        try:
            cache_key = f"rate_limit:{api_id}"
            cached_data = await redis_manager.get(cache_key, prefix="api_limits")

            if cached_data:
                rate_limit = RateLimitRule(**cached_data)
                self.rate_limits[api_id] = rate_limit
                return rate_limit

        except Exception as e:
            logger.error(f"Error retrieving rate limit for {api_id}: {e}")

        # Return default limit
        return self.default_limits["free"]

    async def can_make_request(self, api_id: str) -> tuple[bool, dict[str, Any]]:
        """Check if request can be made within rate limits"""

        rate_limit = await self.get_rate_limit(api_id)
        if not rate_limit:
            return True, {}

        current_time = time.time()

        # Get request history
        if api_id not in self.request_history:
            self.request_history[api_id] = []

        history = self.request_history[api_id]

        # Clean old requests (older than 1 day)
        cutoff_time = current_time - 86400
        history[:] = [req_time for req_time in history if req_time > cutoff_time]

        # Check different time windows
        windows = {"second": 1, "minute": 60, "hour": 3600, "day": 86400}

        rate_limit_info = {}

        for window_name, window_seconds in windows.items():
            window_start = current_time - window_seconds
            requests_in_window = len([t for t in history if t > window_start])

            limit = rate_limit.get_limit_for_window(window_name)
            remaining = max(0, limit - requests_in_window)

            rate_limit_info[f"{window_name}_limit"] = limit
            rate_limit_info[f"{window_name}_remaining"] = remaining
            rate_limit_info[f"{window_name}_reset"] = int(current_time + window_seconds)

            # If any window is exceeded, deny request
            if requests_in_window >= limit:
                return False, rate_limit_info

        # Check burst limit
        recent_requests = len([t for t in history if t > current_time - 10])  # Last 10 seconds
        if recent_requests >= rate_limit.burst_limit:
            rate_limit_info["burst_limit_exceeded"] = True
            return False, rate_limit_info

        return True, rate_limit_info

    async def record_request(self, api_id: str):
        """Record a successful API request"""

        current_time = time.time()

        if api_id not in self.request_history:
            self.request_history[api_id] = []

        self.request_history[api_id].append(current_time)

        # Keep only last 1000 requests per API
        if len(self.request_history[api_id]) > 1000:
            self.request_history[api_id] = self.request_history[api_id][-1000:]

        # Update Redis cache
        try:
            cache_key = f"request_history:{api_id}"
            await redis_manager.set(
                cache_key,
                self.request_history[api_id][-100:],  # Store last 100 requests
                ttl=86400,
                prefix="api_limits",
            )
        except Exception as e:
            logger.error(f"Error caching request history for {api_id}: {e}")

    async def get_rate_limit_status(self, api_id: str) -> dict[str, Any]:
        """Get current rate limit status for API"""

        can_request, rate_info = await self.can_make_request(api_id)

        return {
            "api_id": api_id,
            "can_make_request": can_request,
            "rate_limit_info": rate_info,
            "total_requests_today": len([t for t in self.request_history.get(api_id, []) if t > time.time() - 86400]),
        }

    async def get_all_rate_limit_status(self) -> dict[str, dict[str, Any]]:
        """Get rate limit status for all APIs"""

        status = {}

        for api_id in self.rate_limits:
            status[api_id] = await self.get_rate_limit_status(api_id)

        return status


# Global instances
auth_manager = AuthenticationManager()
rate_limit_manager = RateLimitManager()
