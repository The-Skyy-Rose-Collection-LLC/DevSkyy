# tests/api/test_asset_versions_api.py
"""Tests for asset versioning API endpoints.

Implements US-023: Asset versioning with retention policies.

Author: DevSkyy Platform Team
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI

from services.storage import (
    AssetInfo,
    AssetNotFoundError,
    AssetVersionManager,
    RetentionPolicy,
    VersionInfo,
    VersionListResponse,
    VersionNotFoundError,
    VersionStatus,
)


@pytest.fixture
def mock_version_manager() -> MagicMock:
    """Create a mock version manager."""
    manager = MagicMock(spec=AssetVersionManager)

    # Mock async methods
    manager.list_versions = AsyncMock(
        return_value=VersionListResponse(
            asset_id="asset_123",
            versions=[
                VersionInfo(
                    version_id="ver_2",
                    asset_id="asset_123",
                    version_number=2,
                    is_original=False,
                    is_current=True,
                    status=VersionStatus.ACTIVE,
                    r2_key="versioned/asset_123/v2/image.jpg",
                    content_hash="sha256_v2",
                    file_size_bytes=2048,
                    created_at=datetime.now(UTC),
                ),
                VersionInfo(
                    version_id="ver_1",
                    asset_id="asset_123",
                    version_number=1,
                    is_original=True,
                    is_current=False,
                    status=VersionStatus.ARCHIVED,
                    r2_key="versioned/asset_123/v1/image.jpg",
                    content_hash="sha256_v1",
                    file_size_bytes=1024,
                    created_at=datetime.now(UTC),
                ),
            ],
            total=2,
            current_version=2,
        )
    )

    manager.get_version = AsyncMock(
        return_value=VersionInfo(
            version_id="ver_1",
            asset_id="asset_123",
            version_number=1,
            is_original=True,
            is_current=False,
            status=VersionStatus.ARCHIVED,
            r2_key="versioned/asset_123/v1/image.jpg",
            content_hash="sha256_v1",
            file_size_bytes=1024,
            created_at=datetime.now(UTC),
        )
    )

    manager.revert_version = AsyncMock(
        return_value=VersionInfo(
            version_id="ver_3",
            asset_id="asset_123",
            version_number=3,
            is_original=False,
            is_current=True,
            status=VersionStatus.ACTIVE,
            r2_key="versioned/asset_123/v1/image.jpg",
            content_hash="sha256_v1",
            file_size_bytes=1024,
            created_at=datetime.now(UTC),
            source_version=1,
            change_description="Reverted to version 1",
        )
    )

    manager.update_retention = AsyncMock(
        return_value=AssetInfo(
            asset_id="asset_123",
            name="image.jpg",
            category="original",
            current_version=2,
            total_versions=2,
            retention_policy=RetentionPolicy.KEEP_LAST_N,
            retention_value=5,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )

    manager.delete_version = AsyncMock(return_value=None)

    return manager


@pytest.fixture
def mock_user() -> MagicMock:
    """Create a mock authenticated user."""
    from security.jwt_oauth2_auth import TokenPayload, TokenType

    return TokenPayload(
        sub="user_123",
        jti="test_jti_123",
        type=TokenType.ACCESS,
        roles=["user"],
        exp=datetime.now(UTC),
        iat=datetime.now(UTC),
    )


@pytest.fixture
def app(mock_version_manager: MagicMock, mock_user: MagicMock) -> FastAPI:
    """Create test FastAPI app with mocked dependencies."""
    from api.v1.assets import router, get_version_manager
    from security.jwt_oauth2_auth import get_current_user

    app = FastAPI()
    app.include_router(router)

    # Override dependencies
    app.dependency_overrides[get_version_manager] = lambda: mock_version_manager
    app.dependency_overrides[get_current_user] = lambda: mock_user

    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestListVersions:
    """Tests for GET /assets/{asset_id}/versions."""

    def test_list_versions_success(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return version history."""
        response = client.get("/assets/asset_123/versions")

        assert response.status_code == 200
        data = response.json()
        assert data["asset_id"] == "asset_123"
        assert data["total"] == 2
        assert data["current_version"] == 2
        assert len(data["versions"]) == 2
        mock_version_manager.list_versions.assert_called_once()

    def test_list_versions_include_deleted(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should pass include_deleted parameter."""
        response = client.get("/assets/asset_123/versions?include_deleted=true")

        assert response.status_code == 200
        mock_version_manager.list_versions.assert_called_once_with(
            asset_id="asset_123",
            include_deleted=True,
        )

    def test_list_versions_not_found(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return 404 for nonexistent asset."""
        mock_version_manager.list_versions.side_effect = AssetNotFoundError("nonexistent")

        response = client.get("/assets/nonexistent/versions")

        assert response.status_code == 404


class TestGetVersion:
    """Tests for GET /assets/{asset_id}/versions/{n}."""

    def test_get_version_success(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return specific version."""
        response = client.get("/assets/asset_123/versions/1")

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 1
        assert data["is_original"] is True
        mock_version_manager.get_version.assert_called_once_with(
            asset_id="asset_123",
            version_number=1,
        )

    def test_get_version_not_found(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return 404 for nonexistent version."""
        mock_version_manager.get_version.side_effect = VersionNotFoundError(
            "asset_123", 99
        )

        response = client.get("/assets/asset_123/versions/99")

        assert response.status_code == 404


class TestRevertVersion:
    """Tests for POST /assets/{asset_id}/revert."""

    def test_revert_version_success(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should revert to previous version."""
        response = client.post(
            "/assets/asset_123/revert",
            json={"target_version": 1, "create_new_version": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 3
        assert data["source_version"] == 1
        mock_version_manager.revert_version.assert_called_once()

    def test_revert_version_not_found(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return 404 for nonexistent version."""
        mock_version_manager.revert_version.side_effect = VersionNotFoundError(
            "asset_123", 99
        )

        response = client.post(
            "/assets/asset_123/revert",
            json={"target_version": 99},
        )

        assert response.status_code == 404

    def test_revert_invalid_version(
        self, client: TestClient
    ) -> None:
        """Should return 422 for invalid version number."""
        response = client.post(
            "/assets/asset_123/revert",
            json={"target_version": 0},
        )

        assert response.status_code == 422


class TestUpdateRetention:
    """Tests for PUT /assets/{asset_id}/retention."""

    def test_update_retention_success(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should update retention policy."""
        response = client.put(
            "/assets/asset_123/retention",
            json={"policy": "keep_last_n", "value": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["retention_policy"] == "keep_last_n"
        assert data["retention_value"] == 5
        mock_version_manager.update_retention.assert_called_once()

    def test_update_retention_keep_all(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should allow KEEP_ALL without value."""
        mock_version_manager.update_retention.return_value = AssetInfo(
            asset_id="asset_123",
            name="image.jpg",
            category="original",
            current_version=2,
            total_versions=2,
            retention_policy=RetentionPolicy.KEEP_ALL,
            retention_value=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        response = client.put(
            "/assets/asset_123/retention",
            json={"policy": "keep_all"},
        )

        assert response.status_code == 200

    def test_update_retention_requires_value(
        self, client: TestClient
    ) -> None:
        """Should require value for KEEP_LAST_N policy."""
        response = client.put(
            "/assets/asset_123/retention",
            json={"policy": "keep_last_n"},
        )

        assert response.status_code == 400
        assert "requires a value" in response.json()["detail"]

    def test_update_retention_not_found(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return 404 for nonexistent asset."""
        mock_version_manager.update_retention.side_effect = AssetNotFoundError(
            "nonexistent"
        )

        response = client.put(
            "/assets/nonexistent/retention",
            json={"policy": "keep_all"},
        )

        assert response.status_code == 404


class TestDeleteVersion:
    """Tests for DELETE /assets/{asset_id}/versions/{n}."""

    def test_delete_version_success(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should delete version."""
        response = client.delete("/assets/asset_123/versions/2")

        assert response.status_code == 204
        mock_version_manager.delete_version.assert_called_once_with(
            asset_id="asset_123",
            version_number=2,
        )

    def test_delete_original_version_blocked(
        self, client: TestClient
    ) -> None:
        """Should not allow deleting original version."""
        response = client.delete("/assets/asset_123/versions/1")

        assert response.status_code == 400
        assert "original version" in response.json()["detail"].lower()

    def test_delete_version_not_found(
        self, client: TestClient, mock_version_manager: MagicMock
    ) -> None:
        """Should return 404 for nonexistent version."""
        mock_version_manager.delete_version.side_effect = VersionNotFoundError(
            "asset_123", 99
        )

        response = client.delete("/assets/asset_123/versions/99")

        assert response.status_code == 404
