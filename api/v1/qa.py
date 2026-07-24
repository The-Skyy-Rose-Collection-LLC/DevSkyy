"""3D QA Review API.

Backs the admin `/admin/qa` review UI: human approve/reject/regenerate of
generated 3D models against their source reference photo, before an approved
row is picked up by scripts/promote_model3d_sot.py. Response shapes mirror
frontend/lib/api/schemas.ts's QAReviewSchema / QAReviewListResponseSchema
exactly — see that file before changing any field here.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from services.storage.r2_client import R2Client, R2Config, R2Error
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.models import Model3DGeneration, Model3DReview
from database.db import get_db
from security.jwt_oauth2_auth import RoleChecker, TokenPayload, UserRole
from skyyrose.core.sot_images import resolve_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["3D QA Review"])

# Role-based access control — mirrors api/v1/pipeline.py's own instance
# (that file's copy is intentionally not shared; both define it locally,
# same as api/elementor_3d.py's independent instance).
require_developer = RoleChecker([UserRole.ADMIN, UserRole.DEVELOPER])

# R2 client instance (lazy init to avoid a hard startup failure when R2
# credentials aren't configured in this environment) — mirrors
# api/v1/brand_assets.py's _get_r2_client().
_r2_client: R2Client | None = None


def _get_r2_client() -> R2Client | None:
    """Get or create the R2 client if credentials are configured."""
    global _r2_client
    if _r2_client is None:
        try:
            config = R2Config.from_env()
            config.validate()
            _r2_client = R2Client(config)
        except R2Error as e:
            logger.warning(f"R2 not configured, presigned model URLs disabled: {e}")
            return None
    return _r2_client


# =============================================================================
# Models
# =============================================================================


class QAReviewStatus(StrEnum):
    """Review status — mirrors QAReviewSchema.status in frontend/lib/api/schemas.ts."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REGENERATING = "regenerating"


class FidelityBreakdown(BaseModel):
    """Per-dimension fidelity scores — mirrors QAReviewSchema.fidelity_breakdown."""

    geometry: float
    materials: float
    colors: float
    proportions: float
    branding: float
    texture_detail: float


class QAReview(BaseModel):
    """A single QA review — mirrors frontend/lib/api/schemas.ts QAReviewSchema."""

    id: str
    asset_id: str
    job_id: str
    reference_image_url: str
    generated_model_url: str
    fidelity_score: float = Field(ge=0.0, le=100.0)
    fidelity_breakdown: FidelityBreakdown | None = None
    status: QAReviewStatus
    notes: str | None = None
    reviewed_by: str | None = None
    created_at: str
    reviewed_at: str | None = None


class QAReviewListResponse(BaseModel):
    """Mirrors frontend/lib/api/schemas.ts QAReviewListResponseSchema."""

    reviews: list[QAReview]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int


class QAReviewPatchRequest(BaseModel):
    """Mirrors frontend/lib/api/schemas.ts QAReviewRequest."""

    status: Literal[QAReviewStatus.APPROVED, QAReviewStatus.REJECTED]
    notes: str | None = None


# =============================================================================
# Row -> response mapping
# =============================================================================


def _reference_image_url(sku: str) -> str | None:
    """SOT-resolved front-first product image URL for a SKU, or None if unresolvable.

    Fails hard (KeyError) if WP_SITE_URL is unset — no silent fallback to a
    broken/empty host per this project's fail-closed convention (bug-230).
    """
    image_path = resolve_image(sku, "front")
    if not image_path:
        return None
    site_url = os.environ["WP_SITE_URL"].rstrip("/")
    return f"{site_url}/wp-content/themes/skyyrose-flagship/{image_path}"


def _generated_model_url(model_r2_key: str | None) -> str | None:
    """Fresh presigned R2 URL for the generated GLB, or None if unavailable.

    Computed per call — presigned URLs expire, so this is never cached or
    stored (see D7 in the plan doc).
    """
    if not model_r2_key:
        return None
    client = _get_r2_client()
    if client is None:
        return None
    return client.generate_presigned_url(key=model_r2_key)


def _build_review(review: Model3DReview, generation: Model3DGeneration) -> QAReview | None:
    """Build the API response shape for one (review, generation) pair.

    Returns None when reference_image_url or generated_model_url can't be
    resolved — both are non-optional strings on the frontend schema, and
    serving an obviously-broken required field is worse than omitting the
    row (callers decide how to handle the omission per endpoint).
    """
    reference_image_url = _reference_image_url(generation.sku)
    if reference_image_url is None:
        logger.warning(f"QA review {review.id}: no SOT reference image for sku={generation.sku!r}")
        return None

    generated_model_url = _generated_model_url(generation.model_r2_key)
    if generated_model_url is None:
        logger.warning(
            f"QA review {review.id}: no generated_model_url "
            f"(model_r2_key={generation.model_r2_key!r})"
        )
        return None

    fidelity_breakdown = (
        FidelityBreakdown(**review.fidelity_breakdown) if review.fidelity_breakdown else None
    )

    # Surface reviewer identity + timestamp ONLY for an actual human review
    # DECISION (approve/reject). PENDING has never been touched, and
    # REGENERATING is a queued re-run — not a review — so a row in either state
    # must expose neither the stale prior reviewer nor a review timestamp
    # (attributing a queued regeneration to whoever last approved it is wrong).
    is_review_decision = review.status in {
        QAReviewStatus.APPROVED.value,
        QAReviewStatus.REJECTED.value,
    }
    reviewed_by = str(review.reviewed_by) if is_review_decision and review.reviewed_by else None
    reviewed_at = review.updated_at.isoformat() if is_review_decision else None

    return QAReview(
        id=str(review.id),
        asset_id=generation.sku,
        job_id=generation.task_id or "",
        reference_image_url=reference_image_url,
        generated_model_url=generated_model_url,
        fidelity_score=review.fidelity_score if review.fidelity_score is not None else 0.0,
        fidelity_breakdown=fidelity_breakdown,
        status=QAReviewStatus(review.status),
        notes=review.notes,
        reviewed_by=reviewed_by,
        created_at=review.created_at.isoformat(),
        reviewed_at=reviewed_at,
    )


