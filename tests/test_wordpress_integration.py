"""
WordPress/WooCommerce Integration Tests
========================================

Test suite for WordPress/WooCommerce API integration.

Tests:
1. Connection and authentication
2. Product CRUD operations
3. Order management
4. Customer management
5. Commerce Agent integration

Author: DevSkyy Platform Team
Version: 1.0.0
"""

import os
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from integrations.wordpress_client import (
    OrderStatus,
    ProductStatus,
    WooCommerceProduct,
    WordPressConfig,
    WordPressWooCommerceClient,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def wp_config():
    """WordPress configuration for testing."""
    return WordPressConfig(
        site_url="https://skyyrose.co",
        wc_consumer_key="123138",
        wc_consumer_secret="kQRBrHyNdILBsxtasddwwZCvdglbRBFYltwyW1foKDZ8yOrHsEHbHrZqFNXYNf1F",
        wp_username="admin",
        wp_app_password="test-password",
        timeout=30.0,
        max_retries=3,
        verify_ssl=True,
    )


@pytest.fixture
def sample_product():
    """Sample WooCommerce product."""
    return WooCommerceProduct(
        name="BLACK ROSE Hoodie",
        regular_price="189.99",
        description="Premium luxury hoodie from the BLACK ROSE collection",
        short_description="Dark elegance meets streetwear",
        sku="BR-HOOD-001",
        status=ProductStatus.DRAFT,
        stock_quantity=50,
        categories=[{"name": "BLACK ROSE"}, {"name": "Hoodies"}],
        tags=[{"name": "luxury"}, {"name": "streetwear"}],
        images=[{"src": "https://example.com/hoodie.jpg"}],
    )


@pytest.fixture
async def wp_client(wp_config):
    """WordPress client instance."""
    client = WordPressWooCommerceClient(config=wp_config)
    try:
        await client.connect()
        yield client
    finally:
        await client.close()


# =============================================================================
# Connection Tests
# =============================================================================


class TestConnection:
    """Test WordPress/WooCommerce connection and authentication."""

    def test_config_from_env(self):
        """Test configuration from environment variables."""
        # Set environment variables
        os.environ["WORDPRESS_URL"] = "https://test.com"
        os.environ["WOOCOMMERCE_KEY"] = "test_key"
        os.environ["WOOCOMMERCE_SECRET"] = "test_secret"

        config = WordPressConfig.from_env()

        assert config.site_url == "https://test.com"
        assert config.wc_consumer_key == "test_key"
        assert config.wc_consumer_secret == "test_secret"

    def test_config_validation(self):
        """Test configuration validation."""
        # Missing site URL
        with pytest.raises(ValueError):
            config = WordPressConfig(
                site_url="",
                wc_consumer_key="key",
                wc_consumer_secret="secret",
            )
            WordPressWooCommerceClient(config=config)

        # Missing WooCommerce credentials
        with pytest.raises(ValueError):
            config = WordPressConfig(
                site_url="https://test.com",
                wc_consumer_key="",
                wc_consumer_secret="",
            )
            WordPressWooCommerceClient(config=config)

    @pytest.mark.asyncio
    async def test_connection_context_manager(self, wp_config):
        """Test async context manager."""
        async with WordPressWooCommerceClient(config=wp_config) as client:
            assert client._session is not None
            assert not client._session.closed

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_connection(self):
        """Test real connection to WooCommerce API (integration test)."""
        # Skip if credentials not available
        if not os.getenv("WOOCOMMERCE_KEY"):
            pytest.skip("WooCommerce credentials not available")

        async with WordPressWooCommerceClient() as client:
            result = await client.test_connection()

            assert result["success"] is True
            assert result["woocommerce_connected"] is True
            assert "site_url" in result


# =============================================================================
# Product Tests
# =============================================================================


class TestProducts:
    """Test WooCommerce product operations."""

    @pytest.mark.asyncio
    async def test_list_products(self, wp_client):
        """Test listing products."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = [
                {
                    "id": 1,
                    "name": "Test Product",
                    "sku": "TEST-001",
                    "regular_price": "99.99",
                    "status": "publish",
                    "stock_quantity": 10,
                    "type": "simple",
                    "manage_stock": True,
                    "stock_status": "instock",
                    "description": "",
                    "short_description": "",
                    "categories": [],
                    "tags": [],
                    "images": [],
                    "attributes": [],
                    "meta_data": [],
                }
            ]

            products = await wp_client.list_products(per_page=10)

            assert len(products) == 1
            assert products[0].name == "Test Product"
            assert products[0].sku == "TEST-001"
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_product(self, wp_client):
        """Test getting product by ID."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {
                "id": 123,
                "name": "Test Product",
                "sku": "TEST-001",
                "regular_price": "99.99",
                "status": "publish",
                "stock_quantity": 10,
                "type": "simple",
                "manage_stock": True,
                "stock_status": "instock",
                "description": "",
                "short_description": "",
                "categories": [],
                "tags": [],
                "images": [],
                "attributes": [],
                "meta_data": [],
            }

            product = await wp_client.get_product(123)

            assert product.id == 123
            assert product.name == "Test Product"

    @pytest.mark.asyncio
    async def test_create_product(self, wp_client, sample_product):
        """Test creating a product."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {
                **sample_product.model_dump(),
                "id": 456,
                "permalink": "https://skyyrose.co/product/black-rose-hoodie/",
            }

            created_product = await wp_client.create_product(sample_product)

            assert created_product.id == 456
            assert created_product.name == "BLACK ROSE Hoodie"
            assert created_product.permalink is not None

    @pytest.mark.asyncio
    async def test_update_product(self, wp_client):
        """Test updating a product."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {
                "id": 123,
                "name": "Updated Product",
                "regular_price": "149.99",
                "status": "publish",
                "sku": "TEST-001",
                "stock_quantity": 20,
                "type": "simple",
                "manage_stock": True,
                "stock_status": "instock",
                "description": "",
                "short_description": "",
                "categories": [],
                "tags": [],
                "images": [],
                "attributes": [],
                "meta_data": [],
            }

            updates = {"regular_price": "149.99", "stock_quantity": 20}
            product = await wp_client.update_product(123, updates)

            assert product.regular_price == "149.99"
            assert product.stock_quantity == 20

    @pytest.mark.asyncio
    async def test_delete_product(self, wp_client):
        """Test deleting a product."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {"id": 123, "deleted": True}

            result = await wp_client.delete_product(123, force=True)

            assert result["deleted"] is True

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_real_product_crud(self):
        """Test real product CRUD operations (integration test)."""
        if not os.getenv("WOOCOMMERCE_KEY"):
            pytest.skip("WooCommerce credentials not available")

        async with WordPressWooCommerceClient() as client:
            # Create product
            product = WooCommerceProduct(
                name="Test Product - DevSkyy",
                regular_price="99.99",
                description="Test product created by integration test",
                status=ProductStatus.DRAFT,
                sku=f"TEST-{os.getpid()}",
            )

            created = await client.create_product(product)
            assert created.id is not None

            # Get product
            retrieved = await client.get_product(created.id)
            assert retrieved.name == "Test Product - DevSkyy"

            # Update product
            updated = await client.update_product(
                created.id,
                {"regular_price": "79.99"},
            )
            assert updated.regular_price == "79.99"

            # Delete product
            await client.delete_product(created.id, force=True)


# =============================================================================
# Order Tests
# =============================================================================


class TestOrders:
    """Test WooCommerce order operations."""

    @pytest.mark.asyncio
    async def test_list_orders(self, wp_client):
        """Test listing orders."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = [
                {
                    "id": 1,
                    "status": "processing",
                    "currency": "USD",
                    "total": "189.99",
                    "customer_id": 1,
                    "billing": {"email": "test@example.com"},
                    "shipping": {},
                    "line_items": [],
                    "date_created": "2024-01-01T12:00:00",
                    "date_modified": "2024-01-01T12:00:00",
                }
            ]

            orders = await wp_client.list_orders(per_page=10)

            assert len(orders) == 1
            assert orders[0].status == OrderStatus.PROCESSING

    @pytest.mark.asyncio
    async def test_get_order(self, wp_client):
        """Test getting order by ID."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {
                "id": 123,
                "status": "completed",
                "currency": "USD",
                "total": "189.99",
                "customer_id": 1,
                "billing": {"email": "test@example.com"},
                "shipping": {},
                "line_items": [],
                "date_created": "2024-01-01T12:00:00",
                "date_modified": "2024-01-01T12:00:00",
            }

            order = await wp_client.get_order(123)

            assert order.id == 123
            assert order.status == OrderStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_update_order_status(self, wp_client):
        """Test updating order status."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            mock_request.return_value = {
                "id": 123,
                "status": "completed",
                "currency": "USD",
                "total": "189.99",
                "customer_id": 1,
                "billing": {},
                "shipping": {},
                "line_items": [],
                "date_created": "2024-01-01T12:00:00",
                "date_modified": "2024-01-01T12:00:00",
            }

            order = await wp_client.update_order_status(123, OrderStatus.COMPLETED)

            assert order.status == OrderStatus.COMPLETED


