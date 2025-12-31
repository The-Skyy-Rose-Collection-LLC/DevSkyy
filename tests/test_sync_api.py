"""
Tests for Sync API Endpoints
=============================

Tests for the catalog synchronization API endpoints.

Coverage:
- Product sync endpoint
- Bulk sync endpoint
- Sync status endpoint
- Job listing and retrieval
- Error handling
"""

from unittest.mock import AsyncMock, patch

import pytest

from api.sync_endpoints import (
    BulkSyncRequest,
    BulkSyncResponse,
    ProductSyncRequest,
    SyncJobResponse,
    SyncJobStore,
    SyncStatusResponse,
    sync_router,
)

# =============================================================================
# Request Model Tests
# =============================================================================


class TestRequestModels:
    """Tests for request model validation."""

    def test_product_sync_request_minimal(self):
        """Should create request with minimal fields."""
        request = ProductSyncRequest(
            sku="SKR-001",
            name="Test Product",
            price=99.99,
        )

        assert request.sku == "SKR-001"
        assert request.name == "Test Product"
        assert request.price == 99.99
        assert request.description == ""
        assert request.stock == 0

    def test_product_sync_request_full(self):
        """Should create request with all fields."""
        request = ProductSyncRequest(
            sku="SKR-001",
            name="SkyyRose Signature Hoodie",
            price=149.99,
            description="Premium luxury streetwear hoodie",
            short_description="Signature hoodie",
            stock=50,
            categories=[1, 2, 3],
            tags=["hoodie", "streetwear"],
            image_paths=["/path/to/image1.jpg", "/path/to/image2.jpg"],
        )

        assert request.stock == 50
        assert len(request.categories) == 3
        assert len(request.tags) == 2
        assert len(request.image_paths) == 2

    def test_bulk_sync_request(self):
        """Should create bulk sync request."""
        request = BulkSyncRequest(
            products=[
                ProductSyncRequest(sku="SKR-001", name="Product 1", price=99.99),
                ProductSyncRequest(sku="SKR-002", name="Product 2", price=149.99),
            ],
            config={"priority": "high"},
        )

        assert len(request.products) == 2
        assert request.config["priority"] == "high"

    def test_product_sync_request_validation(self):
        """Should validate field constraints."""
        # SKU must be non-empty
        with pytest.raises(ValueError):
            ProductSyncRequest(sku="", name="Test", price=99.99)

        # Price must be non-negative
        with pytest.raises(ValueError):
            ProductSyncRequest(sku="SKR-001", name="Test", price=-10)


# =============================================================================
# Response Model Tests
# =============================================================================


class TestResponseModels:
    """Tests for response model structures."""

    def test_sync_job_response(self):
        """Should create SyncJobResponse."""
        response = SyncJobResponse(
            job_id="sync_abc123",
            product_sku="SKR-001",
            status="completed",
            started_at="2025-01-01T12:00:00Z",
            completed_at="2025-01-01T12:01:00Z",
            success=True,
            wordpress_id=12345,
            images_uploaded=5,
            model_uploaded=True,
            photoshoot_generated=True,
            errors=[],
            warnings=[],
        )

        assert response.job_id == "sync_abc123"
        assert response.success is True
        assert response.wordpress_id == 12345

    def test_sync_status_response(self):
        """Should create SyncStatusResponse."""
        response = SyncStatusResponse(
            product_sku="SKR-001",
            synced_to_wordpress=True,
            wordpress_id=12345,
            has_3d_model=True,
            has_processed_images=True,
            last_sync="2025-01-01T12:00:00Z",
        )

        assert response.synced_to_wordpress is True
        assert response.has_3d_model is True

    def test_bulk_sync_response(self):
        """Should create BulkSyncResponse."""
        response = BulkSyncResponse(
            total=10,
            successful=8,
            failed=2,
            job_ids=["sync_1", "sync_2"],
            results=[],
        )

        assert response.total == 10
        assert response.successful == 8
        assert response.failed == 2


# =============================================================================
# SyncJobStore Tests
# =============================================================================


class TestSyncJobStore:
    """Tests for SyncJobStore."""

    @pytest.fixture
    def store(self):
        """Create fresh job store."""
        return SyncJobStore()

    def test_create_job(self, store):
        """Should create new job."""
        job_id = store.create("SKR-001")

        assert job_id.startswith("sync_")

        job = store.get(job_id)
        assert job is not None
        assert job["product_sku"] == "SKR-001"
        assert job["status"] == "queued"

    def test_get_job(self, store):
        """Should retrieve job by ID."""
        job_id = store.create("SKR-001")

        job = store.get(job_id)

        assert job is not None
        assert job["job_id"] == job_id

    def test_get_nonexistent_job(self, store):
        """Should return None for nonexistent job."""
        result = store.get("nonexistent_id")

        assert result is None

    def test_update_job(self, store):
        """Should update job fields."""
        job_id = store.create("SKR-001")

        store.update(job_id, status="processing", images_uploaded=3)

        job = store.get(job_id)
        assert job["status"] == "processing"
        assert job["images_uploaded"] == 3

    def test_complete_job(self, store):
        """Should mark job as completed."""
        job_id = store.create("SKR-001")

        store.complete(
            job_id,
            {
                "success": True,
                "wordpress_id": 12345,
                "images_uploaded": 5,
                "model_uploaded": True,
            },
        )

        job = store.get(job_id)
        assert job["status"] == "completed"
        assert job["success"] is True
        assert job["wordpress_id"] == 12345
        assert job["completed_at"] is not None

    def test_fail_job(self, store):
        """Should mark job as failed."""
        job_id = store.create("SKR-001")

        store.fail(job_id, "API connection failed")

        job = store.get(job_id)
        assert job["status"] == "failed"
        assert "API connection failed" in job["errors"]

    def test_list_jobs(self, store):
        """Should list recent jobs."""
        for i in range(5):
            store.create(f"SKR-00{i}")

        jobs = store.list_jobs(limit=3)

        assert len(jobs) == 3

    def test_list_jobs_ordered(self, store):
        """Should list jobs in reverse chronological order."""
        import time

        ids = []
        for i in range(3):
            ids.append(store.create(f"SKR-00{i}"))
            time.sleep(0.01)  # Small delay to ensure different timestamps

        jobs = store.list_jobs()

        # Most recent first
        assert jobs[0]["product_sku"] == "SKR-002"


