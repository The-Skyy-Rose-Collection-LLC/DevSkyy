"""
Sync API Endpoints
==================

REST API endpoints for catalog synchronization.

Endpoints:
- POST /api/v1/sync/product - Sync single product
- POST /api/v1/sync/bulk - Sync multiple products
- GET /api/v1/sync/status/{sku} - Get sync status
- GET /api/v1/sync/jobs - List sync jobs

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

sync_router = APIRouter(prefix="/sync", tags=["Catalog Sync"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ProductSyncRequest(BaseModel):
    """Request to sync a single product."""

    sku: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    price: float = Field(..., ge=0)
    description: str = Field(default="")
    short_description: str = Field(default="")
    stock: int = Field(default=0, ge=0)
    categories: list[int] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    image_paths: list[str] = Field(default_factory=list)


class BulkSyncRequest(BaseModel):
    """Request to sync multiple products."""

    products: list[ProductSyncRequest] = Field(...)
    config: dict[str, Any] = Field(default_factory=dict)


class SyncJobResponse(BaseModel):
    """Response with sync job details."""

    job_id: str
    product_sku: str
    status: str
    started_at: str
    completed_at: str | None = None
    success: bool = False
    wordpress_id: int | None = None
    images_uploaded: int = 0
    model_uploaded: bool = False
    photoshoot_generated: bool = False
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SyncStatusResponse(BaseModel):
    """Response with product sync status."""

    product_sku: str
    synced_to_wordpress: bool = False
    wordpress_id: int | None = None
    has_3d_model: bool = False
    has_processed_images: bool = False
    last_sync: str | None = None


class BulkSyncResponse(BaseModel):
    """Response from bulk sync operation."""

    total: int
    successful: int
    failed: int
    job_ids: list[str] = Field(default_factory=list)
    results: list[SyncJobResponse] = Field(default_factory=list)


# =============================================================================
# In-Memory Job Store
# =============================================================================


class SyncJobStore:
    """In-memory storage for sync jobs."""

    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def create(self, product_sku: str) -> str:
        """Create a new sync job."""
        job_id = f"sync_{uuid.uuid4().hex[:12]}"
        self._jobs[job_id] = {
            "job_id": job_id,
            "product_sku": product_sku,
            "status": "queued",
            "started_at": datetime.now(UTC).isoformat(),
            "completed_at": None,
            "success": False,
            "wordpress_id": None,
            "images_uploaded": 0,
            "model_uploaded": False,
            "photoshoot_generated": False,
            "errors": [],
            "warnings": [],
        }
        return job_id

    def get(self, job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs: Any) -> None:
        """Update job fields."""
        if job_id in self._jobs:
            self._jobs[job_id].update(kwargs)

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark job as completed."""
        if job_id in self._jobs:
            self._jobs[job_id].update(
                {
                    "status": "completed",
                    "completed_at": datetime.now(UTC).isoformat(),
                    **result,
                }
            )

    def fail(self, job_id: str, error: str) -> None:
        """Mark job as failed."""
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = "failed"
            self._jobs[job_id]["completed_at"] = datetime.now(UTC).isoformat()
            self._jobs[job_id]["errors"].append(error)

    def list_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        """List recent jobs."""
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return jobs[:limit]


sync_job_store = SyncJobStore()


# =============================================================================
# Background Tasks
# =============================================================================


async def run_product_sync(
    job_id: str,
    product_sku: str,
    product_data: dict[str, Any],
    image_paths: list[str],
) -> None:
    """Run product sync in background."""
    try:
        sync_job_store.update(job_id, status="processing")

        from sync.catalog_sync import CatalogSyncEngine

        engine = CatalogSyncEngine()

        try:
            result = await engine.sync_product(
                product_sku=product_sku,
                product_data=product_data,
                source_images=[Path(p) for p in image_paths],
            )

            sync_job_store.complete(
                job_id,
                {
                    "success": result.success,
                    "wordpress_id": result.wordpress_product_id,
                    "images_uploaded": result.images_uploaded,
                    "model_uploaded": result.model_uploaded,
                    "photoshoot_generated": result.photoshoot_generated,
                    "errors": result.errors,
                    "warnings": result.warnings,
                },
            )

            logger.info(
                "Product sync completed",
                job_id=job_id,
                product_sku=product_sku,
                success=result.success,
            )

        finally:
            await engine.close()

    except Exception as e:
        logger.exception("Product sync failed", job_id=job_id, error=str(e))
        sync_job_store.fail(job_id, str(e))


