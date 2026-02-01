# tests/sync/test_sync_modules.py
"""
Comprehensive unit tests for sync modules.

Tests:
- sync/media_sync.py: WordPress media synchronization
- sync/woocommerce_sync.py: WooCommerce product/order sync

Coverage target: 70%+
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from errors.production_errors import ConfigurationError, WordPressIntegrationError


def create_mock_response(json_data: dict | list, status_code: int = 200) -> MagicMock:
    """Create a mock httpx response that behaves correctly."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data  # json() is synchronous in httpx
    mock.raise_for_status = MagicMock()
    return mock


# =============================================================================
# MediaAsset Tests
# =============================================================================


class TestMediaAsset:
    """Tests for MediaAsset dataclass."""

    def test_from_path_valid_image(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should create asset from valid image file."""
        from sync.media_sync import MediaAsset

        # Create a test image file
        image_path = tmp_path / "test_image.jpg"
        image_content = b"fake image content for testing"
        image_path.write_bytes(image_content)

        asset = MediaAsset.from_path(image_path)

        assert asset.local_path == str(image_path)
        assert asset.filename == "test_image.jpg"
        assert asset.mime_type == "image/jpeg"
        assert asset.file_size == len(image_content)
        expected_checksum = hashlib.md5(image_content, usedforsecurity=False).hexdigest()
        assert asset.checksum == expected_checksum
        assert asset.remote_id is None
        assert asset.remote_url is None
        assert asset.last_synced is None

    def test_from_path_valid_png(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should correctly identify PNG files."""
        from sync.media_sync import MediaAsset

        png_path = tmp_path / "test.png"
        png_path.write_bytes(b"png content")

        asset = MediaAsset.from_path(png_path)

        assert asset.mime_type == "image/png"

    def test_from_path_valid_webp(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should correctly identify WebP files."""
        from sync.media_sync import MediaAsset

        webp_path = tmp_path / "test.webp"
        webp_path.write_bytes(b"webp content")

        asset = MediaAsset.from_path(webp_path)

        assert asset.mime_type == "image/webp"

    def test_from_path_3d_model_glb(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should handle .glb 3D files."""
        from sync.media_sync import MediaAsset

        glb_path = tmp_path / "model.glb"
        glb_path.write_bytes(b"glTF binary content")

        asset = MediaAsset.from_path(glb_path)

        assert asset.mime_type == "model/gltf-binary"
        assert asset.filename == "model.glb"

    def test_from_path_3d_model_gltf(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should handle .gltf 3D files."""
        from sync.media_sync import MediaAsset

        gltf_path = tmp_path / "model.gltf"
        gltf_path.write_bytes(b'{"asset": {"version": "2.0"}}')

        asset = MediaAsset.from_path(gltf_path)

        assert asset.mime_type == "model/gltf+json"

    def test_from_path_3d_model_obj(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should handle .obj 3D files correctly."""
        from sync.media_sync import MediaAsset

        obj_path = tmp_path / "model.obj"
        obj_path.write_bytes(b"v 0 0 0\nv 1 0 0\n")

        asset = MediaAsset.from_path(obj_path)

        # The mimetypes module might return different values on different systems
        # Our code handles this by mapping .obj to model/obj
        assert asset.mime_type in ("model/obj", "application/x-tgif")

    def test_from_path_3d_model_usdz(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should handle .usdz 3D files."""
        from sync.media_sync import MediaAsset

        usdz_path = tmp_path / "model.usdz"
        usdz_path.write_bytes(b"usdz content")

        asset = MediaAsset.from_path(usdz_path)

        assert asset.mime_type == "model/vnd.usdz+zip"

    def test_from_path_fbx_model(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should handle .fbx 3D files."""
        from sync.media_sync import MediaAsset

        fbx_path = tmp_path / "model.fbx"
        fbx_path.write_bytes(b"fbx content")

        asset = MediaAsset.from_path(fbx_path)

        assert asset.mime_type == "application/octet-stream"

    def test_from_path_file_not_found(self) -> None:
        """MediaAsset.from_path should raise FileNotFoundError for missing files."""
        from sync.media_sync import MediaAsset

        with pytest.raises(FileNotFoundError, match="File not found"):
            MediaAsset.from_path("/nonexistent/path/file.jpg")

    def test_from_path_accepts_string(self, tmp_path: Path) -> None:
        """MediaAsset.from_path should accept string paths."""
        from sync.media_sync import MediaAsset

        file_path = tmp_path / "test.jpg"
        file_path.write_bytes(b"content")

        asset = MediaAsset.from_path(str(file_path))

        assert asset.local_path == str(file_path)


# =============================================================================
# MediaSyncResult Tests
# =============================================================================


class TestMediaSyncResult:
    """Tests for MediaSyncResult dataclass."""

    def test_default_values(self) -> None:
        """MediaSyncResult should have correct default values."""
        from sync.media_sync import MediaSyncResult

        result = MediaSyncResult(success=True)

        assert result.success is True
        assert result.uploaded == 0
        assert result.skipped == 0
        assert result.failed == 0
        assert result.assets == []
        assert result.errors == []

    def test_with_values(self) -> None:
        """MediaSyncResult should store provided values."""
        from sync.media_sync import MediaAsset, MediaSyncResult

        asset = MediaAsset(
            local_path="/test/path.jpg",
            filename="path.jpg",
            mime_type="image/jpeg",
            file_size=1024,
            checksum="abc123",
        )

        result = MediaSyncResult(
            success=False,
            uploaded=5,
            skipped=2,
            failed=1,
            assets=[asset],
            errors=["Error message"],
        )

        assert result.success is False
        assert result.uploaded == 5
        assert result.skipped == 2
        assert result.failed == 1
        assert len(result.assets) == 1
        assert len(result.errors) == 1


# =============================================================================
# MediaSyncManager Tests
# =============================================================================


class TestMediaSyncManager:
    """Tests for MediaSyncManager class."""

    def test_init_with_explicit_credentials(self) -> None:
        """MediaSyncManager should accept explicit credentials."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        assert manager.url == "https://test.example.com"
        assert manager.username == "testuser"
        assert manager.app_password == "testpass"

    def test_init_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MediaSyncManager should read credentials from environment."""
        from sync.media_sync import MediaSyncManager

        monkeypatch.setenv("WORDPRESS_URL", "https://env.example.com")
        monkeypatch.setenv("WORDPRESS_USERNAME", "envuser")
        monkeypatch.setenv("WORDPRESS_APP_PASSWORD", "envpass")

        manager = MediaSyncManager()

        assert manager.url == "https://env.example.com"
        assert manager.username == "envuser"
        assert manager.app_password == "envpass"

    def test_init_missing_credentials_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MediaSyncManager should raise ConfigurationError when credentials missing."""
        from sync.media_sync import MediaSyncManager

        # Clear any existing env vars
        monkeypatch.delenv("WORDPRESS_URL", raising=False)
        monkeypatch.delenv("WORDPRESS_USERNAME", raising=False)
        monkeypatch.delenv("WORDPRESS_APP_PASSWORD", raising=False)

        with pytest.raises(ConfigurationError, match="WordPress credentials required"):
            MediaSyncManager()

    def test_init_partial_credentials_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """MediaSyncManager should raise when only some credentials provided."""
        from sync.media_sync import MediaSyncManager

        monkeypatch.setenv("WORDPRESS_URL", "https://test.example.com")
        monkeypatch.delenv("WORDPRESS_USERNAME", raising=False)
        monkeypatch.delenv("WORDPRESS_APP_PASSWORD", raising=False)

        with pytest.raises(ConfigurationError):
            MediaSyncManager()

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """MediaSyncManager.close should close the HTTP client."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )
        manager._client = AsyncMock()

        await manager.close()

        manager._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_success(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_file should upload file successfully."""
        from sync.media_sync import MediaSyncManager

        # Create test file
        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"image content")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        # Create mock response with proper synchronous json() method
        mock_response = create_mock_response(
            {
                "id": 123,
                "source_url": "https://test.example.com/wp-content/uploads/test.jpg",
            }
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(return_value=mock_response)

        asset = await manager.upload_file(test_file)

        assert asset.remote_id == 123
        assert asset.remote_url == "https://test.example.com/wp-content/uploads/test.jpg"
        assert asset.last_synced is not None

    @pytest.mark.asyncio
    async def test_upload_file_with_metadata(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_file should update metadata when provided."""
        from sync.media_sync import MediaSyncManager

        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"image content")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response(
            {"id": 123, "source_url": "https://test.example.com/test.jpg"}
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(return_value=mock_response)

        await manager.upload_file(
            test_file,
            title="Test Title",
            alt_text="Test Alt",
            caption="Test Caption",
        )

        # Should have called post twice: once for upload, once for metadata update
        assert manager._client.post.call_count == 2

    @pytest.mark.asyncio
    async def test_upload_file_duplicate_detection(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_file should skip duplicate files."""
        from sync.media_sync import MediaAsset, MediaSyncManager

        test_file = tmp_path / "test.jpg"
        test_content = b"image content"
        test_file.write_bytes(test_content)
        checksum = hashlib.md5(test_content, usedforsecurity=False).hexdigest()

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        # Pre-populate synced assets cache
        existing_asset = MediaAsset(
            local_path="/existing/path.jpg",
            filename="path.jpg",
            mime_type="image/jpeg",
            file_size=100,
            checksum=checksum,
            remote_id=456,
            remote_url="https://existing.url/path.jpg",
        )
        manager._synced_assets[checksum] = existing_asset

        result = await manager.upload_file(test_file)

        # Should return existing asset without making HTTP call
        assert result.remote_id == 456
        assert result.remote_url == "https://existing.url/path.jpg"

    @pytest.mark.asyncio
    async def test_upload_file_http_error(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_file should raise WordPressIntegrationError on HTTP error."""
        from sync.media_sync import MediaSyncManager

        test_file = tmp_path / "test.jpg"
        test_file.write_bytes(b"content")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        # Create proper HTTPStatusError
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        error = httpx.HTTPStatusError(
            message="Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to upload"):
            await manager.upload_file(test_file)

    @pytest.mark.asyncio
    async def test_upload_3d_model_success(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_3d_model should upload 3D models."""
        from sync.media_sync import MediaSyncManager

        model_file = tmp_path / "product.glb"
        model_file.write_bytes(b"glTF binary content")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response(
            {"id": 789, "source_url": "https://test.example.com/product.glb"}
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(return_value=mock_response)

        asset = await manager.upload_3d_model(model_file, product_name="Test Product")

        assert asset.remote_id == 789

    @pytest.mark.asyncio
    async def test_upload_3d_model_unsupported_format(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_3d_model should reject unsupported formats."""
        from sync.media_sync import MediaSyncManager

        unsupported_file = tmp_path / "model.stl"  # .stl is not in SUPPORTED_3D
        unsupported_file.write_bytes(b"unknown format")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        with pytest.raises(ValueError, match="Unsupported 3D format"):
            await manager.upload_3d_model(unsupported_file)

    @pytest.mark.asyncio
    async def test_upload_product_images(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_product_images should upload multiple images."""
        from sync.media_sync import MediaSyncManager

        # Create test images
        img1 = tmp_path / "product_main.jpg"
        img2 = tmp_path / "product_angle1.png"
        img1.write_bytes(b"main image unique content 1")
        img2.write_bytes(b"angle image unique content 2")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return create_mock_response(
                {
                    "id": call_count,
                    "source_url": f"https://test.example.com/image{call_count}.jpg",
                }
            )

        manager._client = AsyncMock()
        manager._client.post = mock_post

        assets = await manager.upload_product_images([img1, img2], "Test Product")

        assert len(assets) == 2
        assert all(a.remote_id is not None for a in assets)

    @pytest.mark.asyncio
    async def test_upload_product_images_skips_unsupported(self, tmp_path: Path) -> None:
        """MediaSyncManager.upload_product_images should skip unsupported formats."""
        from sync.media_sync import MediaSyncManager

        img1 = tmp_path / "product.jpg"
        unsupported = tmp_path / "product.xyz"
        img1.write_bytes(b"image unique content")
        unsupported.write_bytes(b"unknown")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response(
            {"id": 1, "source_url": "https://test.example.com/img.jpg"}
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(return_value=mock_response)

        assets = await manager.upload_product_images([img1, unsupported], "Test")

        # Should only upload the supported image
        assert len(assets) == 1

    @pytest.mark.asyncio
    async def test_sync_directory_success(self, tmp_path: Path) -> None:
        """MediaSyncManager.sync_directory should sync all files in directory."""
        from sync.media_sync import MediaSyncManager

        # Create test files with unique content
        (tmp_path / "image1.jpg").write_bytes(b"image1 content unique1 " + b"x" * 100)
        (tmp_path / "image2.png").write_bytes(b"image2 content unique2 " + b"y" * 100)
        (tmp_path / "model.glb").write_bytes(b"model content unique3 " + b"z" * 100)
        (tmp_path / "readme.txt").write_bytes(b"ignored")  # Should be ignored

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        upload_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal upload_count
            upload_count += 1
            return create_mock_response(
                {
                    "id": upload_count,
                    "source_url": f"https://test.example.com/file{upload_count}",
                }
            )

        manager._client = AsyncMock()
        manager._client.post = mock_post

        result = await manager.sync_directory(tmp_path)

        assert result.success is True
        assert result.uploaded == 3  # jpg, png, glb
        assert len(result.assets) == 3
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_sync_directory_not_found(self, tmp_path: Path) -> None:
        """MediaSyncManager.sync_directory should handle missing directory."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        result = await manager.sync_directory(tmp_path / "nonexistent")

        assert result.success is False
        assert len(result.errors) == 1
        assert "Directory not found" in result.errors[0]

    @pytest.mark.asyncio
    async def test_sync_directory_handles_errors(self, tmp_path: Path) -> None:
        """MediaSyncManager.sync_directory should handle individual file errors."""
        from sync.media_sync import MediaSyncManager

        (tmp_path / "image.jpg").write_bytes(b"image content")

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        manager._client = AsyncMock()
        manager._client.post = AsyncMock(side_effect=Exception("Upload failed"))

        result = await manager.sync_directory(tmp_path)

        assert result.success is False
        assert result.failed == 1
        assert len(result.errors) == 1

    @pytest.mark.asyncio
    async def test_get_media_by_filename_found(self) -> None:
        """MediaSyncManager.get_media_by_filename should return matching media."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response(
            [
                {"id": 1, "source_url": "https://test.example.com/other.jpg"},
                {"id": 2, "source_url": "https://test.example.com/target.jpg"},
            ]
        )

        manager._client = AsyncMock()
        manager._client.get = AsyncMock(return_value=mock_response)

        result = await manager.get_media_by_filename("target.jpg")

        assert result is not None
        assert result["id"] == 2

    @pytest.mark.asyncio
    async def test_get_media_by_filename_not_found(self) -> None:
        """MediaSyncManager.get_media_by_filename should return None when not found."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response([])

        manager._client = AsyncMock()
        manager._client.get = AsyncMock(return_value=mock_response)

        result = await manager.get_media_by_filename("nonexistent.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_media_by_filename_error(self) -> None:
        """MediaSyncManager.get_media_by_filename should handle errors gracefully."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        manager._client = AsyncMock()
        manager._client.get = AsyncMock(side_effect=Exception("Network error"))

        result = await manager.get_media_by_filename("test.jpg")

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_media_success(self) -> None:
        """MediaSyncManager.delete_media should return True on success."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        mock_response = create_mock_response({}, status_code=200)

        manager._client = AsyncMock()
        manager._client.delete = AsyncMock(return_value=mock_response)

        result = await manager.delete_media(123)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_media_failure(self) -> None:
        """MediaSyncManager.delete_media should return False on failure."""
        from sync.media_sync import MediaSyncManager

        manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="testuser",
            app_password="testpass",
        )

        manager._client = AsyncMock()
        manager._client.delete = AsyncMock(side_effect=Exception("Delete failed"))

        result = await manager.delete_media(123)

        assert result is False


# =============================================================================
# Product Model Tests (WooCommerce)
# =============================================================================


class TestProduct:
    """Tests for WooCommerce Product model."""

    def test_product_creation(self) -> None:
        """Product should be created with required fields."""
        from sync.woocommerce_sync import Product

        product = Product(id=1, name="Test Product", slug="test-product")

        assert product.id == 1
        assert product.name == "Test Product"
        assert product.slug == "test-product"
        assert product.sku == ""
        assert product.status == "publish"

    def test_product_get_image_urls(self) -> None:
        """Product.get_image_urls should extract image URLs."""
        from sync.woocommerce_sync import Product

        product = Product(
            id=1,
            name="Test",
            slug="test",
            images=[
                {"src": "https://example.com/img1.jpg"},
                {"src": "https://example.com/img2.jpg"},
                {"other": "no src"},
            ],
        )

        urls = product.get_image_urls()

        assert urls == ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

    def test_product_get_category_names(self) -> None:
        """Product.get_category_names should extract category names."""
        from sync.woocommerce_sync import Product

        product = Product(
            id=1,
            name="Test",
            slug="test",
            categories=[
                {"name": "Category 1", "id": 1},
                {"name": "Category 2", "id": 2},
            ],
        )

        names = product.get_category_names()

        assert names == ["Category 1", "Category 2"]

    def test_product_get_attribute_found(self) -> None:
        """Product.get_attribute should return attribute value when found."""
        from sync.woocommerce_sync import Product

        product = Product(
            id=1,
            name="Test",
            slug="test",
            attributes=[
                {"name": "Color", "options": ["Red", "Blue"]},
                {"name": "Size", "options": ["Large"]},
            ],
        )

        color = product.get_attribute("Color")
        size = product.get_attribute("size")  # Case insensitive

        assert color == "Red"
        assert size == "Large"

    def test_product_get_attribute_not_found(self) -> None:
        """Product.get_attribute should return None when not found."""
        from sync.woocommerce_sync import Product

        product = Product(
            id=1,
            name="Test",
            slug="test",
            attributes=[],
        )

        result = product.get_attribute("NonExistent")

        assert result is None

    def test_product_get_attribute_empty_options(self) -> None:
        """Product.get_attribute should return None when options empty."""
        from sync.woocommerce_sync import Product

        product = Product(
            id=1,
            name="Test",
            slug="test",
            attributes=[{"name": "Color", "options": []}],
        )

        result = product.get_attribute("Color")

        assert result is None


# =============================================================================
# ProductSyncData Tests
# =============================================================================


class TestProductSyncData:
    """Tests for ProductSyncData dataclass."""

    def test_default_values(self) -> None:
        """ProductSyncData should have correct defaults."""
        from sync.woocommerce_sync import ProductSyncData

        data = ProductSyncData(sku="SKU-001", name="Product Name")

        assert data.sku == "SKU-001"
        assert data.name == "Product Name"
        assert data.description == ""
        assert data.regular_price == ""
        assert data.stock_quantity is None
        assert data.model_3d_url is None


# =============================================================================
# WooCommerceSyncClient Tests
# =============================================================================


class TestWooCommerceSyncClient:
    """Tests for WooCommerceSyncClient class."""

    def test_init_with_explicit_credentials(self) -> None:
        """WooCommerceSyncClient should accept explicit credentials."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        assert client.url == "https://shop.example.com"
        assert client.consumer_key == "ck_test"
        assert client.consumer_secret == "cs_test"

    def test_init_from_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WooCommerceSyncClient should read from environment."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        monkeypatch.setenv("WOOCOMMERCE_URL", "https://env.example.com")
        monkeypatch.setenv("WOOCOMMERCE_KEY", "ck_env")
        monkeypatch.setenv("WOOCOMMERCE_SECRET", "cs_env")

        client = WooCommerceSyncClient()

        assert client.url == "https://env.example.com"
        assert client.consumer_key == "ck_env"
        assert client.consumer_secret == "cs_env"

    def test_init_falls_back_to_wordpress_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WooCommerceSyncClient should fall back to WORDPRESS_URL."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        monkeypatch.delenv("WOOCOMMERCE_URL", raising=False)
        monkeypatch.setenv("WORDPRESS_URL", "https://wp.example.com")
        monkeypatch.setenv("WOOCOMMERCE_KEY", "ck_test")
        monkeypatch.setenv("WOOCOMMERCE_SECRET", "cs_test")

        client = WooCommerceSyncClient()

        assert client.url == "https://wp.example.com"

    def test_init_missing_credentials_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """WooCommerceSyncClient should raise ConfigurationError when credentials missing."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        monkeypatch.delenv("WOOCOMMERCE_URL", raising=False)
        monkeypatch.delenv("WORDPRESS_URL", raising=False)
        monkeypatch.delenv("WOOCOMMERCE_KEY", raising=False)
        monkeypatch.delenv("WOOCOMMERCE_SECRET", raising=False)

        with pytest.raises(ConfigurationError, match="WooCommerce credentials required"):
            WooCommerceSyncClient()

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """WooCommerceSyncClient.close should close HTTP client."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )
        client._client = AsyncMock()

        await client.close()

        client._client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_products_success(self) -> None:
        """WooCommerceSyncClient.get_products should return product list."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            [
                {"id": 1, "name": "Product 1", "slug": "product-1"},
                {"id": 2, "name": "Product 2", "slug": "product-2"},
            ]
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        products = await client.get_products()

        assert len(products) == 2
        assert products[0].id == 1
        assert products[0].name == "Product 1"

    @pytest.mark.asyncio
    async def test_get_products_http_error(self) -> None:
        """WooCommerceSyncClient.get_products should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        error = httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to get products"):
            await client.get_products()

    @pytest.mark.asyncio
    async def test_get_all_products_pagination(self) -> None:
        """WooCommerceSyncClient.get_all_products should handle pagination."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        page_1 = [{"id": i, "name": f"Product {i}", "slug": f"product-{i}"} for i in range(1, 101)]
        page_2 = [
            {"id": i, "name": f"Product {i}", "slug": f"product-{i}"} for i in range(101, 151)
        ]

        call_count = 0

        async def mock_get(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return create_mock_response(page_1)
            else:
                return create_mock_response(page_2)

        client._client = AsyncMock()
        client._client.get = mock_get

        products = await client.get_all_products()

        assert len(products) == 150
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_get_all_products_max_limit(self) -> None:
        """WooCommerceSyncClient.get_all_products should respect max_products."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        products_data = [
            {"id": i, "name": f"Product {i}", "slug": f"product-{i}"} for i in range(1, 101)
        ]

        mock_response = create_mock_response(products_data)

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        products = await client.get_all_products(max_products=50)

        assert len(products) == 50

    @pytest.mark.asyncio
    async def test_get_product_success(self) -> None:
        """WooCommerceSyncClient.get_product should return single product."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({"id": 123, "name": "Test Product"})

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        product = await client.get_product(123)

        assert product["id"] == 123

    @pytest.mark.asyncio
    async def test_get_product_not_found(self) -> None:
        """WooCommerceSyncClient.get_product should raise on 404."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to get product"):
            await client.get_product(999)

    @pytest.mark.asyncio
    async def test_get_product_by_sku_found(self) -> None:
        """WooCommerceSyncClient.get_product_by_sku should return product when found."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            [{"id": 1, "name": "Test", "slug": "test", "sku": "SKU-001"}]
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        result = await client.get_product_by_sku("SKU-001")

        assert result is not None
        assert result.sku == "SKU-001"

    @pytest.mark.asyncio
    async def test_get_product_by_sku_not_found(self) -> None:
        """WooCommerceSyncClient.get_product_by_sku should return None when not found."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response([])

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        result = await client.get_product_by_sku("NONEXISTENT")

        assert result is None

    @pytest.mark.asyncio
    async def test_create_product_success(self) -> None:
        """WooCommerceSyncClient.create_product should create new product."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({"id": 123, "name": "New Product"})

        client._client = AsyncMock()
        client._client.post = AsyncMock(return_value=mock_response)

        result = await client.create_product({"name": "New Product"})

        assert result["id"] == 123
        client._client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_http_error(self) -> None:
        """WooCommerceSyncClient.create_product should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        error = httpx.HTTPStatusError(
            message="Bad Request",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.post = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to create product"):
            await client.create_product({"name": "Invalid"})

    @pytest.mark.asyncio
    async def test_update_product_success(self) -> None:
        """WooCommerceSyncClient.update_product should update existing product."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({"id": 123, "name": "Updated Product"})

        client._client = AsyncMock()
        client._client.put = AsyncMock(return_value=mock_response)

        result = await client.update_product(123, {"name": "Updated Product"})

        assert result["name"] == "Updated Product"

    @pytest.mark.asyncio
    async def test_update_product_http_error(self) -> None:
        """WooCommerceSyncClient.update_product should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            message="Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.put = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to update product"):
            await client.update_product(999, {"name": "Update"})

    @pytest.mark.asyncio
    async def test_delete_product_success(self) -> None:
        """WooCommerceSyncClient.delete_product should delete product."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({"id": 123, "deleted": True})

        client._client = AsyncMock()
        client._client.delete = AsyncMock(return_value=mock_response)

        result = await client.delete_product(123)

        assert result["deleted"] is True

    @pytest.mark.asyncio
    async def test_delete_product_http_error(self) -> None:
        """WooCommerceSyncClient.delete_product should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError(
            message="Forbidden",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.delete = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to delete product"):
            await client.delete_product(123)

    @pytest.mark.asyncio
    async def test_sync_product_creates_new(self) -> None:
        """WooCommerceSyncClient.sync_product should create new product when not exists."""
        from sync.woocommerce_sync import ProductSyncData, WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        # Mock get_products (for SKU lookup) - return empty
        get_response = create_mock_response([])

        # Mock create_product
        post_response = create_mock_response({"id": 999, "name": "New Product"})

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=get_response)
        client._client.post = AsyncMock(return_value=post_response)

        sync_data = ProductSyncData(
            sku="NEW-SKU",
            name="New Product",
            description="Description",
            regular_price="99.99",
        )

        result = await client.sync_product(sync_data)

        assert result["id"] == 999
        client._client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_product_updates_existing(self) -> None:
        """WooCommerceSyncClient.sync_product should update product when exists."""
        from sync.woocommerce_sync import Product, ProductSyncData, WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        # Mock get_product_by_sku to return an existing Product
        # Note: get_product_by_sku returns Product objects, not dicts
        existing_product = Product(id=123, name="Old Name", slug="old", sku="EXIST-SKU")

        # Mock update_product
        put_response = create_mock_response({"id": 123, "name": "Updated Name"})

        client._client = AsyncMock()
        client._client.put = AsyncMock(return_value=put_response)

        # Patch get_product_by_sku to return the existing product directly
        with patch.object(client, "get_product_by_sku", return_value=existing_product):
            sync_data = ProductSyncData(
                sku="EXIST-SKU",
                name="Updated Name",
                regular_price="149.99",
            )

            result = await client.sync_product(sync_data)

            assert result["name"] == "Updated Name"
            client._client.put.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_product_with_3d_model(self) -> None:
        """WooCommerceSyncClient.sync_product should add 3D model metadata."""
        from sync.woocommerce_sync import ProductSyncData, WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        get_response = create_mock_response([])
        post_response = create_mock_response({"id": 456, "name": "3D Product"})

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=get_response)
        client._client.post = AsyncMock(return_value=post_response)

        sync_data = ProductSyncData(
            sku="3D-SKU",
            name="3D Product",
            regular_price="299.99",
            model_3d_url="https://cdn.example.com/model.glb",
        )

        await client.sync_product(sync_data)

        # Verify meta_data includes 3D model info
        call_args = client._client.post.call_args
        product_data = call_args.kwargs.get(
            "json", call_args.args[1] if len(call_args.args) > 1 else {}
        )
        assert "meta_data" in product_data
        meta_keys = [m["key"] for m in product_data["meta_data"]]
        assert "_3d_model_url" in meta_keys
        assert "_has_3d_viewer" in meta_keys

    @pytest.mark.asyncio
    async def test_sync_product_with_stock(self) -> None:
        """WooCommerceSyncClient.sync_product should include stock info."""
        from sync.woocommerce_sync import ProductSyncData, WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        get_response = create_mock_response([])
        post_response = create_mock_response({"id": 789, "name": "Stock Product"})

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=get_response)
        client._client.post = AsyncMock(return_value=post_response)

        sync_data = ProductSyncData(
            sku="STOCK-SKU",
            name="Stock Product",
            regular_price="49.99",
            stock_quantity=100,
        )

        await client.sync_product(sync_data)

        call_args = client._client.post.call_args
        product_data = call_args.kwargs.get(
            "json", call_args.args[1] if len(call_args.args) > 1 else {}
        )
        assert product_data.get("stock_quantity") == 100
        assert product_data.get("manage_stock") is True

    @pytest.mark.asyncio
    async def test_attach_3d_model(self) -> None:
        """WooCommerceSyncClient.attach_3d_model should add 3D model to product."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({"id": 123, "meta_data": []})

        client._client = AsyncMock()
        client._client.put = AsyncMock(return_value=mock_response)

        result = await client.attach_3d_model(123, "https://cdn.example.com/model.glb")

        assert result["id"] == 123
        call_args = client._client.put.call_args
        data = call_args.kwargs.get("json", {})
        assert data["meta_data"][0]["key"] == "_3d_model_url"

    @pytest.mark.asyncio
    async def test_update_inventory(self) -> None:
        """WooCommerceSyncClient.update_inventory should update stock."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            {
                "id": 123,
                "stock_quantity": 50,
                "stock_status": "instock",
            }
        )

        client._client = AsyncMock()
        client._client.put = AsyncMock(return_value=mock_response)

        result = await client.update_inventory(123, stock_quantity=50)

        assert result["stock_quantity"] == 50
        call_args = client._client.put.call_args
        data = call_args.kwargs.get("json", {})
        assert data["stock_quantity"] == 50
        assert data["manage_stock"] is True

    @pytest.mark.asyncio
    async def test_update_inventory_custom_status(self) -> None:
        """WooCommerceSyncClient.update_inventory should allow custom stock status."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            {
                "id": 123,
                "stock_quantity": 0,
                "stock_status": "outofstock",
            }
        )

        client._client = AsyncMock()
        client._client.put = AsyncMock(return_value=mock_response)

        await client.update_inventory(123, stock_quantity=0, stock_status="outofstock")

        call_args = client._client.put.call_args
        data = call_args.kwargs.get("json", {})
        assert data["stock_status"] == "outofstock"

    @pytest.mark.asyncio
    async def test_get_orders_success(self) -> None:
        """WooCommerceSyncClient.get_orders should return orders."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            [
                {"id": 1001, "status": "completed"},
                {"id": 1002, "status": "processing"},
            ]
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        orders = await client.get_orders()

        assert len(orders) == 2
        assert orders[0]["id"] == 1001

    @pytest.mark.asyncio
    async def test_get_orders_with_status_filter(self) -> None:
        """WooCommerceSyncClient.get_orders should filter by status."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response([{"id": 1001, "status": "processing"}])

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        await client.get_orders(status="processing")

        call_args = client._client.get.call_args
        params = call_args.kwargs.get("params", {})
        assert params.get("status") == "processing"

    @pytest.mark.asyncio
    async def test_get_orders_http_error(self) -> None:
        """WooCommerceSyncClient.get_orders should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            message="Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to get orders"):
            await client.get_orders()

    @pytest.mark.asyncio
    async def test_get_categories_success(self) -> None:
        """WooCommerceSyncClient.get_categories should return categories."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response(
            [
                {"id": 1, "name": "Jewelry"},
                {"id": 2, "name": "Accessories"},
            ]
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        categories = await client.get_categories()

        assert len(categories) == 2
        assert categories[0]["name"] == "Jewelry"

    @pytest.mark.asyncio
    async def test_get_categories_http_error(self) -> None:
        """WooCommerceSyncClient.get_categories should raise on HTTP error."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError(
            message="Forbidden",
            request=MagicMock(),
            response=mock_response,
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=error)

        with pytest.raises(WordPressIntegrationError, match="Failed to get categories"):
            await client.get_categories()

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        """WooCommerceSyncClient.health_check should return True when healthy."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({}, status_code=200)

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self) -> None:
        """WooCommerceSyncClient.health_check should return False when unhealthy."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        client._client = AsyncMock()
        client._client.get = AsyncMock(side_effect=Exception("Connection failed"))

        result = await client.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_non_200(self) -> None:
        """WooCommerceSyncClient.health_check should return False on non-200."""
        from sync.woocommerce_sync import WooCommerceSyncClient

        client = WooCommerceSyncClient(
            url="https://shop.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        mock_response = create_mock_response({}, status_code=503)

        client._client = AsyncMock()
        client._client.get = AsyncMock(return_value=mock_response)

        result = await client.health_check()

        assert result is False


# =============================================================================
# Integration Tests (Marked for selective running)
# =============================================================================


@pytest.mark.integration
class TestSyncIntegration:
    """Integration tests requiring external services."""

    @pytest.mark.asyncio
    async def test_media_woo_sync_workflow(self, tmp_path: Path) -> None:
        """Test complete workflow of uploading media and syncing to WooCommerce."""
        from sync.woocommerce_sync import ProductSyncData, WooCommerceSyncClient

        from sync.media_sync import MediaSyncManager

        # Create test image
        image_path = tmp_path / "product.jpg"
        image_path.write_bytes(b"product image content")

        # Create managers with mock credentials
        media_manager = MediaSyncManager(
            wordpress_url="https://test.example.com",
            username="user",
            app_password="pass",
        )
        woo_client = WooCommerceSyncClient(
            url="https://test.example.com",
            consumer_key="ck_test",
            consumer_secret="cs_test",
        )

        # Mock HTTP responses
        media_response = create_mock_response(
            {
                "id": 789,
                "source_url": "https://test.example.com/wp-content/uploads/product.jpg",
            }
        )

        product_get_response = create_mock_response([])
        product_create_response = create_mock_response({"id": 456, "name": "Test Product"})

        media_manager._client = AsyncMock()
        media_manager._client.post = AsyncMock(return_value=media_response)

        woo_client._client = AsyncMock()
        woo_client._client.get = AsyncMock(return_value=product_get_response)
        woo_client._client.post = AsyncMock(return_value=product_create_response)

        # Execute workflow
        media_asset = await media_manager.upload_file(image_path)

        sync_data = ProductSyncData(
            sku="TEST-001",
            name="Test Product",
            regular_price="99.99",
            images=[{"src": media_asset.remote_url}],
        )

        product = await woo_client.sync_product(sync_data)

        # Verify
        assert media_asset.remote_id == 789
        assert product["id"] == 456
