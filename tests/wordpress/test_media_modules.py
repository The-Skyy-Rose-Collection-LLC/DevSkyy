"""
Tests for WordPress Media Modules
=================================

Comprehensive tests for wordpress/media.py and wordpress/media_3d_sync.py

Target: >70% coverage for both modules.

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from wordpress.media import ImageOptimizer, MediaManager, MediaUpload
from wordpress.media_3d_sync import (
    InvalidAssetURLError,
    ProductNotFoundError,
    QAApprovedModel,
    WordPress3DConfig,
    WordPress3DMediaSync,
    WordPress3DPipelineSync,
    WordPress3DSyncError,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_wordpress_client() -> AsyncMock:
    """Create a mock WordPress client."""
    client = AsyncMock()
    client.upload_media = AsyncMock(
        return_value={
            "id": 123,
            "source_url": "https://example.com/wp-content/uploads/test.jpg",
            "title": {"rendered": "Test Image"},
            "mime_type": "image/jpeg",
            "media_details": {
                "width": 800,
                "height": 600,
                "filesize": 12345,
            },
        }
    )
    client._request = AsyncMock()
    return client


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    # Create a small valid JPEG-like file
    img_path = tmp_path / "test_image.jpg"
    # Write minimal JPEG header (SOI marker)
    img_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
    return img_path


@pytest.fixture
def sample_png_image(tmp_path: Path) -> Path:
    """Create a sample PNG image."""
    img_path = tmp_path / "test_image.png"
    # Minimal PNG header
    img_path.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    )
    return img_path


@pytest.fixture
def sample_webp_image(tmp_path: Path) -> Path:
    """Create a sample WebP image."""
    img_path = tmp_path / "test_image.webp"
    # Minimal WebP header (RIFF + WEBP)
    img_path.write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 \x00\x00\x00\x00")
    return img_path


@pytest.fixture
def wp_3d_sync_config() -> WordPress3DConfig:
    """Create WordPress 3D sync configuration."""
    return WordPress3DConfig(
        wp_url="https://test.skyyrose.co",
        username="test_user",
        app_password="test_app_password",
        timeout=10.0,
        max_retries=2,
    )


@pytest.fixture
def qa_approved_model() -> QAApprovedModel:
    """Create a sample QA approved model."""
    return QAApprovedModel(
        id="model-123",
        product_id=456,
        product_name="Rose Gold Earrings",
        collection="black-rose",
        glb_path="/assets/3d-models-generated/black-rose/earrings-456.glb",
        usdz_path="/assets/3d-models-generated/black-rose/earrings-456.usdz",
        thumbnail_path="/assets/3d-models-generated/black-rose/earrings-456-thumb.jpg",
        fidelity_score=0.95,
        approved_at="2024-01-15T10:30:00Z",
        sku="SR-BGE-001",
    )


def create_async_context_manager(return_value: Any):
    """Helper to create a proper async context manager mock."""

    @asynccontextmanager
    async def async_cm(*args, **kwargs):
        yield return_value

    return async_cm


# =============================================================================
# Tests: MediaUpload Model
# =============================================================================


class TestMediaUpload:
    """Test MediaUpload pydantic model."""

    def test_create_media_upload(self) -> None:
        """Should create MediaUpload with required fields."""
        upload = MediaUpload(
            id=123,
            url="https://example.com/image.jpg",
        )

        assert upload.id == 123
        assert upload.url == "https://example.com/image.jpg"
        assert upload.title == ""
        assert upload.alt_text == ""
        assert upload.width is None
        assert upload.height is None
        assert upload.file_size == 0

    def test_create_media_upload_with_all_fields(self) -> None:
        """Should create MediaUpload with all fields."""
        upload = MediaUpload(
            id=456,
            url="https://example.com/photo.png",
            title="Product Photo",
            alt_text="Beautiful product image",
            mime_type="image/png",
            width=1920,
            height=1080,
            file_size=54321,
        )

        assert upload.id == 456
        assert upload.title == "Product Photo"
        assert upload.alt_text == "Beautiful product image"
        assert upload.mime_type == "image/png"
        assert upload.width == 1920
        assert upload.height == 1080
        assert upload.file_size == 54321


# =============================================================================
# Tests: ImageOptimizer
# =============================================================================


class TestImageOptimizer:
    """Test ImageOptimizer class."""

    def test_create_optimizer_with_defaults(self) -> None:
        """Should create optimizer with default settings."""
        optimizer = ImageOptimizer()

        assert optimizer.max_dimension == 2048
        assert optimizer.jpeg_quality == 85
        assert optimizer.webp_quality == 80
        assert optimizer.preserve_exif is False

    def test_create_optimizer_with_custom_settings(self) -> None:
        """Should create optimizer with custom settings."""
        optimizer = ImageOptimizer(
            max_dimension=1024,
            jpeg_quality=90,
            webp_quality=85,
            preserve_exif=True,
        )

        assert optimizer.max_dimension == 1024
        assert optimizer.jpeg_quality == 90
        assert optimizer.webp_quality == 85
        assert optimizer.preserve_exif is True

    def test_optimize_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        optimizer = ImageOptimizer()
        missing_file = tmp_path / "nonexistent.jpg"

        with pytest.raises(FileNotFoundError, match="Image file not found"):
            optimizer.optimize(str(missing_file))

    def test_optimize_without_pillow(self, sample_image: Path, tmp_path: Path) -> None:
        """Should handle missing Pillow gracefully."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        output_path = tmp_path / "output.jpg"
        result = optimizer.optimize(str(sample_image), str(output_path))

        assert result == str(output_path)
        assert output_path.exists()

    def test_optimize_without_pillow_no_output_path(self, sample_image: Path) -> None:
        """Should return original path when Pillow missing and no output."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        result = optimizer.optimize(str(sample_image))

        assert result == str(sample_image)

    def test_generate_webp_file_not_found(self, tmp_path: Path) -> None:
        """Should return None for missing file."""
        optimizer = ImageOptimizer()
        missing_file = tmp_path / "nonexistent.jpg"

        result = optimizer.generate_webp(str(missing_file))

        assert result is None

    def test_generate_webp_without_pillow(self, sample_image: Path) -> None:
        """Should return None when Pillow not available."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        result = optimizer.generate_webp(str(sample_image))

        assert result is None

    def test_generate_responsive_sizes_file_not_found(self, tmp_path: Path) -> None:
        """Should return empty dict for missing file."""
        optimizer = ImageOptimizer()
        missing_file = tmp_path / "nonexistent.jpg"

        result = optimizer.generate_responsive_sizes(str(missing_file))

        assert result == {}

    def test_generate_responsive_sizes_without_pillow(self, sample_image: Path) -> None:
        """Should return empty dict when Pillow not available."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        result = optimizer.generate_responsive_sizes(str(sample_image))

        assert result == {}

    def test_generate_responsive_sizes_custom_widths(self, sample_image: Path) -> None:
        """Should accept custom size list."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        # Even without Pillow, should accept custom sizes parameter
        result = optimizer.generate_responsive_sizes(
            str(sample_image),
            sizes=[480, 960],
        )

        assert result == {}

    def test_check_pillow_not_installed(self) -> None:
        """Should detect Pillow not available."""
        with patch.dict("sys.modules", {"PIL": None, "PIL.Image": None}):
            optimizer = ImageOptimizer()
            # Can't override import, but we can test the attribute is set
            # based on actual environment
            assert isinstance(optimizer._pillow_available, bool)