def _require_built_review(review: Model3DReview, generation: Model3DGeneration) -> QAReview:
    """_build_review, raising 500 instead of silently returning a broken single row.

    Used by single-row endpoints (get/patch/regenerate) where there's no list
    to omit the row from — unlike the list endpoint, a directly-addressed
    review can't just disappear.
    """
    built = _build_review(review, generation)
    if built is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"QA review {review.id} is missing a resolvable reference image "
                "or generated model URL — check SOT imagery and R2 upload status"
            ),
        )
    return built


def _reviewer_uuid(sub: str) -> uuid.UUID:
    """Coerce the authenticated user's JWT subject into a UUID for reviewed_by.

    `sub` is NOT guaranteed to be UUID-shaped: security/jwt_oauth2_auth.py's
    dev-mode login fallback sets it to the raw username
    (jwt_oauth2_auth.py:1175), and create_token_pair() accepts any string.
    Fail with a clean 500 instead of letting a raw ValueError (with a stack
    trace) reach the client.
    """
    try:
        return uuid.UUID(sub)
    except ValueError as e:
        logger.error(f"Authenticated user id {sub!r} is not a valid UUID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authenticated user id is not in a valid format for reviewed_by",
        ) from e


def _review_generation_join_stmt():
    """Base SELECT joining Model3DReview to its parent Model3DGeneration."""
    return select(Model3DReview, Model3DGeneration).join(
        Model3DGeneration, Model3DReview.generation_id == Model3DGeneration.id
    )


async def _count_status(db: AsyncSession, review_status: QAReviewStatus) -> int:
    result = await db.execute(
        select(func.count())
        .select_from(Model3DReview)
        .where(Model3DReview.status == review_status.value)
    )
    return result.scalar() or 0


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/reviews",
    response_model=QAReviewListResponse,
    response_model_exclude_none=True,
    summary="List 3D QA reviews",
)
async def list_reviews(
    status_filter: QAReviewStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_developer),
) -> QAReviewListResponse:
    """List 3D QA reviews, optionally filtered by status.

    Rows missing a resolvable reference image or generated model URL are
    omitted from `reviews` (with a warning logged) but still counted in the
    per-status totals below.
    """
    stmt = _review_generation_join_stmt().order_by(Model3DReview.created_at.desc())
    if status_filter is not None:
        stmt = stmt.where(Model3DReview.status == status_filter.value)

    rows = (await db.execute(stmt)).all()
    reviews = [built for review, generation in rows if (built := _build_review(review, generation))]

    return QAReviewListResponse(
        reviews=reviews,
        total=len(reviews),
        pending_count=await _count_status(db, QAReviewStatus.PENDING),
        approved_count=await _count_status(db, QAReviewStatus.APPROVED),
        rejected_count=await _count_status(db, QAReviewStatus.REJECTED),
    )


@router.get(
    "/reviews/{review_id}",
    response_model=QAReview,
    response_model_exclude_none=True,
    summary="Get a single 3D QA review",
)
async def get_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_developer),
) -> QAReview:
    """Fetch a single 3D QA review by id (404 if absent, 500 if unrenderable)."""
    row = (
        await db.execute(_review_generation_join_stmt().where(Model3DReview.id == review_id))
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QA review not found: {review_id}",
        )
    review, generation = row
    return _require_built_review(review, generation)


@router.patch(
    "/reviews/{review_id}",
    response_model=QAReview,
    response_model_exclude_none=True,
    summary="Approve or reject a 3D QA review",
)
async def patch_review(
    review_id: uuid.UUID,
    body: QAReviewPatchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_developer),
) -> QAReview:
    """Approve or reject a review — sets status, notes, reviewer, and updated_at."""
    review = await db.get(Model3DReview, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QA review not found: {review_id}",
        )

    review.status = body.status.value
    if body.notes is not None:
        review.notes = body.notes
    review.reviewed_by = _reviewer_uuid(current_user.sub)
    # No onupdate= / DB trigger on this ORM column for non-Postgres targets —
    # set explicitly rather than relying on one.
    review.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(review)

    generation = await db.get(Model3DGeneration, review.generation_id)
    return _require_built_review(review, generation)


@router.post(
    "/reviews/{review_id}/regenerate",
    response_model=QAReview,
    response_model_exclude_none=True,
    summary="Queue a 3D QA review for regeneration",
)
async def regenerate_review(
    review_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(require_developer),
) -> QAReview:
    """Mark a review as queued for regeneration.

    This does NOT and must never autonomously trigger a paid Tripo3D
    dispatch — this project's CLAUDE.md has a hard, non-overridable
    STOP-AND-SHOW rule for any paid API call. An operator fulfills the
    actual regeneration manually via the existing gated CLI script
    (scripts/generate_3d_from_catalog.py). This handler only persists the
    'regenerating' state so the UI reflects the queued request.
    """
    review = await db.get(Model3DReview, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QA review not found: {review_id}",
        )

    review.status = QAReviewStatus.REGENERATING.value
    review.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(review)

    generation = await db.get(Model3DGeneration, review.generation_id)
    return _require_built_review(review, generation)
