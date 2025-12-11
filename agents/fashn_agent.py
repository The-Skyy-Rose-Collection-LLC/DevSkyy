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
"""

import asyncio
import base64
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration & Enums
# =============================================================================


class GarmentCategory(str, Enum):
    """Garment categories for try-on"""

    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    FULL_BODY = "full_body"


class TryOnMode(str, Enum):
    """Try-on mode"""

    QUALITY = "quality"  # Higher quality, slower
    BALANCED = "balanced"  # Balance of speed and quality
    FAST = "fast"  # Faster, lower quality


class FashnTaskStatus(str, Enum):
    """Task status"""

    STARTING = "starting"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class FashnConfig:
    """FASHN API configuration"""

    api_key: str = field(default_factory=lambda: os.getenv("FASHN_API_KEY", ""))
    base_url: str = "https://api.fashn.ai/v1"
    timeout: float = 120.0
    poll_interval: float = 1.0
    output_dir: str = "./generated_assets/tryon"

    # Default output size
    output_width: int = 576
    output_height: int = 864

    @classmethod
    def from_env(cls) -> "FashnConfig":
        return cls(
            api_key=os.getenv("FASHN_API_KEY", ""),
            output_dir=os.getenv("FASHN_OUTPUT_DIR", "./generated_assets/tryon"),
        )


# =============================================================================
# Models
# =============================================================================


class FashnTask(BaseModel):
    """FASHN task"""

    id: str
    status: FashnTaskStatus
    output: list[str] | None = None
    error: str | None = None
    created_at: str | None = None

    # Additional metadata
    input_garment: str | None = None
    input_model: str | None = None


class TryOnResult(BaseModel):
    """Virtual try-on result"""

    task_id: str
    image_url: str
    image_path: str
    metadata: dict[str, Any] = {}


class ModelGenerationResult(BaseModel):
    """AI model generation result"""

    task_id: str
    image_url: str
    image_path: str
    prompt: str
    metadata: dict[str, Any] = {}


# =============================================================================
# FASHN Agent
# =============================================================================


class FashnTryOnAgent:
    """
    FASHN Virtual Try-On Agent

    Generate virtual try-on images for SkyyRose products.

    Usage:
        agent = FashnTryOnAgent()

        # Virtual try-on
        result = await agent.virtual_tryon(
            model_image="path/to/model.jpg",
            garment_image="path/to/garment.jpg",
            category=GarmentCategory.TOPS
        )

        # Generate AI model
        model = await agent.create_ai_model(
            prompt="Fashion model, professional, studio lighting",
            gender="female"
        )

        # Product-to-model
        result = await agent.product_to_model(
            product_image="path/to/product.jpg"
        )
    """

    def __init__(self, config: FashnConfig = None):
        self.config = config or FashnConfig.from_env()
        self._session: aiohttp.ClientSession | None = None

        # Ensure output directory
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            )

    async def close(self):
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 data URL"""
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
        data: dict = None,
    ) -> dict:
        """Make API request"""
        await self._ensure_session()

        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"

        async with self._session.request(method, url, json=data) as response:
            result = await response.json()

            if response.status >= 400:
                error_msg = result.get("error", {}).get("message", str(result))
                raise Exception(f"FASHN API error ({response.status}): {error_msg}")

            return result

    async def _poll_prediction(self, prediction_id: str) -> FashnTask:
        """Poll prediction until complete"""
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
            await asyncio.sleep(self.config.poll_interval)

    async def _download_image(self, url: str, filename: str) -> str:
        """Download image to output directory"""
        await self._ensure_session()

        filepath = Path(self.config.output_dir) / filename

        async with self._session.get(url) as response:
            if response.status >= 400:
                raise Exception(f"Download failed: {response.status}")

            async with aiofiles.open(filepath, "wb") as f:
                async for chunk in response.content.iter_chunked(8192):
                    await f.write(chunk)

        logger.info(f"Downloaded: {filepath}")
        return str(filepath)

    # -------------------------------------------------------------------------
    # Virtual Try-On
    # -------------------------------------------------------------------------

    async def virtual_tryon(
        self,
        model_image: str,
        garment_image: str,
        category: GarmentCategory = GarmentCategory.TOPS,
        mode: TryOnMode = TryOnMode.BALANCED,
        nsfw_filter: bool = True,
        cover_feet: bool = False,
        adjust_hands: bool = False,
        restore_background: bool = True,
        restore_clothes: bool = False,
        garment_photo_type: str = "auto",
        long_top: bool = False,
        seed: int = None,
    ) -> TryOnResult:
        """
        Generate virtual try-on image

        Args:
            model_image: Path to model/person image
            garment_image: Path to garment image
            category: Garment category
            mode: Quality/speed tradeoff
            nsfw_filter: Filter inappropriate content
            cover_feet: Cover model's feet
            adjust_hands: Adjust hand positions
            restore_background: Keep original background
            restore_clothes: Keep visible clothes not replaced
            garment_photo_type: "auto", "flat-lay", or "model"
            long_top: Garment is a long top
            seed: Random seed for reproducibility

        Returns:
            TryOnResult with generated image
        """
        logger.info(f"Starting virtual try-on: {garment_image} on {model_image}")

        # Encode images
        model_data = await self._encode_image(model_image)
        garment_data = await self._encode_image(garment_image)

        # Build request
        input_data = {
            "model_image": model_data,
            "garment_image": garment_data,
            "category": category.value,
            "mode": mode.value,
            "nsfw_filter": nsfw_filter,
            "cover_feet": cover_feet,
            "adjust_hands": adjust_hands,
            "restore_background": restore_background,
            "restore_clothes": restore_clothes,
            "garment_photo_type": garment_photo_type,
            "long_top": long_top,
        }

        if seed is not None:
            input_data["seed"] = seed

        # Create prediction
        result = await self._api_request("POST", "/run", data={"input": input_data})

        prediction_id = result.get("id")

        if not prediction_id:
            # Synchronous result
            output = result.get("output", [])
            image_url = output[0] if output else None
        else:
            # Async - poll for result
            task = await self._poll_prediction(prediction_id)
            image_url = task.output[0] if task.output else None

        if not image_url:
            raise Exception("No output image generated")

        # Download result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tryon_{timestamp}.png"
        image_path = await self._download_image(image_url, filename)

        return TryOnResult(
            task_id=prediction_id or "sync",
            image_url=image_url,
            image_path=image_path,
            metadata={
                "model_image": model_image,
                "garment_image": garment_image,
                "category": category.value,
                "mode": mode.value,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )

    async def batch_tryon(
        self,
        model_image: str,
        garment_images: list[str],
        category: GarmentCategory = GarmentCategory.TOPS,
        concurrency: int = 3,
    ) -> list[TryOnResult]:
        """
        Batch virtual try-on for multiple garments

        Args:
            model_image: Path to model image
            garment_images: List of garment image paths
            category: Garment category
            concurrency: Max concurrent requests

        Returns:
            List of TryOnResult
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def process_garment(garment_path: str) -> TryOnResult:
            async with semaphore:
                return await self.virtual_tryon(
                    model_image=model_image,
                    garment_image=garment_path,
                    category=category,
                )

        tasks = [process_garment(g) for g in garment_images]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        successful = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed for {garment_images[i]}: {result}")
            else:
                successful.append(result)

        return successful

    # -------------------------------------------------------------------------
    # AI Model Generation
    # -------------------------------------------------------------------------

    async def create_ai_model(
        self,
        prompt: str = None,
        gender: str = "female",
        age: str = "young adult",
        ethnicity: str = None,
        pose: str = "standing",
        background: str = "studio",
        style: str = "fashion photography",
    ) -> ModelGenerationResult:
        """
        Generate AI fashion model image

        Args:
            prompt: Custom prompt (overrides other params)
            gender: Model gender
            age: Age description
            ethnicity: Optional ethnicity
            pose: Pose description
            background: Background type
            style: Photography style

        Returns:
            ModelGenerationResult with generated image
        """
        # Build prompt if not provided
        if not prompt:
            parts = [
                f"{gender} fashion model",
                age,
                f"{pose} pose",
                f"{background} background",
                style,
                "high quality, professional lighting",
            ]
            if ethnicity:
                parts.insert(2, ethnicity)
            prompt = ", ".join(parts)

        logger.info(f"Generating AI model: {prompt[:50]}...")

        input_data = {
            "prompt": prompt,
            "width": self.config.output_width,
            "height": self.config.output_height,
        }

        result = await self._api_request("POST", "/model-create/run", data={"input": input_data})

        prediction_id = result.get("id")

        if prediction_id:
            task = await self._poll_prediction(prediction_id)
            image_url = task.output[0] if task.output else None
        else:
            output = result.get("output", [])
            image_url = output[0] if output else None

        if not image_url:
            raise Exception("No model image generated")

        # Download
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_model_{timestamp}.png"
        image_path = await self._download_image(image_url, filename)

        return ModelGenerationResult(
            task_id=prediction_id or "sync",
            image_url=image_url,
            image_path=image_path,
            prompt=prompt,
            metadata={
                "gender": gender,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )

    # -------------------------------------------------------------------------
    # Product-to-Model
    # -------------------------------------------------------------------------

    async def product_to_model(
        self,
        product_image: str,
        model_type: str = "fashion_model",
        background: str = "studio",
    ) -> TryOnResult:
        """
        Convert product flat-lay to model shot

        Args:
            product_image: Path to product image
            model_type: Type of model to use
            background: Background style

        Returns:
            TryOnResult with model wearing product
        """
        logger.info(f"Product-to-model: {product_image}")

        product_data = await self._encode_image(product_image)

        input_data = {
            "product_image": product_data,
            "model_type": model_type,
            "background": background,
        }

        result = await self._api_request(
            "POST", "/product-to-model/run", data={"input": input_data}
        )

        prediction_id = result.get("id")

        if prediction_id:
            task = await self._poll_prediction(prediction_id)
            image_url = task.output[0] if task.output else None
        else:
            output = result.get("output", [])
            image_url = output[0] if output else None

        if not image_url:
            raise Exception("No output generated")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"product_model_{timestamp}.png"
        image_path = await self._download_image(image_url, filename)

        return TryOnResult(
            task_id=prediction_id or "sync",
            image_url=image_url,
            image_path=image_path,
            metadata={
                "product_image": product_image,
                "model_type": model_type,
                "generated_at": datetime.now(UTC).isoformat(),
            },
        )

    # -------------------------------------------------------------------------
    # Background Removal
    # -------------------------------------------------------------------------

    async def remove_background(
        self,
        image_path: str,
        output_format: str = "png",
    ) -> str:
        """
        Remove background from image

        Args:
            image_path: Input image path
            output_format: Output format (png for transparency)

        Returns:
            Path to processed image
        """
        logger.info(f"Removing background: {image_path}")

        image_data = await self._encode_image(image_path)

        input_data = {
            "image": image_data,
            "output_format": output_format,
        }

        result = await self._api_request(
            "POST", "/background-removal/run", data={"input": input_data}
        )

        prediction_id = result.get("id")

        if prediction_id:
            task = await self._poll_prediction(prediction_id)
            image_url = task.output[0] if task.output else None
        else:
            output = result.get("output", [])
            image_url = output[0] if output else None

        if not image_url:
            raise Exception("No output generated")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_name = Path(image_path).stem
        filename = f"{original_name}_nobg_{timestamp}.{output_format}"

        return await self._download_image(image_url, filename)

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    async def get_prediction(self, prediction_id: str) -> FashnTask:
        """Get prediction status"""
        result = await self._api_request("GET", f"/predictions/{prediction_id}")

        return FashnTask(
            id=prediction_id,
            status=FashnTaskStatus(result.get("status", "processing")),
            output=result.get("output"),
            error=result.get("error"),
        )

    async def cancel_prediction(self, prediction_id: str) -> bool:
        """Cancel a running prediction"""
        try:
            await self._api_request("POST", f"/predictions/{prediction_id}/cancel")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel: {e}")
            return False
