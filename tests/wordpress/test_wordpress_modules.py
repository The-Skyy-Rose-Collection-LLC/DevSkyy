"""
Comprehensive Unit Tests for WordPress Modules

Tests for:
1. hotspot_config_generator.py - 3D Hotspot Configuration Generator
2. page_builders/about_builder.py - About Page Builder
3. page_builders/home_builder.py - Home Page Builder
4. preorder_manager.py - Pre-Order Management System

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import os
import pytest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

# Import modules under test
from wordpress.hotspot_config_generator import (
    CameraWaypoint,
    CameraWaypointCalculator,
    CollectionHotspotConfig,
    CollectionType,
    HotspotConfig,
    HotspotConfigGenerator,
    HotspotExportError,
    HotspotGenerationError,
    HotspotPositionCalculator,
    HotspotValidationError,
    Position3D,
)
from wordpress.preorder_manager import (
    CountdownConfig,
    PreOrderError,
    PreOrderKlaviyoError,
    PreOrderManager,
    PreOrderMetadata,
    PreOrderNotification,
    PreOrderValidationError,
    PreOrderWordPressError,
    get_server_time,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def sample_product_data() -> dict[int, dict[str, Any]]:
    """Sample product data for testing."""
    return {
        1: {
            "name": "Black Rose Hoodie",
            "price": "149.99",
            "image_url": "https://skyyrose.com/images/hoodie.jpg",
            "url": "https://skyyrose.com/product/black-rose-hoodie",
            "sku": "BR-001",
            "short_description": "Luxurious black hoodie",
        },
        2: {
            "name": "Love Hurts Jacket",
            "price": "299.99",
            "image_url": "https://skyyrose.com/images/jacket.jpg",
            "url": "https://skyyrose.com/product/love-hurts-jacket",
            "sku": "LH-001",
            "short_description": "Bold statement jacket",
        },
        3: {
            "name": "Signature Tee",
            "price": "79.99",
            "image_url": "https://skyyrose.com/images/tee.jpg",
            "url": "https://skyyrose.com/product/signature-tee",
            "sku": "SG-001",
            "short_description": "Essential premium tee",
        },
    }


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create temporary output directory for testing."""
    output_dir = tmp_path / "hotspots"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_wordpress_response() -> dict[str, Any]:
    """Mock WordPress API response for product data."""
    return {
        "id": 123,
        "name": "Test Product",
        "regular_price": "99.99",
        "meta_data": [
            {"key": "_preorder_enabled", "value": "yes"},
            {"key": "_preorder_status", "value": "blooming_soon"},
            {"key": "_preorder_launch_date", "value": "2025-06-01T00:00:00+00:00"},
            {"key": "_preorder_ar_enabled", "value": "yes"},
            {"key": "_preorder_collection", "value": "signature"},
            {"key": "_preorder_early_access_list", "value": "list123"},
        ],
    }


# =============================================================================
# TESTS: Position3D Model
# =============================================================================


