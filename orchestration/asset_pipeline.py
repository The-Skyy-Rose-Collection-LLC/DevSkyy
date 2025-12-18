"""
Product Asset Pipeline Orchestrator
====================================

Orchestrates the 3D asset generation pipeline connecting:
- Tripo3D Agent: 3D model generation (GLB, USDZ)
- FASHN Agent: Virtual try-on images
- WordPress Asset Agent: Media upload and product attachment

Usage:
    from orchestration.asset_pipeline import ProductAssetPipeline

    pipeline = ProductAssetPipeline()
    result = await pipeline.process_product(
        product_id="12345",
        title="SkyyRose Signature Hoodie",
        description="Premium heavyweight cotton hoodie",
        images=["path/to/product.jpg"],
        category="apparel",
    )

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field

from agents.fashn_agent import FashnConfig, FashnTryOnAgent, GarmentCategory
from agents.tripo_agent import TripoAssetAgent, TripoConfig
from agents.wordpress_asset_agent import WordPressAssetAgent, WordPressAssetConfig

logger = structlog.get_logger(__name__)

# =============================================================================
# Prometheus Metrics (optional - only if prometheus_client is installed)
# =============================================================================

try:
    from prometheus_client import Counter, Gauge, Histogram

    METRICS_ENABLED = True

    # Counters
    ASSET_GENERATION_TOTAL = Counter(
        "devskyy_asset_generation_total",
        "Total number of asset generation requests",
        ["category", "collection", "status"],
    )
    ASSET_GENERATION_ERRORS = Counter(
        "devskyy_asset_generation_errors_total",
        "Total number of asset generation errors",
        ["stage", "error_type"],
    )

    # Histograms
    ASSET_GENERATION_DURATION = Histogram(
        "devskyy_asset_generation_duration_seconds",
        "Time spent generating assets",
        ["category", "stage"],
        buckets=[1, 5, 10, 30, 60, 120, 300, 600],
    )

    # Gauges
    PIPELINE_ACTIVE = Gauge(
        "devskyy_pipeline_active",
        "Number of active pipeline executions",
    )

except ImportError:
    METRICS_ENABLED = False
    ASSET_GENERATION_TOTAL = None
    ASSET_GENERATION_ERRORS = None
    ASSET_GENERATION_DURATION = None
    PIPELINE_ACTIVE = None


# =============================================================================
# Configuration & Enums
# =============================================================================


class ProductCategory(str, Enum):
    """Product category for pipeline routing."""

    APPAREL = "apparel"  # Clothing - uses both Tripo3D and FASHN
    ACCESSORY = "accessory"  # Bags, jewelry - Tripo3D only
    FOOTWEAR = "footwear"  # Shoes - Tripo3D only


class PipelineStage(str, Enum):
    """Pipeline execution stages."""

    INITIALIZED = "initialized"
    GENERATING_3D = "generating_3d"
    GENERATING_TRYON = "generating_tryon"
    UPLOADING_ASSETS = "uploading_assets"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Asset pipeline configuration."""

    # Agent configs
    tripo_config: TripoConfig = field(default_factory=TripoConfig.from_env)
    fashn_config: FashnConfig = field(default_factory=FashnConfig.from_env)
    wordpress_config: WordPressAssetConfig = field(default_factory=WordPressAssetConfig.from_env)

    # Pipeline settings
    enable_3d_generation: bool = True
    enable_virtual_tryon: bool = True
    enable_wordpress_upload: bool = True

    # Output formats
    output_formats: list[str] = field(default_factory=lambda: ["glb", "usdz"])

    # Model images for try-on (paths to default model images)
    default_model_images: dict[str, str] = field(default_factory=dict)

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 2.0

    @classmethod
    def from_env(cls) -> PipelineConfig:
        """Create config from environment variables."""
        return cls(
            tripo_config=TripoConfig.from_env(),
            fashn_config=FashnConfig.from_env(),
            wordpress_config=WordPressAssetConfig.from_env(),
            enable_3d_generation=os.getenv("PIPELINE_ENABLE_3D", "true").lower() == "true",
            enable_virtual_tryon=os.getenv("PIPELINE_ENABLE_TRYON", "true").lower() == "true",
            enable_wordpress_upload=os.getenv("PIPELINE_ENABLE_WP", "true").lower() == "true",
        )


# =============================================================================
# Models
# =============================================================================


