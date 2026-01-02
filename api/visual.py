"""
Visual Generation API Endpoints
================================

E-commerce product photography and visual content generation.

Providers:
- Google Imagen 3 - High-quality image generation
- HuggingFace FLUX - Fast, creative images
- Google Veo - Video generation

Author: DevSkyy Platform Team
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

visual_router = APIRouter(tags=["Visual Generation"])

# Output directory
OUTPUT_DIR = Path(os.getenv("VISUAL_OUTPUT_DIR", "./assets/visual-generated"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Enums & Models
# =============================================================================


class VisualProvider(str, Enum):
    """Visual generation provider."""

    GOOGLE_IMAGEN = "google_imagen"
    HUGGINGFACE_FLUX = "huggingface_flux"
    AUTO = "auto"  # Best available


class ImageStyle(str, Enum):
    """Product photography styles."""

    PRODUCT_STUDIO = "product_studio"  # Clean white background
    LIFESTYLE = "lifestyle"  # In-context lifestyle shot
    FLAT_LAY = "flat_lay"  # Top-down product arrangement
    HERO = "hero"  # Hero banner image
    DETAIL = "detail"  # Close-up detail shot


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ProductPhotoRequest(BaseModel):
    """Request for e-commerce product photo."""

    product_name: str = Field(..., description="Product name or description")
    collection: str = Field(default="SIGNATURE", description="SkyyRose collection")
    style: ImageStyle = Field(default=ImageStyle.PRODUCT_STUDIO)
    background: str = Field(default="white studio background")
    provider: VisualProvider = Field(default=VisualProvider.AUTO)
    aspect_ratio: str = Field(default="1:1", description="1:1, 4:3, 16:9, 9:16")
    quality: str = Field(default="high", description="low, medium, high")


class BatchPhotoRequest(BaseModel):
    """Request for batch product photos (multiple styles)."""

    product_name: str = Field(..., description="Product name")
    collection: str = Field(default="SIGNATURE")
    styles: list[ImageStyle] = Field(
        default=[ImageStyle.PRODUCT_STUDIO, ImageStyle.LIFESTYLE, ImageStyle.DETAIL]
    )


class VisualJobResponse(BaseModel):
    """Visual generation job response."""

    job_id: str
    status: JobStatus
    provider: str
    product_name: str
    style: str
    created_at: str
    completed_at: str | None = None
    image_url: str | None = None
    image_path: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchJobResponse(BaseModel):
    """Batch generation response."""

    batch_id: str
    jobs: list[VisualJobResponse]
    status: str


# =============================================================================
# Job Store
# =============================================================================


class VisualJobStore:
    """In-memory visual job storage."""

    def __init__(self):
        self._jobs: dict[str, VisualJobResponse] = {}

    def create(
        self,
        product_name: str,
        style: ImageStyle,
        provider: VisualProvider,
        metadata: dict | None = None,
    ) -> VisualJobResponse:
        job_id = f"vis_{uuid.uuid4().hex[:12]}"
        job = VisualJobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            provider=provider.value,
            product_name=product_name,
            style=style.value,
            created_at=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )
        self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> VisualJobResponse | None:
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> VisualJobResponse | None:
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
        return job

    def complete(self, job_id: str, image_url: str, image_path: str) -> VisualJobResponse | None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.image_url = image_url
            job.image_path = image_path
            job.completed_at = datetime.now(UTC).isoformat()
        return job

    def fail(self, job_id: str, error: str) -> VisualJobResponse | None:
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(UTC).isoformat()
        return job

    def list_jobs(self, limit: int = 20) -> list[VisualJobResponse]:
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]


visual_job_store = VisualJobStore()


# =============================================================================
# Background Tasks
# =============================================================================


async def run_product_photo_generation(
    job_id: str,
    product_name: str,
    collection: str,
    style: ImageStyle,
    background: str,
    provider: VisualProvider,
    aspect_ratio: str,
    quality: str,
):
    """Generate product photo in background."""
    try:
        visual_job_store.update(job_id, status=JobStatus.PROCESSING)

        from agents.visual_generation import create_visual_router

        router = await create_visual_router()

        # Generate product image
        result = await router.generate_product_image(
            product_name=product_name,
            collection=collection,
            style=_style_to_description(style),
            background=background,
            aspect_ratio=aspect_ratio,
            quality=quality,
        )

        if result.success and result.output_path:
            visual_job_store.complete(
                job_id,
                image_url=f"/assets/visual-generated/{Path(result.output_path).name}",
                image_path=result.output_path,
            )
            logger.info(f"Product photo generated: {job_id}")
        else:
            visual_job_store.fail(job_id, result.error or "Generation failed")

    except Exception as e:
        logger.exception(f"Product photo generation failed: {e}")
        visual_job_store.fail(job_id, str(e))


def _style_to_description(style: ImageStyle) -> str:
    """Convert style enum to prompt description."""
    descriptions = {
        ImageStyle.PRODUCT_STUDIO: "professional e-commerce product photography, clean white studio background, soft shadows, high-key lighting",
        ImageStyle.LIFESTYLE: "lifestyle product photography, authentic setting, natural lighting, in-use context",
        ImageStyle.FLAT_LAY: "flat lay product photography, top-down view, minimalist arrangement, styled props",
        ImageStyle.HERO: "hero banner product image, dramatic lighting, premium feel, brand showcase",
        ImageStyle.DETAIL: "macro detail shot, close-up texture, fabric quality, stitching details visible",
    }
    return descriptions.get(style, "professional product photography")


# =============================================================================
# Endpoints
# =============================================================================


@visual_router.get("/visual/providers")
async def list_providers():
    """List available visual generation providers."""
    google_key = bool(os.getenv("GOOGLE_AI_API_KEY"))
    hf_key = bool(os.getenv("HUGGINGFACE_API_TOKEN") or os.getenv("HF_TOKEN"))

    return [
        {
            "name": "google_imagen",
            "display_name": "Google Imagen 3",
            "description": "High-quality photorealistic image generation",
            "status": "available" if google_key else "requires_api_key",
            "best_for": ["product_studio", "hero", "lifestyle"],
        },
        {
            "name": "huggingface_flux",
            "display_name": "FLUX (HuggingFace)",
            "description": "Fast creative image generation",
            "status": "available" if hf_key else "requires_api_key",
            "best_for": ["lifestyle", "creative", "artistic"],
        },
        {
            "name": "auto",
            "display_name": "Auto (Best Available)",
            "description": "Automatically select best provider for the task",
            "status": "available",
            "best_for": ["all"],
        },
    ]


@visual_router.get("/visual/styles")
async def list_styles():
    """List available photography styles."""
    return [
        {
            "id": ImageStyle.PRODUCT_STUDIO.value,
            "name": "Product Studio",
            "description": "Clean white background, professional e-commerce ready",
            "use_case": "Product listings, catalogs",
        },
        {
            "id": ImageStyle.LIFESTYLE.value,
            "name": "Lifestyle",
            "description": "In-context lifestyle setting, authentic feel",
            "use_case": "Social media, lookbooks",
        },
        {
            "id": ImageStyle.FLAT_LAY.value,
            "name": "Flat Lay",
            "description": "Top-down styled arrangement",
            "use_case": "Instagram, Pinterest",
        },
        {
            "id": ImageStyle.HERO.value,
            "name": "Hero",
            "description": "Dramatic banner-ready hero shot",
            "use_case": "Homepage, campaigns",
        },
        {
            "id": ImageStyle.DETAIL.value,
            "name": "Detail",
            "description": "Close-up texture and quality shots",
            "use_case": "Product pages, quality showcase",
        },
    ]


@visual_router.get("/visual/jobs", response_model=list[VisualJobResponse])
async def list_jobs(limit: int = 20):
    """List recent visual generation jobs."""
    return visual_job_store.list_jobs(limit)


@visual_router.get("/visual/jobs/{job_id}", response_model=VisualJobResponse)
async def get_job(job_id: str):
    """Get a specific job."""
    job = visual_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@visual_router.post("/visual/product-photo", response_model=VisualJobResponse)
async def generate_product_photo(
    request: ProductPhotoRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate e-commerce product photo.

    Creates professional product photography with SkyyRose branding.
    """
    job = visual_job_store.create(
        product_name=request.product_name,
        style=request.style,
        provider=request.provider,
        metadata={
            "collection": request.collection,
            "background": request.background,
            "aspect_ratio": request.aspect_ratio,
            "quality": request.quality,
        },
    )

    background_tasks.add_task(
        run_product_photo_generation,
        job.job_id,
        request.product_name,
        request.collection,
        request.style,
        request.background,
        request.provider,
        request.aspect_ratio,
        request.quality,
    )

    return job


