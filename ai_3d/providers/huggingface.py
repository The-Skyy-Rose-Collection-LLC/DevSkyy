# ai_3d/providers/huggingface.py
"""
HuggingFace 3D Client for DevSkyy.

Provides access to open-source 3D generation models on HuggingFace:
- Shap-E: OpenAI's image/text to 3D
- Point-E: OpenAI's text to 3D
- TripoSR: Fast image-to-3D
- Various community models

API Reference: https://huggingface.co/docs/api-inference
"""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

import httpx

from errors.production_errors import ConfigurationError

logger = logging.getLogger(__name__)


class HuggingFace3DClient:
    """
    HuggingFace client for 3D model generation.

    Supports multiple models:
    - stabilityai/TripoSR (fast image-to-3D)
    - openai/shap-e (text/image to 3D)
    - openai/point-e (text to 3D)

    Requires HUGGINGFACE_API_KEY or HF_TOKEN environment variable.
    """

    BASE_URL = "https://api-inference.huggingface.co/models"

    # Supported models
    MODELS = {
        "triposr": "stabilityai/TripoSR",
        "shap-e": "openai/shap-e",
        "shap-e-img2img": "openai/shap-e-img2img",
    }

    DEFAULT_MODEL = "triposr"

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the HuggingFace client.

        Args:
            api_key: HuggingFace API key (or set HF_TOKEN env var)
        """
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
        if not self.api_key:
            raise ConfigurationError(
                "HUGGINGFACE_API_KEY or HF_TOKEN is required",
                config_key="HUGGINGFACE_API_KEY",
            )

        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
            },
            timeout=300.0,  # 5 minutes for large models
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
        model: str = "triposr",
        texture_resolution: int = 2048,
    ) -> str | None:
        """
        Generate a 3D model from an image.

        Args:
            image_path: Path to the source image
            output_dir: Directory to save the model
            output_format: Output format (glb recommended)
            prompt: Optional text prompt
            model: Model to use (triposr, shap-e-img2img)
            texture_resolution: Texture resolution (if supported)

        Returns:
            Path to the generated model or None on failure
        """
        image_path = Path(image_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if model not in self.MODELS:
            logger.warning(f"Unknown model {model}, using {self.DEFAULT_MODEL}")
            model = self.DEFAULT_MODEL

        model_id = self.MODELS[model]

        try:
            # Read image
            image_data = image_path.read_bytes()

            # Call inference API
            url = f"{self.BASE_URL}/{model_id}"

            response = await self._client.post(
                url,
                content=image_data,
                headers={"Content-Type": "application/octet-stream"},
            )

            # Handle model loading
            if response.status_code == 503:
                # Model is loading
                data = response.json()
                estimated_time = data.get("estimated_time", 60)
                logger.info(f"Model loading, waiting {estimated_time}s")
                await asyncio.sleep(min(estimated_time, 120))

                # Retry
                response = await self._client.post(
                    url,
                    content=image_data,
                    headers={"Content-Type": "application/octet-stream"},
                )

            response.raise_for_status()

            # Save the model
            output_filename = f"{image_path.stem}_hf3d.{output_format}"
            output_path = output_dir / output_filename

            # Response should be the 3D model data
            content_type = response.headers.get("content-type", "")

            if "application/octet-stream" in content_type or "model" in content_type:
                output_path.write_bytes(response.content)
            else:
                # May be JSON with URL
                data = response.json()
                if "url" in data:
                    await self._download_file(data["url"], output_path)
                elif "model" in data:
                    # Base64 encoded
                    import base64

                    model_data = base64.b64decode(data["model"])
                    output_path.write_bytes(model_data)
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return None

            logger.info(f"Generated 3D model: {output_path}")
            return str(output_path)

        except httpx.HTTPStatusError as e:
            logger.error(f"HuggingFace API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.exception(f"HuggingFace 3D generation failed: {e}")
            return None

    async def generate_from_text(
        self,
        prompt: str,
        output_dir: str,
        output_format: str = "glb",
        model: str = "shap-e",
    ) -> str | None:
        """
        Generate a 3D model from text description.

        Args:
            prompt: Text description
            output_dir: Directory to save the model
            output_format: Output format
            model: Model to use (shap-e recommended for text)

        Returns:
            Path to the generated model or None on failure
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        model_id = self.MODELS.get(model, self.MODELS["shap-e"])

        try:
            url = f"{self.BASE_URL}/{model_id}"

            response = await self._client.post(
                url,
                json={"inputs": prompt},
            )

            # Handle model loading
            if response.status_code == 503:
                data = response.json()
                estimated_time = data.get("estimated_time", 60)
                logger.info(f"Model loading, waiting {estimated_time}s")
                await asyncio.sleep(min(estimated_time, 120))

                response = await self._client.post(
                    url,
                    json={"inputs": prompt},
                )

            response.raise_for_status()

            # Save the model
            safe_name = "".join(c if c.isalnum() else "_" for c in prompt[:30])
            output_filename = f"{safe_name}_hf3d.{output_format}"
            output_path = output_dir / output_filename

            content_type = response.headers.get("content-type", "")

            if "application/octet-stream" in content_type:
                output_path.write_bytes(response.content)
            else:
                data = response.json()
                if "url" in data:
                    await self._download_file(data["url"], output_path)
                else:
                    logger.error(f"Unexpected response: {data}")
                    return None

            logger.info(f"Generated 3D model: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.exception(f"HuggingFace text-to-3D failed: {e}")
            return None

    async def _download_file(self, url: str, output_path: Path) -> None:
        """Download a file from URL."""
        response = await self._client.get(url)
        response.raise_for_status()
        output_path.write_bytes(response.content)

    async def list_available_models(self) -> list[dict[str, Any]]:
        """List available 3D generation models."""
        models = []

        for name, model_id in self.MODELS.items():
            try:
                url = f"https://huggingface.co/api/models/{model_id}"
                response = await self._client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    models.append(
                        {
                            "name": name,
                            "model_id": model_id,
                            "downloads": data.get("downloads", 0),
                            "likes": data.get("likes", 0),
                            "pipeline_tag": data.get("pipeline_tag"),
                        }
                    )

            except Exception as e:
                logger.warning(f"Failed to get info for {model_id}: {e}")

        return models

    async def check_model_status(self, model: str = "triposr") -> dict[str, Any]:
        """Check if a model is loaded and ready."""
        model_id = self.MODELS.get(model, self.MODELS[self.DEFAULT_MODEL])

        try:
            url = f"{self.BASE_URL}/{model_id}"
            response = await self._client.get(url)

            if response.status_code == 200:
                return {"status": "ready", "model": model_id}
            elif response.status_code == 503:
                data = response.json()
                return {
                    "status": "loading",
                    "model": model_id,
                    "estimated_time": data.get("estimated_time"),
                }
            else:
                return {"status": "error", "model": model_id}

        except Exception as e:
            return {"status": "error", "model": model_id, "error": str(e)}
