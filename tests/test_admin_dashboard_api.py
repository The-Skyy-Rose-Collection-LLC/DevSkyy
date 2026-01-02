"""
Tests for Admin Dashboard API
==============================

Tests for the admin dashboard API endpoints.

Coverage:
- Dashboard stats endpoint
- Product listing endpoint
- Sync job management
- Analytics endpoints
- Authorization
"""

from unittest.mock import AsyncMock, patch

import pytest

from api.admin_dashboard import (
    AdminDataStore,
    DashboardStats,
    ProductListResponse,
    SalesAnalytics,
    SyncJobListResponse,
    admin_dashboard_router,
)

# =============================================================================
# AdminDataStore Tests
# =============================================================================


class TestAdminDataStore:
    """Tests for AdminDataStore."""

    @pytest.fixture
    def store(self):
        """Create fresh data store."""
        return AdminDataStore()

    def test_store_initialization(self, store):
        """Should initialize with empty collections."""
        assert store._products == {}
        assert store._orders == []
        assert store._sync_jobs == {}

    def test_add_product(self, store):
        """Should add product to store."""
        store.add_product("SKR-001", {
            "name": "Test Product",
            "price": 99.99,
            "stock": 50,
        })

        assert "SKR-001" in store._products
        assert store._products["SKR-001"]["name"] == "Test Product"

    def test_get_product(self, store):
        """Should retrieve product by SKU."""
        store.add_product("SKR-001", {"name": "Test"})

        result = store.get_products()
        found = [p for p in result if p["sku"] == "SKR-001"]

        assert len(found) == 1
        assert found[0]["name"] == "Test"

    def test_get_nonexistent_product(self, store):
        """Should return empty list for nonexistent product."""
        result = store.get_products()

        assert result == []

    def test_list_products(self, store):
        """Should list all products."""
        for i in range(5):
            store.add_product(f"SKR-00{i}", {"name": f"Product {i}"})

        products = store.get_products()

        assert len(products) == 5

    def test_list_products_with_pagination(self, store):
        """Should paginate product list."""
        for i in range(10):
            store.add_product(f"SKR-{i:03d}", {"name": f"Product {i}"})

        products = store.get_products(skip=5, limit=3)

        assert len(products) == 3

    def test_add_sync_job(self, store):
        """Should add sync job."""
        store.add_sync_job("sync_123", {
            "product_sku": "SKR-001",
            "status": "queued",
        })

        assert "sync_123" in store._sync_jobs

    def test_list_sync_jobs(self, store):
        """Should list sync jobs."""
        for i in range(3):
            store.add_sync_job(
                f"sync_{i}",
                {
                    "product_sku": f"SKR-00{i}",
                    "status": "completed",
                    "started_at": f"2026-01-01T0{i}:00:00",
                }
            )

        jobs = store.get_sync_jobs()

        assert len(jobs) == 3

    def test_get_stats(self, store):
        """Should calculate stats."""
        for i in range(5):
            store.add_product(f"SKR-00{i}", {"name": f"Product {i}"})

        for i in range(3):
            store.add_sync_job(
                f"sync_{i}",
                {
                    "product_sku": f"SKR-00{i}",
                    "status": "completed" if i < 2 else "failed",
                    "started_at": f"2026-01-01T0{i}:00:00",
                }
            )

        stats = store.get_stats()

        assert stats["total_products"] == 5


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Tests for response model structures."""

    def test_dashboard_stats(self):
        """Should create DashboardStats."""
        stats = DashboardStats(
            total_products=100,
            synced_products=85,
            pending_sync=15,
            sync_jobs_today=10,
            successful_syncs=8,
            failed_syncs=2,
            models_generated=75,
            photoshoots_generated=60,
            last_sync_time="2025-01-01T12:00:00Z",
        )

        assert stats.total_products == 100
        assert stats.synced_products == 85
        assert stats.successful_syncs == 8

    def test_product_list_response(self):
        """Should create ProductListResponse."""
        response = ProductListResponse(
            products=[
                {"sku": "SKR-001", "name": "Product 1"},
                {"sku": "SKR-002", "name": "Product 2"},
            ],
            total=100,
            page=1,
            page_size=20,
            total_pages=5,
        )

        assert len(response.products) == 2
        assert response.total == 100
        assert response.total_pages == 5

    def test_sync_job_list_response(self):
        """Should create SyncJobListResponse."""
        response = SyncJobListResponse(
            jobs=[
                {
                    "job_id": "sync_1",
                    "product_sku": "SKR-001",
                    "status": "completed",
                },
            ],
            total=50,
            page=1,
            page_size=20,
        )

        assert len(response.jobs) == 1
        assert response.total == 50

    def test_sales_analytics(self):
        """Should create SalesAnalytics."""
        analytics = SalesAnalytics(
            period="last_30_days",
            total_revenue=15000.00,
            total_orders=150,
            average_order_value=100.00,
            top_products=[
                {"sku": "SKR-001", "sales": 50},
                {"sku": "SKR-002", "sales": 35},
            ],
            daily_breakdown=[
                {"date": "2025-01-01", "revenue": 500.00, "orders": 5},
            ],
        )

        assert analytics.total_revenue == 15000.00
        assert len(analytics.top_products) == 2


# =============================================================================
# Router Tests
# =============================================================================


class TestAdminRouter:
    """Tests for admin router endpoints."""

    def test_router_has_prefix(self):
        """Should have correct prefix."""
        assert admin_dashboard_router.prefix == "/admin"

    def test_router_has_tags(self):
        """Should have tags."""
        assert "Admin Dashboard" in admin_dashboard_router.tags

    def test_router_has_endpoints(self):
        """Should have expected endpoints."""
        routes = [r.path for r in admin_dashboard_router.routes]
        prefix = admin_dashboard_router.prefix

        assert f"{prefix}/stats" in routes
        assert f"{prefix}/products" in routes
        assert f"{prefix}/sync-jobs" in routes


# =============================================================================
# Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Tests for admin endpoint responses."""

    async def test_get_dashboard_stats(self):
        """Should return dashboard stats."""
        from api.admin_dashboard import get_dashboard_stats

        stats = await get_dashboard_stats()

        assert isinstance(stats, DashboardStats)
        assert stats.total_products >= 0

    async def test_list_products(self):
        """Should return product list."""
        from api.admin_dashboard import list_products

        response = await list_products(page=1, page_size=20)

        assert isinstance(response, ProductListResponse)
        assert response.page == 1
        assert response.page_size == 20

    async def test_list_products_with_search(self):
        """Should filter products by search."""
        from api.admin_dashboard import list_products

        response = await list_products(page=1, page_size=20, search="hoodie")

        assert isinstance(response, ProductListResponse)

    async def test_list_sync_jobs(self):
        """Should return sync job list."""
        from api.admin_dashboard import list_sync_jobs

        response = await list_sync_jobs(page=1, page_size=20)

        assert isinstance(response, SyncJobListResponse)

    async def test_list_sync_jobs_filtered(self):
        """Should filter sync jobs by status."""
        from api.admin_dashboard import list_sync_jobs

        response = await list_sync_jobs(page=1, page_size=20, status="completed")

        assert isinstance(response, SyncJobListResponse)

    async def test_get_sales_analytics(self):
        """Should return sales analytics."""
        from api.admin_dashboard import get_sales_analytics

        analytics = await get_sales_analytics(period="last_30_days")

        assert isinstance(analytics, SalesAnalytics)
        assert analytics.period == "last_30_days"