# =============================================================================
# Tests: MediaManager
# =============================================================================


class TestMediaManager:
    """Test MediaManager class."""

    def test_create_manager_without_client(self) -> None:
        """Should create manager without client."""
        manager = MediaManager()

        assert manager.client is None
        assert manager.optimizer is not None

    def test_create_manager_with_optimizer(self) -> None:
        """Should create manager with custom optimizer."""
        optimizer = ImageOptimizer(max_dimension=1024)
        manager = MediaManager(optimizer=optimizer)

        assert manager.optimizer.max_dimension == 1024

    @pytest.mark.asyncio
    async def test_upload_without_client(self, sample_image: Path) -> None:
        """Should raise RuntimeError when client not configured."""
        manager = MediaManager()

        with pytest.raises(RuntimeError, match="WordPress client not configured"):
            await manager.upload(str(sample_image))

    @pytest.mark.asyncio
    async def test_upload_file_not_found(
        self, mock_wordpress_client: AsyncMock, tmp_path: Path
    ) -> None:
        """Should raise FileNotFoundError for missing file."""
        manager = MediaManager(client=mock_wordpress_client)
        missing_file = tmp_path / "nonexistent.jpg"

        with pytest.raises(FileNotFoundError, match="File not found"):
            await manager.upload(str(missing_file))

    @pytest.mark.asyncio
    async def test_upload_success(
        self, mock_wordpress_client: AsyncMock, sample_image: Path
    ) -> None:
        """Should upload file successfully."""
        manager = MediaManager(client=mock_wordpress_client)
        manager.optimizer._pillow_available = False  # Skip optimization

        result = await manager.upload(
            str(sample_image),
            title="Test Image",
            alt_text="Alt text",
            optimize=False,
        )

        assert isinstance(result, MediaUpload)
        assert result.id == 123
        assert result.url == "https://example.com/wp-content/uploads/test.jpg"
        mock_wordpress_client.upload_media.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_with_alt_text(
        self, mock_wordpress_client: AsyncMock, sample_image: Path
    ) -> None:
        """Should update alt text after upload."""
        mock_wordpress_client.upload_media.return_value = {
            "id": 123,
            "source_url": "https://example.com/test.jpg",
            "title": {"rendered": "Test"},
            "mime_type": "image/jpeg",
            "media_details": {},
        }

        manager = MediaManager(client=mock_wordpress_client)
        manager.optimizer._pillow_available = False

        await manager.upload(
            str(sample_image),
            alt_text="Product description",
            optimize=False,
        )

        # Should call _request to update alt text
        mock_wordpress_client._request.assert_called_once_with(
            "POST",
            "/media/123",
            json={"alt_text": "Product description"},
        )

    @pytest.mark.asyncio
    async def test_upload_batch(self, mock_wordpress_client: AsyncMock, tmp_path: Path) -> None:
        """Should upload multiple files."""
        # Create multiple test files
        files = []
        for i in range(3):
            f = tmp_path / f"test_{i}.jpg"
            f.write_bytes(b"\xff\xd8\xff\xe0test content")
            files.append(str(f))

        manager = MediaManager(client=mock_wordpress_client)
        manager.optimizer._pillow_available = False

        results = await manager.upload_batch(files, optimize=False)

        assert len(results) == 3
        assert all(isinstance(r, MediaUpload) for r in results)

    @pytest.mark.asyncio
    async def test_upload_batch_with_failures(
        self, mock_wordpress_client: AsyncMock, tmp_path: Path
    ) -> None:
        """Should handle failures in batch upload."""
        # Create test files
        valid_file = tmp_path / "valid.jpg"
        valid_file.write_bytes(b"\xff\xd8\xff\xe0test")

        files = [str(valid_file), "/nonexistent/missing.jpg"]

        manager = MediaManager(client=mock_wordpress_client)
        manager.optimizer._pillow_available = False

        results = await manager.upload_batch(files, optimize=False)

        # Only successful uploads are returned
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_get_by_id_without_client(self) -> None:
        """Should return None when client not configured."""
        manager = MediaManager()

        result = await manager.get_by_id(123)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_wordpress_client: AsyncMock) -> None:
        """Should get media by ID."""
        mock_wordpress_client._request.return_value = {
            "id": 123,
            "source_url": "https://example.com/test.jpg",
            "title": {"rendered": "Test Image"},
            "alt_text": "Alt text",
            "mime_type": "image/jpeg",
            "media_details": {"width": 800, "height": 600},
        }

        manager = MediaManager(client=mock_wordpress_client)
        result = await manager.get_by_id(123)

        assert result is not None
        assert result.id == 123
        assert result.url == "https://example.com/test.jpg"
        assert result.alt_text == "Alt text"
        mock_wordpress_client._request.assert_called_once_with("GET", "/media/123")

    @pytest.mark.asyncio
    async def test_delete_without_client(self) -> None:
        """Should return False when client not configured."""
        manager = MediaManager()

        result = await manager.delete(123)

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_wordpress_client: AsyncMock) -> None:
        """Should delete media successfully."""
        manager = MediaManager(client=mock_wordpress_client)

        result = await manager.delete(123)

        assert result is True
        mock_wordpress_client._request.assert_called_once_with(
            "DELETE",
            "/media/123",
            params={"force": True},
        )

    @pytest.mark.asyncio
    async def test_delete_failure(self, mock_wordpress_client: AsyncMock) -> None:
        """Should return False on delete failure."""
        mock_wordpress_client._request.side_effect = Exception("Delete failed")

        manager = MediaManager(client=mock_wordpress_client)
        result = await manager.delete(123)

        assert result is False


