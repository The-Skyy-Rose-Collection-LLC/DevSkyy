"""
Tests for Catalog Sync Engine
==============================

Tests for the CatalogSyncEngine class and WordPress/WooCommerce synchronization.

Coverage:
- Engine initialization
- Product sync to WordPress
- Image upload
- 3D model generation integration
- Photoshoot generation integration
- Error handling and recovery
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from sync.catalog_sync import (
    CatalogSyncConfig,
    CatalogSyncEngine,
    SyncConfig,
    SyncError,
    SyncResult,
)

# =============================================================================
# SyncConfig Tests
# =============================================================================


class TestSyncConfig:
    """Tests for SyncConfig."""

    def test_default_config(self):
        """Should have sensible defaults."""
        config = SyncConfig()

        assert config.wordpress_url is not None
        assert config.generate_3d_model is True
        assert config.generate_photoshoot is True
        assert config.upload_images is True
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 2.0

    def test_custom_config(self):
        """Should accept custom values."""
        config = SyncConfig(
            wordpress_url="https://custom.example.com",
            generate_3d_model=False,
            generate_photoshoot=False,
            upload_images=True,
            retry_attempts=5,
            retry_delay_seconds=5.0,
        )

        assert config.wordpress_url == "https://custom.example.com"
        assert config.generate_3d_model is False
        assert config.generate_photoshoot is False
        assert config.retry_attempts == 5


class TestCatalogSyncConfig:
    """Tests for CatalogSyncConfig (internal engine config)."""

    def test_default_catalog_config(self):
        """Should have sensible defaults for catalog sync."""
        config = CatalogSyncConfig()

        assert config.upload_main_image is True
        assert config.upload_gallery_images is True
        assert config.upload_3d_model is True
        assert config.generate_photoshoot is True
        assert config.parallel_uploads == 3
        assert config.fidelity_threshold == 0.95

    def test_custom_catalog_config(self):
        """Should accept custom values."""
        config = CatalogSyncConfig(
            upload_3d_model=False,
            generate_photoshoot=False,
            parallel_uploads=5,
            fidelity_threshold=0.90,
        )

        assert config.upload_3d_model is False
        assert config.generate_photoshoot is False
        assert config.parallel_uploads == 5
        assert config.fidelity_threshold == 0.90


# =============================================================================
# SyncResult Tests
# =============================================================================


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_successful_result(self):
        """Should create successful result."""
        result = SyncResult(
            product_sku="SKR-001",
            success=True,
            wordpress_product_id=12345,
            images_uploaded=5,
            model_uploaded=True,
            photoshoot_generated=True,
            errors=[],
            warnings=[],
        )

        assert result.success is True
        assert result.wordpress_product_id == 12345
        assert result.images_uploaded == 5
        assert len(result.errors) == 0

    def test_failed_result(self):
        """Should create failed result with errors."""
        result = SyncResult(
            product_sku="SKR-002",
            success=False,
            wordpress_product_id=None,
            images_uploaded=0,
            model_uploaded=False,
            photoshoot_generated=False,
            errors=["Connection timeout", "API rate limit exceeded"],
            warnings=["Image resolution below recommended"],
        )

        assert result.success is False
        assert result.wordpress_product_id is None
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_partial_result(self):
        """Should handle partial success."""
        result = SyncResult(
            product_sku="SKR-003",
            success=True,
            wordpress_product_id=12346,
            images_uploaded=3,
            model_uploaded=True,
            photoshoot_generated=False,
            errors=[],
            warnings=["Photoshoot generation skipped due to missing textures"],
        )

        assert result.success is True
        assert result.photoshoot_generated is False
        assert len(result.warnings) == 1

    def test_to_dict(self):
        """Should serialize to dictionary."""
        result = SyncResult(
            product_sku="SKR-004",
            success=True,
            wordpress_product_id=12347,
        )
        result_dict = result.to_dict()

        assert result_dict["product_sku"] == "SKR-004"
        assert result_dict["success"] is True
        assert result_dict["wordpress_product_id"] == 12347
        assert "started_at" in result_dict


# =============================================================================
# CatalogSyncEngine Tests
# =============================================================================


class TestCatalogSyncEngine:
    """Tests for CatalogSyncEngine class."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create engine instance with temp directories."""
        return CatalogSyncEngine(
            output_dir=tmp_path / "output",
            models_dir=tmp_path / "models",
            images_dir=tmp_path / "images",
        )

    @pytest.fixture
    def custom_engine(self, tmp_path):
        """Create engine with custom config."""
        config = CatalogSyncConfig(
            upload_3d_model=False,
            generate_photoshoot=False,
        )
        return CatalogSyncEngine(
            config=config,
            output_dir=tmp_path / "output",
            models_dir=tmp_path / "models",
            images_dir=tmp_path / "images",
        )

    @pytest.fixture
    def sample_images(self, tmp_path):
        """Create sample image files."""
        images = []
        for i in range(3):
            img_path = tmp_path / f"product_image_{i}.jpg"
            img_path.write_bytes(b"fake image data " + bytes([i]))
            images.append(img_path)
        return images

    @pytest.fixture
    def product_data(self):
        """Create sample product data."""
        return {
            "name": "SkyyRose Signature Hoodie",
            "price": 129.99,
            "description": "Premium luxury streetwear hoodie",
            "short_description": "Signature hoodie",
            "stock": 50,
            "categories": [1, 2],
            "tags": ["hoodie", "streetwear", "luxury"],
        }

    def test_engine_initialization(self, engine):
        """Should initialize with default config."""
        assert engine.config is not None
        assert isinstance(engine.config, CatalogSyncConfig)

    def test_engine_custom_config(self, custom_engine):
        """Should use custom config."""
        assert custom_engine.config.upload_3d_model is False
        assert custom_engine.config.generate_photoshoot is False

    def test_directories_created(self, engine):
        """Should create output directories on init."""
        assert engine.output_dir.exists()
        assert engine.models_dir.exists()
        assert engine.images_dir.exists()

    @pytest.mark.asyncio
    async def test_sync_product_basic(self, engine, sample_images, product_data):
        """Should sync product and return result."""
        # Mock the WordPress sync to avoid network calls
        with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
            mock_wp.return_value = None  # No WP sync available

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=sample_images,
            )

            assert isinstance(result, SyncResult)
            assert result.product_sku == "SKR-001"
            # Without WP sync, should have warnings
            assert len(result.warnings) > 0 or result.success is False

    @pytest.mark.asyncio
    async def test_sync_product_no_images(self, engine, product_data):
        """Should handle product with no images."""
        with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
            mock_wp.return_value = None

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=[],
            )

            assert isinstance(result, SyncResult)
            assert result.images_uploaded == 0

    @pytest.mark.asyncio
    async def test_sync_product_with_missing_images(self, engine, product_data, tmp_path):
        """Should filter out missing images."""
        # Create one real and one missing image path
        real_image = tmp_path / "real.jpg"
        real_image.write_bytes(b"fake image")
        missing_image = tmp_path / "missing.jpg"

        with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
            mock_wp.return_value = None

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=[real_image, missing_image],
            )

            # Should warn about missing images
            assert any("missing" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_close(self, engine):
        """Should close cleanly."""
        await engine.close()
        # Should complete without error

    @pytest.mark.asyncio
    async def test_get_sync_status(self, engine):
        """Should return sync status for a product."""
        status = await engine.get_sync_status("SKR-001")

        assert status["product_sku"] == "SKR-001"
        assert "has_3d_model" in status
        assert "has_processed_images" in status


# =============================================================================
# Bulk Sync Tests
# =============================================================================


class TestBulkSync:
    """Tests for bulk synchronization."""

    @pytest.fixture
    def engine(self, tmp_path):
        """Create engine instance."""
        return CatalogSyncEngine(
            output_dir=tmp_path / "output",
            models_dir=tmp_path / "models",
            images_dir=tmp_path / "images",
        )

    @pytest.fixture
    def products(self, tmp_path):
        """Create multiple products for bulk sync."""
        products = []
        for i in range(3):
            img_path = tmp_path / f"product_{i}.jpg"
            img_path.write_bytes(b"fake image")
            products.append(
                {
                    "sku": f"SKR-00{i}",
                    "data": {
                        "name": f"Product {i}",
                        "price": 99.99 + i * 10,
                        "description": f"Description {i}",
                    },
                    "images": [str(img_path)],
                }
            )
        return products

    @pytest.mark.asyncio
    async def test_sync_catalog(self, engine, products):
        """Should sync multiple products via sync_catalog."""
        with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
            mock_wp.return_value = None

            results = await engine.sync_catalog(products)

            assert len(results) == 3
            for result in results:
                assert isinstance(result, SyncResult)

    @pytest.mark.asyncio
    async def test_sync_catalog_handles_exceptions(self, engine, products):
        """Should handle exceptions in individual syncs."""
        call_count = 0

        async def mock_sync(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Simulated error")
            return SyncResult(
                product_sku=f"SKR-00{call_count - 1}",
                success=True,
            )

        with patch.object(engine, "sync_product", side_effect=mock_sync):
            results = await engine.sync_catalog(products)

            assert len(results) == 3
            # Second product should have failed
            failed_results = [r for r in results if not r.success]
            assert len(failed_results) >= 1


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestSyncErrorHandling:
    """Tests for error handling in sync operations."""

    def test_sync_error_creation(self):
        """Should create SyncError with source and target."""
        error = SyncError(source="catalog", target="wordpress")

        assert "catalog" in error.message
        assert error.context.get("source") == "catalog"
        assert error.context.get("target") == "wordpress"

    def test_sync_error_with_message(self):
        """Should create SyncError with custom message."""
        error = SyncError(
            source="catalog",
            target="wordpress",
            message="Connection failed",
        )

        assert "Connection failed" in error.message

    @pytest.mark.asyncio
    async def test_engine_handles_sync_exception(self, tmp_path):
        """Should handle exceptions during sync gracefully."""
        engine = CatalogSyncEngine(
            output_dir=tmp_path / "output",
            models_dir=tmp_path / "models",
            images_dir=tmp_path / "images",
        )

        # Create a mock that raises an exception
        with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
            mock_wp.side_effect = Exception("Unexpected error")

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data={"name": "Test"},
                source_images=[],
            )

            # Should return a failed result, not raise
            assert result.success is False
            assert len(result.errors) > 0


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_sync_pipeline():
    """Test full sync pipeline (mocked)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        engine = CatalogSyncEngine(
            output_dir=tmpdir_path / "output",
            models_dir=tmpdir_path / "models",
            images_dir=tmpdir_path / "images",
        )

        try:
            # Create test image
            image_path = tmpdir_path / "product.jpg"
            image_path.write_bytes(b"fake image data")

            # Mock the WordPress sync
            with patch.object(engine, "_get_wp_sync", new_callable=AsyncMock) as mock_wp:
                mock_wp.return_value = None

                result = await engine.sync_product(
                    product_sku="TEST-001",
                    product_data={
                        "name": "Test Product",
                        "price": 149.99,
                        "description": "Full pipeline test",
                    },
                    source_images=[image_path],
                )

                assert isinstance(result, SyncResult)
                assert result.product_sku == "TEST-001"
                assert result.completed_at is not None

        finally:
            await engine.close()


__all__ = [
    "TestSyncConfig",
    "TestCatalogSyncConfig",
    "TestSyncResult",
    "TestCatalogSyncEngine",
    "TestBulkSync",
    "TestSyncErrorHandling",
]
