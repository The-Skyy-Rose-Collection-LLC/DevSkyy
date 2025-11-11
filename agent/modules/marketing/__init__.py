"""Marketing and campaign orchestration agents."""

from .marketing_campaign_orchestrator import (
    Campaign,
    CampaignAnalytics,
    CampaignStatus,
    CampaignType,
    CampaignVariant,
    Channel,
    CustomerSegment,
    MarketingCampaignOrchestrator,
    SegmentCriteria,
    TestType,
    marketing_orchestrator,
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
