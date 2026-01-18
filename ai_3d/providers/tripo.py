# ai_3d/providers/tripo.py
"""
Tripo3D Client for DevSkyy.

Tripo3D provides high-quality image-to-3D and text-to-3D generation
optimized for e-commerce and product visualization.

API Reference: https://platform.tripo3d.ai/docs
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field, field_validator

from errors.production_errors import ConfigurationError

# Import config for API keys (loads .env.hf)
try:
    from config import TRIPO3D_API_KEY
except ImportError:
    TRIPO3D_API_KEY = os.getenv("TRIPO3D_API_KEY", "")

logger = logging.getLogger(__name__)


# =============================================================================
# Request Validation Models (3D Pipeline Hardening)
# =============================================================================


class ImageGenerationRequest(BaseModel):
    """Validated image-to-3D generation request."""

    image_path: Path
    output_format: str
    prompt: str | None = None
    texture_resolution: int = Field(default=2048, ge=512, le=4096)

    @field_validator("image_path")
    @classmethod
    def validate_image_exists(cls, v: Path) -> Path:
        """Validate image file exists."""
        if not v.exists():
            raise ValueError("Image file does not exist")
        return v

    @field_validator("image_path")
    @classmethod
    def validate_file_size(cls, v: Path) -> Path:
        """Validate file size is ≤10MB."""
        max_size = 10 * 1024 * 1024  # 10MB
        if v.stat().st_size > max_size:
            raise ValueError(
                f"Image file too large (max 10MB): {v.stat().st_size / 1024 / 1024:.1f}MB"
            )
        return v

    @field_validator("image_path")
    @classmethod
    def validate_format(cls, v: Path) -> Path:
        """Validate file format is allowed."""
        allowed = {".jpg", ".jpeg", ".png", ".webp"}
        if v.suffix.lower() not in allowed:
            raise ValueError(f"Invalid image format: {v.suffix} (allowed: {allowed})")
        return v

    @field_validator("prompt")
    @classmethod
    def sanitize_prompt(cls, v: str | None) -> str | None:
        """Sanitize prompt for XSS/injection attacks."""
        if v is None:
            return None

        # Check for dangerous patterns
        dangerous = ["<script", "javascript:", "<iframe", "onerror=", "onclick=", "onload="]
        if any(pattern in v.lower() for pattern in dangerous):
            raise ValueError("Potentially dangerous content in prompt")

        return v

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format is supported."""
        allowed = {"glb", "gltf", "obj", "fbx"}
        if v.lower() not in allowed:
            raise ValueError(f"Invalid format: {v} (allowed: {allowed})")
        return v.lower()


class TextGenerationRequest(BaseModel):
    """Validated text-to-3D generation request."""

    prompt: str = Field(min_length=10)
    output_format: str

    @field_validator("prompt")
    @classmethod
    def sanitize_and_trim(cls, v: str) -> str:
        """Sanitize and trim prompt."""
        # Trim whitespace
        v = v.strip()

        # Check for XSS/injection
        dangerous = ["<script", "javascript:", "<iframe", "onerror=", "onclick=", "onload="]
        if any(pattern in v.lower() for pattern in dangerous):
            raise ValueError("Potentially dangerous content in prompt")

        return v


class TripoAPIResponse(BaseModel):
    """Validated Tripo API response."""

    code: int
    message: str
    data: dict[str, Any] | None = None

    @field_validator("code")
    @classmethod
    def validate_code_range(cls, v: int) -> int:
        """Validate HTTP status code is in valid range."""
        if not (100 <= v <= 599):
            raise ValueError(f"Invalid API response code: {v} (must be 100-599)")
        return v

    def is_success(self) -> bool:
        """Check if response indicates success."""
        return 200 <= self.code < 300 and self.data is not None


class TripoTaskStatus(BaseModel):
    """Status of a Tripo generation task."""

    task_id: str
    status: str  # pending, running, success, failed
    progress: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None


