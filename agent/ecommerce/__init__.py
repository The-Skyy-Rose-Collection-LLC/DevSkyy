"""
E-commerce Automation Module
Full-stack fashion ecommerce with ML-powered automation
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .product_manager import ProductManager
    from .inventory_optimizer import InventoryOptimizer
    from .pricing_engine import DynamicPricingEngine
    from .order_automation import OrderAutomation
    from .customer_intelligence import CustomerIntelligence
    from .analytics_engine import EcommerceAnalytics

__all__ = [
    "ProductManager",
    "InventoryOptimizer",
    "DynamicPricingEngine",
    "OrderAutomation",
    "CustomerIntelligence",
    "EcommerceAnalytics",
]

__version__ = "1.0.0"
