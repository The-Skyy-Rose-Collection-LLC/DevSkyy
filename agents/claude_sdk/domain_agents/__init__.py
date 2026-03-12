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

__all__ = [
    # Operations
    "SDKDeployRunnerAgent",
    "SDKCodeDoctorAgent",
    "SDKSecurityScannerAgent",
    # Content
    "SDKSeoWriterAgent",
    "SDKCollectionPublisherAgent",
    # Analytics
    "SDKDataAnalystAgent",
    "SDKReportGeneratorAgent",
    # Web Builder
    "SDKThemeDevAgent",
    "SDKTemplateBuilderAgent",
    # Marketing
    "SDKCampaignAnalystAgent",
    "SDKCompetitiveIntelAgent",
    # Commerce
    "SDKCatalogManagerAgent",
    "SDKPriceOptimizerAgent",
]
