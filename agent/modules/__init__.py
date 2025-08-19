
"""
DevSkyy Agent Modules Package

This package contains all the specialized AI agents for comprehensive 
website management, optimization, and monitoring.
"""

__version__ = "2.0.0"
__author__ = "DevSkyy Enhanced Platform"

# Import all agent modules for easy access
from .scanner import scan_site
from .fixer import fix_code
from .inventory_agent import InventoryAgent
from .financial_agent import FinancialAgent
from .ecommerce_agent import EcommerceAgent
from .wordpress_agent import WordPressAgent
from .web_development_agent import WebDevelopmentAgent
from .site_communication_agent import SiteCommunicationAgent
from .brand_intelligence_agent import BrandIntelligenceAgent

__all__ = [
    'scan_site',
    'fix_code', 
    'InventoryAgent',
    'FinancialAgent',
    'EcommerceAgent',
    'WordPressAgent',
    'WebDevelopmentAgent',
    'SiteCommunicationAgent',
    'BrandIntelligenceAgent'
]