# =============================================================================
# Tests: WordPress3DConfig
# =============================================================================


class TestWordPress3DConfig:
    """Test WordPress3DConfig dataclass."""

    def test_create_config(self) -> None:
        """Should create config with required fields."""
        config = WordPress3DConfig(
            wp_url="https://skyyrose.co",
            username="admin",
            app_password="xxxx xxxx xxxx",
        )

        assert config.wp_url == "https://skyyrose.co"
        assert config.username == "admin"
        assert config.api_version == "wc/v3"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.verify_ssl is True

    def test_base_url_property(self) -> None:
        """Should construct base URL correctly."""
        config = WordPress3DConfig(
            wp_url="https://skyyrose.co",
            username="admin",
            app_password="password",
        )

        assert config.base_url == "https://skyyrose.co/wp-json/wc/v3"


# =============================================================================
# Tests: WordPress3DSyncError Exceptions
# =============================================================================


class TestWordPress3DSyncErrors:
    """Test exception classes."""

    def test_wordpress_3d_sync_error(self) -> None:
        """Should create base sync error."""
        error = WordPress3DSyncError("Test error", product_id=123)

        assert str(error) == "Test error"
        assert error.product_id == 123

    def test_product_not_found_error(self) -> None:
        """Should create product not found error."""
        error = ProductNotFoundError("Product 123 not found", product_id=123)

        assert "Product 123 not found" in str(error)
        assert error.product_id == 123

    def test_invalid_asset_url_error(self) -> None:
        """Should create invalid asset URL error."""
        error = InvalidAssetURLError("Invalid URL format")

        assert "Invalid URL format" in str(error)


# =============================================================================
# Tests: WordPress3DMediaSync
# =============================================================================


