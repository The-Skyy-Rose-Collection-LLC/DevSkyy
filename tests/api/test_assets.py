"""Tests for Assets API endpoints.

Tests the actual ingest/job-status endpoints and the versioning endpoints
provided by api.v1.assets.  Uses a standalone TestClient with dependency
overrides so tests are isolated from the global rate limiter.
"""

import io
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from services.storage import (
    AssetNotFoundError,
    AssetVersionManager,
    VersionInfo,
    VersionListResponse,
    VersionNotFoundError,
    VersionStatus,
)

from api.v1.assets import get_version_manager, router
from security.jwt_oauth2_auth import TokenPayload, TokenType

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_user() -> TokenPayload:
    """Create mock authenticated user."""
    return TokenPayload(
        sub="user_test",
        jti="jti_test",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def mock_version_manager() -> MagicMock:
    """Create a mock version manager."""
    manager = MagicMock(spec=AssetVersionManager)
    manager.list_versions = AsyncMock(
        return_value=VersionListResponse(
            asset_id="asset_1",
            versions=[],
            total=0,
            current_version=1,
        )
    )
    manager.get_version = AsyncMock(
        return_value=VersionInfo(
            version_id="ver_1",
            asset_id="asset_1",
            version_number=1,
            is_original=True,
            is_current=True,
            status=VersionStatus.ACTIVE,
            r2_key="versioned/asset_1/v1/image.jpg",
            content_hash="sha256_v1",
            file_size_bytes=1024,
            created_at=datetime.now(UTC),
        )
    )
    manager.delete_version = AsyncMock(return_value=None)
    return manager


@pytest.fixture
def app(mock_user: TokenPayload, mock_version_manager: MagicMock) -> FastAPI:
    """Create isolated test FastAPI app with mocked dependencies."""
    from security.jwt_oauth2_auth import get_current_user

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_current_user] = lambda: mock_user
    test_app.dependency_overrides[get_version_manager] = lambda: mock_version_manager
    return test_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Synchronous test client -- no rate limiter, no global middleware."""
    return TestClient(app)


@pytest.fixture
def test_image():
    """Create a test image file (meets minimum 100x100 dimension requirement)."""
    img = Image.new("RGB", (200, 200), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    img_bytes.name = "test.jpg"
    return img_bytes


# ---------------------------------------------------------------------------
# Ingest endpoint tests
# ---------------------------------------------------------------------------


class TestAssetIngest:
    """Test POST /assets/ingest endpoint."""

    def test_ingest_success(self, client: TestClient, test_image):
        """Test successful image ingest returns 202 with job id."""
        response = client.post(
            "/assets/ingest",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"source": "api"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert data["message"] == "Image accepted for processing"

    def test_ingest_invalid_content_type(self, client: TestClient):
        """Test upload with invalid file type returns 400."""
        invalid_file = io.BytesIO(b"not an image")

        response = client.post(
            "/assets/ingest",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={"source": "api"},
        )

        assert response.status_code == 400

    def test_ingest_image_too_small(self, client: TestClient):
        """Test upload with image below minimum dimensions returns 400."""
        img = Image.new("RGB", (50, 50), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        response = client.post(
            "/assets/ingest",
            files={"file": ("small.jpg", buf, "image/jpeg")},
            data={"source": "api"},
        )

        assert response.status_code == 400

    def test_ingest_with_product_id(self, client: TestClient, test_image):
        """Test ingest with optional product_id."""
        response = client.post(
            "/assets/ingest",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"source": "woocommerce", "product_id": "prod-123"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "pending"

    def test_ingest_with_processing_profile(self, client: TestClient, test_image):
        """Test ingest with different processing profiles."""
        response = client.post(
            "/assets/ingest",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"source": "api", "processing_profile": "quick"},
        )

        assert response.status_code == 202

    def test_ingest_webp_format(self, client: TestClient):
        """Test ingest accepts WebP format."""
        img = Image.new("RGB", (200, 200), color="green")
        buf = io.BytesIO()
        img.save(buf, format="WEBP")
        buf.seek(0)

        response = client.post(
            "/assets/ingest",
            files={"file": ("test.webp", buf, "image/webp")},
            data={"source": "dashboard"},
        )

        assert response.status_code == 202

    def test_ingest_png_format(self, client: TestClient):
        """Test ingest accepts PNG format."""
        img = Image.new("RGB", (200, 200), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        response = client.post(
            "/assets/ingest",
            files={"file": ("test.png", buf, "image/png")},
            data={"source": "api"},
        )

        assert response.status_code == 202


# ---------------------------------------------------------------------------
# Job status endpoint tests
# ---------------------------------------------------------------------------


class TestJobStatus:
    """Test GET /assets/jobs/{job_id} endpoint."""

    def test_get_job_not_found(self, client: TestClient):
        """Test getting a non-existent job returns 404."""
        response = client.get("/assets/jobs/nonexistent-job-id")

        assert response.status_code == 404

    def test_get_job_after_ingest(self, client: TestClient, test_image):
        """Test getting job status after ingesting an image."""
        # First ingest an image
        ingest_resp = client.post(
            "/assets/ingest",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
            data={"source": "api"},
        )
        assert ingest_resp.status_code == 202
        job_id = ingest_resp.json()["job_id"]

        # Then check job status
        status_resp = client.get(f"/assets/jobs/{job_id}")

        assert status_resp.status_code == 200
        data = status_resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"


# ---------------------------------------------------------------------------
# Version listing endpoint tests
# ---------------------------------------------------------------------------


class TestVersionListing:
    """Test GET /assets/{asset_id}/versions endpoint."""

    def test_list_versions_success(self, client: TestClient, mock_version_manager: MagicMock):
        """Test listing versions returns 200."""
        response = client.get("/assets/asset_1/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == "asset_1"
        mock_version_manager.list_versions.assert_called_once()

    def test_list_versions_not_found(self, client: TestClient, mock_version_manager: MagicMock):
        """Test listing versions for non-existent asset returns 404."""
        mock_version_manager.list_versions.side_effect = AssetNotFoundError("missing")

        response = client.get("/assets/missing/versions")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Version get endpoint tests
# ---------------------------------------------------------------------------


class TestVersionGet:
    """Test GET /assets/{asset_id}/versions/{n} endpoint."""

    def test_get_version_success(self, client: TestClient, mock_version_manager: MagicMock):
        """Test getting a specific version returns 200."""
        response = client.get("/assets/asset_1/versions/1")

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 1
        mock_version_manager.get_version.assert_called_once()

    def test_get_version_not_found(self, client: TestClient, mock_version_manager: MagicMock):
        """Test getting non-existent version returns 404."""
        mock_version_manager.get_version.side_effect = VersionNotFoundError("a", 99)

        response = client.get("/assets/asset_1/versions/99")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Version delete endpoint tests
# ---------------------------------------------------------------------------


class TestVersionDelete:
    """Test DELETE /assets/{asset_id}/versions/{n} endpoint."""

    def test_delete_version_success(self, client: TestClient, mock_version_manager: MagicMock):
        """Test deleting a non-original version returns 204."""
        response = client.delete("/assets/asset_1/versions/2")

        assert response.status_code == 204
        mock_version_manager.delete_version.assert_called_once()

    def test_delete_original_blocked(self, client: TestClient):
        """Test deleting version 1 (original) is rejected with 400."""
        response = client.delete("/assets/asset_1/versions/1")

        assert response.status_code == 400
        assert "original version" in response.json()["detail"].lower()

    def test_delete_version_not_found(self, client: TestClient, mock_version_manager: MagicMock):
        """Test deleting non-existent version returns 404."""
        mock_version_manager.delete_version.side_effect = VersionNotFoundError("a", 99)

        response = client.delete("/assets/asset_1/versions/99")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Multiple ingest test
# ---------------------------------------------------------------------------


class TestMultipleIngest:
    """Test sequential ingest operations."""

    def test_ingest_multiple_images(self, client: TestClient):
        """Test that multiple images can be ingested sequentially."""
        for i in range(3):
            img = Image.new("RGB", (200, 200), color="red")
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            response = client.post(
                "/assets/ingest",
                files={"file": (f"img{i}.jpg", buf, "image/jpeg")},
                data={"source": "api"},
            )
            assert response.status_code == 202
