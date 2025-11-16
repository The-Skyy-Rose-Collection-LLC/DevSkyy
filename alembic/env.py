"""
Alembic Environment Configuration for DevSkyy
Production-ready async SQLAlchemy migration support
Supports SQLite, PostgreSQL, MySQL backends
"""

import asyncio
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import database configuration
from database_config import DATABASE_URL

# Import Base and all models (CRITICAL: ensures all models are registered)
from database import Base
from models_sqlalchemy import (
    User,
    Product,
    Customer,
    Order,
    AgentLog,
    BrandAsset,
    Campaign,
)

# Alembic Config object - provides access to .ini values
config = context.config

# Override sqlalchemy.url from environment (Truth Protocol Rule 5)
if DATABASE_URL:
    # Convert async URL to sync URL for Alembic
    sync_url = DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "").replace("+aiomysql", "")
    config.set_main_option("sqlalchemy.url", sync_url)

# Setup Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
# This is the SQLAlchemy MetaData object from our Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the
    Engine creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations with a given connection.

    Args:
        connection: SQLAlchemy connection object
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect default value changes
        render_as_batch=True,  # Support SQLite ALTER TABLE
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in async mode.

    Uses async engine for production compatibility with FastAPI async database.
    """
    # Get async-compatible URL
    url = config.get_main_option("sqlalchemy.url")

    # Convert sync URL back to async for engine creation
    if "postgresql" in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://")
    elif "sqlite" in url and "+aiosqlite" not in url:
        url = url.replace("sqlite://", "sqlite+aiosqlite://")
    elif "mysql" in url and "+aiomysql" not in url:
        url = url.replace("mysql://", "mysql+aiomysql://")

    # Create async engine configuration
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.

    For async compatibility, we use asyncio.run() to execute async migrations.
    """
    asyncio.run(run_async_migrations())


# Determine offline vs online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
