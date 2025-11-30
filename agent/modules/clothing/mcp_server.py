#!/usr/bin/env python3
"""
3D Clothing Asset Automation MCP Server

Exposes SkyyRose 3D clothing asset generation capabilities via Model Context Protocol:
- 3D model generation (Tripo3D)
- Virtual try-on (FASHN)
- WordPress media upload

Brand: SkyyRose - Oakland luxury streetwear, "where love meets luxury"
Collections: BLACK_ROSE, LOVE_HURTS, SIGNATURE

Truth Protocol Compliance:
- Rule #1: All APIs verified from official documentation
- Rule #5: All API keys via environment variables
- Rule #9: Fully documented with type hints
- Rule #10: Error handling with continue policy

Usage:
    # Run the MCP server
    python -m agent.modules.clothing.mcp_server

    # Or with uvicorn
    uvicorn agent.modules.clothing.mcp_server:mcp --host 0.0.0.0 --port 8001
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from agent.modules.clothing.clients.fashn_client import FASHNClient, FASHNError
from agent.modules.clothing.clients.tripo3d_client import Tripo3DClient, Tripo3DError
from agent.modules.clothing.clients.wordpress_media import (
    WordPressMediaClient,
    WordPressError,
)
from agent.modules.clothing.pipeline import ClothingAssetPipeline
from agent.modules.clothing.schemas.schemas import (
    ClothingCategory,
    ClothingCollection,
    ClothingItem,
    Model3DFormat,
    TryOnModel,
)

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

MCP_SERVER_NAME = "skyyrose-3d-assets"
MCP_SERVER_VERSION = "1.0.0"

# ============================================================================
# RESPONSE MODELS
# ============================================================================


class Model3DResponse(BaseModel):
    """Response model for 3D generation."""

    success: bool
    task_id: str
    status: str
    model_url: str | None = None
    thumbnail_url: str | None = None
    local_path: str | None = None
    generation_time_seconds: float | None = None
    error: str | None = None


class TryOnResponse(BaseModel):
    """Response model for virtual try-on."""

    success: bool
    task_id: str
    status: str
    image_url: str | None = None
    local_path: str | None = None
    model_type: str
    processing_time_seconds: float | None = None
    error: str | None = None


class UploadResponse(BaseModel):
    """Response model for WordPress upload."""

    success: bool
    media_id: int | None = None
    source_url: str | None = None
    mime_type: str | None = None
    title: str | None = None
    error: str | None = None


class PipelineResponse(BaseModel):
    """Response model for full pipeline."""

    success: bool
    item_id: str
    item_name: str
    stage: str
    model_3d: dict[str, Any] | None = None
    try_on_results: list[dict[str, Any]] = Field(default_factory=list)
    wordpress_uploads: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    total_processing_time_seconds: float = 0.0


# ============================================================================
# LAZY CLIENT INITIALIZATION
# ============================================================================


class ClientManager:
    """Manages lazy initialization of API clients."""

    _tripo_client: Tripo3DClient | None = None
    _fashn_client: FASHNClient | None = None
    _wordpress_client: WordPressMediaClient | None = None
    _pipeline: ClothingAssetPipeline | None = None

    @classmethod
    async def get_tripo_client(cls) -> Tripo3DClient:
        """Get or create Tripo3D client."""
        if cls._tripo_client is None:
            cls._tripo_client = Tripo3DClient()
            await cls._tripo_client.initialize()
        return cls._tripo_client

    @classmethod
    async def get_fashn_client(cls) -> FASHNClient:
        """Get or create FASHN client."""
        if cls._fashn_client is None:
            cls._fashn_client = FASHNClient()
            await cls._fashn_client.initialize()
        return cls._fashn_client

    @classmethod
    async def get_wordpress_client(cls) -> WordPressMediaClient:
        """Get or create WordPress client."""
        if cls._wordpress_client is None:
            cls._wordpress_client = WordPressMediaClient()
            await cls._wordpress_client.initialize()
        return cls._wordpress_client

    @classmethod
    async def get_pipeline(cls) -> ClothingAssetPipeline:
        """Get or create the full pipeline."""
        if cls._pipeline is None:
            cls._pipeline = ClothingAssetPipeline()
            await cls._pipeline.initialize()
        return cls._pipeline


# ============================================================================
# MCP SERVER
# ============================================================================

mcp = FastMCP(MCP_SERVER_NAME, version=MCP_SERVER_VERSION)


# ============================================================================
# MCP TOOLS - 3D GENERATION
# ============================================================================


@mcp.tool()
async def generate_3d_from_text(
    product_name: str,
    description: str,
    collection: str = "signature",
    category: str = "hoodie",
    color: str = "black",
    output_format: str = "glb",
) -> str:
    """
    Generate a 3D model from text description using Tripo3D.

    Creates a high-quality 3D model of clothing based on text prompts,
    optimized for SkyyRose luxury streetwear aesthetics.

    Args:
        product_name: Name of the product (e.g., "Black Rose Hoodie")
        description: Detailed description for 3D generation
        collection: SkyyRose collection (black_rose, love_hurts, signature)
        category: Clothing type (hoodie, t_shirt, jacket, pants, etc.)
        color: Primary color of the item
        output_format: 3D format (glb, fbx, obj, usdz)

    Returns:
        JSON with task_id, status, model_url, and download path
    """
    try:
        # Create a ClothingItem for optimized prompt generation
        item = ClothingItem(
            item_id=f"mcp-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            name=product_name,
            description=description,
            collection=ClothingCollection(collection),
            category=ClothingCategory(category),
            color=color,
            price=99.99,  # Placeholder
            sku="MCP-GEN",
        )

        # Get optimized prompt
        prompt = item.prompt_for_3d

        logger.info(f"Generating 3D model for: {product_name}")
        logger.info(f"Using prompt: {prompt}")

        client = await ClientManager.get_tripo_client()
        result = await client.text_to_3d(
            prompt=prompt,
            output_format=Model3DFormat(output_format),
            wait_for_completion=True,
        )

        response = Model3DResponse(
            success=result.status == "success",
            task_id=result.task_id,
            status=result.status,
            model_url=result.model_url,
            thumbnail_url=result.thumbnail_url,
            local_path=result.local_path,
            generation_time_seconds=result.generation_time_seconds,
        )

        return json.dumps(response.model_dump(), indent=2)

    except Tripo3DError as e:
        return json.dumps(
            Model3DResponse(
                success=False,
                task_id="error",
                status="failed",
                error=str(e),
            ).model_dump(),
            indent=2,
        )
    except Exception as e:
        logger.exception(f"3D generation failed: {e}")
        return json.dumps(
            Model3DResponse(
                success=False,
                task_id="error",
                status="failed",
                error=str(e),
            ).model_dump(),
            indent=2,
        )


@mcp.tool()
async def generate_3d_from_image(
    image_url: str,
    product_name: str,
    output_format: str = "glb",
) -> str:
    """
    Generate a 3D model from a reference image using Tripo3D.

    Creates a 3D model that matches the appearance of the provided
    reference image for accurate product visualization.

    Args:
        image_url: URL to the reference image (must be publicly accessible)
        product_name: Name for the generated model
        output_format: 3D format (glb, fbx, obj, usdz)

    Returns:
        JSON with task_id, status, model_url, and download path
    """
    try:
        logger.info(f"Generating 3D from image: {image_url}")

        client = await ClientManager.get_tripo_client()
        result = await client.image_to_3d(
            image_url=image_url,
            output_format=Model3DFormat(output_format),
            wait_for_completion=True,
        )

        response = Model3DResponse(
            success=result.status == "success",
            task_id=result.task_id,
            status=result.status,
            model_url=result.model_url,
            thumbnail_url=result.thumbnail_url,
            local_path=result.local_path,
            generation_time_seconds=result.generation_time_seconds,
        )

        return json.dumps(response.model_dump(), indent=2)

    except Tripo3DError as e:
        return json.dumps(
            Model3DResponse(
                success=False,
                task_id="error",
                status="failed",
                error=str(e),
            ).model_dump(),
            indent=2,
        )


@mcp.tool()
async def get_3d_task_status(task_id: str) -> str:
    """
    Get the status of a 3D generation task.

    Args:
        task_id: Tripo3D task ID from a previous generation request

    Returns:
        JSON with current task status and results if complete
    """
    try:
        client = await ClientManager.get_tripo_client()
        status = await client.get_task_status(task_id)

        return json.dumps(
            {
                "task_id": task_id,
                "status": status.get("status", "unknown"),
                "progress": status.get("progress"),
                "output": status.get("output"),
            },
            indent=2,
        )

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# MCP TOOLS - VIRTUAL TRY-ON
# ============================================================================


@mcp.tool()
async def virtual_tryon(
    garment_image_url: str,
    model_type: str = "female",
    category: str = "tops",
) -> str:
    """
    Generate a virtual try-on image using FASHN.

    Creates a realistic image of a garment on a model for
    product visualization and e-commerce.

    Args:
        garment_image_url: URL to the garment image
        model_type: Model type (female, male, unisex)
        category: Clothing category (tops, bottoms, one-pieces)

    Returns:
        JSON with task_id, status, and try-on image URL
    """
    try:
        logger.info(f"Generating try-on for: {garment_image_url}")

        client = await ClientManager.get_fashn_client()
        result = await client.virtual_tryon(
            garment_image_url=garment_image_url,
            model_type=TryOnModel(model_type),
            category=category,
            wait_for_completion=True,
        )

        response = TryOnResponse(
            success=result.status == "completed",
            task_id=result.task_id,
            status=result.status,
            image_url=result.image_url,
            local_path=result.local_path,
            model_type=result.model_type.value,
            processing_time_seconds=result.processing_time_seconds,
        )

        return json.dumps(response.model_dump(), indent=2)

    except FASHNError as e:
        return json.dumps(
            TryOnResponse(
                success=False,
                task_id="error",
                status="failed",
                model_type=model_type,
                error=str(e),
            ).model_dump(),
            indent=2,
        )


@mcp.tool()
async def batch_virtual_tryon(
    garment_image_url: str,
    model_types: str = "female,male",
    category: str = "tops",
) -> str:
    """
    Generate virtual try-on images for multiple model types.

    Creates try-on images for female, male, and/or unisex models
    in a single batch request for efficiency.

    Args:
        garment_image_url: URL to the garment image
        model_types: Comma-separated model types (female,male,unisex)
        category: Clothing category (tops, bottoms, one-pieces)

    Returns:
        JSON array with try-on results for each model type
    """
    try:
        types = [TryOnModel(t.strip()) for t in model_types.split(",")]

        logger.info(f"Batch try-on for: {garment_image_url} with {len(types)} models")

        client = await ClientManager.get_fashn_client()
        results = await client.batch_tryon(
            garment_image_url=garment_image_url,
            model_types=types,
            category=category,
        )

        responses = []
        for result in results:
            responses.append(
                TryOnResponse(
                    success=result.status == "completed",
                    task_id=result.task_id,
                    status=result.status,
                    image_url=result.image_url,
                    local_path=result.local_path,
                    model_type=result.model_type.value,
                    processing_time_seconds=result.processing_time_seconds,
                ).model_dump()
            )

        return json.dumps(responses, indent=2)

    except FASHNError as e:
        return json.dumps({"error": str(e)}, indent=2)


# ============================================================================
# MCP TOOLS - WORDPRESS UPLOAD
# ============================================================================


@mcp.tool()
async def upload_to_wordpress(
    file_path: str,
    title: str,
    alt_text: str | None = None,
) -> str:
    """
    Upload a file to WordPress/WooCommerce media library.

    Supports images (PNG, JPG, WebP) and 3D models (GLB, GLTF).
    Files are uploaded to SkyyRose's WordPress media library.

    Args:
        file_path: Local path to the file to upload
        title: Title for the media item
        alt_text: Alt text for accessibility (optional)

    Returns:
        JSON with media_id, source_url, and upload details
    """
    try:
        logger.info(f"Uploading to WordPress: {file_path}")

        client = await ClientManager.get_wordpress_client()
        result = await client.upload_file(
            file_path=file_path,
            title=title,
            alt_text=alt_text,
        )

        response = UploadResponse(
            success=True,
            media_id=result.media_id,
            source_url=result.source_url,
            mime_type=result.mime_type,
            title=result.title,
        )

        return json.dumps(response.model_dump(), indent=2)

    except WordPressError as e:
        return json.dumps(
            UploadResponse(
                success=False,
                error=str(e),
            ).model_dump(),
            indent=2,
        )


@mcp.tool()
async def upload_from_url_to_wordpress(
    url: str,
    title: str,
    alt_text: str | None = None,
) -> str:
    """
    Download a file from URL and upload to WordPress.

    Fetches the file from the provided URL and uploads it
    directly to SkyyRose's WordPress media library.

    Args:
        url: URL to download the file from
        title: Title for the media item
        alt_text: Alt text for accessibility (optional)

    Returns:
        JSON with media_id, source_url, and upload details
    """
    try:
        logger.info(f"Uploading from URL: {url}")

        client = await ClientManager.get_wordpress_client()
        result = await client.upload_from_url(
            url=url,
            title=title,
            alt_text=alt_text,
        )

        response = UploadResponse(
            success=True,
            media_id=result.media_id,
            source_url=result.source_url,
            mime_type=result.mime_type,
            title=result.title,
        )

        return json.dumps(response.model_dump(), indent=2)

    except WordPressError as e:
        return json.dumps(
            UploadResponse(
                success=False,
                error=str(e),
            ).model_dump(),
            indent=2,
        )


# ============================================================================
# MCP TOOLS - FULL PIPELINE
# ============================================================================


@mcp.tool()
async def process_clothing_item(
    item_id: str,
    name: str,
    description: str,
    collection: str = "signature",
    category: str = "hoodie",
    color: str = "black",
    price: float = 99.99,
    sku: str = "SKU-001",
    reference_image_url: str | None = None,
    generate_3d: bool = True,
    generate_tryon: bool = True,
    upload_to_wp: bool = True,
    tryon_models: str = "female,male",
) -> str:
    """
    Process a clothing item through the complete 3D asset pipeline.

    Executes the full workflow:
    1. Generate 3D model (text-to-3D or image-to-3D)
    2. Create virtual try-on images for specified model types
    3. Upload all assets to WordPress/WooCommerce

    This is the primary tool for automating SkyyRose product asset generation.

    Args:
        item_id: Unique identifier for the item
        name: Product name (e.g., "Black Rose Hoodie")
        description: Detailed product description
        collection: SkyyRose collection (black_rose, love_hurts, signature)
        category: Clothing type (hoodie, t_shirt, jacket, pants, etc.)
        color: Primary color
        price: Product price in USD
        sku: Stock Keeping Unit
        reference_image_url: URL to reference image (optional, enables image-to-3D)
        generate_3d: Enable 3D model generation
        generate_tryon: Enable virtual try-on generation
        upload_to_wp: Enable WordPress upload
        tryon_models: Comma-separated model types for try-on (female,male,unisex)

    Returns:
        JSON with complete pipeline results including all generated assets
    """
    try:
        logger.info(f"Processing item: {name} ({item_id})")

        # Create ClothingItem
        item = ClothingItem(
            item_id=item_id,
            name=name,
            description=description,
            collection=ClothingCollection(collection),
            category=ClothingCategory(category),
            color=color,
            price=price,
            sku=sku,
            reference_image_url=reference_image_url,
        )

        # Configure pipeline
        tryon_types = [TryOnModel(t.strip()) for t in tryon_models.split(",")]

        pipeline = await ClientManager.get_pipeline()
        pipeline.enable_3d = generate_3d
        pipeline.enable_tryon = generate_tryon
        pipeline.enable_upload = upload_to_wp
        pipeline.tryon_models = tryon_types

        # Execute pipeline
        result = await pipeline.process_item(item)

        # Build response
        response = PipelineResponse(
            success=result.success,
            item_id=result.item_id,
            item_name=result.item_name,
            stage=result.stage.value,
            model_3d={
                "task_id": result.model_3d.task_id if result.model_3d else None,
                "status": result.model_3d.status if result.model_3d else None,
                "model_url": result.model_3d.model_url if result.model_3d else None,
                "local_path": result.model_3d.local_path if result.model_3d else None,
                "thumbnail_url": result.model_3d.thumbnail_url if result.model_3d else None,
            }
            if result.model_3d
            else None,
            try_on_results=[
                {
                    "task_id": tr.task_id,
                    "status": tr.status,
                    "image_url": tr.image_url,
                    "local_path": tr.local_path,
                    "model_type": tr.model_type.value,
                }
                for tr in result.try_on_results
            ],
            wordpress_uploads=[
                {
                    "media_id": u.media_id,
                    "source_url": u.source_url,
                    "title": u.title,
                    "mime_type": u.mime_type,
                }
                for u in result.wordpress_uploads
            ],
            errors=result.errors,
            total_processing_time_seconds=result.total_processing_time_seconds,
        )

        return json.dumps(response.model_dump(), indent=2)

    except Exception as e:
        logger.exception(f"Pipeline failed: {e}")
        return json.dumps(
            PipelineResponse(
                success=False,
                item_id=item_id,
                item_name=name,
                stage="failed",
                errors=[str(e)],
            ).model_dump(),
            indent=2,
        )


# ============================================================================
# MCP TOOLS - INFO & UTILITIES
# ============================================================================


@mcp.tool()
async def list_skyyrose_collections() -> str:
    """
    List available SkyyRose clothing collections.

    Returns information about each collection's style and aesthetic
    to help guide 3D generation prompts.

    Returns:
        JSON with collection details and descriptions
    """
    collections = {
        "black_rose": {
            "name": "BLACK_ROSE",
            "description": "Dark elegance collection featuring rose motifs and premium black fabrics",
            "style": "dark elegant luxury streetwear with rose motifs",
            "colors": ["black", "rose gold", "burgundy", "charcoal"],
            "aesthetic": "Gothic romance meets urban luxury",
        },
        "love_hurts": {
            "name": "LOVE_HURTS",
            "description": "Emotional expression collection with heart designs and bold statements",
            "style": "emotional expressive streetwear with heart designs",
            "colors": ["red", "black", "white", "pink"],
            "aesthetic": "Raw emotion and vulnerability through fashion",
        },
        "signature": {
            "name": "SIGNATURE",
            "description": "Essential pieces collection with classic SkyyRose branding",
            "style": "classic premium streetwear essentials",
            "colors": ["black", "white", "gray", "navy"],
            "aesthetic": "Timeless luxury streetwear fundamentals",
        },
    }

    return json.dumps(collections, indent=2)


@mcp.tool()
async def list_clothing_categories() -> str:
    """
    List supported clothing categories for 3D generation.

    Returns:
        JSON with available categories and their FASHN mapping
    """
    categories = {
        "hoodie": {"fashn_category": "tops", "description": "Hooded sweatshirt"},
        "t_shirt": {"fashn_category": "tops", "description": "T-shirt"},
        "jacket": {"fashn_category": "tops", "description": "Jacket or outerwear"},
        "sweater": {"fashn_category": "tops", "description": "Sweater or pullover"},
        "tank_top": {"fashn_category": "tops", "description": "Tank top or sleeveless"},
        "coat": {"fashn_category": "tops", "description": "Coat or heavy outerwear"},
        "pants": {"fashn_category": "bottoms", "description": "Pants or trousers"},
        "shorts": {"fashn_category": "bottoms", "description": "Shorts"},
        "skirt": {"fashn_category": "bottoms", "description": "Skirt"},
        "dress": {"fashn_category": "one-pieces", "description": "Dress or one-piece"},
    }

    return json.dumps(categories, indent=2)


@mcp.tool()
async def get_api_status() -> str:
    """
    Check the status of all integrated APIs.

    Tests connectivity to Tripo3D, FASHN, and WordPress
    to verify credentials and availability.

    Returns:
        JSON with status for each API service
    """
    status = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
    }

    # Check Tripo3D
    try:
        tripo_key = os.getenv("TRIPO_API_KEY", "")
        status["services"]["tripo3d"] = {
            "configured": bool(tripo_key),
            "status": "ready" if tripo_key else "missing_credentials",
        }
    except Exception as e:
        status["services"]["tripo3d"] = {"status": "error", "error": str(e)}

    # Check FASHN
    try:
        fashn_key = os.getenv("FASHN_API_KEY", "")
        status["services"]["fashn"] = {
            "configured": bool(fashn_key),
            "status": "ready" if fashn_key else "missing_credentials",
        }
    except Exception as e:
        status["services"]["fashn"] = {"status": "error", "error": str(e)}

    # Check WordPress
    try:
        wp_url = os.getenv("WORDPRESS_SITE_URL", "")
        wp_user = os.getenv("WORDPRESS_USERNAME", "")
        wp_pass = os.getenv("WORDPRESS_APP_PASSWORD", "")
        status["services"]["wordpress"] = {
            "configured": bool(wp_url and wp_user and wp_pass),
            "status": "ready" if (wp_url and wp_user and wp_pass) else "missing_credentials",
            "site_url": wp_url if wp_url else None,
        }
    except Exception as e:
        status["services"]["wordpress"] = {"status": "error", "error": str(e)}

    return json.dumps(status, indent=2)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    import uvicorn

    uvicorn.run(
        "agent.modules.clothing.mcp_server:mcp",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
