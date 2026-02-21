"""
Tests for CommandBus — CQRS Write Side
=======================================

TDD RED Phase — Commands are the write side of CQRS.
Each Command is handled by exactly one handler, which validates the
command, performs business logic, and returns domain Events.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.cqrs.command_bus import Command, CommandBus
from core.events.event_store import Event


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommand:
    """Test Command dataclass"""

    def test_command_has_required_fields(self):
        cmd = Command(
            command_type="CreateProduct",
            data={"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99},
            user_id="user-123",
        )
        assert cmd.command_type == "CreateProduct"
        assert cmd.data["sku"] == "br-001"
        assert cmd.user_id == "user-123"

    def test_command_correlation_id_auto_generated(self):
        """Each command gets a unique correlation_id for distributed tracing"""
        cmd1 = Command(command_type="CreateProduct", data={}, user_id="u-1")
        cmd2 = Command(command_type="CreateProduct", data={}, user_id="u-2")
        assert cmd1.correlation_id != cmd2.correlation_id
        assert len(cmd1.correlation_id) > 0


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandBus:
    """Test CommandBus routing, handling, and event emission"""

    @pytest.fixture
    def bus(self):
        return CommandBus()

    async def test_execute_command_calls_handler(self, bus):
        """
        execute() routes the command to its registered handler.
        The handler produces Events that are appended to the EventStore.
        """
        mock_handler = AsyncMock(
            return_value=[
                Event(event_type="ProductCreated", aggregate_id="p-1", data={"sku": "br-001"})
            ]
        )
        bus.register_handler("CreateProduct", mock_handler)

        cmd = Command(command_type="CreateProduct", data={"sku": "br-001"}, user_id="u-1")

        with patch("core.cqrs.command_bus.EventStore") as mock_store_cls:
            mock_store = MagicMock()
            mock_store.append = AsyncMock()
            mock_store_cls.return_value = mock_store

            await bus.execute(cmd)

            mock_handler.assert_called_once_with(cmd)
            # Events returned by handler should be persisted
            assert mock_store.append.call_count == 1

    async def test_unknown_command_raises_error(self, bus):
        """
        Executing a command with no registered handler raises ValueError.
        This prevents silent failures.
        """
        cmd = Command(command_type="UnknownCommand", data={}, user_id="u-1")

        with pytest.raises(ValueError, match="No handler for UnknownCommand"):
            await bus.execute(cmd)

    async def test_multiple_events_per_command(self, bus):
        """
        A single command can produce multiple events.
        All events must be persisted.
        """
        events = [
            Event(event_type="ProductCreated", aggregate_id="p-1", data={}),
            Event(event_type="InventoryInitialized", aggregate_id="p-1", data={"qty": 100}),
            Event(event_type="ProductActivated", aggregate_id="p-1", data={}),
        ]
        bus.register_handler("CreateProduct", AsyncMock(return_value=events))

        cmd = Command(command_type="CreateProduct", data={}, user_id="u-1")

        with patch("core.cqrs.command_bus.EventStore") as mock_store_cls:
            mock_store = MagicMock()
            mock_store.append = AsyncMock()
            mock_store_cls.return_value = mock_store

            await bus.execute(cmd)

            # 3 events → 3 append calls
            assert mock_store.append.call_count == 3

    async def test_handler_validation_raises_on_invalid_command(self, bus):
        """
        If a handler raises ValueError (validation failure),
        the CommandBus propagates it. No events are persisted.
        """
        async def strict_handler(cmd: Command):
            if not cmd.data.get("sku"):
                raise ValueError("sku is required")
            return [Event(event_type="ProductCreated", aggregate_id="p-1", data={})]

        bus.register_handler("CreateProduct", strict_handler)
        cmd = Command(command_type="CreateProduct", data={}, user_id="u-1")  # Missing sku

        with patch("core.cqrs.command_bus.EventStore") as mock_store_cls:
            mock_store = MagicMock()
            mock_store.append = AsyncMock()
            mock_store_cls.return_value = mock_store

            with pytest.raises(ValueError, match="sku is required"):
                await bus.execute(cmd)

            # No events should have been persisted
            mock_store.append.assert_not_called()

    async def test_register_handler_overrides_previous(self, bus):
        """
        Registering a second handler for the same command type replaces the first.
        """
        handler_v1 = AsyncMock(return_value=[])
        handler_v2 = AsyncMock(return_value=[])

        bus.register_handler("SomeCommand", handler_v1)
        bus.register_handler("SomeCommand", handler_v2)  # Override

        cmd = Command(command_type="SomeCommand", data={}, user_id="u-1")

        with patch("core.cqrs.command_bus.EventStore") as mock_store_cls:
            mock_store = MagicMock()
            mock_store.append = AsyncMock()
            mock_store_cls.return_value = mock_store

            await bus.execute(cmd)

            handler_v1.assert_not_called()
            handler_v2.assert_called_once()
