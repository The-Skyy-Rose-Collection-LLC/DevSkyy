# api/v1/brand_assets.py
"""Brand asset ingestion API for training data preparation.

Implements US-013: Brand asset ingestion for training.

Features:
- Bulk ingestion (up to 100 images per request)
- Category classification (product, lifestyle, campaign, mood_board)
- Auto-extract visual features (color palettes, composition, lighting)
- Training readiness check (minimum asset requirements)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from security.jwt_oauth2_auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/brand-assets", tags=["Brand Assets"])


# =============================================================================
# Enums
# =============================================================================


class BrandAssetCategory(str, Enum):
    """Category of brand asset."""

    PRODUCT = "product"
    LIFESTYLE = "lifestyle"
    CAMPAIGN = "campaign"
    MOOD_BOARD = "mood_board"
    TEXTURE = "texture"
    COLOR_REFERENCE = "color_reference"


class AssetApprovalStatus(str, Enum):
    """Approval status for brand assets."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class IngestionJobStatus(str, Enum):
    """Status of bulk ingestion job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class TrainingReadinessStatus(str, Enum):
    """Training readiness status."""

    READY = "ready"
    NOT_READY = "not_ready"
    NEEDS_REVIEW = "needs_review"


# =============================================================================
# Models - Requests
# =============================================================================


class BrandAssetMetadata(BaseModel):
    """Metadata for a brand asset."""

    campaign: str | None = None
    season: str | None = None
    photographer: str | None = None
    location: str | None = None
    shoot_date: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    notes: str | None = None


class BrandAssetUpload(BaseModel):
    """Single asset in bulk upload."""

    url: str = Field(..., description="URL of image to ingest")
    category: BrandAssetCategory
    metadata: BrandAssetMetadata = Field(default_factory=BrandAssetMetadata)


class BulkIngestionRequest(BaseModel):
    """Request for bulk brand asset ingestion."""

    assets: list[BrandAssetUpload] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of assets to ingest (max 100)",
    )
    campaign_name: str | None = Field(None, description="Campaign name for all assets")
    auto_approve: bool = Field(False, description="Auto-approve assets after ingestion")
    extract_features: bool = Field(True, description="Extract visual features")


# =============================================================================
# Models - Responses
# =============================================================================


class ColorPalette(BaseModel):
    """Extracted color palette from image."""

    primary: str = Field(..., description="Primary color hex")
    secondary: list[str] = Field(default_factory=list, description="Secondary colors")
    accent: str | None = Field(None, description="Accent color hex")


class CompositionAnalysis(BaseModel):
    """Composition analysis of image."""

    type: str = Field(..., description="Composition type (centered, rule_of_thirds, etc.)")
    focal_point: str | None = Field(None, description="Focal point location")
    balance: str = Field("balanced", description="Visual balance")


class LightingProfile(BaseModel):
    """Lighting analysis of image."""

    type: str = Field(..., description="Lighting type (natural, studio, dramatic, etc.)")
    direction: str | None = Field(None, description="Light direction")
    mood: str | None = Field(None, description="Lighting mood")


class VisualFeatures(BaseModel):
    """Extracted visual features from image."""

    color_palette: ColorPalette | None = None
    composition: CompositionAnalysis | None = None
    lighting: LightingProfile | None = None
    style_tags: list[str] = Field(default_factory=list)
    quality_score: float = Field(0.0, ge=0.0, le=1.0)


class BrandAsset(BaseModel):
    """Brand asset with extracted features."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    url: str
    category: BrandAssetCategory
    approval_status: AssetApprovalStatus = AssetApprovalStatus.PENDING
    metadata: BrandAssetMetadata = Field(default_factory=BrandAssetMetadata)
    visual_features: VisualFeatures | None = None
    file_size_bytes: int = 0
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None
    r2_key: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_by: str | None = None


class IngestionJobResult(BaseModel):
    """Result of individual asset ingestion."""

    url: str
    success: bool
    asset_id: str | None = None
    error: str | None = None


