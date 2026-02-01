"""
Product Training Dataset Module
================================

Bridge between WooCommerce products and LoRA training datasets.

This module fetches products from WooCommerce, downloads their images,
evaluates quality, and prepares them for LoRA fine-tuning with proper
captions based on SkyyRose brand DNA.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from PIL import Image
from sync.woocommerce_sync import Product, WooCommerceSyncClient

from imagery.lora_trainer import TrainingDataset, TrainingImage
from orchestration.brand_context import COLLECTION_CONTEXT

logger = logging.getLogger(__name__)

__all__ = [
    "ProductTrainingSource",
    "ProductTrainingDataset",
    "fetch_products_from_woocommerce",
    "download_product_images",
    "prepare_training_dataset",
]


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class ProductTrainingSource:
    """Product information for LoRA training.

    Represents a WooCommerce product with its images and metadata,
    ready for inclusion in a training dataset.
    """

    product_id: int
    sku: str
    name: str
    collection: str  # BLACK_ROSE, LOVE_HURTS, SIGNATURE
    garment_type: str = ""
    image_urls: list[str] = field(default_factory=list)
    local_image_paths: list[Path] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0


@dataclass
class ProductTrainingDataset(TrainingDataset):
    """Extended training dataset with product tracking.

    Extends the base TrainingDataset with WooCommerce product
    metadata for version tracking and monitoring.
    """

    products: list[ProductTrainingSource] = field(default_factory=list)
    collection_filter: str | None = None
    woocommerce_sync_timestamp: datetime = field(default_factory=datetime.now)
    version: str = "v1.0.0"


# =============================================================================
# Product Fetching
# =============================================================================


async def fetch_products_from_woocommerce(
    collections: list[str] | None = None,
    max_products: int | None = None,
    min_images: int = 2,
    woocommerce_url: str | None = None,
    consumer_key: str | None = None,
    consumer_secret: str | None = None,
) -> list[ProductTrainingSource]:
    """Fetch products from WooCommerce filtered by collection.

    Args:
        collections: Filter by collection tags (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
        max_products: Maximum number of products to fetch
        min_images: Minimum number of images required per product
        woocommerce_url: WordPress URL (uses env var if None)
        consumer_key: WooCommerce consumer key (uses env var if None)
        consumer_secret: WooCommerce consumer secret (uses env var if None)

    Returns:
        List of ProductTrainingSource objects

    Raises:
        ValueError: If WooCommerce credentials are missing
        httpx.HTTPError: If API request fails
    """
    logger.info(
        "Fetching products from WooCommerce",
        extra={
            "collections": collections,
            "max_products": max_products,
            "min_images": min_images,
        },
    )

    # Initialize WooCommerce client
    client = WooCommerceSyncClient(
        url=woocommerce_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
    )

    # Fetch products with pagination
    all_products: list[Product] = []
    page = 1
    per_page = 100

    while True:
        try:
            # Get products page
            products = await client.get_products(
                page=page,
                per_page=per_page,
                status="publish",
            )

            if not products:
                break

            all_products.extend(products)

            # Check if we have enough
            if max_products and len(all_products) >= max_products:
                all_products = all_products[:max_products]
                break

            page += 1

        except Exception as e:
            logger.error(f"Error fetching products page {page}: {e}")
            break

    logger.info(f"Fetched {len(all_products)} products from WooCommerce")

    # Filter and convert to ProductTrainingSource
    training_sources: list[ProductTrainingSource] = []

    for product in all_products:
        # Extract collection from tags or categories
        collection = _extract_collection(product)

        # Filter by collection if specified
        if collections and collection not in collections:
            continue

        # Filter by minimum images
        if len(product.images) < min_images:
            logger.debug(f"Skipping product {product.sku}: only {len(product.images)} images")
            continue

        # Extract garment type from name or categories
        garment_type = _extract_garment_type(product)

        # Get image URLs
        image_urls = [img.src for img in product.images if img.src]

        # Create training source
        training_source = ProductTrainingSource(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            collection=collection,
            garment_type=garment_type,
            image_urls=image_urls,
            metadata={
                "description": product.description,
                "short_description": product.short_description,
                "price": product.price,
                "categories": [cat.name for cat in product.categories],
                "attributes": [{attr.name: attr.options} for attr in product.attributes],
            },
        )

        training_sources.append(training_source)

    logger.info(
        f"Prepared {len(training_sources)} products for training",
        extra={"collections": collections},
    )

    return training_sources


def _extract_collection(product: Product) -> str:
    """Extract collection from product tags or categories.

    Args:
        product: WooCommerce product

    Returns:
        Collection name (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
        Defaults to SIGNATURE if not found
    """
    # Check categories
    for category in product.categories:
        category_upper = category.name.upper().replace(" ", "_")
        if category_upper in COLLECTION_CONTEXT:
            return category_upper

    # Check tags (if available)
    if hasattr(product, "tags"):
        for tag in product.tags:
            tag_upper = tag.name.upper().replace(" ", "_")
            if tag_upper in COLLECTION_CONTEXT:
                return tag_upper

    # Default to SIGNATURE
    return "SIGNATURE"


def _extract_garment_type(product: Product) -> str:
    """Extract garment type from product name or attributes.

    Args:
        product: WooCommerce product

    Returns:
        Garment type (hoodie, tee, shorts, etc.)
    """
    name_lower = product.name.lower()

    garment_types = {
        "hoodie": ["hoodie", "hood"],
        "tee": ["tee", "t-shirt", "shirt"],
        "shorts": ["shorts", "short"],
        "sherpa": ["sherpa", "jacket"],
        "dress": ["dress"],
        "bomber": ["bomber"],
        "windbreaker": ["windbreaker", "jacket"],
        "joggers": ["joggers", "jogger", "pants"],
        "beanie": ["beanie", "hat"],
    }

    for garment, keywords in garment_types.items():
        if any(keyword in name_lower for keyword in keywords):
            return garment

    return "apparel"  # Generic fallback


# =============================================================================
# Image Download & Caching
# =============================================================================


async def download_product_images(
    products: list[ProductTrainingSource],
    cache_dir: Path = Path("assets/woocommerce-cache"),
    force_refresh: bool = False,
) -> list[ProductTrainingSource]:
    """Download and cache product images locally.

    Args:
        products: List of ProductTrainingSource objects
        cache_dir: Directory for cached images
        force_refresh: If True, re-download even if cached

    Returns:
        Updated products with local_image_paths populated
    """
    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        f"Downloading images for {len(products)} products",
        extra={"cache_dir": str(cache_dir), "force_refresh": force_refresh},
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        for product in products:
            collection_dir = cache_dir / product.collection.lower()
            sku_dir = collection_dir / product.sku
            sku_dir.mkdir(parents=True, exist_ok=True)

            local_paths: list[Path] = []

            for idx, image_url in enumerate(product.image_urls):
                # Generate cache filename from URL hash
                url_hash = hashlib.md5(image_url.encode()).hexdigest()[:12]
                extension = Path(image_url).suffix or ".jpg"
                cache_path = sku_dir / f"image_{idx}_{url_hash}{extension}"

                # Check cache
                if cache_path.exists() and not force_refresh:
                    logger.debug(f"Using cached image: {cache_path}")
                    local_paths.append(cache_path)
                    continue

                # Download image
                try:
                    logger.debug(f"Downloading: {image_url}")
                    response = await client.get(image_url)
                    response.raise_for_status()

                    # Save to cache
                    cache_path.write_bytes(response.content)
                    local_paths.append(cache_path)

                    logger.debug(f"Cached image: {cache_path}")

                except Exception as e:
                    logger.error(f"Failed to download {image_url}: {e}")
                    continue

            product.local_image_paths = local_paths

    logger.info(f"Downloaded {sum(len(p.local_image_paths) for p in products)} images total")

    return products


# =============================================================================
# Quality Evaluation
# =============================================================================


def evaluate_image_quality(image_path: Path) -> float:
    """Evaluate image quality score.

    Args:
        image_path: Path to image file

    Returns:
        Quality score 0.0-1.0 (higher is better)
    """
    try:
        img = Image.open(image_path)

        # Resolution score (target: 1024x1024 or higher)
        width, height = img.size
        resolution_score = min(min(width, height) / 1024.0, 1.0)

        # Blur detection (Laplacian variance)
        import cv2
        import numpy as np

        img_array = np.array(img.convert("L"))
        laplacian_var = cv2.Laplacian(img_array, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 1000.0, 1.0)  # Normalize

        # Brightness check
        brightness = np.mean(img_array) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Penalize extreme

        # Composite score
        quality_score = resolution_score * 0.4 + blur_score * 0.4 + brightness_score * 0.2

        return quality_score

    except Exception as e:
        logger.error(f"Error evaluating {image_path}: {e}")
        return 0.0


async def filter_by_quality(
    products: list[ProductTrainingSource],
    min_quality_score: float = 0.7,
) -> list[ProductTrainingSource]:
    """Filter products by image quality.

    Args:
        products: List of products with local images
        min_quality_score: Minimum acceptable quality (0.0-1.0)

    Returns:
        Filtered products with quality scores updated
    """
    logger.info(f"Filtering {len(products)} products by quality >= {min_quality_score}")

    filtered_products: list[ProductTrainingSource] = []

    for product in products:
        if not product.local_image_paths:
            continue

        # Evaluate each image
        quality_scores = [
            evaluate_image_quality(img_path) for img_path in product.local_image_paths
        ]

        # Use average quality
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        product.quality_score = avg_quality

        if avg_quality >= min_quality_score:
            filtered_products.append(product)
            logger.debug(f"Product {product.sku}: quality {avg_quality:.2f} - PASS")
        else:
            logger.debug(f"Product {product.sku}: quality {avg_quality:.2f} - SKIP")

    logger.info(
        f"Filtered to {len(filtered_products)} products "
        f"(rejected {len(products) - len(filtered_products)})"
    )

    return filtered_products


# =============================================================================
# Dataset Preparation
# =============================================================================


def prepare_training_dataset(
    products: list[ProductTrainingSource],
    collection_filter: str | None = None,
    version: str = "v1.0.0",
) -> ProductTrainingDataset:
    """Prepare final training dataset from products.

    Args:
        products: List of products with images
        collection_filter: Optional collection to track
        version: LoRA version identifier

    Returns:
        ProductTrainingDataset ready for training
    """
    logger.info(
        f"Preparing training dataset from {len(products)} products",
        extra={"collection_filter": collection_filter, "version": version},
    )

    # Generate captions using brand DNA

    training_images: list[TrainingImage] = []

    for product in products:
        for img_path in product.local_image_paths:
            # Generate caption
            caption = _generate_product_caption(
                collection=product.collection,
                garment_type=product.garment_type,
                product_name=product.name,
                sku=product.sku,
            )

            training_image = TrainingImage(
                path=img_path,
                caption=caption,
                collection=product.collection,
                garment_type=product.garment_type,
                quality_score=product.quality_score,
            )

            training_images.append(training_image)

    # Calculate collection stats
    collection_counts: dict[str, int] = {}
    for product in products:
        collection_counts[product.collection] = collection_counts.get(product.collection, 0) + 1

    # Create dataset
    dataset = ProductTrainingDataset(
        images=training_images,
        total_images=len(training_images),
        collections=collection_counts,
        products=products,
        collection_filter=collection_filter,
        woocommerce_sync_timestamp=datetime.now(),
        version=version,
    )

    logger.info(
        f"Dataset prepared: {dataset.total_images} images from {len(products)} products",
        extra={"collections": collection_counts},
    )

    return dataset


def _generate_product_caption(
    collection: str,
    garment_type: str,
    product_name: str,
    sku: str,
) -> str:
    """Generate LoRA training caption for product image.

    Args:
        collection: Collection name (BLACK_ROSE, etc.)
        garment_type: Type of garment (hoodie, tee, etc.)
        product_name: Product name
        sku: Product SKU

    Returns:
        Training caption combining brand DNA, collection, and product info
    """

    collection_context = COLLECTION_CONTEXT.get(collection, {})
    aesthetic = collection_context.get("aesthetic", "luxury streetwear")

    caption_parts = [
        "SkyyRose luxury streetwear",
        aesthetic,
        f"{garment_type}" if garment_type != "apparel" else "",
        f"{product_name}",
        f"SKU: {sku}",
        "professional product photography, 8k, ultra detailed, high quality",
    ]

    caption = ", ".join(part for part in caption_parts if part)

    return caption