class TestPosition3D:
    """Tests for Position3D Pydantic model."""

    def test_valid_position(self) -> None:
        """Test creating a valid Position3D."""
        pos = Position3D(x=1.0, y=2.0, z=3.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.z == 3.0

    def test_position_from_int(self) -> None:
        """Test Position3D accepts integers and converts to float."""
        pos = Position3D(x=1, y=2, z=3)
        assert isinstance(pos.x, float)
        assert pos.x == 1.0

    def test_position_boundary_values(self) -> None:
        """Test Position3D at boundary values."""
        pos = Position3D(x=-1000, y=0, z=1000)
        assert pos.x == -1000.0
        assert pos.z == 1000.0

    def test_position_out_of_range(self) -> None:
        """Test Position3D rejects out-of-range values."""
        with pytest.raises(ValueError):
            Position3D(x=1001, y=0, z=0)

        with pytest.raises(ValueError):
            Position3D(x=0, y=-1001, z=0)

    def test_position_invalid_type(self) -> None:
        """Test Position3D rejects non-numeric values."""
        with pytest.raises(ValueError):
            Position3D(x="not a number", y=0, z=0)  # type: ignore


# =============================================================================
# TESTS: CameraWaypoint Model
# =============================================================================


class TestCameraWaypoint:
    """Tests for CameraWaypoint Pydantic model."""

    def test_valid_waypoint(self) -> None:
        """Test creating a valid CameraWaypoint."""
        waypoint = CameraWaypoint(
            scroll_percent=50.0,
            camera_position=Position3D(x=0, y=5, z=10),
            camera_target=Position3D(x=0, y=0, z=0),
            duration_ms=500,
        )
        assert waypoint.scroll_percent == 50.0
        assert waypoint.camera_position.y == 5.0
        assert waypoint.duration_ms == 500

    def test_waypoint_default_target(self) -> None:
        """Test CameraWaypoint uses default target when not specified."""
        waypoint = CameraWaypoint(
            scroll_percent=0, camera_position=Position3D(x=0, y=0, z=5)
        )
        assert waypoint.camera_target.x == 0
        assert waypoint.camera_target.y == 0
        assert waypoint.camera_target.z == 0

    def test_waypoint_scroll_percent_bounds(self) -> None:
        """Test scroll_percent must be 0-100."""
        with pytest.raises(ValueError):
            CameraWaypoint(
                scroll_percent=-1, camera_position=Position3D(x=0, y=0, z=0)
            )

        with pytest.raises(ValueError):
            CameraWaypoint(
                scroll_percent=101, camera_position=Position3D(x=0, y=0, z=0)
            )


# =============================================================================
# TESTS: HotspotConfig Model
# =============================================================================


class TestHotspotConfig:
    """Tests for HotspotConfig Pydantic model."""

    def test_valid_hotspot_config(self) -> None:
        """Test creating a valid HotspotConfig."""
        config = HotspotConfig(
            product_id=1,
            position=Position3D(x=0, y=1, z=2),
            title="Test Product",
            price=99.99,
            image_url="https://example.com/image.jpg",
            woocommerce_url="https://example.com/product/1",
            collection_slug="black-rose",
        )
        assert config.product_id == 1
        assert config.title == "Test Product"
        assert config.price == 99.99

    def test_hotspot_config_with_optional_fields(self) -> None:
        """Test HotspotConfig with optional fields."""
        config = HotspotConfig(
            product_id=2,
            position=Position3D(x=0, y=0, z=0),
            title="Product",
            price=50.0,
            image_url="/images/product.jpg",
            woocommerce_url="/product/2",
            collection_slug="signature",
            sku="SKU-001",
            excerpt="A great product",
        )
        assert config.sku == "SKU-001"
        assert config.excerpt == "A great product"

    def test_hotspot_config_invalid_product_id(self) -> None:
        """Test HotspotConfig rejects non-positive product_id."""
        with pytest.raises(ValueError):
            HotspotConfig(
                product_id=0,
                position=Position3D(x=0, y=0, z=0),
                title="Test",
                price=10.0,
                image_url="https://example.com/img.jpg",
                woocommerce_url="https://example.com/product",
                collection_slug="test",
            )

    def test_hotspot_config_invalid_url(self) -> None:
        """Test HotspotConfig rejects invalid URLs."""
        with pytest.raises(ValueError):
            HotspotConfig(
                product_id=1,
                position=Position3D(x=0, y=0, z=0),
                title="Test",
                price=10.0,
                image_url="not-a-valid-url",
                woocommerce_url="https://example.com/product",
                collection_slug="test",
            )

    def test_hotspot_config_relative_url(self) -> None:
        """Test HotspotConfig accepts relative URLs."""
        config = HotspotConfig(
            product_id=1,
            position=Position3D(x=0, y=0, z=0),
            title="Test",
            price=10.0,
            image_url="/images/product.jpg",
            woocommerce_url="/product/1",
            collection_slug="test",
        )
        assert config.image_url == "/images/product.jpg"

    def test_hotspot_config_string_sanitization(self) -> None:
        """Test HotspotConfig sanitizes strings."""
        config = HotspotConfig(
            product_id=1,
            position=Position3D(x=0, y=0, z=0),
            title="  Test Product  ",
            price=10.0,
            image_url="https://example.com/img.jpg",
            woocommerce_url="https://example.com/product",
            collection_slug="test",
        )
        assert config.title == "Test Product"


# =============================================================================
# TESTS: HotspotPositionCalculator
# =============================================================================


class TestHotspotPositionCalculator:
    """Tests for HotspotPositionCalculator."""

    def test_spiral_pattern_positions(self) -> None:
        """Test spiral pattern generates correct number of positions."""
        calculator = HotspotPositionCalculator(CollectionType.BLACK_ROSE)
        positions = calculator.calculate_positions(5)
        assert len(positions) == 5
        assert all(isinstance(p, Position3D) for p in positions)

    def test_radial_pattern_positions(self) -> None:
        """Test radial pattern for Love Hurts collection."""
        calculator = HotspotPositionCalculator(CollectionType.LOVE_HURTS)
        positions = calculator.calculate_positions(6)
        assert len(positions) == 6

    def test_scattered_pattern_positions(self) -> None:
        """Test scattered pattern for Signature collection."""
        calculator = HotspotPositionCalculator(CollectionType.SIGNATURE)
        positions = calculator.calculate_positions(4)
        assert len(positions) == 4

    def test_positions_deterministic(self) -> None:
        """Test positions are deterministic for same input."""
        calculator = HotspotPositionCalculator(CollectionType.BLACK_ROSE)
        positions1 = calculator.calculate_positions(3)
        positions2 = calculator.calculate_positions(3)
        for p1, p2 in zip(positions1, positions2):
            assert p1.x == p2.x
            assert p1.y == p2.y
            assert p1.z == p2.z

    def test_zero_products(self) -> None:
        """Test handling of zero products."""
        calculator = HotspotPositionCalculator(CollectionType.SIGNATURE)
        positions = calculator.calculate_positions(0)
        assert positions == []

    def test_single_product(self) -> None:
        """Test single product placement."""
        calculator = HotspotPositionCalculator(CollectionType.BLACK_ROSE)
        positions = calculator.calculate_positions(1)
        assert len(positions) == 1


# =============================================================================
# TESTS: CameraWaypointCalculator
# =============================================================================


class TestCameraWaypointCalculator:
    """Tests for CameraWaypointCalculator."""

    def test_black_rose_waypoints(self) -> None:
        """Test Black Rose collection camera waypoints."""
        calculator = CameraWaypointCalculator(CollectionType.BLACK_ROSE)
        waypoints = calculator.calculate_waypoints()
        assert len(waypoints) == 5
        assert waypoints[0].scroll_percent == 0
        assert waypoints[-1].scroll_percent == 100

    def test_love_hurts_waypoints(self) -> None:
        """Test Love Hurts collection camera waypoints."""
        calculator = CameraWaypointCalculator(CollectionType.LOVE_HURTS)
        waypoints = calculator.calculate_waypoints()
        assert len(waypoints) == 4
        assert all(isinstance(w, CameraWaypoint) for w in waypoints)

    def test_signature_waypoints(self) -> None:
        """Test Signature collection camera waypoints."""
        calculator = CameraWaypointCalculator(CollectionType.SIGNATURE)
        waypoints = calculator.calculate_waypoints()
        assert len(waypoints) == 3

    def test_waypoints_have_valid_durations(self) -> None:
        """Test all waypoints have positive durations."""
        for collection in CollectionType:
            calculator = CameraWaypointCalculator(collection)
            waypoints = calculator.calculate_waypoints()
            assert all(w.duration_ms > 0 for w in waypoints)


# =============================================================================
# TESTS: HotspotConfigGenerator
# =============================================================================


class TestHotspotConfigGenerator:
    """Tests for HotspotConfigGenerator."""

    @pytest.mark.asyncio
    async def test_generate_for_collection_success(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test successful hotspot generation for a collection."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        config = await generator.generate_for_collection(
            collection_type=CollectionType.BLACK_ROSE,
            product_ids=[1, 2, 3],
            product_data=sample_product_data,
            experience_url="/experiences/black-rose.html",
        )

        assert isinstance(config, CollectionHotspotConfig)
        assert config.collection_type == CollectionType.BLACK_ROSE
        assert len(config.hotspots) == 3
        assert config.total_products == 3

    @pytest.mark.asyncio
    async def test_generate_for_collection_missing_products(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test generation skips missing products."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        config = await generator.generate_for_collection(
            collection_type=CollectionType.LOVE_HURTS,
            product_ids=[1, 99, 2],  # 99 doesn't exist
            product_data=sample_product_data,
            experience_url="/experiences/love-hurts.html",
        )

        assert len(config.hotspots) == 2
        assert config.total_products == 2

    @pytest.mark.asyncio
    async def test_generate_for_collection_invalid_product_ids(
        self, temp_output_dir: Path
    ) -> None:
        """Test generation fails with invalid product_ids type."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        with pytest.raises(HotspotValidationError):
            await generator.generate_for_collection(
                collection_type=CollectionType.SIGNATURE,
                product_ids="not a list",  # type: ignore
                product_data={},
                experience_url="/test.html",
            )

    @pytest.mark.asyncio
    async def test_generate_for_collection_invalid_product_data(
        self, temp_output_dir: Path
    ) -> None:
        """Test generation fails with invalid product_data type."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        with pytest.raises(HotspotValidationError):
            await generator.generate_for_collection(
                collection_type=CollectionType.SIGNATURE,
                product_ids=[1],
                product_data="not a dict",  # type: ignore
                experience_url="/test.html",
            )

    @pytest.mark.asyncio
    async def test_generate_for_collection_no_valid_hotspots(
        self, temp_output_dir: Path
    ) -> None:
        """Test generation fails when no valid hotspots generated."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        with pytest.raises(HotspotValidationError):
            await generator.generate_for_collection(
                collection_type=CollectionType.BLACK_ROSE,
                product_ids=[99, 100],  # Non-existent products
                product_data={},
                experience_url="/test.html",
            )

    @pytest.mark.asyncio
    async def test_export_to_json_success(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test successful JSON export."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        config = await generator.generate_for_collection(
            collection_type=CollectionType.SIGNATURE,
            product_ids=[1, 2],
            product_data=sample_product_data,
            experience_url="/experiences/signature.html",
        )

        filepath = await generator.export_to_json(config)
        assert filepath.exists()
        assert filepath.suffix == ".json"

        # Verify JSON is valid
        with open(filepath) as f:
            data = json.load(f)
        assert data["collection_type"] == "signature"
        assert len(data["hotspots"]) == 2

    @pytest.mark.asyncio
    async def test_export_to_json_custom_filename(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test JSON export with custom filename."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        config = await generator.generate_for_collection(
            collection_type=CollectionType.SIGNATURE,
            product_ids=[1],
            product_data=sample_product_data,
            experience_url="/test.html",
        )

        filepath = await generator.export_to_json(config, filename="custom-hotspots.json")
        assert filepath.name == "custom-hotspots.json"

    @pytest.mark.asyncio
    async def test_export_to_json_invalid_filename(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test JSON export rejects unsafe filenames."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        config = await generator.generate_for_collection(
            collection_type=CollectionType.SIGNATURE,
            product_ids=[1],
            product_data=sample_product_data,
            experience_url="/test.html",
        )

        with pytest.raises(HotspotExportError):
            await generator.export_to_json(config, filename="../../../etc/passwd")

        with pytest.raises(HotspotExportError):
            await generator.export_to_json(config, filename="subdir/file.json")

    @pytest.mark.asyncio
    async def test_export_to_json_invalid_config(self, temp_output_dir: Path) -> None:
        """Test JSON export fails with invalid config type."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        with pytest.raises(HotspotExportError):
            await generator.export_to_json("not a config")  # type: ignore

    def test_calculate_bounds(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test scene bounds calculation."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        positions = [
            Position3D(x=-5, y=0, z=-5),
            Position3D(x=5, y=3, z=5),
            Position3D(x=0, y=1, z=0),
        ]
        bounds = generator._calculate_bounds(positions)

        assert bounds["min"].x == -5
        assert bounds["max"].x == 5
        assert bounds["min"].y == 0
        assert bounds["max"].y == 3

    def test_calculate_bounds_empty(self, temp_output_dir: Path) -> None:
        """Test bounds calculation with empty positions."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))
        bounds = generator._calculate_bounds([])

        assert bounds["min"].x == 0
        assert bounds["max"].x == 0

    @pytest.mark.asyncio
    async def test_generate_all_collections(
        self, sample_product_data: dict[int, dict[str, Any]], temp_output_dir: Path
    ) -> None:
        """Test generating hotspots for all collections."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        collections_data = {
            CollectionType.BLACK_ROSE: {
                "product_ids": [1],
                "product_data": sample_product_data,
                "experience_url": "/black-rose.html",
            },
            CollectionType.LOVE_HURTS: {
                "product_ids": [2],
                "product_data": sample_product_data,
                "experience_url": "/love-hurts.html",
            },
        }

        configs = await generator.generate_all_collections(collections_data)

        assert len(configs) == 2
        assert CollectionType.BLACK_ROSE in configs
        assert CollectionType.LOVE_HURTS in configs


