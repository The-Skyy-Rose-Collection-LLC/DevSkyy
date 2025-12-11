"""
Centralized Configuration for DevSkyy Platform

This module consolidates all configuration classes from:
- main.py (Settings)
- sqlite_auth_system.py (DatabaseConfig, SecurityConfig)
- integration/enhanced_platform.py (EnhancedPlatformConfig)
- integration/prompt_injector.py (PromptInjectionConfig)

Using Pydantic Settings for environment variable support.
"""

import os
import secrets
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    db_path: str = Field(
        default="users.db",
        description="SQLite database file path"
    )
    use_wal: bool = Field(
        default=True,
        description="Use Write-Ahead Logging for better concurrency"
    )
    timeout: float = Field(
        default=30.0,
        description="Database connection timeout in seconds"
    )
    check_same_thread: bool = Field(
        default=False,
        description="Allow database access from multiple threads"
    )
    
    # Async database URL for SQLAlchemy
    async_database_url: str = Field(
        default="sqlite+aiosqlite:///./devskyy.db",
        description="Async database URL for SQLAlchemy"
    )
    
    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class SecurityConfig(BaseSettings):
    """Security configuration."""
    
    # JWT Settings
    secret_key: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_urlsafe(32)),
        description="Secret key for JWT and encryption"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration in minutes"
    )
    
    # Password Policy
    password_min_length: int = Field(
        default=8,
        description="Minimum password length"
    )
    password_require_uppercase: bool = Field(
        default=True,
        description="Require uppercase letters in password"
    )
    password_require_lowercase: bool = Field(
        default=True,
        description="Require lowercase letters in password"
    )
    password_require_numbers: bool = Field(
        default=True,
        description="Require numbers in password"
    )
    password_require_special: bool = Field(
        default=True,
        description="Require special characters in password"
    )
    
    # Encryption Settings
    use_argon2: bool = Field(
        default=True,
        description="Use Argon2 for password hashing (fallback to bcrypt)"
    )
    argon2_time_cost: int = Field(
        default=2,
        description="Argon2 time cost parameter"
    )
    argon2_memory_cost: int = Field(
        default=65536,
        description="Argon2 memory cost parameter"
    )
    argon2_parallelism: int = Field(
        default=1,
        description="Argon2 parallelism parameter"
    )
    bcrypt_rounds: int = Field(
        default=12,
        description="BCrypt hashing rounds"
    )
    
    # Account Lockout
    max_login_attempts: int = Field(
        default=5,
        description="Maximum failed login attempts before lockout"
    )
    lockout_duration_minutes: int = Field(
        default=15,
        description="Account lockout duration in minutes"
    )
    
    # Session Settings
    session_timeout_minutes: int = Field(
        default=60,
        description="Session timeout in minutes"
    )
    allow_multiple_sessions: bool = Field(
        default=True,
        description="Allow multiple concurrent sessions per user"
    )
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


class APIConfig(BaseSettings):
    """API configuration."""
    
    api_base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for the API"
    )
    api_key: str = Field(
        default="",
        description="API key for external integrations"
    )
    api_v1_str: str = Field(
        default="/api/v1",
        description="API v1 prefix"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum API request retries"
    )
    timeout_seconds: float = Field(
        default=60.0,
        description="API request timeout in seconds"
    )
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False


class PromptConfig(BaseSettings):
    """Prompt engineering configuration."""
    
    enable_prompt_engineering: bool = Field(
        default=True,
        description="Enable prompt engineering features"
    )
    max_prompt_tokens: int = Field(
        default=4096,
        description="Maximum tokens in generated prompts"
    )
    include_chain_of_thought: bool = Field(
        default=True,
        description="Include chain-of-thought reasoning"
    )
    include_few_shot_examples: bool = Field(
        default=True,
        description="Include few-shot examples"
    )
    include_negative_prompts: bool = Field(
        default=True,
        description="Include negative prompts"
    )
    include_constitutional_ai: bool = Field(
        default=True,
        description="Include constitutional AI principles"
    )
    auto_select_techniques: bool = Field(
        default=True,
        description="Automatically select prompt techniques"
    )
    
    class Config:
        env_prefix = "PROMPT_"
        case_sensitive = False


class PlatformConfig(BaseSettings):
    """Main platform configuration."""
    
    app_name: str = Field(
        default="DevSkyy Enterprise Platform",
        description="Application name"
    )
    app_version: str = Field(
        default="5.1.0",
        description="Application version"
    )
    debug: bool = Field(
        default=True,
        description="Enable debug mode"
    )
    
    # Component configs
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database configuration"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration"
    )
    api: APIConfig = Field(
        default_factory=APIConfig,
        description="API configuration"
    )
    prompt: PromptConfig = Field(
        default_factory=PromptConfig,
        description="Prompt configuration"
    )
    
    # Performance Settings
    enable_caching: bool = Field(
        default=True,
        description="Enable caching"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    log_prompts: bool = Field(
        default=False,
        description="Log generated prompts (for debugging)"
    )
    
    class Config:
        env_prefix = "PLATFORM_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
_global_config: Optional[PlatformConfig] = None


def get_config() -> PlatformConfig:
    """
    Get or create the global configuration instance.
    
    Returns:
        Global PlatformConfig instance
    """
    global _global_config
    
    if _global_config is None:
        _global_config = PlatformConfig()
    
    return _global_config
