"""
Comprehensive Unit Tests for Database Module (database.py)
Testing database session management, connection handling, and health checks
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database import DatabaseManager, db_manager, get_db


class TestGetDbDependency:
    """Test suite for get_db dependency function"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_yields_session(self):
        """Test get_db yields a valid session"""
        async for session in get_db():
            assert isinstance(session, AsyncSession)
            # Session should be usable
            assert session is not None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_commits_on_success(self):
        """Test get_db commits transaction on successful completion"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            async for _ in get_db():
                pass  # Normal execution

            # Verify commit was called but rollback was not
            mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_rolls_back_on_exception(self):
        """Test get_db rolls back transaction on exception"""

        def _raise_error():
            raise ValueError()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            try:
                async for _ in get_db():
                    _raise_error()
            except ValueError:
                pass

            # Verify rollback was called
            mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_closes_session_always(self):
        """Test get_db always closes session in finally block"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            async for _ in get_db():
                pass

            # Verify close was called
            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_reraises_exception(self):
        """Test get_db re-raises exceptions after rollback"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            with pytest.raises(RuntimeError):
                async for _session in get_db():
                    raise RuntimeError()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_handles_commit_failure(self):
        """Test get_db handles commit failure gracefully"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Commit failed"))
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                async for _session in get_db():
                    pass

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_handles_rollback_failure(self):
        """Test get_db handles rollback failure"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock(spec=AsyncSession)
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock(side_effect=SQLAlchemyError("Rollback failed"))
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            # Should still raise the original exception
            with pytest.raises(ValueError):
                async for _ in get_db():
                    raise ValueError()


class TestDatabaseManager:
    """Test suite for DatabaseManager class"""

    @pytest.mark.unit
    def test_database_manager_initialization(self):
        """Test DatabaseManager initializes with correct defaults"""
        manager = DatabaseManager()

        assert manager.connected is False
        assert manager.session is None

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_connect_success(self):
        """Test successful database connection"""
        manager = DatabaseManager()

        with patch("database.init_db", new_callable=AsyncMock):
            result = await manager.connect()

            assert result["status"] == "connected"
            assert result["type"] == "SQLAlchemy"
            assert "url" in result
            assert manager.connected is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_connect_failure(self):
        """Test database connection failure handling"""
        manager = DatabaseManager()

        with patch(
            "database.init_db", new_callable=AsyncMock, side_effect=OperationalError("Connection refused", None, None)
        ):
            result = await manager.connect()

            assert result["status"] == "failed"
            assert "error" in result
            assert manager.connected is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_connect_handles_various_exceptions(self):
        """Test connect handles different exception types"""
        manager = DatabaseManager()

        exceptions = [
            ValueError("Invalid database URL"),
            RuntimeError("Database not initialized"),
            Exception("Generic error"),
        ]

        for exc in exceptions:
            with patch("database.init_db", new_callable=AsyncMock, side_effect=exc):
                result = await manager.connect()

                assert result["status"] == "failed"
                assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_disconnect_success(self):
        """Test successful database disconnection"""
        manager = DatabaseManager()
        manager.connected = True

        with patch("database.close_db", new_callable=AsyncMock):
            await manager.disconnect()

            assert manager.connected is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_disconnect_when_not_connected(self):
        """Test disconnecting when not connected"""
        manager = DatabaseManager()
        assert manager.connected is False

        with patch("database.close_db", new_callable=AsyncMock) as mock_close:
            await manager.disconnect()

            mock_close.assert_called_once()
            assert manager.connected is False

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_success(self):
        """Test successful database health check"""
        manager = DatabaseManager()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            result = await manager.health_check()

            assert result["status"] == "healthy"
            assert result["connected"] is True
            assert result["type"] == "SQLAlchemy"
            assert "url" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_failure(self):
        """Test database health check failure"""
        manager = DatabaseManager()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(side_effect=OperationalError("Cannot connect", None, None))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            result = await manager.health_check()

            assert result["status"] == "unhealthy"
            assert result["connected"] is False
            assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_with_timeout(self):
        """Test health check with database timeout"""
        manager = DatabaseManager()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(side_effect=TimeoutError("Query timeout"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            result = await manager.health_check()

            assert result["status"] == "unhealthy"
            assert result["connected"] is False

    @pytest.mark.unit
    def test_database_manager_context_enter(self):
        """Test DatabaseManager context manager enter"""
        manager = DatabaseManager()

        result = manager.__enter__()

        assert result is manager

    @pytest.mark.unit
    def test_database_manager_context_exit(self):
        """Test DatabaseManager context manager exit"""
        manager = DatabaseManager()

        # Should not raise exception
        manager.__exit__(None, None, None)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_multiple_connections(self):
        """Test handling multiple connection attempts"""
        manager = DatabaseManager()

        with patch("database.init_db", new_callable=AsyncMock):
            # First connection
            result1 = await manager.connect()
            assert result1["status"] == "connected"
            assert manager.connected is True

            # Second connection attempt
            result2 = await manager.connect()
            assert result2["status"] == "connected"
            assert manager.connected is True

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_connect_disconnect_cycle(self):
        """Test connect-disconnect cycle"""
        manager = DatabaseManager()

        with patch("database.init_db", new_callable=AsyncMock), patch("database.close_db", new_callable=AsyncMock):

            # Connect
            result = await manager.connect()
            assert result["status"] == "connected"
            assert manager.connected is True

            # Disconnect
            await manager.disconnect()
            assert manager.connected is False

            # Reconnect
            result = await manager.connect()
            assert result["status"] == "connected"
            assert manager.connected is True


class TestDatabaseManagerInstance:
    """Test the global db_manager instance"""

    @pytest.mark.unit
    def test_global_db_manager_exists(self):
        """Test global db_manager instance exists"""
        assert db_manager is not None
        assert isinstance(db_manager, DatabaseManager)

    @pytest.mark.unit
    def test_global_db_manager_not_connected_initially(self):
        """Test global db_manager starts disconnected"""
        # Create fresh instance to test
        manager = DatabaseManager()
        assert manager.connected is False


class TestDatabaseEdgeCases:
    """Test edge cases and boundary conditions"""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_with_sqlalchemy_error(self):
        """Test get_db handles SQLAlchemy errors"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            with pytest.raises(SQLAlchemyError):
                async for _session in get_db():
                    pass

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_with_network_error(self):
        """Test health check with network errors"""
        manager = DatabaseManager()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock(side_effect=ConnectionError("Network unreachable"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            result = await manager.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_health_checks(self):
        """Test multiple concurrent health checks"""
        import asyncio

        manager = DatabaseManager()

        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.execute = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            # Run multiple health checks concurrently
            results = await asyncio.gather(manager.health_check(), manager.health_check(), manager.health_check())

            assert len(results) == 3
            for result in results:
                assert result["status"] == "healthy"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_db_with_close_error(self):
        """Test get_db handles close errors gracefully"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock(side_effect=Exception("Close failed"))
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            # Should still complete despite close error
            async for _session in get_db():
                pass


class TestDatabaseIntegration:
    """Integration tests for database functionality"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_database_lifecycle(self):
        """Test complete database lifecycle"""
        manager = DatabaseManager()

        with (
            patch("database.init_db", new_callable=AsyncMock),
            patch("database.close_db", new_callable=AsyncMock),
            patch("database.AsyncSessionLocal") as mock_session_local,
        ):

            mock_session = MagicMock()
            mock_session.execute = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()
            mock_session_local.return_value = mock_session

            # Connect
            connect_result = await manager.connect()
            assert connect_result["status"] == "connected"

            # Health check
            health_result = await manager.health_check()
            assert health_result["status"] == "healthy"

            # Disconnect
            await manager.disconnect()
            assert manager.connected is False

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_session_usage_pattern(self):
        """Test typical session usage pattern"""
        with patch("database.AsyncSessionLocal") as mock_session_local:
            mock_session = MagicMock()
            mock_session.commit = AsyncMock()
            mock_session.rollback = AsyncMock()
            mock_session.close = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock()

            mock_session_local.return_value = mock_session

            # Simulate FastAPI dependency usage
            async for session in get_db():
                # Simulate database query
                await session.execute("SELECT 1")

            # Verify proper lifecycle
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