# =============================================================================
# Router Tests
# =============================================================================


class TestSyncRouter:
    """Tests for sync router endpoints."""

    def test_router_has_prefix(self):
        """Should have correct prefix."""
        assert sync_router.prefix == "/sync"

    def test_router_has_tags(self):
        """Should have tags."""
        assert "Catalog Sync" in sync_router.tags

    def test_router_has_endpoints(self):
        """Should have expected endpoints."""
        routes = [r.path for r in sync_router.routes]
        prefix = sync_router.prefix

        assert f"{prefix}/product" in routes
        assert f"{prefix}/bulk" in routes
        assert f"{prefix}/status/{{product_sku}}" in routes
        assert f"{prefix}/jobs" in routes
        assert f"{prefix}/jobs/{{job_id}}" in routes


# =============================================================================
# Endpoint Tests
# =============================================================================


@pytest.mark.asyncio
class TestSyncEndpoints:
    """Tests for sync endpoint responses."""

    async def test_sync_single_product(self):
        """Should sync single product."""
        from api.sync_endpoints import sync_single_product

        request = ProductSyncRequest(
            sku="SKR-001",
            name="Test Product",
            price=99.99,
        )

        # Mock background tasks
        with patch(
            "api.sync_endpoints.run_product_sync", new_callable=AsyncMock
        ):
            response = await sync_single_product(request, background_tasks=None)

            assert isinstance(response, SyncJobResponse)
            assert response.product_sku == "SKR-001"
            assert response.status in ["queued", "processing", "completed"]

    async def test_sync_bulk_products(self):
        """Should sync multiple products."""
        from api.sync_endpoints import sync_bulk_products

        request = BulkSyncRequest(
            products=[
                ProductSyncRequest(sku="SKR-001", name="Product 1", price=99.99),
                ProductSyncRequest(sku="SKR-002", name="Product 2", price=149.99),
            ]
        )

        with patch(
            "api.sync_endpoints.run_product_sync", new_callable=AsyncMock
        ):
            response = await sync_bulk_products(request, background_tasks=None)

            assert isinstance(response, BulkSyncResponse)
            assert response.total == 2
            assert len(response.job_ids) == 2

    async def test_get_sync_status(self):
        """Should get product sync status."""
        from api.sync_endpoints import get_sync_status

        response = await get_sync_status("SKR-001")

        assert isinstance(response, SyncStatusResponse)
        assert response.product_sku == "SKR-001"

    async def test_list_sync_jobs(self):
        """Should list sync jobs."""
        from api.sync_endpoints import list_sync_jobs

        response = await list_sync_jobs(limit=20)

        assert isinstance(response, list)
        for job in response:
            assert isinstance(job, SyncJobResponse)

    async def test_list_sync_jobs_filtered(self):
        """Should filter sync jobs by status."""
        from api.sync_endpoints import list_sync_jobs

        response = await list_sync_jobs(limit=20, status="completed")

        assert isinstance(response, list)
        for job in response:
            assert job.status == "completed"

    async def test_get_sync_job(self):
        """Should get specific sync job."""
        from api.sync_endpoints import get_sync_job, sync_job_store

        # Create a job first
        job_id = sync_job_store.create("SKR-TEST")

        response = await get_sync_job(job_id)

        assert isinstance(response, SyncJobResponse)
        assert response.job_id == job_id

    async def test_get_sync_job_not_found(self):
        """Should raise 404 for nonexistent job."""
        from fastapi import HTTPException

        from api.sync_endpoints import get_sync_job

        with pytest.raises(HTTPException) as exc_info:
            await get_sync_job("nonexistent_job_id")

        assert exc_info.value.status_code == 404


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_integration(client, auth_headers):
    """Test sync endpoints with authenticated client."""
    # Create a sync job
    response = await client.post(
        "/api/v1/sync/product",
        json={
            "sku": "SKR-TEST",
            "name": "Test Product",
            "price": 99.99,
        },
        headers=auth_headers,
    )

    assert response.status_code in [200, 201, 202]
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # Get job status
    response = await client.get(
        f"/api/v1/sync/jobs/{job_id}",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id

    # Get product sync status
    response = await client.get(
        "/api/v1/sync/status/SKR-TEST",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["product_sku"] == "SKR-TEST"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_integration(client, auth_headers):
    """Test bulk sync endpoint."""
    response = await client.post(
        "/api/v1/sync/bulk",
        json={
            "products": [
                {"sku": "SKR-001", "name": "Product 1", "price": 99.99},
                {"sku": "SKR-002", "name": "Product 2", "price": 149.99},
            ],
        },
        headers=auth_headers,
    )

    assert response.status_code in [200, 201, 202]
    data = response.json()
    assert data["total"] == 2
    assert len(data["job_ids"]) == 2


__all__ = [
    "TestRequestModels",
    "TestResponseModels",
    "TestSyncJobStore",
    "TestSyncRouter",
    "TestSyncEndpoints",
]