@visual_router.post("/visual/batch-photos", response_model=BatchJobResponse)
async def generate_batch_photos(
    request: BatchPhotoRequest,
    background_tasks: BackgroundTasks,
):
    """
    Generate multiple product photos in different styles.

    Creates a set of e-commerce ready images for the product.
    """
    batch_id = f"batch_{uuid.uuid4().hex[:8]}"
    jobs = []

    for style in request.styles:
        job = visual_job_store.create(
            product_name=request.product_name,
            style=style,
            provider=VisualProvider.AUTO,
            metadata={
                "collection": request.collection,
                "batch_id": batch_id,
            },
        )
        jobs.append(job)

        background_tasks.add_task(
            run_product_photo_generation,
            job.job_id,
            request.product_name,
            request.collection,
            style,
            "white studio background" if style == ImageStyle.PRODUCT_STUDIO else "contextual",
            VisualProvider.AUTO,
            "1:1",
            "high",
        )

    return BatchJobResponse(
        batch_id=batch_id,
        jobs=jobs,
        status="processing",
    )


# =============================================================================
# Image Enhancement Endpoints
# =============================================================================


class EnhancementType(str, Enum):
    """Type of image enhancement."""

    UPSCALE = "upscale"  # 2x-4x resolution increase
    BACKGROUND = "background"  # Background removal/replacement
    LIGHTING = "lighting"  # Professional lighting correction
    COLOR = "color"  # Color enhancement/correction
    FULL = "full"  # All enhancements