class BulkIngestionJob(BaseModel):
    """Bulk ingestion job status."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    status: IngestionJobStatus = IngestionJobStatus.PENDING
    total: int = 0
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[IngestionJobResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    created_by: str | None = None


class BrandAssetsListResponse(BaseModel):
    """Paginated list of brand assets."""

    assets: list[BrandAsset]
    total: int
    page: int
    page_size: int
    has_more: bool


class CategoryStats(BaseModel):
    """Statistics for a category."""

    category: BrandAssetCategory
    total: int
    approved: int
    pending: int
    rejected: int


class TrainingReadinessResponse(BaseModel):
    """Training readiness assessment."""

    status: TrainingReadinessStatus
    total_assets: int
    approved_assets: int
    minimum_required: int
    categories: list[CategoryStats]
    recommendations: list[str] = Field(default_factory=list)
    estimated_training_time: str | None = None


# =============================================================================
# In-Memory Storage (Replace with DB in production)
# =============================================================================


_brand_assets: dict[str, BrandAsset] = {}
_ingestion_jobs: dict[str, BulkIngestionJob] = {}


# =============================================================================
# Helper Functions
# =============================================================================


async def extract_visual_features(
    image_url: str,
    *,
    correlation_id: str | None = None,
) -> VisualFeatures:
    """Extract visual features from image.

    In production, this would call ML models to analyze the image.

    Args:
        image_url: URL of image to analyze
        correlation_id: Optional correlation ID

    Returns:
        VisualFeatures with extracted data
    """
    # TODO: Integrate with actual ML pipeline
    # For now, return placeholder features
    return VisualFeatures(
        color_palette=ColorPalette(
            primary="#1A1A1A",
            secondary=["#B76E79", "#FFFFFF"],
            accent="#B76E79",
        ),
        composition=CompositionAnalysis(
            type="centered",
            focal_point="center",
            balance="balanced",
        ),
        lighting=LightingProfile(
            type="studio",
            direction="front",
            mood="dramatic",
        ),
        style_tags=["luxury", "minimal", "sophisticated"],
        quality_score=0.85,
    )


async def process_bulk_ingestion(
    job_id: str,
    request: BulkIngestionRequest,
    user_id: str,
) -> None:
    """Process bulk ingestion in background.

    Args:
        job_id: Job identifier
        request: Ingestion request
        user_id: User who initiated the job
    """
    job = _ingestion_jobs.get(job_id)
    if not job:
        return

    job.status = IngestionJobStatus.PROCESSING

    for asset_upload in request.assets:
        try:
            # Extract features if requested
            features = None
            if request.extract_features:
                features = await extract_visual_features(
                    asset_upload.url,
                    correlation_id=job_id,
                )

            # Create asset
            asset = BrandAsset(
                url=asset_upload.url,
                category=asset_upload.category,
                approval_status=(
                    AssetApprovalStatus.APPROVED
                    if request.auto_approve
                    else AssetApprovalStatus.PENDING
                ),
                metadata=asset_upload.metadata,
                visual_features=features,
                created_by=user_id,
            )

            # Apply campaign name if provided
            if request.campaign_name:
                asset.metadata.campaign = request.campaign_name

            _brand_assets[asset.id] = asset

            job.results.append(
                IngestionJobResult(
                    url=asset_upload.url,
                    success=True,
                    asset_id=asset.id,
                )
            )
            job.succeeded += 1

        except Exception as e:
            logger.error(
                f"Failed to ingest {asset_upload.url}: {e}",
                extra={"job_id": job_id},
            )
            job.results.append(
                IngestionJobResult(
                    url=asset_upload.url,
                    success=False,
                    error=str(e),
                )
            )
            job.failed += 1

        job.processed += 1

    # Finalize job
    job.completed_at = datetime.now(UTC)
    if job.failed == 0:
        job.status = IngestionJobStatus.COMPLETED
    elif job.succeeded == 0:
        job.status = IngestionJobStatus.FAILED
    else:
        job.status = IngestionJobStatus.PARTIAL

    logger.info(
        f"Bulk ingestion job {job_id} completed: {job.succeeded}/{job.total} succeeded",
    )


# =============================================================================
# Endpoints - Ingestion
# =============================================================================


@router.post("/ingest/bulk", response_model=BulkIngestionJob)
async def bulk_ingest_brand_assets(
    request: BulkIngestionRequest,
    background_tasks: BackgroundTasks,
    current_user: TokenPayload = Depends(get_current_user),
) -> BulkIngestionJob:
    """
    Bulk ingest brand assets for training.

    - Accepts up to **100 images** per request
    - Supports all major image formats
    - Optionally extracts visual features (color palette, composition, lighting)
    - Can auto-approve assets

    Images are processed in the background. Use the returned job ID
    to check progress via `/ingest/{job_id}`.
    """
    job = BulkIngestionJob(
        total=len(request.assets),
        created_by=current_user.sub,
    )
    _ingestion_jobs[job.id] = job

    # Process in background
    background_tasks.add_task(
        process_bulk_ingestion,
        job.id,
        request,
        current_user.sub,
    )

    logger.info(
        f"Started bulk ingestion job {job.id} with {len(request.assets)} assets",
        extra={"user_id": current_user.sub},
    )

    return job


@router.get("/ingest/{job_id}", response_model=BulkIngestionJob)
async def get_ingestion_job(
    job_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> BulkIngestionJob:
    """
    Get bulk ingestion job status and progress.

    Returns current progress and results of individual asset ingestions.
    """
    job = _ingestion_jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job not found: {job_id}",
        )
    return job


# =============================================================================
# Endpoints - Assets
# =============================================================================


@router.get("/assets", response_model=BrandAssetsListResponse)
async def list_brand_assets(
    category: BrandAssetCategory | None = Query(None),
    approval_status: AssetApprovalStatus | None = Query(None),
    campaign: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAssetsListResponse:
    """
    List brand assets with filtering.

    Filter by:
    - **category**: product, lifestyle, campaign, mood_board, texture, color_reference
    - **approval_status**: pending, approved, rejected
    - **campaign**: Campaign name
    """
    assets = list(_brand_assets.values())

    # Apply filters
    if category:
        assets = [a for a in assets if a.category == category]
    if approval_status:
        assets = [a for a in assets if a.approval_status == approval_status]
    if campaign:
        assets = [a for a in assets if a.metadata.campaign == campaign]

    # Sort by created_at descending
    assets.sort(key=lambda x: x.created_at, reverse=True)

    # Paginate
    total = len(assets)
    start = (page - 1) * page_size
    end = start + page_size
    page_assets = assets[start:end]

    return BrandAssetsListResponse(
        assets=page_assets,
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total,
    )


@router.get("/assets/{asset_id}", response_model=BrandAsset)
async def get_brand_asset(
    asset_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Get a specific brand asset by ID.

    Returns full asset details including extracted visual features.
    """
    asset = _brand_assets.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )
    return asset