# =============================================================================
# TESTS: PreOrderMetadata Model
# =============================================================================


class TestPreOrderMetadata:
    """Tests for PreOrderMetadata Pydantic model."""

    def test_valid_preorder_metadata(self) -> None:
        """Test creating valid PreOrderMetadata."""
        metadata = PreOrderMetadata(
            product_id=123,
            enabled=True,
            status="blooming_soon",
            launch_date=datetime.now(UTC) + timedelta(days=7),
            collection="signature",
        )
        assert metadata.product_id == 123
        assert metadata.enabled is True
        assert metadata.status == "blooming_soon"

    def test_preorder_metadata_defaults(self) -> None:
        """Test PreOrderMetadata default values."""
        metadata = PreOrderMetadata(product_id=1)
        assert metadata.enabled is False
        assert metadata.status == "blooming_soon"
        assert metadata.ar_enabled is True
        assert metadata.notify_count == 0

    def test_preorder_metadata_launch_date_from_string(self) -> None:
        """Test launch_date parsing from ISO string."""
        metadata = PreOrderMetadata(
            product_id=1, launch_date="2025-06-01T12:00:00+00:00"
        )
        assert isinstance(metadata.launch_date, datetime)
        assert metadata.launch_date.tzinfo is not None

    def test_preorder_metadata_invalid_launch_date(self) -> None:
        """Test launch_date validation with invalid format."""
        with pytest.raises(ValueError):
            PreOrderMetadata(product_id=1, launch_date="not a date")

    def test_preorder_metadata_invalid_product_id(self) -> None:
        """Test product_id must be positive."""
        with pytest.raises(ValueError):
            PreOrderMetadata(product_id=0)


