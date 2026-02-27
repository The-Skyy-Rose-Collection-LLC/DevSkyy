"""Tests for WordPress Bridge Agent MCP tools.

The @tool decorator from claude_agent_sdk wraps each function into an
SdkMcpTool object. The original async function is accessible via the
.handler attribute.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestWordPressCoreTools:
    """Tests for the 8 WordPress core MCP tools."""

    @pytest.fixture
    def mock_wp_client(self):
        """Mock WordPressClient with pre-configured return values."""
        client = AsyncMock()
        client.health_check.return_value = {
            "healthy": True,
            "woocommerce_api": True,
            "wordpress_api": True,
            "site_url": "https://skyyrose.co",
            "api_type": "wpcom",
        }
        client.list_products.return_value = [
            {"id": 1, "name": "Rose Gold Pendant", "sku": "SR-BR-001"}
        ]
        client.list_orders.return_value = [{"id": 100, "status": "processing"}]
        client.update_order_status.return_value = {"id": 100, "status": "completed"}
        client.create_page.return_value = {"id": 50, "title": {"rendered": "Test Page"}}
        client.upload_media_from_url.return_value = MagicMock(
            id=10,
            url="https://skyyrose.co/wp-content/uploads/test.jpg",
            title="Test Image",
            alt_text="A test image",
            mime_type="image/jpeg",
        )
        return client

    @pytest.fixture
    def mock_sync(self):
        """Mock WordPressProductSync with pre-configured return values."""
        sync = AsyncMock()
        sync.sync_product.return_value = MagicMock(
            sku="SR-BR-001", woo_id=1, action="updated", error=None
        )
        sync.sync_collection.return_value = [
            MagicMock(sku="SR-BR-001", woo_id=1, action="updated", error=None),
            MagicMock(sku="SR-BR-002", woo_id=2, action="created", error=None),
        ]
        return sync

    # -----------------------------------------------------------------------
    # wp_health_check
    # -----------------------------------------------------------------------

    async def test_wp_health_check(self, mock_wp_client):
        """wp_health_check should return site status JSON."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_health_check

            result = await wp_health_check.handler({})

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["healthy"] is True
        assert data["woocommerce_api"] is True
        mock_wp_client.health_check.assert_awaited_once()

    # -----------------------------------------------------------------------
    # wp_get_products
    # -----------------------------------------------------------------------

    async def test_wp_get_products(self, mock_wp_client):
        """wp_get_products should list products with count."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_get_products

            result = await wp_get_products.handler(
                {"collection": "signature", "page": 1, "per_page": 10}
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["count"] == 1
        assert data["products"][0]["sku"] == "SR-BR-001"
        mock_wp_client.list_products.assert_awaited_once_with(
            collection="signature", page=1, per_page=10
        )

    # -----------------------------------------------------------------------
    # wp_get_orders
    # -----------------------------------------------------------------------

    async def test_wp_get_orders(self, mock_wp_client):
        """wp_get_orders should list orders with count."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_get_orders

            result = await wp_get_orders.handler(
                {"status": "processing", "page": 1, "per_page": 20}
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["count"] == 1
        assert data["orders"][0]["status"] == "processing"
        mock_wp_client.list_orders.assert_awaited_once_with(
            status="processing", page=1, per_page=20
        )

    # -----------------------------------------------------------------------
    # wp_update_order
    # -----------------------------------------------------------------------

    async def test_wp_update_order(self, mock_wp_client):
        """wp_update_order should update order status and confirm."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_update_order

            result = await wp_update_order.handler(
                {"order_id": 100, "status": "completed"}
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert "Order 100 updated" in data["message"]
        assert data["order"]["status"] == "completed"
        mock_wp_client.update_order_status.assert_awaited_once_with(
            order_id=100, status="completed"
        )

    # -----------------------------------------------------------------------
    # wp_sync_product
    # -----------------------------------------------------------------------

    async def test_wp_sync_product(self, mock_sync):
        """wp_sync_product should sync a product and return result."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_product_sync",
            new_callable=AsyncMock,
            return_value=mock_sync,
        ):
            from agents.wordpress_bridge.mcp_server import wp_sync_product

            result = await wp_sync_product.handler(
                {
                    "sku": "SR-BR-001",
                    "name": "Rose Gold Pendant",
                    "collection": "black-rose",
                    "price": "299.00",
                    "description": "A beautiful rose gold pendant.",
                }
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["sku"] == "SR-BR-001"
        assert data["action"] == "updated"
        assert data["woo_id"] == 1
        mock_sync.sync_product.assert_awaited_once()

    # -----------------------------------------------------------------------
    # wp_sync_collection
    # -----------------------------------------------------------------------

    async def test_wp_sync_collection(self, mock_sync):
        """wp_sync_collection should batch-sync and return summary."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_product_sync",
            new_callable=AsyncMock,
            return_value=mock_sync,
        ):
            from agents.wordpress_bridge.mcp_server import wp_sync_collection

            result = await wp_sync_collection.handler({"collection": "black-rose"})

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["collection"] == "black-rose"
        assert data["synced"] == 2
        mock_sync.sync_collection.assert_awaited_once()

    # -----------------------------------------------------------------------
    # wp_create_page
    # -----------------------------------------------------------------------

    async def test_wp_create_page(self, mock_wp_client):
        """wp_create_page should create a page and return confirmation."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_create_page

            result = await wp_create_page.handler(
                {
                    "title": "About Us",
                    "slug": "about-us",
                    "content": "<h1>About SkyyRose</h1>",
                    "status": "draft",
                }
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert "About Us" in data["message"]
        assert data["page"]["id"] == 50
        mock_wp_client.create_page.assert_awaited_once_with(
            title="About Us",
            slug="about-us",
            content="<h1>About SkyyRose</h1>",
            status="draft",
        )

    # -----------------------------------------------------------------------
    # wp_upload_media
    # -----------------------------------------------------------------------

    async def test_wp_upload_media(self, mock_wp_client):
        """wp_upload_media should upload from URL and return media info."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            return_value=mock_wp_client,
        ):
            from agents.wordpress_bridge.mcp_server import wp_upload_media

            result = await wp_upload_media.handler(
                {
                    "image_url": "https://cdn.example.com/rose-pendant.jpg",
                    "title": "Rose Pendant",
                    "alt_text": "SkyyRose Rose Gold Pendant product photo",
                }
            )

        assert "is_error" not in result
        text = result["content"][0]["text"]
        data = json.loads(text)
        assert data["media_id"] == 10
        assert "skyyrose.co" in data["url"]
        mock_wp_client.upload_media_from_url.assert_awaited_once_with(
            image_url="https://cdn.example.com/rose-pendant.jpg",
            title="Rose Pendant",
            alt_text="SkyyRose Rose Gold Pendant product photo",
        )

    # -----------------------------------------------------------------------
    # Error handling
    # -----------------------------------------------------------------------

    async def test_tool_returns_error_on_exception(self):
        """All tools should return is_error=True when an exception occurs."""
        with patch(
            "agents.wordpress_bridge.mcp_server._get_wp_client",
            side_effect=ValueError("Missing env vars"),
        ):
            from agents.wordpress_bridge.mcp_server import wp_health_check

            result = await wp_health_check.handler({})

        assert result.get("is_error") is True
        assert "Missing env vars" in result["content"][0]["text"]