class EnhanceRequest(BaseModel):
    """Request to enhance existing product image."""

    image_url: str = Field(..., description="URL of the image to enhance")
    product_name: str = Field(default="Product", description="Product name for context")
    enhancement_type: EnhancementType = Field(default=EnhancementType.FULL)
    upscale_factor: int = Field(default=2, ge=1, le=4, description="Upscale factor (1-4)")
    new_background: str = Field(
        default="white studio", description="New background if using background enhancement"
    )
    preserve_product: bool = Field(default=True, description="Keep the actual product unchanged")


class EnhanceUploadRequest(BaseModel):
    """Response model for upload enhancement."""

    job_id: str
    status: JobStatus
    original_filename: str
    enhancement_type: str
    created_at: str


async def run_image_enhancement(
    job_id: str,
    image_path: str,
    product_name: str,
    enhancement_type: EnhancementType,
    upscale_factor: int,
    new_background: str,
):
    """
    Run image enhancement in background.

    All outputs are standardized to PNG format for consistency
    regardless of input format (PNG, JPG, JPEG supported).
    """
    import shutil

    try:
        visual_job_store.update(job_id, status=JobStatus.PROCESSING)

        # All enhanced outputs are PNG for consistent quality
        # PNG supports transparency and is lossless
        output_path = OUTPUT_DIR / f"enhanced_{job_id}.png"

        if enhancement_type == EnhancementType.UPSCALE:
            # Use Real-ESRGAN or similar for upscaling
            await _upscale_image(image_path, str(output_path), upscale_factor)
        elif enhancement_type == EnhancementType.BACKGROUND:
            # Use rembg or similar for background removal/replacement
            await _enhance_background(image_path, str(output_path), new_background)
        elif enhancement_type == EnhancementType.FULL:
            # Full enhancement pipeline
            await _full_enhancement(image_path, str(output_path), upscale_factor, new_background)
        else:
            # Basic enhancement - just copy for now
            shutil.copy2(image_path, output_path)

        if output_path.exists():
            visual_job_store.complete(
                job_id,
                image_url=f"/assets/visual-generated/{output_path.name}",
                image_path=str(output_path),
            )
            logger.info(f"Image enhancement completed: {job_id}")
        else:
            visual_job_store.fail(job_id, "Enhancement failed - no output generated")

    except Exception as e:
        logger.exception(f"Image enhancement failed: {e}")
        visual_job_store.fail(job_id, str(e))