class Asset3DResult(BaseModel):
    """3D model generation result."""

    task_id: str
    model_path: str
    model_url: str | None = None
    format: str
    texture_path: str | None = None
    thumbnail_path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TryOnAssetResult(BaseModel):
    """Virtual try-on result."""

    task_id: str
    image_path: str
    image_url: str | None = None
    model_image: str
    garment_image: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class WordPressAssetResult(BaseModel):
    """WordPress upload result."""

    media_id: int
    url: str
    asset_type: str  # "3d_model", "tryon_image", "thumbnail"
    product_id: int | None = None


class AssetPipelineResult(BaseModel):
    """Complete pipeline execution result."""

    product_id: str
    status: str
    stage: PipelineStage = PipelineStage.INITIALIZED
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    duration_seconds: float = 0.0

    # Generated assets
    assets_3d: list[Asset3DResult] = Field(default_factory=list)
    assets_tryon: list[TryOnAssetResult] = Field(default_factory=list)
    assets_wordpress: list[WordPressAssetResult] = Field(default_factory=list)

    # Errors
    errors: list[dict[str, Any]] = Field(default_factory=list)

    # Summary
    total_assets_generated: int = 0
    total_assets_uploaded: int = 0


# =============================================================================
# Product Asset Pipeline
# =============================================================================


