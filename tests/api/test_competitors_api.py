# tests/api/test_competitors_api.py
"""Tests for competitors API endpoints.

Implements US-034: Competitor image upload and tagging.

Author: DevSkyy Platform Team
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.competitors import router
from services.competitive.competitor_analysis import (
    _competitor_assets,
    _competitors,
)
from services.competitive.schemas import (
    CompositionType,
    Competitor,
    CompetitorAsset,
    CompetitorCategory,
    ExtractedAttributes,
    PricePositioning,
    StyleCategory,
)


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


@pytest.fixture
def app_with_strategy(mock_user_strategy: MagicMock) -> FastAPI:
    """Create test app with strategy user."""
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user_strategy
    return app


@pytest.fixture
def app_with_regular(mock_user_regular: MagicMock) -> FastAPI:
    """Create test app with regular user."""
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_current_user] = lambda: mock_user_regular
    return app


@pytest.fixture
def client(app_with_strategy: FastAPI) -> TestClient:
    """Create test client with strategy role."""
    return TestClient(app_with_strategy)


@pytest.fixture
def client_regular(app_with_regular: FastAPI) -> TestClient:
    """Create test client with regular user."""
    return TestClient(app_with_regular)


@pytest.fixture(autouse=True)
def clear_storage() -> None:
    """Clear in-memory storage before each test."""
    _competitors.clear()
    _competitor_assets.clear()


# =============================================================================
# RBAC Tests
# =============================================================================


class TestRBAC:
    """Tests for role-based access control."""

    def test_strategy_role_allowed(self, client: TestClient) -> None:
        """Should allow strategy role access."""
        response = client.get("/competitors")
        assert response.status_code == 200

    def test_regular_user_denied(self, client_regular: TestClient) -> None:
        """Should deny regular users."""
        response = client_regular.get("/competitors")
        assert response.status_code == 403
        assert "strategy/marketing" in response.json()["detail"]

    def test_marketing_role_allowed(
        self, app_with_strategy: FastAPI, mock_user_marketing: MagicMock
    ) -> None:
        """Should allow marketing role access."""
        from security.jwt_oauth2_auth import get_current_user

        app_with_strategy.dependency_overrides[get_current_user] = lambda: mock_user_marketing
        client = TestClient(app_with_strategy)

        response = client.get("/competitors")
        assert response.status_code == 200


# =============================================================================
# Competitor CRUD Tests
# =============================================================================


class TestCompetitorCRUD:
    """Tests for competitor CRUD operations."""

    def test_create_competitor(self, client: TestClient) -> None:
        """Should create a competitor."""
        response = client.post(
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

    def test_create_competitor_with_website(self, client: TestClient) -> None:
        """Should accept website URL."""
        response = client.post(
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

    def test_list_competitors_empty(self, client: TestClient) -> None:
        """Should return empty list when no competitors."""
        response = client.get("/competitors")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["competitors"] == []

    def test_list_competitors_with_data(self, client: TestClient) -> None:
        """Should list all competitors."""
        # Create competitors
        client.post("/competitors", json={"name": "Comp 1", "category": "direct"})
        client.post("/competitors", json={"name": "Comp 2", "category": "indirect"})

        response = client.get("/competitors")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_get_competitor_by_id(self, client: TestClient) -> None:
        """Should get competitor by ID."""
        create_resp = client.post(
            "/competitors",
            json={"name": "Test Comp", "category": "direct"},
        )
        comp_id = create_resp.json()["id"]

        response = client.get(f"/competitors/{comp_id}")

        assert response.status_code == 200
        assert response.json()["id"] == comp_id

    def test_get_nonexistent_competitor(self, client: TestClient) -> None:
        """Should return 404 for non-existent competitor."""
        response = client.get("/competitors/nonexistent")
        assert response.status_code == 404

    def test_delete_competitor(self, client: TestClient) -> None:
        """Should delete competitor."""
        create_resp = client.post(
            "/competitors",
            json={"name": "To Delete", "category": "emerging"},
        )
        comp_id = create_resp.json()["id"]

        response = client.delete(f"/competitors/{comp_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_resp = client.get(f"/competitors/{comp_id}")
        assert get_resp.status_code == 404


# =============================================================================
# Competitor Asset Tests
# =============================================================================


class TestCompetitorAssets:
    """Tests for competitor asset operations."""

    def _create_competitor(self, client: TestClient) -> str:
        """Helper to create a competitor."""
        resp = client.post(
            "/competitors",
            json={"name": "Test Competitor", "category": "direct"},
        )
        return resp.json()["id"]

    def test_upload_asset(self, client: TestClient) -> None:
        """Should upload competitor asset."""
        comp_id = self._create_competitor(client)

        response = client.post(
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

    def test_upload_asset_nonexistent_competitor(self, client: TestClient) -> None:
        """Should reject asset for non-existent competitor."""
        response = client.post(
            "/competitors/assets",
            json={
                "competitor_id": "nonexistent",
                "url": "https://example.com/img.jpg",
            },
        )

        assert response.status_code == 400

    def test_upload_asset_with_tags(self, client: TestClient) -> None:
        """Should accept manual tags."""
        comp_id = self._create_competitor(client)

        response = client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/product.jpg",
                "manual_tags": ["minimalist", "black", "summer"],
            },
        )

        assert response.status_code == 200
        assert "minimalist" in response.json()["manual_tags"]

    def test_list_assets_empty(self, client: TestClient) -> None:
        """Should return empty list when no assets."""
        response = client.get("/competitors/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_list_assets_with_data(self, client: TestClient) -> None:
        """Should list all assets."""
        comp_id = self._create_competitor(client)

        # Upload assets
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img1.jpg"},
        )
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img2.jpg"},
        )

        response = client.get("/competitors/assets")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_list_assets_filter_by_competitor(self, client: TestClient) -> None:
        """Should filter by competitor ID."""
        comp1_id = self._create_competitor(client)
        comp2_resp = client.post(
            "/competitors",
            json={"name": "Competitor 2", "category": "indirect"},
        )
        comp2_id = comp2_resp.json()["id"]

        # Upload to both
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp1_id, "url": "https://example.com/c1.jpg"},
        )
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp2_id, "url": "https://example.com/c2.jpg"},
        )

        response = client.get(f"/competitors/assets?competitor_id={comp1_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["assets"][0]["competitor_id"] == comp1_id

    def test_get_asset_by_id(self, client: TestClient) -> None:
        """Should get asset by ID."""
        comp_id = self._create_competitor(client)
        upload_resp = client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = client.get(f"/competitors/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["id"] == asset_id

    def test_update_asset(self, client: TestClient) -> None:
        """Should update asset metadata."""
        comp_id = self._create_competitor(client)
        upload_resp = client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = client.patch(
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

    def test_delete_asset(self, client: TestClient) -> None:
        """Should delete asset."""
        comp_id = self._create_competitor(client)
        upload_resp = client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img.jpg"},
        )
        asset_id = upload_resp.json()["id"]

        response = client.delete(f"/competitors/assets/{asset_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

    def test_delete_competitor_cascades_assets(self, client: TestClient) -> None:
        """Should delete associated assets when competitor deleted."""
        comp_id = self._create_competitor(client)

        # Upload assets
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img1.jpg"},
        )
        client.post(
            "/competitors/assets",
            json={"competitor_id": comp_id, "url": "https://example.com/img2.jpg"},
        )

        # Delete competitor
        client.delete(f"/competitors/{comp_id}")

        # Verify assets deleted
        response = client.get("/competitors/assets")
        assert response.json()["total"] == 0


# =============================================================================
# Analytics Tests
# =============================================================================


class TestAnalytics:
    """Tests for analytics endpoints."""

    def test_style_analytics_empty(self, client: TestClient) -> None:
        """Should return empty analytics when no data."""
        response = client.get("/competitors/analytics/style-distribution")

        assert response.status_code == 200
        data = response.json()
        assert data["total_assets"] == 0

    def test_style_analytics_with_data(self, client: TestClient) -> None:
        """Should return style distribution."""
        # Create competitor with assets
        comp_resp = client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Add assets with extracted attributes (manually for testing)
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
        _competitor_assets[asset.id] = asset

        response = client.get("/competitors/analytics/style-distribution")

        assert response.status_code == 200
        data = response.json()
        assert data["total_assets"] == 1
        assert len(data["style_distribution"]) > 0

    def test_summary_analytics(self, client: TestClient) -> None:
        """Should return summary analytics."""
        # Create competitors
        client.post(
            "/competitors",
            json={"name": "Comp 1", "category": "direct", "price_positioning": "premium"},
        )
        client.post(
            "/competitors",
            json={"name": "Comp 2", "category": "indirect", "price_positioning": "luxury"},
        )

        response = client.get("/competitors/analytics/summary")

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

    def test_filter_by_tags(self, client: TestClient) -> None:
        """Should filter by tags."""
        comp_resp = client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Create assets with different tags
        client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/summer.jpg",
                "manual_tags": ["summer", "bright"],
            },
        )
        client.post(
            "/competitors/assets",
            json={
                "competitor_id": comp_id,
                "url": "https://example.com/winter.jpg",
                "manual_tags": ["winter", "dark"],
            },
        )

        response = client.get("/competitors/assets?tags=summer")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "summer" in data["assets"][0]["manual_tags"]

    def test_pagination(self, client: TestClient) -> None:
        """Should paginate results."""
        comp_resp = client.post(
            "/competitors",
            json={"name": "Test", "category": "direct"},
        )
        comp_id = comp_resp.json()["id"]

        # Create 5 assets
        for i in range(5):
            client.post(
                "/competitors/assets",
                json={
                    "competitor_id": comp_id,
                    "url": f"https://example.com/img{i}.jpg",
                },
            )

        # Get page 1
        resp1 = client.get("/competitors/assets?page=1&page_size=2")
        assert resp1.json()["total"] == 5
        assert len(resp1.json()["assets"]) == 2

        # Get page 2
        resp2 = client.get("/competitors/assets?page=2&page_size=2")
        assert len(resp2.json()["assets"]) == 2

        # Get page 3
        resp3 = client.get("/competitors/assets?page=3&page_size=2")
        assert len(resp3.json()["assets"]) == 1
