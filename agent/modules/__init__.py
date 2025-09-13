
"""
DevSkyy Agent Modules Package

This package contains all the specialized AI agents for comprehensive 
website management, optimization, and monitoring.
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

# Import all agent modules for easy access
try:
    from .scanner import scan_site, scan_agents_only
except ImportError as e:
    import logging
    logging.warning(f"Scanner import failed: {e}")
    scan_site = None
    scan_agents_only = None

try:
    from .fixer import fix_code
except ImportError as e:
    import logging
    logging.warning(f"Fixer import failed: {e}")
    fix_code = None

try:
    from .inventory_agent import InventoryAgent
except ImportError as e:
    import logging
    logging.warning(f"InventoryAgent import failed: {e}")
    InventoryAgent = None

try:
    from .financial_agent import FinancialAgent
except ImportError as e:
    import logging
    logging.warning(f"FinancialAgent import failed: {e}")
    FinancialAgent = None

try:
    from .ecommerce_agent import EcommerceAgent
except ImportError as e:
    import logging
    logging.warning(f"EcommerceAgent import failed: {e}")
    EcommerceAgent = None

try:
    from .wordpress_agent import WordPressAgent
except ImportError as e:
    import logging
    logging.warning(f"WordPressAgent import failed: {e}")
    WordPressAgent = None

try:
    from .web_development_agent import WebDevelopmentAgent
except ImportError as e:
    import logging
    logging.warning(f"WebDevelopmentAgent import failed: {e}")
    WebDevelopmentAgent = None

try:
    from .site_communication_agent import SiteCommunicationAgent
except ImportError as e:
    import logging
    logging.warning(f"SiteCommunicationAgent import failed: {e}")
    SiteCommunicationAgent = None

try:
    from .brand_intelligence_agent import BrandIntelligenceAgent
except ImportError as e:
    import logging
    logging.warning(f"BrandIntelligenceAgent import failed: {e}")
    BrandIntelligenceAgent = None

__all__ = [
    'scan_site',
    'scan_agents_only',
    'fix_code',
    'InventoryAgent',
    'FinancialAgent',
    'EcommerceAgent',
    'WordPressAgent',
    'WebDevelopmentAgent',
    'SiteCommunicationAgent',
    'BrandIntelligenceAgent'
]
