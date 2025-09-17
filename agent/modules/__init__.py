"""
DevSkyy Agent Modules Package

This package contains all the specialized AI agents for comprehensive
website management, optimization, and monitoring.
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

from .fixer import fix_code

# Lightweight exports only to avoid import side-effects during testing/runtime.
# Importing heavy modules at package import time causes unnecessary dependency
# requirements and slows down test discovery. Consumers should import specific
# agents directly from their modules when needed.
from .scanner import scan_site

__all__ = [
    "scan_site",
    "fix_code",
    # Agents intentionally omitted from package-level __all__ to prevent
    # triggering heavy imports on package import. Import from their modules:
    # - from agent.modules.inventory_agent import InventoryAgent
    # - from agent.modules.financial_agent import FinancialAgent
    # - from agent.modules.ecommerce_agent import EcommerceAgent
    # - from agent.modules.wordpress_agent import WordPressAgent
    # - from agent.modules.web_development_agent import WebDevelopmentAgent
    # - from agent.modules.site_communication_agent import SiteCommunicationAgent
    # - from agent.modules.brand_intelligence_agent import BrandIntelligenceAgent
]