# =============================================================================
# TESTS: CountdownConfig Model
# =============================================================================


class TestCountdownConfig:
    """Tests for CountdownConfig Pydantic model."""

    def test_valid_countdown_config(self) -> None:
        """Test creating valid CountdownConfig."""
        config = CountdownConfig(
            product_id=123,
            launch_date_iso="2025-06-01T00:00:00Z",
            launch_date_unix=1748736000,
            server_time_unix=1705708800,
            status="blooming_soon",
            ar_enabled=True,
            collection="signature",
            time_remaining_seconds=86400,
        )
        assert config.product_id == 123
        assert config.status == "blooming_soon"

    def test_countdown_config_invalid_status(self) -> None:
        """Test CountdownConfig rejects invalid status."""
        with pytest.raises(ValueError):
            CountdownConfig(
                product_id=1,
                launch_date_iso="2025-06-01T00:00:00Z",
                launch_date_unix=1748736000,
                server_time_unix=1705708800,
                status="invalid_status",  # Not a valid status
            )


# =============================================================================
# TESTS: PreOrderNotification Model
# =============================================================================


class TestPreOrderNotification:
    """Tests for PreOrderNotification Pydantic model."""

    def test_valid_notification(self) -> None:
        """Test creating valid PreOrderNotification."""
        notification = PreOrderNotification(
            product_id=123,
            product_name="Test Product",
            launch_date=datetime.now(UTC),
            preview_image_url="https://example.com/image.jpg",
            collection="signature",
        )
        assert notification.product_id == 123
        assert notification.product_name == "Test Product"

    def test_notification_invalid_image_url(self) -> None:
        """Test PreOrderNotification rejects invalid image URL."""
        with pytest.raises(ValueError):
            PreOrderNotification(
                product_id=1,
                product_name="Test",
                launch_date=datetime.now(UTC),
                preview_image_url="ftp://invalid-scheme.com/img.jpg",
            )


