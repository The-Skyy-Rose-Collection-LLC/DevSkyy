# api/v1/assets.py
"""Asset Processing API Endpoints.

This module provides endpoints for:
- Image ingestion for ML processing
- Job status tracking
- Asset management

Implements US-002 (Image Ingestion) and US-011 (Job Status API)

Version: 1.0.0
"""

import io
import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, Field

from security.jwt_oauth2_auth import TokenPayload, get_current_user
from services.storage import (
    AssetInfo,
    AssetNotFoundError,
    AssetVersionManager,
    RetentionPolicy,
    RevertVersionRequest,
    UpdateRetentionRequest,
    VersionInfo,
    VersionListResponse,
    VersionNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["Asset Processing"])


# =============================================================================
# Constants
# =============================================================================

ALLOWED_IMAGE_FORMATS = {"image/jpeg", "image/png", "image/webp", "image/tiff"}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB
MIN_IMAGE_DIMENSION = 100


# =============================================================================
# Enums & Models
# =============================================================================


class JobStatus(str, Enum):
    """Status of a processing job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingProfile(str, Enum):
    """Available processing profiles."""

    FULL = "full"
    QUICK = "quick"
    BACKGROUND_ONLY = "background_only"
    REFORMAT = "reformat"


class ImageSource(str, Enum):
    """Source of the image."""

    API = "api"
    WOOCOMMERCE = "woocommerce"
    DASHBOARD = "dashboard"


class IngestRequest(BaseModel):
    """Request model for image ingestion (JSON metadata)."""

    source: ImageSource = Field(default=ImageSource.API, description="Source of the image")
    product_id: str | None = Field(default=None, description="Associated product ID")
    processing_profile: ProcessingProfile = Field(
        default=ProcessingProfile.FULL,
        description="Processing profile to apply",
    )
    callback_url: str | None = Field(
        default=None,
        description="Webhook URL to call on completion",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata to store with the asset",
    )


class IngestResponse(BaseModel):
    """Response model for image ingestion."""

    job_id: str
    status: str
    message: str
    original_url: str
    created_at: str
    correlation_id: str


class StageInfo(BaseModel):
    """Information about a pipeline stage."""

    name: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    output_url: str | None = None


class JobResponse(BaseModel):
    """Response model for job status."""

    job_id: str
    status: str
    current_stage: str
    progress_percent: int
    stages: list[StageInfo]
    input_url: str
    output_urls: dict[str, str]
    product_id: str | None
    source: str
    created_at: str
    started_at: str | None
    completed_at: str | None
    error_message: str | None
    total_duration_ms: int
    correlation_id: str


class JobListResponse(BaseModel):
    """Response model for job listing."""

    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class JobWebhookPayload(BaseModel):
    """Webhook payload for job completion."""

    job_id: str
    status: str
    output_urls: dict[str, str]
    completed_at: str
    correlation_id: str


# =============================================================================
# In-Memory Storage (Replace with database in production)
# =============================================================================

# Mock storage for jobs
_jobs: dict[str, dict[str, Any]] = {}


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_image(
    file: UploadFile = File(..., description="Image file to process"),
    source: ImageSource = Form(default=ImageSource.API),
    product_id: str | None = Form(default=None),
    processing_profile: ProcessingProfile = Form(default=ProcessingProfile.FULL),
    callback_url: str | None = Form(default=None),
    user: TokenPayload = Depends(get_current_user),
) -> IngestResponse:
    """
    Ingest an image for ML processing.

    Accepts multipart/form-data with:
    - **file**: Image file (JPEG, PNG, WebP, TIFF)
    - **source**: Source of the image (api, woocommerce, dashboard)
    - **product_id**: Optional product ID for linking
    - **processing_profile**: Processing profile (full, quick, background_only, reformat)
    - **callback_url**: Optional webhook URL for completion notification

    Validates:
    - Image format (JPEG, PNG, WebP, TIFF)
    - File size (max 50MB)
    - Image dimensions (min 100x100px)

    Returns a job_id for async tracking.
    """
    job_id = str(uuid4())
    correlation_id = job_id

    logger.info(
        f"Ingesting image for user {user.sub}",
        extra={
            "job_id": job_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "correlation_id": correlation_id,
        },
    )

    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format. Allowed: {', '.join(ALLOWED_IMAGE_FORMATS)}",
        )

    # Read file
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    # Validate image dimensions
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(content))
        width, height = img.size

        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image too small. Minimum dimensions: {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION}px",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file",
        )

    # TODO: Store original image to R2
    # For now, mock the original URL
    original_url = f"https://r2.skyyrose.com/originals/{job_id}/{file.filename}"

    # Create job record
    created_at = datetime.now(UTC).isoformat()
    _jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING.value,
        "current_stage": "ingest",
        "progress_percent": 0,
        "stages_completed": [],
        "input_url": original_url,
        "output_urls": {},
        "product_id": product_id,
        "source": source.value,
        "processing_profile": processing_profile.value,
        "callback_url": callback_url,
        "user_id": user.sub,
        "created_at": created_at,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "total_duration_ms": 0,
        "correlation_id": correlation_id,
    }

    # TODO: Add to processing queue
    # await processing_queue.submit_job(...)

    logger.info(
        "Image ingested successfully",
        extra={
            "job_id": job_id,
            "original_url": original_url,
            "correlation_id": correlation_id,
        },
    )

    return IngestResponse(
        job_id=job_id,
        status=JobStatus.PENDING.value,
        message="Image accepted for processing",
        original_url=original_url,
        created_at=created_at,
        correlation_id=correlation_id,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> JobResponse:
    """
    Get the status of a processing job.

    Returns:
    - **status**: Current job status (pending, running, succeeded, failed, cancelled)
    - **current_stage**: Active pipeline stage
    - **progress_percent**: Completion percentage (0-100)
    - **output_urls**: URLs of processed images (when complete)
    - **error_message**: Error details if failed
    """
    job = _jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    # Check user ownership (in production, also check admin role)
    if job.get("user_id") != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job",
        )

    # Build stage info
    stages = []
    for stage_name in ["ingest", "validate", "background_removal", "lighting", "upscale", "format"]:
        stage_status = "pending"
        if stage_name in job.get("stages_completed", []):
            stage_status = "completed"
        elif stage_name == job.get("current_stage"):
            stage_status = "running"

        stages.append(
            StageInfo(
                name=stage_name,
                status=stage_status,
                output_url=job.get("output_urls", {}).get(stage_name),
            )
        )

    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        current_stage=job.get("current_stage", "ingest"),
        progress_percent=job.get("progress_percent", 0),
        stages=stages,
        input_url=job["input_url"],
        output_urls=job.get("output_urls", {}),
        product_id=job.get("product_id"),
        source=job["source"],
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
        error_message=job.get("error_message"),
        total_duration_ms=job.get("total_duration_ms", 0),
        correlation_id=job["correlation_id"],
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(default=None, description="Filter by status"),
    source: ImageSource | None = Query(default=None, description="Filter by source"),
    product_id: str | None = Query(default=None, description="Filter by product ID"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    user: TokenPayload = Depends(get_current_user),
) -> JobListResponse:
    """
    List processing jobs for the current user.

    Supports filtering by:
    - **status**: pending, running, succeeded, failed, cancelled
    - **source**: api, woocommerce, dashboard
    - **product_id**: Associated product ID

    Pagination via page and page_size parameters.
    """
    # Filter jobs by user
    user_jobs = [j for j in _jobs.values() if j.get("user_id") == user.sub]

    # Apply filters
    if status:
        user_jobs = [j for j in user_jobs if j["status"] == status.value]

    if source:
        user_jobs = [j for j in user_jobs if j["source"] == source.value]

    if product_id:
        user_jobs = [j for j in user_jobs if j.get("product_id") == product_id]

    # Sort by created_at descending
    user_jobs.sort(key=lambda j: j["created_at"], reverse=True)

    # Paginate
    total = len(user_jobs)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_jobs = user_jobs[start_idx:end_idx]

    # Convert to response format
    job_responses = []
    for job in page_jobs:
        stages = []
        for stage_name in [
            "ingest",
            "validate",
            "background_removal",
            "lighting",
            "upscale",
            "format",
        ]:
            stage_status = "pending"
            if stage_name in job.get("stages_completed", []):
                stage_status = "completed"
            elif stage_name == job.get("current_stage"):
                stage_status = "running"

            stages.append(
                StageInfo(
                    name=stage_name,
                    status=stage_status,
                    output_url=job.get("output_urls", {}).get(stage_name),
                )
            )

        job_responses.append(
            JobResponse(
                job_id=job["job_id"],
                status=job["status"],
                current_stage=job.get("current_stage", "ingest"),
                progress_percent=job.get("progress_percent", 0),
                stages=stages,
                input_url=job["input_url"],
                output_urls=job.get("output_urls", {}),
                product_id=job.get("product_id"),
                source=job["source"],
                created_at=job["created_at"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                error_message=job.get("error_message"),
                total_duration_ms=job.get("total_duration_ms", 0),
                correlation_id=job["correlation_id"],
            )
        )

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end_idx < total,
    )


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> JobResponse:
    """
    Cancel a pending or running job.

    Only jobs in pending or running status can be cancelled.
    """
    job = _jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job.get("user_id") != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job",
        )

    if job["status"] not in (JobStatus.PENDING.value, JobStatus.RUNNING.value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job in {job['status']} status",
        )

    # Update job status
    job["status"] = JobStatus.CANCELLED.value
    job["completed_at"] = datetime.now(UTC).isoformat()

    logger.info(
        f"Job {job_id} cancelled by user {user.sub}",
        extra={"correlation_id": job["correlation_id"]},
    )

    return await get_job_status(job_id, user)


@router.post("/jobs/{job_id}/retry", response_model=IngestResponse)
async def retry_job(
    job_id: str,
    user: TokenPayload = Depends(get_current_user),
) -> IngestResponse:
    """
    Retry a failed job.

    Creates a new job using the same input and configuration.
    """
    job = _jobs.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )

    if job.get("user_id") != user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this job",
        )

    if job["status"] != JobStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed jobs can be retried",
        )

    # Create new job with same configuration
    new_job_id = str(uuid4())
    correlation_id = new_job_id
    created_at = datetime.now(UTC).isoformat()

    _jobs[new_job_id] = {
        "job_id": new_job_id,
        "status": JobStatus.PENDING.value,
        "current_stage": "ingest",
        "progress_percent": 0,
        "stages_completed": [],
        "input_url": job["input_url"],
        "output_urls": {},
        "product_id": job.get("product_id"),
        "source": job["source"],
        "processing_profile": job.get("processing_profile", "full"),
        "callback_url": job.get("callback_url"),
        "user_id": user.sub,
        "created_at": created_at,
        "started_at": None,
        "completed_at": None,
        "error_message": None,
        "total_duration_ms": 0,
        "correlation_id": correlation_id,
        "original_job_id": job_id,  # Link to original
    }

    logger.info(
        f"Job {job_id} retried as {new_job_id}",
        extra={"correlation_id": correlation_id},
    )

    return IngestResponse(
        job_id=new_job_id,
        status=JobStatus.PENDING.value,
        message="Job retried successfully",
        original_url=job["input_url"],
        created_at=created_at,
        correlation_id=correlation_id,
    )


# =============================================================================
# Asset Versioning Endpoints (US-023)
# =============================================================================


# Dependency to get version manager
async def get_version_manager() -> AssetVersionManager:
    """Get the AssetVersionManager instance.

    In production, this would get the manager from app state
    or dependency injection container.
    """
    # TODO: Wire up to actual R2 client from app state
    # For now, create a mock instance for API structure
    from services.storage import R2Client, R2Config

    config = R2Config.from_env()
    r2_client = R2Client(config)
    return AssetVersionManager(r2_client=r2_client)


class VersionRevertRequest(BaseModel):
    """Request to revert an asset to a previous version."""

    target_version: int = Field(ge=1, description="Version number to revert to")
    create_new_version: bool = Field(
        default=True,
        description="If True, creates a new version with old content. If False, just updates pointer.",
    )


class RetentionUpdateRequest(BaseModel):
    """Request to update retention policy for an asset."""

    policy: RetentionPolicy = Field(description="Retention policy to apply")
    value: int | None = Field(
        default=None,
        ge=1,
        description="Value for the policy (N versions for KEEP_LAST_N, days for KEEP_DAYS)",
    )


@router.get("/{asset_id}/versions", response_model=VersionListResponse)
async def list_asset_versions(
    asset_id: str,
    include_deleted: bool = Query(default=False, description="Include deleted versions"),
    user: TokenPayload = Depends(get_current_user),
    version_manager: AssetVersionManager = Depends(get_version_manager),
) -> VersionListResponse:
    """
    Get version history for an asset.

    Returns all versions of the asset, optionally including soft-deleted versions.

    - **asset_id**: The asset identifier
    - **include_deleted**: If True, includes versions marked for deletion
    """
    correlation_id = str(uuid4())

    logger.info(
        f"Listing versions for asset {asset_id}",
        extra={
            "asset_id": asset_id,
            "user_id": user.sub,
            "correlation_id": correlation_id,
        },
    )

    try:
        response = await version_manager.list_versions(
            asset_id=asset_id,
            include_deleted=include_deleted,
        )
        return response

    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error listing versions: {e}",
            extra={"asset_id": asset_id, "correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list versions",
        )


@router.get("/{asset_id}/versions/{version_number}", response_model=VersionInfo)
async def get_asset_version(
    asset_id: str,
    version_number: int,
    user: TokenPayload = Depends(get_current_user),
    version_manager: AssetVersionManager = Depends(get_version_manager),
) -> VersionInfo:
    """
    Get a specific version of an asset.

    Returns metadata and download URL for the specified version.

    - **asset_id**: The asset identifier
    - **version_number**: Version number (1 is the original)
    """
    correlation_id = str(uuid4())

    logger.info(
        f"Getting version {version_number} for asset {asset_id}",
        extra={
            "asset_id": asset_id,
            "version_number": version_number,
            "user_id": user.sub,
            "correlation_id": correlation_id,
        },
    )

    try:
        version = await version_manager.get_version(
            asset_id=asset_id,
            version_number=version_number,
        )
        return version

    except VersionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error getting version: {e}",
            extra={
                "asset_id": asset_id,
                "version_number": version_number,
                "correlation_id": correlation_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get version",
        )


@router.post("/{asset_id}/revert", response_model=VersionInfo)
async def revert_asset_version(
    asset_id: str,
    request: VersionRevertRequest,
    user: TokenPayload = Depends(get_current_user),
    version_manager: AssetVersionManager = Depends(get_version_manager),
) -> VersionInfo:
    """
    Revert an asset to a previous version.

    By default, creates a new version with the content of the target version.
    If create_new_version is False, just updates the current version pointer.

    - **asset_id**: The asset identifier
    - **target_version**: Version number to revert to
    - **create_new_version**: Whether to create a new version (recommended)
    """
    correlation_id = str(uuid4())

    logger.info(
        f"Reverting asset {asset_id} to version {request.target_version}",
        extra={
            "asset_id": asset_id,
            "target_version": request.target_version,
            "create_new_version": request.create_new_version,
            "user_id": user.sub,
            "correlation_id": correlation_id,
        },
    )

    try:
        revert_request = RevertVersionRequest(
            asset_id=asset_id,
            target_version=request.target_version,
            create_new_version=request.create_new_version,
        )

        version = await version_manager.revert_version(
            request=revert_request,
            reverted_by=user.sub,
        )

        logger.info(
            f"Asset {asset_id} reverted to version {request.target_version}",
            extra={
                "asset_id": asset_id,
                "new_version": version.version_number,
                "correlation_id": correlation_id,
            },
        )

        return version

    except VersionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error reverting version: {e}",
            extra={
                "asset_id": asset_id,
                "target_version": request.target_version,
                "correlation_id": correlation_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revert version",
        )


@router.put("/{asset_id}/retention", response_model=AssetInfo)
async def update_asset_retention(
    asset_id: str,
    request: RetentionUpdateRequest,
    user: TokenPayload = Depends(get_current_user),
    version_manager: AssetVersionManager = Depends(get_version_manager),
) -> AssetInfo:
    """
    Update the retention policy for an asset.

    Requires admin privileges.

    Available policies:
    - **KEEP_ALL**: Keep all versions forever (default)
    - **KEEP_LAST_N**: Keep only the last N versions (requires value)
    - **KEEP_DAYS**: Keep versions for N days (requires value)

    Note: The original version (v1) is never deleted regardless of policy.
    """
    correlation_id = str(uuid4())

    # TODO: Check for admin role
    # if "admin" not in user.roles:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin privileges required to update retention policy",
    #     )

    logger.info(
        f"Updating retention for asset {asset_id}",
        extra={
            "asset_id": asset_id,
            "policy": request.policy.value,
            "value": request.value,
            "user_id": user.sub,
            "correlation_id": correlation_id,
        },
    )

    # Validate policy requirements
    if request.policy in (RetentionPolicy.KEEP_LAST_N, RetentionPolicy.KEEP_DAYS):
        if request.value is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Policy {request.policy.value} requires a value parameter",
            )

    try:
        update_request = UpdateRetentionRequest(
            asset_id=asset_id,
            policy=request.policy,
            value=request.value,
        )

        asset_info = await version_manager.update_retention(request=update_request)

        logger.info(
            f"Retention updated for asset {asset_id}",
            extra={
                "asset_id": asset_id,
                "new_policy": request.policy.value,
                "correlation_id": correlation_id,
            },
        )

        return asset_info

    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error updating retention: {e}",
            extra={
                "asset_id": asset_id,
                "policy": request.policy.value,
                "correlation_id": correlation_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update retention policy",
        )


@router.delete("/{asset_id}/versions/{version_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_version(
    asset_id: str,
    version_number: int,
    user: TokenPayload = Depends(get_current_user),
    version_manager: AssetVersionManager = Depends(get_version_manager),
) -> None:
    """
    Soft-delete a specific version of an asset.

    Marks the version as PENDING_DELETE. Actual deletion happens during cleanup.
    The original version (v1) cannot be deleted.

    - **asset_id**: The asset identifier
    - **version_number**: Version number to delete (cannot be 1)
    """
    correlation_id = str(uuid4())

    if version_number == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the original version (v1)",
        )

    logger.info(
        f"Deleting version {version_number} of asset {asset_id}",
        extra={
            "asset_id": asset_id,
            "version_number": version_number,
            "user_id": user.sub,
            "correlation_id": correlation_id,
        },
    )

    try:
        await version_manager.delete_version(
            asset_id=asset_id,
            version_number=version_number,
        )

        logger.info(
            f"Version {version_number} of asset {asset_id} marked for deletion",
            extra={"correlation_id": correlation_id},
        )

    except VersionNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(
            f"Error deleting version: {e}",
            extra={
                "asset_id": asset_id,
                "version_number": version_number,
                "correlation_id": correlation_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete version",
        )