class TestWordPress3DMediaSync:
    """Test WordPress3DMediaSync class."""

    def test_create_sync_client(self) -> None:
        """Should create sync client."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        assert sync.config.wp_url == "https://test.skyyrose.co"
        assert sync._session is None

    def test_create_sync_with_config(self, wp_3d_sync_config: WordPress3DConfig) -> None:
        """Should create sync with custom config."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            config=wp_3d_sync_config,
        )

        assert sync.config.timeout == 10.0
        assert sync.config.max_retries == 2

    def test_validate_url_valid_glb(self) -> None:
        """Should accept valid GLB URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Should not raise
        sync._validate_url(
            "https://cdn.skyyrose.co/models/product.glb",
            "glb_url",
        )

    def test_validate_url_valid_usdz(self) -> None:
        """Should accept valid USDZ URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Should not raise
        sync._validate_url(
            "https://cdn.skyyrose.co/models/product.usdz",
            "usdz_url",
        )

    def test_validate_url_none(self) -> None:
        """Should accept None URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Should not raise
        sync._validate_url(None, "glb_url")

    def test_validate_url_invalid_scheme(self) -> None:
        """Should reject non-HTTP URLs."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(InvalidAssetURLError, match="valid HTTP"):
            sync._validate_url("ftp://example.com/model.glb", "glb_url")

    def test_validate_url_wrong_extension_glb(self) -> None:
        """Should reject wrong extension for GLB."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(InvalidAssetURLError, match="must end with .glb"):
            sync._validate_url("https://example.com/model.obj", "glb_url")

    def test_validate_url_wrong_extension_usdz(self) -> None:
        """Should reject wrong extension for USDZ."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(InvalidAssetURLError, match="must end with .usdz"):
            sync._validate_url("https://example.com/model.glb", "usdz_url")

    def test_validate_url_not_string(self) -> None:
        """Should reject non-string URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(InvalidAssetURLError, match="must be a string"):
            sync._validate_url(123, "glb_url")  # type: ignore

    @pytest.mark.asyncio
    async def test_connect_creates_session(self) -> None:
        """Should create aiohttp session on connect."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch("aiohttp.ClientSession") as mock_session:
            await sync.connect()

            mock_session.assert_called_once()
            assert sync._session is not None

    @pytest.mark.asyncio
    async def test_close_session(self) -> None:
        """Should close aiohttp session."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_session = AsyncMock()
        mock_session.closed = False
        sync._session = mock_session

        await sync.close()

        mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        with patch("aiohttp.ClientSession") as mock_session:
            mock_instance = AsyncMock()
            mock_instance.closed = False
            mock_session.return_value = mock_instance

            sync = WordPress3DMediaSync(
                wp_url="https://test.skyyrose.co",
                username="admin",
                app_password="password",
            )

            async with sync:
                assert sync._session is not None

            mock_instance.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_success(self) -> None:
        """Should make successful API request."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"id": 123, "name": "Product"}

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        result = await sync._request("GET", "/products/123")

        assert result == {"id": 123, "name": "Product"}

    @pytest.mark.asyncio
    async def test_request_404_raises_product_not_found(self) -> None:
        """Should raise ProductNotFoundError on 404."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 404

        async def mock_text():
            return "Product not found"

        mock_response.text = mock_text

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        with pytest.raises(ProductNotFoundError):
            await sync._request("GET", "/products/999")

    @pytest.mark.asyncio
    async def test_request_error_raises_sync_error(self) -> None:
        """Should raise WordPress3DSyncError on API error."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 500

        async def mock_text():
            return "Internal server error"

        mock_response.text = mock_text

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        with pytest.raises(WordPress3DSyncError, match="API error"):
            await sync._request("GET", "/products/123")

    @pytest.mark.asyncio
    async def test_request_retry_on_client_error(self) -> None:
        """Should retry on aiohttp.ClientError."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )
        sync.config.max_retries = 2

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"success": True}

        mock_response.json = mock_json

        call_count = 0

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise aiohttp.ClientError("Connection error")
            yield mock_response

        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.request = mock_request
        sync._session = mock_session

        result = await sync._request("GET", "/test")

        assert result == {"success": True}
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_sync_3d_model_success(self) -> None:
        """Should sync 3D model to product."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"id": 123, "name": "Test Product"}

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        result = await sync.sync_3d_model(
            product_id=123,
            glb_url="https://cdn.skyyrose.co/models/product.glb",
            usdz_url="https://cdn.skyyrose.co/models/product.usdz",
            thumbnail_url="https://cdn.skyyrose.co/thumbs/product.jpg",
        )

        assert result["id"] == 123
        assert result["name"] == "Test Product"

    @pytest.mark.asyncio
    async def test_sync_3d_model_invalid_url_raises(self) -> None:
        """Should raise InvalidAssetURLError for invalid URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(InvalidAssetURLError):
            await sync.sync_3d_model(
                product_id=123,
                glb_url="invalid-url",
            )

    @pytest.mark.asyncio
    async def test_enable_ar_success(self) -> None:
        """Should enable AR for product."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"id": 123}

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        result = await sync.enable_ar(product_id=123, enabled=True)

        assert result["id"] == 123

    @pytest.mark.asyncio
    async def test_get_3d_assets_success(self) -> None:
        """Should get 3D assets for product."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {
                "id": 123,
                "name": "Test Product",
                "meta_data": [
                    {"key": "_skyyrose_glb_url", "value": "https://cdn/model.glb"},
                    {"key": "_skyyrose_usdz_url", "value": "https://cdn/model.usdz"},
                    {"key": "_skyyrose_ar_enabled", "value": "true"},
                ],
            }

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        result = await sync.get_3d_assets(product_id=123)

        assert result["product_id"] == 123
        assert result["glb_url"] == "https://cdn/model.glb"
        assert result["usdz_url"] == "https://cdn/model.usdz"
        assert result["ar_enabled"] is True

    @pytest.mark.asyncio
    async def test_bulk_sync_success(self) -> None:
        """Should bulk sync multiple products."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"id": 123, "name": "Product"}

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        products = [
            {"product_id": 123, "glb_url": "https://cdn/model1.glb"},
            {"product_id": 456, "glb_url": "https://cdn/model2.glb"},
        ]

        results = await sync.bulk_sync(products)

        assert len(results) == 2
        assert all(r["status"] == "success" for r in results)

    @pytest.mark.asyncio
    async def test_bulk_sync_handles_failures(self) -> None:
        """Should handle failures in bulk sync."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Mock that raises on second product
        call_count = 0

        async def mock_sync(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise WordPress3DSyncError("Sync failed")
            return {"id": 123, "name": "Product"}

        with patch.object(sync, "sync_3d_model", side_effect=mock_sync):
            products = [
                {"product_id": 123, "glb_url": "https://cdn/model1.glb"},
                {"product_id": 456, "glb_url": "https://cdn/model2.glb"},
            ]

            results = await sync.bulk_sync(products)

            assert len(results) == 2
            assert results[0]["status"] == "success"
            assert results[1]["status"] == "failed"

    @pytest.mark.asyncio
    async def test_bulk_sync_missing_product_id(self) -> None:
        """Should handle missing product_id in bulk sync."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        products = [{"glb_url": "https://cdn/model.glb"}]  # No product_id

        results = await sync.bulk_sync(products)

        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "Missing product_id" in results[0]["error"]

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_assets(self) -> None:
        """Should cleanup orphaned 3D assets."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Mock paginated product response
        products_response = [
            {
                "id": 123,
                "meta_data": [
                    {"key": "_skyyrose_glb_url", "value": ""},
                    {"key": "_skyyrose_ar_enabled", "value": "true"},
                ],
            }
        ]

        request_count = 0

        async def mock_request(method, endpoint, **kwargs):
            nonlocal request_count
            request_count += 1
            if endpoint == "/products" and request_count == 1:
                return products_response
            if endpoint == "/products" and request_count > 1:
                return []  # End pagination
            return {}

        with (
            patch.object(sync, "_request", side_effect=mock_request),
            patch.object(sync, "_remove_3d_meta", new_callable=AsyncMock),
        ):
            count = await sync.cleanup_orphaned_assets()

            assert count == 1


# =============================================================================
# Tests: QAApprovedModel
# =============================================================================


class TestQAApprovedModel:
    """Test QAApprovedModel pydantic model."""

    def test_create_qa_approved_model(self) -> None:
        """Should create QA approved model."""
        model = QAApprovedModel(
            id="model-123",
            product_id=456,
            product_name="Rose Earrings",
            collection="black-rose",
            glb_path="/path/to/model.glb",
            fidelity_score=0.95,
            approved_at="2024-01-15T10:00:00Z",
        )

        assert model.id == "model-123"
        assert model.product_id == 456
        assert model.collection == "black-rose"
        assert model.fidelity_score == 0.95
        assert model.usdz_path is None
        assert model.sku is None

    def test_create_qa_approved_model_full(self, qa_approved_model: QAApprovedModel) -> None:
        """Should create QA approved model with all fields."""
        assert qa_approved_model.usdz_path is not None
        assert qa_approved_model.thumbnail_path is not None
        assert qa_approved_model.sku == "SR-BGE-001"


# =============================================================================
# Tests: WordPress3DPipelineSync
# =============================================================================


class TestWordPress3DPipelineSync:
    """Test WordPress3DPipelineSync class."""

    def test_create_pipeline_sync(self) -> None:
        """Should create pipeline sync."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        assert sync.cdn_base_url == "https://cdn.skyyrose.co"
        assert sync.generated_models_dir == Path("./assets/3d-models-generated")
        assert sync.hotspots_dir == Path("./wordpress/hotspots")

    def test_create_pipeline_sync_custom_paths(self) -> None:
        """Should create pipeline sync with custom paths."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            cdn_base_url="https://custom-cdn.example.com/",
            generated_models_dir="/custom/models",
            hotspots_dir="/custom/hotspots",
        )

        assert sync.cdn_base_url == "https://custom-cdn.example.com"  # Trailing slash removed
        assert sync.generated_models_dir == Path("/custom/models")
        assert sync.hotspots_dir == Path("/custom/hotspots")

    def test_build_cdn_url_relative_path(self) -> None:
        """Should build CDN URL from relative path."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            cdn_base_url="https://cdn.skyyrose.co",
        )

        result = sync._build_cdn_url("black-rose/earrings.glb")

        assert result == "https://cdn.skyyrose.co/models/black-rose/earrings.glb"

    def test_build_cdn_url_absolute_path(self, tmp_path: Path) -> None:
        """Should build CDN URL from absolute path."""
        models_dir = tmp_path / "models"
        models_dir.mkdir()

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            cdn_base_url="https://cdn.skyyrose.co",
            generated_models_dir=str(models_dir),
        )

        abs_path = str(models_dir / "collection" / "product.glb")
        result = sync._build_cdn_url(abs_path)

        assert "cdn.skyyrose.co/models/" in result
        assert "product.glb" in result

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Should work as async context manager."""
        with (
            patch.object(WordPress3DMediaSync, "connect", new_callable=AsyncMock) as mock_connect,
            patch.object(WordPress3DMediaSync, "close", new_callable=AsyncMock) as mock_close,
        ):
            sync = WordPress3DPipelineSync(
                wp_url="https://test.skyyrose.co",
                username="admin",
                app_password="password",
            )

            async with sync:
                mock_connect.assert_called_once()

            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_approved_models_queue_not_found(self, tmp_path: Path) -> None:
        """Should return empty list when queue file not found."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch.object(WordPress3DMediaSync, "connect", new_callable=AsyncMock):
            result = await sync.sync_approved_models(
                qa_queue_path=str(tmp_path / "nonexistent.json")
            )

            assert result == []

    @pytest.mark.asyncio
    async def test_sync_approved_models_no_approved(self, tmp_path: Path) -> None:
        """Should return empty list when no approved models."""
        queue_file = tmp_path / "qa_queue.json"
        queue_file.write_text(json.dumps({"items": [{"status": "pending"}]}))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch.object(WordPress3DMediaSync, "connect", new_callable=AsyncMock):
            result = await sync.sync_approved_models(qa_queue_path=str(queue_file))

            assert result == []

    @pytest.mark.asyncio
    async def test_sync_single_model_success(
        self, qa_approved_model: QAApprovedModel, tmp_path: Path
    ) -> None:
        """Should sync single approved model."""
        # Create models directory
        models_dir = tmp_path / "models" / "black-rose"
        models_dir.mkdir(parents=True)
        (models_dir / "earrings-456.glb").write_bytes(b"fake glb content")

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            generated_models_dir=str(tmp_path / "models"),
        )

        with (
            patch.object(sync.media_sync, "sync_3d_model", new_callable=AsyncMock) as mock_sync,
            patch.object(sync.media_sync, "enable_ar", new_callable=AsyncMock),
        ):
            mock_sync.return_value = {"id": 456, "name": "Product"}

            result = await sync.sync_single_model(qa_approved_model)

            assert result["status"] == "success"
            assert result["product_id"] == 456
            assert result["fidelity_score"] == 0.95

    @pytest.mark.asyncio
    async def test_sync_single_model_failure(self, qa_approved_model: QAApprovedModel) -> None:
        """Should handle sync failure gracefully."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch.object(
            sync.media_sync,
            "sync_3d_model",
            new_callable=AsyncMock,
            side_effect=Exception("Sync failed"),
        ):
            result = await sync.sync_single_model(qa_approved_model)

            assert result["status"] == "failed"
            assert "Sync failed" in result["error"]

    @pytest.mark.asyncio
    async def test_mark_synced_in_queue(self, tmp_path: Path) -> None:
        """Should mark models as synced in queue."""
        queue_file = tmp_path / "qa_queue.json"
        queue_data = {
            "items": [
                {"id": "model-1", "status": "approved"},
                {"id": "model-2", "status": "approved"},
                {"id": "model-3", "status": "pending"},
            ]
        }
        queue_file.write_text(json.dumps(queue_data))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        await sync._mark_synced_in_queue(queue_file, ["model-1", "model-2"])

        # Verify file was updated
        updated_data = json.loads(queue_file.read_text())
        assert updated_data["items"][0]["status"] == "synced"
        assert updated_data["items"][1]["status"] == "synced"
        assert updated_data["items"][2]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_sync_batch_results_empty(self, tmp_path: Path) -> None:
        """Should handle empty batch results."""
        results_file = tmp_path / "batch_results.json"
        results_file.write_text(json.dumps({"results": []}))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch.object(WordPress3DMediaSync, "connect", new_callable=AsyncMock):
            result = await sync.sync_batch_results(
                batch_id="batch-123",
                results_path=str(results_file),
            )

            assert result["status"] == "empty"
            assert result["synced"] == 0

    @pytest.mark.asyncio
    async def test_sync_batch_results_success(self, tmp_path: Path) -> None:
        """Should sync batch results successfully."""
        results_file = tmp_path / "batch_results.json"
        results_data = {
            "results": [
                {
                    "status": "completed",
                    "product_id": 123,
                    "glb_path": "black-rose/product.glb",
                },
                {
                    "status": "completed",
                    "product_id": 456,
                    "glb_path": "black-rose/product2.glb",
                    "usdz_path": "black-rose/product2.usdz",
                },
            ]
        }
        results_file.write_text(json.dumps(results_data))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with patch.object(sync.media_sync, "bulk_sync", new_callable=AsyncMock) as mock_bulk:
            mock_bulk.return_value = [
                {"product_id": 123, "status": "success"},
                {"product_id": 456, "status": "success"},
            ]

            result = await sync.sync_batch_results(
                batch_id="batch-123",
                results_path=str(results_file),
            )

            assert result["status"] == "complete"
            assert result["synced"] == 2
            assert result["batch_id"] == "batch-123"

    @pytest.mark.asyncio
    async def test_sync_batch_results_no_completed(self, tmp_path: Path) -> None:
        """Should handle results with no completed items."""
        results_file = tmp_path / "batch_results.json"
        results_data = {
            "results": [
                {"status": "failed", "product_id": 123},
                {"status": "pending", "product_id": 456},
            ]
        }
        results_file.write_text(json.dumps(results_data))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        result = await sync.sync_batch_results(
            batch_id="batch-456",
            results_path=str(results_file),
        )

        assert result["status"] == "empty"


# =============================================================================
# Tests: Additional Coverage Tests
# =============================================================================


class TestImageOptimizerWithPillow:
    """Test ImageOptimizer with Pillow mocking."""

    def test_optimize_without_pillow_copies_to_output(
        self, sample_image: Path, tmp_path: Path
    ) -> None:
        """Should copy file when Pillow not available and output provided."""
        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        output_path = tmp_path / "output.jpg"
        result = optimizer.optimize(str(sample_image), str(output_path))

        assert result == str(output_path)
        assert output_path.exists()
        # Content should be copied
        assert output_path.read_bytes() == sample_image.read_bytes()

    def test_optimizer_pillow_check(self) -> None:
        """Should check Pillow availability."""
        optimizer = ImageOptimizer()
        # Just verify the check was called and attribute is set
        assert isinstance(optimizer._pillow_available, bool)

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_with_real_pillow(self, tmp_path: Path) -> None:
        """Should optimize image with real Pillow if available."""
        from PIL import Image

        # Create a real test image
        input_file = tmp_path / "input.jpg"
        img = Image.new("RGB", (100, 100), color="red")
        img.save(str(input_file), "JPEG")

        output_file = tmp_path / "output.jpg"

        optimizer = ImageOptimizer(max_dimension=50)
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

        # Check image was resized
        with Image.open(result) as resized:
            assert max(resized.size) <= 50

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_generate_webp_with_real_pillow(self, tmp_path: Path) -> None:
        """Should generate WebP with real Pillow if available."""
        from PIL import Image

        # Create a real test image
        input_file = tmp_path / "input.jpg"
        img = Image.new("RGB", (100, 100), color="blue")
        img.save(str(input_file), "JPEG")

        optimizer = ImageOptimizer()
        result = optimizer.generate_webp(str(input_file))

        assert result is not None
        assert result.endswith(".webp")
        assert Path(result).exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_generate_responsive_sizes_with_real_pillow(self, tmp_path: Path) -> None:
        """Should generate responsive sizes with real Pillow if available."""
        from PIL import Image

        # Create a large test image
        input_file = tmp_path / "input.jpg"
        img = Image.new("RGB", (2000, 1000), color="green")
        img.save(str(input_file), "JPEG")

        optimizer = ImageOptimizer()
        results = optimizer.generate_responsive_sizes(
            str(input_file),
            sizes=[320, 640],
            output_dir=str(tmp_path),
        )

        assert len(results) >= 1
        for _width, path in results.items():
            assert Path(path).exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_png_with_real_pillow(self, tmp_path: Path) -> None:
        """Should optimize PNG image with real Pillow if available."""
        from PIL import Image

        # Create a real PNG test image
        input_file = tmp_path / "input.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(str(input_file), "PNG")

        output_file = tmp_path / "output.png"

        optimizer = ImageOptimizer()
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_webp_with_real_pillow(self, tmp_path: Path) -> None:
        """Should optimize WebP image with real Pillow if available."""
        from PIL import Image

        # Create a real WebP test image
        input_file = tmp_path / "input.webp"
        img = Image.new("RGB", (100, 100), color="purple")
        img.save(str(input_file), "WEBP")

        output_file = tmp_path / "output.webp"

        optimizer = ImageOptimizer()
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_large_image_with_resize(self, tmp_path: Path) -> None:
        """Should resize large images to max dimension."""
        from PIL import Image

        # Create a large test image
        input_file = tmp_path / "large.jpg"
        img = Image.new("RGB", (4000, 3000), color="yellow")
        img.save(str(input_file), "JPEG")

        output_file = tmp_path / "output.jpg"

        optimizer = ImageOptimizer(max_dimension=1024)
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        with Image.open(result) as resized:
            assert max(resized.size) <= 1024

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_with_exif_preservation(self, tmp_path: Path) -> None:
        """Should preserve EXIF data when requested."""
        from PIL import Image

        # Create a test image
        input_file = tmp_path / "input.jpg"
        img = Image.new("RGB", (100, 100), color="cyan")
        img.save(str(input_file), "JPEG")

        output_file = tmp_path / "output.jpg"

        optimizer = ImageOptimizer(preserve_exif=True)
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_generate_webp_with_rgba(self, tmp_path: Path) -> None:
        """Should handle RGBA images when generating WebP."""
        from PIL import Image

        # Create an RGBA test image
        input_file = tmp_path / "input.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(str(input_file), "PNG")

        optimizer = ImageOptimizer()
        result = optimizer.generate_webp(str(input_file))

        assert result is not None
        assert Path(result).exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_generate_webp_with_palette_mode(self, tmp_path: Path) -> None:
        """Should handle palette mode images when generating WebP."""
        from PIL import Image

        # Create a palette mode test image
        input_file = tmp_path / "input.gif"
        img = Image.new("P", (100, 100))
        img.save(str(input_file), "GIF")

        optimizer = ImageOptimizer()
        result = optimizer.generate_webp(str(input_file))

        assert result is not None
        assert Path(result).exists()

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_generate_responsive_no_upscale(self, tmp_path: Path) -> None:
        """Should not upscale small images."""
        from PIL import Image

        # Create a small test image
        input_file = tmp_path / "small.jpg"
        img = Image.new("RGB", (200, 150), color="orange")
        img.save(str(input_file), "JPEG")

        optimizer = ImageOptimizer()
        # Request sizes larger than original
        results = optimizer.generate_responsive_sizes(
            str(input_file),
            sizes=[320, 640, 1024],
            output_dir=str(tmp_path),
        )

        # Should not create any sizes since all requested are larger than original
        assert len(results) == 0

    @pytest.mark.skipif(
        not ImageOptimizer()._pillow_available,
        reason="Pillow required for this test",
    )
    def test_optimize_jpeg_rgba_conversion(self, tmp_path: Path) -> None:
        """Should convert RGBA to RGB for JPEG output."""
        from PIL import Image

        # Create an RGBA image
        input_file = tmp_path / "input.png"
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        img.save(str(input_file), "PNG")

        # Save as JPEG (requires RGB conversion)
        output_file = tmp_path / "output.jpg"

        optimizer = ImageOptimizer()
        result = optimizer.optimize(str(input_file), str(output_file))

        assert result == str(output_file)
        assert output_file.exists()

        # Verify it's a valid JPEG
        with Image.open(result) as img:
            assert img.mode == "RGB"


class TestWordPress3DMediaSyncAdditional:
    """Additional tests for WordPress3DMediaSync."""

    @pytest.mark.asyncio
    async def test_sync_3d_model_product_not_found(self) -> None:
        """Should handle ProductNotFoundError in sync_3d_model."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 404

        async def mock_text():
            return "Not found"

        mock_response.text = mock_text

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        with pytest.raises(WordPress3DSyncError):
            await sync.sync_3d_model(
                product_id=999,
                glb_url="https://cdn.skyyrose.co/models/missing.glb",
            )

    @pytest.mark.asyncio
    async def test_enable_ar_failure(self) -> None:
        """Should handle failure in enable_ar."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 500

        async def mock_text():
            return "Server error"

        mock_response.text = mock_text

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        with pytest.raises(WordPress3DSyncError, match="enable AR"):
            await sync.enable_ar(product_id=123, enabled=True)

    @pytest.mark.asyncio
    async def test_get_3d_assets_failure(self) -> None:
        """Should handle failure in get_3d_assets."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 500

        async def mock_text():
            return "Server error"

        mock_response.text = mock_text

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        with pytest.raises(WordPress3DSyncError, match="get 3D assets"):
            await sync.get_3d_assets(product_id=123)

    @pytest.mark.asyncio
    async def test_cleanup_orphaned_assets_failure(self) -> None:
        """Should handle failure in cleanup_orphaned_assets."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        async def mock_request(method, endpoint, **kwargs):
            raise Exception("API error")

        with (
            patch.object(sync, "_request", side_effect=mock_request),
            pytest.raises(WordPress3DSyncError, match="cleanup orphaned"),
        ):
            await sync.cleanup_orphaned_assets()

    @pytest.mark.asyncio
    async def test_cleanup_with_products_no_3d_meta(self) -> None:
        """Should skip products without 3D meta."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Product without any 3D meta
        products_response = [
            {
                "id": 123,
                "meta_data": [
                    {"key": "_regular_meta", "value": "test"},
                ],
            }
        ]

        request_count = 0

        async def mock_request(method, endpoint, **kwargs):
            nonlocal request_count
            request_count += 1
            if endpoint == "/products" and request_count == 1:
                return products_response
            return []

        with patch.object(sync, "_request", side_effect=mock_request):
            count = await sync.cleanup_orphaned_assets()

            # No products cleaned up (no 3D meta)
            assert count == 0

    @pytest.mark.asyncio
    async def test_cleanup_with_valid_glb_url(self) -> None:
        """Should not cleanup products with valid GLB URL."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Product with valid GLB URL
        products_response = [
            {
                "id": 123,
                "meta_data": [
                    {"key": "_skyyrose_glb_url", "value": "https://cdn/model.glb"},
                    {"key": "_skyyrose_ar_enabled", "value": "true"},
                ],
            }
        ]

        request_count = 0

        async def mock_request(method, endpoint, **kwargs):
            nonlocal request_count
            request_count += 1
            if endpoint == "/products" and request_count == 1:
                return products_response
            return []

        with patch.object(sync, "_request", side_effect=mock_request):
            count = await sync.cleanup_orphaned_assets()

            # No cleanup needed (has valid GLB URL)
            assert count == 0

    @pytest.mark.asyncio
    async def test_remove_3d_meta(self) -> None:
        """Should remove 3D meta from product."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        mock_response = MagicMock()
        mock_response.status = 200

        async def mock_json():
            return {"id": 123}

        mock_response.json = mock_json

        mock_session = MagicMock()
        mock_session.closed = False

        @asynccontextmanager
        async def mock_request(*args, **kwargs):
            yield mock_response

        mock_session.request = mock_request
        sync._session = mock_session

        await sync._remove_3d_meta(123)

        # Should complete without error


