"""
License Tiers and Types for DevSkyy Enterprise Platform

Defines available licensing tiers with feature sets, limits, and pricing structures.
Each tier follows a clear feature progression from Trial to Custom Enterprise.

Standards Compliance:
- Clear feature differentiation per industry best practices
- Transparent limit definitions
- Documented pricing structure
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class LicenseType(str, Enum):
    """
    License duration types per software licensing industry standards.

    - TRIAL: Time-limited evaluation license (typically 14-30 days)
    - SUBSCRIPTION: Recurring monthly or annual license
    - PERPETUAL: One-time purchase with lifetime validity
    - CONCURRENT: Floating license based on concurrent users
    """

    TRIAL = "trial"
    SUBSCRIPTION = "subscription"
    PERPETUAL = "perpetual"
    CONCURRENT = "concurrent"


class LicenseTier(str, Enum):
    """
    License tiers with progressive feature unlocking.

    Industry Standard Progression:
    Trial → Professional → Business → Enterprise → Custom

    Each higher tier includes all features of lower tiers plus additional capabilities.
    """

    TRIAL = "trial"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


@dataclass
class LicenseFeatures:
    """
    Feature set and limits for a license tier.

    All limits follow industry-standard usage patterns and scaling factors.
    """

    # API & Request Limits
    api_requests_per_month: int
    api_rate_limit_per_minute: int

    # Agent Limits
    max_ai_agents: int
    max_concurrent_agents: int

    # User & Team Limits
    max_users: int
    max_teams: int

    # Storage & Data
    storage_gb: int
    max_file_upload_mb: int

    # Advanced Features (Boolean flags)
    custom_branding: bool = False
    priority_support: bool = False
    dedicated_account_manager: bool = False
    sla_guarantee: bool = False
    white_label: bool = False
    on_premise_deployment: bool = False
    custom_integrations: bool = False
    advanced_analytics: bool = False
    audit_logs: bool = False
    sso_saml: bool = False
    rbac_advanced: bool = False
    api_webhooks: bool = False
    multi_region: bool = False
    disaster_recovery: bool = False

    # Feature Access
    features: Dict[str, bool] = field(default_factory=dict)

    # SLA Metrics (if applicable)
    uptime_sla_percentage: Optional[float] = None
    support_response_hours: Optional[int] = None


# ============================================================================
# TIER DEFINITIONS - Industry-Standard Feature Progression
# ============================================================================

TIER_FEATURES: Dict[LicenseTier, LicenseFeatures] = {
    LicenseTier.TRIAL: LicenseFeatures(
        # Trial: Limited evaluation for 14-30 days
        api_requests_per_month=10_000,
        api_rate_limit_per_minute=10,
        max_ai_agents=3,
        max_concurrent_agents=1,
        max_users=1,
        max_teams=0,
        storage_gb=1,
        max_file_upload_mb=10,
        features={
            "basic_agents": True,
            "email_support": True,
            "community_support": True,
        },
    ),

    LicenseTier.PROFESSIONAL: LicenseFeatures(
        # Professional: Individual developers and small teams
        api_requests_per_month=100_000,
        api_rate_limit_per_minute=60,
        max_ai_agents=10,
        max_concurrent_agents=3,
        max_users=5,
        max_teams=1,
        storage_gb=25,
        max_file_upload_mb=50,
        priority_support=True,
        api_webhooks=True,
        advanced_analytics=True,
        uptime_sla_percentage=99.5,
        support_response_hours=24,
        features={
            "basic_agents": True,
            "advanced_agents": True,
            "email_support": True,
            "priority_email": True,
            "webhooks": True,
            "analytics_basic": True,
        },
    ),

    LicenseTier.BUSINESS: LicenseFeatures(
        # Business: Growing companies and teams
        api_requests_per_month=500_000,
        api_rate_limit_per_minute=120,
        max_ai_agents=50,
        max_concurrent_agents=10,
        max_users=25,
        max_teams=5,
        storage_gb=100,
        max_file_upload_mb=100,
        custom_branding=True,
        priority_support=True,
        advanced_analytics=True,
        audit_logs=True,
        sso_saml=True,
        rbac_advanced=True,
        api_webhooks=True,
        uptime_sla_percentage=99.9,
        support_response_hours=12,
        features={
            "basic_agents": True,
            "advanced_agents": True,
            "premium_agents": True,
            "email_support": True,
            "priority_support": True,
            "phone_support": True,
            "webhooks": True,
            "analytics_advanced": True,
            "custom_branding": True,
            "sso": True,
            "audit_logs": True,
        },
    ),

    LicenseTier.ENTERPRISE: LicenseFeatures(
        # Enterprise: Large organizations with advanced needs
        api_requests_per_month=5_000_000,
        api_rate_limit_per_minute=500,
        max_ai_agents=500,
        max_concurrent_agents=50,
        max_users=500,
        max_teams=50,
        storage_gb=1000,
        max_file_upload_mb=500,
        custom_branding=True,
        priority_support=True,
        dedicated_account_manager=True,
        sla_guarantee=True,
        white_label=True,
        on_premise_deployment=True,
        custom_integrations=True,
        advanced_analytics=True,
        audit_logs=True,
        sso_saml=True,
        rbac_advanced=True,
        api_webhooks=True,
        multi_region=True,
        disaster_recovery=True,
        uptime_sla_percentage=99.99,
        support_response_hours=4,
        features={
            "basic_agents": True,
            "advanced_agents": True,
            "premium_agents": True,
            "enterprise_agents": True,
            "email_support": True,
            "priority_support": True,
            "phone_support": True,
            "dedicated_support": True,
            "webhooks": True,
            "analytics_enterprise": True,
            "custom_branding": True,
            "white_label": True,
            "sso": True,
            "audit_logs": True,
            "custom_integrations": True,
            "on_premise": True,
            "multi_region": True,
            "disaster_recovery": True,
        },
    ),

    LicenseTier.CUSTOM: LicenseFeatures(
        # Custom: Fully customizable enterprise solution
        api_requests_per_month=-1,  # Unlimited
        api_rate_limit_per_minute=-1,  # Unlimited
        max_ai_agents=-1,  # Unlimited
        max_concurrent_agents=-1,  # Unlimited
        max_users=-1,  # Unlimited
        max_teams=-1,  # Unlimited
        storage_gb=-1,  # Unlimited
        max_file_upload_mb=-1,  # Unlimited
        custom_branding=True,
        priority_support=True,
        dedicated_account_manager=True,
        sla_guarantee=True,
        white_label=True,
        on_premise_deployment=True,
        custom_integrations=True,
        advanced_analytics=True,
        audit_logs=True,
        sso_saml=True,
        rbac_advanced=True,
        api_webhooks=True,
        multi_region=True,
        disaster_recovery=True,
        uptime_sla_percentage=99.999,
        support_response_hours=1,
        features={
            # All features enabled - customizable per contract
            "all_features": True,
        },
    ),
}


# ============================================================================
# PRICING STRUCTURE - Transparent Pricing Per Tier
# ============================================================================

@dataclass
class TierPricing:
    """Pricing structure for a license tier."""

    monthly_price_usd: float
    annual_price_usd: float  # Usually 10-20% discount
    setup_fee_usd: float = 0.0

    @property
    def annual_discount_percentage(self) -> float:
        """Calculate annual discount percentage."""
        monthly_annual = self.monthly_price_usd * 12
        if monthly_annual == 0:
            return 0.0
        return ((monthly_annual - self.annual_price_usd) / monthly_annual) * 100


TIER_PRICING: Dict[LicenseTier, TierPricing] = {
    LicenseTier.TRIAL: TierPricing(
        monthly_price_usd=0.0,
        annual_price_usd=0.0,
    ),
    LicenseTier.PROFESSIONAL: TierPricing(
        monthly_price_usd=99.00,
        annual_price_usd=990.00,  # 17% discount (2 months free)
    ),
    LicenseTier.BUSINESS: TierPricing(
        monthly_price_usd=299.00,
        annual_price_usd=2990.00,  # 17% discount
    ),
    LicenseTier.ENTERPRISE: TierPricing(
        monthly_price_usd=999.00,
        annual_price_usd=9990.00,  # 17% discount
        setup_fee_usd=2500.00,
    ),
    LicenseTier.CUSTOM: TierPricing(
        monthly_price_usd=0.0,  # Custom pricing - contact sales
        annual_price_usd=0.0,  # Custom pricing - contact sales
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_tier_features(tier: LicenseTier) -> LicenseFeatures:
    """Get feature set for a license tier."""
    return TIER_FEATURES[tier]


def get_tier_pricing(tier: LicenseTier) -> TierPricing:
    """Get pricing for a license tier."""
    return TIER_PRICING[tier]


def check_feature_access(tier: LicenseTier, feature_name: str) -> bool:
    """
    Check if a tier has access to a specific feature.

    Args:
        tier: License tier to check
        feature_name: Feature name (e.g., "webhooks", "sso")

    Returns:
        True if feature is accessible in this tier
    """
    features = get_tier_features(tier)

    # Check in features dict
    if feature_name in features.features:
        return features.features[feature_name]

    # Check boolean flags
    return getattr(features, feature_name, False)


def check_limit(tier: LicenseTier, limit_name: str, current_value: int) -> bool:
    """
    Check if current usage is within tier limits.

    Args:
        tier: License tier
        limit_name: Limit to check (e.g., "max_ai_agents")
        current_value: Current usage value

    Returns:
        True if within limits, False if exceeded
    """
    features = get_tier_features(tier)
    limit = getattr(features, limit_name, 0)

    # -1 means unlimited
    if limit == -1:
        return True

    return current_value <= limit
