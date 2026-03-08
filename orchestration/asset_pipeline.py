"""
Product Asset Pipeline Orchestrator
====================================

Orchestrates the 3D asset generation pipeline connecting:
- Tripo3D Agent: 3D model generation (GLB, USDZ)
- FASHN Agent: Virtual try-on images
- WordPress Asset Agent: Media upload and product attachment

Features (v2.0.0 - Stage 4.7.2 Optimizations):
- Batch processing with 5 concurrent operations
- Redis cache layer with 7-day TTL for 3D models
- WebSocket progress tracking with real-time callbacks
- Retry queue for failed operations with exponential backoff

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

    # Batch processing
    results = await pipeline.process_batch(products, progress_callback=my_callback)

Author: DevSkyy Platform Team
Version: 2.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel, Field, ValidationError

from agents.fashn_agent import FashnConfig, FashnTryOnAgent, GarmentCategory
from agents.tripo_agent import TripoAssetAgent, TripoConfig
from agents.wordpress_asset_agent import WordPressAssetAgent, WordPressAssetConfig
from orchestration.huggingface_3d_client import HuggingFace3DClient, HuggingFace3DConfig

logger = structlog.get_logger(__name__)

# =============================================================================
# Redis Cache Layer (Optional - graceful fallback if not available)
# =============================================================================

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False

# Default cache settings
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days
CACHE_KEY_PREFIX = "devskyy:asset_pipeline:"

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


class Primary3DGenerator(str, Enum):
    """Primary 3D generator selection."""

    HUGGINGFACE = "huggingface"  # Use HuggingFace models (recommended for quality)
    TRIPO3D = "tripo3d"  # Use Tripo3D (original behavior)
    HYBRID = "hybrid"  # HuggingFace for hints, Tripo3D for generation


@dataclass
class PipelineConfig:
    """Asset pipeline configuration."""

    # Agent configs
    tripo_config: TripoConfig = field(default_factory=TripoConfig.from_env)
    fashn_config: FashnConfig = field(default_factory=FashnConfig.from_env)
    wordpress_config: WordPressAssetConfig = field(default_factory=WordPressAssetConfig.from_env)
    huggingface_config: HuggingFace3DConfig = field(default_factory=HuggingFace3DConfig.from_env)

    # Primary 3D generator selection (NEW)
    primary_3d_generator: Primary3DGenerator = Primary3DGenerator.HUGGINGFACE

    # Pipeline settings
    enable_huggingface_3d: bool = True  # Stage 0: HF 3D generation
    enable_3d_generation: bool = True  # Stage 1: Tripo3D generation
    enable_virtual_tryon: bool = True  # Stage 2: Virtual try-on
    enable_wordpress_upload: bool = True  # Stage 3: WordPress upload

    # Output formats
    output_formats: list[str] = field(default_factory=lambda: ["glb", "usdz"])

    # Model images for try-on (paths to default model images)
    default_model_images: dict[str, str] = field(default_factory=dict)

    # Retry settings (enhanced with exponential backoff)
    max_retries: int = 3
    retry_delay: float = 2.0
    retry_backoff_multiplier: float = 2.0  # Exponential backoff
    retry_max_delay: float = 60.0  # Max delay cap

    # Batch processing settings (Stage 4.7.2)
    batch_concurrency: int = 5  # Max concurrent operations
    batch_timeout: float = 600.0  # 10 minute timeout per item

    # Redis cache settings (Stage 4.7.2)
    redis_url: str | None = None  # e.g., redis://localhost:6379
    cache_enabled: bool = True
    cache_ttl_seconds: int = CACHE_TTL_SECONDS  # 7 days default

    # Progress tracking (Stage 4.7.2)
    enable_progress_callbacks: bool = True

    @classmethod
    def from_env(cls) -> PipelineConfig:
        """Create config from environment variables."""
        # Parse primary 3D generator from env
        generator_str = os.getenv("PIPELINE_PRIMARY_3D_GENERATOR", "huggingface").lower()
        primary_generator = (
            Primary3DGenerator(generator_str)
            if generator_str in [e.value for e in Primary3DGenerator]
            else Primary3DGenerator.HUGGINGFACE
        )

        return cls(
            tripo_config=TripoConfig.from_env(),
            fashn_config=FashnConfig.from_env(),
            wordpress_config=WordPressAssetConfig.from_env(),
            huggingface_config=HuggingFace3DConfig.from_env(),
            primary_3d_generator=primary_generator,
            enable_huggingface_3d=os.getenv("PIPELINE_ENABLE_HF_3D", "true").lower() == "true",
            enable_3d_generation=os.getenv("PIPELINE_ENABLE_3D", "true").lower() == "true",
            enable_virtual_tryon=os.getenv("PIPELINE_ENABLE_TRYON", "true").lower() == "true",
            enable_wordpress_upload=os.getenv("PIPELINE_ENABLE_WP", "true").lower() == "true",
            batch_concurrency=int(os.getenv("PIPELINE_BATCH_CONCURRENCY", "5")),
            batch_timeout=float(os.getenv("PIPELINE_BATCH_TIMEOUT", "600")),
            redis_url=os.getenv("REDIS_URL"),
            cache_enabled=os.getenv("PIPELINE_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("PIPELINE_CACHE_TTL", str(CACHE_TTL_SECONDS))),
        )


# =============================================================================
# Progress & Callback Types (Stage 4.7.2)
# =============================================================================

# Type alias for progress callbacks
ProgressCallback = Callable[["ProgressEvent"], None]
AsyncProgressCallback = Callable[["ProgressEvent"], "asyncio.coroutine[None]"]


class ProgressEventType(str, Enum):
    """Progress event types for WebSocket tracking."""

    BATCH_STARTED = "batch_started"
    BATCH_COMPLETED = "batch_completed"
    ITEM_STARTED = "item_started"
    ITEM_COMPLETED = "item_completed"
    ITEM_FAILED = "item_failed"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    CACHE_HIT = "cache_hit"
    RETRY_ATTEMPT = "retry_attempt"


class ProgressEvent(BaseModel):
    """Progress event for real-time tracking."""

    event_type: ProgressEventType
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    product_id: str | None = None
    stage: str | None = None
    progress_percent: float = 0.0
    message: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Batch context
    batch_id: str | None = None
    batch_total: int = 0
    batch_completed: int = 0
    batch_failed: int = 0


class RetryQueueItem(BaseModel):
    """Item in the retry queue."""

    product_id: str
    title: str
    description: str
    images: list[str]
    category: str
    collection: str
    garment_type: str
    model_images: list[str] | None = None
    wp_product_id: int | None = None
    retry_count: int = 0
    last_error: str | None = None
    next_retry_at: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class BatchResult(BaseModel):
    """Result of batch processing."""

    batch_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    duration_seconds: float = 0.0
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    cached_items: int = 0
    results: list[AssetPipelineResult] = Field(default_factory=list)
    retry_queue: list[RetryQueueItem] = Field(default_factory=list)


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

    Stage 4.7.2 Features:
    - Batch processing with configurable concurrency (default: 5)
    - Redis cache layer for 3D models (7-day TTL)
    - WebSocket progress tracking with real-time callbacks
    - Retry queue with exponential backoff
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
    ) -> None:
        """Initialize pipeline with configuration."""
        self.config = config or PipelineConfig.from_env()

        # Initialize agents (lazy - created on first use)
        self._huggingface_client: HuggingFace3DClient | None = None
        self._tripo_agent: TripoAssetAgent | None = None
        self._fashn_agent: FashnTryOnAgent | None = None
        self._wordpress_agent: WordPressAssetAgent | None = None

        # Stage 4.7.2: Batch processing semaphore
        self._semaphore = asyncio.Semaphore(self.config.batch_concurrency)

        # Stage 4.7.2: Redis cache client (lazy initialization)
        self._redis: Any | None = None
        self._redis_connected = False

        # Stage 4.7.2: Retry queue
        self._retry_queue: list[RetryQueueItem] = []

        # Stage 4.7.2: Progress callbacks
        self._progress_callbacks: list[ProgressCallback | AsyncProgressCallback] = []

        # Ensure output directories exist
        Path(self.config.tripo_config.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config.fashn_config.output_dir).mkdir(parents=True, exist_ok=True)

    @property
    def huggingface_client(self) -> HuggingFace3DClient:
        """Get or create HuggingFace 3D client."""
        if self._huggingface_client is None:
            self._huggingface_client = HuggingFace3DClient(config=self.config.huggingface_config)
        return self._huggingface_client

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
        """Close all agent sessions and Redis connection.

        Logs any errors encountered during cleanup but does not raise,
        ensuring all resources are attempted to be released.
        """
        errors: list[str] = []

        if self._huggingface_client:
            try:
                await self._huggingface_client.close()
            except Exception as e:
                errors.append(f"HuggingFace client close error: {e}")
                logger.warning("Failed to close HuggingFace client", error=str(e))

        if self._tripo_agent:
            try:
                await self._tripo_agent.close()
            except Exception as e:
                errors.append(f"Tripo agent close error: {e}")
                logger.warning("Failed to close Tripo agent", error=str(e))

        if self._fashn_agent:
            try:
                await self._fashn_agent.close()
            except Exception as e:
                errors.append(f"FASHN agent close error: {e}")
                logger.warning("Failed to close FASHN agent", error=str(e))

        if self._wordpress_agent:
            try:
                await self._wordpress_agent.close()
            except Exception as e:
                errors.append(f"WordPress agent close error: {e}")
                logger.warning("Failed to close WordPress agent", error=str(e))

        # Stage 4.7.2: Close Redis connection
        if self._redis and self._redis_connected:
            try:
                await self._redis.close()
            except ConnectionError as e:
                errors.append(f"Redis connection close error: {e}")
                logger.warning("Redis connection already closed or unreachable", error=str(e))
            except TimeoutError as e:
                errors.append(f"Redis close timeout: {e}")
                logger.warning("Redis close timed out", error=str(e))
            except Exception as e:
                errors.append(f"Redis close error: {e}")
                logger.warning(
                    "Failed to close Redis connection", error=str(e), error_type=type(e).__name__
                )
            finally:
                self._redis_connected = False

        if errors:
            logger.info(
                "Pipeline close completed with errors", error_count=len(errors), errors=errors
            )

    # =========================================================================
    # Stage 4.7.2: Redis Cache Layer
    # =========================================================================

    async def _ensure_redis_connected(self) -> bool:
        """Ensure Redis connection is established.

        Returns:
            True if Redis is connected and operational, False otherwise.

        Note:
            This method distinguishes between transient errors (retry-able)
            and permanent errors (configuration issues) for better diagnostics.
        """
        if not REDIS_AVAILABLE:
            logger.debug("Redis library not available, caching disabled")
            return False

        if not self.config.cache_enabled:
            logger.debug("Redis caching is disabled by configuration")
            return False

        if self._redis_connected:
            return True

        if not self.config.redis_url:
            logger.debug("Redis URL not configured, caching disabled")
            return False

        try:
            self._redis = aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection with timeout
            await asyncio.wait_for(self._redis.ping(), timeout=5.0)
            self._redis_connected = True
            logger.info(
                "Redis cache connected", url=self.config.redis_url.split("@")[-1]
            )  # Log host only, not credentials
            return True
        except TimeoutError:
            logger.warning(
                "Redis connection timed out (transient error, will retry on next request)",
                redis_url=self.config.redis_url.split("@")[-1],
            )
            self._redis_connected = False
            return False
        except ConnectionRefusedError as e:
            logger.warning(
                "Redis connection refused - server may be down",
                error=str(e),
                redis_url=self.config.redis_url.split("@")[-1],
            )
            self._redis_connected = False
            return False
        except OSError as e:
            # Network-level errors (DNS resolution, network unreachable, etc.)
            logger.warning(
                "Redis network error - check connectivity",
                error=str(e),
                error_type=type(e).__name__,
            )
            self._redis_connected = False
            return False
        except ValueError as e:
            # Configuration errors (invalid URL format, etc.)
            logger.error(
                "Redis configuration error (permanent) - check REDIS_URL format",
                error=str(e),
            )
            self._redis_connected = False
            # Disable cache to prevent repeated config errors
            self.config.cache_enabled = False
            return False
        except Exception as e:
            logger.warning(
                "Redis connection failed with unexpected error",
                error=str(e),
                error_type=type(e).__name__,
            )
            self._redis_connected = False
            return False

    def _generate_cache_key(
        self,
        product_id: str,
        images: list[str],
        category: str,
    ) -> str:
        """Generate a unique cache key for a product's assets."""
        # Create hash from product details and image paths
        content = f"{product_id}:{category}:{':'.join(sorted(images))}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{CACHE_KEY_PREFIX}3d:{hash_value}"

    async def _get_cached_result(self, cache_key: str) -> AssetPipelineResult | None:
        """Retrieve cached pipeline result.

        Args:
            cache_key: The cache key to look up.

        Returns:
            AssetPipelineResult if found and valid, None otherwise.

        Note:
            Cache failures are logged but do not propagate - the pipeline
            will continue without cache on any error.
        """
        if not await self._ensure_redis_connected():
            return None

        try:
            cached = await asyncio.wait_for(
                self._redis.get(cache_key),
                timeout=5.0,
            )
            if cached:
                logger.info("Cache hit", cache_key=cache_key)
                return AssetPipelineResult.model_validate_json(cached)
            return None
        except TimeoutError:
            logger.warning(
                "Cache retrieval timed out",
                cache_key=cache_key,
                timeout_seconds=5.0,
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                "Cache data corruption - invalid JSON",
                cache_key=cache_key,
                error=str(e),
            )
            # Attempt to delete corrupted cache entry
            try:
                await self._redis.delete(cache_key)
                logger.info("Deleted corrupted cache entry", cache_key=cache_key)
            except Exception as delete_err:
                logger.debug(
                    "Failed to delete corrupted cache entry (non-critical)",
                    cache_key=cache_key,
                    error=str(delete_err),
                )
            return None
        except ValidationError as e:
            logger.error(
                "Cache data schema mismatch - data may be from older version",
                cache_key=cache_key,
                error=str(e),
            )
            # Delete incompatible cache entry
            try:
                await self._redis.delete(cache_key)
                logger.info("Deleted incompatible cache entry", cache_key=cache_key)
            except Exception as delete_err:
                logger.debug(
                    "Failed to delete incompatible cache entry (non-critical)",
                    cache_key=cache_key,
                    error=str(delete_err),
                )
            return None
        except ConnectionError as e:
            logger.warning(
                "Redis connection lost during cache retrieval",
                cache_key=cache_key,
                error=str(e),
            )
            self._redis_connected = False
            return None
        except Exception as e:
            logger.warning(
                "Cache retrieval failed with unexpected error",
                cache_key=cache_key,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    async def _cache_result(self, cache_key: str, result: AssetPipelineResult) -> None:
        """Cache a pipeline result.

        Args:
            cache_key: The cache key to store under.
            result: The pipeline result to cache.

        Note:
            Cache write failures are logged but do not affect the pipeline.
            The result is still returned to the caller even if caching fails.
        """
        if not await self._ensure_redis_connected():
            return

        try:
            serialized = result.model_dump_json()
            await asyncio.wait_for(
                self._redis.setex(
                    cache_key,
                    self.config.cache_ttl_seconds,
                    serialized,
                ),
                timeout=5.0,
            )
            logger.info(
                "Result cached",
                cache_key=cache_key,
                ttl_days=self.config.cache_ttl_seconds // 86400,
                size_bytes=len(serialized),
            )
        except TimeoutError:
            logger.warning(
                "Cache write timed out - result not cached",
                cache_key=cache_key,
                timeout_seconds=5.0,
            )
        except ConnectionError as e:
            logger.warning(
                "Redis connection lost during cache write",
                cache_key=cache_key,
                error=str(e),
            )
            self._redis_connected = False
        except MemoryError as e:
            logger.error(
                "Redis out of memory - consider clearing cache or increasing memory",
                cache_key=cache_key,
                error=str(e),
            )
        except Exception as e:
            logger.warning(
                "Cache storage failed with unexpected error",
                cache_key=cache_key,
                error=str(e),
                error_type=type(e).__name__,
            )

    # =========================================================================
    # Stage 4.7.2: Progress Tracking
    # =========================================================================

    def register_progress_callback(
        self,
        callback: ProgressCallback | AsyncProgressCallback,
    ) -> None:
        """Register a callback for progress events."""
        self._progress_callbacks.append(callback)
        logger.debug("Progress callback registered", total=len(self._progress_callbacks))

    def unregister_progress_callback(
        self,
        callback: ProgressCallback | AsyncProgressCallback,
    ) -> None:
        """Unregister a progress callback."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)

    async def _emit_progress(self, event: ProgressEvent) -> None:
        """Emit a progress event to all registered callbacks."""
        if not self.config.enable_progress_callbacks:
            return

        for callback in self._progress_callbacks:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.warning("Progress callback error", error=str(e))

    # =========================================================================
    # Stage 4.7.2: Retry Queue Management
    # =========================================================================

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff."""
        delay = self.config.retry_delay * (self.config.retry_backoff_multiplier**retry_count)
        return min(delay, self.config.retry_max_delay)

    def _add_to_retry_queue(
        self,
        product_id: str,
        title: str,
        description: str,
        images: list[str],
        category: str,
        collection: str,
        garment_type: str,
        model_images: list[str] | None,
        wp_product_id: int | None,
        error: str,
        retry_count: int = 0,
    ) -> RetryQueueItem | None:
        """Add a failed item to the retry queue."""
        if retry_count >= self.config.max_retries:
            logger.warning(
                "Max retries exceeded, not adding to queue",
                product_id=product_id,
                retry_count=retry_count,
            )
            return None

        delay = self._calculate_retry_delay(retry_count)
        next_retry = datetime.now(UTC).timestamp() + delay
        next_retry_iso = datetime.fromtimestamp(next_retry, UTC).isoformat()

        item = RetryQueueItem(
            product_id=product_id,
            title=title,
            description=description,
            images=images,
            category=category,
            collection=collection,
            garment_type=garment_type,
            model_images=model_images,
            wp_product_id=wp_product_id,
            retry_count=retry_count + 1,
            last_error=error,
            next_retry_at=next_retry_iso,
        )

        self._retry_queue.append(item)
        logger.info(
            "Added to retry queue",
            product_id=product_id,
            retry_count=item.retry_count,
            next_retry_at=next_retry_iso,
        )
        return item

    async def process_retry_queue(self) -> list[AssetPipelineResult]:
        """Process all items in the retry queue that are ready."""
        now = datetime.now(UTC)
        ready_items: list[RetryQueueItem] = []
        remaining_items: list[RetryQueueItem] = []

        for item in self._retry_queue:
            if item.next_retry_at:
                retry_time = datetime.fromisoformat(item.next_retry_at)
                if retry_time <= now:
                    ready_items.append(item)
                else:
                    remaining_items.append(item)
            else:
                ready_items.append(item)

        self._retry_queue = remaining_items
        results: list[AssetPipelineResult] = []

        for item in ready_items:
            await self._emit_progress(
                ProgressEvent(
                    event_type=ProgressEventType.RETRY_ATTEMPT,
                    product_id=item.product_id,
                    message=f"Retry attempt {item.retry_count}/{self.config.max_retries}",
                    metadata={"retry_count": item.retry_count},
                )
            )

            result = await self.process_product(
                product_id=item.product_id,
                title=item.title,
                description=item.description,
                images=item.images,
                category=item.category,
                collection=item.collection,
                garment_type=item.garment_type,
                model_images=item.model_images,
                wp_product_id=item.wp_product_id,
                _retry_count=item.retry_count,
            )
            results.append(result)

        return results

    def get_retry_queue_status(self) -> dict[str, Any]:
        """Get current retry queue status."""
        return {
            "queue_length": len(self._retry_queue),
            "items": [item.model_dump() for item in self._retry_queue],
        }

    # =========================================================================
    # Stage 4.7.2: Batch Processing
    # =========================================================================

    async def process_batch(
        self,
        products: list[dict[str, Any]],
        progress_callback: ProgressCallback | AsyncProgressCallback | None = None,
    ) -> BatchResult:
        """
        Process multiple products concurrently with progress tracking.

        Args:
            products: List of product dicts with keys:
                - product_id, title, description, images, category
                - Optional: collection, garment_type, model_images, wp_product_id
            progress_callback: Optional callback for progress events

        Returns:
            BatchResult with all results and retry queue
        """
        import uuid

        batch_id = str(uuid.uuid4())[:8]
        start_time = datetime.now(UTC)

        # Register callback if provided
        if progress_callback:
            self.register_progress_callback(progress_callback)

        batch_result = BatchResult(
            batch_id=batch_id,
            total_items=len(products),
        )

        # Emit batch started
        await self._emit_progress(
            ProgressEvent(
                event_type=ProgressEventType.BATCH_STARTED,
                batch_id=batch_id,
                batch_total=len(products),
                message=f"Starting batch processing of {len(products)} products",
            )
        )

        logger.info(
            "Starting batch processing",
            batch_id=batch_id,
            total_products=len(products),
            concurrency=self.config.batch_concurrency,
        )

        async def process_with_semaphore(
            product: dict[str, Any],
            index: int,
        ) -> tuple[int, AssetPipelineResult | None, RetryQueueItem | None]:
            """Process a single product with semaphore control."""
            async with self._semaphore:
                product_id = product.get("product_id", f"unknown_{index}")

                # Emit item started
                await self._emit_progress(
                    ProgressEvent(
                        event_type=ProgressEventType.ITEM_STARTED,
                        product_id=product_id,
                        batch_id=batch_id,
                        batch_total=len(products),
                        batch_completed=batch_result.successful_items,
                        progress_percent=(index / len(products)) * 100,
                        message=f"Processing product {index + 1}/{len(products)}",
                    )
                )

                try:
                    # Check cache first
                    cache_key = self._generate_cache_key(
                        product_id,
                        product.get("images", []),
                        product.get("category", "apparel"),
                    )
                    cached = await self._get_cached_result(cache_key)

                    if cached and cached.status == "success":
                        await self._emit_progress(
                            ProgressEvent(
                                event_type=ProgressEventType.CACHE_HIT,
                                product_id=product_id,
                                batch_id=batch_id,
                                message="Using cached result",
                            )
                        )
                        return (index, cached, None)

                    # Process product with timeout
                    result = await asyncio.wait_for(
                        self.process_product(
                            product_id=product_id,
                            title=product.get("title", ""),
                            description=product.get("description", ""),
                            images=product.get("images", []),
                            category=product.get("category", "apparel"),
                            collection=product.get("collection", "SIGNATURE"),
                            garment_type=product.get("garment_type", "tee"),
                            model_images=product.get("model_images"),
                            wp_product_id=product.get("wp_product_id"),
                        ),
                        timeout=self.config.batch_timeout,
                    )

                    # Emit completion
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=(
                                ProgressEventType.ITEM_COMPLETED
                                if result.status == "success"
                                else ProgressEventType.ITEM_FAILED
                            ),
                            product_id=product_id,
                            batch_id=batch_id,
                            batch_total=len(products),
                            message=f"Product {result.status}",
                            metadata={"duration": result.duration_seconds},
                        )
                    )

                    return (index, result, None)

                except TimeoutError:
                    error_msg = f"Timeout after {self.config.batch_timeout}s"
                    logger.error("Product processing timeout", product_id=product_id)

                    retry_item = self._add_to_retry_queue(
                        product_id=product_id,
                        title=product.get("title", ""),
                        description=product.get("description", ""),
                        images=product.get("images", []),
                        category=product.get("category", "apparel"),
                        collection=product.get("collection", "SIGNATURE"),
                        garment_type=product.get("garment_type", "tee"),
                        model_images=product.get("model_images"),
                        wp_product_id=product.get("wp_product_id"),
                        error=error_msg,
                    )

                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.ITEM_FAILED,
                            product_id=product_id,
                            batch_id=batch_id,
                            message=error_msg,
                        )
                    )

                    return (index, None, retry_item)

                except Exception as e:
                    error_msg = str(e)
                    logger.error(
                        "Product processing failed",
                        product_id=product_id,
                        error=error_msg,
                    )

                    retry_item = self._add_to_retry_queue(
                        product_id=product_id,
                        title=product.get("title", ""),
                        description=product.get("description", ""),
                        images=product.get("images", []),
                        category=product.get("category", "apparel"),
                        collection=product.get("collection", "SIGNATURE"),
                        garment_type=product.get("garment_type", "tee"),
                        model_images=product.get("model_images"),
                        wp_product_id=product.get("wp_product_id"),
                        error=error_msg,
                    )

                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.ITEM_FAILED,
                            product_id=product_id,
                            batch_id=batch_id,
                            message=error_msg,
                        )
                    )

                    return (index, None, retry_item)

        # Process all products concurrently
        tasks = [process_with_semaphore(product, i) for i, product in enumerate(products)]
        results = await asyncio.gather(*tasks)

        # Aggregate results
        for _, result, retry_item in results:
            if result:
                batch_result.results.append(result)
                if result.status == "success":
                    batch_result.successful_items += 1
                else:
                    batch_result.failed_items += 1
            elif retry_item:
                batch_result.retry_queue.append(retry_item)
                batch_result.failed_items += 1

        # Check for cached items
        batch_result.cached_items = sum(
            1
            for _, r, _ in results
            if r and r.duration_seconds < 1.0  # Cached results are fast
        )

        # Finalize
        end_time = datetime.now(UTC)
        batch_result.completed_at = end_time.isoformat()
        batch_result.duration_seconds = (end_time - start_time).total_seconds()

        # Emit batch completed
        await self._emit_progress(
            ProgressEvent(
                event_type=ProgressEventType.BATCH_COMPLETED,
                batch_id=batch_id,
                batch_total=batch_result.total_items,
                batch_completed=batch_result.successful_items,
                batch_failed=batch_result.failed_items,
                progress_percent=100.0,
                message=f"Batch complete: {batch_result.successful_items}/{batch_result.total_items} successful",
                metadata={
                    "duration_seconds": batch_result.duration_seconds,
                    "cached_items": batch_result.cached_items,
                    "retry_queue_size": len(batch_result.retry_queue),
                },
            )
        )

        # Unregister callback if we registered it
        if progress_callback:
            self.unregister_progress_callback(progress_callback)

        logger.info(
            "Batch processing complete",
            batch_id=batch_id,
            total=batch_result.total_items,
            successful=batch_result.successful_items,
            failed=batch_result.failed_items,
            cached=batch_result.cached_items,
            duration=batch_result.duration_seconds,
        )

        return batch_result

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
        _retry_count: int = 0,  # Stage 4.7.2: Internal retry tracking
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
            _retry_count: Internal parameter for retry tracking (do not set manually)

        Returns:
            AssetPipelineResult with all generated assets
        """
        start_time = datetime.now(UTC)

        # Stage 4.7.2: Check cache first
        cache_key = self._generate_cache_key(product_id, images, category)
        cached_result = await self._get_cached_result(cache_key)
        if cached_result and cached_result.status == "success":
            logger.info("Returning cached result", product_id=product_id)
            await self._emit_progress(
                ProgressEvent(
                    event_type=ProgressEventType.CACHE_HIT,
                    product_id=product_id,
                    message="Using cached result",
                )
            )
            return cached_result

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
            # 3D Generation based on primary generator setting
            hf_3d_result = None

            if self.config.primary_3d_generator == Primary3DGenerator.HUGGINGFACE:
                # Use HuggingFace as primary 3D generator (recommended for quality)
                if images:
                    result.stage = PipelineStage.GENERATING_3D
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_STARTED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=10.0,
                            message="Generating high-quality 3D model with HuggingFace",
                        )
                    )
                    await self._generate_3d_with_huggingface_primary(
                        result=result,
                        title=title,
                        images=images,
                        collection=collection,
                        garment_type=garment_type,
                    )
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_COMPLETED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=40.0,
                            message=f"HuggingFace 3D models generated: {len(result.assets_3d)}",
                        )
                    )

            elif self.config.primary_3d_generator == Primary3DGenerator.HYBRID:
                # Hybrid: HuggingFace for hints, Tripo3D for generation
                if self.config.enable_huggingface_3d and images:
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_STARTED,
                            product_id=product_id,
                            stage="generating_hf_3d",
                            progress_percent=5.0,
                            message="Generating optimization hints with HuggingFace",
                        )
                    )
                    hf_3d_result = await self._generate_3d_with_huggingface(
                        result=result,
                        title=title,
                        images=images,
                    )
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_COMPLETED,
                            product_id=product_id,
                            stage="generating_hf_3d",
                            progress_percent=15.0,
                            message="HuggingFace optimization complete",
                        )
                    )

                # Generate with Tripo3D using HF hints
                if self.config.enable_3d_generation and images:
                    result.stage = PipelineStage.GENERATING_3D
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_STARTED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=20.0,
                            message="Generating 3D models with Tripo3D (HF-optimized)",
                        )
                    )
                    await self._generate_3d_models(
                        result=result,
                        title=title,
                        images=images,
                        collection=collection,
                        garment_type=garment_type,
                        hf_3d_result=hf_3d_result,
                    )
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_COMPLETED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=40.0,
                            message=f"3D models generated: {len(result.assets_3d)}",
                        )
                    )

            else:
                # TRIPO3D: Original behavior - Tripo3D only
                if self.config.enable_3d_generation and images:
                    result.stage = PipelineStage.GENERATING_3D
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_STARTED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=20.0,
                            message="Generating 3D models with Tripo3D",
                        )
                    )
                    await self._generate_3d_models(
                        result=result,
                        title=title,
                        images=images,
                        collection=collection,
                        garment_type=garment_type,
                        hf_3d_result=None,
                    )
                    await self._emit_progress(
                        ProgressEvent(
                            event_type=ProgressEventType.STAGE_COMPLETED,
                            product_id=product_id,
                            stage=PipelineStage.GENERATING_3D.value,
                            progress_percent=40.0,
                            message=f"3D models generated: {len(result.assets_3d)}",
                        )
                    )

            # Stage 2: Generate virtual try-on (apparel only)
            if (
                self.config.enable_virtual_tryon
                and product_category == ProductCategory.APPAREL
                and images
            ):
                result.stage = PipelineStage.GENERATING_TRYON
                await self._emit_progress(
                    ProgressEvent(
                        event_type=ProgressEventType.STAGE_STARTED,
                        product_id=product_id,
                        stage=PipelineStage.GENERATING_TRYON.value,
                        progress_percent=45.0,
                        message="Generating virtual try-on images",
                    )
                )
                await self._generate_tryon_images(
                    result=result,
                    garment_images=images,
                    model_images=model_images,
                    garment_type=garment_type,
                )
                await self._emit_progress(
                    ProgressEvent(
                        event_type=ProgressEventType.STAGE_COMPLETED,
                        product_id=product_id,
                        stage=PipelineStage.GENERATING_TRYON.value,
                        progress_percent=70.0,
                        message=f"Try-on images generated: {len(result.assets_tryon)}",
                    )
                )

            # Stage 3: Upload to WordPress
            if self.config.enable_wordpress_upload:
                result.stage = PipelineStage.UPLOADING_ASSETS
                await self._emit_progress(
                    ProgressEvent(
                        event_type=ProgressEventType.STAGE_STARTED,
                        product_id=product_id,
                        stage=PipelineStage.UPLOADING_ASSETS.value,
                        progress_percent=75.0,
                        message="Uploading assets to WordPress",
                    )
                )
                await self._upload_to_wordpress(
                    result=result,
                    title=title,
                    wp_product_id=wp_product_id,
                )
                await self._emit_progress(
                    ProgressEvent(
                        event_type=ProgressEventType.STAGE_COMPLETED,
                        product_id=product_id,
                        stage=PipelineStage.UPLOADING_ASSETS.value,
                        progress_percent=95.0,
                        message=f"Assets uploaded: {len(result.assets_wordpress)}",
                    )
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
            result.errors.append(
                {
                    "stage": result.stage.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            )

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

        # Stage 4.7.2: Cache successful results
        if result.status == "success":
            await self._cache_result(cache_key, result)

        # Stage 4.7.2: Add to retry queue on failure (if not already a retry)
        if result.status == "error" and _retry_count < self.config.max_retries:
            error_msg = (
                result.errors[-1].get("error", "Unknown error")
                if result.errors
                else "Unknown error"
            )
            self._add_to_retry_queue(
                product_id=product_id,
                title=title,
                description=description,
                images=images,
                category=category,
                collection=collection,
                garment_type=garment_type,
                model_images=model_images,
                wp_product_id=wp_product_id,
                error=str(error_msg),
                retry_count=_retry_count,
            )

        return result

    async def _generate_3d_with_huggingface_primary(
        self,
        result: AssetPipelineResult,
        title: str,
        images: list[str],
        collection: str,
        garment_type: str,
    ) -> None:
        """
        Generate production-quality 3D models using HuggingFace as primary generator.

        This uses Hunyuan3D 2.0 or InstantMesh for best quality output,
        bypassing Tripo3D entirely for higher fidelity.
        """
        from orchestration.huggingface_3d_client import HF3DModel, HF3DQuality

        logger.info(
            "Generating 3D models with HuggingFace (primary)",
            title=title,
            image_count=len(images),
        )

        # Use production quality settings
        models_to_try = [
            HF3DModel.HUNYUAN3D_2,  # Best quality
            HF3DModel.INSTANTMESH,  # Good for complex geometry
            HF3DModel.TRIPOSR,  # Fallback
        ]

        for image_path in images[:1]:  # Use first image for 3D generation
            best_result = None
            best_score = 0.0

            for model in models_to_try:
                try:
                    logger.info(
                        f"Trying HuggingFace model: {model.value}",
                        image=image_path,
                    )

                    hf_result = await self.huggingface_client.generate_from_image(
                        image_path=image_path,
                        model=model,
                        quality=HF3DQuality.PRODUCTION,
                        remove_background=True,
                    )

                    if hf_result.status == "completed" and hf_result.output_path:
                        score = hf_result.quality_score or 0.0

                        if score > best_score:
                            best_score = score
                            best_result = hf_result

                        logger.info(
                            f"HuggingFace {model.value} succeeded",
                            quality_score=score,
                            path=hf_result.output_path,
                        )

                        # If we got a good result, stop trying other models
                        if score >= 85.0:
                            break

                except Exception as e:
                    logger.warning(
                        f"HuggingFace model {model.value} failed",
                        error=str(e),
                    )
                    continue

            # Add best result to pipeline output
            if best_result and best_result.output_path:
                result.assets_3d.append(
                    Asset3DResult(
                        task_id=best_result.task_id,
                        model_path=best_result.output_path,
                        model_url=best_result.output_url,
                        format=best_result.format.value,
                        thumbnail_path=None,
                        metadata={
                            "collection": collection,
                            "garment_type": garment_type,
                            "source_image": image_path,
                            "hf_model": best_result.model_used.value,
                            "quality_score": best_result.quality_score,
                            "polycount": best_result.polycount,
                            "has_textures": best_result.has_textures,
                            "generation_time_ms": best_result.generation_time_ms,
                        },
                    )
                )
                logger.info(
                    "HuggingFace 3D generation successful",
                    model=best_result.model_used.value,
                    quality_score=best_score,
                    path=best_result.output_path,
                )
            else:
                result.errors.append(
                    {
                        "stage": "hf_3d_generation_primary",
                        "error": "All HuggingFace models failed to generate 3D",
                        "image": image_path,
                    }
                )

    async def _generate_3d_with_huggingface(
        self,
        result: AssetPipelineResult,
        title: str,
        images: list[str],
    ) -> Any:
        """
        Generate initial 3D model using HuggingFace Shap-E.

        This is Stage 0 of the hybrid pipeline. HF generates a quick,
        lower-quality 3D model that we analyze for optimization hints
        to enhance the Tripo3D prompt.

        Returns:
            HF3DResult or None if generation fails or HF is disabled
        """
        # Early return if HuggingFace 3D generation is disabled
        if not self.config.enable_huggingface_3d:
            logger.debug("HuggingFace 3D generation disabled, skipping")
            return None

        logger.info("Generating 3D model with HuggingFace Shap-E", title=title)

        for image_path in images[:1]:  # Use first image only
            try:
                # Generate from image
                hf_result = await self.huggingface_client.generate_from_image(
                    image_path=image_path,
                )

                if hf_result:
                    # Get optimization hints for Tripo3D
                    if self.config.huggingface_config.enable_optimization_hints:
                        hints = await self.huggingface_client.get_optimization_hints(hf_result)
                        logger.info(
                            "HF optimization hints generated",
                            geometry=hints.detected_geometry,
                            complexity=hints.detected_complexity,
                            tripo_prompt=hints.suggested_tripo_prompt[:50],
                        )

                    # Store in result metadata for later use
                    result.errors.append(
                        {
                            "stage": "hf_3d_generation",
                            "type": "info",
                            "message": "HF 3D generation successful",
                            "hf_quality_score": hf_result.quality_score,
                            "hf_model": hf_result.model_used.value,
                            "hf_polycount": hf_result.polycount,
                        }
                    )

                    return hf_result

            except Exception as e:
                logger.warning(
                    "HuggingFace 3D generation failed (will fallback to Tripo3D only)",
                    image=image_path,
                    error=str(e),
                )
                # Don't fail pipeline - HF is optional enhancement
                result.errors.append(
                    {
                        "stage": "hf_3d_generation",
                        "type": "warning",
                        "error": str(e),
                        "message": "HF 3D generation failed, will use Tripo3D only",
                    }
                )

        return None

    async def _generate_3d_models(
        self,
        result: AssetPipelineResult,
        title: str,
        images: list[str],
        collection: str,
        garment_type: str,
        hf_3d_result: Any = None,
    ) -> None:
        """
        Generate 3D models using Tripo3D agent (Stage 1).

        If hf_3d_result is provided, uses optimization hints to enhance
        the Tripo3D prompt for better quality output.
        """
        logger.info(
            "Generating 3D models with Tripo3D",
            title=title,
            image_count=len(images),
            has_hf_hints=hf_3d_result is not None,
        )

        for image_path in images[:1]:  # Use first image for 3D generation
            try:
                # Build request with HF optimization hints if available
                request_data = {
                    "action": "generate_from_image",
                    "image_path": image_path,
                    "product_name": title,
                    "output_format": "glb",
                }

                # If HF provided optimization hints, include them
                if hf_3d_result and hf_3d_result.tripo3d_prompt:
                    request_data["optimized_prompt"] = hf_3d_result.tripo3d_prompt
                    logger.info(
                        "Using HF-optimized prompt for Tripo3D",
                        prompt=hf_3d_result.tripo3d_prompt[:50],
                    )

                # Generate from image
                gen_result = await self.tripo_agent.run(request_data)

                if gen_result.get("status") == "success":
                    data = gen_result.get("data", {})
                    result.assets_3d.append(
                        Asset3DResult(
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
                        )
                    )
                else:
                    result.errors.append(
                        {
                            "stage": "3d_generation",
                            "error": gen_result.get("error", "Unknown error"),
                            "image": image_path,
                        }
                    )

            except Exception as e:
                logger.error("3D generation failed", image=image_path, error=str(e))
                result.errors.append(
                    {
                        "stage": "3d_generation",
                        "error": str(e),
                        "image": image_path,
                    }
                )

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
                    tryon_result = await self.fashn_agent.run(
                        {
                            "action": "virtual_tryon",
                            "model_image": model_image,
                            "garment_image": garment_image,
                            "category": category.value,
                            "mode": "balanced",
                        }
                    )

                    if tryon_result.get("status") == "success":
                        data = tryon_result.get("data", {})
                        # Handle nested result structure
                        if isinstance(data, dict) and "fashn_virtual_tryon" in data:
                            data = data.get("fashn_virtual_tryon", {})

                        result.assets_tryon.append(
                            TryOnAssetResult(
                                task_id=data.get("task_id", ""),
                                image_path=data.get("image_path", ""),
                                image_url=data.get("image_url"),
                                model_image=model_image,
                                garment_image=garment_image,
                                metadata={"category": category.value},
                            )
                        )
                    else:
                        result.errors.append(
                            {
                                "stage": "tryon_generation",
                                "error": tryon_result.get("error", "Unknown error"),
                                "garment": garment_image,
                                "model": model_image,
                            }
                        )

                except Exception as e:
                    logger.error(
                        "Try-on generation failed",
                        garment=garment_image,
                        model=model_image,
                        error=str(e),
                    )
                    result.errors.append(
                        {
                            "stage": "tryon_generation",
                            "error": str(e),
                            "garment": garment_image,
                            "model": model_image,
                        }
                    )

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

                result.assets_wordpress.append(
                    WordPressAssetResult(
                        media_id=upload_result.get("media_id", 0),
                        url=upload_result.get("glb_url") or upload_result.get("usdz_url") or "",
                        asset_type="3d_model",
                        product_id=wp_product_id,
                    )
                )

            except Exception as e:
                logger.error("3D model upload failed", error=str(e))
                result.errors.append(
                    {
                        "stage": "wordpress_upload",
                        "error": str(e),
                        "asset_type": "3d_model",
                    }
                )

        # Upload try-on images
        for asset in result.assets_tryon:
            try:
                upload_result = await self.wordpress_agent.run(
                    {
                        "action": "upload_media",
                        "file_path": asset.image_path,
                        "title": f"{title} - Virtual Try-On",
                        "alt_text": f"Virtual try-on of {title}",
                    }
                )

                if upload_result.get("status") == "success":
                    data = upload_result.get("data", {}).get("upload", {})
                    result.assets_wordpress.append(
                        WordPressAssetResult(
                            media_id=data.get("id", 0),
                            url=data.get("url", ""),
                            asset_type="tryon_image",
                            product_id=wp_product_id,
                        )
                    )

            except Exception as e:
                logger.error("Try-on image upload failed", error=str(e))
                result.errors.append(
                    {
                        "stage": "wordpress_upload",
                        "error": str(e),
                        "asset_type": "tryon_image",
                    }
                )


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Core Pipeline
    "ProductAssetPipeline",
    "PipelineConfig",
    # Result Types
    "AssetPipelineResult",
    "Asset3DResult",
    "TryOnAssetResult",
    "WordPressAssetResult",
    # Enums
    "ProductCategory",
    "PipelineStage",
    "Primary3DGenerator",
    # Stage 4.7.2: Batch Processing
    "BatchResult",
    "RetryQueueItem",
    # Stage 4.7.2: Progress Tracking
    "ProgressEvent",
    "ProgressEventType",
    "ProgressCallback",
    "AsyncProgressCallback",
    # Stage 4.7.2: Cache Constants
    "CACHE_TTL_SECONDS",
    "CACHE_KEY_PREFIX",
]
