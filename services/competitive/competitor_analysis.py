# services/competitive/competitor_analysis.py
"""Competitor analysis service for brand intelligence.

Implements US-034: Competitor image upload and tagging.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
from collections import Counter
from typing import Any

from services.competitive.schemas import (
    Competitor,
    CompetitorAsset,
    CompetitorAssetCreate,
    CompetitorAssetFilter,
    CompetitorAssetListResponse,
    CompetitorAssetUpdate,
    CompetitorCreate,
    CompetitorListResponse,
    CompositionDistribution,
    CompositionType,
    ExtractedAttributes,
    PriceAnalytics,
    StyleAnalyticsResponse,
    StyleCategory,
    StyleDistribution,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models_competitors import CompetitorAssetRecord, CompetitorRecord

logger = logging.getLogger(__name__)


# =============================================================================
# Competitor Analysis Service
# =============================================================================


class CompetitorAnalysisService:
    """Service for managing competitor assets and analysis.

    Persistence is SQLAlchemy-backed (database/models_competitors.py) —
    each request gets its own AsyncSession via Depends(get_db), threaded
    in through api/v1/competitors.py's get_analysis_service().
    """

    # RBAC: Allowed roles for competitor management
    ALLOWED_ROLES = {"admin", "strategy", "marketing"}

    def __init__(self, session: AsyncSession) -> None:
        """Initialize service.

        Args:
            session: Request-scoped async DB session
        """
        self._session = session
        self._vision_client: Any = None

    def check_access(self, user_roles: list[str]) -> bool:
        """Check if user has access to competitor features.

        Args:
            user_roles: List of user's roles

        Returns:
            True if user has access
        """
        return bool(set(user_roles) & self.ALLOWED_ROLES)

    # =========================================================================
    # Persistence helpers
    # =========================================================================

    @staticmethod
    def _competitor_to_row(competitor: Competitor) -> CompetitorRecord:
        return CompetitorRecord(
            id=competitor.id,
            name=competitor.name,
            category=competitor.category.value,
            price_positioning=competitor.price_positioning.value,
            website=str(competitor.website) if competitor.website else None,
            notes=competitor.notes,
            created_at=competitor.created_at,
            created_by=competitor.created_by,
        )

    @staticmethod
    def _row_to_competitor(row: CompetitorRecord) -> Competitor:
        return Competitor(
            id=row.id,
            name=row.name,
            category=row.category,
            price_positioning=row.price_positioning,
            website=row.website,
            notes=row.notes,
            created_at=row.created_at,
            created_by=row.created_by,
        )

    @staticmethod
    def _asset_to_row(asset: CompetitorAsset) -> CompetitorAssetRecord:
        return CompetitorAssetRecord(
            id=asset.id,
            competitor_id=asset.competitor_id,
            url=asset.url,
            product_type=asset.product_type,
            product_name=asset.product_name,
            estimated_price=asset.estimated_price,
            currency=asset.currency,
            extracted_attributes_json=(
                asset.extracted_attributes.model_dump_json() if asset.extracted_attributes else None
            ),
            manual_tags_json=json.dumps(asset.manual_tags),
            notes=asset.notes,
            created_at=asset.created_at,
            created_by=asset.created_by,
            source_url=str(asset.source_url) if asset.source_url else None,
        )

    @staticmethod
    def _row_to_asset(row: CompetitorAssetRecord) -> CompetitorAsset:
        return CompetitorAsset(
            id=row.id,
            competitor_id=row.competitor_id,
            url=row.url,
            product_type=row.product_type,
            product_name=row.product_name,
            estimated_price=row.estimated_price,
            currency=row.currency,
            extracted_attributes=(
                ExtractedAttributes.model_validate_json(row.extracted_attributes_json)
                if row.extracted_attributes_json
                else None
            ),
            manual_tags=json.loads(row.manual_tags_json),
            notes=row.notes,
            created_at=row.created_at,
            created_by=row.created_by,
            source_url=row.source_url,
        )

    async def list_all_competitors(self) -> list[Competitor]:
        result = await self._session.execute(select(CompetitorRecord))
        return [self._row_to_competitor(row) for row in result.scalars().all()]

    async def list_all_assets(self) -> list[CompetitorAsset]:
        result = await self._session.execute(select(CompetitorAssetRecord))
        return [self._row_to_asset(row) for row in result.scalars().all()]

    # =========================================================================
    # Competitor CRUD
    # =========================================================================

    async def create_competitor(
        self,
        request: CompetitorCreate,
        *,
        created_by: str,
    ) -> Competitor:
        """Create a new competitor.

        Args:
            request: Competitor creation request
            created_by: User ID

        Returns:
            Created competitor
        """
        competitor = Competitor(
            name=request.name,
            category=request.category,
            price_positioning=request.price_positioning,
            website=request.website,
            notes=request.notes,
            created_by=created_by,
        )

        self._session.add(self._competitor_to_row(competitor))
        await self._session.flush()

        logger.info(f"Created competitor: {competitor.name} (ID: {competitor.id})")
        return competitor

    async def get_competitor(self, competitor_id: str) -> Competitor | None:
        """Get competitor by ID.

        Args:
            competitor_id: Competitor ID

        Returns:
            Competitor or None if not found
        """
        row = await self._session.get(CompetitorRecord, competitor_id)
        return self._row_to_competitor(row) if row else None

    async def list_competitors(self) -> CompetitorListResponse:
        """List all competitors.

        Returns:
            List of competitors
        """
        competitors = await self.list_all_competitors()
        return CompetitorListResponse(
            total=len(competitors),
            competitors=competitors,
        )

    async def delete_competitor(self, competitor_id: str) -> bool:
        """Delete a competitor and all associated assets.

        Args:
            competitor_id: Competitor ID

        Returns:
            True if deleted
        """
        row = await self._session.get(CompetitorRecord, competitor_id)
        if not row:
            return False

        # Delete associated assets
        asset_result = await self._session.execute(
            select(CompetitorAssetRecord).where(
                CompetitorAssetRecord.competitor_id == competitor_id
            )
        )
        asset_rows = asset_result.scalars().all()
        for asset_row in asset_rows:
            await self._session.delete(asset_row)

        await self._session.delete(row)

        logger.info(f"Deleted competitor {competitor_id} and {len(asset_rows)} assets")
        return True

    # =========================================================================
    # Competitor Asset CRUD
    # =========================================================================

    async def upload_asset(
        self,
        request: CompetitorAssetCreate,
        *,
        created_by: str,
        extract_features: bool = True,
    ) -> CompetitorAsset:
        """Upload and analyze a competitor asset.

        Args:
            request: Asset creation request
            created_by: User ID
            extract_features: Whether to auto-extract features

        Returns:
            Created asset
        """
        # Verify competitor exists
        competitor_row = await self._session.get(CompetitorRecord, request.competitor_id)
        if not competitor_row:
            raise ValueError(f"Competitor not found: {request.competitor_id}")

        # Create asset
        asset = CompetitorAsset(
            competitor_id=request.competitor_id,
            url=str(request.url),
            product_type=request.product_type,
            product_name=request.product_name,
            estimated_price=request.estimated_price,
            currency=request.currency,
            manual_tags=request.manual_tags,
            notes=request.notes,
            source_url=request.source_url,
            created_by=created_by,
        )

        # Auto-extract features
        if extract_features:
            asset.extracted_attributes = await self._extract_attributes(str(request.url))

        self._session.add(self._asset_to_row(asset))
        await self._session.flush()

        logger.info(f"Uploaded competitor asset: {asset.id} (competitor: {request.competitor_id})")
        return asset

    async def get_asset(self, asset_id: str) -> CompetitorAsset | None:
        """Get competitor asset by ID.

        Args:
            asset_id: Asset ID

        Returns:
            Asset or None if not found
        """
        row = await self._session.get(CompetitorAssetRecord, asset_id)
        return self._row_to_asset(row) if row else None

    async def list_assets(
        self,
        *,
        filter_params: CompetitorAssetFilter | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CompetitorAssetListResponse:
        """List competitor assets with filtering.

        Args:
            filter_params: Optional filter parameters
            page: Page number
            page_size: Items per page

        Returns:
            Paginated list of assets
        """
        assets = await self.list_all_assets()

        # Apply filters
        if filter_params:
            if filter_params.competitor_id:
                assets = [a for a in assets if a.competitor_id == filter_params.competitor_id]

            if filter_params.competitor_category:
                competitors = await self.list_all_competitors()
                competitor_ids = {
                    c.id for c in competitors if c.category == filter_params.competitor_category
                }
                assets = [a for a in assets if a.competitor_id in competitor_ids]

            if filter_params.price_positioning:
                competitors = await self.list_all_competitors()
                competitor_ids = {
                    c.id
                    for c in competitors
                    if c.price_positioning == filter_params.price_positioning
                }
                assets = [a for a in assets if a.competitor_id in competitor_ids]

            if filter_params.composition_type:
                assets = [
                    a
                    for a in assets
                    if a.extracted_attributes
                    and a.extracted_attributes.composition_type == filter_params.composition_type
                ]

            if filter_params.style_category:
                assets = [
                    a
                    for a in assets
                    if a.extracted_attributes
                    and a.extracted_attributes.style_category == filter_params.style_category
                ]

            if filter_params.tags:
                assets = [
                    a for a in assets if any(tag in a.manual_tags for tag in filter_params.tags)
                ]

        total = len(assets)

        # Paginate
        start = (page - 1) * page_size
        end = start + page_size
        assets = assets[start:end]

        return CompetitorAssetListResponse(
            total=total,
            page=page,
            page_size=page_size,
            assets=assets,
        )

    async def update_asset(
        self,
        asset_id: str,
        request: CompetitorAssetUpdate,
    ) -> CompetitorAsset | None:
        """Update a competitor asset.

        Args:
            asset_id: Asset ID
            request: Update request

        Returns:
            Updated asset or None if not found
        """
        row = await self._session.get(CompetitorAssetRecord, asset_id)
        if not row:
            return None

        # Update fields
        if request.product_type is not None:
            row.product_type = request.product_type
        if request.product_name is not None:
            row.product_name = request.product_name
        if request.estimated_price is not None:
            row.estimated_price = request.estimated_price
        if request.currency is not None:
            row.currency = request.currency
        if request.manual_tags is not None:
            row.manual_tags_json = json.dumps(request.manual_tags)
        if request.notes is not None:
            row.notes = request.notes

        await self._session.flush()

        logger.info(f"Updated competitor asset: {asset_id}")
        return self._row_to_asset(row)

    async def delete_asset(self, asset_id: str) -> bool:
        """Delete a competitor asset.

        Args:
            asset_id: Asset ID

        Returns:
            True if deleted
        """
        row = await self._session.get(CompetitorAssetRecord, asset_id)
        if row:
            await self._session.delete(row)
            logger.info(f"Deleted competitor asset: {asset_id}")
            return True
        return False

    # =========================================================================
    # Analytics
    # =========================================================================

    async def get_style_analytics(
        self,
        *,
        competitor_id: str | None = None,
    ) -> StyleAnalyticsResponse:
        """Get style distribution analytics.

        Args:
            competitor_id: Optional filter by competitor

        Returns:
            Style analytics
        """
        assets = await self.list_all_assets()

        if competitor_id:
            assets = [a for a in assets if a.competitor_id == competitor_id]

        total = len(assets)
        if total == 0:
            return StyleAnalyticsResponse()

        # Style distribution
        style_counts: Counter[StyleCategory] = Counter()
        composition_counts: Counter[CompositionType] = Counter()
        all_colors: list[str] = []
        all_materials: list[str] = []

        for asset in assets:
            if asset.extracted_attributes:
                style_counts[asset.extracted_attributes.style_category] += 1
                composition_counts[asset.extracted_attributes.composition_type] += 1
                all_colors.extend(asset.extracted_attributes.primary_colors)
                all_materials.extend(asset.extracted_attributes.detected_materials)

        style_distribution = [
            StyleDistribution(
                style=style,
                count=count,
                percentage=round(count / total * 100, 1),
            )
            for style, count in style_counts.most_common()
        ]

        composition_distribution = [
            CompositionDistribution(
                composition=comp,
                count=count,
                percentage=round(count / total * 100, 1),
            )
            for comp, count in composition_counts.most_common()
        ]

        # Top colors and materials
        color_counts = Counter(all_colors)
        top_colors = [
            {"color": color, "count": count} for color, count in color_counts.most_common(10)
        ]

        material_counts = Counter(all_materials)
        top_materials = [
            {"material": mat, "count": count} for mat, count in material_counts.most_common(10)
        ]

        # Price analytics by competitor
        price_by_competitor: list[PriceAnalytics] = []
        competitors = await self.list_all_competitors()
        for comp in competitors:
            comp_assets = [a for a in assets if a.competitor_id == comp.id]
            prices = [a.estimated_price for a in comp_assets if a.estimated_price]

            if prices:
                price_by_competitor.append(
                    PriceAnalytics(
                        competitor_id=comp.id,
                        competitor_name=comp.name,
                        average_price=round(sum(prices) / len(prices), 2),
                        min_price=min(prices),
                        max_price=max(prices),
                        asset_count=len(comp_assets),
                    )
                )

        return StyleAnalyticsResponse(
            total_assets=total,
            style_distribution=style_distribution,
            composition_distribution=composition_distribution,
            top_colors=top_colors,
            top_materials=top_materials,
            price_by_competitor=price_by_competitor,
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    async def _extract_attributes(self, image_url: str) -> ExtractedAttributes:
        """Extract attributes from competitor image.

        Args:
            image_url: Image URL

        Returns:
            Extracted attributes
        """
        # In production, this would call a vision model
        # For now, return default attributes
        return ExtractedAttributes(
            composition_type=CompositionType.OTHER,
            style_category=StyleCategory.OTHER,
            primary_colors=[],
            detected_materials=[],
            mood_tags=[],
            quality_assessment=None,
            confidence_score=0.0,
        )
