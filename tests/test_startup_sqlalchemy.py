#!/usr/bin/env python3
"""
Test suite for startup_sqlalchemy.py
Achieves ≥90% coverage per Truth Protocol Rule #8
"""

import logging
from pathlib import Path
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Mock the database module before importing startup_sqlalchemy
# This avoids import-time database connections and resolves database/ vs database.py conflict
mock_db_manager = Mock()
mock_db_manager.connect = AsyncMock()
mock_db_manager.disconnect = AsyncMock()

mock_database = Mock()
mock_database.db_manager = mock_db_manager
mock_database.init_db = AsyncMock()

sys.modules["database"] = mock_database
sys.modules["database_config"] = Mock()

from startup_sqlalchemy import DevSkyStartup, on_shutdown, on_startup, startup_handler


class TestDevSkyStartup:
    """Test suite for DevSkyStartup class"""

    def test_init(self):
        """Test DevSkyStartup initialization"""
        startup = DevSkyStartup()
        assert startup.db_connected is False
        assert startup.wordpress_service is None

    @pytest.mark.asyncio
    async def test_initialize_database_success(self):
        """Test successful database initialization"""
        startup = DevSkyStartup()

        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock) as mock_init_db, patch(
            "startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock
        ) as mock_connect:
            # Mock successful connection
            mock_connect.return_value = {"status": "connected", "type": "SQLAlchemy"}

            result = await startup.initialize_database()

            assert result is True
            assert startup.db_connected is True
            mock_init_db.assert_called_once()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_database_connection_failed(self):
        """Test database initialization with connection failure"""
        startup = DevSkyStartup()

        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock) as mock_init_db, patch(
            "startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock
        ) as mock_connect:
            # Mock failed connection
            mock_connect.return_value = {"status": "failed", "error": "Connection timeout"}

            result = await startup.initialize_database()

            assert result is False
            assert startup.db_connected is False
            mock_init_db.assert_called_once()
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_database_exception(self):
        """Test database initialization with exception"""
        startup = DevSkyStartup()

        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock) as mock_init_db:
            # Mock exception during initialization
            mock_init_db.side_effect = Exception("Database error")

            result = await startup.initialize_database()

            assert result is False
            assert startup.db_connected is False

    @pytest.mark.asyncio
    async def test_initialize_wordpress_service_no_url(self, monkeypatch):
        """Test WordPress initialization when URL not configured"""
        startup = DevSkyStartup()

        # Ensure WORDPRESS_URL is not set
        monkeypatch.delenv("WORDPRESS_URL", raising=False)

        result = await startup.initialize_wordpress_service()

        assert result is False
        assert startup.wordpress_service is None

    @pytest.mark.asyncio
    async def test_initialize_wordpress_service_success(self, monkeypatch):
        """Test successful WordPress service initialization"""
        startup = DevSkyStartup()

        # Set WordPress URL
        monkeypatch.setenv("WORDPRESS_URL", "https://example.com")

        # Create a mock module with the function
        mock_wordpress_module = MagicMock()
        mock_service = MagicMock()
        mock_wordpress_module.create_wordpress_direct_service = MagicMock(return_value=mock_service)

        with patch.dict("sys.modules", {"agent.modules.wordpress_direct_service": mock_wordpress_module}):
            result = await startup.initialize_wordpress_service()

            assert result is True
            assert startup.wordpress_service is mock_service
            mock_wordpress_module.create_wordpress_direct_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_wordpress_service_exception(self, monkeypatch):
        """Test WordPress initialization with exception"""
        startup = DevSkyStartup()

        # Set WordPress URL
        monkeypatch.setenv("WORDPRESS_URL", "https://example.com")

        # Create a mock module that raises an exception
        mock_wordpress_module = MagicMock()
        mock_wordpress_module.create_wordpress_direct_service = MagicMock(
            side_effect=Exception("WordPress connection failed")
        )

        with patch.dict("sys.modules", {"agent.modules.wordpress_direct_service": mock_wordpress_module}):
            result = await startup.initialize_wordpress_service()

            assert result is False
            assert startup.wordpress_service is None

    @pytest.mark.asyncio
    async def test_initialize_wordpress_service_import_error(self, monkeypatch):
        """Test WordPress initialization with import error"""
        startup = DevSkyStartup()

        # Set WordPress URL
        monkeypatch.setenv("WORDPRESS_URL", "https://example.com")

        # Simulate ImportError by not having the module
        with patch.dict("sys.modules", {"agent.modules.wordpress_direct_service": None}):
            result = await startup.initialize_wordpress_service()

            assert result is False
            assert startup.wordpress_service is None

    @pytest.mark.asyncio
    async def test_startup_with_database_success(self):
        """Test startup with successful database initialization"""
        startup = DevSkyStartup()

        with patch.object(startup, "initialize_database", new_callable=AsyncMock) as mock_db, patch.object(
            startup, "initialize_wordpress_service", new_callable=AsyncMock
        ) as mock_wp:
            mock_db.return_value = True
            mock_wp.return_value = True

            result = await startup.startup()

            assert result is True
            mock_db.assert_called_once()
            mock_wp.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_with_database_failure(self):
        """Test startup with database initialization failure"""
        startup = DevSkyStartup()

        with patch.object(startup, "initialize_database", new_callable=AsyncMock) as mock_db, patch.object(
            startup, "initialize_wordpress_service", new_callable=AsyncMock
        ) as mock_wp:
            mock_db.return_value = False
            mock_wp.return_value = False

            result = await startup.startup()

            assert result is True  # Startup still succeeds in memory-only mode
            mock_db.assert_called_once()
            mock_wp.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_with_db_connection(self):
        """Test shutdown with active database connection"""
        startup = DevSkyStartup()
        startup.db_connected = True

        with patch("startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock) as mock_disconnect:
            await startup.shutdown()

            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_shutdown_without_db_connection(self):
        """Test shutdown without database connection"""
        startup = DevSkyStartup()
        startup.db_connected = False

        with patch("startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock) as mock_disconnect:
            await startup.shutdown()

            # Should not call disconnect when not connected
            mock_disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_startup(self):
        """Test FastAPI on_startup event handler"""
        with patch.object(startup_handler, "startup", new_callable=AsyncMock) as mock_startup:
            await on_startup()
            mock_startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_shutdown(self):
        """Test FastAPI on_shutdown event handler"""
        with patch.object(startup_handler, "shutdown", new_callable=AsyncMock) as mock_shutdown:
            await on_shutdown()
            mock_shutdown.assert_called_once()

    def test_global_startup_handler_exists(self):
        """Test that global startup_handler instance is created"""
        assert startup_handler is not None
        assert isinstance(startup_handler, DevSkyStartup)

    @pytest.mark.asyncio
    async def test_initialize_database_logs_info(self, caplog):
        """Test that database initialization logs info messages"""
        startup = DevSkyStartup()

        with caplog.at_level(logging.INFO), patch(
            "startup_sqlalchemy.init_db", new_callable=AsyncMock
        ) as mock_init_db, patch("startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = {"status": "connected", "type": "SQLAlchemy"}

            await startup.initialize_database()

            # Check that info logs were generated
            assert any("Initializing database connection" in record.message for record in caplog.records)
            assert any("Database connection established" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_initialize_database_logs_warning_on_failure(self, caplog):
        """Test that database initialization logs warning on connection failure"""
        startup = DevSkyStartup()

        with caplog.at_level(logging.WARNING), patch(
            "startup_sqlalchemy.init_db", new_callable=AsyncMock
        ) as mock_init_db, patch("startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = {"status": "failed", "error": "Connection timeout"}

            await startup.initialize_database()

            assert any("Database connection issue" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_initialize_database_logs_error_on_exception(self, caplog):
        """Test that database initialization logs error on exception"""
        startup = DevSkyStartup()

        with caplog.at_level(logging.INFO), patch(
            "startup_sqlalchemy.init_db", new_callable=AsyncMock
        ) as mock_init_db:
            mock_init_db.side_effect = Exception("Database error")

            await startup.initialize_database()

            # Check for ERROR level message
            assert any(
                "Database initialization failed" in record.message and record.levelname == "ERROR"
                for record in caplog.records
            )
            # Check for INFO level message
            assert any(
                "Platform will run with in-memory storage only" in record.message and record.levelname == "INFO"
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_initialize_wordpress_logs_info_when_no_url(self, caplog, monkeypatch):
        """Test that WordPress initialization logs info when URL not configured"""
        startup = DevSkyStartup()

        monkeypatch.delenv("WORDPRESS_URL", raising=False)

        with caplog.at_level(logging.INFO):
            await startup.initialize_wordpress_service()

            assert any(
                "WordPress URL not configured, skipping WordPress service" in record.message
                for record in caplog.records
            )

    @pytest.mark.asyncio
    async def test_initialize_wordpress_logs_success(self, caplog, monkeypatch):
        """Test that WordPress initialization logs success"""
        startup = DevSkyStartup()

        monkeypatch.setenv("WORDPRESS_URL", "https://example.com")

        # Create a mock module
        mock_wordpress_module = MagicMock()
        mock_wordpress_module.create_wordpress_direct_service = MagicMock()

        with caplog.at_level(logging.INFO), patch.dict(
            "sys.modules", {"agent.modules.wordpress_direct_service": mock_wordpress_module}
        ):
            await startup.initialize_wordpress_service()

            assert any("Initializing WordPress service" in record.message for record in caplog.records)
            assert any("WordPress service initialized" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_initialize_wordpress_logs_warning_on_failure(self, caplog, monkeypatch):
        """Test that WordPress initialization logs warning on failure"""
        startup = DevSkyStartup()

        monkeypatch.setenv("WORDPRESS_URL", "https://example.com")

        # Create a mock module that raises an exception
        mock_wordpress_module = MagicMock()
        mock_wordpress_module.create_wordpress_direct_service = MagicMock(
            side_effect=Exception("WordPress connection failed")
        )

        with caplog.at_level(logging.WARNING), patch.dict(
            "sys.modules", {"agent.modules.wordpress_direct_service": mock_wordpress_module}
        ):
            await startup.initialize_wordpress_service()

            assert any("WordPress service initialization failed" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_startup_logs_messages(self, caplog):
        """Test that startup logs appropriate messages"""
        startup = DevSkyStartup()

        with caplog.at_level(logging.INFO), patch.object(
            startup, "initialize_database", new_callable=AsyncMock
        ) as mock_db, patch.object(startup, "initialize_wordpress_service", new_callable=AsyncMock) as mock_wp:
            mock_db.return_value = True
            mock_wp.return_value = True

            await startup.startup()

            assert any("Starting DevSkyy Enhanced Platform" in record.message for record in caplog.records)
            assert any("Platform started successfully with database" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_startup_logs_memory_only_mode(self, caplog):
        """Test that startup logs memory-only mode message"""
        startup = DevSkyStartup()

        with caplog.at_level(logging.INFO), patch.object(
            startup, "initialize_database", new_callable=AsyncMock
        ) as mock_db, patch.object(startup, "initialize_wordpress_service", new_callable=AsyncMock) as mock_wp:
            mock_db.return_value = False
            mock_wp.return_value = False

            await startup.startup()

            assert any("Platform started in memory-only mode" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_shutdown_logs_messages(self, caplog):
        """Test that shutdown logs appropriate messages"""
        startup = DevSkyStartup()
        startup.db_connected = True

        with caplog.at_level(logging.INFO), patch(
            "startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock
        ):
            await startup.shutdown()

            assert any("Shutting down DevSkyy Platform" in record.message for record in caplog.records)
            assert any("Database connection closed" in record.message for record in caplog.records)
            assert any("Shutdown complete" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_shutdown_without_db_logs(self, caplog):
        """Test that shutdown logs correctly when no database connection"""
        startup = DevSkyStartup()
        startup.db_connected = False

        with caplog.at_level(logging.INFO):
            await startup.shutdown()

            assert any("Shutting down DevSkyy Platform" in record.message for record in caplog.records)
            assert not any("Database connection closed" in record.message for record in caplog.records)
            assert any("Shutdown complete" in record.message for record in caplog.records)


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_initialize_database_with_partial_result(self):
        """Test database initialization with incomplete result dictionary"""
        startup = DevSkyStartup()

        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock), patch(
            "startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock
        ) as mock_connect:
            # Return dictionary without expected keys
            mock_connect.return_value = {}

            result = await startup.initialize_database()

            assert result is False
            assert startup.db_connected is False

    @pytest.mark.asyncio
    async def test_multiple_startups(self):
        """Test multiple consecutive startup calls"""
        startup = DevSkyStartup()

        with patch.object(startup, "initialize_database", new_callable=AsyncMock) as mock_db, patch.object(
            startup, "initialize_wordpress_service", new_callable=AsyncMock
        ) as mock_wp:
            mock_db.return_value = True
            mock_wp.return_value = True

            # Call startup multiple times
            result1 = await startup.startup()
            result2 = await startup.startup()

            assert result1 is True
            assert result2 is True
            assert mock_db.call_count == 2
            assert mock_wp.call_count == 2

    @pytest.mark.asyncio
    async def test_shutdown_multiple_times(self):
        """Test multiple consecutive shutdown calls"""
        startup = DevSkyStartup()
        startup.db_connected = True

        with patch("startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock) as mock_disconnect:
            # First shutdown
            await startup.shutdown()
            # Manually reset db_connected to simulate what would happen
            startup.db_connected = False

            # Second shutdown - should not call disconnect
            await startup.shutdown()

            # First call should disconnect, second should not (since db_connected is False)
            assert mock_disconnect.call_count == 1


class TestIntegration:
    """Integration tests for startup workflow"""

    @pytest.mark.asyncio
    async def test_full_startup_shutdown_cycle(self):
        """Test complete startup and shutdown cycle"""
        startup = DevSkyStartup()

        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock), patch(
            "startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock
        ) as mock_connect, patch(
            "startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock
        ) as mock_disconnect:
            mock_connect.return_value = {"status": "connected", "type": "SQLAlchemy"}

            # Full cycle
            startup_result = await startup.startup()
            assert startup_result is True
            assert startup.db_connected is True

            await startup.shutdown()

            mock_connect.assert_called()
            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_fastapi_event_handlers_integration(self):
        """Test FastAPI event handlers work with global startup_handler"""
        with patch("startup_sqlalchemy.init_db", new_callable=AsyncMock), patch(
            "startup_sqlalchemy.db_manager.connect", new_callable=AsyncMock
        ) as mock_connect, patch(
            "startup_sqlalchemy.db_manager.disconnect", new_callable=AsyncMock
        ) as mock_disconnect:
            mock_connect.return_value = {"status": "connected", "type": "SQLAlchemy"}

            # Simulate FastAPI lifecycle
            await on_startup()
            await on_shutdown()

            mock_connect.assert_called()
            mock_disconnect.assert_called()
