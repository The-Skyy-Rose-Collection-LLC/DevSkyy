"""
DevSkyy Unified Configuration System
Enterprise-grade configuration with clear precedence and validation

Configuration Precedence (highest to lowest):
1. Environment variables
2. .env file
3. Config class defaults
4. Runtime overrides

Per Truth Protocol Rule #1: Never guess - Verify all configurations
Per Truth Protocol Rule #5: No secrets in code - Environment variables only
Per Truth Protocol Rule #11: Verified languages - Python 3.11.* only
"""

import logging
import os
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# BASE CONFIGURATION MODELS
# ============================================================================


class DatabaseConfig(BaseModel):
    """Database configuration with validation"""

    url: str = Field(default="sqlite+aiosqlite:///./devskyy.db")
    pool_size: int = Field(default=5, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_timeout: int = Field(default=30, ge=5, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=7200)
    pool_pre_ping: bool = Field(default=True)
    echo: bool = Field(default=False)

    class Config:
        frozen = True  # Immutable after creation


class SecurityConfig(BaseModel):
    """Security configuration with validation"""

    secret_key: str
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=30)
    password_hash_algorithm: str = Field(default="argon2id")
    min_password_length: int = Field(default=12, ge=8, le=128)
    require_special_chars: bool = Field(default=True)
    max_login_attempts: int = Field(default=5, ge=3, le=10)
    lockout_duration_minutes: int = Field(default=30, ge=5, le=1440)

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return v

    class Config:
        frozen = True


class LoggingConfig(BaseModel):
    """Logging configuration with validation"""

    level: str = Field(default="INFO")
    format: str = Field(default="json")
    enable_console: bool = Field(default=True)
    enable_file: bool = Field(default=True)
    log_dir: Path = Field(default=Path("logs"))
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=20)
    enable_correlation_id: bool = Field(default=True)
    sanitize_sensitive_data: bool = Field(default=True)

    class Config:
        frozen = True


class RedisConfig(BaseModel):
    """Redis configuration with validation"""

    url: str = Field(default="redis://localhost:6379")
    max_connections: int = Field(default=50, ge=10, le=200)
    socket_timeout: int = Field(default=5, ge=1, le=30)
    socket_connect_timeout: int = Field(default=5, ge=1, le=30)
    retry_on_timeout: bool = Field(default=True)
    default_ttl: int = Field(default=3600, ge=60, le=86400)

    class Config:
        frozen = True


class CORSConfig(BaseModel):
    """CORS configuration with validation"""

    origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    allow_credentials: bool = Field(default=True)
    allow_methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allow_headers: List[str] = Field(default_factory=lambda: ["Content-Type", "Authorization", "X-Requested-With"])
    max_age: int = Field(default=600, ge=0, le=86400)

    class Config:
        frozen = True


class PerformanceConfig(BaseModel):
    """Performance configuration with validation"""

    max_content_length_mb: int = Field(default=16, ge=1, le=100)
    request_timeout_seconds: int = Field(default=300, ge=30, le=3600)
    worker_count: int = Field(default=4, ge=1, le=32)
    enable_gzip: bool = Field(default=True)
    gzip_minimum_size: int = Field(default=1000, ge=100, le=10000)

    class Config:
        frozen = True