# =============================================================================
# TESTS: PreOrderManager
# =============================================================================


class TestPreOrderManager:
    """Tests for PreOrderManager."""

    def test_init_valid_config(self) -> None:
        """Test PreOrderManager initialization with valid config."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )
        assert manager.wordpress_url == "https://skyyrose.com"

    def test_init_invalid_url(self) -> None:
        """Test PreOrderManager rejects invalid WordPress URL."""
        with pytest.raises(PreOrderValidationError):
            PreOrderManager(
                wordpress_url="ftp://invalid-scheme.com",
                app_password="valid-password",
            )

    def test_init_invalid_password(self) -> None:
        """Test PreOrderManager rejects short password."""
        with pytest.raises(PreOrderValidationError):
            PreOrderManager(
                wordpress_url="https://skyyrose.com",
                app_password="short",  # Too short
            )

    def test_init_strips_trailing_slash(self) -> None:
        """Test WordPress URL trailing slash is stripped."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com/",
            app_password="valid-password-123",
        )
        assert manager.wordpress_url == "https://skyyrose.com"

    @pytest.mark.asyncio
    async def test_set_preorder_status_success(self) -> None:
        """Test setting pre-order status successfully."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        with patch.object(manager, "_update_product_metadata", new_callable=AsyncMock):
            metadata = await manager.set_preorder_status(
                product_id=123,
                status="blooming_soon",
                launch_date=datetime.now(UTC) + timedelta(days=7),
                collection="signature",
            )

        assert metadata.product_id == 123
        assert metadata.status == "blooming_soon"
        assert metadata.enabled is True

    @pytest.mark.asyncio
    async def test_set_preorder_status_available(self) -> None:
        """Test setting status to available disables pre-order."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        with patch.object(manager, "_update_product_metadata", new_callable=AsyncMock):
            metadata = await manager.set_preorder_status(
                product_id=123,
                status="available",
            )

        assert metadata.enabled is False

    @pytest.mark.asyncio
    async def test_set_preorder_status_blooming_soon_requires_date(self) -> None:
        """Test blooming_soon status requires launch_date."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        with pytest.raises(PreOrderValidationError):
            await manager.set_preorder_status(
                product_id=123,
                status="blooming_soon",
                # Missing launch_date
            )

    @pytest.mark.asyncio
    async def test_get_countdown_config_success(
        self, mock_wordpress_response: dict[str, Any]
    ) -> None:
        """Test getting countdown configuration."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        with patch.object(
            manager,
            "_fetch_product_metadata",
            new_callable=AsyncMock,
            return_value={
                "_preorder_enabled": "yes",
                "_preorder_status": "blooming_soon",
                "_preorder_launch_date": "2025-06-01T00:00:00+00:00",
                "_preorder_ar_enabled": "yes",
                "_preorder_collection": "signature",
            },
        ):
            countdown = await manager.get_countdown_config(123)

        assert countdown.product_id == 123
        assert countdown.status == "blooming_soon"
        assert countdown.ar_enabled is True

    @pytest.mark.asyncio
    async def test_get_countdown_config_not_preorder(self) -> None:
        """Test error when product is not on pre-order."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        with patch.object(
            manager,
            "_fetch_product_metadata",
            new_callable=AsyncMock,
            return_value={"_preorder_enabled": "no"},
        ):
            with pytest.raises(PreOrderWordPressError):
                await manager.get_countdown_config(123)

    @pytest.mark.asyncio
    async def test_notify_early_access_list_no_klaviyo(self) -> None:
        """Test notification skips when Klaviyo not configured."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
            klaviyo_api_key=None,
        )

        result = await manager.notify_early_access_list(123)
        assert result["sent"] == 0
        assert "not configured" in result["message"]

    @pytest.mark.asyncio
    async def test_notify_early_access_list_no_list_configured(self) -> None:
        """Test notification returns 0 when no early access list."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
            klaviyo_api_key="test-klaviyo-key",
        )

        with patch.object(
            manager,
            "_fetch_product_data",
            new_callable=AsyncMock,
            return_value={"name": "Test Product"},
        ), patch.object(
            manager,
            "_fetch_product_metadata",
            new_callable=AsyncMock,
            return_value={
                "_preorder_launch_date": "2025-06-01T00:00:00+00:00",
                "_preorder_collection": "signature",
                # No _preorder_early_access_list
            },
        ):
            result = await manager.notify_early_access_list(123)

        assert result["sent"] == 0
        assert "No early access list" in result["message"]

    @pytest.mark.asyncio
    async def test_fetch_product_data_success(
        self, mock_wordpress_response: dict[str, Any]
    ) -> None:
        """Test fetching product data from WordPress."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        # Create mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_wordpress_response)

        # Create mock context manager for the response
        mock_response_cm = MagicMock()
        mock_response_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response_cm.__aexit__ = AsyncMock(return_value=None)

        # Create mock session with get method
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response_cm)

        # Create mock context manager for the session
        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("wordpress.preorder_manager.aiohttp.ClientSession", return_value=mock_session_cm):
            data = await manager._fetch_product_data(123)

        assert data["id"] == 123
        assert data["name"] == "Test Product"

    @pytest.mark.asyncio
    async def test_fetch_product_data_not_found(self) -> None:
        """Test error when product not found."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        # Create mock response for 404
        mock_response = MagicMock()
        mock_response.status = 404

        # Create mock context manager for the response
        mock_response_cm = MagicMock()
        mock_response_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response_cm.__aexit__ = AsyncMock(return_value=None)

        # Create mock session with get method
        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_response_cm)

        # Create mock context manager for the session
        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("wordpress.preorder_manager.aiohttp.ClientSession", return_value=mock_session_cm):
            with pytest.raises(PreOrderWordPressError):
                await manager._fetch_product_data(999)

    @pytest.mark.asyncio
    async def test_update_product_metadata(self) -> None:
        """Test updating product metadata in WordPress."""
        manager = PreOrderManager(
            wordpress_url="https://skyyrose.com",
            app_password="valid-password-123",
        )

        metadata = PreOrderMetadata(
            product_id=123,
            enabled=True,
            status="blooming_soon",
            launch_date=datetime.now(UTC),
            collection="signature",
        )

        # Create mock response for successful update
        mock_response = MagicMock()
        mock_response.status = 200

        # Create mock context manager for the response
        mock_response_cm = MagicMock()
        mock_response_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response_cm.__aexit__ = AsyncMock(return_value=None)

        # Create mock session with post method
        mock_session = MagicMock()
        mock_session.post = MagicMock(return_value=mock_response_cm)

        # Create mock context manager for the session
        mock_session_cm = MagicMock()
        mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_cm.__aexit__ = AsyncMock(return_value=None)

        with patch("wordpress.preorder_manager.aiohttp.ClientSession", return_value=mock_session_cm):
            await manager._update_product_metadata(123, metadata)
            # No exception means success


# =============================================================================
# TESTS: get_server_time Function
# =============================================================================


class TestGetServerTime:
    """Tests for get_server_time utility function."""

    @pytest.mark.asyncio
    async def test_get_server_time(self) -> None:
        """Test server time returns valid timestamps."""
        result = await get_server_time()
        assert "timestamp" in result
        assert "milliseconds" in result
        assert result["milliseconds"] > result["timestamp"]
        assert result["timestamp"] > 0


# =============================================================================
# TESTS: Page Builders (About and Home)
# =============================================================================


class TestAboutPageBuilder:
    """Tests for AboutPageBuilder."""

    def test_init_with_default_config(self) -> None:
        """Test AboutPageBuilder initializes with default config."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        assert builder.brand is not None
        assert builder.brand.name == "SkyyRose"

    def test_build_parallax_hero(self) -> None:
        """Test parallax hero section generation."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        widgets = builder.build_parallax_hero()

        assert len(widgets) > 0
        assert any("Where Love Meets Luxury" in str(w) for w in widgets)

    def test_build_brand_narrative(self) -> None:
        """Test brand narrative section generation."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        widgets = builder.build_brand_narrative()

        assert len(widgets) > 0
        # Should have headings for each section
        headings = [w for w in widgets if w.get("widgetType") == "heading"]
        assert len(headings) >= 3  # Our Origin Story, The Collections, Our Commitment

    def test_build_press_timeline(self) -> None:
        """Test press timeline section generation."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        widgets = builder.build_press_timeline()

        assert len(widgets) > 0
        # Should include timeline widgets
        timeline_widgets = [
            w for w in widgets if w.get("widgetType") == "skyyrose-timeline"
        ]
        assert len(timeline_widgets) <= 3  # Limit of 3 featured press

    def test_build_impact_metrics(self) -> None:
        """Test impact metrics section generation."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        widgets = builder.build_impact_metrics()

        assert len(widgets) > 0
        # Should include icon boxes for metrics
        icon_boxes = [w for w in widgets if w.get("widgetType") == "icon-box"]
        assert len(icon_boxes) == 4  # 4 metrics

    def test_generate_full_template(self) -> None:
        """Test full about page template generation."""
        from wordpress.page_builders.about_builder import AboutPageBuilder

        builder = AboutPageBuilder()
        template = builder.generate()

        assert template.title == "About SkyyRose"
        assert len(template.content) >= 5  # 5 sections
        assert template.page_settings.get("hide_title") == "yes"


