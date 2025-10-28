"""Marketing and campaign orchestration agents."""

from .marketing_campaign_orchestrator import (
    marketing_orchestrator,
    MarketingCampaignOrchestrator,
    Campaign,
    CampaignVariant,
    CustomerSegment,
    CampaignAnalytics,
    CampaignStatus,
    CampaignType,
    Channel,
    TestType,
    SegmentCriteria,
)

__all__ = [
    "marketing_orchestrator",
    "MarketingCampaignOrchestrator",
    "Campaign",
    "CampaignVariant",
    "CustomerSegment",
    "CampaignAnalytics",
    "CampaignStatus",
    "CampaignType",
    "Channel",
    "TestType",
    "SegmentCriteria",
]