@router.patch("/assets/{asset_id}/approve", response_model=BrandAsset)
async def approve_brand_asset(
    asset_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Approve a brand asset for training use.

    Only approved assets are included in training datasets.
    """
    asset = _brand_assets.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    asset.approval_status = AssetApprovalStatus.APPROVED
    return asset


@router.patch("/assets/{asset_id}/reject", response_model=BrandAsset)
async def reject_brand_asset(
    asset_id: str,
    reason: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Reject a brand asset from training use.

    Rejected assets are excluded from training datasets.
    """
    asset = _brand_assets.get(asset_id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    asset.approval_status = AssetApprovalStatus.REJECTED
    if reason:
        asset.metadata.notes = f"Rejected: {reason}"
    return asset


@router.delete("/assets/{asset_id}")
async def delete_brand_asset(
    asset_id: str,
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, bool]:
    """
    Delete a brand asset.

    This permanently removes the asset from the training library.
    """
    if asset_id not in _brand_assets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    del _brand_assets[asset_id]
    return {"deleted": True}


# =============================================================================
# Endpoints - Training Readiness
# =============================================================================


@router.get("/training-readiness", response_model=TrainingReadinessResponse)
async def check_training_readiness(
    minimum_assets: int = Query(500, ge=100, description="Minimum assets required"),
    current_user: TokenPayload = Depends(get_current_user),
) -> TrainingReadinessResponse:
    """
    Check if brand assets are ready for training.

    Assesses:
    - Total approved assets vs minimum requirement
    - Category distribution
    - Quality scores
    - Recommendations for improvement
    """
    assets = list(_brand_assets.values())
    approved = [a for a in assets if a.approval_status == AssetApprovalStatus.APPROVED]

    # Calculate category stats
    categories: dict[BrandAssetCategory, CategoryStats] = {}
    for cat in BrandAssetCategory:
        cat_assets = [a for a in assets if a.category == cat]
        cat_approved = [a for a in cat_assets if a.approval_status == AssetApprovalStatus.APPROVED]
        cat_pending = [a for a in cat_assets if a.approval_status == AssetApprovalStatus.PENDING]
        cat_rejected = [a for a in cat_assets if a.approval_status == AssetApprovalStatus.REJECTED]

        categories[cat] = CategoryStats(
            category=cat,
            total=len(cat_assets),
            approved=len(cat_approved),
            pending=len(cat_pending),
            rejected=len(cat_rejected),
        )

    # Determine status
    if len(approved) >= minimum_assets:
        status_val = TrainingReadinessStatus.READY
    elif len(approved) + sum(1 for a in assets if a.approval_status == AssetApprovalStatus.PENDING) >= minimum_assets:
        status_val = TrainingReadinessStatus.NEEDS_REVIEW
    else:
        status_val = TrainingReadinessStatus.NOT_READY

    # Generate recommendations
    recommendations = []

    if len(approved) < minimum_assets:
        needed = minimum_assets - len(approved)
        recommendations.append(f"Need {needed} more approved assets to reach minimum")

    pending_count = sum(1 for a in assets if a.approval_status == AssetApprovalStatus.PENDING)
    if pending_count > 0:
        recommendations.append(f"Review {pending_count} pending assets")

    # Check category balance
    for cat, stats in categories.items():
        if stats.approved < 50:
            recommendations.append(
                f"Add more {cat.value} assets (currently {stats.approved} approved)"
            )

    # Estimate training time
    estimated_time = None
    if status_val == TrainingReadinessStatus.READY:
        # Rough estimate: 10 minutes per 100 assets
        hours = (len(approved) / 100) * (10 / 60)
        estimated_time = f"{hours:.1f} hours"

    return TrainingReadinessResponse(
        status=status_val,
        total_assets=len(assets),
        approved_assets=len(approved),
        minimum_required=minimum_assets,
        categories=list(categories.values()),
        recommendations=recommendations,
        estimated_training_time=estimated_time,
    )


# =============================================================================
# Endpoints - Statistics
# =============================================================================


@router.get("/stats", response_model=dict[str, Any])
async def get_brand_assets_stats(
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get brand assets statistics.

    Returns counts by category, approval status, and quality metrics.
    """
    assets = list(_brand_assets.values())

    # Count by category
    by_category = {}
    for cat in BrandAssetCategory:
        by_category[cat.value] = sum(1 for a in assets if a.category == cat)

    # Count by approval status
    by_status = {}
    for stat in AssetApprovalStatus:
        by_status[stat.value] = sum(1 for a in assets if a.approval_status == stat)

    # Quality metrics
    quality_scores = [
        a.visual_features.quality_score
        for a in assets
        if a.visual_features and a.visual_features.quality_score
    ]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    return {
        "total": len(assets),
        "by_category": by_category,
        "by_approval_status": by_status,
        "average_quality_score": round(avg_quality, 2),
        "campaigns": list(set(a.metadata.campaign for a in assets if a.metadata.campaign)),
    }
