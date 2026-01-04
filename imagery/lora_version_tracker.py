"""
LoRA Version Tracker Module
============================

SQLite-backed version history tracking for SkyyRose LoRA training.

This module tracks:
- Which LoRA versions have been created
- Which products contributed to each version
- Training configuration and metadata
- Version comparison and product history

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

__all__ = [
    "LoRAVersion",
    "ProductContribution",
    "VersionDiff",
    "LoRAVersionTracker",
    "create_version_database",
]


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class ProductContribution:
    """Product contribution to a LoRA version.

    Tracks which products (and how many images) were used in training.
    """

    id: int | None = None
    lora_version_id: int | None = None
    product_id: int = 0
    sku: str = ""
    product_name: str = ""
    collection: str = ""
    images_count: int = 0
    quality_score: float = 0.0


@dataclass
class LoRAVersion:
    """LoRA version metadata.

    Represents a specific trained LoRA model with full provenance tracking.
    """

    id: int | None = None
    version: str = ""
    base_model: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    training_config: dict[str, Any] = field(default_factory=dict)
    model_path: str = ""
    total_images: int = 0
    total_products: int = 0
    collections: dict[str, int] = field(default_factory=dict)
    products: list[ProductContribution] = field(default_factory=list)


@dataclass
class VersionDiff:
    """Comparison between two LoRA versions.

    Shows what changed between versions.
    """

    version_1: str
    version_2: str
    added_products: list[ProductContribution]
    removed_products: list[ProductContribution]
    common_products: list[ProductContribution]
    image_count_diff: int
    product_count_diff: int
    collection_changes: dict[str, tuple[int, int]]  # collection: (v1_count, v2_count)


# =============================================================================
# Database Schema
# =============================================================================

SCHEMA_SQL = """
-- LoRA versions table
CREATE TABLE IF NOT EXISTS lora_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    base_model TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_config TEXT,  -- JSON
    model_path TEXT,
    total_images INTEGER DEFAULT 0,
    total_products INTEGER DEFAULT 0,
    collections TEXT  -- JSON: {"BLACK_ROSE": 10, "SIGNATURE": 5}
);

-- Product contributions table
CREATE TABLE IF NOT EXISTS product_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lora_version_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    sku TEXT NOT NULL,
    product_name TEXT,
    collection TEXT,
    images_count INTEGER DEFAULT 0,
    quality_score REAL DEFAULT 0.0,
    FOREIGN KEY (lora_version_id) REFERENCES lora_versions(id) ON DELETE CASCADE
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_product_contributions_version
    ON product_contributions(lora_version_id);
CREATE INDEX IF NOT EXISTS idx_product_contributions_sku
    ON product_contributions(sku);
CREATE INDEX IF NOT EXISTS idx_product_contributions_collection
    ON product_contributions(collection);
CREATE INDEX IF NOT EXISTS idx_lora_versions_version
    ON lora_versions(version);
CREATE INDEX IF NOT EXISTS idx_lora_versions_created_at
    ON lora_versions(created_at DESC);
"""


# =============================================================================
# Database Initialization
# =============================================================================


async def create_version_database(db_path: Path) -> None:
    """Create SQLite database with schema.

    Args:
        db_path: Path to SQLite database file

    Raises:
        sqlite3.Error: If database creation fails
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()

    logger.info(f"Created version database at {db_path}")


# =============================================================================
# Version Tracker
# =============================================================================