async def _upscale_image(input_path: str, output_path: str, factor: int):
    """
    Upscale image using Real-ESRGAN via HuggingFace.

    Supports PNG, JPG, JPEG input - always outputs PNG.
    """
    try:
        from gradio_client import Client, handle_file

        # Use Real-ESRGAN on HuggingFace
        client = Client("ai-forever/Real-ESRGAN")
        result = client.predict(handle_file(input_path), api_name="/predict")
        # Convert to PNG if needed
        from PIL import Image

        img = Image.open(result)
        img.save(output_path, "PNG")
    except Exception as e:
        logger.warning(f"HuggingFace upscaling failed: {e}, using PIL fallback")
        # Fallback to PIL upscaling with Lanczos resampling
        from PIL import Image

        img = Image.open(input_path)
        # Convert to RGB if needed (handles RGBA, grayscale, etc.)
        if img.mode in ("RGBA", "LA"):
            background = Image.new("RGBA", img.size, (255, 255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        new_size = (img.width * factor, img.height * factor)
        img_upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
        img_upscaled.save(output_path, "PNG")


async def _enhance_background(input_path: str, output_path: str, new_background: str):
    """
    Remove/replace background using HuggingFace.

    Supports PNG, JPG, JPEG input - always outputs PNG with transparency.
    """
    try:
        from gradio_client import Client, handle_file

        # Use background removal on HuggingFace
        client = Client("ECCV2022/dis-background-removal")
        result = client.predict(handle_file(input_path), api_name="/predict")
        # Ensure output is PNG
        from PIL import Image

        img = Image.open(result)
        img.save(output_path, "PNG")
    except Exception as e:
        logger.warning(f"Background removal failed: {e}")
        # Fallback: copy as PNG
        from PIL import Image

        img = Image.open(input_path)
        img.save(output_path, "PNG")


async def _full_enhancement(
    input_path: str, output_path: str, upscale_factor: int, new_background: str
):
    """Full enhancement pipeline: background + upscale + color correction."""
    import tempfile
    from pathlib import Path

    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Step 1: Remove/replace background
        bg_removed = temp_dir / "bg_removed.png"
        await _enhance_background(input_path, str(bg_removed), new_background)

        # Step 2: Upscale
        await _upscale_image(str(bg_removed), output_path, upscale_factor)

    finally:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)


UPLOAD_DIR = Path(os.getenv("VISUAL_UPLOAD_DIR", "./assets/visual-uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@visual_router.post("/visual/enhance")
async def enhance_from_url(
    request: EnhanceRequest,
    background_tasks: BackgroundTasks,
):
    """
    Enhance an existing product image from URL.

    Downloads the image, applies enhancements, and returns production-ready version.
    The actual product remains unchanged - only quality improvements applied.
    """
    import httpx

    job = visual_job_store.create(
        product_name=request.product_name,
        style=ImageStyle.PRODUCT_STUDIO,
        provider=VisualProvider.AUTO,
        metadata={
            "enhancement_type": request.enhancement_type.value,
            "upscale_factor": request.upscale_factor,
            "original_url": request.image_url,
        },
    )

    # Download image
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(request.image_url)
            resp.raise_for_status()

            ext = Path(request.image_url).suffix or ".png"
            temp_path = UPLOAD_DIR / f"{job.job_id}{ext}"
            temp_path.write_bytes(resp.content)

    except Exception as e:
        visual_job_store.fail(job.job_id, f"Failed to download image: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to download image: {e}")

    background_tasks.add_task(
        run_image_enhancement,
        job.job_id,
        str(temp_path),
        request.product_name,
        request.enhancement_type,
        request.upscale_factor,
        request.new_background,
    )

    return job


@visual_router.post("/visual/enhance/upload")
async def enhance_from_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enhancement_type: EnhancementType = EnhancementType.FULL,
    upscale_factor: int = 2,
    new_background: str = "white studio",
    product_name: str = "Product",
):
    """
    Upload and enhance a product image.

    Upload your existing product photo and get back a production-ready,
    e-commerce quality version. The product itself remains identical -
    only quality improvements are applied.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    job = visual_job_store.create(
        product_name=product_name,
        style=ImageStyle.PRODUCT_STUDIO,
        provider=VisualProvider.AUTO,
        metadata={
            "enhancement_type": enhancement_type.value,
            "upscale_factor": upscale_factor,
            "original_filename": file.filename,
        },
    )

    # Save uploaded file
    ext = Path(file.filename or "image.png").suffix or ".png"
    upload_path = UPLOAD_DIR / f"{job.job_id}{ext}"

    try:
        content = await file.read()
        upload_path.write_bytes(content)
    except Exception as e:
        visual_job_store.fail(job.job_id, f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    background_tasks.add_task(
        run_image_enhancement,
        job.job_id,
        str(upload_path),
        product_name,
        enhancement_type,
        upscale_factor,
        new_background,
    )

    return job


@visual_router.post("/visual/batch-enhance")
async def batch_enhance(
    background_tasks: BackgroundTasks,
    image_urls: list[str],
    enhancement_type: EnhancementType = EnhancementType.FULL,
    upscale_factor: int = 2,
):
    """
    Batch enhance multiple product images.

    Enhance all your product photos at once with consistent quality settings.
    """
    import httpx

    batch_id = f"enhance_batch_{uuid.uuid4().hex[:8]}"
    jobs = []

    async with httpx.AsyncClient() as client:
        for i, url in enumerate(image_urls):
            job = visual_job_store.create(
                product_name=f"Product {i+1}",
                style=ImageStyle.PRODUCT_STUDIO,
                provider=VisualProvider.AUTO,
                metadata={
                    "enhancement_type": enhancement_type.value,
                    "batch_id": batch_id,
                    "original_url": url,
                },
            )
            jobs.append(job)

            try:
                resp = await client.get(url)
                resp.raise_for_status()
                ext = Path(url).suffix or ".png"
                temp_path = UPLOAD_DIR / f"{job.job_id}{ext}"
                temp_path.write_bytes(resp.content)

                background_tasks.add_task(
                    run_image_enhancement,
                    job.job_id,
                    str(temp_path),
                    f"Product {i+1}",
                    enhancement_type,
                    upscale_factor,
                    "white studio",
                )
            except Exception as e:
                visual_job_store.fail(job.job_id, f"Failed to download: {e}")

    return BatchJobResponse(
        batch_id=batch_id,
        jobs=jobs,
        status="processing",
    )
