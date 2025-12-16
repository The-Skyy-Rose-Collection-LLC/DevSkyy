"""
FASHN Virtual Try-On Agent
==========================

Generate virtual try-on images using FASHN API.

Features:
- Virtual try-on (garment on model)
- AI model generation
- Product-to-model photography
- Background removal

API Documentation: https://docs.fashn.ai/
SDK: pip install fashn

Pricing (as of Dec 2025):
- Pay-as-you-go: $0.075 per image
- Monthly plans available

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from pydantic import BaseModel, Field

from base import (
    AgentCapability,
    AgentConfig,
    ExecutionResult,
    LLMCategory,
    PlanStep,
    RetrievalContext,
    SuperAgent,
    ValidationResult,
)
from runtime.tools import (
    ToolCallContext,
    ToolCategory,
    ToolRegistry,
    ToolSeverity,
    ToolSpec,
    get_tool_registry,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Enums
# =============================================================================


class GarmentCategory(str, Enum):
    """Garment categories for try-on."""

    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    FULL_BODY = "full_body"


class TryOnMode(str, Enum):
    """Try-on mode."""

    QUALITY = "quality"  # Higher quality, slower
    BALANCED = "balanced"  # Balance of speed and quality
    FAST = "fast"  # Faster, lower quality


class FashnTaskStatus(str, Enum):
    """Task status."""

    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class FashnConfig:
    """FASHN API configuration."""

    api_key: str = field(default_factory=lambda: os.getenv("FASHN_API_KEY", ""))
    base_url: str = "https://api.fashn.ai/v1"
    timeout: float = 120.0
    poll_interval: float = 1.0
    max_retries: int = 3
    output_dir: str = "./generated_assets/tryon"

    # Default output size
    output_width: int = 576
    output_height: int = 864

    @classmethod
    def from_env(cls) -> FashnConfig:
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("FASHN_API_KEY", ""),
            output_dir=os.getenv("FASHN_OUTPUT_DIR", "./generated_assets/tryon"),
        )


# =============================================================================
# Models
# =============================================================================


class FashnTask(BaseModel):
    """FASHN task."""

    id: str
    status: FashnTaskStatus
    output: list[str] | None = None
    error: str | None = None
    created_at: str | None = None

    # Additional metadata
    input_garment: str | None = None
    input_model: str | None = None


class TryOnResult(BaseModel):
    """Virtual try-on result."""

    task_id: str
    image_url: str
    image_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Tracking
    duration_seconds: float = 0.0
    retries: int = 0


class ModelGenerationResult(BaseModel):
    """AI model generation result."""

    task_id: str
    image_url: str
    image_path: str
    prompt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# FASHN Agent
# =============================================================================


class FashnTryOnAgent(SuperAgent):
    """
    FASHN Virtual Try-On Agent.

    Generate virtual try-on images for SkyyRose products.

    Usage:
        agent = FashnTryOnAgent()

        # Run virtual try-on workflow
        result = await agent.run({
            "action": "virtual_tryon",
            "model_image": "path/to/model.jpg",
            "garment_image": "path/to/garment.jpg",
            "category": "tops",
        })

        # Generate AI model
        result = await agent.run({
            "action": "create_model",
            "prompt": "Fashion model, professional, studio lighting",
            "gender": "female",
        })
    """

    def __init__(
        self,
        config: FashnConfig | None = None,
        registry: ToolRegistry | None = None,
    ) -> None:
        agent_config = AgentConfig(
            name="fashn_tryon",
            description="FASHN Virtual Try-On Agent for fashion visualization",
            version="1.0.0",
            capabilities={
                AgentCapability.VIRTUAL_TRYON,
                AgentCapability.IMAGE_GENERATION,
            },
            llm_category=LLMCategory.CATEGORY_B,
            tool_category=ToolCategory.MEDIA,
            default_timeout=120.0,
        )

        super().__init__(agent_config, registry or get_tool_registry())

        self.fashn_config = config or FashnConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

        # Ensure output directory
        Path(self.fashn_config.output_dir).mkdir(parents=True, exist_ok=True)

    def _register_tools(self) -> None:
        """Register FASHN-specific tools."""
        self.registry.register(
            ToolSpec(
                name="fashn_virtual_tryon",
                description="Generate virtual try-on image using FASHN API",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=120.0,
                idempotent=False,
            ),
            self._tool_virtual_tryon,
        )

        self.registry.register(
            ToolSpec(
                name="fashn_create_model",
                description="Generate AI fashion model using FASHN API",
                category=ToolCategory.MEDIA,
                severity=ToolSeverity.MEDIUM,
                timeout_seconds=120.0,
            ),
            self._tool_create_model,
        )

    # -------------------------------------------------------------------------
    # SuperAgent Implementation
    # -------------------------------------------------------------------------

    async def _plan(
        self,
        request: dict[str, Any],
        context: ToolCallContext,
    ) -> list[PlanStep]:
        """Create execution plan based on request action."""
        action = request.get("action", "virtual_tryon")

        if action == "virtual_tryon":
            return [
                PlanStep(
                    tool_name="fashn_virtual_tryon",
                    description="Generate virtual try-on image",
                    inputs={
                        "model_image": request.get("model_image"),
                        "garment_image": request.get("garment_image"),
                        "category": request.get("category", GarmentCategory.TOPS.value),
                        "mode": request.get("mode", TryOnMode.BALANCED.value),
                    },
                    priority=0,
                ),
            ]
        elif action == "create_model":
            return [
                PlanStep(
                    tool_name="fashn_create_model",
                    description="Generate AI fashion model",
                    inputs={
                        "prompt": request.get("prompt", "Fashion model"),
                        "gender": request.get("gender", "neutral"),
                    },
                    priority=0,
                ),
            ]
        else:
            raise ValueError(f"Unknown action: {action}")

    async def _retrieve(
        self,
        request: dict[str, Any],
        plan: list[PlanStep],
        context: ToolCallContext,
    ) -> RetrievalContext:
        """Retrieve context (no RAG needed for FASHN)."""
        return RetrievalContext(
            query=f"FASHN {request.get('action', 'tryon')}",
            documents=[],
        )

    async def _execute_step(
        self,
        step: PlanStep,
        retrieval_context: RetrievalContext,
        context: ToolCallContext,
    ) -> ExecutionResult:
        """Execute a single step."""
        started_at = datetime.now(UTC)

        try:
            result = await self.registry.execute(
                step.tool_name,
                step.inputs,
                context,
            )

            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=result.success,
                result=result.result,
                error=result.error,
                duration_seconds=result.duration_seconds,
                started_at=started_at,
                completed_at=datetime.now(UTC),
                retries=result.retries,
            )
        except Exception as e:
            return ExecutionResult(
                tool_name=step.tool_name,
                step_id=step.step_id,
                success=False,
                error=str(e),
                error_type=type(e).__name__,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )

    async def _validate(
        self,
        results: list[ExecutionResult],
        context: ToolCallContext,
    ) -> ValidationResult:
        """Validate execution results."""
        validation = ValidationResult(is_valid=True)

        for result in results:
            if not result.success:
                validation.add_error(f"{result.tool_name} failed: {result.error}")
            elif result.result and isinstance(result.result, dict):
                # Validate output has required fields
                if "image_path" not in result.result and "task_id" not in result.result:
                    validation.add_warning(f"{result.tool_name} missing expected output fields")

        if not validation.errors:
            validation.quality_score = 1.0
            validation.confidence_score = 0.95

        return validation

    async def _emit(
        self,
        results: list[ExecutionResult],
        validation: ValidationResult,
        context: ToolCallContext,
    ) -> dict[str, Any]:
        """Emit final structured output."""
        output = {
            "status": "success" if validation.is_valid else "error",
            "agent": self.name,
            "request_id": context.request_id,
            "validation": validation.to_dict(),
        }

        if results:
            output["results"] = [r.to_dict() for r in results]

            # Extract main result
            main_result = results[0]
            if main_result.success and main_result.result:
                output["data"] = main_result.result

        return output

    # -------------------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------------------

    async def _tool_virtual_tryon(
        self,
        model_image: str,
        garment_image: str,
        category: str = "tops",
        mode: str = "balanced",
    ) -> dict[str, Any]:
        """Execute virtual try-on."""
        await self._ensure_session()

        # Encode images
        model_data = await self._encode_image(model_image)
        garment_data = await self._encode_image(garment_image)

        # Create prediction
        response = await self._api_request(
            "POST",
            "/run",
            {
                "model_image": model_data,
                "garment_image": garment_data,
                "category": category,
                "mode": mode,
                "output_width": self.fashn_config.output_width,
                "output_height": self.fashn_config.output_height,
            },
        )

        prediction_id = response.get("id")
        if not prediction_id:
            raise ValueError("No prediction ID returned")

        # Poll for result
        task = await self._poll_prediction(prediction_id)

        # Download result
        if task.output:
            image_url = task.output[0]
            filename = f"tryon_{prediction_id}_{uuid.uuid4().hex[:8]}.png"
            image_path = await self._download_image(image_url, filename)

            return TryOnResult(
                task_id=prediction_id,
                image_url=image_url,
                image_path=image_path,
                metadata={
                    "category": category,
                    "mode": mode,
                    "model_image": model_image,
                    "garment_image": garment_image,
                },
            ).model_dump()

        raise ValueError("No output generated")

    async def _tool_create_model(
        self,
        prompt: str,
        gender: str = "neutral",
    ) -> dict[str, Any]:
        """Generate AI fashion model."""
        await self._ensure_session()

        # Build model prompt
        full_prompt = (
            f"Fashion model, {gender}, {prompt}, professional studio lighting, full body shot"
        )

        response = await self._api_request(
            "POST",
            "/generate-model",
            {
                "prompt": full_prompt,
                "output_width": self.fashn_config.output_width,
                "output_height": self.fashn_config.output_height,
            },
        )

        prediction_id = response.get("id")
        if not prediction_id:
            raise ValueError("No prediction ID returned")

        task = await self._poll_prediction(prediction_id)

        if task.output:
            image_url = task.output[0]
            filename = f"model_{prediction_id}_{uuid.uuid4().hex[:8]}.png"
            image_path = await self._download_image(image_url, filename)

            return ModelGenerationResult(
                task_id=prediction_id,
                image_url=image_url,
                image_path=image_path,
                prompt=full_prompt,
                metadata={"gender": gender},
            ).model_dump()

        raise ValueError("No output generated")

    # -------------------------------------------------------------------------
    # HTTP Client Methods
    # -------------------------------------------------------------------------

    async def _ensure_session(self) -> None:
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.fashn_config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.fashn_config.timeout),
            )

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 data URL."""
        async with aiofiles.open(image_path, "rb") as f:
            data = await f.read()

        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = mime_types.get(ext, "image/jpeg")

        b64 = base64.b64encode(data).decode()
        return f"data:{mime_type};base64,{b64}"

    async def _api_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make API request with retry logic."""
        await self._ensure_session()

        url = f"{self.fashn_config.base_url}/{endpoint.lstrip('/')}"
        last_error: Exception | None = None

        for attempt in range(self.fashn_config.max_retries):
            try:
                async with self._session.request(method, url, json=data) as response:
                    result = await response.json()

                    if response.status >= 400:
                        error_msg = result.get("error", {}).get("message", str(result))
                        raise Exception(f"FASHN API error ({response.status}): {error_msg}")

                    return result
            except aiohttp.ClientError as e:
                last_error = e
                if attempt < self.fashn_config.max_retries - 1:
                    await asyncio.sleep(2**attempt)

        raise last_error or Exception("API request failed")

    async def _poll_prediction(self, prediction_id: str) -> FashnTask:
        """Poll prediction until complete."""
        while True:
            result = await self._api_request("GET", f"/predictions/{prediction_id}")

            status = FashnTaskStatus(result.get("status", "processing"))

            if status == FashnTaskStatus.SUCCEEDED:
                output = result.get("output", [])
                return FashnTask(
                    id=prediction_id,
                    status=status,
                    output=output if isinstance(output, list) else [output],
                )

            if status == FashnTaskStatus.FAILED:
                error = result.get("error", "Unknown error")
                raise Exception(f"Prediction failed: {error}")

            if status == FashnTaskStatus.CANCELED:
                raise Exception("Prediction was canceled")

            logger.debug(f"Prediction {prediction_id}: {status.value}")
            await asyncio.sleep(self.fashn_config.poll_interval)

    async def _download_image(self, url: str, filename: str) -> str:
        """Download image to output directory."""
        await self._ensure_session()

        filepath = Path(self.fashn_config.output_dir) / filename

        async with self._session.get(url) as response:
            if response.status >= 400:
                raise Exception(f"Download failed: {response.status}")

            async with aiofiles.open(filepath, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        logger.info(f"Downloaded: {filepath}")
        return str(filepath)


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "FashnTryOnAgent",
    "FashnConfig",
    "FashnTask",
    "TryOnResult",
    "ModelGenerationResult",
    "GarmentCategory",
    "TryOnMode",
    "FashnTaskStatus",
]
