"""
Stability AI Client
===================

Client for Stability AI API - Professional image generation and editing.

Key capabilities for DevSkyy:
- SDXL 1.0 image generation (highest quality product renders)
- Image-to-image transformation (style transfer, variations)
- Inpainting (product background replacement)
- Outpainting (extend product images)
- Upscaling (4x enhancement)
- Control modes (sketch-to-image, structure guidance)

Reference: https://platform.stability.ai/docs/api-reference
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

# Import config for API keys (loads .env.hf)
try:
    from config import settings

    STABILITY_API_KEY = getattr(settings, "STABILITY_API_KEY", "") or os.getenv(
        "STABILITY_API_KEY", ""
    )
except ImportError:
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")

logger = logging.getLogger(__name__)


class StabilityClient:
    """
    Stability AI API Client for professional image generation.

    Capabilities:
    - Text-to-Image: SDXL 1.0, SD 3.0
    - Image-to-Image: Style transfer, variations
    - Inpainting: Background replacement, object removal
    - Outpainting: Extend image boundaries
    - Upscaling: 4x creative upscaling
    - Control: Sketch, structure, style guidance

    Usage:
        client = StabilityClient()

        # Generate product image
        images = await client.generate(
            "luxury fashion hoodie, skyyrose brand, studio lighting, white background",
            style_preset="photographic"
        )

        # Create variations
        variations = await client.image_to_image(
            "product.jpg",
            prompt="same hoodie in lavender color",
            strength=0.7
        )

        # Replace background
        result = await client.inpaint(
            "product.jpg",
            mask="background_mask.png",
            prompt="professional studio backdrop, soft lighting"
        )
    """

    BASE_URL = "https://api.stability.ai"

    # Available engines
    ENGINES = {
        "sdxl": "stable-diffusion-xl-1024-v1-0",
        "sd-3": "sd3",
        "sd-3-turbo": "sd3-turbo",
        "core": "stable-image-core",
        "ultra": "stable-image-ultra",
    }

    # Style presets for fashion/e-commerce
    STYLE_PRESETS = [
        "photographic",  # Best for product photos
        "digital-art",  # Stylized renders
        "cinematic",  # Dramatic lighting
        "analog-film",  # Vintage aesthetic
        "neon-punk",  # Bold urban style
        "enhance",  # Photo enhancement
        "3d-model",  # 3D-like renders
        "low-poly",  # Stylized graphics
    ]

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the Stability AI client.

        Args:
            api_key: Stability API key (or set STABILITY_API_KEY env var)
        """
        self.api_key = api_key or STABILITY_API_KEY
        if not self.api_key:
            logger.warning("STABILITY_API_KEY not configured")

        self._client = None

    async def _get_client(self):
        """Lazy-load the HTTP client."""
        if self._client is None:
            try:
                import httpx

                self._client = httpx.AsyncClient(
                    base_url=self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json",
                    },
                    timeout=120.0,
                )
            except ImportError:
                raise ImportError("Install httpx: pip install httpx")
        return self._client

    def _load_image(self, image_path: str) -> bytes:
        """Load image from path or URL."""
        if image_path.startswith(("http://", "https://")):
            import httpx

            response = httpx.get(image_path)
            return response.content
        return Path(image_path).read_bytes()

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "low quality, blurry, distorted, ugly, deformed",
        engine: str = "sdxl",
        width: int = 1024,
        height: int = 1024,
        samples: int = 1,
        steps: int = 30,
        cfg_scale: float = 7.0,
        style_preset: str | None = "photographic",
        seed: int | None = None,
        **kwargs,
    ) -> list[bytes]:
        """
        Generate images from text prompt.

        Args:
            prompt: Text description of desired image
            negative_prompt: What to avoid in generation
            engine: Model to use (sdxl, sd-3, core, ultra)
            width: Image width (1024 for SDXL)
            height: Image height (1024 for SDXL)
            samples: Number of images to generate (1-10)
            steps: Denoising steps (20-50)
            cfg_scale: Prompt adherence (5-15)
            style_preset: Visual style (photographic, cinematic, etc.)
            seed: Random seed for reproducibility

        Returns:
            List of image bytes

        Example:
            images = await client.generate(
                "skyyrose signature collection hoodie, luxury fashion, "
                "studio lighting, white background, professional product photo",
                style_preset="photographic"
            )
        """
        client = await self._get_client()
        engine_id = self.ENGINES.get(engine, engine)

        # Use appropriate API based on engine
        if engine in ("core", "ultra", "sd-3", "sd-3-turbo"):
            return await self._generate_v2(
                prompt=prompt,
                negative_prompt=negative_prompt,
                model=engine,
                aspect_ratio=self._get_aspect_ratio(width, height),
                seed=seed,
                **kwargs,
            )

        # SDXL generation
        payload = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
                {"text": negative_prompt, "weight": -1.0},
            ],
            "cfg_scale": cfg_scale,
            "width": width,
            "height": height,
            "samples": samples,
            "steps": steps,
        }

        if style_preset:
            payload["style_preset"] = style_preset
        if seed is not None:
            payload["seed"] = seed

        logger.info(f"Generating with {engine}: {prompt[:50]}...")

        response = await client.post(
            f"/v1/generation/{engine_id}/text-to-image",
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        images = []
        for artifact in result.get("artifacts", []):
            if artifact.get("finishReason") == "SUCCESS":
                images.append(base64.b64decode(artifact["base64"]))

        return images

    async def _generate_v2(
        self,
        prompt: str,
        negative_prompt: str = "",
        model: str = "core",
        aspect_ratio: str = "1:1",
        seed: int | None = None,
        output_format: str = "png",
        **kwargs,
    ) -> list[bytes]:
        """Generate using v2beta API (Core, Ultra, SD3)."""
        client = await self._get_client()

        # Build multipart form data
        data = {
            "prompt": prompt,
            "output_format": output_format,
            "aspect_ratio": aspect_ratio,
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if seed is not None:
            data["seed"] = str(seed)

        endpoint = f"/v2beta/stable-image/generate/{model}"

        response = await client.post(
            endpoint,
            data=data,
            headers={"Accept": "image/*"},
        )
        response.raise_for_status()

        return [response.content]

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """Convert dimensions to aspect ratio string."""
        ratios = {
            (1024, 1024): "1:1",
            (1152, 896): "4:3",
            (896, 1152): "3:4",
            (1216, 832): "3:2",
            (832, 1216): "2:3",
            (1344, 768): "16:9",
            (768, 1344): "9:16",
            (1536, 640): "21:9",
            (640, 1536): "9:21",
        }
        return ratios.get((width, height), "1:1")

    async def image_to_image(
        self,
        image_path: str,
        prompt: str,
        negative_prompt: str = "low quality, blurry",
        strength: float = 0.7,
        engine: str = "sdxl",
        cfg_scale: float = 7.0,
        steps: int = 30,
        style_preset: str | None = "photographic",
        **kwargs,
    ) -> list[bytes]:
        """
        Transform an existing image based on prompt.

        Args:
            image_path: Path to source image or URL
            prompt: Description of desired transformation
            negative_prompt: What to avoid
            strength: How much to change (0.0-1.0, higher = more change)
            engine: Model to use
            cfg_scale: Prompt adherence
            steps: Denoising steps
            style_preset: Visual style

        Returns:
            List of transformed image bytes

        Example:
            # Create color variation
            images = await client.image_to_image(
                "hoodie_black.jpg",
                prompt="same hoodie in rose gold color, luxury fabric",
                strength=0.6
            )
        """
        client = await self._get_client()
        engine_id = self.ENGINES.get(engine, engine)

        image_data = self._load_image(image_path)

        files = {
            "init_image": ("image.png", image_data, "image/png"),
        }

        data = {
            "text_prompts[0][text]": prompt,
            "text_prompts[0][weight]": "1.0",
            "text_prompts[1][text]": negative_prompt,
            "text_prompts[1][weight]": "-1.0",
            "cfg_scale": str(cfg_scale),
            "image_strength": str(1 - strength),
            "steps": str(steps),
        }

        if style_preset:
            data["style_preset"] = style_preset

        response = await client.post(
            f"/v1/generation/{engine_id}/image-to-image",
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()

        images = []
        for artifact in result.get("artifacts", []):
            if artifact.get("finishReason") == "SUCCESS":
                images.append(base64.b64decode(artifact["base64"]))

        return images

    async def inpaint(
        self,
        image_path: str,
        mask_path: str,
        prompt: str,
        negative_prompt: str = "low quality, blurry",
        engine: str = "sdxl",
        cfg_scale: float = 7.0,
        steps: int = 30,
        **kwargs,
    ) -> list[bytes]:
        """
        Inpaint masked regions of an image.

        Args:
            image_path: Path to source image
            mask_path: Path to mask (white = inpaint, black = keep)
            prompt: Description of what to generate in masked area
            negative_prompt: What to avoid
            engine: Model to use
            cfg_scale: Prompt adherence
            steps: Denoising steps

        Returns:
            List of inpainted image bytes

        Example:
            # Replace background
            images = await client.inpaint(
                "product.jpg",
                "background_mask.png",
                prompt="professional studio backdrop, soft gradient lighting"
            )
        """
        client = await self._get_client()
        engine_id = self.ENGINES.get(engine, engine)

        image_data = self._load_image(image_path)
        mask_data = self._load_image(mask_path)

        files = {
            "init_image": ("image.png", image_data, "image/png"),
            "mask_image": ("mask.png", mask_data, "image/png"),
        }

        data = {
            "text_prompts[0][text]": prompt,
            "text_prompts[0][weight]": "1.0",
            "text_prompts[1][text]": negative_prompt,
            "text_prompts[1][weight]": "-1.0",
            "cfg_scale": str(cfg_scale),
            "steps": str(steps),
            "mask_source": "MASK_IMAGE_WHITE",
        }

        response = await client.post(
            f"/v1/generation/{engine_id}/image-to-image/masking",
            data=data,
            files=files,
        )
        response.raise_for_status()
        result = response.json()

        images = []
        for artifact in result.get("artifacts", []):
            if artifact.get("finishReason") == "SUCCESS":
                images.append(base64.b64decode(artifact["base64"]))

        return images

    async def upscale(
        self,
        image_path: str,
        prompt: str | None = None,
        creativity: float = 0.3,
        output_format: str = "png",
    ) -> bytes:
        """
        Upscale image with creative enhancement.

        Args:
            image_path: Path to source image
            prompt: Optional prompt to guide enhancement
            creativity: How creative the upscaling should be (0-0.35)
            output_format: Output format (png, jpeg, webp)

        Returns:
            Upscaled image bytes

        Example:
            upscaled = await client.upscale(
                "product_small.jpg",
                prompt="luxury fashion product, sharp details"
            )
        """
        client = await self._get_client()
        image_data = self._load_image(image_path)

        files = {
            "image": ("image.png", image_data, "image/png"),
        }

        data = {
            "output_format": output_format,
        }

        if prompt:
            data["prompt"] = prompt
        if creativity:
            data["creativity"] = str(creativity)

        response = await client.post(
            "/v2beta/stable-image/upscale/creative",
            data=data,
            files=files,
            headers={"Accept": "image/*"},
        )
        response.raise_for_status()

        return response.content

    async def outpaint(
        self,
        image_path: str,
        prompt: str,
        left: int = 0,
        right: int = 0,
        up: int = 0,
        down: int = 0,
        creativity: float = 0.5,
        output_format: str = "png",
    ) -> bytes:
        """
        Extend image boundaries (outpainting).

        Args:
            image_path: Path to source image
            prompt: Description of extended area
            left: Pixels to extend left
            right: Pixels to extend right
            up: Pixels to extend up
            down: Pixels to extend down
            creativity: Generation creativity (0-1)
            output_format: Output format

        Returns:
            Extended image bytes

        Example:
            # Extend product shot to show more context
            extended = await client.outpaint(
                "hoodie_crop.jpg",
                prompt="model wearing hoodie, full body shot, studio",
                down=512  # Extend downward
            )
        """
        client = await self._get_client()
        image_data = self._load_image(image_path)

        files = {
            "image": ("image.png", image_data, "image/png"),
        }

        data = {
            "prompt": prompt,
            "left": str(left),
            "right": str(right),
            "up": str(up),
            "down": str(down),
            "creativity": str(creativity),
            "output_format": output_format,
        }

        response = await client.post(
            "/v2beta/stable-image/edit/outpaint",
            data=data,
            files=files,
            headers={"Accept": "image/*"},
        )
        response.raise_for_status()

        return response.content

    async def remove_background(self, image_path: str, output_format: str = "png") -> bytes:
        """
        Remove background from image.

        Args:
            image_path: Path to source image
            output_format: Output format (png recommended for transparency)

        Returns:
            Image bytes with transparent background

        Example:
            transparent = await client.remove_background("product.jpg")
        """
        client = await self._get_client()
        image_data = self._load_image(image_path)

        files = {
            "image": ("image.png", image_data, "image/png"),
        }

        data = {
            "output_format": output_format,
        }

        response = await client.post(
            "/v2beta/stable-image/edit/remove-background",
            data=data,
            files=files,
            headers={"Accept": "image/*"},
        )
        response.raise_for_status()

        return response.content

    async def search_and_replace(
        self,
        image_path: str,
        search_prompt: str,
        prompt: str,
        negative_prompt: str = "",
        output_format: str = "png",
    ) -> bytes:
        """
        Find and replace objects in an image.

        Args:
            image_path: Path to source image
            search_prompt: What to find and replace
            prompt: What to replace it with
            negative_prompt: What to avoid
            output_format: Output format

        Returns:
            Modified image bytes

        Example:
            # Change hoodie color
            modified = await client.search_and_replace(
                "hoodie_black.jpg",
                search_prompt="black hoodie",
                prompt="rose gold hoodie"
            )
        """
        client = await self._get_client()
        image_data = self._load_image(image_path)

        files = {
            "image": ("image.png", image_data, "image/png"),
        }

        data = {
            "search_prompt": search_prompt,
            "prompt": prompt,
            "output_format": output_format,
        }

        if negative_prompt:
            data["negative_prompt"] = negative_prompt

        response = await client.post(
            "/v2beta/stable-image/edit/search-and-replace",
            data=data,
            files=files,
            headers={"Accept": "image/*"},
        )
        response.raise_for_status()

        return response.content

    async def get_balance(self) -> float:
        """Get current API credit balance."""
        client = await self._get_client()
        response = await client.get("/v1/user/balance")
        response.raise_for_status()
        return response.json().get("credits", 0)


__all__ = ["StabilityClient"]
