"""
DevSkyy Application Settings

Centralized, validated configuration using Pydantic Settings.
All settings are loaded from environment variables with validation.

Truth Protocol Compliance:
- Rule #5: No secrets in code (all from env vars)
- Rule #7: Input validation via Pydantic
- Rule #9: Fully documented

Example:
    from core.settings import get_settings

    settings = get_settings()
    print(settings.database_url)
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    All settings are loaded from environment variables.
    Use get_settings() to get a cached singleton instance.

    Attributes:
        environment: Deployment environment (development, staging, production)
        debug: Enable debug mode (auto-disabled in production)
        version: Application version string
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

        secret_key: JWT signing key (required in production)
        database_url: SQLAlchemy async database URL
        redis_url: Redis connection URL for caching

        cors_origins: Comma-separated list of allowed CORS origins
        trusted_hosts: Comma-separated list of trusted hosts

        anthropic_api_key: Claude API key for AI services
        openai_api_key: OpenAI API key (optional)

        db_pool_size: Database connection pool size
        db_max_overflow: Max connections beyond pool_size
        db_pool_timeout: Seconds to wait for connection
        db_pool_recycle: Seconds before recycling connections

        rate_limit_per_minute: API rate limit per IP
        p95_latency_threshold_ms: P95 latency SLO in milliseconds
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # Core Application Settings
    # ==========================================================================

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    version: str = Field(
        default="5.2.0-enterprise",
        description="Application version",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # ==========================================================================
    # Security Settings (Truth Protocol Rule #5)
    # ==========================================================================

    secret_key: str = Field(
        default="",
        description="JWT signing key - MUST be set in production",
    )

    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )

    jwt_access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        le=1440,
        description="Access token expiry in minutes",
    )

    jwt_refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="Refresh token expiry in days",
    )

    # ==========================================================================
    # Database Settings
    # ==========================================================================

    database_url: str = Field(
        default="sqlite+aiosqlite:///./devskyy.db",
        description="SQLAlchemy async database URL",
    )

    db_pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Database connection pool size",
    )

    db_max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Max connections beyond pool_size",
    )

    db_pool_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Seconds to wait for connection",
    )

    db_pool_recycle: int = Field(
        default=1800,
        ge=60,
        le=7200,
        description="Seconds before recycling connections",
    )

    # ==========================================================================
    # Cache Settings
    # ==========================================================================

    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL",
    )

    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Default cache TTL in seconds",
    )

    # ==========================================================================
    # API Settings
    # ==========================================================================

    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173,http://localhost:8080",
        description="Comma-separated CORS origins",
    )

    trusted_hosts: str = Field(
        default="localhost,127.0.0.1,testserver",
        description="Comma-separated trusted hosts",
    )

    rate_limit_per_minute: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="API rate limit per IP per minute",
    )

    # ==========================================================================
    # Performance SLOs (Truth Protocol Rule #12)
    # ==========================================================================

    p95_latency_threshold_ms: int = Field(
        default=200,
        ge=50,
        le=5000,
        description="P95 latency SLO in milliseconds",
    )

    max_request_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum request body size in MB",
    )

    # ==========================================================================
    # AI Service Settings
    # ==========================================================================

    anthropic_api_key: str = Field(
        default="",
        description="Claude API key",
    )

    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (optional)",
    )

    default_ai_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Default AI model for inference",
    )

    # ==========================================================================
    # WordPress Integration
    # ==========================================================================

    wordpress_site_url: str = Field(
        default="",
        description="WordPress site URL",
    )

    wordpress_username: str = Field(
        default="",
        description="WordPress admin username",
    )

    wordpress_app_password: str = Field(
        default="",
        description="WordPress application password",
    )

    # ==========================================================================
    # Validators
    # ==========================================================================

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure secret_key is set in production."""
        environment = info.data.get("environment", "development")
        if environment == "production" and not v:
            raise ValueError(
                "SECRET_KEY must be set in production. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        if not v:
            # Development default - log warning handled elsewhere
            return "dev-only-insecure-key-DO-NOT-USE-IN-PRODUCTION"
        return v

    @field_validator("debug")
    @classmethod
    def validate_debug(cls, v: bool, info) -> bool:
        """Auto-disable debug in production."""
        environment = info.data.get("environment", "development")
        if environment == "production" and v:
            return False
        return v

    # ==========================================================================
    # Computed Properties
    # ==========================================================================

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        """Get trusted hosts as a list."""
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def database_connection_args(self) -> dict:
        """Get database connection arguments based on URL type."""
        if self.database_url.startswith("postgresql"):
            return {
                "pool_size": self.db_pool_size,
                "max_overflow": self.db_max_overflow,
                "pool_timeout": self.db_pool_timeout,
                "pool_recycle": self.db_pool_recycle,
                "pool_pre_ping": True,
            }
        elif self.database_url.startswith("mysql"):
            return {
                "pool_size": self.db_pool_size,
                "max_overflow": self.db_max_overflow,
                "pool_timeout": self.db_pool_timeout,
                "pool_recycle": self.db_pool_recycle,
                "pool_pre_ping": True,
            }
        return {}  # SQLite doesn't use connection pooling


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings singleton.

    Returns:
        Settings: Application settings instance.

    Example:
        settings = get_settings()
        if settings.is_production:
            configure_production_logging()
    """
    return Settings()


# Export for convenience
settings = get_settings()
