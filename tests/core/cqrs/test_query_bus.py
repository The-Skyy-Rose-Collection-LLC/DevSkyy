"""
Tests for QueryBus — CQRS Read Side
=====================================

TDD RED Phase — Queries hit read-optimized projections, NOT the write DB.
This separation enables independent scaling of reads vs writes.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from core.cqrs.query_bus import Query, QueryBus


@pytest.mark.unit
@pytest.mark.asyncio
class TestQuery:
    """Test Query dataclass"""

    def test_query_has_required_fields(self):
        q = Query(query_type="GetProduct", filters={"sku": "br-001"})
        assert q.query_type == "GetProduct"
        assert q.filters["sku"] == "br-001"

    def test_query_defaults_to_empty_filters(self):
        q = Query(query_type="ListProducts")
        assert q.filters == {}


@pytest.mark.unit
@pytest.mark.asyncio
class TestQueryBus:
    """Test QueryBus routing and read model access"""

    @pytest.fixture
    def bus(self):
        return QueryBus()

    async def test_execute_query_calls_handler(self, bus):
        """
        execute() routes to the registered handler and returns its result.
        """
        expected = {"sku": "br-001", "name": "Black Rose Crewneck", "price": 79.99}
        mock_handler = AsyncMock(return_value=expected)
        bus.register_handler("GetProduct", mock_handler)

        q = Query(query_type="GetProduct", filters={"sku": "br-001"})
        result = await bus.execute(q)

        mock_handler.assert_called_once_with(q)
        assert result == expected

    async def test_unknown_query_raises_error(self, bus):
        """Querying without a registered handler raises ValueError"""
        q = Query(query_type="NonExistentQuery", filters={})
        with pytest.raises(ValueError, match="No handler for NonExistentQuery"):
            await bus.execute(q)

    async def test_query_returns_none_for_missing_record(self, bus):
        """Handler returning None is valid (record not found)"""
        bus.register_handler("GetProduct", AsyncMock(return_value=None))
        q = Query(query_type="GetProduct", filters={"sku": "doesnt-exist"})
        result = await bus.execute(q)
        assert result is None

    async def test_list_query_returns_collection(self, bus):
        """
        List queries return a list (potentially empty).
        Handlers receive the full Query object including filters.
        """
        mock_products = [
            {"sku": "br-001", "name": "Black Rose Crewneck"},
            {"sku": "br-002", "name": "Black Rose Hoodie"},
        ]
        bus.register_handler("ListProducts", AsyncMock(return_value=mock_products))

        q = Query(query_type="ListProducts", filters={"collection": "black-rose", "limit": 20})
        result = await bus.execute(q)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_multiple_handlers_registered(self, bus):
        """Multiple query types can each have their own handler"""
        bus.register_handler("GetProduct", AsyncMock(return_value={"sku": "br-001"}))
        bus.register_handler("GetOrder", AsyncMock(return_value={"id": "order-1"}))

        product = await bus.execute(Query(query_type="GetProduct", filters={"sku": "br-001"}))
        order = await bus.execute(Query(query_type="GetOrder", filters={"id": "order-1"}))

        assert product["sku"] == "br-001"
        assert order["id"] == "order-1"
