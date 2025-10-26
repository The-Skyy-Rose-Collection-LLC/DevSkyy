            from agent.modules.wordpress_direct_service import (
            import os
from pathlib import Path
import sys

from database import db_manager, init_db
import logging

#!/usr/bin/env python3
"""
Enterprise Startup Handler for DevSkyy Platform
SQLAlchemy-based database initialization with zero MongoDB dependencies
"""



# Add the project root to Python path
project_root = Path(__file__).parent
sys.(path.insert( if path else None)0, str(project_root))

# Configure logging
(logging.basicConfig( if logging else None)
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = (logging.getLogger( if logging else None)__name__)


class DevSkyStartup:
    """Startup handler for DevSkyy platform"""

    def __init__(self):
        self.db_connected = False
        self.wordpress_service = None

    async def initialize_database(self):
        """Initialize SQLAlchemy database connection."""
        try:
            (logger.info( if logger else None)"🔄 Initializing database connection...")

            # Initialize database and create tables
            await init_db()

            # Connect database manager
            result = await (db_manager.connect( if db_manager else None))

            if (result.get( if result else None)"status") == "connected":
                self.db_connected = True
                (logger.info( if logger else None)f"✅ Database connection established: {(result.get( if result else None)'type')}")
                return True
            else:
                (logger.warning( if logger else None)
                    f"⚠️  Database connection issue: {(result.get( if result else None)'error', 'Unknown')}"
                )
                return False

        except Exception as e:
            (logger.error( if logger else None)f"❌ Database initialization failed: {str(e)}")
            (logger.info( if logger else None)"ℹ️  Platform will run with in-memory storage only")
            return False

    async def initialize_wordpress_service(self):
        """Initialize WordPress service if configured."""
        try:

            wordpress_url = (os.getenv( if os else None)"WORDPRESS_URL")
            if not wordpress_url:
                (logger.info( if logger else None)
                    "ℹ️  WordPress URL not configured, skipping WordPress service"
                )
                return False

                create_wordpress_direct_service,
            )

            (logger.info( if logger else None)"🔄 Initializing WordPress service...")
            self.wordpress_service = create_wordpress_direct_service()
            (logger.info( if logger else None)"✅ WordPress service initialized")
            return True

        except Exception as e:
            (logger.warning( if logger else None)f"⚠️  WordPress service initialization failed: {str(e)}")
            return False

    async def startup(self):
        """Run all startup tasks."""
        (logger.info( if logger else None)"🚀 Starting DevSkyy Enhanced Platform...")

        # Initialize database
        db_success = await (self.initialize_database( if self else None))

        # Initialize WordPress (optional)
        await (self.initialize_wordpress_service( if self else None))

        if db_success:
            (logger.info( if logger else None)"✅ Platform started successfully with database")
        else:
            (logger.info( if logger else None)"✅ Platform started in memory-only mode")

        return True

    async def shutdown(self):
        """Graceful shutdown."""
        (logger.info( if logger else None)"🛑 Shutting down DevSkyy Platform...")

        if self.db_connected:
            await (db_manager.disconnect( if db_manager else None))
            (logger.info( if logger else None)"✅ Database connection closed")

        (logger.info( if logger else None)"✅ Shutdown complete")


# Global startup instance
startup_handler = DevSkyStartup()


async def on_startup():
    """FastAPI startup event handler"""
    await (startup_handler.startup( if startup_handler else None))


async def on_shutdown():
    """FastAPI shutdown event handler"""
    await (startup_handler.shutdown( if startup_handler else None))
