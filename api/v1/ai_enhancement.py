"""
AI Image Enhancement API Endpoints
Provides REST API for WordPress integration
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
from pathlib import Path
import shutil
from datetime import datetime
import blurhash

from services.ai_image_enhancement import LuxuryImageEnhancer
from core.auth.interfaces import requires_api_key

router = APIRouter(prefix="/ai", tags=["AI Enhancement"])

# Initialize enhancer (keys loaded from environment)
enhancer = LuxuryImageEnhancer()


@router.post("/enhance-image")
@requires_api_key
async def enhance_image(
    file: UploadFile = File(...),
    apply_luxury_filter: bool = Form(True),
    remove_background: bool = Form(False),
    upscale: bool = Form(False),
    correlation_id: Optional[str] = None,
):
    """
    Enhance uploaded image with AI processing

    Args:
        file: Image file to enhance
        apply_luxury_filter: Apply SkyyRose luxury color grading
        remove_background: Remove background (RemBG)
        upscale: Upscale 4x using AI
        correlation_id: Request correlation ID

    Returns:
        Enhanced image details and metadata
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Create temp directory
    temp_dir = Path("/tmp/skyyrose_enhancement")
    temp_dir.mkdir(exist_ok=True)

    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = temp_dir / f"input_{timestamp}_{file.filename}"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        current_path = str(input_path)

        # Remove background if requested
        if remove_background:
            bg_removed_path = temp_dir / f"nobg_{timestamp}_{file.filename}"
            img = await enhancer.remove_background(current_path, str(bg_removed_path))
            current_path = str(bg_removed_path)

        # Apply luxury filter
        if apply_luxury_filter:
            filtered_path = temp_dir / f"luxury_{timestamp}_{file.filename}"
            await enhancer.apply_luxury_filter(current_path, str(filtered_path))
            current_path = str(filtered_path)

        # Upscale if requested
        upscaled_url = None
        if upscale:
            upscaled_url = await enhancer.upscale_image(current_path, scale=4)

        # Generate blurhash
        blurhash_value = generate_blurhash_from_path(current_path)

        # Return enhanced image
        return {
            "success": True,
            "enhanced_path": current_path,
            "upscaled_url": upscaled_url,
            "blurhash": blurhash_value,
            "processing_steps": {
                "remove_background": remove_background,
                "luxury_filter": apply_luxury_filter,
                "upscale": upscale,
            },
            "correlation_id": correlation_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Enhancement failed: {str(e)}"
        )


@router.post("/generate-blurhash")
@requires_api_key
async def generate_blurhash_endpoint(
    file: UploadFile = File(...),
    correlation_id: Optional[str] = None,
):
    """
    Generate blurhash placeholder for image

    Args:
        file: Image file
        correlation_id: Request correlation ID

    Returns:
        Blurhash string
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Create temp directory
    temp_dir = Path("/tmp/skyyrose_blurhash")
    temp_dir.mkdir(exist_ok=True)

    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = temp_dir / f"input_{timestamp}_{file.filename}"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        blurhash_value = generate_blurhash_from_path(str(input_path))

        return {
            "success": True,
            "blurhash": blurhash_value,
            "correlation_id": correlation_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Blurhash generation failed: {str(e)}"
        )
    finally:
        # Cleanup
        if input_path.exists():
            input_path.unlink()


@router.post("/interrogate-image")
@requires_api_key
async def interrogate_image(
    file: UploadFile = File(...),
    correlation_id: Optional[str] = None,
):
    """
    Analyze image and generate descriptive prompts (CLIP Interrogator)

    Args:
        file: Image file
        correlation_id: Request correlation ID

    Returns:
        Image analysis and prompts
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Create temp directory
    temp_dir = Path("/tmp/skyyrose_interrogate")
    temp_dir.mkdir(exist_ok=True)

    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = temp_dir / f"input_{timestamp}_{file.filename}"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analysis = await enhancer.interrogate_image(str(input_path))

        return {
            "success": True,
            "analysis": analysis,
            "correlation_id": correlation_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image interrogation failed: {str(e)}"
        )
    finally:
        # Cleanup
        if input_path.exists():
            input_path.unlink()


@router.post("/generate-product-image")
@requires_api_key
async def generate_product_image(
    prompt: str = Form(...),
    model: str = Form("flux"),
    image_size: str = Form("1024x1024"),
    correlation_id: Optional[str] = None,
):
    """
    Generate product image from text prompt

    Args:
        prompt: Product description
        model: AI model (flux, sd3, sdxl)
        image_size: Output size
        correlation_id: Request correlation ID

    Returns:
        Generated image URL
    """
    try:
        image_url = await enhancer.generate_product_image(
            prompt=prompt,
            model=model,
            image_size=image_size,
        )

        return {
            "success": True,
            "image_url": image_url,
            "prompt": prompt,
            "model": model,
            "correlation_id": correlation_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )


@router.post("/create-product-video")
@requires_api_key
async def create_product_video(
    file: UploadFile = File(...),
    motion_type: str = Form("zoom"),
    correlation_id: Optional[str] = None,
):
    """
    Create video from product image (RunwayML Gen-3)

    Args:
        file: Product image
        motion_type: Camera motion (zoom, pan, rotate, dolly)
        correlation_id: Request correlation ID

    Returns:
        Video URL
    """
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )

    # Create temp directory
    temp_dir = Path("/tmp/skyyrose_video")
    temp_dir.mkdir(exist_ok=True)

    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_path = temp_dir / f"input_{timestamp}_{file.filename}"

    try:
        with input_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        video_url = await enhancer.create_product_video(
            str(input_path),
            motion_type=motion_type,
        )

        return {
            "success": True,
            "video_url": video_url,
            "motion_type": motion_type,
            "correlation_id": correlation_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Video creation failed: {str(e)}"
        )
    finally:
        # Cleanup
        if input_path.exists():
            input_path.unlink()


@router.get("/enhancement-status/{attachment_id}")
@requires_api_key
async def get_enhancement_status(
    attachment_id: int,
    correlation_id: Optional[str] = None,
):
    """
    Get enhancement status for WordPress attachment

    Args:
        attachment_id: WordPress attachment ID
        correlation_id: Request correlation ID

    Returns:
        Enhancement status and metadata
    """
    # This would query a database or cache for status
    # For now, return placeholder
    return {
        "attachment_id": attachment_id,
        "status": "pending",
        "correlation_id": correlation_id,
    }


def generate_blurhash_from_path(image_path: str, components_x: int = 4, components_y: int = 3) -> str:
    """
    Generate blurhash from image file path

    Args:
        image_path: Path to image file
        components_x: Horizontal components (4-9 recommended)
        components_y: Vertical components (3-9 recommended)

    Returns:
        Blurhash string
    """
    from PIL import Image

    try:
        img = Image.open(image_path)
        img = img.convert('RGB')

        # Resize for performance (max 256px on longest side)
        max_size = 256
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Generate blurhash
        hash_value = blurhash.encode(img, components_x, components_y)

        return hash_value

    except Exception as e:
        raise ValueError(f"Failed to generate blurhash: {str(e)}")
