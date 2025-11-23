"""
Test database_ecosystem module
Comprehensive tests for PostgreSQL, MongoDB, ClickHouse managers and DatabaseEcosystem
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from infrastructure.database_ecosystem import (
    ClickHouseManager,
    ConnectionMetrics,
    DatabaseConfig,
    DatabaseEcosystem,
    DatabaseType,
    MongoDBManager,
    PostgreSQLManager,
    database_ecosystem,
)


class TestDatabaseConfig:
    """Test DatabaseConfig dataclass"""

    def test_to_dict_basic(self):
        """Test basic dictionary conversion"""
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        result = config.to_dict()

        assert result["db_type"] == "postgresql"
        assert result["host"] == "localhost"
        assert result["port"] == 5432
        assert result["database"] == "testdb"
        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["pool_size"] == 10
        assert result["max_overflow"] == 20

    def test_to_dict_with_ssl(self):
        """Test dictionary conversion with SSL enabled"""
        config = DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="secure.example.com",
            port=27017,
            database="securedb",
            username="admin",
            password="secret",
            ssl_enabled=True,
            ssl_cert_path="/path/to/cert.pem",
        )

        result = config.to_dict()

        assert result["ssl_enabled"] is True
        assert result["ssl_cert_path"] == "/path/to/cert.pem"


class TestConnectionMetrics:
    """Test ConnectionMetrics dataclass"""

    def test_to_dict_without_timestamp(self):
        """Test dictionary conversion without last_updated"""
        metrics = ConnectionMetrics(
            total_connections=10,
            active_connections=5,
            idle_connections=5,
            failed_connections=2,
            average_response_time=0.15,
            total_queries=100,
            successful_queries=98,
            failed_queries=2,
        )

        result = metrics.to_dict()

        assert result["total_connections"] == 10
        assert result["active_connections"] == 5
        assert result["idle_connections"] == 5
        assert result["failed_connections"] == 2
        assert result["average_response_time"] == 0.15
        assert result["total_queries"] == 100
        assert result["successful_queries"] == 98
        assert result["failed_queries"] == 2

    def test_to_dict_with_timestamp(self):
        """Test dictionary conversion with last_updated timestamp"""
        now = datetime(2025, 11, 21, 10, 30, 0)
        metrics = ConnectionMetrics(
            total_connections=5,
            last_updated=now,
        )

        result = metrics.to_dict()

        assert result["last_updated"] == "2025-11-21T10:30:00"


class TestPostgreSQLManager:
    """Test PostgreSQLManager"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
            pool_size=5,
            pool_timeout=10,
        )

    def test_init(self, config):
        """Test PostgreSQL manager initialization"""
        manager = PostgreSQLManager(config)

        assert manager.config == config
        assert manager.pool is None
        assert manager.is_connected is False
        assert manager.metrics.total_connections == 0

    @pytest.mark.asyncio
    async def test_connect_success(self, config):
        """Test successful connection"""
        manager = PostgreSQLManager(config)

        # Mock asyncpg.create_pool
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.execute = AsyncMock(return_value=None)

        with patch("infrastructure.database_ecosystem.asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
            result = await manager.connect()

        assert result is True
        assert manager.is_connected is True
        assert manager.metrics.total_connections == 1
        assert manager.pool is not None

    @pytest.mark.asyncio
    async def test_connect_failure(self, config):
        """Test connection failure"""
        manager = PostgreSQLManager(config)

        with patch(
            "infrastructure.database_ecosystem.asyncpg.create_pool", side_effect=Exception("Connection failed")
        ):
            result = await manager.connect()

        assert result is False
        assert manager.is_connected is False
        assert manager.metrics.failed_connections == 1

    @pytest.mark.asyncio
    async def test_execute_query_success(self, config):
        """Test successful query execution"""
        manager = PostgreSQLManager(config)

        # Mock pool and connection
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context

        # Mock query result
        mock_record = {"id": 1, "name": "test"}
        mock_conn.fetch = AsyncMock(return_value=[mock_record])

        manager.pool = mock_pool

        result = await manager.execute_query("SELECT * FROM users")

        assert len(result) == 1
        assert result[0] == mock_record
        assert manager.metrics.total_queries == 1
        assert manager.metrics.successful_queries == 1
        assert manager.metrics.average_response_time > 0

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, config):
        """Test query execution with parameters"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.fetch = AsyncMock(return_value=[])

        manager.pool = mock_pool

        await manager.execute_query("SELECT * FROM users WHERE id = $1", (1,))

        mock_conn.fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self, config):
        """Test query execution when not connected"""
        manager = PostgreSQLManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, config):
        """Test query execution failure"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        # __aexit__ must return None/False to not suppress exceptions
        async def mock_aexit(*args):
            return None
        mock_acquire_context.__aexit__ = mock_aexit
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.fetch = AsyncMock(side_effect=Exception("Query failed"))

        manager.pool = mock_pool

        with pytest.raises(Exception, match="Query failed"):
            await manager.execute_query("SELECT * FROM invalid_table")

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_execute_command_success(self, config):
        """Test successful command execution"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        manager.pool = mock_pool

        result = await manager.execute_command("INSERT INTO users VALUES ($1, $2)", ("test", "email"))

        assert result == "INSERT 0 1"
        assert manager.metrics.successful_queries == 1

    @pytest.mark.asyncio
    async def test_execute_command_not_connected(self, config):
        """Test command execution when not connected"""
        manager = PostgreSQLManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.execute_command("INSERT INTO users VALUES (1)")

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, config):
        """Test command execution failure"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        # __aexit__ must return None/False to not suppress exceptions
        async def mock_aexit(*args):
            return None
        mock_acquire_context.__aexit__ = mock_aexit
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.execute = AsyncMock(side_effect=Exception("Command failed"))

        manager.pool = mock_pool

        with pytest.raises(Exception, match="Command failed"):
            await manager.execute_command("INVALID COMMAND")

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_create_indexes_success(self, config):
        """Test successful index creation"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.execute = AsyncMock(return_value=None)

        manager.pool = mock_pool

        result = await manager.create_indexes()

        assert result is True
        assert mock_conn.execute.call_count > 0

    @pytest.mark.asyncio
    async def test_create_indexes_failure(self, config):
        """Test index creation failure"""
        manager = PostgreSQLManager(config)

        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute = AsyncMock(side_effect=Exception("Index creation failed"))

        manager.pool = mock_pool

        result = await manager.create_indexes()

        assert result is False

    def test_update_response_time_first_call(self, config):
        """Test response time update on first call"""
        manager = PostgreSQLManager(config)

        assert manager.metrics.average_response_time == 0.0

        manager._update_response_time(0.5)

        assert manager.metrics.average_response_time == 0.5
        assert manager.metrics.last_updated is not None

    def test_update_response_time_exponential_moving_average(self, config):
        """Test exponential moving average for response time"""
        manager = PostgreSQLManager(config)

        manager._update_response_time(1.0)
        first_avg = manager.metrics.average_response_time
        assert first_avg == 1.0

        manager._update_response_time(0.5)
        second_avg = manager.metrics.average_response_time

        # EMA: 0.1 * 0.5 + 0.9 * 1.0 = 0.95
        assert second_avg == pytest.approx(0.95, rel=1e-2)

    @pytest.mark.asyncio
    async def test_get_pool_status_not_connected(self, config):
        """Test pool status when not connected"""
        manager = PostgreSQLManager(config)

        status = await manager.get_pool_status()

        assert status == {"status": "disconnected"}

    @pytest.mark.asyncio
    async def test_get_pool_status_connected(self, config):
        """Test pool status when connected"""
        manager = PostgreSQLManager(config)

        mock_pool = MagicMock()
        mock_pool.get_size.return_value = 10
        mock_pool.get_idle_size.return_value = 3

        manager.pool = mock_pool

        status = await manager.get_pool_status()

        assert status["size"] == 10
        assert status["checked_in"] == 7
        assert status["checked_out"] == 3

    @pytest.mark.asyncio
    async def test_close(self, config):
        """Test connection pool closure"""
        manager = PostgreSQLManager(config)

        mock_pool = AsyncMock()
        manager.pool = mock_pool
        manager.is_connected = True

        await manager.close()

        mock_pool.close.assert_called_once()
        assert manager.is_connected is False


class TestMongoDBManager:
    """Test MongoDBManager"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            database="testdb",
            username="user",
            password="pass",
        )

    def test_init(self, config):
        """Test MongoDB manager initialization"""
        manager = MongoDBManager(config)

        assert manager.config == config
        assert manager.client is None
        assert manager.database is None
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, config):
        """Test successful MongoDB connection"""
        manager = MongoDBManager(config)

        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})

        with patch("infrastructure.database_ecosystem.motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client):
            result = await manager.connect()

        assert result is True
        assert manager.is_connected is True
        assert manager.metrics.total_connections == 1

    @pytest.mark.asyncio
    async def test_connect_failure(self, config):
        """Test MongoDB connection failure"""
        manager = MongoDBManager(config)

        with patch(
            "infrastructure.database_ecosystem.motor.motor_asyncio.AsyncIOMotorClient",
            side_effect=Exception("Connection failed"),
        ):
            result = await manager.connect()

        assert result is False
        assert manager.metrics.failed_connections == 1

    @pytest.mark.asyncio
    async def test_find_documents_success(self, config):
        """Test successful document finding"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()

        # Mock documents with ObjectId
        from bson import ObjectId

        doc_id = ObjectId()
        mock_cursor.to_list = AsyncMock(return_value=[{"_id": doc_id, "name": "test"}])
        mock_cursor.limit = MagicMock(return_value=mock_cursor)  # limit() returns self

        mock_collection.find.return_value = mock_cursor
        mock_database.__getitem__.return_value = mock_collection

        manager.database = mock_database

        result = await manager.find_documents("users", {"name": "test"}, limit=10)

        assert len(result) == 1
        assert result[0]["name"] == "test"
        assert isinstance(result[0]["_id"], str)
        assert manager.metrics.successful_queries == 1

    @pytest.mark.asyncio
    async def test_find_documents_not_connected(self, config):
        """Test finding documents when not connected"""
        manager = MongoDBManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.find_documents("users")

    @pytest.mark.asyncio
    async def test_find_documents_failure(self, config):
        """Test document finding failure"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(side_effect=Exception("Query failed"))
        mock_cursor.limit = MagicMock(return_value=mock_cursor)  # limit() returns self

        mock_collection.find.return_value = mock_cursor
        mock_database.__getitem__.return_value = mock_collection

        manager.database = mock_database

        with pytest.raises(Exception, match="Query failed"):
            await manager.find_documents("users")

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_insert_document_success(self, config):
        """Test successful document insertion"""
        manager = MongoDBManager(config)

        from bson import ObjectId

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        inserted_id = ObjectId()
        mock_result = MagicMock()
        mock_result.inserted_id = inserted_id
        mock_collection.insert_one = AsyncMock(return_value=mock_result)

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        result = await manager.insert_document("users", {"name": "test", "email": "test@example.com"})

        assert isinstance(result, str)
        assert manager.metrics.successful_queries == 1

    @pytest.mark.asyncio
    async def test_insert_document_not_connected(self, config):
        """Test document insertion when not connected"""
        manager = MongoDBManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.insert_document("users", {"name": "test"})

    @pytest.mark.asyncio
    async def test_insert_document_failure(self, config):
        """Test document insertion failure"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.insert_one = AsyncMock(side_effect=Exception("Insert failed"))

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        with pytest.raises(Exception, match="Insert failed"):
            await manager.insert_document("users", {"name": "test"})

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_update_document_success(self, config):
        """Test successful document update"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        mock_result = MagicMock()
        mock_result.modified_count = 5
        mock_collection.update_many = AsyncMock(return_value=mock_result)

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        result = await manager.update_document("users", {"status": "active"}, {"last_login": "2025-11-21"})

        assert result == 5
        assert manager.metrics.successful_queries == 1

    @pytest.mark.asyncio
    async def test_update_document_not_connected(self, config):
        """Test document update when not connected"""
        manager = MongoDBManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.update_document("users", {}, {})

    @pytest.mark.asyncio
    async def test_update_document_failure(self, config):
        """Test document update failure"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.update_many = AsyncMock(side_effect=Exception("Update failed"))

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        with pytest.raises(Exception, match="Update failed"):
            await manager.update_document("users", {}, {})

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_create_indexes_success(self, config):
        """Test successful MongoDB index creation"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock(return_value=None)

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        result = await manager.create_indexes()

        assert result is True
        assert mock_collection.create_index.call_count > 0

    @pytest.mark.asyncio
    async def test_create_indexes_failure(self, config):
        """Test MongoDB index creation failure"""
        manager = MongoDBManager(config)

        mock_database = MagicMock()
        mock_collection = AsyncMock()
        mock_collection.create_index = AsyncMock(side_effect=Exception("Index creation failed"))

        mock_database.__getitem__.return_value = mock_collection
        manager.database = mock_database

        result = await manager.create_indexes()

        assert result is False

    def test_update_response_time_mongodb(self, config):
        """Test MongoDB response time update"""
        manager = MongoDBManager(config)

        manager._update_response_time(0.3)
        assert manager.metrics.average_response_time == 0.3

        manager._update_response_time(0.1)
        # EMA: 0.1 * 0.1 + 0.9 * 0.3 = 0.28
        assert manager.metrics.average_response_time == pytest.approx(0.28, rel=1e-2)

    @pytest.mark.asyncio
    async def test_close(self, config):
        """Test MongoDB connection closure"""
        manager = MongoDBManager(config)

        mock_client = MagicMock()
        manager.client = mock_client
        manager.is_connected = True

        await manager.close()

        mock_client.close.assert_called_once()
        assert manager.is_connected is False


class TestClickHouseManager:
    """Test ClickHouseManager"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return DatabaseConfig(
            db_type=DatabaseType.CLICKHOUSE,
            host="localhost",
            port=9000,
            database="testdb",
            username="default",
            password="",
        )

    def test_init(self, config):
        """Test ClickHouse manager initialization"""
        manager = ClickHouseManager(config)

        assert manager.config == config
        assert manager.client is None
        assert manager.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_success(self, config):
        """Test successful ClickHouse connection"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[[1]])

        with patch("infrastructure.database_ecosystem.ClickHouseClient", return_value=mock_client):
            result = await manager.connect()

        assert result is True
        assert manager.is_connected is True
        assert manager.metrics.total_connections == 1

    @pytest.mark.asyncio
    async def test_connect_failure(self, config):
        """Test ClickHouse connection failure"""
        manager = ClickHouseManager(config)

        with patch("infrastructure.database_ecosystem.ClickHouseClient", side_effect=Exception("Connection failed")):
            result = await manager.connect()

        assert result is False
        assert manager.metrics.failed_connections == 1

    @pytest.mark.asyncio
    async def test_execute_query_success(self, config):
        """Test successful ClickHouse query execution"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[[1, "test"], [2, "test2"]])

        manager.client = mock_client

        result = await manager.execute_query("SELECT * FROM users")

        assert len(result) == 2
        assert result[0]["col_0"] == 1
        assert result[0]["col_1"] == "test"
        assert manager.metrics.successful_queries == 1

    @pytest.mark.asyncio
    async def test_execute_query_with_params(self, config):
        """Test query execution with parameters"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[[1]])

        manager.client = mock_client

        result = await manager.execute_query("SELECT * FROM users WHERE id = %(id)s", {"id": 1})

        mock_client.execute.assert_called_once()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_execute_query_empty_result(self, config):
        """Test query execution with empty result"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[])

        manager.client = mock_client

        result = await manager.execute_query("SELECT * FROM users WHERE id = 999")

        assert result == []

    @pytest.mark.asyncio
    async def test_execute_query_not_connected(self, config):
        """Test query execution when not connected"""
        manager = ClickHouseManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, config):
        """Test query execution failure"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(side_effect=Exception("Query failed"))

        manager.client = mock_client

        with pytest.raises(Exception, match="Query failed"):
            await manager.execute_query("SELECT * FROM invalid_table")

        assert manager.metrics.failed_queries == 1

    @pytest.mark.asyncio
    async def test_create_tables_success(self, config):
        """Test successful table creation"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=None)

        manager.client = mock_client

        result = await manager.create_tables()

        assert result is True
        assert mock_client.execute.call_count >= 3  # At least 3 tables

    @pytest.mark.asyncio
    async def test_create_tables_not_connected(self, config):
        """Test table creation when not connected"""
        manager = ClickHouseManager(config)

        with pytest.raises(Exception, match="Database not connected"):
            await manager.create_tables()

    @pytest.mark.asyncio
    async def test_create_tables_failure(self, config):
        """Test table creation failure"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        mock_client.execute = MagicMock(side_effect=Exception("Table creation failed"))

        manager.client = mock_client

        result = await manager.create_tables()

        assert result is False

    def test_update_response_time_clickhouse(self, config):
        """Test ClickHouse response time update"""
        manager = ClickHouseManager(config)

        manager._update_response_time(0.2)
        assert manager.metrics.average_response_time == 0.2

    def test_close(self, config):
        """Test ClickHouse connection closure"""
        manager = ClickHouseManager(config)

        mock_client = MagicMock()
        manager.client = mock_client
        manager.is_connected = True

        manager.close()

        mock_client.disconnect.assert_called_once()
        assert manager.is_connected is False


class TestDatabaseEcosystem:
    """Test DatabaseEcosystem"""

    def test_init(self):
        """Test ecosystem initialization"""
        ecosystem = DatabaseEcosystem()

        assert ecosystem.databases == {}
        assert ecosystem.configs == {}
        assert ecosystem.backup_configs == {}

    @pytest.mark.asyncio
    async def test_add_database_postgresql_success(self):
        """Test adding PostgreSQL database"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        # Mock connection
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.execute = AsyncMock(return_value=None)

        with patch("infrastructure.database_ecosystem.asyncpg.create_pool", new_callable=AsyncMock, return_value=mock_pool):
            result = await ecosystem.add_database("primary", config)

        assert result is True
        assert "primary" in ecosystem.databases
        assert ecosystem.databases["primary"].is_connected is True

    @pytest.mark.asyncio
    async def test_add_database_mongodb_success(self):
        """Test adding MongoDB database"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            database="testdb",
            username="user",
            password="pass",
        )

        mock_client = AsyncMock()
        mock_client.admin.command = AsyncMock(return_value={"ok": 1})

        with patch("infrastructure.database_ecosystem.motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_client):
            result = await ecosystem.add_database("mongo", config)

        assert result is True
        assert "mongo" in ecosystem.databases

    @pytest.mark.asyncio
    async def test_add_database_clickhouse_success(self):
        """Test adding ClickHouse database"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.CLICKHOUSE,
            host="localhost",
            port=9000,
            database="analytics",
            username="default",
            password="",
        )

        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[[1]])

        with patch("infrastructure.database_ecosystem.ClickHouseClient", return_value=mock_client):
            result = await ecosystem.add_database("analytics", config)

        assert result is True
        assert "analytics" in ecosystem.databases

    @pytest.mark.asyncio
    async def test_add_database_unsupported_type(self):
        """Test adding unsupported database type"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.REDIS,
            host="localhost",
            port=6379,
            database="0",
            username="",
            password="",
        )

        result = await ecosystem.add_database("cache", config)

        assert result is False

    @pytest.mark.asyncio
    async def test_add_database_connection_failure(self):
        """Test adding database with connection failure"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="invalid-host",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        with patch(
            "infrastructure.database_ecosystem.asyncpg.create_pool", side_effect=Exception("Connection failed")
        ):
            result = await ecosystem.add_database("primary", config)

        assert result is False

    def test_get_database_success(self):
        """Test getting database by name"""
        ecosystem = DatabaseEcosystem()

        mock_manager = MagicMock()
        ecosystem.databases["test"] = mock_manager

        result = ecosystem.get_database("test")

        assert result == mock_manager

    def test_get_database_not_found(self):
        """Test getting non-existent database"""
        ecosystem = DatabaseEcosystem()

        with pytest.raises(ValueError, match="Database not found: nonexistent"):
            ecosystem.get_database("nonexistent")

    @pytest.mark.asyncio
    async def test_initialize_all_indexes_success(self):
        """Test initializing indexes for all databases"""
        ecosystem = DatabaseEcosystem()

        # Use spec to limit which attributes exist
        mock_pg_manager = MagicMock(spec=["create_indexes", "is_connected", "metrics"])
        mock_pg_manager.create_indexes = AsyncMock(return_value=True)

        mock_ch_manager = MagicMock(spec=["create_tables", "is_connected", "metrics"])
        mock_ch_manager.create_tables = AsyncMock(return_value=True)

        ecosystem.databases = {
            "postgres": mock_pg_manager,
            "clickhouse": mock_ch_manager,
        }

        results = await ecosystem.initialize_all_indexes()

        assert results["postgres"] is True
        assert results["clickhouse"] is True

    @pytest.mark.asyncio
    async def test_initialize_all_indexes_failure(self):
        """Test index initialization with failures"""
        ecosystem = DatabaseEcosystem()

        mock_manager = MagicMock(spec=["create_indexes", "is_connected", "metrics"])
        mock_manager.create_indexes = AsyncMock(side_effect=Exception("Index creation failed"))

        ecosystem.databases = {"test": mock_manager}

        results = await ecosystem.initialize_all_indexes()

        assert results["test"] is False

    @pytest.mark.asyncio
    async def test_initialize_all_indexes_no_method(self):
        """Test index initialization with manager without create methods"""
        ecosystem = DatabaseEcosystem()

        # Manager with only basic attributes, no create methods
        mock_manager = MagicMock(spec=["is_connected", "metrics"])

        ecosystem.databases = {"test": mock_manager}

        results = await ecosystem.initialize_all_indexes()

        assert results["test"] is True

    @pytest.mark.asyncio
    async def test_get_ecosystem_metrics(self):
        """Test getting ecosystem metrics"""
        ecosystem = DatabaseEcosystem()

        mock_manager = MagicMock()
        mock_manager.is_connected = True
        mock_manager.metrics.to_dict.return_value = {
            "total_connections": 10,
            "successful_queries": 100,
        }
        mock_manager.get_pool_status = AsyncMock(return_value={"size": 10, "checked_out": 2})

        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        ecosystem.databases = {"primary": mock_manager}
        ecosystem.configs = {"primary": config}

        metrics = await ecosystem.get_ecosystem_metrics()

        assert "primary" in metrics
        assert metrics["primary"]["type"] == "postgresql"
        assert metrics["primary"]["is_connected"] is True
        assert "connection_metrics" in metrics["primary"]
        assert "pool_status" in metrics["primary"]

    @pytest.mark.asyncio
    async def test_get_ecosystem_metrics_error(self):
        """Test getting metrics with error"""
        ecosystem = DatabaseEcosystem()

        mock_manager = MagicMock()
        mock_manager.is_connected = True
        mock_manager.metrics.to_dict.side_effect = Exception("Metrics error")

        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        ecosystem.databases = {"primary": mock_manager}
        ecosystem.configs = {"primary": config}

        metrics = await ecosystem.get_ecosystem_metrics()

        assert "primary" in metrics
        assert "error" in metrics["primary"]

    @pytest.mark.asyncio
    async def test_health_check_all_healthy(self):
        """Test health check with all databases healthy"""
        ecosystem = DatabaseEcosystem()

        # Create real manager instances with mocked connections
        config_pg = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        config_mongo = DatabaseConfig(
            db_type=DatabaseType.MONGODB,
            host="localhost",
            port=27017,
            database="testdb",
            username="user",
            password="pass",
        )

        mock_pg_manager = PostgreSQLManager(config_pg)
        mock_pg_manager.is_connected = True
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.return_value = mock_conn
        mock_acquire_context.__aexit__.return_value = AsyncMock()
        mock_pool.acquire.return_value = mock_acquire_context
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pg_manager.pool = mock_pool

        mock_mongo_manager = MongoDBManager(config_mongo)
        mock_mongo_manager.is_connected = True
        mock_database = MagicMock()
        mock_collection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_cursor.limit = MagicMock(return_value=mock_cursor)  # limit() returns self
        mock_collection.find.return_value = mock_cursor
        mock_database.__getitem__.return_value = mock_collection
        mock_mongo_manager.database = mock_database

        ecosystem.databases = {
            "postgres": mock_pg_manager,
            "mongo": mock_mongo_manager,
        }
        ecosystem.configs = {
            "postgres": config_pg,
            "mongo": config_mongo,
        }

        health = await ecosystem.health_check()

        assert health["overall_status"] == "healthy"
        assert health["total_databases"] == 2
        assert health["healthy_databases"] == 2
        assert health["databases"]["postgres"]["status"] == "healthy"
        assert health["databases"]["mongo"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_degraded(self):
        """Test health check with degraded status"""
        ecosystem = DatabaseEcosystem()

        # Create a real PostgreSQLManager instance but mock the pool
        config = DatabaseConfig(
            db_type=DatabaseType.POSTGRESQL,
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass",
        )

        mock_manager = PostgreSQLManager(config)
        mock_manager.is_connected = True

        # Mock the pool to simulate connection failure
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_acquire_context = AsyncMock()
        mock_acquire_context.__aenter__.side_effect = Exception("Connection timeout")
        mock_pool.acquire.return_value = mock_acquire_context

        mock_manager.pool = mock_pool

        ecosystem.databases = {"postgres": mock_manager}
        ecosystem.configs = {"postgres": config}

        health = await ecosystem.health_check()

        assert health["overall_status"] == "degraded"
        assert health["healthy_databases"] == 0
        assert health["databases"]["postgres"]["status"] == "unhealthy"
        assert "error" in health["databases"]["postgres"]

    @pytest.mark.asyncio
    async def test_health_check_clickhouse(self):
        """Test health check for ClickHouse"""
        ecosystem = DatabaseEcosystem()

        config = DatabaseConfig(
            db_type=DatabaseType.CLICKHOUSE,
            host="localhost",
            port=9000,
            database="analytics",
            username="default",
            password="",
        )

        mock_manager = ClickHouseManager(config)
        mock_manager.is_connected = True

        # Mock the client
        mock_client = MagicMock()
        mock_client.execute = MagicMock(return_value=[[1]])
        mock_manager.client = mock_client

        ecosystem.databases = {"clickhouse": mock_manager}
        ecosystem.configs = {"clickhouse": config}

        health = await ecosystem.health_check()

        assert health["overall_status"] == "healthy"
        assert health["databases"]["clickhouse"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_close_all(self):
        """Test closing all database connections"""
        ecosystem = DatabaseEcosystem()

        mock_async_manager = AsyncMock()
        mock_async_manager.close = AsyncMock()

        mock_sync_manager = MagicMock()
        mock_sync_manager.close = MagicMock()

        ecosystem.databases = {
            "async_db": mock_async_manager,
            "sync_db": mock_sync_manager,
        }

        await ecosystem.close_all()

        mock_async_manager.close.assert_called_once()
        mock_sync_manager.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_all_with_errors(self):
        """Test closing all connections with errors"""
        ecosystem = DatabaseEcosystem()

        mock_manager = AsyncMock()
        mock_manager.close = AsyncMock(side_effect=Exception("Close failed"))

        ecosystem.databases = {"test": mock_manager}

        # Should not raise exception
        await ecosystem.close_all()

        mock_manager.close.assert_called_once()


class TestGlobalInstance:
    """Test global database_ecosystem instance"""

    def test_global_instance_exists(self):
        """Test that global instance is created"""
        assert database_ecosystem is not None
        assert isinstance(database_ecosystem, DatabaseEcosystem)
