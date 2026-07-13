# tests/api/test_brand_assets.py
"""Tests for brand assets API endpoints.

Implements US-013: Brand asset ingestion for training.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.brand_assets import (
    AssetApprovalStatus,
    BrandAsset,
    BrandAssetCategory,
    ColorPalette,
    VisualFeatures,
    _asset_to_row,
    router,
)
from database.db import DatabaseConfig, DatabaseManager, db_manager

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
async def client(mock_user: MagicMock):
    """ASGI test client backed by a fresh in-memory DB, isolated per test.

    Mirrors tests/test_auth_endpoints.py's db_manager reset pattern: the
    module-level singleton backs both the FastAPI get_db dependency and
    process_bulk_ingestion's background-task session, so it must be reset
    and reinitialized per test rather than overridden via
    dependency_overrides alone.
    """
    from security.jwt_oauth2_auth import get_current_user

    if db_manager._engine:
        await db_manager.close()
        db_manager._instance = None

    mgr = DatabaseManager()
    await mgr.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    await mgr.close()
    mgr._instance = None


async def _save_asset(asset: BrandAsset) -> None:
    """Persist a BrandAsset directly, bypassing the API (test setup only)."""
    async with db_manager.session() as session:
        session.add(_asset_to_row(asset))


# =============================================================================
# Bulk Ingestion Tests
# =============================================================================


class TestBulkIngestion:
    """Tests for bulk ingestion endpoints."""

    @pytest.mark.asyncio
    async def test_bulk_ingest_single_asset(self, client: AsyncClient) -> None:
        """Should start bulk ingestion with single asset."""
        response = await client.post(
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
        assert data["status"] in ("pending", "completed", "partial", "failed")
        assert data["total"] == 1
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_bulk_ingest_multiple_assets(self, client: AsyncClient) -> None:
        """Should handle multiple assets."""
        response = await client.post(
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

    @pytest.mark.asyncio
    async def test_bulk_ingest_max_100_assets(self, client: AsyncClient) -> None:
        """Should accept up to 100 assets."""
        assets = [
            {"url": f"https://example.com/img{i}.jpg", "category": "product"} for i in range(100)
        ]

        response = await client.post(
            "/brand-assets/ingest/bulk",
            json={"assets": assets},
        )

        assert response.status_code == 200
        assert response.json()["total"] == 100

    @pytest.mark.asyncio
    async def test_bulk_ingest_over_limit(self, client: AsyncClient) -> None:
        """Should reject over 100 assets."""
        assets = [
            {"url": f"https://example.com/img{i}.jpg", "category": "product"} for i in range(101)
        ]

        response = await client.post(
            "/brand-assets/ingest/bulk",
            json={"assets": assets},
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_bulk_ingest_with_auto_approve(self, client: AsyncClient) -> None:
        """Should auto-approve assets when requested."""
        response = await client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [{"url": "https://example.com/img.jpg", "category": "product"}],
                "auto_approve": True,
            },
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_ingestion_job(self, client: AsyncClient) -> None:
        """Should retrieve ingestion job status."""
        # Create job
        create_response = await client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [{"url": "https://example.com/img.jpg", "category": "product"}],
            },
        )
        job_id = create_response.json()["id"]

        # Get job
        response = await client.get(f"/brand-assets/ingest/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == job_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, client: AsyncClient) -> None:
        """Should return 404 for non-existent job."""
        response = await client.get("/brand-assets/ingest/nonexistent_id")
        assert response.status_code == 404


# =============================================================================
# Asset CRUD Tests
# =============================================================================


class TestAssetCrud:
    """Tests for asset CRUD operations."""

    async def _create_test_asset(self, client: AsyncClient) -> str:
        """Helper to create a test asset."""
        asset = BrandAsset(
            url="https://example.com/test.jpg",
            category=BrandAssetCategory.PRODUCT,
        )
        await _save_asset(asset)
        return asset.id

    @pytest.mark.asyncio
    async def test_list_assets_empty(self, client: AsyncClient) -> None:
        """Should return empty list when no assets."""
        response = await client.get("/brand-assets/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["assets"] == []

    @pytest.mark.asyncio
    async def test_list_assets_with_data(self, client: AsyncClient) -> None:
        """Should list all assets."""
        await self._create_test_asset(client)
        await self._create_test_asset(client)

        response = await client.get("/brand-assets/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_assets_filter_by_category(self, client: AsyncClient) -> None:
        """Should filter by category."""
        product = BrandAsset(
            url="https://example.com/product.jpg",
            category=BrandAssetCategory.PRODUCT,
        )
        await _save_asset(product)

        lifestyle = BrandAsset(
            url="https://example.com/lifestyle.jpg",
            category=BrandAssetCategory.LIFESTYLE,
        )
        await _save_asset(lifestyle)

        response = await client.get("/brand-assets/assets?category=product")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["category"] == "product"

    @pytest.mark.asyncio
    async def test_list_assets_filter_by_status(self, client: AsyncClient) -> None:
        """Should filter by approval status."""
        pending = BrandAsset(
            url="https://example.com/pending.jpg",
            category=BrandAssetCategory.PRODUCT,
            approval_status=AssetApprovalStatus.PENDING,
        )
        await _save_asset(pending)

        approved = BrandAsset(
            url="https://example.com/approved.jpg",
            category=BrandAssetCategory.PRODUCT,
            approval_status=AssetApprovalStatus.APPROVED,
        )
        await _save_asset(approved)

        response = await client.get("/brand-assets/assets?approval_status=approved")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_get_asset_by_id(self, client: AsyncClient) -> None:
        """Should get asset by ID."""
        asset_id = await self._create_test_asset(client)

        response = await client.get(f"/brand-assets/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_asset(self, client: AsyncClient) -> None:
        """Should return 404 for non-existent asset."""
        response = await client.get("/brand-assets/assets/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_approve_asset(self, client: AsyncClient) -> None:
        """Should approve an asset."""
        asset_id = await self._create_test_asset(client)

        response = await client.patch(f"/brand-assets/assets/{asset_id}/approve")

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "approved"

    @pytest.mark.asyncio
    async def test_reject_asset(self, client: AsyncClient) -> None:
        """Should reject an asset."""
        asset_id = await self._create_test_asset(client)

        response = await client.patch(
            f"/brand-assets/assets/{asset_id}/reject",
            params={"reason": "Low quality"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["approval_status"] == "rejected"

    @pytest.mark.asyncio
    async def test_delete_asset(self, client: AsyncClient) -> None:
        """Should delete an asset."""
        asset_id = await self._create_test_asset(client)

        response = await client.delete(f"/brand-assets/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_response = await client.get(f"/brand-assets/assets/{asset_id}")
        assert get_response.status_code == 404


# =============================================================================
# Training Readiness Tests
# =============================================================================


class TestTrainingReadiness:
    """Tests for training readiness assessment."""

    @pytest.mark.asyncio
    async def test_training_readiness_empty(self, client: AsyncClient) -> None:
        """Should report not ready when empty."""
        response = await client.get("/brand-assets/training-readiness")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["total_assets"] == 0
        assert data["approved_assets"] == 0

    @pytest.mark.asyncio
    async def test_training_readiness_below_minimum(self, client: AsyncClient) -> None:
        """Should report not ready below minimum."""
        # Create 50 approved assets
        for i in range(50):
            asset = BrandAsset(
                url=f"https://example.com/img{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            await _save_asset(asset)

        response = await client.get("/brand-assets/training-readiness?minimum_assets=100")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["approved_assets"] == 50

    @pytest.mark.asyncio
    async def test_training_readiness_needs_review(self, client: AsyncClient) -> None:
        """Should report needs review when pending assets could meet minimum."""
        # Create 50 approved and 60 pending
        for i in range(50):
            approved = BrandAsset(
                url=f"https://example.com/approved{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            await _save_asset(approved)

        for i in range(60):
            pending = BrandAsset(
                url=f"https://example.com/pending{i}.jpg",
                category=BrandAssetCategory.LIFESTYLE,
                approval_status=AssetApprovalStatus.PENDING,
            )
            await _save_asset(pending)

        response = await client.get("/brand-assets/training-readiness?minimum_assets=100")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "needs_review"
        # Check that review recommendation exists somewhere in recommendations
        recommendations_str = str(data["recommendations"]).lower()
        assert "review" in recommendations_str or "pending" in recommendations_str

    @pytest.mark.asyncio
    async def test_training_readiness_ready(self, client: AsyncClient) -> None:
        """Should report ready when minimum met."""
        # Create 150 approved assets
        for i in range(150):
            asset = BrandAsset(
                url=f"https://example.com/img{i}.jpg",
                category=BrandAssetCategory.PRODUCT,
                approval_status=AssetApprovalStatus.APPROVED,
            )
            await _save_asset(asset)

        response = await client.get("/brand-assets/training-readiness?minimum_assets=100")

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

    @pytest.mark.asyncio
    async def test_stats_empty(self, client: AsyncClient) -> None:
        """Should return zero stats when empty."""
        response = await client.get("/brand-assets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_data(self, client: AsyncClient) -> None:
        """Should return accurate statistics."""
        # Create assets with different categories and statuses
        for i, cat in enumerate(
            [
                BrandAssetCategory.PRODUCT,
                BrandAssetCategory.LIFESTYLE,
                BrandAssetCategory.CAMPAIGN,
            ]
        ):
            asset = BrandAsset(
                url=f"https://example.com/{cat.value}.jpg",
                category=cat,
                approval_status=(
                    AssetApprovalStatus.APPROVED if i % 2 == 0 else AssetApprovalStatus.PENDING
                ),
                visual_features=VisualFeatures(
                    color_palette=ColorPalette(primary="#000"),
                    quality_score=0.8,
                ),
            )
            await _save_asset(asset)

        response = await client.get("/brand-assets/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert "by_category" in data
        assert "by_approval_status" in data
        assert data["average_quality_score"] > 0


# =============================================================================
# Persistence Tests
# =============================================================================


class TestPersistence:
    """Tests that data survives a fresh DB session (the point of this store)."""

    @pytest.mark.asyncio
    async def test_asset_survives_new_session(self, client: AsyncClient) -> None:
        """An asset written in one session must be readable from a new one."""
        asset = BrandAsset(
            url="https://example.com/durable.jpg",
            category=BrandAssetCategory.PRODUCT,
        )
        async with db_manager.session() as write_session:
            write_session.add(_asset_to_row(asset))

        async with db_manager.session() as read_session:
            from database.models_brand_assets import BrandAssetRecord

            row = await read_session.get(BrandAssetRecord, asset.id)
            assert row is not None
            assert row.url == asset.url

    @pytest.mark.asyncio
    async def test_ingestion_job_survives_new_session(self, client: AsyncClient) -> None:
        """A job written in one session must be readable from a new one."""
        response = await client.post(
            "/brand-assets/ingest/bulk",
            json={
                "assets": [{"url": "https://example.com/durable-job.jpg", "category": "product"}]
            },
        )
        job_id = response.json()["id"]

        async with db_manager.session() as read_session:
            from database.models_brand_assets import IngestionJobRecord

            row = await read_session.get(IngestionJobRecord, job_id)
            assert row is not None
            assert row.total == 1
