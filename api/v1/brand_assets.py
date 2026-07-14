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

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from services.ml.visual_feature_extractor import (
    VisualFeatureExtractor,
    get_visual_feature_extractor,
)
from services.storage.r2_client import R2Client, R2Config, R2Error
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import db_manager, get_db
from database.models_brand_assets import BrandAssetRecord, IngestionJobRecord
from security.jwt_oauth2_auth import TokenPayload, get_current_user
from security.ssrf_protection import SSRFProtection

logger = logging.getLogger(__name__)

# Feature extractor instance
_feature_extractor: VisualFeatureExtractor | None = None

# R2 client instance (lazy init to avoid startup errors)
_r2_client: R2Client | None = None


def _get_r2_client() -> R2Client | None:
    """Get or create R2 client if credentials are configured."""
    global _r2_client
    if _r2_client is None:
        try:
            config = R2Config.from_env()
            config.validate()
            _r2_client = R2Client(config)
        except R2Error as e:
            logger.warning(f"R2 not configured, storage disabled: {e}")
            return None
    return _r2_client


router = APIRouter(prefix="/brand-assets", tags=["Brand Assets"])


# =============================================================================
# Enums
# =============================================================================


class BrandAssetCategory(StrEnum):
    """Category of brand asset."""

    PRODUCT = "product"
    LIFESTYLE = "lifestyle"
    CAMPAIGN = "campaign"
    MOOD_BOARD = "mood_board"
    TEXTURE = "texture"
    COLOR_REFERENCE = "color_reference"


class AssetApprovalStatus(StrEnum):
    """Approval status for brand assets."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class IngestionJobStatus(StrEnum):
    """Status of bulk ingestion job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class TrainingReadinessStatus(StrEnum):
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

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        # SSRF guard at the ingest boundary — block internal hosts / cloud
        # metadata before any fetch (upload_to_r2 + visual feature extraction).
        # Block-internal-only: brand assets legitimately come from many domains.
        if v.startswith(("http://", "https://")):
            SSRFProtection().validate_url(v)
        return v


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
# Persistence (SQLAlchemy — see database/models_brand_assets.py)
# =============================================================================


def _asset_to_row(asset: BrandAsset) -> BrandAssetRecord:
    """Serialize a BrandAsset into its persisted row."""
    return BrandAssetRecord(
        id=asset.id,
        url=asset.url,
        category=asset.category.value,
        approval_status=asset.approval_status.value,
        metadata_json=asset.metadata.model_dump_json(),
        visual_features_json=(
            asset.visual_features.model_dump_json() if asset.visual_features else None
        ),
        file_size_bytes=asset.file_size_bytes,
        width=asset.width,
        height=asset.height,
        mime_type=asset.mime_type,
        r2_key=asset.r2_key,
        created_at=asset.created_at,
        created_by=asset.created_by,
    )


def _row_to_asset(row: BrandAssetRecord) -> BrandAsset:
    """Deserialize a persisted row back into a BrandAsset."""
    return BrandAsset(
        id=row.id,
        url=row.url,
        category=row.category,
        approval_status=row.approval_status,
        metadata=BrandAssetMetadata.model_validate_json(row.metadata_json),
        visual_features=(
            VisualFeatures.model_validate_json(row.visual_features_json)
            if row.visual_features_json
            else None
        ),
        file_size_bytes=row.file_size_bytes,
        width=row.width,
        height=row.height,
        mime_type=row.mime_type,
        r2_key=row.r2_key,
        created_at=row.created_at,
        created_by=row.created_by,
    )


def _job_to_row(job: BulkIngestionJob) -> IngestionJobRecord:
    """Serialize a BulkIngestionJob into its persisted row."""
    return IngestionJobRecord(
        id=job.id,
        status=job.status.value,
        total=job.total,
        processed=job.processed,
        succeeded=job.succeeded,
        failed=job.failed,
        results_json=json.dumps([r.model_dump(mode="json") for r in job.results]),
        created_at=job.created_at,
        completed_at=job.completed_at,
        created_by=job.created_by,
    )


def _row_to_job(row: IngestionJobRecord) -> BulkIngestionJob:
    """Deserialize a persisted row back into a BulkIngestionJob."""
    return BulkIngestionJob(
        id=row.id,
        status=row.status,
        total=row.total,
        processed=row.processed,
        succeeded=row.succeeded,
        failed=row.failed,
        results=[IngestionJobResult(**r) for r in json.loads(row.results_json)],
        created_at=row.created_at,
        completed_at=row.completed_at,
        created_by=row.created_by,
    )


# =============================================================================
# Helper Functions
# =============================================================================


