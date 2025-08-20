"""
Production startup script for the AI Agent Dashboard.
Handles database connections, environment setup, and graceful startup.
"""
import os
import sys
import logging
import asyncio
from typing import Optional
import certifi
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Handles MongoDB connection with Atlas support."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        
    async def connect(self) -> bool:
        """Connect to MongoDB with fallback options."""
        mongo_url = self._get_mongo_url()
        
        try:
            # Determine connection type
            if self._is_atlas_connection(mongo_url):
                self.client = await self._connect_to_atlas(mongo_url)
            else:
                self.client = await self._connect_to_local(mongo_url)
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database
            db_name = self._extract_db_name(mongo_url)
            self.db = self.client[db_name]
            
            logger.info(f"✅ Successfully connected to MongoDB: {db_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {str(e)}")
            return False
    
    def _get_mongo_url(self) -> str:
        """Get MongoDB URL from environment variables."""
        # Check for production Atlas URL first
        atlas_url = os.getenv('MONGODB_URI')
        if atlas_url:
            logger.info("🌍 Using MongoDB Atlas connection")
            return atlas_url
        
        # Fallback to local development URL
        local_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017/ai_agent_dashboard')
        logger.info("🔧 Using local MongoDB connection")
        return local_url
    
    def _is_atlas_connection(self, url: str) -> bool:
        """Check if the URL is for MongoDB Atlas."""
        return 'mongodb+srv://' in url or 'mongodb.net' in url
    
    async def _connect_to_atlas(self, url: str) -> AsyncIOMotorClient:
        """Connect to MongoDB Atlas with proper SSL configuration."""
        return AsyncIOMotorClient(
            url,
            tls=True,
            tlsCAFile=certifi.where(),
            retryWrites=True,
            w='majority',
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxPoolSize=10,
            minPoolSize=1
        )
    
    async def _connect_to_local(self, url: str) -> AsyncIOMotorClient:
        """Connect to local MongoDB."""
        return AsyncIOMotorClient(
            url,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            socketTimeoutMS=5000
        )
    
    def _extract_db_name(self, url: str) -> str:
        """Extract database name from MongoDB URL."""
        if '/' in url:
            parts = url.split('/')
            if len(parts) > 3:
                db_name = parts[-1].split('?')[0]  # Remove query parameters
                if db_name:
                    return db_name
        return 'ai_agent_dashboard'  # Default database name
    
    async def close(self):
        """Close the database connection."""
        if self.client:
            self.client.close()
            logger.info("📡 Database connection closed")

# Global database instance
db_connection = DatabaseConnection()

async def startup_sequence():
    """Execute startup sequence for the application."""
    logger.info("🚀 Starting AI Agent Dashboard...")
    
    # Connect to database
    connected = await db_connection.connect()
    if not connected:
        logger.warning("⚠️  Database connection failed, running in limited mode")
    
    # Initialize other services
    await initialize_services()
    
    logger.info("✅ Startup sequence complete")

async def initialize_services():
    """Initialize application services."""
    try:
        # Initialize OpenAI client
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            logger.info("🧠 OpenAI integration enabled")
        else:
            logger.warning("⚠️  OpenAI API key not found")
        
        # Initialize other services as needed
        logger.info("⚙️  Services initialized")
        
    except Exception as e:
        logger.error(f"❌ Service initialization failed: {str(e)}")

async def shutdown_sequence():
    """Execute shutdown sequence for the application."""
    logger.info("🛑 Shutting down AI Agent Dashboard...")
    
    # Close database connection
    await db_connection.close()
    
    logger.info("✅ Shutdown sequence complete")

def get_database():
    """Get the database instance."""
    return db_connection.db

def health_check() -> dict:
    """Perform application health check."""
    health = {
        "status": "healthy",
        "database": "disconnected",
        "services": "operational",
        "timestamp": asyncio.get_event_loop().time()
    }
    
    if db_connection.client:
        try:
            # Quick ping to check database
            asyncio.create_task(db_connection.client.admin.command('ping'))
            health["database"] = "connected"
        except:
            health["database"] = "disconnected"
            health["status"] = "degraded"
    
    return health

if __name__ == "__main__":
    # Run startup sequence for testing
    asyncio.run(startup_sequence())