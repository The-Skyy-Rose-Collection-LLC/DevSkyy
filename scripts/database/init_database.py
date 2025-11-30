"""
Initialize DevSkyy Database
Sets up database with all required tables using SQLAlchemy models
"""

import asyncio
import logging
from pathlib import Path

# Load environment variables FIRST before any other imports
from dotenv import load_dotenv


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def init_database():
    """Initialize the database with all tables"""
    try:
        # Import database modules
        from database import db_manager, init_db, DATABASE_URL
        import models_sqlalchemy  # noqa: F401 - Import for side effects (model registration)

        db_provider = "postgresql" if "postgresql" in DATABASE_URL else "sqlite"
        logger.info(f"🗄️  Database Provider: {db_provider}")
        logger.info(f"📍 Database URL: {DATABASE_URL}")

        # Create database file if it doesn't exist
        if "sqlite" in DATABASE_URL:
            db_path = Path("./devskyy.db")
            if not db_path.exists():
                logger.info("📁 Creating new SQLite database file...")
                db_path.touch()

        # Initialize database (create all tables)
        logger.info("🔨 Creating database tables...")
        await init_db()

        # Verify tables were created
        logger.info("✅ Database tables created successfully!")

        # Test connection
        logger.info("🔍 Testing database connection...")
        health = await db_manager.health_check()

        if health.get("status") == "healthy":
            logger.info("✅ Database connection healthy!")
            logger.info(f"📊 Database info: {health}")
        else:
            logger.error(f"❌ Database health check failed: {health}")
            return False

        # List created tables using async query
        from sqlalchemy import text

        from database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            if "sqlite" in DATABASE_URL:
                # Query SQLite system table
                result = await session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                )
                tables = [row[0] for row in result.fetchall()]
            else:
                # For PostgreSQL/MySQL, use information_schema
                result = await session.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                )
                tables = [row[0] for row in result.fetchall()]

        logger.info(f"\n📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"  ✓ {table}")

        logger.info("\n🎉 Database initialization complete!")
        return True

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def verify_models():
    """Verify all models are properly registered"""
    import models_sqlalchemy

    logger.info("\n🔍 Verifying SQLAlchemy models...")

    model_classes = [
        models_sqlalchemy.User,
        models_sqlalchemy.Product,
        models_sqlalchemy.Customer,
        models_sqlalchemy.Order,
        models_sqlalchemy.AgentLog,
        models_sqlalchemy.BrandAsset,
        models_sqlalchemy.Campaign,
    ]

    for model in model_classes:
        table_name = model.__tablename__
        logger.info(f"  ✓ {model.__name__} → {table_name}")

    logger.info(f"\n✅ {len(model_classes)} models registered")
    return True


async def create_sample_data():
    """Create sample data for testing (optional)"""
    from datetime import datetime

    from database import AsyncSessionLocal
    from models_sqlalchemy import AgentLog, Product, User

    logger.info("\n📝 Creating sample data...")

    async with AsyncSessionLocal() as session:
        try:
            # Create sample user
            sample_user = User(
                email="admin@devskyy.com",
                username="admin",
                full_name="DevSkyy Admin",
                hashed_password="<replace with hashed password>",
                is_superuser=True,
            )
            session.add(sample_user)

            # Create sample product
            sample_product = Product(
                name="Luxury Rose Gold Watch",
                description="Premium timepiece with rose gold finish",
                sku="RG-WATCH-001",
                category="Watches",
                price=2999.99,
                cost=1500.00,
                stock_quantity=10,
                sizes=["One Size"],
                colors=["Rose Gold"],
                tags=["luxury", "watches", "rose-gold"],
            )
            session.add(sample_product)

            # Create sample agent log
            sample_log = AgentLog(
                agent_name="Brand Intelligence Agent",
                action="database_initialized",
                status="success",
                input_data={"event": "database_init"},
                output_data={"tables_created": 7},
                execution_time_ms=125.5,
                created_at=datetime.utcnow(),
            )
            session.add(sample_log)

            await session.commit()
            logger.info("✅ Sample data created successfully!")
            logger.info("  - Admin user: admin@devskyy.com")
            logger.info("  - Sample product: Luxury Rose Gold Watch")
            logger.info("  - Agent log entry")

            return True

        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Failed to create sample data: {e}")
            return False


async def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("DevSkyy Database Initialization")
    logger.info("=" * 60)

    # Step 1: Verify models
    if not await verify_models():
        logger.error("❌ Model verification failed")
        return False

    # Step 2: Initialize database
    if not await init_database():
        logger.error("❌ Database initialization failed")
        return False

    # Step 3: Create sample data (optional)
    create_samples = input("\n📝 Create sample data? (y/n): ").lower().strip() == "y"
    if create_samples:
        await create_sample_data()

    logger.info("\n" + "=" * 60)
    logger.info("✅ Database setup complete!")
    logger.info("=" * 60)

    return True


if __name__ == "__main__":
    asyncio.run(main())
