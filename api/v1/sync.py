"""
Sync Pipeline API
=================
API endpoints for managing asset synchronization across HuggingFace, DevSkyy, and WordPress.

Routes:
- GET /api/v1/sync/status - Get sync pipeline status
- POST /api/v1/sync/trigger - Trigger sync operation
- GET /api/v1/sync/health - Health check
"""

import logging
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from prometheus_client import Counter, Histogram
from pydantic import BaseModel, Field, field_validator

from orchestration.sync_pipeline import (
    SyncDirection,
    SyncPipelineStatus,
    SyncTriggerResponse,
    get_sync_pipeline,
)
from security.prometheus_exporter import devskyy_registry

# =============================================================================
# Input Validation Constants
# =============================================================================

VALID_DIRECTIONS = frozenset({"full", "rt_to_hf", "hf_to_devskyy", "devskyy_to_wp"})

logger = logging.getLogger(__name__)

# =============================================================================
# Prometheus Metrics
# =============================================================================

sync_operations_total = Counter(
    "sync_operations_total",
    "Total sync operations",
    ["direction", "status"],
    registry=devskyy_registry,
)

sync_duration_seconds = Histogram(
    "sync_duration_seconds",
    "Sync operation duration in seconds",
    ["direction"],
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=devskyy_registry,
)

# Create router
sync_router = APIRouter(prefix="/sync", tags=["Sync Pipeline"])


# =============================================================================
# Request/Response Models
# =============================================================================


class TriggerSyncRequest(BaseModel):
    """Request to trigger sync operation."""

    direction: Literal["full", "rt_to_hf", "hf_to_devskyy", "devskyy_to_wp"] = Field(
        default="full",
        description="Sync direction: full (all), rt_to_hf, hf_to_devskyy, devskyy_to_wp",
    )

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate direction against whitelist."""
        if v not in VALID_DIRECTIONS:
            raise ValueError(f"Invalid direction: {v}. Valid: {sorted(VALID_DIRECTIONS)}")
        return v


# =============================================================================
# API Endpoints
# =============================================================================


@sync_router.get("/status", response_model=SyncPipelineStatus)
async def get_sync_status():
    """
    Get current sync pipeline status.

    Returns status of all systems in the sync chain:
    - Round Table results availability
    - HuggingFace connectivity
    - WordPress connectivity
    - Local exports status
    """
    try:
        logger.info("Fetching sync pipeline status")
        pipeline = get_sync_pipeline()
        status = await pipeline.get_status()
        logger.info(f"Sync status: {status.status}")
        return status

    except Exception as e:
        logger.error(f"Error getting sync status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@sync_router.post("/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(request: TriggerSyncRequest):
    """
    Trigger a sync operation.

    Available directions:
    - **full**: Run all sync stages (RT → HF → DevSkyy → WP)
    - **rt_to_hf**: Export Round Table results to HuggingFace
    - **hf_to_devskyy**: Download HuggingFace assets to local storage
    - **devskyy_to_wp**: Upload local assets to WordPress

    Returns:
        SyncTriggerResponse with operation results

    Raises:
        400: Invalid direction
        500: Sync operation failed
    """
    # Generate correlation ID for tracing
    correlation_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"[{correlation_id}] Sync triggered: {request.direction}")

        # Map string to enum
        direction_map = {
            "full": SyncDirection.FULL,
            "rt_to_hf": SyncDirection.RT_TO_HF,
            "hf_to_devskyy": SyncDirection.HF_TO_DEVSKYY,
            "devskyy_to_wp": SyncDirection.DEVSKYY_TO_WP,
        }

        direction = direction_map.get(request.direction)
        if not direction:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid direction: {request.direction}",
            )

        pipeline = get_sync_pipeline()
        result = await pipeline.sync(direction=direction)

        # Record metrics
        status = "success" if result.success else "failed"
        sync_operations_total.labels(direction=request.direction, status=status).inc()

        logger.info(f"[{correlation_id}] Sync result: {result.message}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{correlation_id}] Error triggering sync: {e}", exc_info=True)
        sync_operations_total.labels(direction=request.direction, status="error").inc()
        # Don't leak internal error details in production
        raise HTTPException(
            status_code=500, detail=f"Sync operation failed. Reference: {correlation_id}"
        )


@sync_router.post("/rt-to-hf")
async def sync_round_table_to_hf():
    """
    Quick endpoint to sync Round Table results to HuggingFace.

    Reads ROUND_TABLE_ELITE_RESULTS.json and exports to HuggingFace dataset format.
    """
    try:
        logger.info("RT → HF sync triggered")

        pipeline = get_sync_pipeline()
        result = await pipeline.sync_round_table_to_hf()

        sync_operations_total.labels(direction="rt_to_hf", status="success").inc()

        return {
            "success": True,
            "items_synced": result.get("items_synced", 0),
            "export_path": result.get("export_path"),
            "collections": result.get("collections", []),
            "message": f"Exported {result.get('items_synced', 0)} scene specs",
        }

    except Exception as e:
        logger.error(f"RT → HF sync failed: {e}", exc_info=True)
        sync_operations_total.labels(direction="rt_to_hf", status="failed").inc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@sync_router.get("/health")
async def sync_health_check():
    """
    Health check for sync pipeline.

    Returns availability status of all systems.
    """
    try:
        pipeline = get_sync_pipeline()
        status = await pipeline.get_status()

        # Determine health based on system availability
        critical_systems = ["round_table", "huggingface", "wordpress"]
        critical_available = sum(
            1 for s in status.systems if s.system in critical_systems and s.available
        )

        is_healthy = critical_available >= 2  # At least 2/3 critical systems

        return {
            "status": "healthy" if is_healthy else "degraded",
            "service": "sync-pipeline",
            "timestamp": datetime.utcnow().isoformat(),
            "systems_available": critical_available,
            "systems_total": len(critical_systems),
            "last_full_sync": status.last_full_sync,
            "pending_syncs": status.pending_syncs,
        }

    except Exception as e:
        logger.error(f"Sync health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "sync-pipeline",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