class ProductAssetPipeline:
    """
    Orchestrates the complete 3D asset generation pipeline.

    Coordinates Tripo3D, FASHN, and WordPress agents to:
    1. Generate 3D models from product images/descriptions
    2. Create virtual try-on images for apparel
    3. Upload all assets to WordPress/WooCommerce
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
    ) -> None:
        """Initialize pipeline with configuration."""
        self.config = config or PipelineConfig.from_env()

        # Initialize agents (lazy - created on first use)
        self._tripo_agent: TripoAssetAgent | None = None
        self._fashn_agent: FashnTryOnAgent | None = None
        self._wordpress_agent: WordPressAssetAgent | None = None

        # Ensure output directories exist
        Path(self.config.tripo_config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.fashn_config.output_dir).mkdir(parents=True, exist_ok=True)

    @property
    def tripo_agent(self) -> TripoAssetAgent:
        """Get or create Tripo3D agent."""
        if self._tripo_agent is None:
            self._tripo_agent = TripoAssetAgent(config=self.config.tripo_config)
        return self._tripo_agent

    @property
    def fashn_agent(self) -> FashnTryOnAgent:
        """Get or create FASHN agent."""
        if self._fashn_agent is None:
            self._fashn_agent = FashnTryOnAgent(config=self.config.fashn_config)
        return self._fashn_agent

    @property
    def wordpress_agent(self) -> WordPressAssetAgent:
        """Get or create WordPress agent."""
        if self._wordpress_agent is None:
            self._wordpress_agent = WordPressAssetAgent(config=self.config.wordpress_config)
        return self._wordpress_agent

    async def close(self) -> None:
        """Close all agent sessions."""
        if self._tripo_agent:
            await self._tripo_agent.close()
        if self._fashn_agent:
            await self._fashn_agent.close()
        if self._wordpress_agent:
            await self._wordpress_agent.close()

    async def process_product(
        self,
        product_id: str,
        title: str,
        description: str,
        images: list[str],
        category: str = "apparel",
        collection: str = "SIGNATURE",
        garment_type: str = "tee",
        model_images: list[str] | None = None,
        wp_product_id: int | None = None,
    ) -> AssetPipelineResult:
        """
        Process a product through the complete asset pipeline.

        Args:
            product_id: Unique product identifier
            title: Product title
            description: Product description
            images: List of product image paths
            category: Product category (apparel, accessory, footwear)
            collection: SkyyRose collection (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
            garment_type: Type of garment (hoodie, tee, jacket, etc.)
            model_images: Optional model images for try-on
            wp_product_id: Optional WordPress product ID for attachment

        Returns:
            AssetPipelineResult with all generated assets
        """
        start_time = datetime.now(UTC)
        result = AssetPipelineResult(
            product_id=product_id,
            status="processing",
            stage=PipelineStage.INITIALIZED,
        )

        try:
            product_category = ProductCategory(category.lower())
        except ValueError:
            product_category = ProductCategory.APPAREL

        logger.info(
            "Starting asset pipeline",
            product_id=product_id,
            title=title,
            category=product_category.value,
        )

        # Track active pipelines
        if METRICS_ENABLED and PIPELINE_ACTIVE:
            PIPELINE_ACTIVE.inc()

        try:
            # Stage 1: Generate 3D models
            if self.config.enable_3d_generation and images:
                result.stage = PipelineStage.GENERATING_3D
                await self._generate_3d_models(
                    result=result,
                    title=title,
                    images=images,
                    collection=collection,
                    garment_type=garment_type,
                )

            # Stage 2: Generate virtual try-on (apparel only)
            if (
                self.config.enable_virtual_tryon
                and product_category == ProductCategory.APPAREL
                and images
            ):
                result.stage = PipelineStage.GENERATING_TRYON
                await self._generate_tryon_images(
                    result=result,
                    garment_images=images,
                    model_images=model_images,
                    garment_type=garment_type,
                )

            # Stage 3: Upload to WordPress
            if self.config.enable_wordpress_upload:
                result.stage = PipelineStage.UPLOADING_ASSETS
                await self._upload_to_wordpress(
                    result=result,
                    title=title,
                    wp_product_id=wp_product_id,
                )

            result.stage = PipelineStage.COMPLETED
            result.status = "success"

        except Exception as e:
            logger.error(
                "Pipeline failed",
                product_id=product_id,
                error=str(e),
                stage=result.stage.value,
            )
            result.stage = PipelineStage.FAILED
            result.status = "error"
            result.errors.append({
                "stage": result.stage.value,
                "error": str(e),
                "error_type": type(e).__name__,
            })

            # Record error metrics
            if METRICS_ENABLED and ASSET_GENERATION_ERRORS:
                ASSET_GENERATION_ERRORS.labels(
                    stage=result.stage.value,
                    error_type=type(e).__name__,
                ).inc()

        finally:
            # Decrement active pipelines
            if METRICS_ENABLED and PIPELINE_ACTIVE:
                PIPELINE_ACTIVE.dec()

        # Finalize result
        end_time = datetime.now(UTC)
        result.completed_at = end_time.isoformat()
        result.duration_seconds = (end_time - start_time).total_seconds()
        result.total_assets_generated = len(result.assets_3d) + len(result.assets_tryon)
        result.total_assets_uploaded = len(result.assets_wordpress)

        # Record metrics
        if METRICS_ENABLED:
            if ASSET_GENERATION_TOTAL:
                ASSET_GENERATION_TOTAL.labels(
                    category=product_category.value,
                    collection=collection,
                    status=result.status,
                ).inc()
            if ASSET_GENERATION_DURATION:
                ASSET_GENERATION_DURATION.labels(
                    category=product_category.value,
                    stage="total",
                ).observe(result.duration_seconds)

        logger.info(
            "Pipeline completed",
            product_id=product_id,
            status=result.status,
            duration=result.duration_seconds,
            assets_generated=result.total_assets_generated,
            assets_uploaded=result.total_assets_uploaded,
        )

        return result

    async def _generate_3d_models(
        self,
        result: AssetPipelineResult,
        title: str,
        images: list[str],
        collection: str,
        garment_type: str,
    ) -> None:
        """Generate 3D models using Tripo3D agent."""
        logger.info("Generating 3D models", title=title, image_count=len(images))

        for image_path in images[:1]:  # Use first image for 3D generation
            try:
                # Generate from image
                gen_result = await self.tripo_agent.run({
                    "action": "generate_from_image",
                    "image_path": image_path,
                    "product_name": title,
                    "output_format": "glb",
                })

                if gen_result.get("status") == "success":
                    data = gen_result.get("data", {})
                    result.assets_3d.append(Asset3DResult(
                        task_id=data.get("task_id", ""),
                        model_path=data.get("model_path", ""),
                        model_url=data.get("model_url"),
                        format="glb",
                        texture_path=data.get("texture_path"),
                        thumbnail_path=data.get("thumbnail_path"),
                        metadata={
                            "collection": collection,
                            "garment_type": garment_type,
                            "source_image": image_path,
                        },
                    ))
                else:
                    result.errors.append({
                        "stage": "3d_generation",
                        "error": gen_result.get("error", "Unknown error"),
                        "image": image_path,
                    })

            except Exception as e:
                logger.error("3D generation failed", image=image_path, error=str(e))
                result.errors.append({
                    "stage": "3d_generation",
                    "error": str(e),
                    "image": image_path,
                })

    async def _generate_tryon_images(
        self,
        result: AssetPipelineResult,
        garment_images: list[str],
        model_images: list[str] | None,
        garment_type: str,
    ) -> None:
        """Generate virtual try-on images using FASHN agent."""
        # Use provided model images or defaults
        models = model_images or list(self.config.default_model_images.values())

        if not models:
            logger.warning("No model images available for try-on")
            return

        # Map garment type to FASHN category
        category_map = {
            "hoodie": GarmentCategory.TOPS,
            "tee": GarmentCategory.TOPS,
            "shirt": GarmentCategory.TOPS,
            "jacket": GarmentCategory.OUTERWEAR,
            "coat": GarmentCategory.OUTERWEAR,
            "pants": GarmentCategory.BOTTOMS,
            "shorts": GarmentCategory.BOTTOMS,
            "dress": GarmentCategory.DRESSES,
        }
        category = category_map.get(garment_type.lower(), GarmentCategory.TOPS)

        logger.info(
            "Generating try-on images",
            garment_count=len(garment_images),
            model_count=len(models),
            category=category.value,
        )

        # Generate try-on for each garment/model combination
        for garment_image in garment_images[:1]:  # Limit to first garment
            for model_image in models[:2]:  # Limit to 2 models
                try:
                    tryon_result = await self.fashn_agent.run({
                        "action": "virtual_tryon",
                        "model_image": model_image,
                        "garment_image": garment_image,
                        "category": category.value,
                        "mode": "balanced",
                    })

                    if tryon_result.get("status") == "success":
                        data = tryon_result.get("data", {})
                        # Handle nested result structure
                        if isinstance(data, dict) and "fashn_virtual_tryon" in data:
                            data = data.get("fashn_virtual_tryon", {})

                        result.assets_tryon.append(TryOnAssetResult(
                            task_id=data.get("task_id", ""),
                            image_path=data.get("image_path", ""),
                            image_url=data.get("image_url"),
                            model_image=model_image,
                            garment_image=garment_image,
                            metadata={"category": category.value},
                        ))
                    else:
                        result.errors.append({
                            "stage": "tryon_generation",
                            "error": tryon_result.get("error", "Unknown error"),
                            "garment": garment_image,
                            "model": model_image,
                        })

                except Exception as e:
                    logger.error(
                        "Try-on generation failed",
                        garment=garment_image,
                        model=model_image,
                        error=str(e),
                    )
                    result.errors.append({
                        "stage": "tryon_generation",
                        "error": str(e),
                        "garment": garment_image,
                        "model": model_image,
                    })

    async def _upload_to_wordpress(
        self,
        result: AssetPipelineResult,
        title: str,
        wp_product_id: int | None,
    ) -> None:
        """Upload generated assets to WordPress."""
        logger.info(
            "Uploading assets to WordPress",
            assets_3d=len(result.assets_3d),
            assets_tryon=len(result.assets_tryon),
            product_id=wp_product_id,
        )

        # Upload 3D models
        for asset in result.assets_3d:
            try:
                upload_result = await self.wordpress_agent.upload_3d_model(
                    glb_path=asset.model_path if asset.format == "glb" else None,
                    usdz_path=asset.model_path if asset.format == "usdz" else None,
                    thumbnail_path=asset.thumbnail_path,
                    product_id=wp_product_id,
                    title=f"{title} - 3D Model",
                    alt_text=f"3D model of {title}",
                )

                result.assets_wordpress.append(WordPressAssetResult(
                    media_id=upload_result.get("media_id", 0),
                    url=upload_result.get("glb_url") or upload_result.get("usdz_url") or "",
                    asset_type="3d_model",
                    product_id=wp_product_id,
                ))

            except Exception as e:
                logger.error("3D model upload failed", error=str(e))
                result.errors.append({
                    "stage": "wordpress_upload",
                    "error": str(e),
                    "asset_type": "3d_model",
                })

        # Upload try-on images
        for asset in result.assets_tryon:
            try:
                upload_result = await self.wordpress_agent.run({
                    "action": "upload_media",
                    "file_path": asset.image_path,
                    "title": f"{title} - Virtual Try-On",
                    "alt_text": f"Virtual try-on of {title}",
                })

                if upload_result.get("status") == "success":
                    data = upload_result.get("data", {}).get("upload", {})
                    result.assets_wordpress.append(WordPressAssetResult(
                        media_id=data.get("id", 0),
                        url=data.get("url", ""),
                        asset_type="tryon_image",
                        product_id=wp_product_id,
                    ))

            except Exception as e:
                logger.error("Try-on image upload failed", error=str(e))
                result.errors.append({
                    "stage": "wordpress_upload",
                    "error": str(e),
                    "asset_type": "tryon_image",
                })


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "ProductAssetPipeline",
    "PipelineConfig",
    "AssetPipelineResult",
    "Asset3DResult",
    "TryOnAssetResult",
    "WordPressAssetResult",
    "ProductCategory",
    "PipelineStage",
]
