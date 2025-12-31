# ai_3d/providers/tripo.py
"""
Tripo3D Client for DevSkyy.

Tripo3D provides high-quality image-to-3D and text-to-3D generation
optimized for e-commerce and product visualization.

API Reference: https://platform.tripo3d.ai/docs
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel

from errors.production_errors import ConfigurationError

logger = logging.getLogger(__name__)


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

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Tripo client.

        Args:
            api_key: Tripo API key (or set TRIPO_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("TRIPO_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "TRIPO_API_KEY is required",
                config_key="TRIPO_API_KEY",
            )

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

    async def get_balance(self) -> dict[str, Any]:
        """Get account balance/credits."""
        try:
            response = await self._client.get("/user/balance")
            response.raise_for_status()
            return response.json().get("data", {})
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {}