# =============================================================================
# Action Tests
# =============================================================================


@pytest.mark.asyncio
class TestAdminActions:
    """Tests for admin action endpoints."""

    async def test_trigger_sync_all(self):
        """Should trigger sync for all products."""
        from api.admin_dashboard import trigger_sync_all

        with patch(
            "api.admin_dashboard.catalog_sync_engine.sync_bulk",
            new_callable=AsyncMock,
        ) as mock_sync:
            mock_sync.return_value = []

            result = await trigger_sync_all()

            assert "message" in result or "queued" in result

    async def test_trigger_product_sync(self):
        """Should trigger sync for single product."""
        from api.admin_dashboard import trigger_product_sync

        with patch(
            "api.admin_dashboard.catalog_sync_engine.sync_product",
            new_callable=AsyncMock,
        ) as mock_sync:
            mock_sync.return_value = {
                "success": True,
                "wordpress_product_id": 12345,
            }

            result = await trigger_product_sync("SKR-001")

            assert result is not None

    async def test_regenerate_3d_model(self):
        """Should trigger 3D model regeneration."""
        from api.admin_dashboard import regenerate_3d_model

        with patch(
            "api.admin_dashboard.ai_3d_generator.generate_model",
            new_callable=AsyncMock,
        ) as mock_gen:
            mock_gen.return_value = {"model_path": "/path/to/model.glb"}

            result = await regenerate_3d_model("SKR-001")

            assert result is not None


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_integration(client, admin_headers):
    """Test dashboard endpoints with authenticated client."""
    # Get dashboard stats
    response = await client.get("/api/v1/admin/stats", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data

    # Get product list
    response = await client.get(
        "/api/v1/admin/products",
        params={"page": 1, "page_size": 10},
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "total" in data

    # Get sync jobs
    response = await client.get(
        "/api/v1/admin/sync-jobs",
        headers=admin_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dashboard_requires_auth(client):
    """Test dashboard endpoints require authentication."""
    # Try without auth headers
    response = await client.get("/api/v1/admin/stats")

    # Should return 401 or 403
    assert response.status_code in [401, 403]


__all__ = [
    "TestAdminDataStore",
    "TestResponseModels",
    "TestAdminRouter",
    "TestAdminEndpoints",
    "TestAdminActions",
]
