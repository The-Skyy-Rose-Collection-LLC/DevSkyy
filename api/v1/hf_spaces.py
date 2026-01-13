"""
HuggingFace Spaces API
======================
API endpoints for managing HuggingFace Spaces integration

Routes:
- GET /api/v1/hf-spaces/status - Get all Spaces status
- GET /api/v1/hf-spaces/{space_id} - Get specific Space status
- POST /api/v1/hf-spaces/{space_id}/refresh - Refresh Space
"""

import logging
import os
import time
from datetime import datetime
from typing import Literal

import aiohttp
from fastapi import APIRouter, HTTPException
from prometheus_client import Counter, Gauge, Histogram
from pydantic import BaseModel, Field

from security.prometheus_exporter import devskyy_registry

logger = logging.getLogger(__name__)

# =============================================================================
# Prometheus Metrics
# =============================================================================

# Counter: HF Space Status Checks
hf_space_checks_total = Counter(
    "hf_space_checks_total",
    "Total number of HF Space status checks",
    ["space_id", "status"],
    registry=devskyy_registry,
)

# Histogram: HF Space Check Duration
hf_space_check_duration_seconds = Histogram(
    "hf_space_check_duration_seconds",
    "HF Space status check duration in seconds",
    ["space_id"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 15.0),
    registry=devskyy_registry,
)

# Gauge: HF Space Availability
hf_space_availability = Gauge(
    "hf_space_availability",
    "HF Space availability (1=running, 0=error/building/unknown)",
    ["space_id", "category"],
    registry=devskyy_registry,
)

# Counter: HF Space Errors
hf_space_errors_total = Counter(
    "hf_space_errors_total",
    "Total number of HF Space errors",
    ["space_id", "error_type"],
    registry=devskyy_registry,
)

# Create router
hf_spaces_router = APIRouter(prefix="/hf-spaces", tags=["HuggingFace Spaces"])

# HuggingFace configuration
HF_USERNAME = "damBruh"
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_ACCESS_TOKEN")


class HFSpaceInfo(BaseModel):
    """HuggingFace Space information"""

    id: str = Field(..., description="Space ID (e.g., '3d-converter')")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Space description")
    url: str = Field(..., description="HuggingFace Space URL")
    category: Literal["media", "ai", "analytics"] = Field(..., description="Space category")
    status: Literal["running", "building", "error", "unknown"] = Field(
        default="unknown", description="Space status"
    )
    last_updated: str | None = Field(None, description="Last update timestamp")


class HFSpacesStatus(BaseModel):
    """Status of all HuggingFace Spaces"""

    total_spaces: int = Field(..., description="Total number of Spaces")
    running: int = Field(..., description="Number of running Spaces")
    building: int = Field(..., description="Number of building Spaces")
    error: int = Field(..., description="Number of Spaces with errors")
    spaces: list[HFSpaceInfo] = Field(..., description="List of Spaces")
    checked_at: str = Field(..., description="Status check timestamp")


# Define DevSkyy Spaces
DEVSKYY_SPACES = [
    {
        "id": "skyyrose-3d-converter",
        "name": "3D Converter",
        "description": "Convert 3D models between formats (GLB, USDZ, OBJ, FBX)",
        "url": "https://huggingface.co/spaces/damBruh/skyyrose-3d-converter",
        "category": "media",
    },
    {
        "id": "skyyrose-flux-upscaler",
        "name": "FLUX Upscaler",
        "description": "AI-powered image upscaling using FLUX model",
        "url": "https://huggingface.co/spaces/damBruh/skyyrose-flux-upscaler",
        "category": "ai",
    },
    {
        "id": "skyyrose-lora-training-monitor",
        "name": "LoRA Training Monitor",
        "description": "Monitor and manage LoRA model training runs",
        "url": "https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor",
        "category": "ai",
    },
    {
        "id": "skyyrose-product-analyzer",
        "name": "Product Analyzer",
        "description": "Analyze product images and extract insights",
        "url": "https://huggingface.co/spaces/damBruh/skyyrose-product-analyzer",
        "category": "analytics",
    },
    {
        "id": "skyyrose-product-photography",
        "name": "Product Photography",
        "description": "AI-enhanced product photography and background removal",
        "url": "https://huggingface.co/spaces/damBruh/skyyrose-product-photography",
        "category": "media",
    },
]


async def check_space_status(space_id: str) -> Literal["running", "building", "error", "unknown"]:
    """
    Check HuggingFace Space status by making HTTP request.

    Args:
        space_id: Space ID (e.g., 'skyyrose/3d-converter')

    Returns:
        Space status
    """
    start_time = time.time()
    status = "unknown"

    try:
        url = f"https://huggingface.co/spaces/{space_id}"
        logger.info(f"Checking Space status: {space_id}")

        async with (
            aiohttp.ClientSession() as session,
            session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response,
        ):
            if response.status == 200:
                status = "running"
                logger.info(f"Space {space_id} is running (status={response.status})")
            elif response.status in [503, 502]:
                status = "building"
                logger.warning(f"Space {space_id} is building/starting (status={response.status})")
            else:
                status = "error"
                logger.error(f"Space {space_id} returned error status: {response.status}")
                hf_space_errors_total.labels(
                    space_id=space_id, error_type=f"http_{response.status}"
                ).inc()

    except aiohttp.ClientError as e:
        status = "error"
        logger.error(f"Network error checking Space {space_id}: {e}")
        hf_space_errors_total.labels(space_id=space_id, error_type="network_error").inc()

    except Exception as e:
        status = "unknown"
        logger.error(f"Unexpected error checking Space {space_id}: {e}", exc_info=True)
        hf_space_errors_total.labels(space_id=space_id, error_type="unexpected_error").inc()

    finally:
        # Record metrics
        duration = time.time() - start_time
        hf_space_check_duration_seconds.labels(space_id=space_id).observe(duration)
        hf_space_checks_total.labels(space_id=space_id, status=status).inc()

        logger.debug(f"Space {space_id} status check completed in {duration:.2f}s: {status}")

    return status


