"""
Database Migration System
Enterprise-grade migrations for production deployments
"""

import asyncio
import logging

from database import Base, engine
from models_sqlalchemy import Product

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """Create all database tables"""
    logger.info("🔧 Creating database tables...")

    async with engine.begin() as conn:
        # Drop all tables (use with caution in production!)
        # await conn.run_sync(Base.metadata.drop_all)

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Database tables created successfully")


async def verify_tables():
    """Verify all tables exist"""
    logger.info("🔍 Verifying database tables...")

    from sqlalchemy import inspect

    async with engine.connect() as conn:

        def _inspect(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()

        tables = await conn.run_sync(_inspect)

    expected_tables = [
        "products",
        "customers",
        "orders",
        "payments",
        "analytics",
        "brand_assets",
        "campaigns",
    ]

    for table in expected_tables:
        if table in tables:
            logger.info(f"  ✅ Table '{table}' exists")
        else:
            logger.warning(f"  ⚠️  Table '{table}' missing")

    return all(table in tables for table in expected_tables)


async def seed_initial_data():
    """Seed initial data for new deployments (optional)"""
    logger.info("🌱 Seeding initial data...")

    from database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        # Check if data already exists
        from sqlalchemy import select

        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none():
            logger.info("  ℹ️  Data already exists, skipping seed")
            return

        # Add initial data here if needed
        logger.info("  ℹ️  No seed data configured")


async def run_migrations():
    """Run all database migrations"""
    logger.info("=" * 60)
    logger.info("🚀 Starting Database Migration")
    logger.info("=" * 60)

    try:
        # Step 1: Create tables
        await create_tables()

        # Step 2: Verify tables
        all_exist = await verify_tables()

        if not all_exist:
            logger.error("❌ Migration incomplete - some tables missing")
            return False

        # Step 3: Seed initial data (optional)
        # await seed_initial_data()

        logger.info("=" * 60)
        logger.info("✅ Database Migration Complete")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"❌ Migration failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    asyncio.run(run_migrations())
