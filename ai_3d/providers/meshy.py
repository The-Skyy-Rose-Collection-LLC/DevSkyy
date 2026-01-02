# ai_3d/providers/meshy.py
"""
Meshy AI 3D Client for DevSkyy.

Provides high-quality image-to-3D and retexturing capabilities.
Features:
- Proper async/await patterns (no deadlocks)
- Rate limiting with asyncio.Semaphore(5)
- 2s delay between API calls
- Exponential backoff on 429 errors
- Robust response parsing

API Reference: https://docs.meshy.ai/
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import httpx

from errors.production_errors import (
    ConfigurationError,
    ExternalServiceError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class MeshyTaskStatus(str, Enum):
    """Meshy task status values."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class MeshyArtStyle(str, Enum):
    """Art style for 3D generation."""

    REALISTIC = "realistic"
    CARTOON = "cartoon"


class MeshyTopology(str, Enum):
    """Mesh topology type."""

    QUAD = "quad"
    TRIANGLE = "triangle"


@dataclass
class MeshyTask:
    """Result from a Meshy generation task."""

    task_id: str
    status: MeshyTaskStatus
    progress: int = 0
    model_urls: dict[str, str] = field(default_factory=dict)
    thumbnail_url: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None
    finished_at: datetime | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> MeshyTask:
        """Parse task from API response."""
        return cls(
            task_id=data.get("id", data.get("result", "")),
            status=MeshyTaskStatus(data.get("status", "PENDING")),
            progress=data.get("progress", 0),
            model_urls=data.get("model_urls", {}),
            thumbnail_url=data.get("thumbnail_url"),
            error_message=data.get("message"),
            created_at=None,
            finished_at=None,
        )


