"""
Replicate Client
================

Client for Replicate API - Run ML models in the cloud.

Key capabilities for DevSkyy:
- SDXL image generation (product photos, marketing assets)
- ControlNet (pose transfer, edge-guided generation)
- Real-ESRGAN (image upscaling)
- BLIP-2 (image captioning for training data)
- InstantID (face-preserving generation)
- Background removal
- Custom LoRA inference

Reference: https://replicate.com/docs
"""

from __future__ import annotations

import logging
import os

# Import config for API keys (loads .env.hf)
try:
    from config import settings

    REPLICATE_API_TOKEN = getattr(settings, "REPLICATE_API_TOKEN", "") or os.getenv(
        "REPLICATE_API_TOKEN", ""
    )
except ImportError:
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

logger = logging.getLogger(__name__)


class ReplicateClient:
    """
    Replicate API Client for ML model inference.

    Capabilities:
    - Image Generation: SDXL, Flux, Stable Diffusion
    - Image Enhancement: Real-ESRGAN, CodeFormer
    - ControlNet: Pose, Canny, Depth conditioning
    - Image Analysis: BLIP-2, LLaVA
    - Video: Stable Video Diffusion
    - Custom LoRA: Run your trained models

    Usage:
        client = ReplicateClient()

        # Generate product image
        url = await client.generate_image(
            "luxury fashion hoodie, skyyrose brand, studio lighting",
            model="sdxl"
        )

        # Upscale existing image
        url = await client.upscale_image("product.jpg", scale=4)

        # Run custom LoRA
        url = await client.run_lora(
            "damBruh/skyyrose-lora:latest",
            prompt="skyyrose signature collection hoodie"
        )
    """

    # Popular models for fashion/e-commerce
    MODELS = {
        # Image Generation
        "sdxl": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
        "flux-dev": "black-forest-labs/flux-dev",
        "flux-schnell": "black-forest-labs/flux-schnell",
        "sd-3": "stability-ai/stable-diffusion-3",
        # SkyyRose Custom LoRA (trained on 390 exact product images)
        "skyyrose-lora": "devskyy/skyyrose-lora-v3:64dbb859fed83670e7cde81fc161c183bd9d0607fb7028b01bfc0a000ec114b4",
        # Image Enhancement
        "real-esrgan": "nightmareai/real-esrgan:42fed1c4974146d4d2414e2be2c5277c7fcf05fcc3a73abf41610695738c1d7b",
        "codeformer": "sczhou/codeformer:7de2ea26c616d5bf2245ad0d5e24f0ff9a6204578a5c876db53142edd9d2cd56",
        # ControlNet
        "controlnet-canny": "jagilley/controlnet-canny:aff48af9c68d162388d230a2ab003f68d2638d88307bdaf1c2f1ac95079c9613",
        "controlnet-pose": "jagilley/controlnet-openpose:9c3cfbae2ed17a3a7adbfb222a13469b10a69f8a9a4e1a82bde60b8b276f93ea",
        # Image Analysis
        "blip-2": "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
        "llava": "yorickvp/llava-13b:b5f6212d032508382d61ff00469ddda3e32fd8a0e75dc39d8a4191bb742157fb",
        # Background Removal
        "rembg": "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003",
        # Video
        "svd": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
    }

    def __init__(self, api_token: str | None = None) -> None:
        """
        Initialize the Replicate client.

        Args:
            api_token: Replicate API token (or set REPLICATE_API_TOKEN env var)
        """
        self.api_token = api_token or REPLICATE_API_TOKEN
        if not self.api_token:
            logger.warning("REPLICATE_API_TOKEN not configured")

        self._client = None

    def _get_client(self):
        """Lazy-load the replicate client."""
        if self._client is None:
            try:
                import replicate

                os.environ["REPLICATE_API_TOKEN"] = self.api_token
                self._client = replicate
            except ImportError:
                raise ImportError("Install replicate: pip install replicate")
        return self._client

    async def generate_image(
        self,
        prompt: str,
        model: str = "sdxl",
        negative_prompt: str = "low quality, blurry, distorted",
        width: int = 1024,
        height: int = 1024,
        num_outputs: int = 1,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50,
        scheduler: str = "K_EULER",
        **kwargs,
    ) -> list[str]:
        """
        Generate images using SDXL or other models.

        Args:
            prompt: Text description of desired image
            model: Model key or full model ID
            negative_prompt: What to avoid in generation
            width: Image width (1024 for SDXL)
            height: Image height (1024 for SDXL)
            num_outputs: Number of images to generate
            guidance_scale: CFG scale (7.5 typical)
            num_inference_steps: Denoising steps
            scheduler: Sampling method

        Returns:
            List of image URLs

        Example:
            urls = await client.generate_image(
                "luxury hoodie, skyyrose signature collection, studio photo",
                model="sdxl"
            )
        """
        client = self._get_client()
        model_id = self.MODELS.get(model, model)

        input_params = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_outputs": num_outputs,
            "guidance_scale": guidance_scale,
            "num_inference_steps": num_inference_steps,
            "scheduler": scheduler,
            **kwargs,
        }

        logger.info(f"Generating image with {model}: {prompt[:50]}...")
        output = client.run(model_id, input=input_params)

        # Output is usually a list of URLs
        return list(output) if hasattr(output, "__iter__") else [output]

    async def upscale_image(
        self,
        image_path: str,
        scale: int = 4,
        face_enhance: bool = False,
    ) -> str:
        """
        Upscale an image using Real-ESRGAN.

        Args:
            image_path: Path to image file or URL
            scale: Upscale factor (2 or 4)
            face_enhance: Use GFPGAN for face enhancement

        Returns:
            URL to upscaled image
        """
        client = self._get_client()

        input_params = {
            "image": (
                open(image_path, "rb") if not image_path.startswith("http") else image_path
            ),  # noqa: SIM115
            "scale": scale,
            "face_enhance": face_enhance,
        }

        output = client.run(self.MODELS["real-esrgan"], input=input_params)
        return str(output)

    async def remove_background(self, image_path: str) -> str:
        """
        Remove background from an image.

        Args:
            image_path: Path to image file or URL

        Returns:
            URL to image with transparent background
        """
        client = self._get_client()

        input_params = {
            "image": (
                open(image_path, "rb") if not image_path.startswith("http") else image_path
            ),  # noqa: SIM115
        }

        output = client.run(self.MODELS["rembg"], input=input_params)
        return str(output)

    async def caption_image(self, image_path: str) -> str:
        """
        Generate caption for an image using BLIP-2.

        Useful for creating training data captions.

        Args:
            image_path: Path to image file or URL

        Returns:
            Image caption text
        """
        client = self._get_client()

        input_params = {
            "image": (
                open(image_path, "rb") if not image_path.startswith("http") else image_path
            ),  # noqa: SIM115
            "task": "image_captioning",
        }

        output = client.run(self.MODELS["blip-2"], input=input_params)
        return str(output)

    async def run_controlnet(
        self,
        prompt: str,
        control_image: str,
        control_type: str = "canny",
        **kwargs,
    ) -> list[str]:
        """
        Generate image guided by ControlNet.

        Args:
            prompt: Text description
            control_image: Path to control image (edge map, pose, etc.)
            control_type: Type of control ("canny", "pose")
            **kwargs: Additional generation parameters

        Returns:
            List of generated image URLs

        Example:
            # Generate hoodie in specific pose
            urls = await client.run_controlnet(
                prompt="skyyrose hoodie, professional model, studio",
                control_image="pose_reference.jpg",
                control_type="pose"
            )
        """
        client = self._get_client()
        model_key = f"controlnet-{control_type}"
        model_id = self.MODELS.get(model_key)

        if not model_id:
            raise ValueError(f"Unknown ControlNet type: {control_type}")

        input_params = {
            "prompt": prompt,
            "image": (
                open(control_image, "rb")  # noqa: SIM115
                if not control_image.startswith("http")
                else control_image
            ),
            **kwargs,
        }

        output = client.run(model_id, input=input_params)
        return list(output) if hasattr(output, "__iter__") else [output]

    async def run_lora(
        self,
        model_id: str,
        prompt: str,
        **kwargs,
    ) -> list[str]:
        """
        Run inference with a custom LoRA model.

        Args:
            model_id: Full Replicate model ID (e.g., "damBruh/skyyrose-lora:latest")
            prompt: Generation prompt with trigger words
            **kwargs: Additional model parameters

        Returns:
            List of generated image URLs

        Example:
            urls = await client.run_lora(
                model_id="damBruh/skyyrose-lora:latest",
                prompt="skyyrose signature collection, lavender beanie"
            )
        """
        client = self._get_client()

        input_params = {
            "prompt": prompt,
            **kwargs,
        }

        output = client.run(model_id, input=input_params)
        return list(output) if hasattr(output, "__iter__") else [output]

    async def generate_skyyrose_product(
        self,
        prompt: str,
        collection: str = "SIGNATURE",
        num_outputs: int = 1,
        guidance_scale: float = 3.5,
        num_inference_steps: int = 28,
        **kwargs,
    ) -> list[str]:
        """
        Generate SkyyRose product images using custom-trained LoRA.

        The LoRA was trained on 390 exact SkyyRose product images
        with trigger word "skyyrose".

        Args:
            prompt: Product description (automatically prepended with "skyyrose")
            collection: Collection name (SIGNATURE, BLACK_ROSE, LOVE_HURTS)
            num_outputs: Number of images to generate (1-4)
            guidance_scale: CFG scale (3.5 recommended for Flux)
            num_inference_steps: Denoising steps (28 default)

        Returns:
            List of image URLs

        Example:
            urls = await client.generate_skyyrose_product(
                prompt="lavender beanie with rose embroidery",
                collection="SIGNATURE"
            )
        """
        # Collection style mapping
        collection_styles = {
            "SIGNATURE": "signature collection, lavender rose, classic elegant",
            "BLACK_ROSE": "black_rose collection, dark elegance, gothic luxury",
            "LOVE_HURTS": "love_hurts collection, bold red, emotional expression",
        }

        style = collection_styles.get(collection.upper(), collection_styles["SIGNATURE"])

        # Build prompt with trigger word
        full_prompt = (
            f"skyyrose {style}, {prompt}, luxury streetwear, product photo, studio lighting"
        )

        return await self.run_lora(
            model_id=self.MODELS["skyyrose-lora"],
            prompt=full_prompt,
            num_outputs=num_outputs,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            **kwargs,
        )

    async def generate_video(
        self,
        image_path: str,
        motion_bucket_id: int = 127,
        fps: int = 7,
        **kwargs,
    ) -> str:
        """
        Generate video from image using Stable Video Diffusion.

        Args:
            image_path: Path to source image
            motion_bucket_id: Amount of motion (1-255)
            fps: Frames per second (6-30)

        Returns:
            URL to generated video

        Example:
            video_url = await client.generate_video("product.jpg")
        """
        client = self._get_client()

        input_params = {
            "input_image": (
                open(image_path, "rb")  # noqa: SIM115
                if not image_path.startswith("http")
                else image_path
            ),
            "motion_bucket_id": motion_bucket_id,
            "fps": fps,
            **kwargs,
        }

        output = client.run(self.MODELS["svd"], input=input_params)
        return str(output)


__all__ = ["ReplicateClient"]
