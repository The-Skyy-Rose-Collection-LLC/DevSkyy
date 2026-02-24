"""Marketing campaign tool."""

from typing import Any, Literal

from pydantic import Field

from mcp_tools.api_client import _format_response, _make_api_request
from mcp_tools.security import secure_tool
from mcp_tools.server import mcp
from mcp_tools.types import BaseAgentInput


class MarketingCampaignInput(BaseAgentInput):
    """Input for marketing campaign operations."""

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


@mcp.tool(
    name="devskyy_marketing_campaign",
    annotations={
        "title": "DevSkyy Marketing Automation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "defer_loading": True,
        "input_examples": [
            {
                "campaign_type": "email",
                "target_audience": {"segment": "high_value", "location": "US"},
                "schedule": "2025-10-25T10:00:00Z",
            },
            {
                "campaign_type": "multi_channel",
                "target_audience": {"segment": "new_customers", "age_range": "18-35"},
                "content_template": "Welcome to SkyyRose! Enjoy 15% off your first order.",
            },
            {
                "campaign_type": "social",
                "target_audience": {"segment": "engaged", "platform": "instagram"},
            },
        ],
    },
)
@secure_tool("marketing_campaign")
async def marketing_campaign(params: MarketingCampaignInput) -> str:
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
        params (MarketingCampaignInput): Campaign configuration containing:
            - campaign_type: email, sms, social, or multi_channel
            - target_audience: Segmentation criteria
            - content_template: Custom content or AI-generated
            - schedule: Campaign launch time
            - response_format: Output format (markdown/json)

    Returns:
        str: Campaign details with predicted performance metrics

    Example:
        >>> marketing_campaign({
        ...     "campaign_type": "email",
        ...     "target_audience": {"segment": "high_value", "location": "US"},
        ...     "schedule": "2025-10-25T10:00:00Z"
        ... })
    """
    data = await _make_api_request(
        "marketing/campaign",
        method="POST",
        data={
            "campaign_type": params.campaign_type,
            "target_audience": params.target_audience,
            "content_template": params.content_template,
            "schedule": params.schedule,
        },
    )

    return _format_response(data, params.response_format, "Marketing Campaign")