async def extract_visual_features(
    image_url: str,
    *,
    correlation_id: str | None = None,
) -> VisualFeatures:
    """Extract visual features from image using Gemini vision.

    Uses the VisualFeatureExtractor service to analyze images
    and extract color palettes, composition, lighting, and style.

    Args:
        image_url: URL of image to analyze
        correlation_id: Optional correlation ID

    Returns:
        VisualFeatures with extracted data
    """
    global _feature_extractor

    try:
        # Get or create extractor
        if _feature_extractor is None:
            _feature_extractor = await get_visual_feature_extractor()

        # Extract features using Gemini
        extracted = await _feature_extractor.extract(
            image_url,
            correlation_id=correlation_id,
        )

        # Map to API response models
        return VisualFeatures(
            color_palette=ColorPalette(
                primary=extracted.color_palette.primary if extracted.color_palette else "#1A1A1A",
                secondary=extracted.color_palette.secondary if extracted.color_palette else [],
                accent=extracted.color_palette.accent if extracted.color_palette else None,
            ),
            composition=CompositionAnalysis(
                type=extracted.composition.type if extracted.composition else "centered",
                focal_point=extracted.composition.focal_point if extracted.composition else None,
                balance=extracted.composition.balance if extracted.composition else "balanced",
            ),
            lighting=LightingProfile(
                type=extracted.lighting.type if extracted.lighting else "studio",
                direction=extracted.lighting.direction if extracted.lighting else None,
                mood=extracted.lighting.mood if extracted.lighting else None,
            ),
            style_tags=extracted.style_tags,
            quality_score=extracted.quality_score,
        )

    except Exception as e:
        logger.warning(
            f"Feature extraction failed, using defaults: {e}",
            extra={"image_url": image_url, "correlation_id": correlation_id},
        )
        # Fallback to SkyyRose brand defaults
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
            quality_score=0.0,
        )


async def upload_to_r2(
    image_url: str,
    asset_id: str,
    category: BrandAssetCategory,
    *,
    correlation_id: str | None = None,
) -> tuple[str | None, int, int | None, int | None, str | None]:
    """Download image from URL and upload to R2.

    Args:
        image_url: Source image URL
        asset_id: Asset ID for storage key
        category: Asset category
        correlation_id: Optional correlation ID

    Returns:
        Tuple of (r2_key, file_size, width, height, mime_type)
        Returns (None, 0, None, None, None) if R2 not configured
    """
    import io

    import httpx
    from PIL import Image

    r2_client = _get_r2_client()
    if r2_client is None:
        logger.debug("R2 not configured, skipping upload")
        return None, 0, None, None, None

    try:
        # Download image
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(image_url)
            response.raise_for_status()
            image_data = response.content
            content_type = response.headers.get("content-type", "image/jpeg")

        # Get image dimensions
        width, height = None, None
        try:
            img = Image.open(io.BytesIO(image_data))
            width, height = img.size
        except Exception as e:
            logger.warning(f"Could not read image dimensions: {e}")

        # Generate key and upload
        from pathlib import Path
        from urllib.parse import urlparse

        # Allowlist the extension derived from the (attacker-influenced) URL so
        # it can't inject path-like segments into the R2 object key.
        ext = Path(urlparse(image_url).path).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif"):
            ext = ".jpg"
        key = f"brand/{category.value}/{asset_id}{ext}"

        result = r2_client.upload_bytes(
            image_data,
            key,
            content_type=content_type,
            metadata={
                "asset-id": asset_id,
                "category": category.value,
                "source-url": image_url[:200],  # Truncate long URLs
            },
            correlation_id=correlation_id,
        )

        logger.info(
            f"Uploaded brand asset to R2: {key}",
            extra={
                "asset_id": asset_id,
                "size": len(image_data),
                "correlation_id": correlation_id,
            },
        )

        return result.key, len(image_data), width, height, content_type

    except Exception as e:
        logger.error(
            f"Failed to upload to R2: {e}",
            extra={"image_url": image_url, "correlation_id": correlation_id},
        )
        return None, 0, None, None, None


