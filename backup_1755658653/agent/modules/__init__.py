
"""
DevSkyy Agent Modules Package

This package contains all the specialized AI agents for comprehensive 
website management, optimization, and monitoring.
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

# Import core modules (always available)
from .scanner import scan_site
from .fixer import fix_code

# Import optional agent modules (may have additional dependencies)
try:
    from .inventory_agent import InventoryAgent
except ImportError:
    InventoryAgent = None

try:
    from .financial_agent import FinancialAgent
except ImportError:
    FinancialAgent = None

try:
    from .ecommerce_agent import EcommerceAgent
except ImportError:
    EcommerceAgent = None

try:
    from .wordpress_agent import WordPressAgent
except ImportError:
    WordPressAgent = None

try:
    from .web_development_agent import WebDevelopmentAgent
except ImportError:
    WebDevelopmentAgent = None

try:
    from .site_communication_agent import SiteCommunicationAgent
except ImportError:
    SiteCommunicationAgent = None

try:
    from .brand_intelligence_agent import BrandIntelligenceAgent
except ImportError:
    BrandIntelligenceAgent = None

# Build __all__ dynamically based on what's available
__all__ = ['scan_site', 'fix_code']

# Add optional agents to __all__ if they were imported successfully
for agent_name in ['InventoryAgent', 'FinancialAgent', 'EcommerceAgent',
                   'WordPressAgent', 'WebDevelopmentAgent', 'SiteCommunicationAgent',
                   'BrandIntelligenceAgent']:
    if globals().get(agent_name) is not None:
        __all__.append(agent_name)