# =============================================================================
# Endpoints
# =============================================================================


@sync_router.post("/product", response_model=SyncJobResponse)
async def sync_single_product(
    request: ProductSyncRequest,
    background_tasks: BackgroundTasks,
) -> SyncJobResponse:
    """
    Sync a single product to WordPress/WooCommerce.

    Generates 3D model, photoshoot, and uploads everything.
    """
    job_id = sync_job_store.create(request.sku)

    product_data = {
        "name": request.name,
        "price": request.price,
        "description": request.description,
        "short_description": request.short_description,
        "stock": request.stock,
        "categories": request.categories,
        "tags": request.tags,
    }

    if background_tasks:
        background_tasks.add_task(
            run_product_sync,
            job_id,
            request.sku,
            product_data,
            request.image_paths,
        )
    else:
        # Run synchronously for testing
        await run_product_sync(job_id, request.sku, product_data, request.image_paths)

    job = sync_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Failed to create sync job")

    return SyncJobResponse(**job)


@sync_router.post("/bulk", response_model=BulkSyncResponse)
async def sync_bulk_products(
    request: BulkSyncRequest,
    background_tasks: BackgroundTasks,
) -> BulkSyncResponse:
    """Sync multiple products to WordPress/WooCommerce."""
    job_ids = []

    for product in request.products:
        job_id = sync_job_store.create(product.sku)
        job_ids.append(job_id)

        product_data = {
            "name": product.name,
            "price": product.price,
            "description": product.description,
            "stock": product.stock,
        }

        if background_tasks:
            background_tasks.add_task(
                run_product_sync,
                job_id,
                product.sku,
                product_data,
                product.image_paths,
            )

    # Get initial job states
    results = [
        SyncJobResponse(**sync_job_store.get(jid)) for jid in job_ids if sync_job_store.get(jid)
    ]

    return BulkSyncResponse(
        total=len(request.products),
        successful=0,  # Will be updated as jobs complete
        failed=0,
        job_ids=job_ids,
        results=results,
    )


@sync_router.get("/status/{product_sku}", response_model=SyncStatusResponse)
async def get_sync_status(product_sku: str) -> SyncStatusResponse:
    """Get sync status for a product."""
    # Check 3D model
    model_path = Path(f"./generated_models/models/{product_sku}.glb")
    has_3d = model_path.exists()

    # Check images
    images_dir = Path(f"./processed_images/{product_sku}")
    has_images = images_dir.exists() and any(images_dir.iterdir()) if images_dir.exists() else False

    # Check WordPress (would be actual API call in production)
    synced_to_wp = False
    wordpress_id = None

    # Find last sync job
    last_sync = None
    for job in sync_job_store.list_jobs():
        if job.get("product_sku") == product_sku and job.get("status") == "completed":
            last_sync = job.get("completed_at")
            if job.get("success"):
                synced_to_wp = True
                wordpress_id = job.get("wordpress_id")
            break

    return SyncStatusResponse(
        product_sku=product_sku,
        synced_to_wordpress=synced_to_wp,
        wordpress_id=wordpress_id,
        has_3d_model=has_3d,
        has_processed_images=has_images,
        last_sync=last_sync,
    )


@sync_router.get("/jobs", response_model=list[SyncJobResponse])
async def list_sync_jobs(
    limit: int = 50,
    status: str | None = None,
) -> list[SyncJobResponse]:
    """List recent sync jobs."""
    jobs = sync_job_store.list_jobs(limit)

    if status:
        jobs = [j for j in jobs if j.get("status") == status]

    return [SyncJobResponse(**job) for job in jobs]


@sync_router.get("/jobs/{job_id}", response_model=SyncJobResponse)
async def get_sync_job(job_id: str) -> SyncJobResponse:
    """Get sync job by ID."""
    job = sync_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Sync job {job_id} not found")
    return SyncJobResponse(**job)


@sync_router.post("/trigger-all")
async def trigger_full_sync(
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Trigger sync for all pending products."""
    # In production, this would query the database for pending products
    # For now, return a placeholder response
    return {
        "message": "Full sync triggered",
        "queued": 0,
    }


__all__ = ["sync_router"]
