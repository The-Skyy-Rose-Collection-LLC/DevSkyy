"""SkyyRose LoRA Image Generator.

Generates product images using the custom-trained SkyyRose LoRA v3 model.
Trained on 390 exact product images from the SkyyRose catalog.

Model: devskyy/skyyrose-lora-v3
Trigger word: skyyrose
Version: 64dbb859fed83670e7cde81fc161c183bd9d0607fb7028b01bfc0a000ec114b4

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

logger = logging.getLogger(__name__)


class SkyyRoseCollection(str, Enum):
    """SkyyRose collection types."""

    SIGNATURE = "SIGNATURE"
    BLACK_ROSE = "BLACK_ROSE"
    LOVE_HURTS = "LOVE_HURTS"


class GarmentType(str, Enum):
    """Supported garment types."""

    HOODIE = "hoodie"
    TEE = "tee"
    BEANIE = "beanie"
    SHORTS = "shorts"
    JACKET = "jacket"
    WINDBREAKER = "windbreaker"
    SHERPA = "sherpa"
    BOMBER = "bomber"
    JOGGERS = "joggers"
    DRESS = "dress"
    ACCESSORY = "accessory"


@dataclass
class LoRAGenerationConfig:
    """Configuration for LoRA image generation."""

    prompt: str
    collection: SkyyRoseCollection = SkyyRoseCollection.SIGNATURE
    garment_type: GarmentType | None = None
    num_outputs: int = 1
    guidance_scale: float = 3.5
    num_inference_steps: int = 28
    output_format: str = "webp"
    output_quality: int = 90
    seed: int | None = None
    aspect_ratio: str = "1:1"
    disable_safety_checker: bool = False


@dataclass
class LoRAGenerationResult:
    """Result of LoRA image generation."""

    id: str
    success: bool
    output_urls: list[str] = field(default_factory=list)
    prompt: str = ""
    enhanced_prompt: str = ""
    collection: str = ""
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# Collection style mappings
COLLECTION_STYLES = {
    SkyyRoseCollection.SIGNATURE: {
        "style": "signature collection, lavender rose, classic elegant, timeless",
        "colors": "lavender, rose gold, soft pastels, cream white",
        "mood": "refined, versatile, foundation wardrobe",
    },
    SkyyRoseCollection.BLACK_ROSE: {
        "style": "black_rose collection, dark elegance, gothic luxury, midnight",
        "colors": "obsidian black, deep burgundy, silver accents",
        "mood": "mysterious, sophisticated, limited edition",
    },
    SkyyRoseCollection.LOVE_HURTS: {
        "style": "love_hurts collection, bold red, emotional expression, urban",
        "colors": "vivid red, black contrast, white accents",
        "mood": "vulnerable strength, authentic rebellion, bold statements",
    },
}

# Garment descriptions
GARMENT_DESCRIPTIONS = {
    GarmentType.HOODIE: "premium heavyweight hoodie, relaxed fit, embroidered details",
    GarmentType.TEE: "soft cotton tee, premium fabric, screen printed graphics",
    GarmentType.BEANIE: "knit beanie, embroidered rose logo, cozy winter accessory",
    GarmentType.SHORTS: "athletic shorts, comfortable fit, branded waistband",
    GarmentType.JACKET: "structured jacket, premium construction, statement piece",
    GarmentType.WINDBREAKER: "lightweight windbreaker, water resistant, retro athletic",
    GarmentType.SHERPA: "sherpa jacket, plush fleece, streetwear luxury",
    GarmentType.BOMBER: "bomber jacket, satin finish, embroidered back panel",
    GarmentType.JOGGERS: "jogger pants, tapered fit, side stripe detail",
    GarmentType.DRESS: "hooded dress, casual elegance, versatile styling",
    GarmentType.ACCESSORY: "branded accessory, premium materials, functional luxury",
}


class SkyyRoseLoRAGenerator:
    """
    Generate SkyyRose product images using custom-trained LoRA.

    The LoRA was trained on 390 exact SkyyRose product images including:
    - SIGNATURE collection (lavender, pastels, rose gold)
    - BLACK_ROSE collection (dark elegance, gothic)
    - LOVE_HURTS collection (bold red, emotional)

    Usage:
        generator = SkyyRoseLoRAGenerator()

        # Generate a beanie
        result = await generator.generate(
            prompt="lavender rose beanie",
            collection=SkyyRoseCollection.SIGNATURE,
            garment_type=GarmentType.BEANIE,
        )

        # Generate using config
        config = LoRAGenerationConfig(
            prompt="black sherpa jacket with rose embroidery",
            collection=SkyyRoseCollection.BLACK_ROSE,
            num_outputs=4,
        )
        result = await generator.generate_from_config(config)
    """

    # Model configuration
    MODEL_ID = "devskyy/skyyrose-lora-v3"
    MODEL_VERSION = "64dbb859fed83670e7cde81fc161c183bd9d0607fb7028b01bfc0a000ec114b4"  # pragma: allowlist secret
    TRIGGER_WORD = "skyyrose"
    API_BASE = "https://api.replicate.com/v1"

    def __init__(self, api_token: str | None = None) -> None:
        """
        Initialize the SkyyRose LoRA generator.

        Args:
            api_token: Replicate API token (or set REPLICATE_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not configured")

        self._generation_history: list[LoRAGenerationResult] = []

    def _build_prompt(
        self,
        prompt: str,
        collection: SkyyRoseCollection,
        garment_type: GarmentType | None = None,
    ) -> str:
        """Build enhanced prompt with brand DNA and trigger word."""
        parts = [self.TRIGGER_WORD]

        # Add collection style
        collection_data = COLLECTION_STYLES.get(
            collection, COLLECTION_STYLES[SkyyRoseCollection.SIGNATURE]
        )
        parts.append(collection_data["style"])

        # Add garment description if specified
        if garment_type and garment_type in GARMENT_DESCRIPTIONS:
            parts.append(GARMENT_DESCRIPTIONS[garment_type])

        # Add user prompt
        parts.append(prompt)

        # Add quality keywords
        parts.extend(
            [
                "luxury streetwear",
                "product photography",
                "studio lighting",
                "white background",
                "high quality",
                "professional photo",
            ]
        )

        return ", ".join(parts)

    async def generate(
        self,
        prompt: str,
        collection: SkyyRoseCollection = SkyyRoseCollection.SIGNATURE,
        garment_type: GarmentType | None = None,
        num_outputs: int = 1,
        **kwargs,
    ) -> LoRAGenerationResult:
        """
        Generate SkyyRose product images.

        Args:
            prompt: Product description
            collection: SkyyRose collection
            garment_type: Type of garment
            num_outputs: Number of images (1-4)
            **kwargs: Additional generation parameters

        Returns:
            LoRAGenerationResult with output URLs
        """
        config = LoRAGenerationConfig(
            prompt=prompt,
            collection=collection,
            garment_type=garment_type,
            num_outputs=num_outputs,
            **kwargs,
        )
        return await self.generate_from_config(config)

    async def generate_from_config(self, config: LoRAGenerationConfig) -> LoRAGenerationResult:
        """
        Generate images using a configuration object.

        Args:
            config: LoRAGenerationConfig with all parameters

        Returns:
            LoRAGenerationResult with output URLs
        """
        result_id = str(uuid4())[:16]
        start_time = time.time()

        if not self.api_token:
            return LoRAGenerationResult(
                id=result_id,
                success=False,
                prompt=config.prompt,
                error="REPLICATE_API_TOKEN not configured",
            )

        try:
            # Build enhanced prompt
            enhanced_prompt = self._build_prompt(
                config.prompt,
                config.collection,
                config.garment_type,
            )

            # Prepare API request
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }

            input_params = {
                "prompt": enhanced_prompt,
                "num_outputs": min(config.num_outputs, 4),
                "guidance_scale": config.guidance_scale,
                "num_inference_steps": config.num_inference_steps,
                "output_format": config.output_format,
                "output_quality": config.output_quality,
                "disable_safety_checker": config.disable_safety_checker,
            }

            if config.seed is not None:
                input_params["seed"] = config.seed

            if config.aspect_ratio != "1:1":
                input_params["aspect_ratio"] = config.aspect_ratio

            # Create prediction
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.API_BASE}/predictions",
                    headers=headers,
                    json={
                        "version": self.MODEL_VERSION,
                        "input": input_params,
                    },
                )

                if response.status_code not in (200, 201):
                    return LoRAGenerationResult(
                        id=result_id,
                        success=False,
                        prompt=config.prompt,
                        enhanced_prompt=enhanced_prompt,
                        error=f"API error {response.status_code}: {response.text[:200]}",
                        latency_ms=(time.time() - start_time) * 1000,
                    )

                prediction = response.json()
                pred_id = prediction.get("id")

                # Poll for completion
                status = prediction.get("status")
                while status in ("starting", "processing"):
                    await httpx.AsyncClient().aclose()
                    import asyncio

                    await asyncio.sleep(2)

                    poll_response = await client.get(
                        f"{self.API_BASE}/predictions/{pred_id}",
                        headers=headers,
                    )
                    if poll_response.status_code == 200:
                        prediction = poll_response.json()
                        status = prediction.get("status")

                if status == "succeeded":
                    output = prediction.get("output", [])
                    output_urls = list(output) if isinstance(output, list) else [output]

                    latency_ms = (time.time() - start_time) * 1000
                    cost_usd = 0.003 * config.num_outputs  # Estimated Flux LoRA cost

                    result = LoRAGenerationResult(
                        id=result_id,
                        success=True,
                        output_urls=output_urls,
                        prompt=config.prompt,
                        enhanced_prompt=enhanced_prompt,
                        collection=config.collection.value,
                        latency_ms=latency_ms,
                        cost_usd=cost_usd,
                        metadata={
                            "prediction_id": pred_id,
                            "model": f"{self.MODEL_ID}:{self.MODEL_VERSION[:12]}",
                            "garment_type": (
                                config.garment_type.value if config.garment_type else None
                            ),
                            "num_outputs": config.num_outputs,
                            "guidance_scale": config.guidance_scale,
                            "steps": config.num_inference_steps,
                        },
                    )
                else:
                    result = LoRAGenerationResult(
                        id=result_id,
                        success=False,
                        prompt=config.prompt,
                        enhanced_prompt=enhanced_prompt,
                        error=prediction.get("error") or f"Generation failed: {status}",
                        latency_ms=(time.time() - start_time) * 1000,
                    )

            # Record history
            self._generation_history.append(result)
            if len(self._generation_history) > 500:
                self._generation_history = self._generation_history[-500:]

            return result

        except Exception as e:
            logger.exception(f"LoRA generation error: {e}")
            return LoRAGenerationResult(
                id=result_id,
                success=False,
                prompt=config.prompt,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000,
            )

    async def generate_product_set(
        self,
        product_name: str,
        collection: SkyyRoseCollection,
        garment_type: GarmentType,
        angles: list[str] | None = None,
    ) -> dict[str, LoRAGenerationResult]:
        """
        Generate a complete product image set with multiple angles.

        Args:
            product_name: Name of the product
            collection: SkyyRose collection
            garment_type: Type of garment
            angles: List of angles (default: front, back, detail)

        Returns:
            Dict mapping angle names to generation results
        """
        if angles is None:
            angles = ["front view", "back view", "detail closeup"]

        results = {}
        for angle in angles:
            prompt = f"{product_name}, {angle}"
            result = await self.generate(
                prompt=prompt,
                collection=collection,
                garment_type=garment_type,
            )
            results[angle] = result

        return results

    def get_history(self, limit: int = 100) -> list[LoRAGenerationResult]:
        """Get generation history."""
        return self._generation_history[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get generation statistics."""
        total = len(self._generation_history)
        successful = sum(1 for r in self._generation_history if r.success)
        total_cost = sum(r.cost_usd for r in self._generation_history)
        avg_latency = (
            sum(r.latency_ms for r in self._generation_history) / total if total > 0 else 0
        )

        collection_counts = {}
        for r in self._generation_history:
            c = r.collection or "unknown"
            collection_counts[c] = collection_counts.get(c, 0) + 1

        return {
            "total_generations": total,
            "successful": successful,
            "success_rate": successful / total if total > 0 else 0,
            "total_cost_usd": total_cost,
            "avg_latency_ms": avg_latency,
            "by_collection": collection_counts,
            "model": f"{self.MODEL_ID}:{self.MODEL_VERSION[:12]}",
        }

    async def download_images(
        self,
        result: LoRAGenerationResult,
        output_dir: Path | str,
        prefix: str = "skyyrose",
    ) -> list[Path]:
        """
        Download generated images to local files.

        Args:
            result: Generation result with output URLs
            output_dir: Directory to save images
            prefix: Filename prefix

        Returns:
            List of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        async with httpx.AsyncClient() as client:
            for i, url in enumerate(result.output_urls):
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        # Determine extension from URL or content-type
                        ext = "webp"
                        if ".png" in url:
                            ext = "png"
                        elif ".jpg" in url or ".jpeg" in url:
                            ext = "jpg"

                        filename = f"{prefix}_{result.id}_{i + 1}.{ext}"
                        file_path = output_dir / filename

                        file_path.write_bytes(response.content)
                        saved_paths.append(file_path)
                        logger.info(f"Saved: {file_path}")

                except Exception as e:
                    logger.warning(f"Failed to download {url}: {e}")

        return saved_paths


# Convenience function
async def generate_skyyrose_image(
    prompt: str,
    collection: str = "SIGNATURE",
    garment_type: str | None = None,
    num_outputs: int = 1,
) -> LoRAGenerationResult:
    """
    Quick function to generate SkyyRose product image.

    Args:
        prompt: Product description
        collection: Collection name (SIGNATURE, BLACK_ROSE, LOVE_HURTS)
        garment_type: Optional garment type
        num_outputs: Number of images

    Returns:
        LoRAGenerationResult

    Example:
        result = await generate_skyyrose_image(
            "lavender beanie with rose embroidery",
            collection="SIGNATURE",
            garment_type="beanie"
        )
    """
    generator = SkyyRoseLoRAGenerator()

    col = SkyyRoseCollection[collection.upper()]
    gt = GarmentType[garment_type.upper()] if garment_type else None

    return await generator.generate(
        prompt=prompt,
        collection=col,
        garment_type=gt,
        num_outputs=num_outputs,
    )


__all__ = [
    "SkyyRoseCollection",
    "GarmentType",
    "LoRAGenerationConfig",
    "LoRAGenerationResult",
    "SkyyRoseLoRAGenerator",
    "generate_skyyrose_image",
    "COLLECTION_STYLES",
    "GARMENT_DESCRIPTIONS",
]