class TestHomePageBuilder:
    """Tests for HomePageBuilder."""

    def test_init_with_default_config(self) -> None:
        """Test HomePageBuilder initializes with default config."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        assert builder.brand is not None

    def test_build_spinning_logo_section(self) -> None:
        """Test spinning logo section generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        widgets = builder.build_spinning_logo_section()

        assert len(widgets) > 0
        # Should include Lottie animation
        lottie = [w for w in widgets if w.get("widgetType") == "skyyrose-lottie"]
        assert len(lottie) == 1

    def test_build_spinning_logo_custom_url(self) -> None:
        """Test spinning logo with custom URL."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        custom_url = "/custom/logo.json"
        widgets = builder.build_spinning_logo_section(logo_json_url=custom_url)

        lottie = [w for w in widgets if w.get("widgetType") == "skyyrose-lottie"][0]
        assert lottie["settings"]["lottie_url"] == custom_url

    def test_build_3d_background_section(self) -> None:
        """Test 3D background section generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        widgets = builder.build_3d_background_section()

        assert len(widgets) > 0
        threejs = [
            w for w in widgets if w.get("widgetType") == "skyyrose-3d-background"
        ]
        assert len(threejs) == 1

    def test_build_featured_collections_grid(self) -> None:
        """Test featured collections grid generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        widgets = builder.build_featured_collections_grid()

        assert len(widgets) > 0
        # Should include collection cards
        cards = [w for w in widgets if w.get("widgetType") == "skyyrose-collection-card"]
        assert len(cards) == 3  # BLACK ROSE, LOVE HURTS, SIGNATURE

    def test_build_brand_statement(self) -> None:
        """Test brand statement section generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        widgets = builder.build_brand_statement()

        assert len(widgets) > 0
        # Should include heading and buttons
        buttons = [w for w in widgets if w.get("widgetType") == "button"]
        assert len(buttons) == 2  # Shop Now, Read Our Story

    def test_build_newsletter_section(self) -> None:
        """Test newsletter section generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        widgets = builder.build_newsletter_section()

        assert len(widgets) > 0
        # Should include form
        forms = [w for w in widgets if w.get("widgetType") == "form"]
        assert len(forms) == 1

    def test_generate_full_template(self) -> None:
        """Test full home page template generation."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        template = builder.generate()

        assert template.title == "Home"
        assert len(template.content) >= 4  # 4 sections
        assert template.page_settings.get("hide_title") == "yes"
        assert template.page_settings.get("template") == "elementor_canvas"

    def test_generate_with_custom_title(self) -> None:
        """Test template generation with custom hero title."""
        from wordpress.page_builders.home_builder import HomePageBuilder

        builder = HomePageBuilder()
        template = builder.generate(hero_title="Custom Title")

        # Template should still be generated successfully
        assert template is not None
        assert template.title == "Home"


