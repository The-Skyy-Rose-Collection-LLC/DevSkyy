# services/three_d/replicate_provider.py
"""Replicate 3D Provider Implementation.

Wraps the existing ReplicateClient for 3D model generation.

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
from pathlib import Path

import httpx

from services.ml.replicate_client import (
    ReplicateClient,
    ReplicateConfig,
    ReplicateError,
    ReplicateTimeoutError,
)
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
class ReplicateProviderConfig:
    """Replicate provider configuration."""

    api_token: str = field(default_factory=lambda: os.getenv("REPLICATE_API_TOKEN", ""))

    # Model versions
    image_to_3d_model: str = field(
        default_factory=lambda: os.getenv(
            "REPLICATE_IMAGE_TO_3D_MODEL",
            "adirik/wonder3d:e6a3eda1a67e8a9b915e45e1d7b3f7e3",
        )
    )
    text_to_3d_model: str = field(
        default_factory=lambda: os.getenv(
            "REPLICATE_TEXT_TO_3D_MODEL",
            "cjwbw/shap-e:5957069d5c509126a73c7cb68abcddbb985aeefa",
        )
    )

    # Timeouts
    timeout_seconds: float = 300.0
    poll_interval: float = 2.0

    # Output
    output_dir: str = field(
        default_factory=lambda: os.getenv("THREE_D_OUTPUT_DIR", "./assets/3d-models-generated")
    )

    @classmethod
    def from_env(cls) -> ReplicateProviderConfig:
        """Create config from environment."""
        return cls()


# =============================================================================
# Provider Implementation
# =============================================================================


class ReplicateProvider:
    """Replicate 3D generation provider.

    Uses Replicate API for image-to-3D and text-to-3D generation.
    Wraps existing ReplicateClient with I3DProvider interface.

    Usage:
        provider = ReplicateProvider()
        response = await provider.generate_from_image(
            ThreeDRequest(image_url="https://...", product_name="Hoodie")
        )
    """

    def __init__(self, config: ReplicateProviderConfig | None = None) -> None:
        self.config = config or ReplicateProviderConfig.from_env()
        self._client: ReplicateClient | None = None
        self._http_client: httpx.AsyncClient | None = None

        # Ensure output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        """Provider name identifier."""
        return "replicate"

    @property
    def capabilities(self) -> list[ThreeDCapability]:
        """List of supported capabilities."""
        return [
            ThreeDCapability.IMAGE_TO_3D,
            ThreeDCapability.TEXT_TO_3D,
        ]

    async def _get_client(self) -> ReplicateClient:
        """Get or create Replicate client."""
        if self._client is None:
            replicate_config = ReplicateConfig(
                api_token=self.config.api_token,
                timeout=self.config.timeout_seconds,
                poll_interval=self.config.poll_interval,
                image_to_3d_model=self.config.image_to_3d_model,
            )
            self._client = ReplicateClient(replicate_config)
            await self._client.connect()
        return self._client

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client for downloads."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    def _generate_correlation_id(self) -> str:
        """Generate correlation ID."""
        return str(uuid.uuid4())

    async def _download_model(
        self,
        url: str,
        output_format: OutputFormat,
        correlation_id: str,
    ) -> str:
        """Download generated model to local storage."""
        http_client = await self._get_http_client()

        try:
            response = await http_client.get(url)
            response.raise_for_status()

            # Generate output path
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"replicate_{timestamp}_{correlation_id[:8]}.{output_format.value}"
            output_path = Path(self.config.output_dir) / filename

            output_path.write_bytes(response.content)
            logger.info(f"Downloaded model to {output_path}")

            return str(output_path)

        except httpx.HTTPError as e:
            raise ThreeDProviderError(
                f"Failed to download model: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=True,
            ) from e

    async def generate_from_text(
        self,
        request: ThreeDRequest,
    ) -> ThreeDResponse:
        """Generate 3D model from text prompt.

        Args:
            request: ThreeDRequest with prompt set

        Returns:
            ThreeDResponse with generation result
        """
        correlation_id = request.correlation_id or self._generate_correlation_id()
        start_time = time.time()
        task_id = f"rep_txt_{uuid.uuid4().hex[:12]}"

        if not request.prompt:
            raise ThreeDProviderError(
                "Text prompt is required for text-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from text via Replicate",
            extra={
                "correlation_id": correlation_id,
                "prompt_length": len(request.prompt),
            },
        )

        try:
            client = await self._get_client()

            # Run prediction
            prediction = await client.run_prediction(
                self.config.text_to_3d_model,
                {"prompt": request.prompt},
                correlation_id=correlation_id,
            )

            if not prediction.succeeded:
                raise ThreeDGenerationError(
                    f"Replicate text-to-3D failed: {prediction.error}",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            # Extract output URL
            output = prediction.output
            if isinstance(output, list):
                model_url = output[0] if output else None
            elif isinstance(output, str):
                model_url = output
            else:
                model_url = None

            if not model_url:
                raise ThreeDGenerationError(
                    "No model URL in Replicate response",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            # Download model
            model_path = await self._download_model(
                model_url,
                request.output_format,
                correlation_id,
            )

            duration = time.time() - start_time

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=model_url,
                model_path=model_path,
                output_format=request.output_format,
                provider=self.name,
                duration_seconds=duration,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "prompt": request.prompt,
                    "prediction_id": prediction.id,
                    "model": self.config.text_to_3d_model,
                },
            )

        except ReplicateTimeoutError as e:
            raise ThreeDTimeoutError(
                f"Replicate generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except ReplicateError as e:
            raise ThreeDProviderError(
                f"Replicate error: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=e.retryable,
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
        task_id = f"rep_img_{uuid.uuid4().hex[:12]}"

        image_source = request.get_image_source()
        if not image_source:
            raise ThreeDProviderError(
                "Image URL or path is required for image-to-3D generation",
                provider=self.name,
                correlation_id=correlation_id,
            )

        logger.info(
            "Generating 3D from image via Replicate",
            extra={
                "correlation_id": correlation_id,
                "image_source": image_source[:100],
            },
        )

        try:
            client = await self._get_client()

            # Run prediction
            prediction = await client.image_to_3d(
                image_source,
                output_format=request.output_format.value,
                correlation_id=correlation_id,
            )

            if not prediction.succeeded:
                raise ThreeDGenerationError(
                    f"Replicate image-to-3D failed: {prediction.error}",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            # Extract output URL
            output = prediction.output
            if isinstance(output, list):
                model_url = output[0] if output else None
            elif isinstance(output, str):
                model_url = output
            else:
                model_url = None

            if not model_url:
                raise ThreeDGenerationError(
                    "No model URL in Replicate response",
                    provider=self.name,
                    task_id=task_id,
                    correlation_id=correlation_id,
                )

            # Download model
            model_path = await self._download_model(
                model_url,
                request.output_format,
                correlation_id,
            )

            duration = time.time() - start_time

            return ThreeDResponse(
                success=True,
                task_id=task_id,
                status="completed",
                model_url=model_url,
                model_path=model_path,
                output_format=request.output_format,
                provider=self.name,
                duration_seconds=duration,
                created_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                correlation_id=correlation_id,
                metadata={
                    "image_source": image_source,
                    "prediction_id": prediction.id,
                    "model": self.config.image_to_3d_model,
                },
            )

        except ReplicateTimeoutError as e:
            raise ThreeDTimeoutError(
                f"Replicate generation timed out: {e}",
                provider=self.name,
                timeout_seconds=self.config.timeout_seconds,
                correlation_id=correlation_id,
            ) from e

        except ReplicateError as e:
            raise ThreeDProviderError(
                f"Replicate error: {e}",
                provider=self.name,
                correlation_id=correlation_id,
                cause=e,
                retryable=e.retryable,
            ) from e

    async def health_check(self) -> ProviderHealth:
        """Check provider health and availability."""
        start_time = time.time()

        try:
            if not self.config.api_token:
                return ProviderHealth(
                    provider=self.name,
                    status=ProviderStatus.UNAVAILABLE,
                    capabilities=self.capabilities,
                    last_check=datetime.now(UTC),
                    error_message="REPLICATE_API_TOKEN not configured",
                )

            # Simple connectivity check
            client = await self._get_client()
            await client.connect()

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
        if self._client:
            await self._client.close()
            self._client = None

        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None


__all__ = [
    "ReplicateProvider",
    "ReplicateProviderConfig",
]
