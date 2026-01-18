"""
Google Vertex AI / Imagen 3 Client
==================================

Client for Google's Imagen 3 API via Vertex AI - Next-generation image generation.

Key capabilities for DevSkyy:
- Imagen 3 Generate: 8K photorealistic image generation
- Imagen 3 Fast: Rapid generation for previews
- Advanced editing: Mask-free image editing
- Safety controls: Granular content filtering
- Person generation: Fashion model/lifestyle shots

Reference: https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

# Import config for API keys
try:
    from config import settings

    GOOGLE_PROJECT_ID = getattr(settings, "GOOGLE_PROJECT_ID", "") or os.getenv(
        "GOOGLE_PROJECT_ID", ""
    )
    GOOGLE_LOCATION = getattr(settings, "GOOGLE_LOCATION", "") or os.getenv(
        "GOOGLE_LOCATION", "us-central1"
    )
except ImportError:
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_LOCATION = os.getenv("GOOGLE_LOCATION", "us-central1")

logger = logging.getLogger(__name__)


# Type aliases for clarity
AspectRatio = Literal["1:1", "9:16", "16:9", "3:4", "4:3", "2:3", "3:2", "9:21", "21:9"]
SafetyLevel = Literal["block_none", "block_few", "block_some", "block_most"]
PersonGeneration = Literal["dont_allow", "allow_adult"]


class VertexImagenClient:
    """
    Google Vertex AI Imagen 3 Client for photorealistic image generation.

    Capabilities:
    - Text-to-Image: Imagen 3 (highest quality), Imagen 3 Fast (speed)
    - Image Editing: Mask-free editing via text descriptions
    - Upscaling: 2x-4x creative upscaling
    - Style Control: Photographic, artistic, anime, etc.

    Usage:
        client = VertexImagenClient(project_id="your-project")

        # Generate product image
        images = await client.generate(
            "luxury fashion hoodie, skyyrose brand, studio lighting, 8k resolution",
            aspect_ratio="3:4"
        )

        # Edit existing image
        edited = await client.edit(
            "product.jpg",
            prompt="change the hoodie color to rose gold"
        )

    Requirements:
        pip install google-cloud-aiplatform
    """

    # Available models
    MODELS = {
        "imagen-3": "imagen-3.0-generate-001",  # Highest quality
        "imagen-3-fast": "imagen-3.0-fast-generate-001",  # Fast generation
    }

    # Recommended aspect ratios for fashion/e-commerce
    ASPECT_RATIOS = {
        "square": "1:1",  # Social media, thumbnails
        "portrait": "3:4",  # Product cards
        "portrait-tall": "9:16",  # Stories, mobile
        "landscape": "4:3",  # Website banners
        "widescreen": "16:9",  # Hero images
        "ultrawide": "21:9",  # Panoramic
    }

    def __init__(
        self,
        project_id: str | None = None,
        location: str | None = None,
    ) -> None:
        """
        Initialize the Vertex AI Imagen client.

        Args:
            project_id: Google Cloud project ID (or set GOOGLE_PROJECT_ID env var)
            location: Vertex AI location (default: us-central1)
        """
        self.project_id = project_id or GOOGLE_PROJECT_ID
        self.location = location or GOOGLE_LOCATION

        if not self.project_id:
            logger.warning("GOOGLE_PROJECT_ID not configured")

        self._model = None
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Lazy-initialize Vertex AI client."""
        if self._initialized:
            return

        try:
            import vertexai
            from vertexai.preview.vision_models import ImageGenerationModel

            vertexai.init(project=self.project_id, location=self.location)
            self._model = ImageGenerationModel.from_pretrained(self.MODELS["imagen-3"])
            self._initialized = True
            logger.info(f"Vertex AI initialized: {self.project_id}/{self.location}")

        except ImportError:
            raise ImportError(
                "Install google-cloud-aiplatform: pip install google-cloud-aiplatform"
            )
        except Exception as e:
            logger.error(f"Vertex AI initialization failed: {e}")
            raise

    def _load_image(self, image_path: str) -> bytes:
        """Load image from path or URL."""
        if image_path.startswith(("http://", "https://")):
            try:
                import httpx

                response = httpx.get(image_path, timeout=30.0)
                response.raise_for_status()
                return response.content
            except ImportError:
                import urllib.request

                with urllib.request.urlopen(image_path) as response:
                    return response.read()
        return Path(image_path).read_bytes()

    async def generate(
        self,
        prompt: str,
        *,
        number_of_images: int = 1,
        aspect_ratio: AspectRatio = "1:1",
        safety_filter_level: SafetyLevel = "block_some",
        person_generation: PersonGeneration = "allow_adult",
        negative_prompt: str | None = None,
        seed: int | None = None,
        model: str = "imagen-3",
        **kwargs,
    ) -> list[bytes]:
        """
        Generate images from text prompt using Imagen 3.

        Args:
            prompt: Text description of desired image
            number_of_images: Number of images to generate (1-4)
            aspect_ratio: Image dimensions (1:1, 16:9, 9:16, 3:4, 4:3, etc.)
            safety_filter_level: Content safety filtering
            person_generation: Whether to allow person generation
            negative_prompt: What to avoid (optional)
            seed: Random seed for reproducibility
            model: Model variant (imagen-3, imagen-3-fast)

        Returns:
            List of image bytes (PNG format)

        Example:
            images = await client.generate(
                "skyyrose signature collection hoodie, luxury fashion, "
                "professional product photography, studio lighting, "
                "white background, 8k resolution",
                aspect_ratio="3:4",
                person_generation="dont_allow"
            )
        """
        await self._ensure_initialized()

        # Switch model if requested
        if model != "imagen-3" and model in self.MODELS:
            from vertexai.preview.vision_models import ImageGenerationModel

            self._model = ImageGenerationModel.from_pretrained(self.MODELS[model])

        logger.info(f"Generating with Imagen 3: {prompt[:50]}...")

        # Build generation parameters
        gen_params = {
            "prompt": prompt,
            "number_of_images": min(number_of_images, 4),
            "aspect_ratio": aspect_ratio,
            "safety_filter_level": safety_filter_level,
            "person_generation": person_generation,
        }

        if negative_prompt:
            gen_params["negative_prompt"] = negative_prompt
        if seed is not None:
            gen_params["seed"] = seed

        # Generate images
        response = self._model.generate_images(**gen_params)

        # Extract image bytes
        images = []
        for idx, image in enumerate(response.images):
            # Save to bytes
            import io

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            images.append(buffer.getvalue())
            logger.debug(f"Generated image {idx + 1}/{len(response.images)}")

        logger.info(f"Generated {len(images)} images")
        return images

    async def generate_fast(
        self,
        prompt: str,
        *,
        number_of_images: int = 1,
        aspect_ratio: AspectRatio = "1:1",
        **kwargs,
    ) -> list[bytes]:
        """
        Generate images quickly using Imagen 3 Fast.

        Faster generation (~2s vs ~5s) with slightly lower quality.
        Good for previews and iterations.

        Args:
            prompt: Text description
            number_of_images: Number of images (1-4)
            aspect_ratio: Image dimensions

        Returns:
            List of image bytes
        """
        return await self.generate(
            prompt,
            number_of_images=number_of_images,
            aspect_ratio=aspect_ratio,
            model="imagen-3-fast",
            **kwargs,
        )

    async def edit(
        self,
        image_path: str,
        prompt: str,
        *,
        mask_path: str | None = None,
        number_of_images: int = 1,
        edit_mode: Literal[
            "inpainting-insert", "inpainting-remove", "outpainting", "product-image"
        ] = "inpainting-insert",
        **kwargs,
    ) -> list[bytes]:
        """
        Edit an existing image using text instructions.

        Imagen 3 supports mask-free editing - just describe the change.

        Args:
            image_path: Path to source image or URL
            prompt: Description of desired edit
            mask_path: Optional mask for targeted edits
            number_of_images: Number of variations
            edit_mode: Edit operation type:
                - inpainting-insert: Add elements to image (default)
                - inpainting-remove: Remove elements from image
                - outpainting: Extend image boundaries
                - product-image: Product-specific editing

        Returns:
            List of edited image bytes

        Example:
            # Change hoodie color (mask-free)
            edited = await client.edit(
                "hoodie_black.jpg",
                "change the hoodie to rose gold color, keep everything else"
            )

            # Replace background
            edited = await client.edit(
                "product.jpg",
                "replace background with professional studio setting",
                edit_mode="product-image"
            )
        """
        await self._ensure_initialized()

        from vertexai.preview.vision_models import Image

        # Load source image
        image_bytes = self._load_image(image_path)
        source_image = Image(image_bytes)

        logger.info(f"Editing image ({edit_mode}): {prompt[:50]}...")

        # Load mask if provided
        mask_image = None
        if mask_path:
            mask_bytes = self._load_image(mask_path)
            mask_image = Image(mask_bytes)

        # Build edit parameters
        edit_params = {
            "prompt": prompt,
            "base_image": source_image,
            "number_of_images": number_of_images,
            "edit_mode": edit_mode,
        }
        if mask_image:
            edit_params["mask"] = mask_image

        # Edit image
        response = self._model.edit_image(**edit_params)

        # Extract results
        images = []
        for image in response.images:
            import io

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            images.append(buffer.getvalue())

        logger.info(f"Edited {len(images)} images")
        return images

    async def upscale(
        self,
        image_path: str,
        *,
        upscale_factor: Literal["x2", "x4"] = "x2",
    ) -> bytes:
        """
        Upscale image with AI enhancement.

        Args:
            image_path: Path to source image
            upscale_factor: Upscaling factor (x2 or x4)

        Returns:
            Upscaled image bytes
        """
        await self._ensure_initialized()

        from vertexai.preview.vision_models import Image

        image_bytes = self._load_image(image_path)
        source_image = Image(image_bytes)

        logger.info(f"Upscaling image: {upscale_factor}")

        response = self._model.upscale_image(
            image=source_image,
            upscale_factor=upscale_factor,
        )

        import io

        buffer = io.BytesIO()
        response.images[0].save(buffer, format="PNG")

        logger.info("Upscaling complete")
        return buffer.getvalue()

    async def generate_product_image(
        self,
        product_name: str,
        collection: str = "signature",
        *,
        style: str = "product_photo",
        background: str = "white studio",
        aspect_ratio: AspectRatio = "3:4",
        **kwargs,
    ) -> list[bytes]:
        """
        Generate SkyyRose product image with brand DNA.

        Args:
            product_name: Product name (e.g., "lavender rose beanie")
            collection: SkyyRose collection (signature, black_rose, love_hurts)
            style: Image style (product_photo, lifestyle, editorial)
            background: Background description
            aspect_ratio: Image dimensions

        Returns:
            List of brand-aligned product images

        Example:
            images = await client.generate_product_image(
                "lavender rose beanie",
                collection="signature",
                style="lifestyle"
            )
        """
        # Collection-specific styling
        collection_styles = {
            "signature": "luxury elegance, rose gold accents, timeless sophistication",
            "black_rose": "dark romantic aesthetic, gothic elegance, premium materials",
            "love_hurts": "bold emotional design, heart motifs, vulnerable strength",
        }

        style_prompts = {
            "product_photo": f"professional product photography, {background} background, studio lighting, 8k resolution, commercial quality",
            "lifestyle": "lifestyle photography, urban setting, natural lighting, authentic, candid moment",
            "editorial": "high fashion editorial, dramatic lighting, artistic composition, magazine quality",
        }

        # Build prompt with brand DNA
        prompt = (
            f"skyyrose {collection} collection, {product_name}, "
            f"{collection_styles.get(collection, 'luxury fashion')}, "
            f"{style_prompts.get(style, style_prompts['product_photo'])}, "
            f"oakland bay area streetwear meets high fashion"
        )

        return await self.generate(
            prompt,
            aspect_ratio=aspect_ratio,
            person_generation="dont_allow" if style == "product_photo" else "allow_adult",
            **kwargs,
        )

    async def generate_lifestyle_shot(
        self,
        product_name: str,
        scenario: str,
        *,
        model_description: str = "fashion model",
        collection: str = "signature",
        aspect_ratio: AspectRatio = "16:9",
        **kwargs,
    ) -> list[bytes]:
        """
        Generate lifestyle/lookbook images with models.

        Args:
            product_name: Product being worn
            scenario: Scene description (e.g., "urban rooftop at golden hour")
            model_description: Model characteristics
            collection: SkyyRose collection
            aspect_ratio: Image dimensions (16:9 for hero, 9:16 for stories)

        Returns:
            Lifestyle image bytes

        Example:
            images = await client.generate_lifestyle_shot(
                "sherpa jacket",
                scenario="urban oakland street, golden hour",
                model_description="confident young professional"
            )
        """
        collection_vibes = {
            "signature": "timeless elegance, sophisticated",
            "black_rose": "dark romantic, mysterious",
            "love_hurts": "emotionally expressive, bold",
        }

        prompt = (
            f"{model_description} wearing skyyrose {collection} {product_name}, "
            f"{scenario}, {collection_vibes.get(collection, 'luxury streetwear')}, "
            f"editorial photography, natural lighting, authentic moment, "
            f"8k resolution, fashion magazine quality"
        )

        return await self.generate(
            prompt,
            aspect_ratio=aspect_ratio,
            person_generation="allow_adult",
            safety_filter_level="block_few",
            **kwargs,
        )


__all__ = ["VertexImagenClient"]
