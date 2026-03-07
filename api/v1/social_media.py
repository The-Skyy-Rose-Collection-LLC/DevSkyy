"""
Social Media Pipeline API Endpoints
====================================

Provides endpoints for the SkyyRose social media content pipeline:
- POST /generate   - Generate a post for a product/platform
- POST /campaign   - Generate a full multi-platform campaign
- GET  /queue      - Get the current post queue
- GET  /analytics  - Get platform analytics
- POST /schedule   - Schedule a post for publishing
- POST /publish    - Publish a post

Integrates with agents/social_media_agent.py SocialMediaAgent.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from security.jwt_oauth2_auth import TokenPayload, get_current_user

logger = logging.getLogger(__name__)

# =============================================================================
# Router
# =============================================================================

router = APIRouter(prefix="/social-media", tags=["Social Media"])


# =============================================================================
# Request Models
# =============================================================================


class GeneratePostRequest(BaseModel):
    """Request to generate a social media post."""

    product_sku: str = Field(
        ...,
        description="Product SKU from the catalog (e.g., 'br-001', 'lh-004', 'sg-003')",
        min_length=1,
        max_length=50,
    )
    platform: Literal["instagram", "tiktok", "twitter", "facebook"] = Field(
        ...,
        description="Target social media platform",
    )
    content_type: Literal[
        "product_launch", "collection_drop", "behind_scenes", "lifestyle", "engagement"
    ] = Field(
        default="product_launch",
        description="Content type determines tone and formatting",
    )

    @field_validator("product_sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        """Sanitize and validate SKU format."""
        cleaned = v.strip().lower()
        if not cleaned:
            raise ValueError("Product SKU cannot be empty")
        return cleaned


class GenerateCampaignRequest(BaseModel):
    """Request to generate a multi-platform campaign."""

    collection: Literal["black-rose", "love-hurts", "signature"] = Field(
        ...,
        description="Collection to generate campaign for",
    )
    campaign_name: str = Field(
        ...,
        description="Human-readable campaign name",
        min_length=1,
        max_length=200,
    )
    max_products: int = Field(
        default=5,
        description="Maximum number of products to include",
        ge=1,
        le=20,
    )
    platforms: list[Literal["instagram", "tiktok", "twitter", "facebook"]] | None = Field(
        default=None,
        description="Platforms to target (default: all 4)",
    )

    @field_validator("campaign_name")
    @classmethod
    def validate_campaign_name(cls, v: str) -> str:
        """Sanitize campaign name."""
        return v.strip()


class SchedulePostRequest(BaseModel):
    """Request to schedule a post."""

    post_id: str = Field(
        ...,
        description="Post identifier",
        min_length=1,
        max_length=64,
    )
    scheduled_at: str = Field(
        ...,
        description="ISO 8601 datetime for scheduled publishing",
    )

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: str) -> str:
        """Validate ISO 8601 datetime format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            raise ValueError("scheduled_at must be a valid ISO 8601 datetime string")
        return v


class PublishPostRequest(BaseModel):
    """Request to publish a post."""

    post_id: str = Field(
        ...,
        description="Post identifier",
        min_length=1,
        max_length=64,
    )


# =============================================================================
# Response Models
# =============================================================================


class SocialPostResponse(BaseModel):
    """Response model for a social media post."""

    id: str
    platform: str
    content_type: str
    caption: str
    hashtags: list[str]
    media_urls: list[str]
    product_sku: str
    collection: str
    scheduled_at: str | None = None
    published_at: str | None = None
    status: str
    engagement: dict[str, int] = Field(default_factory=dict)
    media_recommendations: dict[str, str] = Field(default_factory=dict)
    scheduling_recommendation: str | None = None
    created_at: str | None = None


class CampaignResponse(BaseModel):
    """Response model for a campaign."""

    id: str
    name: str
    collection: str
    posts: list[SocialPostResponse]
    created_at: str
    status: str