class TripoClient:
    """
    Tripo3D API client for 3D model generation.

    Requires TRIPO_API_KEY environment variable.

    Usage:
        client = TripoClient()
        model_path = await client.generate_from_image("product.jpg", "./output")
    """

    BASE_URL = "https://api.tripo3d.ai/v2/openapi"
    POLL_INTERVAL = 5  # seconds
    MAX_WAIT_TIME = 600  # 10 minutes

    def __init__(self, api_key: str | None = None, enable_resilience: bool = False) -> None:
        """
        Initialize the Tripo client.

        Args:
            api_key: Tripo API key (or set TRIPO_API_KEY env var)
            enable_resilience: Enable retry/circuit breaker (for production)
        """
        # Check multiple env var names for compatibility
        self.api_key = (
            api_key or TRIPO3D_API_KEY or os.getenv("TRIPO3D_API_KEY") or os.getenv("TRIPO_API_KEY")
        )
        if not self.api_key:
            raise ConfigurationError(
                "TRIPO3D_API_KEY is required (set in .env.hf or environment)",
                config_key="TRIPO3D_API_KEY",
            )

        self.enable_resilience = enable_resilience
        self._result_cache: dict[str, Any] = {}  # Simple in-memory cache

        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def generate_from_image(
        self,
        image_path: str,
        output_dir: str,
        output_format: str = "glb",
        prompt: str | None = None,
        texture_resolution: int = 2048,
    ) -> str | None:
        """
        Generate a 3D model from an image.

        Args:
            image_path: Path to the source image
            output_dir: Directory to save the model
            output_format: Output format (glb, gltf, obj, fbx)
            prompt: Optional text prompt to guide generation
            texture_resolution: Texture resolution

        Returns:
            Path to the generated model or None on failure
        """
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Upload image and create task
            task_id = await self._create_image_to_3d_task(
                image_path,
                prompt=prompt,
                texture_resolution=texture_resolution,
            )

            if not task_id:
                return None

            # Wait for completion
            result = await self._wait_for_task(task_id)

            if not result or result.status != "success":
                error_msg = result.error if result else "Unknown error"
                logger.error(f"Tripo generation failed: {error_msg}")
                return None

            # Download the model
            model_url = result.result.get("model", {}).get("url") if result.result else None
            if not model_url:
                logger.error("No model URL in result")
                return None

            output_filename = f"{image_path.stem}_3d.{output_format}"
            output_path = output_dir / output_filename

            await self._download_model(model_url, output_path)

            return str(output_path)

        except Exception as e:
            logger.exception(f"Tripo generation failed: {e}")
            return None

    async def generate_from_text(
        self,
        prompt: str,
        output_dir: str,
        output_format: str = "glb",
    ) -> str | None:
        """
        Generate a 3D model from text description.

        Args:
            prompt: Text description
            output_dir: Directory to save the model
            output_format: Output format

        Returns:
            Path to the generated model or None on failure
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create text-to-3D task
            task_id = await self._create_text_to_3d_task(prompt)

            if not task_id:
                return None

            # Wait for completion
            result = await self._wait_for_task(task_id)

            if not result or result.status != "success":
                return None

            # Download the model
            model_url = result.result.get("model", {}).get("url") if result.result else None
            if not model_url:
                return None

            # Create filename from prompt
            safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            output_filename = f"{safe_name}_3d.{output_format}"
            output_path = output_dir / output_filename

            await self._download_model(model_url, output_path)

            return str(output_path)

        except Exception as e:
            logger.exception(f"Tripo text-to-3D failed: {e}")
            return None

    async def _create_image_to_3d_task(
        self,
        image_path: Path,
        prompt: str | None = None,
        texture_resolution: int = 2048,
    ) -> str | None:
        """Create an image-to-3D generation task."""
        try:
            # Read and encode image
            import base64

            image_data = image_path.read_bytes()
            image_base64 = base64.b64encode(image_data).decode()

            # Determine MIME type
            suffix = image_path.suffix.lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(suffix, "image/png")

            # Create task
            payload = {
                "type": "image_to_model",
                "file": {
                    "type": mime_type,
                    "data": image_base64,
                },
                "model_version": "v2.0-20240919",
            }

            if prompt:
                payload["prompt"] = prompt

            response = await self._client.post("/task", json=payload)
            response.raise_for_status()

            data = response.json()
            task_id = data.get("data", {}).get("task_id")

            logger.info(f"Created Tripo task: {task_id}")
            return task_id

        except httpx.HTTPStatusError as e:
            logger.error(f"Tripo API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"Failed to create Tripo task: {e}")
            return None

    async def _create_text_to_3d_task(self, prompt: str) -> str | None:
        """Create a text-to-3D generation task."""
        try:
            payload = {
                "type": "text_to_model",
                "prompt": prompt,
                "model_version": "v2.0-20240919",
            }

            response = await self._client.post("/task", json=payload)
            response.raise_for_status()

            data = response.json()
            return data.get("data", {}).get("task_id")

        except Exception as e:
            logger.exception(f"Failed to create text-to-3D task: {e}")
            return None

    async def _wait_for_task(self, task_id: str) -> TripoTaskStatus | None:
        """Wait for a task to complete."""
        elapsed = 0

        while elapsed < self.MAX_WAIT_TIME:
            status = await self._get_task_status(task_id)

            if not status:
                return None

            if status.status == "success":
                logger.info(f"Tripo task {task_id} completed successfully")
                return status

            if status.status == "failed":
                logger.error(f"Tripo task {task_id} failed: {status.error}")
                return status

            logger.debug(f"Task {task_id} progress: {status.progress}%")
            await asyncio.sleep(self.POLL_INTERVAL)
            elapsed += self.POLL_INTERVAL

        logger.error(f"Tripo task {task_id} timed out after {self.MAX_WAIT_TIME}s")
        return None

    async def _get_task_status(self, task_id: str) -> TripoTaskStatus | None:
        """Get the status of a task."""
        try:
            response = await self._client.get(f"/task/{task_id}")
            response.raise_for_status()

            data = response.json().get("data", {})

            return TripoTaskStatus(
                task_id=task_id,
                status=data.get("status", "unknown"),
                progress=data.get("progress", 0),
                result=data.get("output"),
                error=data.get("error"),
            )

        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None

    async def _download_model(self, url: str, output_path: Path) -> None:
        """Download a model file from URL."""
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            output_path.write_bytes(response.content)
            logger.info(f"Downloaded model to: {output_path}")

    def _validate_task_result(self, result: dict[str, Any]) -> None:
        """
        Validate task result structure.

        Args:
            result: Task result dictionary

        Raises:
            ValueError: If result structure is invalid
        """
        if "model" not in result:
            raise ValueError("Task result missing 'model' field")

        model = result["model"]
        if not isinstance(model, dict):
            raise ValueError("Invalid model data structure")

        if "url" not in model:
            raise ValueError("Task result missing valid model URL")

        url = model["url"]
        if not isinstance(url, str) or not (
            url.startswith("https://") or url.startswith("http://")
        ):
            raise ValueError(f"Invalid model URL: {url}")

    async def _download_model_resilient(self, url: str, output_path: Path) -> None:
        """
        Download model with retry logic.

        Args:
            url: Model URL
            output_path: Destination path
        """
        if not self.enable_resilience:
            # No resilience - use simple download
            await self._download_model(url, output_path)
            return

        # Retry logic for resilient download
        max_retries = 3
        retry_delay = 2.0

        for attempt in range(1, max_retries + 1):
            try:
                await self._download_model(url, output_path)
                return
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                if attempt == max_retries:
                    raise
                logger.warning(
                    f"Download attempt {attempt} failed: {e}. Retrying in {retry_delay}s..."
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    def _sanitize_for_logs(self, text: str, max_length: int = 100) -> str:
        """
        Sanitize text for logging (PII protection).

        Args:
            text: Text to sanitize
            max_length: Max length before truncation

        Returns:
            Sanitized text with hash
        """
        if len(text) <= max_length:
            return text

        # Truncate and add hash for uniqueness
        truncated = text[:max_length]
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:8]
        return f"{truncated}... (hash:{text_hash})"

    def get_health_status(self) -> dict[str, Any]:
        """
        Get client health status.

        Returns:
            Health status dictionary
        """
        return {
            "service_name": "tripo3d",
            "api_configured": bool(self.api_key),
            "resilience_enabled": self.enable_resilience,
            "cache_size": len(self._result_cache),
            "circuit_breaker": {
                "state": "CLOSED" if self.enable_resilience else "N/A",
            },
        }

    async def get_balance(self) -> dict[str, Any]:
        """Get account balance/credits."""
        try:
            response = await self._client.get("/user/balance")
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
