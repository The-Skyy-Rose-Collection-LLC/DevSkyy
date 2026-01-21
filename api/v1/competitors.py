# api/v1/competitors.py
"""API endpoints for competitor analysis.

Implements US-034: Competitor image upload and tagging.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from security.jwt_oauth2_auth import TokenPayload, get_current_user
from services.competitive.competitor_analysis import (
    CompetitorAnalysisService,
    _competitor_assets,
    _competitors,
)
from services.competitive.schemas import (
    CompositionType,
    Competitor,
    CompetitorAsset,
    CompetitorAssetCreate,
    CompetitorAssetFilter,
    CompetitorAssetListResponse,
    CompetitorAssetUpdate,
    CompetitorCategory,
    CompetitorCreate,
    CompetitorListResponse,
    PricePositioning,
    StyleAnalyticsResponse,
    StyleCategory,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/competitors", tags=["competitors"])


# =============================================================================
# Dependency Injection
# =============================================================================


def get_analysis_service() -> CompetitorAnalysisService:
    """Get competitor analysis service."""
    return CompetitorAnalysisService()


def check_competitor_access(
    current_user: TokenPayload = Depends(get_current_user),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> TokenPayload:
    """Check user has access to competitor features.

    Restricted to strategy and marketing roles.
    """
    if not service.check_access(current_user.roles):
        raise HTTPException(
            status_code=403,
            detail="Access denied. Competitor analysis restricted to strategy/marketing roles.",
        )
    return current_user


# =============================================================================
# Analytics Endpoints (MUST be before dynamic routes)
# =============================================================================


@router.get("/analytics/style-distribution", response_model=StyleAnalyticsResponse)
async def get_style_analytics(
    competitor_id: str | None = Query(None, description="Filter by competitor"),
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> StyleAnalyticsResponse:
    """Get style distribution analytics across competitor assets.

    Returns:
    - Style category distribution
    - Composition type distribution
    - Top colors used
    - Top materials detected
    - Price analytics by competitor

    Restricted to strategy/marketing roles.
    """
    return await service.get_style_analytics(competitor_id=competitor_id)


@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> dict[str, Any]:
    """Get high-level analytics summary.

    Restricted to strategy/marketing roles.
    """
    competitors = list(_competitors.values())
    assets = list(_competitor_assets.values())

    # Count by category
    by_category = {}
    for cat in CompetitorCategory:
        count = len([c for c in competitors if c.category == cat])
        if count > 0:
            by_category[cat.value] = count

    # Count by price positioning
    by_price = {}
    for pos in PricePositioning:
        count = len([c for c in competitors if c.price_positioning == pos])
        if count > 0:
            by_price[pos.value] = count

    # Assets per competitor
    assets_per_competitor = {}
    for comp in competitors:
        comp_assets = [a for a in assets if a.competitor_id == comp.id]
        assets_per_competitor[comp.name] = len(comp_assets)

    return {
        "total_competitors": len(competitors),
        "total_assets": len(assets),
        "competitors_by_category": by_category,
        "competitors_by_price_positioning": by_price,
        "assets_per_competitor": assets_per_competitor,
    }


# =============================================================================
# Competitor Asset Endpoints (MUST be before /{competitor_id})
# =============================================================================


@router.post("/assets", response_model=CompetitorAsset)
async def upload_competitor_asset(
    request: CompetitorAssetCreate,
    extract_features: bool = Query(True, description="Auto-extract visual features"),
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> CompetitorAsset:
    """Upload a competitor product image for analysis.

    This endpoint is for manual uploads only. Competitor images are stored
    separately from brand assets and are never processed through our
    generation pipeline.

    Restricted to strategy/marketing roles.
    """
    try:
        return await service.upload_asset(
            request,
            created_by=current_user.sub,
            extract_features=extract_features,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to upload competitor asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assets", response_model=CompetitorAssetListResponse)
async def list_competitor_assets(
    competitor_id: str | None = Query(None),
    competitor_category: CompetitorCategory | None = Query(None),
    price_positioning: PricePositioning | None = Query(None),
    composition_type: CompositionType | None = Query(None),
    style_category: StyleCategory | None = Query(None),
    tags: str | None = Query(None, description="Comma-separated tags"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> CompetitorAssetListResponse:
    """List competitor assets with filtering.

    Restricted to strategy/marketing roles.
    """
    filter_params = CompetitorAssetFilter(
        competitor_id=competitor_id,
        competitor_category=competitor_category,
        price_positioning=price_positioning,
        composition_type=composition_type,
        style_category=style_category,
        tags=tags.split(",") if tags else None,
    )

    return await service.list_assets(
        filter_params=filter_params,
        page=page,
        page_size=page_size,
    )


@router.get("/assets/{asset_id}", response_model=CompetitorAsset)
async def get_competitor_asset(
    asset_id: str,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> CompetitorAsset:
    """Get competitor asset by ID.

    Restricted to strategy/marketing roles.
    """
    asset = await service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/assets/{asset_id}", response_model=CompetitorAsset)
async def update_competitor_asset(
    asset_id: str,
    request: CompetitorAssetUpdate,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> CompetitorAsset:
    """Update competitor asset metadata.

    Restricted to strategy/marketing roles.
    """
    asset = await service.update_asset(asset_id, request)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/assets/{asset_id}")
async def delete_competitor_asset(
    asset_id: str,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> dict[str, Any]:
    """Delete a competitor asset.

    Restricted to strategy/marketing roles.
    """
    deleted = await service.delete_asset(asset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"deleted": True, "asset_id": asset_id}


# =============================================================================
# Competitor CRUD Endpoints
# =============================================================================


@router.post("", response_model=Competitor)
async def create_competitor(
    request: CompetitorCreate,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> Competitor:
    """Create a new competitor brand.

    Restricted to strategy/marketing roles.
    """
    try:
        return await service.create_competitor(
            request,
            created_by=current_user.sub,
        )
    except Exception as e:
        logger.error(f"Failed to create competitor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=CompetitorListResponse)
async def list_competitors(
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> CompetitorListResponse:
    """List all competitors.

    Restricted to strategy/marketing roles.
    """
    return await service.list_competitors()


@router.get("/{competitor_id}", response_model=Competitor)
async def get_competitor(
    competitor_id: str,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> Competitor:
    """Get competitor by ID.

    Restricted to strategy/marketing roles.
    """
    competitor = await service.get_competitor(competitor_id)
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return competitor


@router.delete("/{competitor_id}")
async def delete_competitor(
    competitor_id: str,
    current_user: TokenPayload = Depends(check_competitor_access),
    service: CompetitorAnalysisService = Depends(get_analysis_service),
) -> dict[str, Any]:
    """Delete competitor and all associated assets.

    Restricted to strategy/marketing roles.
    """
    deleted = await service.delete_competitor(competitor_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Competitor not found")
    return {"deleted": True, "competitor_id": competitor_id}
