"""
SDK-Powered Domain Agents
==========================

Concrete SDKSubAgent implementations for each core domain.
These agents can DO things (run commands, read/write files,
search the web) unlike their text-only SubAgent counterparts.

Registration:
    Each core agent's _register_sub_agents() imports and registers
    the SDK variant alongside existing sub-agents. The SDK agents
    use names prefixed with 'sdk_' to avoid collisions.
"""

import logging as _logging

_logger = _logging.getLogger(__name__)

try:
    from .operations import (
        SDKCodeDoctorAgent,
        SDKDeployRunnerAgent,
        SDKSecurityScannerAgent,
    )
except ImportError as _e:
    _logger.debug("SDK operations agents unavailable: %s", _e)

try:
    from .content import (
        SDKCollectionPublisherAgent,
        SDKSeoWriterAgent,
    )
except ImportError as _e:
    _logger.debug("SDK content agents unavailable: %s", _e)

try:
    from .analytics import (
        SDKDataAnalystAgent,
        SDKReportGeneratorAgent,
    )
except ImportError as _e:
    _logger.debug("SDK analytics agents unavailable: %s", _e)

try:
    from .web_builder import (
        SDKTemplateBuilderAgent,
        SDKThemeDevAgent,
    )
except ImportError as _e:
    _logger.debug("SDK web_builder agents unavailable: %s", _e)

try:
    from .marketing import (
        SDKCampaignAnalystAgent,
        SDKCompetitiveIntelAgent,
    )
except ImportError as _e:
    _logger.debug("SDK marketing agents unavailable: %s", _e)

try:
    from .commerce import (
        SDKCatalogManagerAgent,
        SDKPriceOptimizerAgent,
    )
except ImportError as _e:
    _logger.debug("SDK commerce agents unavailable: %s", _e)

try:
    from .imagery import (
        SDKCompositorAgent,
        SDKImageGenAgent,
        SDKVirtualTryOnAgent,
    )
except ImportError as _e:
    _logger.debug("SDK imagery agents unavailable: %s", _e)

try:
    from .creative import (
        SDKBrandAssetAgent,
        SDKDesignSystemAgent,
    )
except ImportError as _e:
    _logger.debug("SDK creative agents unavailable: %s", _e)

try:
    from .immersive import (
        SDKAvatarStylistAgent,
        SDKGarment3DAgent,
        SDKSceneBuilderAgent,
    )
except ImportError as _e:
    _logger.debug("SDK immersive agents unavailable: %s", _e)

try:
    from .customer_intelligence import SDKCustomerIntelAgent
except ImportError as _e:
    _logger.debug("SDK customer intelligence agent unavailable: %s", _e)

try:
    from .influencer import SDKInfluencerAgent
except ImportError as _e:
    _logger.debug("SDK influencer agent unavailable: %s", _e)

try:
    from .supply_chain import SDKSupplyChainAgent
except ImportError as _e:
    _logger.debug("SDK supply chain agent unavailable: %s", _e)

try:
    from .brand_guardian import SDKBrandGuardianAgent
except ImportError as _e:
    _logger.debug("SDK brand guardian agent unavailable: %s", _e)

try:
    from .community import SDKCommunityLoyaltyAgent
except ImportError as _e:
    _logger.debug("SDK community/loyalty agent unavailable: %s", _e)

try:
    from .seo_discovery import SDKSEODiscoveryAgent
except ImportError as _e:
    _logger.debug("SDK SEO discovery agent unavailable: %s", _e)

__all__ = [
    # Operations
    "SDKDeployRunnerAgent",
    "SDKCodeDoctorAgent",
    "SDKSecurityScannerAgent",
    # Content
    "SDKSeoWriterAgent",
    "SDKCollectionPublisherAgent",
    "SDKSEODiscoveryAgent",
    # Analytics
    "SDKDataAnalystAgent",
    "SDKReportGeneratorAgent",
    "SDKCustomerIntelAgent",
    # Web Builder
    "SDKThemeDevAgent",
    "SDKTemplateBuilderAgent",
    # Marketing
    "SDKCampaignAnalystAgent",
    "SDKCompetitiveIntelAgent",
    "SDKInfluencerAgent",
    "SDKCommunityLoyaltyAgent",
    # Commerce
    "SDKCatalogManagerAgent",
    "SDKPriceOptimizerAgent",
    "SDKSupplyChainAgent",
    # Imagery
    "SDKVirtualTryOnAgent",
    "SDKCompositorAgent",
    "SDKImageGenAgent",
    # Creative
    "SDKBrandAssetAgent",
    "SDKDesignSystemAgent",
    "SDKBrandGuardianAgent",
    # Immersive 3D/AR
    "SDKGarment3DAgent",
    "SDKSceneBuilderAgent",
    "SDKAvatarStylistAgent",
]