# =============================================================================
# TESTS: Integration / Edge Cases
# =============================================================================


class TestIntegration:
    """Integration and edge case tests."""

    @pytest.mark.asyncio
    async def test_hotspot_generation_with_invalid_product_data(
        self, temp_output_dir: Path
    ) -> None:
        """Test hotspot generation handles invalid product data gracefully."""
        generator = HotspotConfigGenerator(output_dir=str(temp_output_dir))

        product_data = {
            1: {
                "name": "Valid Product",
                "price": "99.99",
                "image_url": "https://example.com/img.jpg",
                "url": "https://example.com/product/1",
            },
            2: "not a dict",  # Invalid
            3: {
                "name": "Another Valid",
                "price": "49.99",
                "image_url": "https://example.com/img2.jpg",
                "url": "https://example.com/product/3",
            },
        }

        config = await generator.generate_for_collection(
            collection_type=CollectionType.BLACK_ROSE,
            product_ids=[1, 2, 3],
            product_data=product_data,  # type: ignore
            experience_url="/test.html",
        )

        # Should skip invalid product and continue
        assert len(config.hotspots) == 2

    def test_collection_type_enum_values(self) -> None:
        """Test CollectionType enum has expected values."""
        assert CollectionType.BLACK_ROSE.value == "black-rose"
        assert CollectionType.LOVE_HURTS.value == "love-hurts"
        assert CollectionType.SIGNATURE.value == "signature"

    def test_preorder_status_literals(self) -> None:
        """Test PreOrderMetadata accepts all valid status literals."""
        for status in ["blooming_soon", "now_blooming", "available"]:
            metadata = PreOrderMetadata(product_id=1, status=status)  # type: ignore
            assert metadata.status == status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