class MeshyClient:
    """
    Async Meshy AI client for 3D model generation.

    Features:
    - Rate limiting: Max 5 concurrent requests, 2s between calls
    - Exponential backoff on 429 errors
    - Proper async/await patterns

    Requires MESHY_API_KEY environment variable.

    Usage:
        client = MeshyClient()
        model_path = await client.generate_from_image("product.jpg", "./output")
    """

    BASE_URL = "https://api.meshy.ai/openapi/v1"
    POLL_INTERVAL = 5  # seconds
    MAX_WAIT_TIME = 600  # 10 minutes

    # Rate limiting
    MAX_CONCURRENT_REQUESTS = 5
    MIN_DELAY_BETWEEN_CALLS = 2.0  # seconds

    # Exponential backoff config
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 60.0
    BACKOFF_MULTIPLIER = 2.0
    MAX_RETRIES = 5

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Meshy client.

        Args:
            api_key: Meshy API key (or set MESHY_API_KEY env var)

        Raises:
            ConfigurationError: If API key is not provided
        """
        self.api_key = api_key or os.getenv("MESHY_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "MESHY_API_KEY is required for Meshy 3D generation",
                config_key="MESHY_API_KEY",
            )

        # Rate limiting semaphore
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

        # HTTP client
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=300.0,  # 5 minutes for large uploads
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> MeshyClient:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    async def _rate_limited_request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Make a rate-limited API request with exponential backoff.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for httpx

        Returns:
            API response

        Raises:
            RateLimitError: If rate limit exceeded after all retries
            ExternalServiceError: If API request fails
        """
        async with self._semaphore:
            # Enforce minimum delay between requests
            async with self._lock:
                now = asyncio.get_event_loop().time()
                elapsed = now - self._last_request_time
                if elapsed < self.MIN_DELAY_BETWEEN_CALLS:
                    await asyncio.sleep(self.MIN_DELAY_BETWEEN_CALLS - elapsed)
                self._last_request_time = asyncio.get_event_loop().time()

            # Retry loop with exponential backoff
            backoff = self.INITIAL_BACKOFF
            last_error: Exception | None = None

            for attempt in range(self.MAX_RETRIES):
                try:
                    response = await self._client.request(method, endpoint, **kwargs)

                    # Handle rate limiting (429)
                    if response.status_code == 429:
                        retry_after = response.headers.get("Retry-After")
                        if retry_after:
                            wait_time = float(retry_after)
                        else:
                            # Add jitter to prevent thundering herd
                            jitter = random.uniform(0, backoff * 0.1)
                            wait_time = backoff + jitter

                        logger.warning(
                            f"Rate limited (429). Attempt {attempt + 1}/{self.MAX_RETRIES}. "
                            f"Waiting {wait_time:.1f}s"
                        )

                        await asyncio.sleep(wait_time)
                        backoff = min(backoff * self.BACKOFF_MULTIPLIER, self.MAX_BACKOFF)
                        continue

                    # Handle server errors with retry
                    if response.status_code >= 500:
                        logger.warning(
                            f"Server error {response.status_code}. "
                            f"Attempt {attempt + 1}/{self.MAX_RETRIES}"
                        )
                        await asyncio.sleep(backoff)
                        backoff = min(backoff * self.BACKOFF_MULTIPLIER, self.MAX_BACKOFF)
                        continue

                    # Raise for other errors
                    response.raise_for_status()
                    return response

                except httpx.TimeoutException as e:
                    last_error = e
                    logger.warning(f"Timeout on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * self.BACKOFF_MULTIPLIER, self.MAX_BACKOFF)

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        continue  # Already handled above
                    raise ExternalServiceError(
                        service_name="Meshy",
                        error_message=f"HTTP {e.response.status_code}: {e.response.text}",
                    )

            # All retries exhausted
            if last_error:
                raise RateLimitError(
                    service="Meshy",
                    retry_after=self.MAX_BACKOFF,
                    context={"attempts": self.MAX_RETRIES},
                )

            raise ExternalServiceError(
                service_name="Meshy",
                error_message="Max retries exceeded",
            )

    async def generate_from_image(
        self,
        image_path: str,
        output_dir: str,
        output_format: str = "glb",
        prompt: str | None = None,
        texture_resolution: int = 2048,
        art_style: MeshyArtStyle = MeshyArtStyle.REALISTIC,
        topology: MeshyTopology = MeshyTopology.QUAD,
        target_polycount: int = 30000,
    ) -> str | None:
        """
        Generate a 3D model from an image.

        Args:
            image_path: Path to the source image
            output_dir: Directory to save the model
            output_format: Output format (glb, fbx, obj)
            prompt: Optional text prompt
            texture_resolution: Texture resolution
            art_style: Art style (realistic or cartoon)
            topology: Mesh topology (quad or triangle)
            target_polycount: Target polygon count

        Returns:
            Path to the generated model or None on failure
        """
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create generation task
            task = await self._create_image_to_3d_task(
                image_path=image_path,
                art_style=art_style,
                topology=topology,
                target_polycount=target_polycount,
            )

            if not task or not task.task_id:
                logger.error("Failed to create Meshy task")
                return None

            logger.info(f"Created Meshy task: {task.task_id}")

            # Wait for completion
            completed_task = await self._wait_for_task(task.task_id)

            if not completed_task or completed_task.status != MeshyTaskStatus.SUCCEEDED:
                error_msg = completed_task.error_message if completed_task else "Unknown"
                logger.error(f"Meshy generation failed: {error_msg}")
                return None

            # Download the model
            model_url = completed_task.model_urls.get(
                output_format
            ) or completed_task.model_urls.get("glb")
            if not model_url:
                logger.error(f"No model URL for format {output_format} in response")
                return None

            output_filename = f"{image_path.stem}_meshy.{output_format}"
            output_path = output_dir / output_filename

            await self._download_model(model_url, output_path)
            logger.info(f"Downloaded Meshy model: {output_path}")

            return str(output_path)

        except Exception as e:
            logger.exception(f"Meshy generation failed: {e}")
            return None

    async def generate_from_text(
        self,
        prompt: str,
        output_dir: str,
        output_format: str = "glb",
        art_style: MeshyArtStyle = MeshyArtStyle.REALISTIC,
    ) -> str | None:
        """
        Generate a 3D model from text description.

        Args:
            prompt: Text description
            output_dir: Directory to save the model
            output_format: Output format
            art_style: Art style

        Returns:
            Path to the generated model or None on failure
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create text-to-3D task
            task = await self._create_text_to_3d_task(
                prompt=prompt,
                art_style=art_style,
            )

            if not task or not task.task_id:
                logger.error("Failed to create Meshy text-to-3D task")
                return None

            logger.info(f"Created Meshy text-to-3D task: {task.task_id}")

            # Wait for completion
            completed_task = await self._wait_for_task(task.task_id)

            if not completed_task or completed_task.status != MeshyTaskStatus.SUCCEEDED:
                return None

            # Download the model
            model_url = completed_task.model_urls.get(
                output_format
            ) or completed_task.model_urls.get("glb")
            if not model_url:
                return None

            safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            output_filename = f"{safe_name}_meshy.{output_format}"
            output_path = output_dir / output_filename

            await self._download_model(model_url, output_path)

            return str(output_path)

        except Exception as e:
            logger.exception(f"Meshy text-to-3D failed: {e}")
            return None

    async def retexture_model(
        self,
        model_path: str,
        output_dir: str,
        style_image_path: str | None = None,
        text_prompt: str | None = None,
        enable_pbr: bool = True,
    ) -> str | None:
        """
        Retexture an existing 3D model.

        Args:
            model_path: Path to existing GLB model
            output_dir: Directory to save the retextured model
            style_image_path: Optional image to use as texture reference
            text_prompt: Optional text description of desired texture
            enable_pbr: Whether to generate PBR maps

        Returns:
            Path to the retextured model or None on failure
        """
        model_path = Path(model_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            task = await self._create_retexture_task(
                model_path=model_path,
                style_image_path=Path(style_image_path) if style_image_path else None,
                text_prompt=text_prompt,
                enable_pbr=enable_pbr,
            )

            if not task or not task.task_id:
                return None

            completed_task = await self._wait_for_task(task.task_id, task_type="retexture")

            if not completed_task or completed_task.status != MeshyTaskStatus.SUCCEEDED:
                return None

            model_url = completed_task.model_urls.get("glb")
            if not model_url:
                return None

            output_filename = f"{model_path.stem}_retextured.glb"
            output_path = output_dir / output_filename

            await self._download_model(model_url, output_path)

            return str(output_path)

        except Exception as e:
            logger.exception(f"Meshy retexture failed: {e}")
            return None

    async def _create_image_to_3d_task(
        self,
        image_path: Path,
        art_style: MeshyArtStyle = MeshyArtStyle.REALISTIC,
        topology: MeshyTopology = MeshyTopology.QUAD,
        target_polycount: int = 30000,
    ) -> MeshyTask | None:
        """Create an image-to-3D generation task."""
        try:
            # Read and encode image
            image_data = image_path.read_bytes()
            b64 = base64.b64encode(image_data).decode("utf-8")

            # Determine MIME type
            ext = image_path.suffix.lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
            }
            mime_type = mime_types.get(ext, "image/jpeg")

            image_url = f"data:{mime_type};base64,{b64}"

            payload = {
                "image_url": image_url,
                "enable_pbr": True,
                "should_remesh": True,
                "topology": topology.value,
                "target_polycount": target_polycount,
                "ai_model": "meshy-5",
                "art_style": art_style.value,
            }

            response = await self._rate_limited_request(
                "POST",
                "/image-to-3d",
                json=payload,
            )

            data = response.json()
            # Handle different response formats
            task_id = data.get("result") or data.get("id") or data.get("task_id")

            if not task_id:
                logger.error(f"No task_id in response: {data}")
                return None

            return MeshyTask(
                task_id=task_id,
                status=MeshyTaskStatus.PENDING,
            )

        except Exception as e:
            logger.exception(f"Failed to create image-to-3D task: {e}")
            return None

    async def _create_text_to_3d_task(
        self,
        prompt: str,
        art_style: MeshyArtStyle = MeshyArtStyle.REALISTIC,
    ) -> MeshyTask | None:
        """Create a text-to-3D generation task."""
        try:
            payload = {
                "mode": "preview",
                "prompt": prompt,
                "art_style": art_style.value,
                "negative_prompt": "low quality, blurry, distorted",
            }

            response = await self._rate_limited_request(
                "POST",
                "/text-to-3d",
                json=payload,
            )

            data = response.json()
            task_id = data.get("result") or data.get("id") or data.get("task_id")

            if not task_id:
                return None

            return MeshyTask(
                task_id=task_id,
                status=MeshyTaskStatus.PENDING,
            )

        except Exception as e:
            logger.exception(f"Failed to create text-to-3D task: {e}")
            return None

    async def _create_retexture_task(
        self,
        model_path: Path,
        style_image_path: Path | None = None,
        text_prompt: str | None = None,
        enable_pbr: bool = True,
    ) -> MeshyTask | None:
        """Create a retexture task."""
        try:
            model_data = model_path.read_bytes()
            model_b64 = base64.b64encode(model_data).decode("utf-8")
            model_url = f"data:model/gltf-binary;base64,{model_b64}"

            payload = {
                "model_url": model_url,
                "enable_pbr": enable_pbr,
                "enable_original_uv": True,
            }

            if style_image_path:
                style_data = style_image_path.read_bytes()
                style_b64 = base64.b64encode(style_data).decode("utf-8")
                ext = style_image_path.suffix.lower()
                mime_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
                    ext, "image/jpeg"
                )
                payload["image_style_url"] = f"data:{mime_type};base64,{style_b64}"
            elif text_prompt:
                payload["text_style_prompt"] = text_prompt
            else:
                payload["text_style_prompt"] = (
                    "High quality fabric texture, realistic clothing material, "
                    "detailed stitching, professional lighting"
                )

            response = await self._rate_limited_request(
                "POST",
                "/retexture",
                json=payload,
            )

            data = response.json()
            task_id = data.get("result") or data.get("id") or data.get("task_id")

            if not task_id:
                return None

            return MeshyTask(
                task_id=task_id,
                status=MeshyTaskStatus.PENDING,
            )

        except Exception as e:
            logger.exception(f"Failed to create retexture task: {e}")
            return None

    async def _wait_for_task(
        self,
        task_id: str,
        task_type: str = "image-to-3d",
    ) -> MeshyTask | None:
        """Wait for a task to complete with polling."""
        elapsed = 0

        while elapsed < self.MAX_WAIT_TIME:
            try:
                response = await self._rate_limited_request(
                    "GET",
                    f"/{task_type}/{task_id}",
                )

                data = response.json()

                status_str = data.get("status", "PENDING")
                try:
                    status = MeshyTaskStatus(status_str)
                except ValueError:
                    status = MeshyTaskStatus.PENDING

                task = MeshyTask(
                    task_id=task_id,
                    status=status,
                    progress=data.get("progress", 0),
                    model_urls=data.get("model_urls", {}),
                    thumbnail_url=data.get("thumbnail_url"),
                    error_message=data.get("message"),
                )

                if status == MeshyTaskStatus.SUCCEEDED:
                    logger.info(f"Meshy task {task_id} completed successfully")
                    return task

                if status in (MeshyTaskStatus.FAILED, MeshyTaskStatus.EXPIRED):
                    logger.error(f"Meshy task {task_id} failed: {task.error_message}")
                    return task

                logger.debug(f"Task {task_id} progress: {task.progress}%")

            except Exception as e:
                logger.warning(f"Error polling task {task_id}: {e}")

            await asyncio.sleep(self.POLL_INTERVAL)
            elapsed += self.POLL_INTERVAL

        logger.error(f"Meshy task {task_id} timed out after {self.MAX_WAIT_TIME}s")
        return None

    async def _download_model(self, url: str, output_path: Path) -> None:
        """Download a model file from URL."""
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            output_path.write_bytes(response.content)

    async def get_task_status(
        self, task_id: str, task_type: str = "image-to-3d"
    ) -> MeshyTask | None:
        """Get the status of a task."""
        try:
            response = await self._rate_limited_request(
                "GET",
                f"/{task_type}/{task_id}",
            )

            data = response.json()
            return MeshyTask.from_api_response(data)

        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return None

    async def get_balance(self) -> dict[str, Any]:
        """Get account credits/balance."""
        try:
            response = await self._rate_limited_request("GET", "/user/credits")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get Meshy balance: {e}")
            return {}
