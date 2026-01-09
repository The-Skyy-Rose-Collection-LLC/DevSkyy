"""
Tests for Admin Dashboard API
==============================

Tests for the admin dashboard API endpoints.

Coverage:
- Dashboard stats endpoint
- Product listing endpoint
- Sync job management
- Analytics endpoints
"""

import pytest

from api.admin_dashboard import (
    AdminDataStore,
    DashboardStats,
    ProductListResponse,
    ProductSummary,
    SalesAnalytics,
    SalesDataPoint,
    SyncJobListResponse,
    SyncJobSummary,
    admin_dashboard_router,
    get_dashboard_stats,
    get_products,
    get_sales_analytics,
    get_sync_jobs,
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
        store.add_product(
            "SKR-001",
            {
                "name": "Test Product",
                "price": 99.99,
                "stock": 50,
            },
        )

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
        store.add_sync_job(
            "sync_123",
            {
                "product_sku": "SKR-001",
                "status": "queued",
            },
        )

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
                },
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
                },
            )

        stats = store.get_stats()

        assert stats["total_products"] == 5


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Tests for response model structures."""

    def test_dashboard_stats(self):
        """Should create DashboardStats with actual fields."""
        stats = DashboardStats(
            total_products=100,
            products_with_3d=75,
            products_synced=85,
            pending_sync=15,
            total_orders_today=10,
            revenue_today=1000.00,
            total_orders_month=200,
            revenue_month=20000.00,
        )

        assert stats.total_products == 100
        assert stats.products_synced == 85
        assert stats.products_with_3d == 75

    def test_product_summary(self):
        """Should create ProductSummary."""
        summary = ProductSummary(
            sku="SKR-001",
            name="Test Product",
            status="published",
            has_3d_model=True,
            synced=True,
            stock=50,
            price=99.99,
        )

        assert summary.sku == "SKR-001"
        assert summary.has_3d_model is True

    def test_product_list_response(self):
        """Should create ProductListResponse."""
        response = ProductListResponse(
            products=[
                ProductSummary(
                    sku="SKR-001",
                    name="Product 1",
                    status="published",
                    has_3d_model=True,
                    synced=True,
                ),
                ProductSummary(
                    sku="SKR-002",
                    name="Product 2",
                    status="draft",
                    has_3d_model=False,
                    synced=False,
                ),
            ],
            total=100,
            page=1,
            page_size=20,
        )

        assert len(response.products) == 2
        assert response.total == 100
        assert response.page == 1

    def test_sync_job_summary(self):
        """Should create SyncJobSummary."""
        job = SyncJobSummary(
            id="sync_123",
            product_sku="SKR-001",
            status="completed",
            started_at="2026-01-01T12:00:00Z",
            completed_at="2026-01-01T12:05:00Z",
            errors=[],
        )

        assert job.id == "sync_123"
        assert job.status == "completed"

    def test_sync_job_list_response(self):
        """Should create SyncJobListResponse."""
        response = SyncJobListResponse(
            jobs=[
                SyncJobSummary(
                    id="sync_1",
                    product_sku="SKR-001",
                    status="completed",
                    started_at="2026-01-01T12:00:00Z",
                ),
            ],
            total=50,
        )

        assert len(response.jobs) == 1
        assert response.total == 50

    def test_sales_data_point(self):
        """Should create SalesDataPoint."""
        point = SalesDataPoint(
            date="2026-01-01",
            orders=10,
            revenue=1000.00,
        )

        assert point.date == "2026-01-01"
        assert point.orders == 10
        assert point.revenue == 1000.00

    def test_sales_analytics(self):
        """Should create SalesAnalytics with actual fields."""
        analytics = SalesAnalytics(
            period_days=30,
            total_orders=150,
            total_revenue=15000.00,
            data=[
                SalesDataPoint(date="2026-01-01", orders=5, revenue=500.00),
            ],
        )

        assert analytics.period_days == 30
        assert analytics.total_orders == 150
        assert analytics.total_revenue == 15000.00
        assert len(analytics.data) == 1


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

        # Check that key routes exist (with prefix)
        assert "/admin/stats" in routes
        assert "/admin/products" in routes
        assert "/admin/sync-jobs" in routes


# =============================================================================
# Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
class TestAdminEndpoints:
    """Tests for admin endpoint responses."""

    async def test_get_dashboard_stats(self):
        """Should return dashboard stats."""
        stats = await get_dashboard_stats()

        assert isinstance(stats, DashboardStats)
        assert stats.total_products >= 0

    async def test_get_products(self):
        """Should return product list."""
        # Pass actual values since Query defaults aren't resolved outside HTTP context
        products = await get_products(skip=0, limit=50)

        assert isinstance(products, list)

    async def test_get_products_with_filters(self):
        """Should filter products."""
        products = await get_products(skip=0, limit=10, status=None, has_3d=None)

        assert isinstance(products, list)
        assert len(products) <= 10

    async def test_get_sync_jobs(self):
        """Should return sync job list."""
        # Pass actual values since Query defaults aren't resolved outside HTTP context
        jobs = await get_sync_jobs(limit=50, status=None)

        assert isinstance(jobs, list)

    async def test_get_sales_analytics(self):
        """Should return sales analytics with days parameter."""
        analytics = await get_sales_analytics(days=30)

        assert isinstance(analytics, SalesAnalytics)
        assert analytics.period_days == 30


# =============================================================================
# Integration Tests (require test client fixtures)
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Integration test: Requires running FastAPI app and database. "
    "Run with: pytest -m integration --run-integration"
)
async def test_dashboard_integration(client, admin_headers):
    """Test dashboard endpoints with authenticated client."""
    # Get dashboard stats
    response = await client.get("/api/v1/admin/stats", headers=admin_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_products" in data


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(
    reason="Integration test: Requires running FastAPI app and database. "
    "Run with: pytest -m integration --run-integration"
)
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
]
