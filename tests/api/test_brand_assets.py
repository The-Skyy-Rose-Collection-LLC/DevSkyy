# tests/api/test_brand_assets.py
"""Tests for brand assets API endpoints.

Implements US-013: Brand asset ingestion for training.

Author: DevSkyy Platform Team
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.brand_assets import (
    router,
    BrandAssetCategory,
    AssetApprovalStatus,
    IngestionJobStatus,
    TrainingReadinessStatus,
    _brand_assets,
    _ingestion_jobs,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user() -> MagicMock:
    """Create mock authenticated user."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="test_jti_123",
        type=TokenType.ACCESS,
        roles=["user", "admin"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def app(mock_user: MagicMock) -> FastAPI:
    """Create test FastAPI app."""
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    """Clear in-memory storage before each test."""
    _brand_assets.clear()
    _ingestion_jobs.clear()


# =============================================================================
# Bulk Ingestion Tests
# =============================================================================


class TestBulkIngestion:
    """Tests for bulk ingestion endpoints."""

    def test_bulk_ingest_single_asset(self, client: TestClient) -> None:
        """Should start bulk ingestion with single asset."""
        response = client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [
                    {
                        "url": "https://example.com/product1.jpg",
                        "category": "product",
                        "metadata": {"campaign": "Spring 2024"},
                    }
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["total"] == 1
        assert data["id"] is not None

    def test_bulk_ingest_multiple_assets(self, client: TestClient) -> None:
        """Should handle multiple assets."""
        response = client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [
                    {"url": "https://example.com/img1.jpg", "category": "product"},
                    {"url": "https://example.com/img2.jpg", "category": "lifestyle"},
                    {"url": "https://example.com/img3.jpg", "category": "campaign"},
                ],
                "campaign_name": "Black Rose Collection",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3

    def test_bulk_ingest_max_100_assets(self, client: TestClient) -> None:
        """Should accept up to 100 assets."""
        assets = [
            {"url": f"https://example.com/img{i}.jpg", "category": "product"}
            for i in range(100)
        ]

        response = client.post(
            "/brand-assets/ingest/bulk",
            json={"assets": assets},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 100

    def test_bulk_ingest_over_limit(self, client: TestClient) -> None:
        """Should reject over 100 assets."""
        assets = [
            {"url": f"https://example.com/img{i}.jpg", "category": "product"}
            for i in range(101)
        ]

        response = client.post(
            "/brand-assets/ingest/bulk",
            json={"assets": assets},
        )

        assert response.status_code == 422  # Validation error

    def test_bulk_ingest_with_auto_approve(self, client: TestClient) -> None:
        """Should auto-approve assets when requested."""
        response = client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [
                    {"url": "https://example.com/img.jpg", "category": "product"}
                ],
                "auto_approve": True,
            },
        )

        assert response.status_code == 200

    def test_get_ingestion_job(self, client: TestClient) -> None:
        """Should retrieve ingestion job status."""
        # Create job
        create_response = client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [
                    {"url": "https://example.com/img.jpg", "category": "product"}
                ],
            },
        )
        job_id = create_response.json()["id"]

        # Get job
        response = client.get(f"/brand-assets/ingest/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id

    def test_get_nonexistent_job(self, client: TestClient) -> None:
        """Should return 404 for non-existent job."""
        response = client.get("/brand-assets/ingest/nonexistent_id")
        assert response.status_code == 404


# =============================================================================
# Asset CRUD Tests
# =============================================================================


class TestAssetCrud:
    """Tests for asset CRUD operations."""

    def _create_test_asset(self, client: TestClient) -> str:
        """Helper to create a test asset."""
        from api.v1.brand_assets import BrandAsset, BrandAssetCategory

        asset = BrandAsset(
            url="https://example.com/test.jpg",
            category=BrandAssetCategory.PRODUCT,
        )
        _brand_assets[asset.id] = asset
        return asset.id

    def test_list_assets_empty(self, client: TestClient) -> None:
        """Should return empty list when no assets."""
        response = client.get("/brand-assets/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["assets"] == []

    def test_list_assets_with_data(self, client: TestClient) -> None:
        """Should list all assets."""
        self._create_test_asset(client)
        self._create_test_asset(client)

        response = client.get("/brand-assets/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_assets_filter_by_category(self, client: TestClient) -> None:
        """Should filter by category."""
        from api.v1.brand_assets import BrandAsset

        # Create product asset
        product = BrandAsset(
            url="https://example.com/product.jpg",
            category=BrandAssetCategory.PRODUCT,
        )
        _brand_assets[product.id] = product

        # Create lifestyle asset
        lifestyle = BrandAsset(
            url="https://example.com/lifestyle.jpg",
            category=BrandAssetCategory.LIFESTYLE,
        )
        _brand_assets[lifestyle.id] = lifestyle

        response = client.get("/brand-assets/assets?category=product")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["category"] == "product"

    def test_list_assets_filter_by_status(self, client: TestClient) -> None:
        """Should filter by approval status."""
        from api.v1.brand_assets import BrandAsset

        # Create pending asset
        pending = BrandAsset(
            url="https://example.com/pending.jpg",
            category=BrandAssetCategory.PRODUCT,
            approval_status=AssetApprovalStatus.PENDING,
        )
        _brand_assets[pending.id] = pending

        # Create approved asset
        approved = BrandAsset(
            url="https://example.com/approved.jpg",
            category=BrandAssetCategory.PRODUCT,
            approval_status=AssetApprovalStatus.APPROVED,
        )
        _brand_assets[approved.id] = approved

        response = client.get("/brand-assets/assets?approval_status=approved")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_get_asset_by_id(self, client: TestClient) -> None:
        """Should get asset by ID."""
        asset_id = self._create_test_asset(client)

        response = client.get(f"/brand-assets/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    def test_get_nonexistent_asset(self, client: TestClient) -> None:
        """Should return 404 for non-existent asset."""
        response = client.get("/brand-assets/assets/nonexistent")
        assert response.status_code == 404

    def test_approve_asset(self, client: TestClient) -> None:
        """Should approve an asset."""
        asset_id = self._create_test_asset(client)

        response = client.patch(f"/brand-assets/assets/{asset_id}/approve")

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"

    def test_reject_asset(self, client: TestClient) -> None:
        """Should reject an asset."""
        asset_id = self._create_test_asset(client)

        response = client.patch(
            f"/brand-assets/assets/{asset_id}/reject",
            params={"reason": "Low quality"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"

    def test_delete_asset(self, client: TestClient) -> None:
        """Should delete an asset."""
        asset_id = self._create_test_asset(client)

        response = client.delete(f"/brand-assets/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        assert asset_id not in _brand_assets


# =============================================================================
# Training Readiness Tests
# =============================================================================


class TestTrainingReadiness:
    """Tests for training readiness assessment."""

    def test_training_readiness_empty(self, client: TestClient) -> None:
        """Should report not ready when empty."""
        response = client.get("/brand-assets/training-readiness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["total_assets"] == 0
        assert data["approved_assets"] == 0

    def test_training_readiness_below_minimum(self, client: TestClient) -> None:
        """Should report not ready below minimum."""
        from api.v1.brand_assets import BrandAsset

        # Create 50 approved assets
        for i in range(50):
            asset = BrandAsset(
                url=f"https://example.com/img{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            _brand_assets[asset.id] = asset

        response = client.get("/brand-assets/training-readiness?minimum_assets=100")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["approved_assets"] == 50

    def test_training_readiness_needs_review(self, client: TestClient) -> None:
        """Should report needs review when pending assets could meet minimum."""
        from api.v1.brand_assets import BrandAsset

        # Create 50 approved and 60 pending
        for i in range(50):
            approved = BrandAsset(
                url=f"https://example.com/approved{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            _brand_assets[approved.id] = approved

        for i in range(60):
            pending = BrandAsset(
                url=f"https://example.com/pending{i}.jpg",
                category=BrandAssetCategory.LIFESTYLE,
                approval_status=AssetApprovalStatus.PENDING,
            )
            _brand_assets[pending.id] = pending

        response = client.get("/brand-assets/training-readiness?minimum_assets=100")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_review"
        # Check that review recommendation exists somewhere in recommendations
        recommendations_str = str(data["recommendations"]).lower()
        assert "review" in recommendations_str or "pending" in recommendations_str

    def test_training_readiness_ready(self, client: TestClient) -> None:
        """Should report ready when minimum met."""
        from api.v1.brand_assets import BrandAsset

        # Create 150 approved assets
        for i in range(150):
            asset = BrandAsset(
                url=f"https://example.com/img{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            _brand_assets[asset.id] = asset

        response = client.get("/brand-assets/training-readiness?minimum_assets=100")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["approved_assets"] == 150
        assert data["estimated_training_time"] is not None


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for brand assets statistics."""

    def test_stats_empty(self, client: TestClient) -> None:
        """Should return zero stats when empty."""
        response = client.get("/brand-assets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_stats_with_data(self, client: TestClient) -> None:
        """Should return accurate statistics."""
        from api.v1.brand_assets import BrandAsset, VisualFeatures, ColorPalette

        # Create assets with different categories and statuses
        for i, cat in enumerate([
            BrandAssetCategory.PRODUCT,
            BrandAssetCategory.LIFESTYLE,
            BrandAssetCategory.CAMPAIGN,
        ]):
            asset = BrandAsset(
                url=f"https://example.com/{cat.value}.jpg",
                category=cat,
                approval_status=AssetApprovalStatus.APPROVED if i % 2 == 0 else AssetApprovalStatus.PENDING,
                visual_features=VisualFeatures(
                    color_palette=ColorPalette(primary="#000"),
                    quality_score=0.8,
                ),
            )
            _brand_assets[asset.id] = asset

        response = client.get("/brand-assets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "by_category" in data
        assert "by_approval_status" in data
        assert data["average_quality_score"] > 0
