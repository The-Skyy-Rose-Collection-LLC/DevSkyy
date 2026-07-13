# tests/api/test_competitors_api.py
"""Tests for competitors API endpoints.

Implements US-034: Competitor image upload and tagging.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from services.competitive.competitor_analysis import CompetitorAnalysisService
from services.competitive.schemas import (
    CompetitorAsset,
    CompositionType,
    ExtractedAttributes,
    StyleCategory,
)

from api.v1.competitors import router
from database.db import DatabaseConfig, DatabaseManager, db_manager

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_user_strategy() -> MagicMock:
    """Create mock user with strategy role."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_strategy",
        jti="test_jti_strategy",
        type=TokenType.ACCESS,
        roles=["user", "strategy"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def mock_user_marketing() -> MagicMock:
    """Create mock user with marketing role."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_marketing",
        jti="test_jti_marketing",
        type=TokenType.ACCESS,
        roles=["user", "marketing"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def mock_user_regular() -> MagicMock:
    """Create mock user without special roles."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_regular",
        jti="test_jti_regular",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


async def _reset_db() -> DatabaseManager:
    """Reset the db_manager singleton onto a fresh in-memory DB.

    Mirrors tests/test_auth_endpoints.py — the same singleton backs the
    FastAPI get_db dependency, so it must be reset per test.
    """
    if db_manager._engine:
        await db_manager.close()
        db_manager._instance = None

    mgr = DatabaseManager()
    await mgr.initialize(DatabaseConfig(url="sqlite+aiosqlite:///:memory:"))
    return mgr


@pytest.fixture
async def app_with_strategy(mock_user_strategy: MagicMock):
    """Create test app with strategy user, backed by a fresh in-memory DB."""
    from security.jwt_oauth2_auth import get_current_user

    mgr = await _reset_db()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user_strategy
    yield app

    await mgr.close()
    mgr._instance = None


@pytest.fixture
async def app_with_regular(mock_user_regular: MagicMock):
    """Create test app with regular user, backed by a fresh in-memory DB."""
    from security.jwt_oauth2_auth import get_current_user

    mgr = await _reset_db()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user_regular
    yield app

    await mgr.close()
    mgr._instance = None


@pytest.fixture
async def client(app_with_strategy: FastAPI):
    """Create test client with strategy role."""
    transport = ASGITransport(app=app_with_strategy)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def client_regular(app_with_regular: FastAPI):
    """Create test client with regular user."""
    transport = ASGITransport(app=app_with_regular)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def _save_competitor_asset(asset: CompetitorAsset) -> None:
    """Persist a CompetitorAsset directly, bypassing the API (test setup only)."""
    async with db_manager.session() as session:
        session.add(CompetitorAnalysisService._asset_to_row(asset))


# =============================================================================
# RBAC Tests
# =============================================================================


class TestRBAC:
    """Tests for role-based access control."""

    @pytest.mark.asyncio
    async def test_strategy_role_allowed(self, client: AsyncClient) -> None:
        """Should allow strategy role access."""
        response = await client.get("/competitors")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_regular_user_denied(self, client_regular: AsyncClient) -> None:
        """Should deny regular users."""
        response = await client_regular.get("/competitors")
        assert response.status_code == 403
        assert "strategy/marketing" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_marketing_role_allowed(
        self, app_with_strategy: FastAPI, mock_user_marketing: MagicMock
    ) -> None:
        """Should allow marketing role access."""
        from security.jwt_oauth2_auth import get_current_user

        app_with_strategy.dependency_overrides[get_current_user] = lambda: mock_user_marketing
        transport = ASGITransport(app=app_with_strategy)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/competitors")
            assert response.status_code == 200


# =============================================================================
# Competitor CRUD Tests
# =============================================================================


class TestCompetitorCRUD:
    """Tests for competitor CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_competitor(self, client: AsyncClient) -> None:
        """Should create a competitor."""
        response = await client.post(
            "/competitors",
            json={
                "name": "Test Competitor",
                "category": "direct",
                "price_positioning": "premium",
                "notes": "Main competitor",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Competitor"
        assert data["category"] == "direct"
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_competitor_with_website(self, client: AsyncClient) -> None:
        """Should accept website URL."""
        response = await client.post(
            "/competitors",
            json={
                "name": "Brand X",
                "category": "aspirational",
                "price_positioning": "luxury",
                "website": "https://brandx.com",
            },
        )

        assert response.status_code == 200
        assert response.json()["website"] == "https://brandx.com/"

    @pytest.mark.asyncio
    async def test_list_competitors_empty(self, client: AsyncClient) -> None:
        """Should return empty list when no competitors."""
        response = await client.get("/competitors")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["competitors"] == []

    @pytest.mark.asyncio
    async def test_list_competitors_with_data(self, client: AsyncClient) -> None:
        """Should list all competitors."""
        await client.post("/competitors", json={"name": "Comp 1", "category": "direct"})
        await client.post("/competitors", json={"name": "Comp 2", "category": "indirect"})

        response = await client.get("/competitors")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_get_competitor_by_id(self, client: AsyncClient) -> None:
        """Should get competitor by ID."""
        create_resp = await client.post(
            "/competitors",
            json={"name": "Test Comp", "category": "direct"},
        )
        comp_id = create_resp.json()["id"]

        response = await client.get(f"/competitors/{comp_id}")

        assert response.status_code == 200
        assert response.json()["id"] == comp_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_competitor(self, client: AsyncClient) -> None:
        """Should return 404 for non-existent competitor."""
        response = await client.get("/competitors/nonexistent")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_competitor(self, client: AsyncClient) -> None:
        """Should delete competitor."""
        create_resp = await client.post(
            "/competitors",
            json={"name": "To Delete", "category": "emerging"},
        )
        comp_id = create_resp.json()["id"]

        response = await client.delete(f"/competitors/{comp_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_resp = await client.get(f"/competitors/{comp_id}")
        assert get_resp.status_code == 404


# =============================================================================
# Competitor Asset Tests
# =============================================================================


class TestCompetitorAssets:
    """Tests for competitor asset operations."""

    async def _create_competitor(self, client: AsyncClient) -> str:
        """Helper to create a competitor."""
        resp = await client.post(
            "/competitors",
            json={"name": "Test Competitor", "category": "direct"},
        )
        return resp.json()["id"]

    @pytest.mark.asyncio
    async def test_upload_asset(self, client: AsyncClient) -> None:
        """Should upload competitor asset."""
        comp_id = await self._create_competitor(client)

        response = await client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/product.jpg",
                "product_type": "dress",
                "estimated_price": 299.99,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["competitor_id"] == comp_id
        assert data["url"] == "https://example.com/product.jpg"
        assert data["estimated_price"] == 299.99

    @pytest.mark.asyncio
    async def test_upload_asset_nonexistent_competitor(self, client: AsyncClient) -> None:
        """Should reject asset for non-existent competitor."""
        response = await client.post(
            "/competitors/assets",
            json={
                "competitor_id": "nonexistent",
                "url": "https://example.com/img.jpg",
            },
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_asset_with_tags(self, client: AsyncClient) -> None:
        """Should accept manual tags."""
        comp_id = await self._create_competitor(client)

        response = await client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/product.jpg",
                "manual_tags": ["minimalist", "black", "summer"],
            },
        )

        assert response.status_code == 200
        assert "minimalist" in response.json()["manual_tags"]

    @pytest.mark.asyncio
    async def test_list_assets_empty(self, client: AsyncClient) -> None:
        """Should return empty list when no assets."""
        response = await client.get("/competitors/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_assets_with_data(self, client: AsyncClient) -> None:
        """Should list all assets."""
        comp_id = await self._create_competitor(client)

        # Upload assets
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img1.jpg"},
        )
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img2.jpg"},
        )

        response = await client.get("/competitors/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_assets_filter_by_competitor(self, client: AsyncClient) -> None:
        """Should filter by competitor ID."""
        comp1_id = await self._create_competitor(client)
        comp2_resp = await client.post(
            "/competitors",
            json={"name": "Competitor 2", "category": "indirect"},
        )
        comp2_id = comp2_resp.json()["id"]

        # Upload to both
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp1_id, "url": "https://example.com/c1.jpg"},
        )
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp2_id, "url": "https://example.com/c2.jpg"},
        )

        response = await client.get(f"/competitors/assets?competitor_id={comp1_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["competitor_id"] == comp1_id

    @pytest.mark.asyncio
    async def test_get_asset_by_id(self, client: AsyncClient) -> None:
        """Should get asset by ID."""
        comp_id = await self._create_competitor(client)
        upload_resp = await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = await client.get(f"/competitors/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    @pytest.mark.asyncio
    async def test_update_asset(self, client: AsyncClient) -> None:
        """Should update asset metadata."""
        comp_id = await self._create_competitor(client)
        upload_resp = await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = await client.patch(
            f"/competitors/assets/{asset_id}",
            json={
                "product_name": "Summer Dress",
                "estimated_price": 199.99,
                "manual_tags": ["summer", "dress"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_name"] == "Summer Dress"
        assert data["estimated_price"] == 199.99
        assert "summer" in data["manual_tags"]

    @pytest.mark.asyncio
    async def test_delete_asset(self, client: AsyncClient) -> None:
        """Should delete asset."""
        comp_id = await self._create_competitor(client)
        upload_resp = await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = await client.delete(f"/competitors/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_competitor_cascades_assets(self, client: AsyncClient) -> None:
        """Should delete associated assets when competitor deleted."""
        comp_id = await self._create_competitor(client)

        # Upload assets
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img1.jpg"},
        )
        await client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img2.jpg"},
        )

        # Delete competitor
        await client.delete(f"/competitors/{comp_id}")

        # Verify assets deleted
        response = await client.get("/competitors/assets")
        assert response.json()["total"] == 0


# =============================================================================
# Analytics Tests
# =============================================================================


class TestAnalytics:
    """Tests for analytics endpoints."""

    @pytest.mark.asyncio
    async def test_style_analytics_empty(self, client: AsyncClient) -> None:
        """Should return empty analytics when no data."""
        response = await client.get("/competitors/analytics/style-distribution")

        assert response.status_code == 200
        data = response.json()
        assert data["total_assets"] == 0

    @pytest.mark.asyncio
    async def test_style_analytics_with_data(self, client: AsyncClient) -> None:
        """Should return style distribution."""
        # Create competitor with assets
        comp_resp = await client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Add assets with extracted attributes (persisted directly for testing)
        asset = CompetitorAsset(
            competitor_id=comp_id,
            url="https://example.com/img.jpg",
            extracted_attributes=ExtractedAttributes(
                composition_type=CompositionType.FLAT_LAY,
                style_category=StyleCategory.MINIMALIST,
                primary_colors=["black", "white"],
                detected_materials=["cotton", "silk"],
            ),
        )
        await _save_competitor_asset(asset)

        response = await client.get("/competitors/analytics/style-distribution")

        assert response.status_code == 200
        data = response.json()
        assert data["total_assets"] == 1
        assert len(data["style_distribution"]) > 0

    @pytest.mark.asyncio
    async def test_summary_analytics(self, client: AsyncClient) -> None:
        """Should return summary analytics."""
        # Create competitors
        await client.post(
            "/competitors",
            json={"name": "Comp 1", "category": "direct", "price_positioning": "premium"},
        )
        await client.post(
            "/competitors",
            json={"name": "Comp 2", "category": "indirect", "price_positioning": "luxury"},
        )

        response = await client.get("/competitors/analytics/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_competitors"] == 2
        assert "direct" in data["competitors_by_category"]
        assert "indirect" in data["competitors_by_category"]


# =============================================================================
# Filter Tests
# =============================================================================


class TestFiltering:
    """Tests for asset filtering."""

    @pytest.mark.asyncio
    async def test_filter_by_tags(self, client: AsyncClient) -> None:
        """Should filter by tags."""
        comp_resp = await client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Create assets with different tags
        await client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/summer.jpg",
                "manual_tags": ["summer", "bright"],
            },
        )
        await client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/winter.jpg",
                "manual_tags": ["winter", "dark"],
            },
        )

        response = await client.get("/competitors/assets?tags=summer")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "summer" in data["assets"][0]["manual_tags"]

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient) -> None:
        """Should paginate results."""
        comp_resp = await client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Create 5 assets
        for i in range(5):
            await client.post(
                "/competitors/assets",
                json={
                    "competitor_id": comp_id,
                    "url": f"https://example.com/img{i}.jpg",
                },
            )

        # Get page 1
        resp1 = await client.get("/competitors/assets?page=1&page_size=2")
        assert resp1.json()["total"] == 5
        assert len(resp1.json()["assets"]) == 2

        # Get page 2
        resp2 = await client.get("/competitors/assets?page=2&page_size=2")
        assert len(resp2.json()["assets"]) == 2

        # Get page 3
        resp3 = await client.get("/competitors/assets?page=3&page_size=2")
        assert len(resp3.json()["assets"]) == 1


# =============================================================================
# Persistence Tests
# =============================================================================


class TestPersistence:
    """Tests that data survives a fresh DB session (the point of this store)."""

    @pytest.mark.asyncio
    async def test_competitor_survives_new_session(self, client: AsyncClient) -> None:
        """A competitor written via the API must be readable from a new session."""
        create_resp = await client.post(
            "/competitors",
            json={"name": "Durable Co", "category": "direct"},
        )
        comp_id = create_resp.json()["id"]

        async with db_manager.session() as read_session:
            from database.models_competitors import CompetitorRecord

            row = await read_session.get(CompetitorRecord, comp_id)
            assert row is not None
            assert row.name == "Durable Co"
