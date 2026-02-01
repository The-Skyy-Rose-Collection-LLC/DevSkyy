# services/three_d/tripo_provider.py
"""Tripo3D Provider Adapter.

Wraps the existing TripoAssetAgent for the unified 3D provider interface.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from services.three_d.provider_interface import (
    OutputFormat,
    ProviderHealth,
    ProviderStatus,
    ThreeDCapability,
    ThreeDGenerationError,
    ThreeDProviderError,
    ThreeDRequest,
    ThreeDResponse,
    ThreeDTimeoutError,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================


@dataclass
class TripoProviderConfig:
    """Tripo3D provider configuration."""

    api_key: str = field(
        default_factory=lambda: os.getenv("TRIPO_API_KEY", "") or os.getenv("TRIPO3D_API_KEY", "")
    )
    output_dir: str = field(
        default_factory=lambda: os.getenv("THREE_D_OUTPUT_DIR", "./assets/3d-models-generated")
    )
    timeout_seconds: float = 300.0

    @classmethod
    def from_env(cls) -> TripoProviderConfig:
        """Create config from environment."""
        return cls()


# =============================================================================
# Provider Implementation
# =============================================================================


class TripoProvider:
    """Tripo3D generation provider adapter.

    Wraps the existing TripoAssetAgent to provide a unified interface
    for the 3D provider factory.

    Usage:
        provider = TripoProvider()
        response = await provider.generate_from_text(
            ThreeDRequest(
                prompt="luxury hoodie",
                collection="BLACK_ROSE",
                garment_type="hoodie",
            )
        )
    """

    def __init__(self, config: TripoProviderConfig | None = None) -> None:
        self.config = config or TripoProviderConfig.from_env()
        self._agent = None

    @property
    def name(self) -> str:
        """Provider name identifier."""
        return "tripo"

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        """List of supported capabilities."""
        return [
            ThreeDCapability.TEXT_TO_3D,
            ThreeDCapability.IMAGE_TO_3D,
            ThreeDCapability.TEXTURE_GENERATION,
        ]

    async def _get_agent(self):
        """Get or create Tripo agent."""
        if self._agent is None:
            # Lazy import to avoid circular dependencies
            from agents.tripo_agent import TripoAssetAgent, TripoConfig

            tripo_config = TripoConfig(
                api_key=self.config.api_key,
                output_dir=self.config.output_dir,
                timeout=self.config.timeout_seconds,
            )
            self._agent = TripoAssetAgent(config=tripo_config)

        return self._agent

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID."""
        return str(uuid.uuid4())

    async def generate_from_text(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from text prompt.

        Uses SkyyRose brand context for enhanced prompts.

        Args:
            request: ThreeDRequest with prompt and optional collection/garment_type

        Returns:
            ThreeDResponse with generation result
        """
        correlation_id = request.correlation_id or self._generate_correlation_id()
        start_time = time.time()
        task_id = f"tripo_txt_{uuid.uuid4().hex[:12]}"

        if not request.prompt:
            raise ThreeDProviderError(
                "Text prompt is required for text-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from text via Tripo3D",
            extra={
                "correlation_id": correlation_id,
                "collection": request.collection,
                "garment_type": request.garment_type,
            },
        )

        try:
            agent = await self._get_agent()

            # Call the agent's tool method directly
            result = await agent._tool_generate_from_text(
                product_name=request.product_name or "Product",
                collection=request.collection or "SIGNATURE",
                garment_type=request.garment_type or "tee",
                additional_details=request.prompt,
                output_format=request.output_format.value,
            )

            duration = time.time() - start_time

            if not result:
                raise ThreeDGenerationError(
                    "Tripo3D returned no result",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            return ThreeDResponse(
                success=True,
                task_id=result.get("task_id", task_id),
                status="completed",
                model_url=result.get("model_url"),
                model_path=result.get("model_path"),
                output_format=OutputFormat(result.get("format", request.output_format.value)),
                provider=self.name,
                duration_seconds=result.get("duration_seconds", duration),
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "product_name": request.product_name,
                    "collection": request.collection,
                    "garment_type": request.garment_type,
                    "prompt": request.prompt,
                    **result.get("metadata", {}),
                },
            )

        except TimeoutError as e:
            raise ThreeDTimeoutError(
                f"Tripo3D generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except (RuntimeError, ValueError, PermissionError, ConnectionError) as e:
            raise ThreeDProviderError(
                f"Tripo3D error: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=isinstance(e, ConnectionError),
            ) from e

    async def generate_from_image(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from image.

        Args:
            request: ThreeDRequest with image_url or image_path set

        Returns:
            ThreeDResponse with generation result
        """
        correlation_id = request.correlation_id or self._generate_correlation_id()
        start_time = time.time()
        task_id = f"tripo_img_{uuid.uuid4().hex[:12]}"

        image_source = request.get_image_source()
        if not image_source:
            raise ThreeDProviderError(
                "Image URL or path is required for image-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from image via Tripo3D",
            extra={
                "correlation_id": correlation_id,
                "image_source": image_source[:100],
            },
        )

        try:
            agent = await self._get_agent()

            # Call the agent's tool method directly
            result = await agent._tool_generate_from_image(
                image_path=image_source,
                product_name=request.product_name or "Product",
                output_format=request.output_format.value,
            )

            duration = time.time() - start_time

            if not result:
                raise ThreeDGenerationError(
                    "Tripo3D returned no result",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            return ThreeDResponse(
                success=True,
                task_id=result.get("task_id", task_id),
                status="completed",
                model_url=result.get("model_url"),
                model_path=result.get("model_path"),
                output_format=OutputFormat(result.get("format", request.output_format.value)),
                provider=self.name,
                duration_seconds=result.get("duration_seconds", duration),
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "product_name": request.product_name,
                    "image_source": image_source,
                    **result.get("metadata", {}),
                },
            )

        except TimeoutError as e:
            raise ThreeDTimeoutError(
                f"Tripo3D generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except FileNotFoundError as e:
            raise ThreeDProviderError(
                f"Image file not found: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=False,
            ) from e

        except (RuntimeError, ValueError, PermissionError, ConnectionError) as e:
            raise ThreeDProviderError(
                f"Tripo3D error: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=isinstance(e, ConnectionError),
            ) from e

    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability."""
        start_time = time.time()

        try:
            if not self.config.api_key:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.UNAVAILABLE,
                    capabilities=self.capabilities,
                    last_check=datetime.now(UTC),
                    error_message="TRIPO_API_KEY not configured",
                )

            # Check if Tripo SDK is available
            try:
                from tripo3d import TripoClient

                TRIPO_SDK_AVAILABLE = True
            except ImportError:
                TRIPO_SDK_AVAILABLE = False

            if not TRIPO_SDK_AVAILABLE:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.UNAVAILABLE,
                    capabilities=self.capabilities,
                    last_check=datetime.now(UTC),
                    error_message="tripo3d SDK not installed",
                )

            latency = (time.time() - start_time) * 1000

            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.AVAILABLE,
                capabilities=self.capabilities,
                latency_ms=latency,
                last_check=datetime.now(UTC),
            )

        except Exception as e:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.UNAVAILABLE,
                capabilities=self.capabilities,
                last_check=datetime.now(UTC),
                error_message=str(e),
            )

    async def close(self) -> None:
        """Close provider resources."""
        if self._agent:
            await self._agent.close()
            self._agent = None


__all__ = [
    "TripoProvider",
    "TripoProviderConfig",
]
