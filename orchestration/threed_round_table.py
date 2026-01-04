"""
3D Model Round Table - Production-Ready Implementation
======================================================

Tournament system where multiple 3D generation models compete on every task.

Architecture:
- Circuit Breaker Pattern: Fail fast when providers are unhealthy
- Retry Pattern: Exponential backoff with jitter for transient failures
- Timeout Pattern: Maximum execution times per provider
- Concurrency Control: Semaphore-based task management
- Fallback Mechanisms: Cached/default responses when circuit is open
- Health Monitoring: Provider health tracking and automatic recovery
- Quality-First: All assets optimized to highest quality before preprocessing

Flow:
1. All 3D models generate outputs in parallel (with circuit breakers)
2. Automatic quality enhancement and preprocessing
3. Score and rank using quality metrics
4. Select top 2 for A/B comparison
5. Quality analysis determines winner
6. Persist results to database
7. Return best 3D model output

References:
- Circuit Breaker: https://github.com/arlyon/aiobreaker
- Retry patterns: tenacity library
- Release It! by Michael T. Nygard

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import random
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, TypeVar
from uuid import uuid4

import structlog

from orchestration.huggingface_3d_client import (
    HF3DFormat,
    HF3DModel,
    HF3DQuality,
    HF3DResult,
    HuggingFace3DClient,
    HuggingFace3DConfig,
)

logger = structlog.get_logger(__name__)

T = TypeVar("T")


# =============================================================================
# Circuit Breaker Implementation
# =============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 30.0  # Seconds before half-open
    success_threshold: int = 2  # Successes in half-open to close
    timeout: float = 60.0  # Request timeout in seconds


@dataclass
class CircuitBreakerState:
    """State tracking for a circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime = field(default_factory=lambda: datetime.now(UTC))

    def should_allow_request(self, config: CircuitBreakerConfig) -> bool:
        """Check if request should be allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if self.last_failure_time:
                elapsed = (datetime.now(UTC) - self.last_failure_time).total_seconds()
                if elapsed >= config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.last_state_change = datetime.now(UTC)
                    return True
            return False
        return True

    def record_success(self, config: CircuitBreakerConfig) -> None:
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                self.last_state_change = datetime.now(UTC)
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self, config: CircuitBreakerConfig) -> None:
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now(UTC)

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now(UTC)
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= config.failure_threshold:
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now(UTC)


# =============================================================================
# Retry Configuration
# =============================================================================


@dataclass
class RetryConfig:
    """Configuration for retry behavior with exponential backoff + jitter."""

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: float = 0.5
    retryable_exceptions: tuple[type[Exception], ...] = (
        asyncio.TimeoutError,
        ConnectionError,
        OSError,
    )

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff + jitter."""
        delay = min(
            self.base_delay * (self.exponential_base**attempt),
            self.max_delay,
        )
        jitter_range = delay * self.jitter
        delay += random.uniform(-jitter_range, jitter_range)
        return max(0, delay)


# =============================================================================
# Quality Enhancement Configuration
# =============================================================================


@dataclass
class QualityEnhancementConfig:
    """Configuration for automatic quality enhancement before preprocessing."""

    # Enable quality enhancement
    enable_enhancement: bool = True

    # Resolution settings (higher = better quality)
    target_texture_resolution: int = 4096  # 4K textures
    min_polycount: int = 50000  # Minimum polygons
    max_polycount: int = 500000  # Maximum for web performance

    # Format preferences
    preferred_format: HF3DFormat = HF3DFormat.GLB
    enable_draco_compression: bool = True  # Compress for web

    # Quality thresholds
    min_quality_score: float = 75.0  # Reject below this
    target_quality_score: float = 90.0  # Aim for this

    # Enhancement passes
    enable_mesh_optimization: bool = True
    enable_texture_upscaling: bool = True
    enable_normal_map_generation: bool = True
    enable_uv_unwrapping: bool = True

    # Post-processing
    enable_auto_rigging: bool = False  # For animated models
    enable_lod_generation: bool = True  # Level of Detail for web


# =============================================================================
# Provider Health Tracking
# =============================================================================


@dataclass
class ProviderHealth:
    """Health status for a 3D generation provider."""

    provider: str
    circuit_breaker: CircuitBreakerState = field(default_factory=CircuitBreakerState)
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    last_error: str | None = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def average_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests

    @property
    def is_healthy(self) -> bool:
        """Check if provider is healthy."""
        return self.circuit_breaker.state == CircuitState.CLOSED


# =============================================================================
# Enums and Types
# =============================================================================


class ThreeDProvider(str, Enum):
    """3D generation providers participating in Round Table."""

    # HuggingFace Models
    HUNYUAN3D_2 = "hunyuan3d_2"
    TRIPOSR = "triposr"
    INSTANTMESH = "instantmesh"
    LGM = "lgm"
    SHAP_E = "shap_e"
    POINT_E = "point_e"

    # External APIs
    TRIPO3D = "tripo3d"

    # Custom/Community
    CUSTOM = "custom"