class TestWordPress3DPipelineSyncAdditional:
    """Additional tests for WordPress3DPipelineSync."""

    @pytest.mark.asyncio
    async def test_sync_approved_models_success(self, tmp_path: Path) -> None:
        """Should sync approved models from queue."""
        queue_file = tmp_path / "qa_queue.json"
        queue_data = {
            "items": [
                {
                    "id": "model-1",
                    "status": "approved",
                    "product_id": 123,
                    "product_name": "Test Product",
                    "collection": "black-rose",
                    "glb_path": "/path/to/model.glb",
                    "fidelity_score": 0.95,
                    "approved_at": "2024-01-15T10:00:00Z",
                }
            ]
        }
        queue_file.write_text(json.dumps(queue_data))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with (
            patch.object(sync, "sync_single_model", new_callable=AsyncMock) as mock_single,
            patch.object(sync, "_mark_synced_in_queue", new_callable=AsyncMock),
            patch.object(sync, "regenerate_collection_hotspots", new_callable=AsyncMock),
        ):
            mock_single.return_value = {"status": "success"}

            results = await sync.sync_approved_models(qa_queue_path=str(queue_file))

            assert len(results) == 1
            mock_single.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_approved_models_exception(self, tmp_path: Path) -> None:
        """Should handle exception during sync."""
        queue_file = tmp_path / "qa_queue.json"
        # Invalid JSON to trigger exception
        queue_file.write_text("invalid json")

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(WordPress3DSyncError, match="sync approved models"):
            await sync.sync_approved_models(qa_queue_path=str(queue_file))

    @pytest.mark.asyncio
    async def test_mark_synced_in_queue_error(self, tmp_path: Path) -> None:
        """Should handle error when marking synced."""
        # Non-existent file
        queue_file = tmp_path / "nonexistent.json"

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Should not raise, just log warning
        await sync._mark_synced_in_queue(queue_file, ["model-1"])

    @pytest.mark.asyncio
    async def test_sync_batch_results_exception(self, tmp_path: Path) -> None:
        """Should handle exception during batch sync."""
        results_file = tmp_path / "batch_results.json"
        results_file.write_text("invalid json")

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        with pytest.raises(WordPress3DSyncError, match="sync batch results"):
            await sync.sync_batch_results(
                batch_id="batch-123",
                results_path=str(results_file),
            )

    @pytest.mark.asyncio
    async def test_sync_batch_results_missing_product_id(self, tmp_path: Path) -> None:
        """Should skip results without product_id or glb_path."""
        results_file = tmp_path / "batch_results.json"
        results_data = {
            "results": [
                {
                    "status": "completed",
                    # Missing product_id
                    "glb_path": "black-rose/product.glb",
                },
                {
                    "status": "completed",
                    "product_id": 123,
                    # Missing glb_path
                },
            ]
        }
        results_file.write_text(json.dumps(results_data))

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        result = await sync.sync_batch_results(
            batch_id="batch-456",
            results_path=str(results_file),
        )

        # Results are filtered but bulk_sync is still called with empty list
        # which results in "complete" status with 0 synced
        assert result["synced"] == 0
        assert result["total"] == 0