class LoRAVersionTracker:
    """SQLite-backed LoRA version tracker.

    Manages version history, product contributions, and version comparisons.

    Example:
        tracker = LoRAVersionTracker(Path("models/lora-versions.db"))
        await tracker.initialize()

        version = await tracker.create_version(
            version="v1.1.0",
            products=product_list,
            config=training_config,
            model_path="models/skyyrose-luxury-lora",
        )

        history = await tracker.get_product_history("SRS-BR-001")
    """

    def __init__(self, db_path: Path):
        """Initialize version tracker.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    async def initialize(self) -> None:
        """Initialize database schema.

        Creates tables if they don't exist.
        """
        await create_version_database(self.db_path)

    @asynccontextmanager
    async def _get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Get database connection context manager.

        Yields:
            Database connection
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def create_version(
        self,
        version: str,
        products: list[Any],  # list[ProductTrainingSource]
        config: dict[str, Any],
        model_path: str,
        base_model: str = "stabilityai/stable-diffusion-xl-base-1.0",
    ) -> LoRAVersion:
        """Create new LoRA version record.

        Args:
            version: Semantic version string (e.g., "v1.1.0")
            products: List of ProductTrainingSource objects
            config: Training configuration dict
            model_path: Path to saved model
            base_model: Base model identifier

        Returns:
            Created LoRAVersion object

        Raises:
            sqlite3.IntegrityError: If version already exists
        """
        logger.info(f"Creating version record: {version}")

        # Calculate stats
        total_images = sum(len(p.local_image_paths) for p in products)
        total_products = len(products)

        # Calculate collection counts
        collections: dict[str, int] = {}
        for product in products:
            collections[product.collection] = collections.get(product.collection, 0) + 1

        async with self._get_connection() as db:
            # Insert version
            cursor = await db.execute(
                """
                INSERT INTO lora_versions
                (version, base_model, training_config, model_path,
                 total_images, total_products, collections)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    version,
                    base_model,
                    json.dumps(config),
                    str(model_path),
                    total_images,
                    total_products,
                    json.dumps(collections),
                ),
            )

            version_id = cursor.lastrowid

            # Insert product contributions
            for product in products:
                await db.execute(
                    """
                    INSERT INTO product_contributions
                    (lora_version_id, product_id, sku, product_name,
                     collection, images_count, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        version_id,
                        product.product_id,
                        product.sku,
                        product.name,
                        product.collection,
                        len(product.local_image_paths),
                        product.quality_score,
                    ),
                )

            await db.commit()

        logger.info(
            f"Created version {version}: " f"{total_products} products, {total_images} images"
        )

        # Return LoRAVersion object
        return await self.get_version(version)

    async def get_version(self, version: str) -> LoRAVersion:
        """Get LoRA version by version string.

        Args:
            version: Version string (e.g., "v1.1.0")

        Returns:
            LoRAVersion object with products loaded

        Raises:
            ValueError: If version not found
        """
        async with self._get_connection() as db:
            # Get version record
            cursor = await db.execute(
                """
                SELECT * FROM lora_versions WHERE version = ?
                """,
                (version,),
            )

            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Version not found: {version}")

            # Parse row
            version_obj = LoRAVersion(
                id=row["id"],
                version=row["version"],
                base_model=row["base_model"],
                created_at=datetime.fromisoformat(row["created_at"]),
                training_config=json.loads(row["training_config"] or "{}"),
                model_path=row["model_path"],
                total_images=row["total_images"],
                total_products=row["total_products"],
                collections=json.loads(row["collections"] or "{}"),
            )

            # Get product contributions
            cursor = await db.execute(
                """
                SELECT * FROM product_contributions
                WHERE lora_version_id = ?
                ORDER BY collection, sku
                """,
                (version_obj.id,),
            )

            products = []
            async for row in cursor:
                contribution = ProductContribution(
                    id=row["id"],
                    lora_version_id=row["lora_version_id"],
                    product_id=row["product_id"],
                    sku=row["sku"],
                    product_name=row["product_name"],
                    collection=row["collection"],
                    images_count=row["images_count"],
                    quality_score=row["quality_score"],
                )
                products.append(contribution)

            version_obj.products = products

        return version_obj

    async def get_product_history(self, sku: str) -> list[LoRAVersion]:
        """Get all LoRA versions that include a specific product.

        Args:
            sku: Product SKU

        Returns:
            List of LoRAVersion objects, sorted by creation date (newest first)
        """
        logger.info(f"Fetching version history for product: {sku}")

        async with self._get_connection() as db:
            cursor = await db.execute(
                """
                SELECT DISTINCT lv.*
                FROM lora_versions lv
                INNER JOIN product_contributions pc ON lv.id = pc.lora_version_id
                WHERE pc.sku = ?
                ORDER BY lv.created_at DESC
                """,
                (sku,),
            )

            versions = []
            async for row in cursor:
                version_obj = LoRAVersion(
                    id=row["id"],
                    version=row["version"],
                    base_model=row["base_model"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    training_config=json.loads(row["training_config"] or "{}"),
                    model_path=row["model_path"],
                    total_images=row["total_images"],
                    total_products=row["total_products"],
                    collections=json.loads(row["collections"] or "{}"),
                )
                versions.append(version_obj)

        logger.info(f"Found {len(versions)} versions for {sku}")
        return versions

    async def list_versions(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[LoRAVersion]:
        """List all LoRA versions.

        Args:
            limit: Maximum number of versions to return
            offset: Number of versions to skip

        Returns:
            List of LoRAVersion objects (without products loaded for performance)
        """
        async with self._get_connection() as db:
            query = "SELECT * FROM lora_versions ORDER BY created_at DESC"
            params: tuple[Any, ...] = ()

            if limit is not None:
                query += " LIMIT ? OFFSET ?"
                params = (limit, offset)

            cursor = await db.execute(query, params)

            versions = []
            async for row in cursor:
                version_obj = LoRAVersion(
                    id=row["id"],
                    version=row["version"],
                    base_model=row["base_model"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    training_config=json.loads(row["training_config"] or "{}"),
                    model_path=row["model_path"],
                    total_images=row["total_images"],
                    total_products=row["total_products"],
                    collections=json.loads(row["collections"] or "{}"),
                )
                versions.append(version_obj)

        return versions

    async def compare_versions(self, v1: str, v2: str) -> VersionDiff:
        """Compare two LoRA versions.

        Args:
            v1: First version string
            v2: Second version string

        Returns:
            VersionDiff object showing changes

        Raises:
            ValueError: If either version not found
        """
        logger.info(f"Comparing versions: {v1} vs {v2}")

        # Get both versions
        version_1 = await self.get_version(v1)
        version_2 = await self.get_version(v2)

        # Build SKU sets
        v1_skus = {p.sku for p in version_1.products}
        v2_skus = {p.sku for p in version_2.products}

        # Find differences
        added_skus = v2_skus - v1_skus
        removed_skus = v1_skus - v2_skus
        common_skus = v1_skus & v2_skus

        # Build product lists
        added_products = [p for p in version_2.products if p.sku in added_skus]
        removed_products = [p for p in version_1.products if p.sku in removed_skus]
        common_products = [p for p in version_2.products if p.sku in common_skus]

        # Calculate diffs
        image_count_diff = version_2.total_images - version_1.total_images
        product_count_diff = version_2.total_products - version_1.total_products

        # Collection changes
        collection_changes: dict[str, tuple[int, int]] = {}
        all_collections = set(version_1.collections.keys()) | set(version_2.collections.keys())
        for collection in all_collections:
            v1_count = version_1.collections.get(collection, 0)
            v2_count = version_2.collections.get(collection, 0)
            if v1_count != v2_count:
                collection_changes[collection] = (v1_count, v2_count)

        diff = VersionDiff(
            version_1=v1,
            version_2=v2,
            added_products=added_products,
            removed_products=removed_products,
            common_products=common_products,
            image_count_diff=image_count_diff,
            product_count_diff=product_count_diff,
            collection_changes=collection_changes,
        )

        logger.info(
            f"Version diff: +{len(added_products)} products, "
            f"-{len(removed_products)} products, "
            f"{len(common_products)} common"
        )

        return diff

    async def delete_version(self, version: str) -> None:
        """Delete a LoRA version and all product contributions.

        Args:
            version: Version string to delete

        Raises:
            ValueError: If version not found
        """
        logger.warning(f"Deleting version: {version}")

        async with self._get_connection() as db:
            # Check if version exists
            cursor = await db.execute("SELECT id FROM lora_versions WHERE version = ?", (version,))
            row = await cursor.fetchone()
            if not row:
                raise ValueError(f"Version not found: {version}")

            # Delete (CASCADE will delete product_contributions)
            await db.execute("DELETE FROM lora_versions WHERE version = ?", (version,))
            await db.commit()

        logger.info(f"Deleted version: {version}")

    async def get_latest_version(self) -> LoRAVersion | None:
        """Get the most recent LoRA version.

        Returns:
            Latest LoRAVersion or None if no versions exist
        """
        versions = await self.list_versions(limit=1)
        return versions[0] if versions else None

    async def version_exists(self, version: str) -> bool:
        """Check if a version exists.

        Args:
            version: Version string to check

        Returns:
            True if version exists, False otherwise
        """
        async with self._get_connection() as db:
            cursor = await db.execute("SELECT 1 FROM lora_versions WHERE version = ?", (version,))
            row = await cursor.fetchone()
            return row is not None
