"""Tests for Assets API endpoints."""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_asset_data():
    """Sample asset data for testing."""
    return {
        "id": "test-asset-123",
        "name": "test-product.jpg",
        "url": "https://storage.example.com/test-product.jpg",
        "collection": "signature",
        "sku": "SKY-001",
        "tags": ["rose-gold", "hoodie"],
        "type": "image",
        "size": 2048576,
        "dimensions": {"width": 1920, "height": 1080},
        "uploaded_at": "2026-01-29T00:00:00Z",
    }


@pytest.fixture
def test_image():
    """Create a test image file."""
    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    img_bytes.seek(0)
    img_bytes.name = "test.jpg"
    return img_bytes


class TestAssetsList:
    """Test GET /api/v1/assets endpoint."""

    async def test_list_assets_success(self, client: TestClient, mock_asset_data):
        """Test listing assets with default parameters."""
        with patch("api.v1.assets.get_assets") as mock_get:
            mock_get.return_value = {
                "assets": [mock_asset_data],
                "total": 1,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

            response = client.get("/api/v1/assets")

            assert response.status_code == 200
            data = response.json()
            assert len(data["assets"]) == 1
            assert data["assets"][0]["id"] == "test-asset-123"
            assert data["total"] == 1

    async def test_list_assets_with_collection_filter(self, client: TestClient):
        """Test filtering assets by collection."""
        with patch("api.v1.assets.get_assets") as mock_get:
            mock_get.return_value = {
                "assets": [],
                "total": 0,
                "page": 1,
                "page_size": 20,
                "has_more": False,
            }

            response = client.get("/api/v1/assets?collection=black-rose")

            assert response.status_code == 200
            mock_get.assert_called_once()
            assert mock_get.call_args[1]["collection"] == "black-rose"

    async def test_list_assets_with_type_filter(self, client: TestClient):
        """Test filtering assets by type."""
        response = client.get("/api/v1/assets?type=3d_model")

        assert response.status_code == 200

    async def test_list_assets_pagination(self, client: TestClient):
        """Test pagination parameters."""
        response = client.get("/api/v1/assets?page=2&page_size=10")

        assert response.status_code == 200


class TestAssetsUpload:
    """Test POST /api/v1/assets/upload endpoint."""

    async def test_upload_asset_success(self, client: TestClient, test_image, mock_asset_data):
        """Test successful asset upload."""
        with patch("api.v1.assets.upload_asset") as mock_upload:
            mock_upload.return_value = mock_asset_data

            response = client.post(
                "/api/v1/assets/upload",
                files={"file": ("test.jpg", test_image, "image/jpeg")},
                data={"collection": "signature"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-asset-123"
            assert data["collection"] == "signature"

    async def test_upload_asset_invalid_file_type(self, client: TestClient):
        """Test upload with invalid file type."""
        invalid_file = io.BytesIO(b"not an image")
        invalid_file.name = "test.txt"

        response = client.post(
            "/api/v1/assets/upload",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={"collection": "signature"},
        )

        assert response.status_code == 400

    async def test_upload_asset_missing_collection(self, client: TestClient, test_image):
        """Test upload without collection parameter."""
        response = client.post(
            "/api/v1/assets/upload",
            files={"file": ("test.jpg", test_image, "image/jpeg")},
        )

        # Should use default collection or return 400
        assert response.status_code in [200, 400]

    async def test_upload_asset_with_metadata(self, client: TestClient, test_image):
        """Test upload with additional metadata."""
        with patch("api.v1.assets.upload_asset") as mock_upload:
            mock_upload.return_value = {
                "id": "test-123",
                "name": "test.jpg",
                "collection": "signature",
                "sku": "SKY-999",
                "tags": ["custom"],
            }

            response = client.post(
                "/api/v1/assets/upload",
                files={"file": ("test.jpg", test_image, "image/jpeg")},
                data={
                    "collection": "signature",
                    "sku": "SKY-999",
                    "tags": '["custom"]',
                },
            )

            assert response.status_code == 200


class TestAssetsGet:
    """Test GET /api/v1/assets/{asset_id} endpoint."""

    async def test_get_asset_success(self, client: TestClient, mock_asset_data):
        """Test getting a single asset by ID."""
        with patch("api.v1.assets.get_asset") as mock_get:
            mock_get.return_value = mock_asset_data

            response = client.get("/api/v1/assets/test-asset-123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-asset-123"

    async def test_get_asset_not_found(self, client: TestClient):
        """Test getting non-existent asset."""
        with patch("api.v1.assets.get_asset") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/v1/assets/nonexistent")

            assert response.status_code == 404


class TestAssetsUpdate:
    """Test PUT /api/v1/assets/{asset_id} endpoint."""

    async def test_update_asset_metadata(self, client: TestClient, mock_asset_data):
        """Test updating asset metadata."""
        updated_data = {**mock_asset_data, "sku": "SKY-002", "tags": ["updated"]}

        with patch("api.v1.assets.update_asset") as mock_update:
            mock_update.return_value = updated_data

            response = client.put(
                "/api/v1/assets/test-asset-123",
                json={"sku": "SKY-002", "tags": ["updated"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["sku"] == "SKY-002"

    async def test_update_asset_not_found(self, client: TestClient):
        """Test updating non-existent asset."""
        with patch("api.v1.assets.update_asset") as mock_update:
            mock_update.return_value = None

            response = client.put(
                "/api/v1/assets/nonexistent",
                json={"sku": "SKY-999"},
            )

            assert response.status_code == 404


class TestAssetsDelete:
    """Test DELETE /api/v1/assets/{asset_id} endpoint."""

    async def test_delete_asset_success(self, client: TestClient):
        """Test deleting an asset."""
        with patch("api.v1.assets.delete_asset") as mock_delete:
            mock_delete.return_value = True

            response = client.delete("/api/v1/assets/test-asset-123")

            assert response.status_code == 200

    async def test_delete_asset_not_found(self, client: TestClient):
        """Test deleting non-existent asset."""
        with patch("api.v1.assets.delete_asset") as mock_delete:
            mock_delete.return_value = False

            response = client.delete("/api/v1/assets/nonexistent")

            assert response.status_code == 404


class TestBatchOperations:
    """Test batch operations on assets."""

    async def test_batch_delete(self, client: TestClient):
        """Test batch deletion of assets."""
        with patch("api.v1.assets.batch_delete") as mock_batch:
            mock_batch.return_value = {"deleted": 3, "failed": 0}

            response = client.post(
                "/api/v1/assets/batch/delete",
                json={"asset_ids": ["id1", "id2", "id3"]},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] == 3

    async def test_batch_update_collection(self, client: TestClient):
        """Test batch updating collection."""
        with patch("api.v1.assets.batch_update") as mock_batch:
            mock_batch.return_value = {"updated": 5, "failed": 0}

            response = client.post(
                "/api/v1/assets/batch/update",
                json={
                    "asset_ids": ["id1", "id2", "id3", "id4", "id5"],
                    "collection": "love-hurts",
                },
            )

            assert response.status_code == 200


class TestCollectionStats:
    """Test collection statistics endpoint."""

    async def test_get_collection_stats(self, client: TestClient):
        """Test getting collection statistics."""
        with patch("api.v1.assets.get_collection_stats") as mock_stats:
            mock_stats.return_value = {
                "signature": 50,
                "black-rose": 30,
                "love-hurts": 20,
            }

            response = client.get("/api/v1/assets/stats/collections")

            assert response.status_code == 200
            data = response.json()
            assert data["signature"] == 50
            assert data["black-rose"] == 30