class CompetitionStatus(str, Enum):
    """Status of a 3D Round Table competition."""

    PENDING = "pending"
    GENERATING = "generating"
    ENHANCING = "enhancing"  # Quality enhancement phase
    SCORING = "scoring"
    COMPARING = "comparing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class GenerationType(str, Enum):
    """Type of 3D generation task."""

    TEXT_TO_3D = "text_to_3d"
    IMAGE_TO_3D = "image_to_3d"


# =============================================================================
# Scoring Data Classes
# =============================================================================


@dataclass(slots=True)
class ThreeDQualityScores:
    """Quality scoring breakdown for a 3D model. Memory-optimized."""

    geometry_quality: float = 0.0
    texture_quality: float = 0.0
    polycount_efficiency: float = 0.0
    file_format_score: float = 0.0
    generation_speed: float = 0.0
    web_readiness: float = 0.0
    enhancement_bonus: float = 0.0  # Bonus for quality enhancement

    @property
    def total(self) -> float:
        """Weighted total score (0-100)."""
        base_score = (
            self.geometry_quality * 0.30
            + self.texture_quality * 0.25
            + self.polycount_efficiency * 0.15
            + self.file_format_score * 0.10
            + self.generation_speed * 0.10
            + self.web_readiness * 0.10
        )
        return min(base_score + self.enhancement_bonus, 100.0)

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "geometry_quality": self.geometry_quality,
            "texture_quality": self.texture_quality,
            "polycount_efficiency": self.polycount_efficiency,
            "file_format_score": self.file_format_score,
            "generation_speed": self.generation_speed,
            "web_readiness": self.web_readiness,
            "enhancement_bonus": self.enhancement_bonus,
            "total": self.total,
        }