async def process_bulk_ingestion(
    job_id: str,
    request: BulkIngestionRequest,
    user_id: str,
) -> None:
    """Process bulk ingestion in background.

    Runs as a FastAPI BackgroundTask, which cannot use Depends(get_db) —
    it opens its own session and commits incrementally so job progress is
    visible to concurrent GET /ingest/{job_id} requests as it runs.

    Args:
        job_id: Job identifier
        request: Ingestion request
        user_id: User who initiated the job
    """
    async with db_manager.session() as db:
        job_row = await db.get(IngestionJobRecord, job_id)
        if not job_row:
            return

        job_row.status = IngestionJobStatus.PROCESSING.value
        await db.commit()

        for asset_upload in request.assets:
            results = json.loads(job_row.results_json)
            try:
                # Generate asset ID first (needed for R2 key)
                asset_id = str(uuid4())

                # Upload to R2 storage
                r2_key, file_size, width, height, mime_type = await upload_to_r2(
                    asset_upload.url,
                    asset_id,
                    asset_upload.category,
                    correlation_id=job_id,
                )

                # Extract features if requested
                features = None
                if request.extract_features:
                    features = await extract_visual_features(
                        asset_upload.url,
                        correlation_id=job_id,
                    )

                # Create asset with all extracted data
                asset = BrandAsset(
                    id=asset_id,
                    url=asset_upload.url,
                    category=asset_upload.category,
                    approval_status=(
                        AssetApprovalStatus.APPROVED
                        if request.auto_approve
                        else AssetApprovalStatus.PENDING
                    ),
                    metadata=asset_upload.metadata,
                    visual_features=features,
                    file_size_bytes=file_size,
                    width=width,
                    height=height,
                    mime_type=mime_type,
                    r2_key=r2_key,
                    created_by=user_id,
                )

                # Apply campaign name if provided
                if request.campaign_name:
                    asset.metadata.campaign = request.campaign_name

                db.add(_asset_to_row(asset))

                results.append(
                    IngestionJobResult(
                        url=asset_upload.url,
                        success=True,
                        asset_id=asset.id,
                    ).model_dump(mode="json")
                )
                job_row.succeeded += 1

            except Exception as e:
                logger.error(
                    f"Failed to ingest {asset_upload.url}: {e}",
                    extra={"job_id": job_id},
                )
                results.append(
                    IngestionJobResult(
                        url=asset_upload.url,
                        success=False,
                        error=str(e),
                    ).model_dump(mode="json")
                )
                job_row.failed += 1

            job_row.results_json = json.dumps(results)
            job_row.processed += 1
            await db.commit()

        # Finalize job
        job_row.completed_at = datetime.now(UTC)
        if job_row.failed == 0:
            job_row.status = IngestionJobStatus.COMPLETED.value
        elif job_row.succeeded == 0:
            job_row.status = IngestionJobStatus.FAILED.value
        else:
            job_row.status = IngestionJobStatus.PARTIAL.value
        await db.commit()

        logger.info(
            f"Bulk ingestion job {job_id} completed: {job_row.succeeded}/{job_row.total} succeeded",
        )


# =============================================================================
# Endpoints - Ingestion
# =============================================================================


@router.post("/ingest/bulk", response_model=BulkIngestionJob)
async def bulk_ingest_brand_assets(
    request: BulkIngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
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
    db.add(_job_to_row(job))
    await db.flush()

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
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> BulkIngestionJob:
    """
    Get bulk ingestion job status and progress.

    Returns current progress and results of individual asset ingestions.
    """
    row = await db.get(IngestionJobRecord, job_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job not found: {job_id}",
        )
    return _row_to_job(row)


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
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAssetsListResponse:
    """
    List brand assets with filtering.

    Filter by:
    - **category**: product, lifestyle, campaign, mood_board, texture, color_reference
    - **approval_status**: pending, approved, rejected
    - **campaign**: Campaign name
    """
    result = await db.execute(select(BrandAssetRecord))
    assets = [_row_to_asset(row) for row in result.scalars().all()]

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
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Get a specific brand asset by ID.

    Returns full asset details including extracted visual features.
    """
    row = await db.get(BrandAssetRecord, asset_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )
    return _row_to_asset(row)


@router.patch("/assets/{asset_id}/approve", response_model=BrandAsset)
async def approve_brand_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Approve a brand asset for training use.

    Only approved assets are included in training datasets.
    """
    row = await db.get(BrandAssetRecord, asset_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    row.approval_status = AssetApprovalStatus.APPROVED.value
    await db.flush()
    return _row_to_asset(row)


@router.patch("/assets/{asset_id}/reject", response_model=BrandAsset)
async def reject_brand_asset(
    asset_id: str,
    reason: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> BrandAsset:
    """
    Reject a brand asset from training use.

    Rejected assets are excluded from training datasets.
    """
    row = await db.get(BrandAssetRecord, asset_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    row.approval_status = AssetApprovalStatus.REJECTED.value
    if reason:
        metadata = BrandAssetMetadata.model_validate_json(row.metadata_json)
        metadata.notes = f"Rejected: {reason}"
        row.metadata_json = metadata.model_dump_json()
    await db.flush()
    return _row_to_asset(row)


@router.delete("/assets/{asset_id}")
async def delete_brand_asset(
    asset_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, bool]:
    """
    Delete a brand asset.

    This permanently removes the asset from the training library.
    """
    row = await db.get(BrandAssetRecord, asset_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand asset not found: {asset_id}",
        )

    await db.delete(row)
    return {"deleted": True}


# =============================================================================
# Endpoints - Training Readiness
# =============================================================================


@router.get("/training-readiness", response_model=TrainingReadinessResponse)
async def check_training_readiness(
    minimum_assets: int = Query(500, ge=100, description="Minimum assets required"),
    db: AsyncSession = Depends(get_db),
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
    result = await db.execute(select(BrandAssetRecord))
    assets = [_row_to_asset(row) for row in result.scalars().all()]
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
    elif (
        len(approved) + sum(1 for a in assets if a.approval_status == AssetApprovalStatus.PENDING)
        >= minimum_assets
    ):
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
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get brand assets statistics.

    Returns counts by category, approval status, and quality metrics.
    """
    result = await db.execute(select(BrandAssetRecord))
    assets = [_row_to_asset(row) for row in result.scalars().all()]

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
        "campaigns": list({a.metadata.campaign for a in assets if a.metadata.campaign}),
    }