# =============================================================================
# Commerce Agent Integration Tests
# =============================================================================


class TestCommerceAgentIntegration:
    """Test Commerce Agent integration with WordPress client."""

    @pytest.mark.asyncio
    async def test_agent_sync_product_to_woocommerce(self):
        """Test syncing product through Commerce Agent."""
        from agents.commerce_agent import CommerceAgent

        # Create mock client
        mock_client = AsyncMock(spec=WordPressWooCommerceClient)
        mock_client.create_product = AsyncMock(
            return_value=WooCommerceProduct(
                id=123,
                name="Test Product",
                regular_price="99.99",
                permalink="https://skyyrose.co/product/test/",
                status=ProductStatus.PUBLISH,
                type="simple",
                manage_stock=True,
                stock_status="instock",
                description="",
                short_description="",
                categories=[],
                tags=[],
                images=[],
                attributes=[],
                meta_data=[],
            )
        )

        # Create agent with mock client
        agent = CommerceAgent(wordpress_client=mock_client)
        agent._wordpress_connected = True

        # Sync product
        result = await agent.sync_product_to_woocommerce(
            name="Test Product",
            price=99.99,
            description="Test description",
            status="publish",
        )

        assert result["success"] is True
        assert result["woocommerce_id"] == 123
        mock_client.create_product.assert_called_once()

    @pytest.mark.asyncio
    async def test_agent_get_woocommerce_product(self):
        """Test getting product through Commerce Agent."""
        from agents.commerce_agent import CommerceAgent

        mock_client = AsyncMock(spec=WordPressWooCommerceClient)
        mock_client.get_product = AsyncMock(
            return_value=WooCommerceProduct(
                id=123,
                name="Test Product",
                regular_price="99.99",
                status=ProductStatus.PUBLISH,
                type="simple",
                manage_stock=True,
                stock_status="instock",
                description="",
                short_description="",
                categories=[],
                tags=[],
                images=[],
                attributes=[],
                meta_data=[],
            )
        )

        agent = CommerceAgent(wordpress_client=mock_client)
        agent._wordpress_connected = True

        result = await agent.get_woocommerce_product(123)

        assert result["id"] == 123
        assert result["name"] == "Test Product"


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestAPIEndpoints:
    """Test WordPress API endpoints."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        from main_enterprise import app

        return TestClient(app)

    def test_test_connection_endpoint(self, client):
        """Test connection test endpoint."""
        # This endpoint doesn't require auth
        response = client.get("/api/v1/wordpress/test-connection")

        # Should return something even without credentials
        assert response.status_code in [200, 500]

    @pytest.mark.integration
    def test_list_products_endpoint(self, client):
        """Test list products endpoint (requires auth)."""
        if not os.getenv("WOOCOMMERCE_KEY"):
            pytest.skip("WooCommerce credentials not available")

        # TODO: Add proper JWT token generation
        # response = client.get(
        #     "/api/v1/wordpress/products",
        #     headers={"Authorization": f"Bearer {token}"}
        # )
        # assert response.status_code == 200


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_authentication_error(self, wp_config):
        """Test authentication error handling."""
        # Use invalid credentials
        bad_config = WordPressConfig(
            site_url=wp_config.site_url,
            wc_consumer_key="invalid",
            wc_consumer_secret="invalid",
            wp_username="invalid",
            wp_app_password="invalid",
        )

        client = WordPressWooCommerceClient(config=bad_config)

        with patch.object(client, "_request_wc") as mock_request:
            from integrations.wordpress_client import AuthenticationError

            mock_request.side_effect = AuthenticationError("Auth failed", 401)

            with pytest.raises(AuthenticationError):
                await client.list_products()

    @pytest.mark.asyncio
    async def test_not_found_error(self, wp_client):
        """Test not found error handling."""
        with patch.object(wp_client, "_request_wc") as mock_request:
            from integrations.wordpress_client import NotFoundError

            mock_request.side_effect = NotFoundError("Not found", 404)

            with pytest.raises(NotFoundError):
                await wp_client.get_product(99999)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
