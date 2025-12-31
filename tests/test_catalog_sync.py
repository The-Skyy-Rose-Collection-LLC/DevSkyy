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
            sync_time_seconds=45.0,
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
            sync_time_seconds=5.0,
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
            sync_time_seconds=30.0,
            errors=[],
            warnings=["Photoshoot generation skipped due to missing textures"],
        )

        assert result.success is True
        assert result.photoshoot_generated is False
        assert len(result.warnings) == 1


# =============================================================================
# CatalogSyncEngine Tests
# =============================================================================


class TestCatalogSyncEngine:
    """Tests for CatalogSyncEngine class."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return CatalogSyncEngine()

    @pytest.fixture
    def custom_engine(self):
        """Create engine with custom config."""
        config = SyncConfig(
            generate_3d_model=False,
            generate_photoshoot=False,
        )
        return CatalogSyncEngine(config=config)

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
        assert engine.wordpress_client is not None

    def test_engine_custom_config(self, custom_engine):
        """Should use custom config."""
        assert custom_engine.config.generate_3d_model is False
        assert custom_engine.config.generate_photoshoot is False

    @pytest.mark.asyncio
    async def test_sync_product_success(self, engine, sample_images, product_data):
        """Should sync product successfully."""
        mock_result = SyncResult(
            product_sku="SKR-001",
            success=True,
            wordpress_product_id=12345,
            images_uploaded=3,
            model_uploaded=True,
            photoshoot_generated=True,
            sync_time_seconds=45.0,
            errors=[],
            warnings=[],
        )

        with patch.object(
            engine, "_run_sync_pipeline", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=sample_images,
            )

            assert result.success is True
            assert result.wordpress_product_id == 12345
            assert result.images_uploaded == 3

    @pytest.mark.asyncio
    async def test_sync_product_no_images(self, engine, product_data):
        """Should handle product with no images."""
        mock_result = SyncResult(
            product_sku="SKR-001",
            success=True,
            wordpress_product_id=12345,
            images_uploaded=0,
            model_uploaded=False,
            photoshoot_generated=False,
            sync_time_seconds=15.0,
            errors=[],
            warnings=["No source images provided"],
        )

        with patch.object(
            engine, "_run_sync_pipeline", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=[],
            )

            assert result.success is True
            assert result.images_uploaded == 0
            assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_sync_product_wordpress_error(self, engine, sample_images, product_data):
        """Should handle WordPress API errors."""
        with patch.object(
            engine, "_run_sync_pipeline", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.side_effect = SyncError("WordPress API unavailable")

            with pytest.raises(SyncError, match="WordPress API unavailable"):
                await engine.sync_product(
                    product_sku="SKR-001",
                    product_data=product_data,
                    source_images=sample_images,
                )

    @pytest.mark.asyncio
    async def test_sync_product_without_3d(self, custom_engine, sample_images, product_data):
        """Should skip 3D model generation when disabled."""
        mock_result = SyncResult(
            product_sku="SKR-001",
            success=True,
            wordpress_product_id=12345,
            images_uploaded=3,
            model_uploaded=False,
            photoshoot_generated=False,
            sync_time_seconds=20.0,
            errors=[],
            warnings=[],
        )

        with patch.object(
            custom_engine, "_run_sync_pipeline", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.return_value = mock_result

            result = await custom_engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=sample_images,
            )

            assert result.model_uploaded is False
            assert result.photoshoot_generated is False

    @pytest.mark.asyncio
    async def test_sync_product_retries(self, engine, sample_images, product_data):
        """Should retry on transient failures."""
        call_count = 0

        async def mock_sync(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise SyncError("Transient error")
            return SyncResult(
                product_sku="SKR-001",
                success=True,
                wordpress_product_id=12345,
                images_uploaded=3,
                model_uploaded=True,
                photoshoot_generated=True,
                sync_time_seconds=60.0,
                errors=[],
                warnings=["Succeeded after 3 attempts"],
            )

        with patch.object(engine, "_run_sync_pipeline", side_effect=mock_sync):
            result = await engine.sync_product(
                product_sku="SKR-001",
                product_data=product_data,
                source_images=sample_images,
            )

            assert result.success is True
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_close(self, engine):
        """Should close cleanly."""
        await engine.close()
        # Should complete without error


# =============================================================================
# Bulk Sync Tests
# =============================================================================


class TestBulkSync:
    """Tests for bulk synchronization."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return CatalogSyncEngine()

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
                    "images": [img_path],
                }
            )
        return products

    @pytest.mark.asyncio
    async def test_bulk_sync(self, engine, products):
        """Should sync multiple products."""
        mock_results = [
            SyncResult(
                product_sku=p["sku"],
                success=True,
                wordpress_product_id=12345 + i,
                images_uploaded=1,
                model_uploaded=True,
                photoshoot_generated=True,
                sync_time_seconds=30.0,
                errors=[],
                warnings=[],
            )
            for i, p in enumerate(products)
        ]

        with patch.object(
            engine, "sync_product", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.side_effect = mock_results

            results = await engine.sync_bulk(products)

            assert len(results) == 3
            assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_bulk_sync_partial_failure(self, engine, products):
        """Should handle partial failures in bulk sync."""
        mock_results = [
            SyncResult(
                product_sku="SKR-000",
                success=True,
                wordpress_product_id=12345,
                images_uploaded=1,
                model_uploaded=True,
                photoshoot_generated=True,
                sync_time_seconds=30.0,
                errors=[],
                warnings=[],
            ),
            SyncResult(
                product_sku="SKR-001",
                success=False,
                wordpress_product_id=None,
                images_uploaded=0,
                model_uploaded=False,
                photoshoot_generated=False,
                sync_time_seconds=5.0,
                errors=["API error"],
                warnings=[],
            ),
            SyncResult(
                product_sku="SKR-002",
                success=True,
                wordpress_product_id=12347,
                images_uploaded=1,
                model_uploaded=True,
                photoshoot_generated=True,
                sync_time_seconds=35.0,
                errors=[],
                warnings=[],
            ),
        ]

        with patch.object(
            engine, "sync_product", new_callable=AsyncMock
        ) as mock_sync:
            mock_sync.side_effect = mock_results

            results = await engine.sync_bulk(products)

            assert len(results) == 3
            assert sum(1 for r in results if r.success) == 2
            assert sum(1 for r in results if not r.success) == 1


# =============================================================================
# WordPress Client Integration Tests
# =============================================================================


class TestWordPressIntegration:
    """Tests for WordPress/WooCommerce integration."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return CatalogSyncEngine()

    @pytest.mark.asyncio
    async def test_create_product(self, engine):
        """Should create product in WordPress."""
        mock_response = {
            "id": 12345,
            "name": "Test Product",
            "status": "publish",
        }

        with patch.object(
            engine.wordpress_client,
            "create_product",
            new_callable=AsyncMock,
        ) as mock_create:
            mock_create.return_value = mock_response

            result = await engine._create_wordpress_product(
                product_data={
                    "name": "Test Product",
                    "price": 99.99,
                    "description": "Test description",
                }
            )

            assert result["id"] == 12345

    @pytest.mark.asyncio
    async def test_update_product(self, engine):
        """Should update existing product."""
        mock_response = {
            "id": 12345,
            "name": "Updated Product",
            "status": "publish",
        }

        with patch.object(
            engine.wordpress_client,
            "update_product",
            new_callable=AsyncMock,
        ) as mock_update:
            mock_update.return_value = mock_response

            result = await engine._update_wordpress_product(
                product_id=12345,
                product_data={"name": "Updated Product"},
            )

            assert result["name"] == "Updated Product"

    @pytest.mark.asyncio
    async def test_upload_media(self, engine, tmp_path):
        """Should upload media to WordPress."""
        image_path = tmp_path / "test.jpg"
        image_path.write_bytes(b"fake image data")

        mock_response = {
            "id": 999,
            "source_url": "https://example.com/wp-content/uploads/test.jpg",
        }

        with patch.object(
            engine.wordpress_client,
            "upload_media",
            new_callable=AsyncMock,
        ) as mock_upload:
            mock_upload.return_value = mock_response

            result = await engine._upload_image(image_path)

            assert result["id"] == 999
            assert "source_url" in result


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestSyncErrorHandling:
    """Tests for error handling in sync operations."""

    def test_sync_error_creation(self):
        """Should create SyncError."""
        error = SyncError("Sync failed")

        assert str(error) == "Sync failed"
        assert isinstance(error, Exception)

    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Should handle connection errors."""
        engine = CatalogSyncEngine()

        with patch.object(
            engine.wordpress_client,
            "create_product",
            new_callable=AsyncMock,
            side_effect=ConnectionError("Connection refused"),
        ), pytest.raises((SyncError, ConnectionError)):
            await engine._create_wordpress_product({"name": "Test"})

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Should handle timeout errors."""
        import asyncio

        engine = CatalogSyncEngine()

        with patch.object(
            engine.wordpress_client,
            "create_product",
            new_callable=AsyncMock,
            side_effect=TimeoutError("Request timeout"),
        ), pytest.raises((SyncError, asyncio.TimeoutError)):
            await engine._create_wordpress_product({"name": "Test"})


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_sync_pipeline():
    """Test full sync pipeline (mocked)."""
    engine = CatalogSyncEngine()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            image_path = Path(tmpdir) / "product.jpg"
            image_path.write_bytes(b"fake image data")

            # Mock the entire pipeline
            mock_result = SyncResult(
                product_sku="TEST-001",
                success=True,
                wordpress_product_id=99999,
                images_uploaded=1,
                model_uploaded=True,
                photoshoot_generated=True,
                sync_time_seconds=60.0,
                errors=[],
                warnings=[],
            )

            with patch.object(
                engine, "_run_sync_pipeline", new_callable=AsyncMock
            ) as mock_sync:
                mock_sync.return_value = mock_result

                result = await engine.sync_product(
                    product_sku="TEST-001",
                    product_data={
                        "name": "Test Product",
                        "price": 149.99,
                        "description": "Full pipeline test",
                    },
                    source_images=[image_path],
                )

                assert result.success is True
                assert result.wordpress_product_id == 99999
                assert result.model_uploaded is True
                assert result.photoshoot_generated is True

    finally:
        await engine.close()


__all__ = [
    "TestSyncConfig",
    "TestSyncResult",
    "TestCatalogSyncEngine",
    "TestBulkSync",
    "TestWordPressIntegration",
    "TestSyncErrorHandling",
]
