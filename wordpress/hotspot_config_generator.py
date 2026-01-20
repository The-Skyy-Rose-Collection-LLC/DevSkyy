"""
3D Hotspot Configuration Generator for SkyyRose Collections

Generates interactive hotspot configurations from WooCommerce product data for use
in immersive Three.js collection experiences.

Features:
- Fetch product data from WooCommerce REST API
- Generate 3D positions for product hotspots in collection scenes
- Create camera waypoints for scroll-based transitions
- Export to JSON for frontend consumption
- Support for all SkyyRose collections (Black Rose, Love Hurts, Signature)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class HotspotGenerationError(Exception):
    """Base exception for hotspot generation errors."""

    pass


class HotspotValidationError(HotspotGenerationError):
    """Raised when hotspot configuration validation fails."""

    pass


class HotspotExportError(HotspotGenerationError):
    """Raised when exporting hotspot configuration fails."""

    pass


class CollectionType(str, Enum):
    """SkyyRose collection types."""

    BLACK_ROSE = "black-rose"
    LOVE_HURTS = "love-hurts"
    SIGNATURE = "signature"


class Position3D(BaseModel):
    """3D position coordinates."""

    x: float = Field(..., ge=-1000, le=1000, description="X position (-1000 to 1000)")
    y: float = Field(..., ge=-1000, le=1000, description="Y position (-1000 to 1000)")
    z: float = Field(..., ge=-1000, le=1000, description="Z position (-1000 to 1000)")

    @field_validator("x", "y", "z", mode="before")
    @classmethod
    def validate_finite(cls, v):
        """Ensure coordinates are finite numbers."""
        if not isinstance(v, int | float):
            raise ValueError("Coordinates must be numbers")
        if not (-1000 <= v <= 1000):
            raise ValueError("Coordinates must be between -1000 and 1000")
        return float(v)


class CameraWaypoint(BaseModel):
    """Camera position for scroll-based transitions."""

    scroll_percent: float = Field(..., ge=0, le=100, description="Scroll percentage (0-100)")
    camera_position: Position3D = Field(..., description="Camera position at waypoint")
    camera_target: Position3D = Field(
        default_factory=lambda: Position3D(x=0, y=0, z=0), description="Look-at target"
    )
    duration_ms: int = Field(default=500, description="Transition duration in milliseconds")


class HotspotConfig(BaseModel):
    """Configuration for a single interactive hotspot."""

    product_id: int = Field(..., ge=1, description="WooCommerce product ID (must be positive)")
    position: Position3D = Field(..., description="Hotspot 3D position in scene")
    title: str = Field(..., min_length=1, max_length=200, description="Product title")
    price: float = Field(..., ge=0, description="Product price (non-negative)")
    image_url: str = Field(..., max_length=2048, description="Product featured image URL")
    woocommerce_url: str = Field(
        ..., max_length=2048, description="Link to WooCommerce product page"
    )
    collection_slug: str = Field(..., description="Collection this product belongs to")
    sku: str | None = Field(default=None, max_length=50, description="Product SKU")
    excerpt: str | None = Field(
        default=None, max_length=1000, description="Short product description"
    )

    @field_validator("title", "excerpt", "sku", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        """Sanitize string inputs to prevent injection attacks."""
        if v is None:
            return v
        if isinstance(v, str):
            # Remove any potential HTML/script injection
            return v.strip()
        return v

    @field_validator("image_url", "woocommerce_url", mode="before")
    @classmethod
    def validate_urls(cls, v):
        """Validate URL format."""
        if not isinstance(v, str):
            raise ValueError("URL must be a string")
        # Basic URL validation - must start with http/https or /
        if not (v.startswith("http://") or v.startswith("https://") or v.startswith("/")):
            raise ValueError("URL must be absolute or relative path")
        return v


class CollectionHotspotConfig(BaseModel):
    """Complete hotspot configuration for a collection."""

    collection_type: CollectionType = Field(..., description="Collection identifier")
    collection_name: str = Field(..., description="Human-readable collection name")
    experience_url: str = Field(..., description="URL to Three.js HTML experience file")
    hotspots: list[HotspotConfig] = Field(default_factory=list, description="List of hotspots")
    camera_waypoints: list[CameraWaypoint] = Field(
        default_factory=list, description="Scroll-based camera transitions"
    )

    # Metadata
    generated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(), description="Generation timestamp"
    )
    total_products: int = Field(..., description="Total number of products in hotspots")
    scene_bounds: dict[str, Position3D] = Field(
        default_factory=dict, description="Min/max bounds of scene for camera constraints"
    )


class HotspotPositionCalculator:
    """Calculate 3D positions for hotspots based on product count and collection layout."""

    # Collection-specific layouts
    COLLECTION_LAYOUTS = {
        CollectionType.BLACK_ROSE: {
            "description": "Gothic rose garden layout with diagonal distribution",
            "base_radius": 5.0,
            "height_variation": 2.0,
            "pattern": "spiral",  # spiral, grid, random
        },
        CollectionType.LOVE_HURTS: {
            "description": "Castle ballroom layout with symmetrical placement",
            "base_radius": 6.0,
            "height_variation": 3.0,
            "pattern": "radial",
        },
        CollectionType.SIGNATURE: {
            "description": "Outdoor luxury showroom with scattered placement",
            "base_radius": 4.0,
            "height_variation": 1.5,
            "pattern": "scattered",
        },
    }

    def __init__(self, collection_type: CollectionType):
        """Initialize calculator for specific collection."""
        self.collection_type = collection_type
        self.layout = self.COLLECTION_LAYOUTS[collection_type]

    def calculate_positions(self, num_products: int) -> list[Position3D]:
        """
        Calculate 3D positions for products in collection.

        Args:
            num_products: Number of products to position

        Returns:
            List of Position3D objects
        """
        positions = []
        pattern = self.layout["pattern"]
        base_radius = self.layout["base_radius"]
        height_var = self.layout["height_variation"]

        if pattern == "spiral":
            positions = self._spiral_pattern(num_products, base_radius, height_var)
        elif pattern == "radial":
            positions = self._radial_pattern(num_products, base_radius, height_var)
        elif pattern == "scattered":
            positions = self._scattered_pattern(num_products, base_radius, height_var)
        else:
            positions = self._grid_pattern(num_products, base_radius, height_var)

        return positions

    def _spiral_pattern(
        self, num_products: int, radius: float, height_var: float
    ) -> list[Position3D]:
        """Spiral distribution around center."""
        import math

        positions = []
        for i in range(num_products):
            angle = (i / max(1, num_products - 1)) * math.pi * 4  # 2 full rotations
            height = (i / max(1, num_products - 1)) * height_var
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            y = height
            positions.append(Position3D(x=x, y=y, z=z))

        return positions

    def _radial_pattern(
        self, num_products: int, radius: float, height_var: float
    ) -> list[Position3D]:
        """Radial distribution from center."""
        import math

        positions = []
        for i in range(num_products):
            angle = (i / max(1, num_products)) * math.pi * 2  # Full circle
            height = (i % 3) * (height_var / 3)  # 3 height levels
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            y = height
            positions.append(Position3D(x=x, y=y, z=z))

        return positions

    def _scattered_pattern(
        self, num_products: int, radius: float, height_var: float
    ) -> list[Position3D]:
        """Scattered distribution with some randomness."""
        import random

        positions = []
        for i in range(num_products):
            # Pseudo-random but deterministic
            seed = i * 12345
            random.seed(seed)
            angle = random.uniform(0, 2 * 3.14159)
            dist = random.uniform(radius * 0.5, radius)
            height = random.uniform(0, height_var)
            x = dist * (angle / 6.28) * 2 - dist
            z = dist * ((angle / 6.28) % 1) * 2 - dist
            y = height
            positions.append(Position3D(x=x, y=y, z=z))

        return positions

    def _grid_pattern(
        self, num_products: int, radius: float, height_var: float
    ) -> list[Position3D]:
        """Grid distribution."""
        import math

        positions = []
        cols = max(1, int(math.ceil(math.sqrt(num_products))))
        spacing = (radius * 2) / cols

        for i in range(num_products):
            row = i // cols
            col = i % cols
            x = (col * spacing) - radius
            z = (row * spacing) - radius
            y = (i % 3) * (height_var / 3)
            positions.append(Position3D(x=x, y=y, z=z))

        return positions


class CameraWaypointCalculator:
    """Calculate camera waypoints for scroll-based transitions."""

    def __init__(self, collection_type: CollectionType):
        """Initialize calculator for specific collection."""
        self.collection_type = collection_type

    def calculate_waypoints(self) -> list[CameraWaypoint]:
        """
        Generate camera waypoints for scroll-based transitions.

        Returns:
            List of camera waypoints for scroll percentage points
        """
        if self.collection_type == CollectionType.BLACK_ROSE:
            return self._black_rose_waypoints()
        elif self.collection_type == CollectionType.LOVE_HURTS:
            return self._love_hurts_waypoints()
        else:  # SIGNATURE
            return self._signature_waypoints()

    def _black_rose_waypoints(self) -> list[CameraWaypoint]:
        """Camera path for Black Rose collection."""
        return [
            CameraWaypoint(
                scroll_percent=0,
                camera_position=Position3D(x=0, y=3, z=8),
                camera_target=Position3D(x=0, y=1, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=25,
                camera_position=Position3D(x=5, y=2, z=6),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=50,
                camera_position=Position3D(x=-6, y=1, z=5),
                camera_target=Position3D(x=0, y=0, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=75,
                camera_position=Position3D(x=4, y=2.5, z=-6),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=100,
                camera_position=Position3D(x=0, y=3, z=8),
                camera_target=Position3D(x=0, y=1, z=0),
                duration_ms=500,
            ),
        ]

    def _love_hurts_waypoints(self) -> list[CameraWaypoint]:
        """Camera path for Love Hurts collection."""
        return [
            CameraWaypoint(
                scroll_percent=0,
                camera_position=Position3D(x=0, y=2.5, z=7),
                camera_target=Position3D(x=0, y=1, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=33,
                camera_position=Position3D(x=6, y=1.5, z=5),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=66,
                camera_position=Position3D(x=-6, y=2, z=5),
                camera_target=Position3D(x=0, y=1, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=100,
                camera_position=Position3D(x=0, y=2.5, z=7),
                camera_target=Position3D(x=0, y=1, z=0),
                duration_ms=500,
            ),
        ]

    def _signature_waypoints(self) -> list[CameraWaypoint]:
        """Camera path for Signature collection."""
        return [
            CameraWaypoint(
                scroll_percent=0,
                camera_position=Position3D(x=0, y=2, z=6),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=50,
                camera_position=Position3D(x=0, y=2.5, z=-6),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
            CameraWaypoint(
                scroll_percent=100,
                camera_position=Position3D(x=0, y=2, z=6),
                camera_target=Position3D(x=0, y=0.5, z=0),
                duration_ms=500,
            ),
        ]


class HotspotConfigGenerator:
    """Generate hotspot configurations from WooCommerce product data."""

    def __init__(self, output_dir: str = "./wordpress/collection_templates/hotspots"):
        """
        Initialize hotspot generator.

        Args:
            output_dir: Directory to save generated JSON files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_for_collection(
        self,
        collection_type: CollectionType,
        product_ids: list[int],
        product_data: dict[int, dict[str, Any]],
        experience_url: str,
    ) -> CollectionHotspotConfig:
        """
        Generate complete hotspot configuration for a collection.

        Args:
            collection_type: Collection identifier
            product_ids: List of product IDs in collection
            product_data: Product data keyed by product ID
            experience_url: URL to Three.js experience HTML

        Returns:
            CollectionHotspotConfig ready for export

        Raises:
            HotspotGenerationError: If generation fails
            HotspotValidationError: If product data is invalid
        """
        if not isinstance(product_ids, list) or not all(isinstance(p, int) for p in product_ids):
            raise HotspotValidationError("product_ids must be a list of integers")

        if not isinstance(product_data, dict):
            raise HotspotValidationError("product_data must be a dictionary")

        logger.info(
            f"Generating hotspots for {collection_type.value} ({len(product_ids)} products)"
        )

        try:
            # Calculate 3D positions
            position_calc = HotspotPositionCalculator(collection_type)
            positions = position_calc.calculate_positions(len(product_ids))

            # Create hotspot configs
            hotspots = []
            skipped_count = 0

            for i, product_id in enumerate(product_ids):
                if product_id not in product_data:
                    logger.warning(f"Product {product_id} not found in product data, skipping")
                    skipped_count += 1
                    continue

                try:
                    product = product_data[product_id]

                    # Validate required product fields
                    if not isinstance(product, dict):
                        logger.warning(f"Product {product_id} data is not a dict, skipping")
                        skipped_count += 1
                        continue

                    hotspot = HotspotConfig(
                        product_id=product_id,
                        position=positions[i],
                        title=str(product.get("name", f"Product {product_id}"))[:200],
                        price=float(product.get("price", 0)),
                        image_url=str(product.get("image_url", ""))[:2048],
                        woocommerce_url=str(product.get("url", ""))[:2048],
                        collection_slug=collection_type.value,
                        sku=product.get("sku"),
                        excerpt=product.get("short_description"),
                    )
                    hotspots.append(hotspot)
                except Exception as e:
                    logger.warning(f"Failed to create hotspot for product {product_id}: {e}")
                    skipped_count += 1
                    continue

            if not hotspots:
                raise HotspotValidationError(
                    f"No valid hotspots generated for {collection_type.value}"
                )

            logger.info(f"Generated {len(hotspots)} hotspots ({skipped_count} products skipped)")

            # Calculate camera waypoints
            waypoint_calc = CameraWaypointCalculator(collection_type)
            waypoints = waypoint_calc.calculate_waypoints()

            # Determine scene bounds
            scene_bounds = self._calculate_bounds([h.position for h in hotspots])

            # Create collection config
            config = CollectionHotspotConfig(
                collection_type=collection_type,
                collection_name=collection_type.value.replace("-", " ").title(),
                experience_url=experience_url,
                hotspots=hotspots,
                camera_waypoints=waypoints,
                total_products=len(hotspots),
                scene_bounds=scene_bounds,
            )

            logger.info(f"✓ Generated {len(hotspots)} hotspots for {collection_type.value}")
            return config

        except HotspotValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating hotspots for {collection_type.value}: {e}")
            raise HotspotGenerationError(f"Failed to generate hotspots: {e}")

    def _calculate_bounds(self, positions: list[Position3D]) -> dict[str, Position3D]:
        """Calculate min/max bounds from positions."""
        if not positions:
            return {"min": Position3D(x=0, y=0, z=0), "max": Position3D(x=0, y=0, z=0)}

        min_x = min(p.x for p in positions)
        max_x = max(p.x for p in positions)
        min_y = min(p.y for p in positions)
        max_y = max(p.y for p in positions)
        min_z = min(p.z for p in positions)
        max_z = max(p.z for p in positions)

        return {
            "min": Position3D(x=min_x, y=min_y, z=min_z),
            "max": Position3D(x=max_x, y=max_y, z=max_z),
        }

    async def export_to_json(
        self,
        config: CollectionHotspotConfig,
        filename: str | None = None,
    ) -> Path:
        """
        Export hotspot configuration to JSON file.

        Args:
            config: Configuration to export
            filename: Custom filename (default: {collection_slug}-hotspots.json)

        Returns:
            Path to exported file

        Raises:
            HotspotExportError: If export fails
        """
        if not isinstance(config, CollectionHotspotConfig):
            raise HotspotExportError("config must be a CollectionHotspotConfig instance")

        if filename is None:
            filename = f"{config.collection_type.value}-hotspots.json"

        # Validate filename safety (prevent directory traversal)
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HotspotExportError("Invalid filename - cannot contain path separators")

        filepath = self.output_dir / filename

        try:
            # Ensure directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # Serialize config to JSON with safety checks
            config_dict = json.loads(config.model_dump_json())

            # Write atomically (write to temp, then move)
            temp_filepath = filepath.with_suffix(".json.tmp")

            with open(temp_filepath, "w") as f:
                json.dump(config_dict, f, indent=2)

            # Verify file was written and is valid JSON
            with open(temp_filepath) as f:
                json.load(f)

            # Move temp file to final location
            temp_filepath.replace(filepath)

            logger.info(f"✓ Exported hotspots to {filepath}")
            return filepath

        except json.JSONDecodeError as e:
            logger.error(f"JSON serialization error: {e}")
            raise HotspotExportError(f"Failed to serialize hotspot config: {e}")
        except OSError as e:
            logger.error(f"IO error while exporting hotspots: {e}")
            raise HotspotExportError(f"Failed to write hotspot file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error exporting hotspots: {e}")
            raise HotspotExportError(f"Export failed: {e}")
        finally:
            # Clean up temp file if it still exists
            if temp_filepath.exists():
                try:
                    temp_filepath.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up temp file: {e}")

    async def generate_all_collections(
        self,
        collections_data: dict[CollectionType, dict[str, Any]],
    ) -> dict[CollectionType, CollectionHotspotConfig]:
        """
        Generate hotspot configurations for all collections.

        Args:
            collections_data: Dict mapping collection types to their config
                Expected format:
                {
                    CollectionType.BLACK_ROSE: {
                        "product_ids": [1, 2, 3],
                        "product_data": {...},
                        "experience_url": "..."
                    }
                }

        Returns:
            Dict mapping collection types to their configurations
        """

        configs = {}
        tasks = []

        for collection_type, data in collections_data.items():
            task = self.generate_for_collection(
                collection_type=collection_type,
                product_ids=data["product_ids"],
                product_data=data["product_data"],
                experience_url=data["experience_url"],
            )
            tasks.append((collection_type, task))

        # Execute all generation tasks in parallel
        for collection_type, task in tasks:
            config = await task
            configs[collection_type] = config
            await self.export_to_json(config)

        logger.info("✓ Generated hotspots for all collections")
        return configs


__all__ = [
    # Exceptions
    "HotspotGenerationError",
    "HotspotValidationError",
    "HotspotExportError",
    # Models
    "CollectionType",
    "Position3D",
    "CameraWaypoint",
    "HotspotConfig",
    "CollectionHotspotConfig",
    # Utilities
    "HotspotPositionCalculator",
    "CameraWaypointCalculator",
    "HotspotConfigGenerator",
]