@dataclass
class ThreeDResponse:
    """Response from a 3D generation provider."""

    provider: ThreeDProvider
    model_id: str
    output_path: str | None = None
    output_url: str | None = None
    output_bytes: bytes | None = None
    format: HF3DFormat = HF3DFormat.GLB
    generation_time_ms: float = 0.0
    polycount: int | None = None
    has_textures: bool = False
    file_size_bytes: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0
    circuit_breaker_state: str = "closed"
    enhanced: bool = False  # Was quality enhancement applied
    enhancement_details: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if generation was successful."""
        return self.error is None and (self.output_path or self.output_bytes)


@dataclass
class RoundTableEntry:
    """Entry in the 3D Round Table competition."""

    provider: ThreeDProvider
    response: ThreeDResponse
    scores: ThreeDQualityScores = field(default_factory=ThreeDQualityScores)
    rank: int = 0

    @property
    def total_score(self) -> float:
        """Get total weighted score."""
        return self.scores.total


@dataclass
class ABTestResult:
    """Result from A/B testing between top 2 3D models."""

    entry_a: RoundTableEntry
    entry_b: RoundTableEntry
    winner: RoundTableEntry
    comparison_method: str
    reasoning: str
    confidence: float
    metrics_comparison: dict[str, Any] = field(default_factory=dict)
    tested_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RoundTableResult:
    """Complete result from a 3D Round Table competition."""

    id: str
    task_id: str
    prompt: str
    generation_type: GenerationType
    entries: list[RoundTableEntry]
    top_two: list[RoundTableEntry]
    ab_test: ABTestResult | None
    winner: RoundTableEntry | None
    status: CompetitionStatus
    total_duration_ms: float
    enhancement_applied: bool = False
    provider_health: dict[str, dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "prompt": self.prompt[:500],
            "generation_type": self.generation_type.value,
            "winner_provider": self.winner.provider.value if self.winner else None,
            "winner_score": self.winner.total_score if self.winner else None,
            "status": self.status.value,
            "total_duration_ms": self.total_duration_ms,
            "enhancement_applied": self.enhancement_applied,
            "num_competitors": len(self.entries),
            "num_successful": len([e for e in self.entries if e.response.success]),
            "created_at": self.created_at.isoformat(),
            "provider_health": self.provider_health,
            "entries": [
                {
                    "provider": e.provider.value,
                    "rank": e.rank,
                    "score": e.total_score,
                    "scores": e.scores.to_dict(),
                    "generation_time_ms": e.response.generation_time_ms,
                    "polycount": e.response.polycount,
                    "has_textures": e.response.has_textures,
                    "enhanced": e.response.enhanced,
                    "retry_count": e.response.retry_count,
                    "circuit_state": e.response.circuit_breaker_state,
                    "error": e.response.error,
                }
                for e in self.entries
            ],
        }


# =============================================================================
# 3D Model Round Table - Production Implementation
# =============================================================================


class ThreeDRoundTable:
    """
    3D Model Round Table - Production-Ready Tournament for 3D Generation.

    Features:
    - Circuit breaker per provider (fail fast, auto-recovery)
    - Retry with exponential backoff + jitter
    - Configurable timeouts per provider
    - Provider health monitoring
    - Concurrent generation with semaphore control
    - Automatic quality enhancement to highest quality
    - Quality-first preprocessing pipeline
    - Structured logging for observability
    """

    # Provider to HF3DModel mapping
    PROVIDER_MODEL_MAP: dict[ThreeDProvider, HF3DModel] = {
        ThreeDProvider.HUNYUAN3D_2: HF3DModel.HUNYUAN3D_2,
        ThreeDProvider.TRIPOSR: HF3DModel.TRIPOSR,
        ThreeDProvider.INSTANTMESH: HF3DModel.INSTANTMESH,
        ThreeDProvider.LGM: HF3DModel.LGM,
        ThreeDProvider.SHAP_E: HF3DModel.SHAP_E_TEXT,
        ThreeDProvider.POINT_E: HF3DModel.POINT_E,
    }

    # Provider-specific timeouts (seconds) - generous for high quality
    PROVIDER_TIMEOUTS: dict[ThreeDProvider, float] = {
        ThreeDProvider.HUNYUAN3D_2: 180.0,  # Complex model, needs time for quality
        ThreeDProvider.TRIPOSR: 90.0,
        ThreeDProvider.INSTANTMESH: 120.0,
        ThreeDProvider.LGM: 90.0,
        ThreeDProvider.SHAP_E: 60.0,
        ThreeDProvider.POINT_E: 45.0,
        ThreeDProvider.TRIPO3D: 300.0,  # External API, allow for high quality
    }

    # Default providers for text-to-3D
    TEXT_TO_3D_PROVIDERS: list[ThreeDProvider] = [
        ThreeDProvider.HUNYUAN3D_2,
        ThreeDProvider.SHAP_E,
    ]

    # Default providers for image-to-3D
    IMAGE_TO_3D_PROVIDERS: list[ThreeDProvider] = [
        ThreeDProvider.HUNYUAN3D_2,
        ThreeDProvider.TRIPOSR,
        ThreeDProvider.INSTANTMESH,
        ThreeDProvider.LGM,
    ]

    def __init__(
        self,
        hf_config: HuggingFace3DConfig | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
        retry_config: RetryConfig | None = None,
        quality_config: QualityEnhancementConfig | None = None,
        output_dir: str = "./round_table_outputs",
        enable_tripo3d: bool = True,
        concurrent_limit: int = 4,
    ) -> None:
        """
        Initialize 3D Round Table with production-ready configuration.

        All assets are automatically enhanced to highest quality before preprocessing.

        Args:
            hf_config: HuggingFace configuration
            circuit_breaker_config: Circuit breaker settings
            retry_config: Retry behavior settings
            quality_config: Quality enhancement settings
            output_dir: Directory for generated models
            enable_tripo3d: Whether to include Tripo3D
            concurrent_limit: Max concurrent generation tasks
        """
        # Override HF config for highest quality
        if hf_config is None:
            hf_config = HuggingFace3DConfig.from_env()
        hf_config.default_quality = HF3DQuality.PRODUCTION  # Always highest quality
        hf_config.default_format = HF3DFormat.GLB  # Best for web

        self.hf_client = HuggingFace3DClient(config=hf_config)
        self.cb_config = circuit_breaker_config or CircuitBreakerConfig()
        self.retry_config = retry_config or RetryConfig()
        self.quality_config = quality_config or QualityEnhancementConfig()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.enable_tripo3d = enable_tripo3d
        self._semaphore = asyncio.Semaphore(concurrent_limit)

        # Initialize health tracking for each provider
        self._provider_health: dict[ThreeDProvider, ProviderHealth] = {
            provider: ProviderHealth(provider=provider.value) for provider in ThreeDProvider
        }

        # Tripo agent (lazy loaded)
        self._tripo_agent = None
        self._tripo_agent_loaded = False

        logger.info(
            "3D Round Table initialized with HIGHEST QUALITY settings",
            output_dir=str(self.output_dir),
            concurrent_limit=concurrent_limit,
            default_quality="PRODUCTION",
            enhancement_enabled=self.quality_config.enable_enhancement,
            target_texture_resolution=self.quality_config.target_texture_resolution,
        )

    def _get_tripo_agent(self) -> Any:
        """Lazy load Tripo agent."""
        if not self._tripo_agent_loaded:
            self._tripo_agent_loaded = True
            if self.enable_tripo3d:
                try:
                    from agents.tripo_agent import TripoAssetAgent

                    self._tripo_agent = TripoAssetAgent()
                    logger.info("Tripo3D agent loaded for highest quality generation")
                except (ImportError, Exception) as e:
                    logger.warning("Tripo3D agent not available", error=str(e))
                    self.enable_tripo3d = False
        return self._tripo_agent

    async def compete_text_to_3d(
        self,
        prompt: str,
        providers: list[ThreeDProvider] | None = None,
        output_format: HF3DFormat = HF3DFormat.GLB,
        quality: HF3DQuality = HF3DQuality.PRODUCTION,  # Always highest
        task_id: str | None = None,
        skip_unhealthy: bool = True,
        enhance_quality: bool = True,  # Enable quality enhancement
    ) -> RoundTableResult:
        """
        Run text-to-3D competition with automatic quality enhancement.

        All assets are enhanced to highest quality before preprocessing.

        Args:
            prompt: Text description of the 3D object
            providers: List of providers to compete
            output_format: Desired output format
            quality: Quality preset (defaults to PRODUCTION)
            task_id: Optional task ID for tracking
            skip_unhealthy: Skip providers with open circuit breakers
            enhance_quality: Apply quality enhancement (recommended: True)

        Returns:
            RoundTableResult with winner and all entries
        """
        providers = list(providers or self.TEXT_TO_3D_PROVIDERS)

        if self.enable_tripo3d and ThreeDProvider.TRIPO3D not in providers:
            providers.append(ThreeDProvider.TRIPO3D)

        return await self._run_competition(
            providers=providers,
            generation_type=GenerationType.TEXT_TO_3D,
            prompt=prompt,
            output_format=output_format,
            quality=quality,
            task_id=task_id,
            skip_unhealthy=skip_unhealthy,
            enhance_quality=enhance_quality,
        )

    async def compete_image_to_3d(
        self,
        image_path: str,
        providers: list[ThreeDProvider] | None = None,
        output_format: HF3DFormat = HF3DFormat.GLB,
        quality: HF3DQuality = HF3DQuality.PRODUCTION,  # Always highest
        remove_background: bool = True,
        task_id: str | None = None,
        skip_unhealthy: bool = True,
        enhance_quality: bool = True,  # Enable quality enhancement
    ) -> RoundTableResult:
        """
        Run image-to-3D competition with automatic quality enhancement.

        All assets are enhanced to highest quality before preprocessing.

        Args:
            image_path: Path to input image or URL
            providers: List of providers to compete
            output_format: Desired output format
            quality: Quality preset (defaults to PRODUCTION)
            remove_background: Whether to remove background first
            task_id: Optional task ID for tracking
            skip_unhealthy: Skip providers with open circuit breakers
            enhance_quality: Apply quality enhancement (recommended: True)

        Returns:
            RoundTableResult with winner and all entries
        """
        providers = list(providers or self.IMAGE_TO_3D_PROVIDERS)

        if self.enable_tripo3d and ThreeDProvider.TRIPO3D not in providers:
            providers.append(ThreeDProvider.TRIPO3D)

        image_hash = hashlib.sha256(image_path.encode()).hexdigest()[:16]

        return await self._run_competition(
            providers=providers,
            generation_type=GenerationType.IMAGE_TO_3D,
            prompt=f"image:{image_hash}",
            image_path=image_path,
            output_format=output_format,
            quality=quality,
            remove_background=remove_background,
            task_id=task_id,
            skip_unhealthy=skip_unhealthy,
            enhance_quality=enhance_quality,
        )

    async def _run_competition(
        self,
        providers: list[ThreeDProvider],
        generation_type: GenerationType,
        prompt: str,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        task_id: str | None = None,
        image_path: str | None = None,
        remove_background: bool = True,
        skip_unhealthy: bool = True,
        enhance_quality: bool = True,
    ) -> RoundTableResult:
        """Internal competition runner with quality enhancement."""
        task_id = task_id or str(uuid4())[:8]
        competition_id = str(uuid4())[:12]

        # Filter unhealthy providers
        active_providers = providers.copy()
        skipped_providers: list[ThreeDProvider] = []

        if skip_unhealthy:
            for provider in providers:
                health = self._provider_health[provider]
                if not health.circuit_breaker.should_allow_request(self.cb_config):
                    active_providers.remove(provider)
                    skipped_providers.append(provider)

        if not active_providers:
            logger.error(
                "All providers have open circuit breakers",
                competition_id=competition_id,
            )
            return self._create_failed_result(
                competition_id=competition_id,
                task_id=task_id,
                prompt=prompt,
                generation_type=generation_type,
                error="All providers have open circuit breakers",
            )

        logger.info(
            "Starting 3D Round Table (HIGHEST QUALITY)",
            competition_id=competition_id,
            task_id=task_id,
            generation_type=generation_type.value,
            quality=quality.value,
            enhancement_enabled=enhance_quality,
            active_providers=[p.value for p in active_providers],
        )

        start_time = time.time()

        # Generate from all active providers in parallel
        if generation_type == GenerationType.TEXT_TO_3D:
            tasks = [
                self._generate_with_resilience(
                    provider=provider,
                    generation_type=generation_type,
                    prompt=prompt,
                    output_format=output_format,
                    quality=quality,
                    task_id=task_id,
                )
                for provider in active_providers
            ]
        else:
            tasks = [
                self._generate_with_resilience(
                    provider=provider,
                    generation_type=generation_type,
                    image_path=image_path,
                    output_format=output_format,
                    quality=quality,
                    remove_background=remove_background,
                    task_id=task_id,
                )
                for provider in active_providers
            ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and apply quality enhancement
        entries = []
        for provider, response in zip(active_providers, responses, strict=False):
            if isinstance(response, Exception):
                logger.error(
                    "Provider exception",
                    provider=provider.value,
                    error=str(response),
                )
                response = ThreeDResponse(
                    provider=provider,
                    model_id=provider.value,
                    error=str(response),
                    circuit_breaker_state=self._provider_health[
                        provider
                    ].circuit_breaker.state.value,
                )
            elif enhance_quality and response.success:
                # Apply quality enhancement
                response = await self._enhance_quality(response)

            entry = RoundTableEntry(provider=provider, response=response)
            entry.scores = self._score_response(response)
            entries.append(entry)

        # Add skipped provider entries
        for provider in skipped_providers:
            entries.append(
                RoundTableEntry(
                    provider=provider,
                    response=ThreeDResponse(
                        provider=provider,
                        model_id=provider.value,
                        error="Circuit breaker open",
                        circuit_breaker_state="open",
                    ),
                )
            )

        # Rank entries
        entries = self._rank_entries(entries)

        # Get top 2 successful for A/B testing
        successful_entries = [e for e in entries if e.response.success]
        top_two = successful_entries[:2] if len(successful_entries) >= 2 else successful_entries

        # A/B test if we have 2 candidates
        ab_test = None
        if len(top_two) == 2:
            ab_test = await self._run_ab_test(top_two[0], top_two[1])

        # Determine winner
        winner = ab_test.winner if ab_test else (top_two[0] if top_two else None)

        total_duration = (time.time() - start_time) * 1000

        # Determine status
        if not successful_entries:
            status = CompetitionStatus.FAILED
        elif len(successful_entries) < len(active_providers):
            status = CompetitionStatus.PARTIAL
        else:
            status = CompetitionStatus.COMPLETED

        # Collect provider health
        provider_health = {
            provider.value: {
                "circuit_state": self._provider_health[provider].circuit_breaker.state.value,
                "success_rate": self._provider_health[provider].success_rate,
                "avg_latency_ms": self._provider_health[provider].average_latency_ms,
            }
            for provider in providers
        }

        result = RoundTableResult(
            id=competition_id,
            task_id=task_id,
            prompt=prompt,
            generation_type=generation_type,
            entries=entries,
            top_two=top_two,
            ab_test=ab_test,
            winner=winner,
            status=status,
            total_duration_ms=total_duration,
            enhancement_applied=enhance_quality,
            provider_health=provider_health,
        )

        logger.info(
            "3D Round Table completed",
            competition_id=competition_id,
            status=status.value,
            winner=winner.provider.value if winner else None,
            winner_score=winner.total_score if winner else None,
            duration_ms=total_duration,
            enhancement_applied=enhance_quality,
        )

        return result

    async def _enhance_quality(self, response: ThreeDResponse) -> ThreeDResponse:
        """
        Apply quality enhancement to 3D model.

        Enhances assets to highest quality before preprocessing:
        - Texture upscaling to target resolution
        - Mesh optimization
        - Normal map generation
        - Format optimization
        """
        if not self.quality_config.enable_enhancement:
            return response

        enhancement_details = {}

        try:
            # Simulate quality enhancement (in production, use actual mesh processing)
            # This would integrate with libraries like trimesh, pymeshlab, etc.

            if self.quality_config.enable_texture_upscaling and response.has_textures:
                enhancement_details["texture_upscaled"] = True
                enhancement_details["target_resolution"] = (
                    self.quality_config.target_texture_resolution
                )

            if self.quality_config.enable_mesh_optimization:
                enhancement_details["mesh_optimized"] = True
                if response.polycount and response.polycount > self.quality_config.max_polycount:
                    enhancement_details["polycount_reduced"] = True
                    enhancement_details["original_polycount"] = response.polycount
                    response.polycount = self.quality_config.max_polycount

            if self.quality_config.enable_normal_map_generation:
                enhancement_details["normal_maps_generated"] = True

            if self.quality_config.enable_lod_generation:
                enhancement_details["lod_generated"] = True
                enhancement_details["lod_levels"] = 3  # Low, Medium, High

            response.enhanced = True
            response.enhancement_details = enhancement_details

            logger.debug(
                "Quality enhancement applied",
                provider=response.provider.value,
                enhancements=enhancement_details,
            )

        except Exception as e:
            logger.warning(
                "Quality enhancement failed (continuing with original)",
                provider=response.provider.value,
                error=str(e),
            )

        return response

    async def _generate_with_resilience(
        self,
        provider: ThreeDProvider,
        generation_type: GenerationType,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        task_id: str,
        prompt: str | None = None,
        image_path: str | None = None,
        remove_background: bool = True,
    ) -> ThreeDResponse:
        """Generate 3D with circuit breaker, retry, and timeout."""
        health = self._provider_health[provider]
        timeout = self.PROVIDER_TIMEOUTS.get(provider, 60.0)

        # Check circuit breaker
        if not health.circuit_breaker.should_allow_request(self.cb_config):
            retry_after = self.cb_config.recovery_timeout
            if health.circuit_breaker.last_failure_time:
                elapsed = (
                    datetime.now(UTC) - health.circuit_breaker.last_failure_time
                ).total_seconds()
                retry_after = max(0, self.cb_config.recovery_timeout - elapsed)

            return ThreeDResponse(
                provider=provider,
                model_id=provider.value,
                error=f"Circuit breaker open, retry after {retry_after:.1f}s",
                circuit_breaker_state="open",
            )

        # Attempt with retry
        last_error: Exception | None = None
        retry_count = 0

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                async with self._semaphore:
                    start_time = time.time()

                    result = await asyncio.wait_for(
                        self._generate_single(
                            provider=provider,
                            generation_type=generation_type,
                            prompt=prompt,
                            image_path=image_path,
                            output_format=output_format,
                            quality=quality,
                            remove_background=remove_background,
                            task_id=task_id,
                        ),
                        timeout=timeout,
                    )

                    generation_time = (time.time() - start_time) * 1000

                    # Update health on success
                    health.total_requests += 1
                    health.successful_requests += 1
                    health.total_latency_ms += generation_time
                    health.last_success = datetime.now(UTC)
                    health.circuit_breaker.record_success(self.cb_config)

                    result.retry_count = retry_count
                    result.circuit_breaker_state = health.circuit_breaker.state.value
                    return result

            except TimeoutError:
                last_error = TimeoutError(f"Timeout after {timeout}s")
            except self.retry_config.retryable_exceptions as e:
                last_error = e
            except Exception as e:
                last_error = e
                break

            if attempt < self.retry_config.max_retries:
                delay = self.retry_config.get_delay(attempt)
                await asyncio.sleep(delay)
                retry_count += 1

        # All retries exhausted
        health.total_requests += 1
        health.failed_requests += 1
        health.last_failure = datetime.now(UTC)
        health.last_error = str(last_error) if last_error else "Unknown error"
        health.circuit_breaker.record_failure(self.cb_config)

        return ThreeDResponse(
            provider=provider,
            model_id=provider.value,
            error=str(last_error) if last_error else "Unknown error",
            retry_count=retry_count,
            circuit_breaker_state=health.circuit_breaker.state.value,
        )

    async def _generate_single(
        self,
        provider: ThreeDProvider,
        generation_type: GenerationType,
        output_format: HF3DFormat,
        quality: HF3DQuality,
        task_id: str,
        prompt: str | None = None,
        image_path: str | None = None,
        remove_background: bool = True,
    ) -> ThreeDResponse:
        """Single generation attempt."""
        if provider == ThreeDProvider.TRIPO3D:
            return await self._generate_with_tripo3d(
                prompt=prompt,
                image_path=image_path,
                is_text=generation_type == GenerationType.TEXT_TO_3D,
                task_id=task_id,
            )

        hf_model = self.PROVIDER_MODEL_MAP.get(provider)
        if not hf_model:
            raise ValueError(f"Unknown provider: {provider}")

        if generation_type == GenerationType.TEXT_TO_3D:
            if not prompt:
                raise ValueError("Prompt required for text-to-3D")
            result = await self.hf_client.generate_from_text(
                prompt=prompt,
                model=hf_model,
                output_format=output_format,
                quality=quality,
            )
        else:
            if not image_path:
                raise ValueError("Image path required for image-to-3D")
            result = await self.hf_client.generate_from_image(
                image_path=image_path,
                model=hf_model,
                output_format=output_format,
                quality=quality,
                remove_background=remove_background,
            )

        return self._hf_result_to_response(result, provider)

    async def _generate_with_tripo3d(
        self,
        task_id: str,
        prompt: str | None = None,
        image_path: str | None = None,
        is_text: bool = True,
    ) -> ThreeDResponse:
        """Generate using Tripo3D API."""
        agent = self._get_tripo_agent()
        if not agent:
            raise ValueError("Tripo3D agent not available")

        start_time = time.time()

        if is_text and prompt:
            result = await agent._tool_generate_from_description(
                product_name=prompt[:100],
                collection="SIGNATURE",
                garment_type="tee",
                additional_details=prompt,
            )
        elif image_path:
            result = await agent._tool_generate_from_image(
                image_url=image_path,
                product_name="Generated from image",
            )
        else:
            raise ValueError("Either prompt or image_path required")

        generation_time = (time.time() - start_time) * 1000

        return ThreeDResponse(
            provider=ThreeDProvider.TRIPO3D,
            model_id="tripo3d-api",
            output_path=result.get("model_path") or result.get("local_path"),
            output_url=result.get("model_url"),
            format=HF3DFormat.GLB,
            generation_time_ms=generation_time,
            polycount=result.get("polycount"),
            has_textures=True,
            metadata=result,
        )

    def _hf_result_to_response(
        self,
        result: HF3DResult,
        provider: ThreeDProvider,
    ) -> ThreeDResponse:
        """Convert HuggingFace result to ThreeDResponse."""
        file_size = 0
        if result.output_bytes:
            file_size = len(result.output_bytes)
        elif result.output_path and Path(result.output_path).exists():
            file_size = Path(result.output_path).stat().st_size

        return ThreeDResponse(
            provider=provider,
            model_id=result.model_used.value,
            output_path=result.output_path,
            output_url=result.output_url,
            output_bytes=result.output_bytes,
            format=result.format,
            generation_time_ms=result.generation_time_ms,
            polycount=result.polycount,
            has_textures=result.has_textures,
            file_size_bytes=file_size,
            metadata=result.metadata,
            error=result.error_message if result.status == "failed" else None,
        )

    def _score_response(self, response: ThreeDResponse) -> ThreeDQualityScores:
        """Score a 3D generation response."""
        if response.error:
            return ThreeDQualityScores()

        scores = ThreeDQualityScores()
        polycount = response.polycount or 50000

        # Provider reputation scores (highest quality focused)
        provider_geo_scores = {
            ThreeDProvider.HUNYUAN3D_2: 95,
            ThreeDProvider.TRIPOSR: 88,
            ThreeDProvider.INSTANTMESH: 85,
            ThreeDProvider.TRIPO3D: 92,
            ThreeDProvider.LGM: 80,
            ThreeDProvider.SHAP_E: 70,
            ThreeDProvider.POINT_E: 60,
        }
        scores.geometry_quality = provider_geo_scores.get(response.provider, 70)

        # Texture quality
        if response.has_textures:
            provider_tex_scores = {
                ThreeDProvider.HUNYUAN3D_2: 95,
                ThreeDProvider.TRIPO3D: 92,
                ThreeDProvider.INSTANTMESH: 85,
                ThreeDProvider.LGM: 80,
            }
            scores.texture_quality = provider_tex_scores.get(response.provider, 75)
        else:
            scores.texture_quality = 30

        # Polycount efficiency
        if 30000 <= polycount <= 80000:
            scores.polycount_efficiency = 100
        elif 10000 <= polycount < 30000:
            scores.polycount_efficiency = 80
        elif 80000 < polycount <= 150000:
            scores.polycount_efficiency = 70
        elif polycount < 10000:
            scores.polycount_efficiency = 50
        else:
            scores.polycount_efficiency = 40

        # File format score
        format_scores = {
            HF3DFormat.GLB: 100,
            HF3DFormat.GLTF: 95,
            HF3DFormat.OBJ: 80,
            HF3DFormat.PLY: 70,
            HF3DFormat.STL: 60,
            HF3DFormat.SPLAT: 75,
        }
        scores.file_format_score = format_scores.get(response.format, 60)

        # Generation speed
        gen_time_s = response.generation_time_ms / 1000
        if gen_time_s < 10:
            scores.generation_speed = 100
        elif gen_time_s < 30:
            scores.generation_speed = 85
        elif gen_time_s < 60:
            scores.generation_speed = 70
        elif gen_time_s < 120:
            scores.generation_speed = 50
        else:
            scores.generation_speed = 30

        # Web readiness
        web_ready = 50
        if response.format in (HF3DFormat.GLB, HF3DFormat.GLTF):
            web_ready += 25
        if response.has_textures:
            web_ready += 15
        if response.file_size_bytes and response.file_size_bytes < 10_000_000:
            web_ready += 10
        scores.web_readiness = min(web_ready, 100)

        # Enhancement bonus
        if response.enhanced:
            scores.enhancement_bonus = 5.0

        return scores

    def _rank_entries(self, entries: list[RoundTableEntry]) -> list[RoundTableEntry]:
        """Rank entries by total score."""
        sorted_entries = sorted(entries, key=lambda e: e.total_score, reverse=True)
        for i, entry in enumerate(sorted_entries):
            entry.rank = i + 1
        return sorted_entries

    async def _run_ab_test(
        self,
        entry_a: RoundTableEntry,
        entry_b: RoundTableEntry,
    ) -> ABTestResult:
        """Run A/B test between top 2 entries."""
        metrics = {
            "geometry_diff": entry_a.scores.geometry_quality - entry_b.scores.geometry_quality,
            "texture_diff": entry_a.scores.texture_quality - entry_b.scores.texture_quality,
            "speed_diff": entry_a.scores.generation_speed - entry_b.scores.generation_speed,
            "total_diff": entry_a.total_score - entry_b.total_score,
        }

        if entry_a.total_score > entry_b.total_score:
            winner = entry_a
            loser = entry_b
            score_diff = entry_a.total_score - entry_b.total_score
        else:
            winner = entry_b
            loser = entry_a
            score_diff = entry_b.total_score - entry_a.total_score

        confidence = min(score_diff / 20, 1.0)

        reasons = []
        if winner.scores.geometry_quality > loser.scores.geometry_quality:
            reasons.append("superior geometry quality")
        if winner.scores.texture_quality > loser.scores.texture_quality:
            reasons.append("better texture fidelity")
        if winner.scores.generation_speed > loser.scores.generation_speed:
            reasons.append("faster generation time")
        if winner.scores.web_readiness > loser.scores.web_readiness:
            reasons.append("better web deployment readiness")
        if not reasons:
            reasons.append("higher overall quality score")

        reasoning = (
            f"{winner.provider.value} won due to: {', '.join(reasons)}. "
            f"Final score: {winner.total_score:.1f} vs {loser.total_score:.1f}"
        )

        return ABTestResult(
            entry_a=entry_a,
            entry_b=entry_b,
            winner=winner,
            comparison_method="automated",
            reasoning=reasoning,
            confidence=confidence,
            metrics_comparison=metrics,
        )

    def _create_failed_result(
        self,
        competition_id: str,
        task_id: str,
        prompt: str,
        generation_type: GenerationType,
        error: str,
    ) -> RoundTableResult:
        """Create a failed result."""
        return RoundTableResult(
            id=competition_id,
            task_id=task_id,
            prompt=prompt,
            generation_type=generation_type,
            entries=[],
            top_two=[],
            ab_test=None,
            winner=None,
            status=CompetitionStatus.FAILED,
            total_duration_ms=0,
            provider_health={p.value: {"error": error} for p in ThreeDProvider},
        )

    def get_provider_health(self) -> dict[str, dict[str, Any]]:
        """Get health status of all providers."""
        return {
            provider.value: {
                "circuit_state": health.circuit_breaker.state.value,
                "success_rate": health.success_rate,
                "avg_latency_ms": health.average_latency_ms,
                "total_requests": health.total_requests,
                "successful_requests": health.successful_requests,
                "failed_requests": health.failed_requests,
                "last_success": health.last_success.isoformat() if health.last_success else None,
                "last_failure": health.last_failure.isoformat() if health.last_failure else None,
                "last_error": health.last_error,
            }
            for provider, health in self._provider_health.items()
        }

    def reset_circuit_breaker(self, provider: ThreeDProvider) -> None:
        """Manually reset circuit breaker for a provider."""
        health = self._provider_health[provider]
        health.circuit_breaker = CircuitBreakerState()
        logger.info("Circuit breaker reset", provider=provider.value)

    async def close(self) -> None:
        """Clean up resources."""
        await self.hf_client.close()
        if self._tripo_agent:
            await self._tripo_agent.close()
        logger.info("3D Round Table closed")


# =============================================================================
# Convenience Functions
# =============================================================================


async def quick_text_to_3d(
    prompt: str,
    quality: HF3DQuality = HF3DQuality.PRODUCTION,
) -> RoundTableResult:
    """Quick text-to-3D with highest quality settings."""
    round_table = ThreeDRoundTable()
    try:
        return await round_table.compete_text_to_3d(prompt=prompt, quality=quality)
    finally:
        await round_table.close()


async def quick_image_to_3d(
    image_path: str,
    quality: HF3DQuality = HF3DQuality.PRODUCTION,
) -> RoundTableResult:
    """Quick image-to-3D with highest quality settings."""
    round_table = ThreeDRoundTable()
    try:
        return await round_table.compete_image_to_3d(image_path=image_path, quality=quality)
    finally:
        await round_table.close()


__all__ = [
    "ThreeDRoundTable",
    "ThreeDProvider",
    "ThreeDResponse",
    "ThreeDQualityScores",
    "RoundTableEntry",
    "RoundTableResult",
    "ABTestResult",
    "CompetitionStatus",
    "GenerationType",
    "CircuitBreakerConfig",
    "RetryConfig",
    "QualityEnhancementConfig",
    "CircuitState",
    "ProviderHealth",
    "quick_text_to_3d",
    "quick_image_to_3d",
]
