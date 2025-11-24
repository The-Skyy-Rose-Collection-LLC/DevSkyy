from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import logging
import time
from typing import Any, Union

import asyncpg
from clickhouse_driver import Client as ClickHouseClient
import motor.motor_asyncio


"""
Database Ecosystem Integration
Comprehensive database management for PostgreSQL, MongoDB, ClickHouse
with connection pooling, indexing, migration tools, and backup automation
"""

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Database types supported"""

    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    CLICKHOUSE = "clickhouse"
    REDIS = "redis"


@dataclass
class DatabaseConfig:
    """Database configuration"""

    db_type: DatabaseType
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    ssl_enabled: bool = False
    ssl_cert_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data["db_type"] = self.db_type.value
        return data


@dataclass
class ConnectionMetrics:
    """Database connection metrics"""

    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    average_response_time: float = 0.0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    last_updated: datetime = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        if self.last_updated:
            data["last_updated"] = self.last_updated.isoformat()
        return data


class PostgreSQLManager:
    """PostgreSQL database manager with connection pooling"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool = None
        self.metrics = ConnectionMetrics()
        self.is_connected = False

        logger.info(f"PostgreSQL manager initialized - Host: {config.host}:{config.port}")

    async def connect(self) -> bool:
        """Establish connection pool"""
        try:
            dsn = f"postgresql://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=1,
                max_size=self.config.pool_size,
                command_timeout=self.config.pool_timeout,
                server_settings={
                    "jit": "off",  # Disable JIT for better performance on small queries
                    "application_name": "devskyy_fashion_platform",
                },
            )

            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")

            self.is_connected = True
            self.metrics.total_connections += 1
            logger.info("PostgreSQL connection pool established")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.metrics.failed_connections += 1
            return False

    async def execute_query(self, query: str, params: tuple | None = None) -> list[dict[str, Any]]:
        """Execute query and return results"""
        if not self.pool:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            async with self.pool.acquire() as conn:
                if params:
                    result = await conn.fetch(query, *params)
                else:
                    result = await conn.fetch(query)

                # Convert to list of dictionaries
                rows = [dict(row) for row in result]

                # Update metrics
                response_time = time.time() - start_time
                self.metrics.total_queries += 1
                self.metrics.successful_queries += 1
                self._update_response_time(response_time)

                return rows

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"PostgreSQL query failed: {e}")
            raise e

    async def execute_command(self, command: str, params: tuple | None = None) -> str:
        """Execute command (INSERT, UPDATE, DELETE)"""
        if not self.pool:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            async with self.pool.acquire() as conn:
                if params:
                    result = await conn.execute(command, *params)
                else:
                    result = await conn.execute(command)

                # Update metrics
                response_time = time.time() - start_time
                self.metrics.total_queries += 1
                self.metrics.successful_queries += 1
                self._update_response_time(response_time)

                return result

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"PostgreSQL command failed: {e}")
            raise e

    async def create_indexes(self) -> bool:
        """Create fashion e-commerce specific indexes"""
        indexes = [
            # User indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at)",
            # Product indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_category ON products(category)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_brand ON products(brand)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_price ON products(price)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_created_at ON products(created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_products_fashion_trends ON products USING GIN(fashion_trends)",
            # Order indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_status ON orders(status)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_created_at ON orders(created_at)",
            # Fashion trend indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fashion_trends_category ON fashion_trends(category)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fashion_trends_season ON fashion_trends(season)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fashion_trends_popularity ON fashion_trends(popularity_score)",
            # Analytics indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_behavior_user_id ON user_behavior(user_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_behavior_timestamp ON user_behavior(timestamp)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_behavior_action ON user_behavior(action)",
        ]

        try:
            for index_sql in indexes:
                await self.execute_command(index_sql)
                logger.info(
                    f"Created index: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'}"
                )

            return True

        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
            return False

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.average_response_time
            )

        self.metrics.last_updated = datetime.now()

    async def get_pool_status(self) -> dict[str, Any]:
        """Get connection pool status"""
        if not self.pool:
            return {"status": "disconnected"}

        return {
            "size": self.pool.get_size(),
            "checked_in": self.pool.get_size() - self.pool.get_idle_size(),
            "checked_out": self.pool.get_idle_size(),
            "overflow": 0,  # asyncpg doesn't have overflow concept
            "invalid": 0,
        }

    async def close(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("PostgreSQL connection pool closed")


class MongoDBManager:
    """MongoDB database manager with connection pooling"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = None
        self.database = None
        self.metrics = ConnectionMetrics()
        self.is_connected = False

        logger.info(f"MongoDB manager initialized - Host: {config.host}:{config.port}")

    async def connect(self) -> bool:
        """Establish MongoDB connection"""
        try:
            connection_string = f"mongodb://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"

            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                connection_string,
                maxPoolSize=self.config.pool_size,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=self.config.pool_timeout * 1000,
                appname="devskyy_fashion_platform",
            )

            self.database = self.client[self.config.database]

            # Test connection
            await self.client.admin.command("ping")

            self.is_connected = True
            self.metrics.total_connections += 1
            logger.info("MongoDB connection established")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self.metrics.failed_connections += 1
            return False

    async def find_documents(
        self, collection: str, query: dict[str, Any] | None = None, limit: int = 100
    ) -> list[dict[str, Any]]:
        """Find documents in collection"""
        if not self.database:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            coll = self.database[collection]
            cursor = coll.find(query or {}).limit(limit)
            documents = await cursor.to_list(length=limit)

            # Convert ObjectId to string
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])

            # Update metrics
            response_time = time.time() - start_time
            self.metrics.total_queries += 1
            self.metrics.successful_queries += 1
            self._update_response_time(response_time)

            return documents

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"MongoDB find failed: {e}")
            raise e

    async def insert_document(self, collection: str, document: dict[str, Any]) -> str:
        """Insert document into collection"""
        if not self.database:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            coll = self.database[collection]
            result = await coll.insert_one(document)

            # Update metrics
            response_time = time.time() - start_time
            self.metrics.total_queries += 1
            self.metrics.successful_queries += 1
            self._update_response_time(response_time)

            return str(result.inserted_id)

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"MongoDB insert failed: {e}")
            raise e

    async def update_document(self, collection: str, query: dict[str, Any], update: dict[str, Any]) -> int:
        """Update documents in collection"""
        if not self.database:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            coll = self.database[collection]
            result = await coll.update_many(query, {"$set": update})

            # Update metrics
            response_time = time.time() - start_time
            self.metrics.total_queries += 1
            self.metrics.successful_queries += 1
            self._update_response_time(response_time)

            return result.modified_count

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"MongoDB update failed: {e}")
            raise e

    async def create_indexes(self) -> bool:
        """Create fashion e-commerce specific indexes"""
        indexes = {
            "users": [
                [("email", 1)],
                [("created_at", -1)],
                [("fashion_preferences.style", 1)],
                [("fashion_preferences.brands", 1)],
            ],
            "products": [
                [("category", 1)],
                [("brand", 1)],
                [("price", 1)],
                [("fashion_trends", 1)],
                [("sustainability_rating", -1)],
                [("created_at", -1)],
                [("name", "text"), ("description", "text")],  # Text index for search
            ],
            "orders": [
                [("user_id", 1)],
                [("status", 1)],
                [("created_at", -1)],
                [("total_amount", -1)],
            ],
            "fashion_trends": [
                [("category", 1)],
                [("season", 1)],
                [("popularity_score", -1)],
                [("created_at", -1)],
                [("name", "text"), ("description", "text")],
            ],
            "user_behavior": [
                [("user_id", 1)],
                [("timestamp", -1)],
                [("action", 1)],
                [("product_id", 1)],
            ],
        }

        try:
            for collection_name, collection_indexes in indexes.items():
                collection = self.database[collection_name]

                for index_spec in collection_indexes:
                    await collection.create_index(index_spec)
                    logger.info(f"Created MongoDB index on {collection_name}: {index_spec}")

            return True

        except Exception as e:
            logger.error(f"Failed to create MongoDB indexes: {e}")
            return False

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.average_response_time
            )

        self.metrics.last_updated = datetime.now()

    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.is_connected = False
            logger.info("MongoDB connection closed")


class ClickHouseManager:
    """ClickHouse database manager for analytics"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.client = None
        self.metrics = ConnectionMetrics()
        self.is_connected = False

        logger.info(f"ClickHouse manager initialized - Host: {config.host}:{config.port}")

    async def connect(self) -> bool:
        """Establish ClickHouse connection"""
        try:
            self.client = ClickHouseClient(
                host=self.config.host,
                port=self.config.port,
                user=self.config.username,
                password=self.config.password,
                database=self.config.database,
                settings={
                    "max_execution_time": self.config.pool_timeout,
                    "send_progress_in_http_headers": 1,
                },
            )

            # Test connection
            self.client.execute("SELECT 1")

            self.is_connected = True
            self.metrics.total_connections += 1
            logger.info("ClickHouse connection established")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to ClickHouse: {e}")
            self.metrics.failed_connections += 1
            return False

    async def execute_query(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Execute query and return results"""
        if not self.client:
            raise Exception("Database not connected")

        start_time = time.time()

        try:
            result = self.client.execute(query, params) if params else self.client.execute(query)

            # Convert to list of dictionaries
            if result and len(result) > 0:
                # Get column names from the query or use generic names
                columns = [f"col_{i}" for i in range(len(result[0]))]
                rows = [dict(zip(columns, row, strict=False)) for row in result]
            else:
                rows = []

            # Update metrics
            response_time = time.time() - start_time
            self.metrics.total_queries += 1
            self.metrics.successful_queries += 1
            self._update_response_time(response_time)

            return rows

        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"ClickHouse query failed: {e}")
            raise e

    async def create_tables(self) -> bool:
        """Create fashion analytics tables"""
        if not self.client:
            raise Exception("Database not connected")

        tables = [
            """
            CREATE TABLE IF NOT EXISTS user_events (
                user_id String,
                session_id String,
                timestamp DateTime,
                event_type String,
                page String,
                product_id String,
                category String,
                brand String,
                price Float32,
                device_type String,
                location String,
                referrer String
            ) ENGINE = MergeTree()
            ORDER BY (user_id, timestamp)
            PARTITION BY toYYYYMM(timestamp)
            """,
            """
            CREATE TABLE IF NOT EXISTS fashion_trends_analytics (
                trend_id String,
                name String,
                category String,
                season String,
                popularity_score Float32,
                social_mentions UInt32,
                timestamp DateTime,
                region String
            ) ENGINE = MergeTree()
            ORDER BY (category, timestamp)
            PARTITION BY toYYYYMM(timestamp)
            """,
            """
            CREATE TABLE IF NOT EXISTS sales_analytics (
                order_id String,
                user_id String,
                product_id String,
                category String,
                brand String,
                quantity UInt32,
                price Float32,
                discount Float32,
                timestamp DateTime,
                payment_method String,
                shipping_method String
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, category)
            PARTITION BY toYYYYMM(timestamp)
            """,
        ]

        try:
            for table_sql in tables:
                self.client.execute(table_sql)
                table_name = table_sql.split("TABLE IF NOT EXISTS ")[1].split(" (")[0]
                logger.info(f"Created ClickHouse table: {table_name}")

            return True

        except Exception as e:
            logger.error(f"Failed to create ClickHouse tables: {e}")
            return False

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        if self.metrics.average_response_time == 0:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.average_response_time
            )

        self.metrics.last_updated = datetime.now()

    def close(self):
        """Close ClickHouse connection"""
        if self.client:
            self.client.disconnect()
            self.is_connected = False
            logger.info("ClickHouse connection closed")


class DatabaseEcosystem:
    """Unified database ecosystem manager"""

    def __init__(self):
        self.databases = {}
        self.configs = {}
        self.backup_configs = {}

        logger.info("Database Ecosystem initialized")

    async def add_database(self, name: str, config: DatabaseConfig) -> bool:
        """Add database to ecosystem"""
        try:
            if config.db_type == DatabaseType.POSTGRESQL:
                manager = PostgreSQLManager(config)
            elif config.db_type == DatabaseType.MONGODB:
                manager = MongoDBManager(config)
            elif config.db_type == DatabaseType.CLICKHOUSE:
                manager = ClickHouseManager(config)
            else:
                raise ValueError(f"Unsupported database type: {config.db_type}")

            # Connect to database
            success = await manager.connect()

            if success:
                self.databases[name] = manager
                self.configs[name] = config
                logger.info(f"Added {config.db_type.value} database: {name}")
                return True
            else:
                logger.error(f"Failed to connect to database: {name}")
                return False

        except Exception as e:
            logger.error(f"Error adding database {name}: {e}")
            return False

    def get_database(self, name: str) -> Union[PostgreSQLManager, MongoDBManager, ClickHouseManager]:
        """Get database manager by name"""
        if name not in self.databases:
            raise ValueError(f"Database not found: {name}")

        return self.databases[name]

    async def initialize_all_indexes(self) -> dict[str, bool]:
        """Initialize indexes for all databases"""
        results = {}

        for name, manager in self.databases.items():
            try:
                if hasattr(manager, "create_indexes"):
                    success = await manager.create_indexes()
                    results[name] = success
                elif hasattr(manager, "create_tables"):
                    success = await manager.create_tables()
                    results[name] = success
                else:
                    results[name] = True  # No indexes to create

            except Exception as e:
                logger.error(f"Failed to initialize indexes for {name}: {e}")
                results[name] = False

        return results

    async def get_ecosystem_metrics(self) -> dict[str, Any]:
        """Get metrics for all databases"""
        metrics = {}

        for name, manager in self.databases.items():
            try:
                db_metrics = {
                    "type": self.configs[name].db_type.value,
                    "is_connected": manager.is_connected,
                    "connection_metrics": manager.metrics.to_dict(),
                }

                # Add pool status if available
                if hasattr(manager, "get_pool_status"):
                    db_metrics["pool_status"] = await manager.get_pool_status()

                metrics[name] = db_metrics

            except Exception as e:
                logger.error(f"Error getting metrics for {name}: {e}")
                metrics[name] = {"error": str(e)}

        return metrics

    async def health_check(self) -> dict[str, Any]:
        """Comprehensive health check for all databases"""
        health_status = {}
        overall_healthy = True

        for name, manager in self.databases.items():
            try:
                start_time = time.time()

                # Test basic connectivity
                if hasattr(manager, "execute_query"):
                    if isinstance(manager, (PostgreSQLManager, ClickHouseManager)):
                        await manager.execute_query("SELECT 1")
                elif hasattr(manager, "find_documents"):
                    # MongoDB test
                    await manager.find_documents("test", {}, limit=1)

                response_time = (time.time() - start_time) * 1000

                health_status[name] = {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "type": self.configs[name].db_type.value,
                    "is_connected": manager.is_connected,
                    "metrics": manager.metrics.to_dict(),
                }

            except Exception as e:
                health_status[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "type": self.configs[name].db_type.value,
                    "is_connected": False,
                }
                overall_healthy = False

        return {
            "overall_status": "healthy" if overall_healthy else "degraded",
            "databases": health_status,
            "total_databases": len(self.databases),
            "healthy_databases": sum([1 for db in health_status.values() if db.get("status") == "healthy"]),
        }

    async def close_all(self):
        """Close all database connections"""
        for name, manager in self.databases.items():
            try:
                if hasattr(manager, "close"):
                    await manager.close()
                else:
                    manager.close()
                logger.info(f"Closed database connection: {name}")
            except Exception as e:
                logger.error(f"Error closing database {name}: {e}")


# Global database ecosystem instance
database_ecosystem = DatabaseEcosystem()
