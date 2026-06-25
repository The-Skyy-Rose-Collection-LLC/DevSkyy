"""Marketing Campaign API Endpoints.

This module provides endpoints for:
- Marketing campaign creation and management
- Integration with agents/marketing_agent.py

Version: 1.0.0
"""

import logging
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from adk.base import AgentStatus
from agents.marketing_agent import MarketingAgent
from security.jwt_oauth2_auth import TokenPayload, get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/marketing", tags=["Marketing"])


# =============================================================================
# Request/Response Models
# =============================================================================


class MarketingCampaignRequest(BaseModel):
    """Request model for marketing campaign operations."""

    campaign_type: Literal["email", "sms", "social", "multi_channel"] = Field(
        ..., description="Type of marketing campaign"
    )
    target_audience: dict[str, Any] = Field(
        ...,
        description="Audience targeting criteria (e.g., {'segment': 'high_value', 'location': 'US'})",
    )
    content_template: str | None = Field(
        default=None,
        description="Campaign content template or AI will generate",
        max_length=5000,
    )
    schedule: str | None = Field(
        default=None,
        description="Campaign schedule in ISO format (e.g., '2025-10-25T10:00:00Z')",
    )
    budget: float | None = Field(
        default=None,
        description="Campaign budget in USD",
        ge=0.0,
    )
    ab_test: bool = Field(
        default=False,
        description="Enable A/B testing for campaign optimization",
    )


class MarketingCampaignResponse(BaseModel):
    """Response model for marketing campaigns."""

    campaign_id: str
    status: str
    timestamp: str
    campaign_type: str
    channels: list[str]
    content_generated: bool
    scheduled_for: str | None = None
    campaign_content: str
    metadata: dict[str, Any] | None = None


_CHANNELS_BY_TYPE: dict[str, list[str]] = {
    "email": ["email"],
    "sms": ["sms"],
    "social": ["instagram", "facebook", "tiktok"],
    "multi_channel": ["instagram", "email", "sms", "website"],
}


def _channels_for_campaign(campaign_type: str) -> list[str]:
    """Map a campaign type to the channels the agent should plan for."""
    return _CHANNELS_BY_TYPE.get(campaign_type, ["instagram", "email", "website"])


def _build_campaign_brief(request: MarketingCampaignRequest) -> str:
    """Compose a natural-language brief for the marketing agent from the request."""
    parts = [
        f"Create a {request.campaign_type} marketing campaign for SkyyRose.",
        f"Target audience: {request.target_audience}.",
    ]
    if request.content_template:
        parts.append(f"Content direction: {request.content_template}")
    if request.budget is not None:
        parts.append(f"Budget: ${request.budget:.2f} USD.")
    if request.schedule:
        parts.append(f"Scheduled for: {request.schedule}.")
    if request.ab_test:
        parts.append("Include an A/B test plan.")
    return " ".join(parts)


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/campaigns",
    response_model=MarketingCampaignResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_campaign(
    request: MarketingCampaignRequest, user: TokenPayload = Depends(get_current_user)
) -> MarketingCampaignResponse:
    """Create and execute automated marketing campaigns.

    The Marketing Agent orchestrates multi-channel campaigns:

    **Campaign Types:**

    - **Email**: Personalized email campaigns with AI content
    - **SMS**: Targeted SMS marketing with A/B testing
    - **Social**: Automated social media posts (Instagram, Facebook, TikTok)
    - **Multi-Channel**: Coordinated campaigns across all channels

    **Features:**

    - AI-generated content tailored to audience segments
    - Automatic A/B testing and optimization
    - Real-time performance analytics
    - Customer journey mapping
    - Automated follow-ups based on behavior
    - Compliance with CAN-SPAM, GDPR, TCPA

    **Audience Targeting:**
    - Customer segmentation (high-value, at-risk, new)
    - Behavioral triggers (abandoned cart, browse history)
    - Geographic and demographic filters
    - Purchase history and RFM scoring

    Args:
        request: Campaign configuration (type, audience, content, schedule)
        user: Authenticated user (from JWT token)

    Returns:
        MarketingCampaignResponse with campaign details and predictions

    Raises:
        HTTPException: If campaign creation fails
    """
    campaign_id = str(uuid4())
    logger.info(
        "Creating marketing campaign %s for user %s: %s",
        campaign_id,
        user.sub,
        request.campaign_type,
    )

    channels = _channels_for_campaign(request.campaign_type)
    brief = _build_campaign_brief(request)

    try:
        agent = MarketingAgent()
        result = await agent.create_campaign(brief, channels)
    except Exception as e:
        logger.exception("Marketing campaign creation failed for %s", campaign_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Marketing campaign creation failed",
        ) from e

    if result.status == AgentStatus.FAILED:
        logger.error("Marketing agent failed for %s: %s", campaign_id, result.error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Marketing agent could not generate the campaign",
        )

    return MarketingCampaignResponse(
        campaign_id=campaign_id,
        status="scheduled" if request.schedule else "draft",
        timestamp=datetime.now(UTC).isoformat(),
        campaign_type=request.campaign_type,
        channels=channels,
        content_generated=request.content_template is None,
        scheduled_for=request.schedule,
        campaign_content=result.content,
        metadata=result.metadata,
    )