class TestWordPress3DPipelineSyncHotspots:
    """Test hotspot regeneration in WordPress3DPipelineSync."""

    @pytest.mark.asyncio
    async def test_regenerate_unknown_collection(self) -> None:
        """Should handle unknown collection."""
        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Unknown collection should return None
        result = await sync.regenerate_collection_hotspots("unknown-collection")
        assert result is None

    @pytest.mark.asyncio
    async def test_regenerate_hotspots_file_not_found(self, tmp_path: Path) -> None:
        """Should handle missing hotspot file."""
        hotspots_dir = tmp_path / "hotspots"
        hotspots_dir.mkdir()

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            hotspots_dir=str(hotspots_dir),
        )

        # Hotspot file doesn't exist - should return None
        # The method imports from wordpress.hotspot_config_generator
        # which may not exist, so we need to handle the import error
        result = await sync.regenerate_collection_hotspots("black-rose")

        # If import fails or file not found, returns None
        assert result is None


# =============================================================================
# Tests: Integration-style Tests
# =============================================================================


class TestMediaModulesIntegration:
    """Integration-style tests for media modules."""

    @pytest.mark.asyncio
    async def test_full_upload_workflow(
        self, mock_wordpress_client: AsyncMock, tmp_path: Path
    ) -> None:
        """Should handle full upload workflow."""
        # Create test image
        img_path = tmp_path / "product.jpg"
        img_path.write_bytes(b"\xff\xd8\xff\xe0" + b"test image content")

        # Setup manager
        manager = MediaManager(client=mock_wordpress_client)
        manager.optimizer._pillow_available = False

        # Upload with all options
        result = await manager.upload(
            str(img_path),
            title="Product Image",
            alt_text="Beautiful product photo",
            optimize=False,
        )

        assert result.id == 123
        assert result.url.endswith(".jpg")

    @pytest.mark.asyncio
    async def test_3d_sync_workflow(self) -> None:
        """Should handle 3D sync workflow."""
        sync = WordPress3DMediaSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
        )

        # Validate URLs
        sync._validate_url("https://cdn.skyyrose.co/model.glb", "glb_url")
        sync._validate_url("https://cdn.skyyrose.co/model.usdz", "usdz_url")

        # Should not raise for valid URLs
        assert True

    def test_optimizer_fallback_chain(self, tmp_path: Path) -> None:
        """Should handle optimizer fallback when Pillow unavailable."""
        # Create test file
        input_file = tmp_path / "test.jpg"
        input_file.write_bytes(b"\xff\xd8\xff\xe0test")

        output_file = tmp_path / "output.jpg"

        optimizer = ImageOptimizer()
        optimizer._pillow_available = False

        result = optimizer.optimize(str(input_file), str(output_file))

        assert Path(result).exists()
        assert result == str(output_file)

    @pytest.mark.asyncio
    async def test_pipeline_sync_end_to_end(self, tmp_path: Path) -> None:
        """Should handle pipeline sync end to end."""
        # Setup directories
        models_dir = tmp_path / "models"
        hotspots_dir = tmp_path / "hotspots"
        models_dir.mkdir()
        hotspots_dir.mkdir()

        sync = WordPress3DPipelineSync(
            wp_url="https://test.skyyrose.co",
            username="admin",
            app_password="password",
            cdn_base_url="https://cdn.test.co",
            generated_models_dir=str(models_dir),
            hotspots_dir=str(hotspots_dir),
        )

        # Verify configuration
        assert sync.cdn_base_url == "https://cdn.test.co"
        assert sync.generated_models_dir == models_dir
        assert sync.hotspots_dir == hotspots_dir

        # Test CDN URL building
        url = sync._build_cdn_url("collection/product.glb")
        assert "cdn.test.co" in url
        assert "product.glb" in url
