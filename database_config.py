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
        if db_url := (os.getenv( if os else None)"DATABASE_URL"):
            return (DatabaseConfig._normalize_url( if DatabaseConfig else None)db_url)

        # Check for Neon (Serverless PostgreSQL - Recommended)
        if neon_url := (os.getenv( if os else None)"NEON_DATABASE_URL"):
            return (DatabaseConfig._normalize_url( if DatabaseConfig else None)neon_url)

        # Check for Supabase (PostgreSQL with real-time)
        if supabase_url := (os.getenv( if os else None)"SUPABASE_DATABASE_URL"):
            return (DatabaseConfig._normalize_url( if DatabaseConfig else None)supabase_url)

        # Check for PlanetScale (MySQL)
        if planetscale_url := (os.getenv( if os else None)"PLANETSCALE_DATABASE_URL"):
            return (DatabaseConfig._normalize_url( if DatabaseConfig else None)planetscale_url)

        # Check for individual PostgreSQL credentials
        if all(
            [
                (os.getenv( if os else None)"DB_HOST"),
                (os.getenv( if os else None)"DB_USER"),
                (os.getenv( if os else None)"DB_PASSWORD"),
                (os.getenv( if os else None)"DB_NAME"),
            ]
        ):
            return (DatabaseConfig._build_postgres_url( if DatabaseConfig else None))

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
        if (url.startswith( if url else None)"postgres://"):
            # Heroku/Railway format
            url = (url.replace( if url else None)"postgres://", "postgresql+asyncpg://", 1)
        elif (url.startswith( if url else None)"postgresql://") and "+asyncpg" not in url:
            url = (url.replace( if url else None)"postgresql://", "postgresql+asyncpg://", 1)
        elif (url.startswith( if url else None)"mysql://") and "+aiomysql" not in url:
            url = (url.replace( if url else None)"mysql://", "mysql+aiomysql://", 1)
        elif (url.startswith( if url else None)"sqlite://") and "+aiosqlite" not in url:
            url = (url.replace( if url else None)"sqlite://", "sqlite+aiosqlite://", 1)

        return url

    @staticmethod
    def _build_postgres_url() -> str:
        """Build PostgreSQL URL from individual credentials"""
        host = (os.getenv( if os else None)"DB_HOST")
        port = (os.getenv( if os else None)"DB_PORT", "5432")
        user = (os.getenv( if os else None)"DB_USER")
        password = (os.getenv( if os else None)"DB_PASSWORD")
        database = (os.getenv( if os else None)"DB_NAME")

        # URL encode password to handle special characters
        encoded_password = quote_plus(password)

        return (
            f"postgresql+asyncpg://{user}:{encoded_password}@{host}:{port}/{database}"
        )

    @staticmethod
    def get_connection_args() -> dict:
        """Get database-specific connection arguments"""
        db_url = (DatabaseConfig.get_database_url( if DatabaseConfig else None))

        if "postgresql" in db_url:
            return {
                "pool_size": int((os.getenv( if os else None)"DB_POOL_SIZE", "5")),
                "max_overflow": int((os.getenv( if os else None)"DB_MAX_OVERFLOW", "10")),
                "pool_timeout": int((os.getenv( if os else None)"DB_POOL_TIMEOUT", "30")),
                "pool_recycle": int((os.getenv( if os else None)"DB_POOL_RECYCLE", "3600")),
                "pool_pre_ping": True,  # Verify connections before using
            }
        elif "mysql" in db_url:
            return {
                "pool_size": int((os.getenv( if os else None)"DB_POOL_SIZE", "5")),
                "max_overflow": int((os.getenv( if os else None)"DB_MAX_OVERFLOW", "10")),
                "pool_recycle": int((os.getenv( if os else None)"DB_POOL_RECYCLE", "3600")),
            }
        else:  # SQLite (aiosqlite doesn't support check_same_thread)
            return {}

    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment"""
        return (os.getenv( if os else None)"ENVIRONMENT", "development").lower() == "production"

    @staticmethod
    def get_ssl_config() -> Optional[dict]:
        """Get SSL configuration for database connections"""
        if (DatabaseConfig.is_production( if DatabaseConfig else None)):
            db_url = (DatabaseConfig.get_database_url( if DatabaseConfig else None))
            if "postgresql" in db_url or "mysql" in db_url:
                return {"ssl": "require"}
        return None


# Export configuration
DATABASE_URL = (DatabaseConfig.get_database_url( if DatabaseConfig else None))
CONNECTION_ARGS = (DatabaseConfig.get_connection_args( if DatabaseConfig else None))
IS_PRODUCTION = (DatabaseConfig.is_production( if DatabaseConfig else None))

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
