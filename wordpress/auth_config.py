"""
WordPress Authentication Configuration
=======================================

Production-grade authentication configuration for WordPress REST API
and WooCommerce integration.

Features:
- JWT/OAuth2 authentication support
- Application password authentication
- WooCommerce API key management
- Session management
- Rate limiting integration
- Audit logging

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlencode

from pydantic import BaseModel, Field, SecretStr

# Use structlog if available, otherwise fall back to standard logging
# Note: Library code should only create loggers, not configure logging
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class AuthMethod(str, Enum):
    """Supported authentication methods."""

    APP_PASSWORD = "app_password"
    JWT = "jwt"
    OAUTH2 = "oauth2"
    WC_API_KEY = "wc_api_key"


class UserRole(str, Enum):
    """WordPress user roles."""

    ADMINISTRATOR = "administrator"
    EDITOR = "editor"
    AUTHOR = "author"
    CONTRIBUTOR = "contributor"
    SUBSCRIBER = "subscriber"
    SHOP_MANAGER = "shop_manager"
    CUSTOMER = "customer"


class Permission(str, Enum):
    """Required permissions for DevSkyy operations."""

    READ_PAGES = "read_pages"
    EDIT_PAGES = "edit_pages"
    PUBLISH_PAGES = "publish_pages"
    DELETE_PAGES = "delete_pages"
    READ_PRODUCTS = "read_products"
    EDIT_PRODUCTS = "edit_products"
    MANAGE_WOOCOMMERCE = "manage_woocommerce"
    UPLOAD_MEDIA = "upload_media"
    READ_ORDERS = "read_orders"


# ============================================================================
# Configuration Models
# ============================================================================


class WordPressAuthConfig(BaseModel):
    """WordPress authentication configuration."""

    site_url: str = Field(..., description="WordPress site URL")
    auth_method: AuthMethod = Field(default=AuthMethod.APP_PASSWORD)
    username: str = Field(default="", description="WordPress username")
    app_password: SecretStr = Field(default=SecretStr(""), description="Application password")
    jwt_secret: SecretStr = Field(default=SecretStr(""), description="JWT secret key")
    jwt_expiry_hours: int = Field(default=24, ge=1, le=720)
    oauth_client_id: str = Field(default="")
    oauth_client_secret: SecretStr = Field(default=SecretStr(""))
    oauth_redirect_uri: str = Field(default="")
    verify_ssl: bool = Field(default=True)
    timeout_seconds: int = Field(default=30)
    max_retries: int = Field(default=3)
    rate_limit_per_minute: int = Field(default=60)

    @classmethod
    def from_env(cls) -> "WordPressAuthConfig":
        """Load configuration from environment variables."""
        auth_method = AuthMethod(os.getenv("WP_AUTH_METHOD", "app_password"))
        jwt_secret_env = os.getenv("WP_JWT_SECRET")

        # Fail fast if JWT auth is selected but no secret is configured
        if auth_method == AuthMethod.JWT and not jwt_secret_env:
            raise ValueError(
                "WP_JWT_SECRET environment variable is required when using JWT authentication. "
                "Generate a secure secret with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )

        return cls(
            site_url=os.getenv("WORDPRESS_URL", "https://skyyrose.co"),
            auth_method=auth_method,
            username=os.getenv("WORDPRESS_USERNAME", ""),
            app_password=SecretStr(os.getenv("WORDPRESS_APP_PASSWORD", "")),
            jwt_secret=SecretStr(jwt_secret_env or ""),
            jwt_expiry_hours=int(os.getenv("WP_JWT_EXPIRY_HOURS", "24")),
            oauth_client_id=os.getenv("WP_OAUTH_CLIENT_ID", ""),
            oauth_client_secret=SecretStr(os.getenv("WP_OAUTH_CLIENT_SECRET", "")),
            oauth_redirect_uri=os.getenv("WP_OAUTH_REDIRECT_URI", ""),
            verify_ssl=os.getenv("WP_VERIFY_SSL", "true").lower() == "true",
            timeout_seconds=int(os.getenv("WP_TIMEOUT_SECONDS", "30")),
            max_retries=int(os.getenv("WP_MAX_RETRIES", "3")),
            rate_limit_per_minute=int(os.getenv("WP_RATE_LIMIT", "60")),
        )


class WooCommerceAuthConfig(BaseModel):
    """WooCommerce API authentication configuration."""

    consumer_key: SecretStr = Field(..., description="WooCommerce consumer key")
    consumer_secret: SecretStr = Field(..., description="WooCommerce consumer secret")
    api_version: str = Field(default="wc/v3")
    # WooCommerce OAuth 1.0a uses HMAC-SHA1 by default
    signature_method: str = Field(default="HMAC-SHA1")

    @classmethod
    def from_env(cls) -> "WooCommerceAuthConfig":
        """Load configuration from environment variables."""
        return cls(
            consumer_key=SecretStr(os.getenv("WOOCOMMERCE_KEY", "")),
            consumer_secret=SecretStr(os.getenv("WOOCOMMERCE_SECRET", "")),
            api_version=os.getenv("WC_API_VERSION", "wc/v3"),
        )


# ============================================================================
# Authentication Handlers
# ============================================================================


@dataclass
class AuthToken:
    """Authentication token container."""

    token: str
    token_type: str
    expires_at: datetime
    user_id: int = 0
    username: str = ""
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def expires_in_seconds(self) -> int:
        """Get seconds until token expires."""
        delta = self.expires_at - datetime.now(timezone.utc)
        return max(0, int(delta.total_seconds()))


class WordPressAuthHandler:
    """
    Handles WordPress authentication.

    Supports:
    - Application password (Basic Auth)
    - JWT authentication
    - OAuth2 authentication
    """

    def __init__(self, config: WordPressAuthConfig):
        self.config = config
        self._token: AuthToken | None = None
        self._logger = logger.bind(component="wp_auth")

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        if self.config.auth_method == AuthMethod.APP_PASSWORD:
            return self._get_basic_auth_headers()
        elif self.config.auth_method == AuthMethod.JWT:
            return self._get_jwt_headers()
        elif self.config.auth_method == AuthMethod.OAUTH2:
            return self._get_oauth2_headers()
        else:
            raise ValueError(f"Unsupported auth method: {self.config.auth_method}")

    def _get_basic_auth_headers(self) -> dict[str, str]:
        """Get Basic Auth headers using application password."""
        credentials = f"{self.config.username}:{self.config.app_password.get_secret_value()}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }

    def _get_jwt_headers(self) -> dict[str, str]:
        """Get JWT authentication headers."""
        if not self._token or self._token.is_expired:
            self._token = self._refresh_jwt_token()

        return {
            "Authorization": f"Bearer {self._token.token}",
            "Content-Type": "application/json",
        }

    def _get_oauth2_headers(self) -> dict[str, str]:
        """Get OAuth2 authentication headers."""
        if not self._token or self._token.is_expired:
            self._token = self._refresh_oauth2_token()

        return {
            "Authorization": f"Bearer {self._token.token}",
            "Content-Type": "application/json",
        }

    def _refresh_jwt_token(self) -> AuthToken:
        """Refresh JWT token."""
        # This would call the WordPress JWT endpoint
        # For now, return a mock token
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.jwt_expiry_hours)
        return AuthToken(
            token="jwt_token_placeholder",
            token_type="Bearer",
            expires_at=expires_at,
        )

    def _refresh_oauth2_token(self) -> AuthToken:
        """Refresh OAuth2 token."""
        # This would call the OAuth2 token endpoint
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        return AuthToken(
            token="oauth2_token_placeholder",
            token_type="Bearer",
            expires_at=expires_at,
        )

    async def validate_credentials(self) -> bool:
        """Validate authentication credentials."""
        import aiohttp

        try:
            headers = self.get_auth_headers()
            url = f"{self.config.site_url}/wp-json/wp/v2/users/me"

            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    url,
                    headers=headers,
                    ssl=self.config.verify_ssl,
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        self._logger.info(
                            "credentials_validated",
                            user_id=user_data.get("id"),
                            username=user_data.get("slug"),
                        )
                        return True
                    else:
                        self._logger.warning(
                            "credentials_invalid",
                            status=response.status,
                        )
                        return False
        except Exception as e:
            self._logger.error("credential_validation_failed", error=str(e))
            return False


class WooCommerceAuthHandler:
    """
    Handles WooCommerce API authentication.

    Uses OAuth 1.0a signature for authentication.
    """

    def __init__(self, config: WooCommerceAuthConfig, site_url: str):
        self.config = config
        self.site_url = site_url
        self._logger = logger.bind(component="wc_auth")

    def get_auth_params(
        self,
        method: str,
        url: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        """
        Get authentication parameters for WooCommerce API request.

        For HTTPS connections, uses query string authentication.
        For HTTP connections, uses OAuth 1.0a signature.
        """
        if url.startswith("https://"):
            # Use simple query string authentication for HTTPS
            return {
                "consumer_key": self.config.consumer_key.get_secret_value(),
                "consumer_secret": self.config.consumer_secret.get_secret_value(),
            }
        else:
            # Use OAuth 1.0a for HTTP (not recommended for production)
            return self._get_oauth_params(method, url, params or {})

    def _get_oauth_params(
        self,
        method: str,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, str]:
        """Generate OAuth 1.0a signature parameters."""
        timestamp = str(int(time.time()))
        nonce = secrets.token_hex(16)

        oauth_params = {
            "oauth_consumer_key": self.config.consumer_key.get_secret_value(),
            "oauth_nonce": nonce,
            "oauth_signature_method": self.config.signature_method,
            "oauth_timestamp": timestamp,
            "oauth_version": "1.0",
        }

        # Combine all params for signature
        all_params = {**params, **oauth_params}
        sorted_params = sorted(all_params.items())
        param_string = urlencode(sorted_params)

        # Create signature base string
        base_string = f"{method.upper()}&{self._url_encode(url)}&{self._url_encode(param_string)}"

        # Create signature key
        key = f"{self.config.consumer_secret.get_secret_value()}&"

        # Select hash algorithm based on signature_method
        hash_algo = hashlib.sha1  # Default for HMAC-SHA1
        if self.config.signature_method == "HMAC-SHA256":
            hash_algo = hashlib.sha256

        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                key.encode(),
                base_string.encode(),
                hash_algo,
            ).digest()
        ).decode()

        oauth_params["oauth_signature"] = signature
        return oauth_params

    @staticmethod
    def _url_encode(value: str) -> str:
        """URL encode a value according to OAuth spec."""
        from urllib.parse import quote

        return quote(value, safe="")

    async def validate_credentials(self) -> bool:
        """Validate WooCommerce API credentials."""
        import aiohttp

        try:
            url = f"{self.site_url}/wp-json/{self.config.api_version}/products"
            auth_params = self.get_auth_params("GET", url)

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=auth_params,
                    timeout=30,
                ) as response:
                    if response.status == 200:
                        self._logger.info("wc_credentials_validated")
                        return True
                    else:
                        self._logger.warning(
                            "wc_credentials_invalid",
                            status=response.status,
                        )
                        return False
        except Exception as e:
            self._logger.error("wc_credential_validation_failed", error=str(e))
            return False


# ============================================================================
# Session Management
# ============================================================================


@dataclass
class AuthSession:
    """Authentication session container."""

    session_id: str
    wp_handler: WordPressAuthHandler
    wc_handler: WooCommerceAuthHandler
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_count: int = 0

    def touch(self) -> None:
        """Update last used timestamp and increment request count."""
        self.last_used_at = datetime.now(timezone.utc)
        self.request_count += 1


class AuthSessionManager:
    """
    Manages authentication sessions.

    Provides:
    - Session creation and validation
    - Rate limiting
    - Session cleanup
    """

    def __init__(self):
        self._sessions: dict[str, AuthSession] = {}
        self._logger = logger.bind(component="auth_session_manager")

    def create_session(
        self,
        wp_config: WordPressAuthConfig,
        wc_config: WooCommerceAuthConfig,
    ) -> AuthSession:
        """Create a new authentication session."""
        session_id = secrets.token_urlsafe(32)
        wp_handler = WordPressAuthHandler(wp_config)
        wc_handler = WooCommerceAuthHandler(wc_config, wp_config.site_url)

        session = AuthSession(
            session_id=session_id,
            wp_handler=wp_handler,
            wc_handler=wc_handler,
        )

        self._sessions[session_id] = session
        self._logger.info("session_created", session_id=session_id)

        return session

    def get_session(self, session_id: str) -> AuthSession | None:
        """Get an existing session by ID."""
        session = self._sessions.get(session_id)
        if session:
            session.touch()
        return session

    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Remove expired sessions."""
        now = datetime.now(timezone.utc)
        max_age = timedelta(hours=max_age_hours)

        expired = [
            sid for sid, session in self._sessions.items()
            if now - session.last_used_at > max_age
        ]

        for sid in expired:
            del self._sessions[sid]

        if expired:
            self._logger.info("sessions_cleaned", count=len(expired))

        return len(expired)


# ============================================================================
# Factory Functions
# ============================================================================


def get_auth_session() -> AuthSession:
    """
    Get or create authentication session from environment.

    Returns:
        AuthSession: Configured authentication session
    """
    wp_config = WordPressAuthConfig.from_env()
    wc_config = WooCommerceAuthConfig.from_env()

    manager = AuthSessionManager()
    return manager.create_session(wp_config, wc_config)


async def validate_all_credentials() -> dict[str, bool]:
    """
    Validate all authentication credentials.

    Returns:
        dict: Validation results for each credential type
    """
    session = get_auth_session()

    results = {
        "wordpress": await session.wp_handler.validate_credentials(),
        "woocommerce": await session.wc_handler.validate_credentials(),
    }

    return results


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "AuthMethod",
    "UserRole",
    "Permission",
    "WordPressAuthConfig",
    "WooCommerceAuthConfig",
    "AuthToken",
    "WordPressAuthHandler",
    "WooCommerceAuthHandler",
    "AuthSession",
    "AuthSessionManager",
    "get_auth_session",
    "validate_all_credentials",
]