class PlatformAnalyticsResponse(BaseModel):
    """Analytics for a single platform."""

    posts: int = 0
    likes: int = 0
    comments: int | None = None
    shares: int = 0
    reach: int | None = None
    views: int | None = None
    retweets: int | None = None
    impressions: int | None = None


class AnalyticsResponse(BaseModel):
    """Response model for platform analytics."""

    platforms: dict[str, dict[str, int]]
    total_posts: int
    total_queue: int
    total_published: int


class QueueResponse(BaseModel):
    """Response model for the post queue."""

    posts: list[SocialPostResponse]
    count: int


class SuccessResponse(BaseModel):
    """Generic success response."""

    success: bool
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


# =============================================================================
# Agent Initialization
# =============================================================================


def _get_agent():
    """Lazy-load the social media agent singleton.

    Returns the agent instance. Uses lazy import to avoid circular
    dependencies and allow the agent module to initialize independently.
    """
    from agents.social_media_agent import social_media_agent

    return social_media_agent


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/generate",
    response_model=SocialPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a social media post",
    description=(
        "Generate a platform-optimized social media post for a SkyyRose product. "
        "Returns a draft post with brand-voice caption, collection-specific hashtags, "
        "media size recommendations, and optimal scheduling time."
    ),
)
async def generate_post(
    request: GeneratePostRequest,
    user: TokenPayload = Depends(get_current_user),
) -> SocialPostResponse:
    """Generate a social media post for a product on a specific platform.

    The Social Media Agent generates content with:
    - Platform-specific formatting (character limits, hashtag counts)
    - SkyyRose brand voice enforcement
    - Collection-appropriate tone and aesthetics
    - Media size recommendations per platform
    - Optimal posting time suggestions

    Args:
        request: Post generation parameters (SKU, platform, content type)
        user: Authenticated user from JWT token

    Returns:
        SocialPostResponse with generated post data

    Raises:
        HTTPException 404: Product SKU not found
        HTTPException 422: Invalid platform or content type
        HTTPException 500: Internal generation error
    """
    logger.info(
        "Generating social post: sku=%s, platform=%s, type=%s, user=%s",
        request.product_sku,
        request.platform,
        request.content_type,
        user.sub,
    )

    try:
        agent = _get_agent()
        post = agent.generate_post(
            product_sku=request.product_sku,
            platform=request.platform,
            content_type=request.content_type,
            correlation_id=f"api-{user.sub}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        )

        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Could not generate post. Product SKU '{request.product_sku}' "
                    f"not found or platform '{request.platform}' unsupported."
                ),
            )

        return SocialPostResponse(**post.to_dict())

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Post generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.post(
    "/campaign",
    response_model=CampaignResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a multi-platform campaign",
    description=(
        "Generate a full campaign across multiple platforms for an entire collection. "
        "Creates posts for each product in the collection on each specified platform."
    ),
)
async def generate_campaign(
    request: GenerateCampaignRequest,
    user: TokenPayload = Depends(get_current_user),
) -> CampaignResponse:
    """Generate a multi-platform campaign for a SkyyRose collection.

    Creates posts for up to `max_products` from the collection across
    all specified platforms. Each post gets platform-specific formatting,
    collection-appropriate hashtags, and scheduling recommendations.

    Args:
        request: Campaign generation parameters
        user: Authenticated user from JWT token

    Returns:
        CampaignResponse with all generated posts

    Raises:
        HTTPException 500: Internal generation error
    """
    logger.info(
        "Generating campaign: collection=%s, name=%s, user=%s",
        request.collection,
        request.campaign_name,
        user.sub,
    )

    try:
        agent = _get_agent()
        campaign = agent.generate_campaign(
            collection=request.collection,
            campaign_name=request.campaign_name,
            max_products=request.max_products,
            platforms=request.platforms,
            correlation_id=f"api-campaign-{user.sub}-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        )

        return CampaignResponse(**campaign.to_dict())

    except Exception as exc:
        logger.error("Campaign generation failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.get(
    "/queue",
    response_model=QueueResponse,
    summary="Get the post queue",
    description="Retrieve all posts currently in the draft/scheduled queue.",
)
async def get_queue(
    user: TokenPayload = Depends(get_current_user),
) -> QueueResponse:
    """Get all posts in the social media queue.

    Returns draft and scheduled posts awaiting publication.

    Args:
        user: Authenticated user from JWT token

    Returns:
        QueueResponse with list of posts and count
    """
    try:
        agent = _get_agent()
        queue_data = agent.get_queue()
        posts = [SocialPostResponse(**p) for p in queue_data]
        return QueueResponse(posts=posts, count=len(posts))

    except Exception as exc:
        logger.error("Queue retrieval failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.get(
    "/analytics",
    response_model=AnalyticsResponse,
    summary="Get platform analytics",
    description=(
        "Retrieve engagement analytics across Instagram, TikTok, X/Twitter, "
        "and Facebook including post counts, engagement metrics, and reach."
    ),
)
async def get_analytics(
    user: TokenPayload = Depends(get_current_user),
) -> AnalyticsResponse:
    """Get social media analytics across all platforms.

    Returns aggregated metrics including posts published, engagement
    (likes, comments, shares), reach/impressions, and queue stats.

    Args:
        user: Authenticated user from JWT token

    Returns:
        AnalyticsResponse with platform-level and aggregate stats
    """
    try:
        agent = _get_agent()
        analytics = agent.get_analytics()
        return AnalyticsResponse(**analytics)

    except Exception as exc:
        logger.error("Analytics retrieval failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.post(
    "/schedule",
    response_model=SuccessResponse,
    summary="Schedule a post",
    description="Schedule a draft post for publishing at a specific time.",
)
async def schedule_post(
    request: SchedulePostRequest,
    user: TokenPayload = Depends(get_current_user),
) -> SuccessResponse:
    """Schedule a post for future publishing.

    Moves a draft post to 'scheduled' status with the specified
    publish time. The post must exist in the queue.

    Args:
        request: Schedule parameters (post_id, scheduled_at)
        user: Authenticated user from JWT token

    Returns:
        SuccessResponse confirming the schedule

    Raises:
        HTTPException 404: Post not found in queue
        HTTPException 500: Internal error
    """
    logger.info(
        "Scheduling post: id=%s, at=%s, user=%s",
        request.post_id,
        request.scheduled_at,
        user.sub,
    )

    try:
        agent = _get_agent()
        success = agent.schedule_post(
            post_id=request.post_id,
            scheduled_at=request.scheduled_at,
            correlation_id=f"api-schedule-{user.sub}",
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post '{request.post_id}' not found in queue",
            )

        return SuccessResponse(
            success=True,
            message=f"Post {request.post_id} scheduled for {request.scheduled_at}",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Post scheduling failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


@router.post(
    "/publish",
    response_model=SuccessResponse,
    summary="Publish a post",
    description=(
        "Publish a post from the queue. In production this triggers the "
        "platform API integration. Currently marks the post as published "
        "and updates analytics counters."
    ),
)
async def publish_post(
    request: PublishPostRequest,
    user: TokenPayload = Depends(get_current_user),
) -> SuccessResponse:
    """Publish a post from the queue.

    Moves the post from queue to published status, records the
    publish timestamp, and increments platform analytics counters.

    Args:
        request: Publish parameters (post_id)
        user: Authenticated user from JWT token

    Returns:
        SuccessResponse confirming publication

    Raises:
        HTTPException 404: Post not found in queue
        HTTPException 500: Internal error
    """
    logger.info(
        "Publishing post: id=%s, user=%s",
        request.post_id,
        user.sub,
    )

    try:
        agent = _get_agent()
        success = agent.publish_post(
            post_id=request.post_id,
            correlation_id=f"api-publish-{user.sub}",
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Post '{request.post_id}' not found in queue",
            )

        return SuccessResponse(
            success=True,
            message=f"Post {request.post_id} published successfully",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Post publishing failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None


# =============================================================================
# Export
# =============================================================================

__all__ = ["router"]
