"""
E-commerce Automation Module
Full-stack fashion ecommerce with ML-powered automation
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from .analytics_engine import EcommerceAnalytics
    from .customer_intelligence import CustomerIntelligence
    from .inventory_optimizer import InventoryOptimizer
    from .order_automation import OrderAutomation
    from .pricing_engine import DynamicPricingEngine
    from .product_manager import ProductManager

__all__ = [
    "CustomerIntelligence",
    "DynamicPricingEngine",
    "EcommerceAnalytics",
    "InventoryOptimizer",
    "OrderAutomation",
    "ProductManager",
]

__version__ = "1.0.0"
