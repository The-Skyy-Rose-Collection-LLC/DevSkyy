# tests/services/test_format_optimizer.py
"""Unit tests for FormatOptimizer."""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image

from services.ml.enhancement.format_optimizer import (
    JPEG_QUALITY,
    PRINT_DPI,
    SOCIAL_VARIANTS,
    THUMBNAIL_SIZES,
    WEBP_QUALITY,
    FormatOptimizationError,
    FormatOptimizationResult,
    FormatOptimizer,
    ImageVariant,
    OutputFormat,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_r2_client() -> MagicMock:
    """Create mock R2 client."""
    client = MagicMock()
    result = MagicMock()
    result.url = "https://r2.example.com/test-key"
    client.upload_bytes = MagicMock(return_value=result)
    return client


@pytest.fixture
def service(mock_r2_client: MagicMock) -> FormatOptimizer:
    """Create service with mock R2 client."""
    return FormatOptimizer(r2_client=mock_r2_client)


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a sample test image."""
    return Image.new("RGB", (800, 600), color=(255, 0, 0))


# =============================================================================
# Model Tests
# =============================================================================


class TestOutputFormat:
    """Test OutputFormat enum."""

    def test_webp_value(self) -> None:
        """OutputFormat.WEBP should have correct value."""
        assert OutputFormat.WEBP.value == "webp"

    def test_jpeg_value(self) -> None:
        """OutputFormat.JPEG should have correct value."""
        assert OutputFormat.JPEG.value == "jpeg"

    def test_png_value(self) -> None:
        """OutputFormat.PNG should have correct value."""
        assert OutputFormat.PNG.value == "png"

    def test_tiff_value(self) -> None:
        """OutputFormat.TIFF should have correct value."""
        assert OutputFormat.TIFF.value == "tiff"


class TestImageVariant:
    """Test ImageVariant model."""

    def test_variant_creation(self) -> None:
        """Should create variant with all fields."""
        variant = ImageVariant(
            name="web",
            format=OutputFormat.WEBP,
            width=800,
            height=600,
            size_bytes=50000,
            url="https://example.com/image.webp",
            key="enhanced/SKU-123/web.webp",
            content_type="image/webp",
            quality=85,
        )
        assert variant.name == "web"
        assert variant.format == OutputFormat.WEBP
        assert variant.quality == 85

    def test_variant_with_dpi(self) -> None:
        """Should create variant with DPI for print."""
        variant = ImageVariant(
            name="print",
            format=OutputFormat.TIFF,
            width=800,
            height=600,
            size_bytes=1000000,
            url="https://example.com/image.tiff",
            key="enhanced/SKU-123/print.tiff",
            content_type="image/tiff",
            dpi=300,
        )
        assert variant.dpi == 300


class TestFormatOptimizationResult:
    """Test FormatOptimizationResult model."""

    def test_web_variant_property(self) -> None:
        """web_variant should return WebP web variant."""
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(800, 600),
            variants=[
                ImageVariant(
                    name="web",
                    format=OutputFormat.WEBP,
                    width=800,
                    height=600,
                    size_bytes=50000,
                    url="https://example.com/web.webp",
                    key="test/web.webp",
                    content_type="image/webp",
                ),
                ImageVariant(
                    name="fallback",
                    format=OutputFormat.JPEG,
                    width=800,
                    height=600,
                    size_bytes=80000,
                    url="https://example.com/fallback.jpg",
                    key="test/fallback.jpg",
                    content_type="image/jpeg",
                ),
            ],
            total_size_bytes=130000,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        web = result.web_variant
        assert web is not None
        assert web.format == OutputFormat.WEBP
        assert web.name == "web"

    def test_web_variant_none_when_missing(self) -> None:
        """web_variant should return None when not present."""
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(800, 600),
            variants=[],
            total_size_bytes=0,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        assert result.web_variant is None

    def test_print_variant_property(self) -> None:
        """print_variant should return TIFF variant."""
        result = FormatOptimizationResult(
            original_url="https://example.com/original.jpg",
            original_dimensions=(800, 600),
            variants=[
                ImageVariant(
                    name="print",
                    format=OutputFormat.TIFF,
                    width=800,
                    height=600,
                    size_bytes=1000000,
                    url="https://example.com/print.tiff",
                    key="test/print.tiff",
                    content_type="image/tiff",
                    dpi=300,
                ),
            ],
            total_size_bytes=1000000,
            processing_time_ms=100,
            correlation_id="test-123",
        )
        print_var = result.print_variant
        assert print_var is not None
        assert print_var.format == OutputFormat.TIFF


class TestFormatOptimizationError:
    """Test FormatOptimizationError class."""

    def test_error_with_context(self) -> None:
        """Error should include context fields."""
        error = FormatOptimizationError(
            "Test error",
            image_url="https://example.com/image.jpg",
            correlation_id="corr-123",
        )
        assert error.context["image_url"] == "https://example.com/image.jpg"
        assert error.correlation_id == "corr-123"

    def test_error_is_retryable(self) -> None:
        """FormatOptimizationError should be retryable."""
        error = FormatOptimizationError("Test error")
        assert error.retryable is True


# =============================================================================
# Service Tests
# =============================================================================


class TestFormatOptimizerInit:
    """Test service initialization."""

    def test_init_with_client(self, mock_r2_client: MagicMock) -> None:
        """Service should accept pre-configured R2 client."""
        service = FormatOptimizer(r2_client=mock_r2_client)
        assert service._r2_client is mock_r2_client
        assert service._owns_client is False

    def test_init_without_client(self) -> None:
        """Service should mark as owning client when none provided."""
        service = FormatOptimizer()
        assert service._r2_client is None
        assert service._owns_client is True


class TestResizeImage:
    """Test image resizing functionality."""

    def test_resize_maintain_aspect(
        self, service: FormatOptimizer, sample_image: Image.Image
    ) -> None:
        """Should resize while maintaining aspect ratio."""
        resized = service._resize_image(sample_image, (400, 400), maintain_aspect=True)
        # 800x600 -> fits in 400x400 while maintaining aspect
        # Width is limiting factor
        assert resized.size[0] <= 400
        assert resized.size[1] <= 400

    def test_resize_exact_size(self, service: FormatOptimizer, sample_image: Image.Image) -> None:
        """Should resize to exact dimensions when maintain_aspect is False."""
        resized = service._resize_image(sample_image, (200, 200), maintain_aspect=False)
        assert resized.size == (200, 200)


class TestCreateThumbnail:
    """Test thumbnail creation."""

    def test_create_square_thumbnail(
        self, service: FormatOptimizer, sample_image: Image.Image
    ) -> None:
        """Should create square thumbnail with center crop."""
        thumb = service._create_thumbnail(sample_image, (150, 150))
        assert thumb.size == (150, 150)

    def test_thumbnail_does_not_modify_original(
        self, service: FormatOptimizer, sample_image: Image.Image
    ) -> None:
        """Creating thumbnail should not modify original image."""
        original_size = sample_image.size
        service._create_thumbnail(sample_image, (150, 150))
        assert sample_image.size == original_size


class TestConvertToFormat:
    """Test format conversion."""

    def test_convert_to_webp(self, service: FormatOptimizer, sample_image: Image.Image) -> None:
        """Should convert to WebP format."""
        data, content_type = service._convert_to_format(sample_image, OutputFormat.WEBP, quality=85)
        assert content_type == "image/webp"
        assert len(data) > 0
        # Verify it's valid WebP by loading it
        loaded = Image.open(io.BytesIO(data))
        assert loaded.format == "WEBP"

    def test_convert_to_jpeg(self, service: FormatOptimizer, sample_image: Image.Image) -> None:
        """Should convert to JPEG format."""
        data, content_type = service._convert_to_format(sample_image, OutputFormat.JPEG, quality=90)
        assert content_type == "image/jpeg"
        loaded = Image.open(io.BytesIO(data))
        assert loaded.format == "JPEG"

    def test_convert_to_png(self, service: FormatOptimizer, sample_image: Image.Image) -> None:
        """Should convert to PNG format."""
        data, content_type = service._convert_to_format(sample_image, OutputFormat.PNG)
        assert content_type == "image/png"
        loaded = Image.open(io.BytesIO(data))
        assert loaded.format == "PNG"

    def test_convert_to_tiff(self, service: FormatOptimizer, sample_image: Image.Image) -> None:
        """Should convert to TIFF format."""
        data, content_type = service._convert_to_format(sample_image, OutputFormat.TIFF, dpi=300)
        assert content_type == "image/tiff"
        loaded = Image.open(io.BytesIO(data))
        assert loaded.format == "TIFF"

    def test_convert_rgba_to_jpeg(self, service: FormatOptimizer) -> None:
        """Should convert RGBA to RGB for JPEG."""
        rgba_image = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        data, content_type = service._convert_to_format(rgba_image, OutputFormat.JPEG)
        assert content_type == "image/jpeg"
        loaded = Image.open(io.BytesIO(data))
        assert loaded.mode == "RGB"


class TestGenerateKey:
    """Test storage key generation."""

    def test_key_format(self, service: FormatOptimizer) -> None:
        """Should generate key with correct format."""
        key = service._generate_key("SKU-123", "web", "webp")
        assert key.startswith("enhanced/SKU-123/")
        assert key.endswith("_web.webp")

    def test_key_contains_timestamp(self, service: FormatOptimizer) -> None:
        """Key should contain timestamp component."""
        key = service._generate_key("SKU-123", "thumb", "webp")
        # Format: enhanced/{product_id}/{timestamp}_{variant_name}.{ext}
        parts = key.split("/")
        assert len(parts) == 3
        filename = parts[-1]
        assert "_" in filename


class TestOptimize:
    """Test the main optimize method."""

    @pytest.mark.asyncio
    async def test_optimize_generates_web_variant(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should generate WebP web variant."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=False,
                generate_social=False,
                generate_print=False,
            )

        assert result.web_variant is not None
        assert result.web_variant.format == OutputFormat.WEBP

    @pytest.mark.asyncio
    async def test_optimize_generates_fallback(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should generate JPEG fallback."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=False,
                generate_social=False,
                generate_print=False,
            )

        fallback = next((v for v in result.variants if v.name == "fallback"), None)
        assert fallback is not None
        assert fallback.format == OutputFormat.JPEG

    @pytest.mark.asyncio
    async def test_optimize_generates_thumbnails(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should generate thumbnail variants when requested."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=True,
                generate_social=False,
                generate_print=False,
            )

        thumb_names = [v.name for v in result.variants if v.name.startswith("thumb_")]
        assert len(thumb_names) == len(THUMBNAIL_SIZES)

    @pytest.mark.asyncio
    async def test_optimize_generates_social_variants(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should generate social media variants when requested."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=False,
                generate_social=True,
                generate_print=False,
            )

        social_names = {v.name for v in result.variants}
        for social_name in SOCIAL_VARIANTS:
            assert social_name in social_names

    @pytest.mark.asyncio
    async def test_optimize_generates_print_variant(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should generate print-ready TIFF when requested."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=False,
                generate_social=False,
                generate_print=True,
            )

        assert result.print_variant is not None
        assert result.print_variant.dpi == PRINT_DPI

    @pytest.mark.asyncio
    async def test_optimize_download_failure(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should raise error on download failure."""
        with (
            patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download,
            pytest.raises(FormatOptimizationError),
        ):
            mock_download.side_effect = Exception("Download failed")
            await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
            )

    @pytest.mark.asyncio
    async def test_optimize_calculates_total_size(
        self, service: FormatOptimizer, mock_r2_client: MagicMock
    ) -> None:
        """Should calculate total size of all variants."""
        with patch.object(service, "_download_image", new_callable=AsyncMock) as mock_download:
            mock_download.return_value = Image.new("RGB", (800, 600))

            result = await service.optimize(
                "https://example.com/product.jpg",
                "SKU-123",
                generate_thumbnails=True,
                generate_social=True,
                generate_print=True,
            )

        expected_total = sum(v.size_bytes for v in result.variants)
        assert result.total_size_bytes == expected_total


class TestConstants:
    """Test module constants."""

    def test_webp_quality_reasonable(self) -> None:
        """WebP quality should be reasonable."""
        assert 70 <= WEBP_QUALITY <= 95

    def test_jpeg_quality_reasonable(self) -> None:
        """JPEG quality should be reasonable."""
        assert 70 <= JPEG_QUALITY <= 95

    def test_print_dpi_standard(self) -> None:
        """Print DPI should be standard value."""
        assert PRINT_DPI == 300

    def test_thumbnail_sizes_defined(self) -> None:
        """Thumbnail sizes should be defined."""
        assert len(THUMBNAIL_SIZES) >= 3
        for size in THUMBNAIL_SIZES:
            assert isinstance(size, tuple)
            assert len(size) == 2

    def test_social_variants_defined(self) -> None:
        """Social media variants should be defined."""
        assert "instagram_square" in SOCIAL_VARIANTS
        assert "pinterest" in SOCIAL_VARIANTS
