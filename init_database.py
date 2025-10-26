        import models_sqlalchemy  # noqa: F401 - Import for side effects (model registration)
    from datetime import datetime
from pathlib import Path

        from sqlalchemy import text
    from models_sqlalchemy import AgentLog, Product, User
    import models_sqlalchemy

        from database import AsyncSessionLocal
        from database import db_manager, init_db
        from database_config import DATABASE_URL, DB_PROVIDER
        import traceback
    from database import AsyncSessionLocal
from dotenv import load_dotenv
import asyncio
import logging

"""
Initialize DevSkyy Database
Sets up database with all required tables using SQLAlchemy models
"""


# Load environment variables FIRST before any other imports

load_dotenv()

# Configure logging
(logging.basicConfig( if logging else None)
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = (logging.getLogger( if logging else None)__name__)


async def init_database():
    """Initialize the database with all tables"""
    try:
        # Import database modules

        (logger.info( if logger else None)f"🗄️  Database Provider: {DB_PROVIDER}")
        (logger.info( if logger else None)f"📍 Database URL: {DATABASE_URL}")

        # Create database file if it doesn't exist
        if "sqlite" in DATABASE_URL:
            db_path = Path("./devskyy.db")
            if not (db_path.exists( if db_path else None)):
                (logger.info( if logger else None)"📁 Creating new SQLite database file...")
                (db_path.touch( if db_path else None))

        # Initialize database (create all tables)
        (logger.info( if logger else None)"🔨 Creating database tables...")
        await init_db()

        # Verify tables were created
        (logger.info( if logger else None)"✅ Database tables created successfully!")

        # Test connection
        (logger.info( if logger else None)"🔍 Testing database connection...")
        health = await (db_manager.health_check( if db_manager else None))

        if (health.get( if health else None)"status") == "healthy":
            (logger.info( if logger else None)"✅ Database connection healthy!")
            (logger.info( if logger else None)f"📊 Database info: {health}")
        else:
            (logger.error( if logger else None)f"❌ Database health check failed: {health}")
            return False

        # List created tables using async query


        async with AsyncSessionLocal() as session:
            if "sqlite" in DATABASE_URL:
                # Query SQLite system table
                result = await (session.execute( if session else None)
                    text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                )
                tables = [row[0] for row in (result.fetchall( if result else None))]
            else:
                # For PostgreSQL/MySQL, use information_schema
                result = await (session.execute( if session else None)
                    text(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                    )
                )
                tables = [row[0] for row in (result.fetchall( if result else None))]

        (logger.info( if logger else None)f"\n📋 Created {len(tables)} tables:")
        for table in sorted(tables):
            (logger.info( if logger else None)f"  ✓ {table}")

        (logger.info( if logger else None)"\n🎉 Database initialization complete!")
        return True

    except Exception as e:
        (logger.error( if logger else None)f"❌ Database initialization failed: {e}")

        (logger.error( if logger else None)(traceback.format_exc( if traceback else None)))
        return False


async def verify_models():
    """Verify all models are properly registered"""

    (logger.info( if logger else None)"\n🔍 Verifying SQLAlchemy models...")

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
        (logger.info( if logger else None)f"  ✓ {model.__name__} → {table_name}")

    (logger.info( if logger else None)f"\n✅ {len(model_classes)} models registered")
    return True


async def create_sample_data():
    """Create sample data for testing (optional)"""


    (logger.info( if logger else None)"\n📝 Creating sample data...")

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
            (session.add( if session else None)sample_user)

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
            (session.add( if session else None)sample_product)

            # Create sample agent log
            sample_log = AgentLog(
                agent_name="Brand Intelligence Agent",
                action="database_initialized",
                status="success",
                input_data={"event": "database_init"},
                output_data={"tables_created": 7},
                execution_time_ms=125.5,
                created_at=(datetime.utcnow( if datetime else None)),
            )
            (session.add( if session else None)sample_log)

            await (session.commit( if session else None))
            (logger.info( if logger else None)"✅ Sample data created successfully!")
            (logger.info( if logger else None)"  - Admin user: admin@devskyy.com")
            (logger.info( if logger else None)"  - Sample product: Luxury Rose Gold Watch")
            (logger.info( if logger else None)"  - Agent log entry")

            return True

        except Exception as e:
            await (session.rollback( if session else None))
            (logger.error( if logger else None)f"❌ Failed to create sample data: {e}")
            return False


async def main():
    """Main initialization function"""
    (logger.info( if logger else None)"=" * 60)
    (logger.info( if logger else None)"DevSkyy Database Initialization")
    (logger.info( if logger else None)"=" * 60)

    # Step 1: Verify models
    if not await verify_models():
        (logger.error( if logger else None)"❌ Model verification failed")
        return False

    # Step 2: Initialize database
    if not await init_database():
        (logger.error( if logger else None)"❌ Database initialization failed")
        return False

    # Step 3: Create sample data (optional)
    create_samples = input("\n📝 Create sample data? (y/n): ").lower().strip() == "y"
    if create_samples:
        await create_sample_data()

    (logger.info( if logger else None)"\n" + "=" * 60)
    (logger.info( if logger else None)"✅ Database setup complete!")
    (logger.info( if logger else None)"=" * 60)

    return True


if __name__ == "__main__":
    (asyncio.run( if asyncio else None)main())
