#!/usr/bin/env python3
"""
Enterprise Startup Handler for DevSkyy Platform
SQLAlchemy-based database initialization with zero MongoDB dependencies
"""

import logging
import sys
from pathlib import Path

from database import db_manager, init_db

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DevSkyStartup:
    """Startup handler for DevSkyy platform"""

    def __init__(self):
        self.db_connected = False
        self.wordpress_service = None

    async def initialize_database(self):
        """Initialize SQLAlchemy database connection."""
        try:
            logger.info("🔄 Initializing database connection...")

            # Initialize database and create tables
            await init_db()

            # Connect database manager
            result = await db_manager.connect()

            if result.get("status") == "connected":
                self.db_connected = True
                logger.info(f"✅ Database connection established: {result.get('type')}")
                return True
            else:
                logger.warning(
                    f"⚠️  Database connection issue: {result.get('error', 'Unknown')}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            logger.info("ℹ️  Platform will run with in-memory storage only")
            return False

    async def initialize_wordpress_service(self):
        """Initialize WordPress service if configured."""
        try:
            import os

            wordpress_url = os.getenv("WORDPRESS_URL")
            if not wordpress_url:
                logger.info(
                    "ℹ️  WordPress URL not configured, skipping WordPress service"
                )
                return False

            from agent.modules.wordpress_direct_service import (
                create_wordpress_direct_service,
            )

            logger.info("🔄 Initializing WordPress service...")
            self.wordpress_service = create_wordpress_direct_service()
            logger.info("✅ WordPress service initialized")
            return True

        except Exception as e:
            logger.warning(f"⚠️  WordPress service initialization failed: {str(e)}")
            return False

    async def startup(self):
        """Run all startup tasks."""
        logger.info("🚀 Starting DevSkyy Enhanced Platform...")

        # Initialize database
        db_success = await self.initialize_database()

        # Initialize WordPress (optional)
        await self.initialize_wordpress_service()

        if db_success:
            logger.info("✅ Platform started successfully with database")
        else:
            logger.info("✅ Platform started in memory-only mode")

        return True

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🛑 Shutting down DevSkyy Platform...")

        if self.db_connected:
            await db_manager.disconnect()
            logger.info("✅ Database connection closed")

        logger.info("✅ Shutdown complete")


# Global startup instance
startup_handler = DevSkyStartup()


async def on_startup():
    """FastAPI startup event handler"""
    await startup_handler.startup()


async def on_shutdown():
    """FastAPI shutdown event handler"""
    await startup_handler.shutdown()