class AIConfig(BaseModel):
    """AI services configuration"""

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_model: str = Field(default="claude-sonnet-4-5")
    max_tokens: int = Field(default=4096, ge=256, le=200000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout_seconds: int = Field(default=120, ge=10, le=300)

    class Config:
        frozen = True


# ============================================================================
# UNIFIED CONFIGURATION CLASS
# ============================================================================


class UnifiedConfig:
    """
    Unified configuration system for DevSkyy Platform

    Configuration precedence:
    1. Environment variables (highest)
    2. .env file
    3. Config class defaults
    4. Runtime overrides (lowest)

    Usage:
        config = UnifiedConfig()
        db_url = config.database.url
        secret = config.security.secret_key
    """

    def __init__(self, environment: Optional[str] = None):
        """
        Initialize unified configuration

        Args:
            environment: Environment name (development, production, testing)
        """
        self.environment = environment or os.getenv("ENVIRONMENT", "development").lower()
        self.version = "5.1.0-enterprise"

        # Validate environment
        if self.environment not in ["development", "production", "testing"]:
            raise ValueError(f"Invalid environment: {self.environment}")

        # Load configurations
        self._load_database_config()
        self._load_security_config()
        self._load_logging_config()
        self._load_redis_config()
        self._load_cors_config()
        self._load_performance_config()
        self._load_ai_config()

        # Log configuration loaded
        logger.info(
            f"✅ Unified configuration loaded - Environment: {self.environment}, "
            f"Version: {self.version}"
        )

    def _load_database_config(self):
        """Load and validate database configuration"""
        # Build database URL with precedence
        db_url = self._get_database_url()

        self.database = DatabaseConfig(
            url=db_url,
            pool_size=int(os.getenv("DB_POOL_SIZE", 5)),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", 10)),
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", 30)),
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", 3600)),
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "true").lower() == "true",
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )

    def _get_database_url(self) -> str:
        """
        Get database URL with fallback logic

        Precedence:
        1. DATABASE_URL
        2. NEON_DATABASE_URL (Serverless PostgreSQL)
        3. SUPABASE_DATABASE_URL
        4. PLANETSCALE_DATABASE_URL
        5. Individual DB credentials
        6. SQLite (default)
        """
        # Check for explicit DATABASE_URL (highest priority)
        if db_url := os.getenv("DATABASE_URL"):
            return self._normalize_database_url(db_url)

        # Check for Neon (Serverless PostgreSQL - Recommended)
        if neon_url := os.getenv("NEON_DATABASE_URL"):
            return self._normalize_database_url(neon_url)

        # Check for Supabase (PostgreSQL with real-time)
        if supabase_url := os.getenv("SUPABASE_DATABASE_URL"):
            return self._normalize_database_url(supabase_url)

        # Check for PlanetScale (MySQL)
        if planetscale_url := os.getenv("PLANETSCALE_DATABASE_URL"):
            return self._normalize_database_url(planetscale_url)

        # Check for individual PostgreSQL credentials
        if all([
            os.getenv("DB_HOST"),
            os.getenv("DB_USER"),
            os.getenv("DB_PASSWORD"),
            os.getenv("DB_NAME")
        ]):
            return self._build_postgres_url()

        # Default: SQLite (development/testing)
        return "sqlite+aiosqlite:///./devskyy.db"

    def _normalize_database_url(self, url: str) -> str:
        """
        Normalize database URL to use async drivers

        PostgreSQL: postgresql:// → postgresql+asyncpg://
        MySQL: mysql:// → mysql+aiomysql://
        SQLite: sqlite:// → sqlite+aiosqlite://
        """
        if url.startswith("postgres://"):
            # Heroku/Railway format
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("mysql://") and "+aiomysql" not in url:
            url = url.replace("mysql://", "mysql+aiomysql://", 1)
        elif url.startswith("sqlite://") and "+aiosqlite" not in url:
            url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

        return url

    def _build_postgres_url(self) -> str:
        """Build PostgreSQL URL from individual credentials"""
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")

        # URL encode password to handle special characters
        encoded_password = quote_plus(password)

        return f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{database}"

    def _load_security_config(self):
        """Load and validate security configuration"""
        # Get SECRET_KEY with validation
        secret_key = os.getenv("SECRET_KEY")

        if not secret_key:
            if self.environment == "production":
                raise ValueError(
                    "SECRET_KEY environment variable must be set in production. "
                    "Generate a secure key using: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
                )
            else:
                # Development/testing only
                secret_key = "dev-only-insecure-key-DO-NOT-USE-IN-PRODUCTION-" + secrets.token_urlsafe(16)
                logger.warning(
                    "⚠️  Using auto-generated SECRET_KEY for development. "
                    "Set SECRET_KEY environment variable before deploying to production!"
                )

        self.security = SecurityConfig(
            secret_key=secret_key,
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7)),
            password_hash_algorithm=os.getenv("PASSWORD_HASH_ALGORITHM", "argon2id"),
            min_password_length=int(os.getenv("MIN_PASSWORD_LENGTH", 12)),
            require_special_chars=os.getenv("REQUIRE_SPECIAL_CHARS", "true").lower() == "true",
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", 5)),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", 30))
        )

    def _load_logging_config(self):
        """Load and validate logging configuration"""
        self.logging = LoggingConfig(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv("LOG_FORMAT", "json"),
            enable_console=os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true",
            enable_file=os.getenv("LOG_ENABLE_FILE", "true").lower() == "true",
            log_dir=Path(os.getenv("LOG_DIR", "logs")),
            max_file_size_mb=int(os.getenv("LOG_MAX_FILE_SIZE_MB", 10)),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", 5)),
            enable_correlation_id=os.getenv("LOG_ENABLE_CORRELATION_ID", "true").lower() == "true",
            sanitize_sensitive_data=os.getenv("LOG_SANITIZE_SENSITIVE", "true").lower() == "true"
        )

    def _load_redis_config(self):
        """Load and validate Redis configuration"""
        self.redis = RedisConfig(
            url=os.getenv("REDIS_URL", "redis://localhost:6379"),
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 50)),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", 5)),
            socket_connect_timeout=int(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", 5)),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
            default_ttl=int(os.getenv("REDIS_DEFAULT_TTL", 3600))
        )

    def _load_cors_config(self):
        """Load and validate CORS configuration"""
        origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
        origins = [origin.strip() for origin in origins_str.split(",")]

        methods_str = os.getenv("CORS_METHODS", "GET,POST,PUT,DELETE,OPTIONS")
        methods = [method.strip() for method in methods_str.split(",")]

        headers_str = os.getenv("CORS_HEADERS", "Content-Type,Authorization,X-Requested-With")
        headers = [header.strip() for header in headers_str.split(",")]

        self.cors = CORSConfig(
            origins=origins,
            allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            allow_methods=methods,
            allow_headers=headers,
            max_age=int(os.getenv("CORS_MAX_AGE", 600))
        )

    def _load_performance_config(self):
        """Load and validate performance configuration"""
        self.performance = PerformanceConfig(
            max_content_length_mb=int(os.getenv("MAX_CONTENT_LENGTH_MB", 16)),
            request_timeout_seconds=int(os.getenv("REQUEST_TIMEOUT_SECONDS", 300)),
            worker_count=int(os.getenv("WORKER_COUNT", 4)),
            enable_gzip=os.getenv("ENABLE_GZIP", "true").lower() == "true",
            gzip_minimum_size=int(os.getenv("GZIP_MINIMUM_SIZE", 1000))
        )

    def _load_ai_config(self):
        """Load and validate AI configuration"""
        self.ai = AIConfig(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            default_model=os.getenv("AI_DEFAULT_MODEL", "claude-sonnet-4-5"),
            max_tokens=int(os.getenv("AI_MAX_TOKENS", 4096)),
            temperature=float(os.getenv("AI_TEMPERATURE", 0.7)),
            timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", 120))
        )

    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment"""
        return self.environment == "testing"

    def get_trusted_hosts(self) -> List[str]:
        """Get list of trusted hosts based on environment"""
        if self.is_production():
            hosts_str = os.getenv("TRUSTED_HOSTS", "theskyy-rose-collection.com")
        else:
            hosts_str = os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1,testserver")

        return [host.strip() for host in hosts_str.split(",")]

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (excluding sensitive data)"""
        return {
            "environment": self.environment,
            "version": self.version,
            "database": {
                "provider": self._detect_database_provider(),
                "pool_size": self.database.pool_size,
                "echo": self.database.echo
            },
            "security": {
                "algorithm": self.security.algorithm,
                "access_token_expire_minutes": self.security.access_token_expire_minutes,
                "password_hash_algorithm": self.security.password_hash_algorithm
            },
            "logging": {
                "level": self.logging.level,
                "format": self.logging.format,
                "enable_correlation_id": self.logging.enable_correlation_id
            },
            "redis": {
                "max_connections": self.redis.max_connections,
                "default_ttl": self.redis.default_ttl
            },
            "performance": {
                "worker_count": self.performance.worker_count,
                "enable_gzip": self.performance.enable_gzip
            }
        }

    def _detect_database_provider(self) -> str:
        """Detect database provider from URL"""
        url = self.database.url.lower()

        if "neon" in url or "neon.tech" in url:
            return "Neon (Serverless PostgreSQL)"
        elif "supabase" in url:
            return "Supabase (PostgreSQL)"
        elif "planetscale" in url:
            return "PlanetScale (MySQL)"
        elif "postgresql" in url:
            return "PostgreSQL"
        elif "mysql" in url:
            return "MySQL"
        elif "sqlite" in url:
            return "SQLite"
        else:
            return "Unknown"


# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

# Singleton configuration instance
_config: Optional[UnifiedConfig] = None


def get_config(environment: Optional[str] = None) -> UnifiedConfig:
    """
    Get or create unified configuration instance

    Args:
        environment: Environment name (optional)

    Returns:
        UnifiedConfig instance
    """
    global _config

    if _config is None:
        _config = UnifiedConfig(environment=environment)

    return _config


def reload_config(environment: Optional[str] = None) -> UnifiedConfig:
    """
    Reload configuration (useful for testing)

    Args:
        environment: Environment name (optional)

    Returns:
        New UnifiedConfig instance
    """
    global _config
    _config = UnifiedConfig(environment=environment)
    return _config


# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================


def validate_production_config(config: UnifiedConfig) -> List[str]:
    """
    Validate configuration for production deployment

    Args:
        config: UnifiedConfig instance

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Security validation
    if len(config.security.secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters for production")

    if "dev" in config.security.secret_key.lower() or "test" in config.security.secret_key.lower():
        errors.append("SECRET_KEY appears to be a development/test key")

    # Database validation
    if "sqlite" in config.database.url.lower():
        errors.append("SQLite is not recommended for production - use PostgreSQL or MySQL")

    # AI validation
    if not config.ai.openai_api_key and not config.ai.anthropic_api_key:
        errors.append("At least one AI API key (OpenAI or Anthropic) should be configured")

    # Logging validation
    if not config.logging.sanitize_sensitive_data:
        errors.append("Sensitive data sanitization should be enabled in production")

    return errors


# Export main configuration getter
__all__ = [
    "UnifiedConfig",
    "get_config",
    "reload_config",
    "validate_production_config",
    "DatabaseConfig",
    "SecurityConfig",
    "LoggingConfig",
    "RedisConfig",
    "CORSConfig",
    "PerformanceConfig",
    "AIConfig"
]