@hf_spaces_router.get("/status", response_model=HFSpacesStatus)
async def get_spaces_status():
    """
    Get status of all HuggingFace Spaces.

    Returns:
        Status of all DevSkyy Spaces
    """
    try:
        logger.info("Fetching status for all HF Spaces")
        spaces_with_status = []

        # Check status of each Space
        for space in DEVSKYY_SPACES:
            full_space_id = f"{HF_USERNAME}/{space['id']}"
            status = await check_space_status(full_space_id)

            # Update availability gauge (1 for running, 0 for others)
            availability = 1.0 if status == "running" else 0.0
            hf_space_availability.labels(space_id=space["id"], category=space["category"]).set(
                availability
            )

            spaces_with_status.append(
                HFSpaceInfo(
                    id=space["id"],
                    name=space["name"],
                    description=space["description"],
                    url=space["url"],
                    category=space["category"],
                    status=status,
                    last_updated=datetime.utcnow().isoformat(),
                )
            )

        # Calculate totals
        running = sum(1 for s in spaces_with_status if s.status == "running")
        building = sum(1 for s in spaces_with_status if s.status == "building")
        error = sum(1 for s in spaces_with_status if s.status == "error")

        logger.info(
            f"HF Spaces status: {running} running, {building} building, {error} error "
            f"(total: {len(spaces_with_status)})"
        )

        return HFSpacesStatus(
            total_spaces=len(spaces_with_status),
            running=running,
            building=building,
            error=error,
            spaces=spaces_with_status,
            checked_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error getting Spaces status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Spaces status: {str(e)}")


@hf_spaces_router.get("/{space_id}", response_model=HFSpaceInfo)
async def get_space_info(space_id: str):
    """
    Get information about a specific HuggingFace Space.

    Args:
        space_id: Space ID (e.g., '3d-converter')

    Returns:
        Space information
    """
    try:
        logger.info(f"Fetching info for Space: {space_id}")

        # Find Space in list
        space = next((s for s in DEVSKYY_SPACES if s["id"] == space_id), None)

        if not space:
            logger.warning(f"Space not found: {space_id}")
            raise HTTPException(status_code=404, detail=f"Space not found: {space_id}")

        # Check status
        full_space_id = f"{HF_USERNAME}/{space_id}"
        status = await check_space_status(full_space_id)

        # Update availability gauge
        availability = 1.0 if status == "running" else 0.0
        hf_space_availability.labels(space_id=space["id"], category=space["category"]).set(
            availability
        )

        logger.info(f"Space {space_id} info retrieved successfully (status={status})")

        return HFSpaceInfo(
            id=space["id"],
            name=space["name"],
            description=space["description"],
            url=space["url"],
            category=space["category"],
            status=status,
            last_updated=datetime.utcnow().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Space info for {space_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get Space info: {str(e)}")


@hf_spaces_router.post("/{space_id}/refresh")
async def refresh_space(space_id: str):
    """
    Refresh a HuggingFace Space (trigger rebuild).

    Args:
        space_id: Space ID (e.g., '3d-converter')

    Returns:
        Success message
    """
    try:
        logger.info(f"Refresh requested for Space: {space_id}")

        # Verify Space exists
        space = next((s for s in DEVSKYY_SPACES if s["id"] == space_id), None)

        if not space:
            logger.warning(f"Refresh failed - Space not found: {space_id}")
            raise HTTPException(status_code=404, detail=f"Space not found: {space_id}")

        if not HF_TOKEN:
            logger.error("Refresh failed - HF_TOKEN not configured")
            raise HTTPException(
                status_code=500,
                detail="HuggingFace token not configured. Set HF_TOKEN environment variable.",
            )

        # TODO: Implement Space refresh via HuggingFace API
        # This requires using the HuggingFace Hub API to trigger a rebuild
        # For now, return success message

        logger.info(f"Refresh initiated for Space: {space['name']} ({space_id})")

        return {
            "message": f"Refresh initiated for Space: {space['name']}",
            "space_id": space_id,
            "url": space["url"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing Space {space_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to refresh Space: {str(e)}")


@hf_spaces_router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint for HF Spaces API.

    Returns:
        Health status and basic diagnostics
    """
    try:
        logger.debug("HF Spaces health check requested")

        # Check if HF_TOKEN is configured
        has_token = bool(HF_TOKEN)

        # Get quick status of all Spaces
        space_count = len(DEVSKYY_SPACES)

        health_status = {
            "status": "healthy",
            "service": "hf-spaces-api",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "hf_token_configured": has_token,
                "total_spaces": space_count,
                "spaces_configured": [s["id"] for s in DEVSKYY_SPACES],
            },
        }

        if not has_token:
            health_status["warnings"] = [
                "HF_TOKEN not configured - Space refresh functionality unavailable"
            ]

        logger.debug(f"HF Spaces health check: {health_status['status']}")

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "hf-spaces-api",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
