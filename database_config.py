import os

from typing import Optional
from urllib.parse import quote_plus

"""
Enterprise Database Configuration
Supports multiple database backends with production-ready configurations
"""

class DatabaseConfig:
    """Enterprise database configuration manager"""

    @staticmethod
    def get_database_url() -> str:
        """
        Get database URL based on environment configuration.
        Supports: SQLite, PostgreSQL (Neon, Supabase), MySQL (PlanetScale)
        """
        # Check for explicit DATABASE_URL (highest priority)
        if db_url := os.getenv("DATABASE_URL"):
            return DatabaseConfig._normalize_url(db_url)

        # Check for Neon (Serverless PostgreSQL - Recommended)
        if neon_url := os.getenv("NEON_DATABASE_URL"):
            return DatabaseConfig._normalize_url(neon_url)

        # Check for Supabase (PostgreSQL with real-time)
        if supabase_url := os.getenv("SUPABASE_DATABASE_URL"):
            return DatabaseConfig._normalize_url(supabase_url)

        # Check for PlanetScale (MySQL)
        if planetscale_url := os.getenv("PLANETSCALE_DATABASE_URL"):
            return DatabaseConfig._normalize_url(planetscale_url)

        # Check for individual PostgreSQL credentials
        if all(
            [
                os.getenv("DB_HOST"),
                os.getenv("DB_USER"),
                os.getenv("DB_PASSWORD"),
                os.getenv("DB_NAME"),
            ]
        ):
            return DatabaseConfig._build_postgres_url()

        # Default: SQLite (development/testing)
        return "sqlite+aiosqlite:///./devskyy.db"

    @staticmethod
    def _normalize_url(url: str) -> str:
        """
        Normalize database URL to use async drivers.
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

    @staticmethod
    def _build_postgres_url() -> str:
        """Build PostgreSQL URL from individual credentials"""
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME")

        # URL encode password to handle special characters
        encoded_password = quote_plus(password)

        return (
            f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{database}"
        )

    @staticmethod
    def get_connection_args() -> dict:
        """Get database-specific connection arguments"""
        db_url = DatabaseConfig.get_database_url()

        if "postgresql" in db_url:
            return {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
                "pool_pre_ping": True,  # Verify connections before using
            }
        elif "mysql" in db_url:
            return {
                "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
                "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
                "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
            }
        else:  # SQLite (aiosqlite doesn't support check_same_thread)
            return {}

    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"

    @staticmethod
    def get_ssl_config() -> Optional[dict]:
        """Get SSL configuration for database connections"""
        if DatabaseConfig.is_production():
            db_url = DatabaseConfig.get_database_url()
            if "postgresql" in db_url or "mysql" in db_url:
                return {"ssl": "require"}
        return None

# Export configuration
DATABASE_URL = DatabaseConfig.get_database_url()
CONNECTION_ARGS = DatabaseConfig.get_connection_args()
IS_PRODUCTION = DatabaseConfig.is_production()

# Database provider detection
if "neon" in DATABASE_URL or "neon.tech" in DATABASE_URL:
    DB_PROVIDER = "Neon (Serverless PostgreSQL)"
elif "supabase" in DATABASE_URL:
    DB_PROVIDER = "Supabase (PostgreSQL)"
elif "planetscale" in DATABASE_URL:
    DB_PROVIDER = "PlanetScale (MySQL)"
elif "postgresql" in DATABASE_URL:
    DB_PROVIDER = "PostgreSQL"
elif "mysql" in DATABASE_URL:
    DB_PROVIDER = "MySQL"
elif "sqlite" in DATABASE_URL:
    DB_PROVIDER = "SQLite"
else:
    DB_PROVIDER = "Unknown"
