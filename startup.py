#!/usr/bin/env python3
"""
Startup script for Skyy Rose AI Agent Management Platform
Handles graceful startup, database connections, and WordPress auto - connection
"""

from agent.modules.wordpress_direct_service import create_wordpress_direct_service
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


# Configure logging
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SkyRoseStartup:
    def __init__(self):
        self.mongodb_client = None
        self.wordpress_service = None

    async def initialize_database(self):
        """Initialize MongoDB connection."""
        try:
            import os
            mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017 / skyy_rose_agents')

            logger.info("🔄 Initializing MongoDB connection...")
            self.mongodb_client = AsyncIOMotorClient(mongo_url)

            # Test connection
            await self.mongodb_client.admin.command('ismaster')
            logger.info("✅ MongoDB connection established successfully")

            return True

        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            return False

    async def initialize_wordpress_connection(self):
        """Auto-connect to WordPress on startup."""
        try:
            logger.info("🔄 Initializing WordPress auto - connection...")

            self.wordpress_service = create_wordpress_direct_service()

            # Attempt auto-connection
            connection_result = await self.wordpress_service.connect_and_verify()

            if connection_result.get('status') == 'connected':
                logger.info("✅ WordPress auto - connection successful!")
                logger.info(f"   └─ Connected to: {connection_result.get('site_url', 'skyyrose.co')}")
                logger.info(f"   └─ Site health: {connection_result.get('health', 'Unknown')}")
                return True
            else:
                logger.warning("⚠️ WordPress auto - connection failed - will retry on first request")
                return False

        except Exception as e:
            logger.error(f"❌ WordPress auto - connection error: {str(e)}")
            return False

    async def run_startup_sequence(self):
        """Run complete startup sequence."""
        logger.info("🚀 Starting Skyy Rose AI Agent Platform...")

        # Initialize database
        db_success = await self.initialize_database()
        if not db_success:
            logger.error("💥 Critical: Database initialization failed!")
            return False

        # Auto-connect WordPress (non-critical)
        wp_success = await self.initialize_wordpress_connection()
        if wp_success:
            logger.info("✅ WordPress integration ready")
        else:
            logger.info("ℹ️ WordPress will connect on first request")

        logger.info("🎉 Skyy Rose platform startup complete!")
        logger.info("   ├─ 🤖 AI Agents: Ready")
        logger.info("   ├─ 💾 Database: Connected")
        logger.info("   ├─ 🌐 WordPress: " + ("Connected" if wp_success else "Standby"))
        logger.info("   └─ ⚡ Automation: Active")

        return True

    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("🔄 Shutting down services...")

        if self.mongodb_client:
            self.mongodb_client.close()
            logger.info("✅ MongoDB connection closed")

        logger.info("👋 Skyy Rose platform shutdown complete")


# Global startup instance
startup_manager = SkyRoseStartup()


async def startup():
    """Main startup function."""
    return await startup_manager.run_startup_sequence()


async def shutdown():
    """Main shutdown function."""
    await startup_manager.shutdown()

if __name__ == "__main__":
    # Run startup sequence directly
    asyncio.run(startup())
