    from .analytics_engine import EcommerceAnalytics
    from .customer_intelligence import CustomerIntelligence
    from .inventory_optimizer import InventoryOptimizer
    from .order_automation import OrderAutomation
    from .pricing_engine import DynamicPricingEngine
    from .product_manager import ProductManager
from typing import TYPE_CHECKING

"""
E-commerce Automation Module
Full-stack fashion ecommerce with ML-powered automation
"""

if TYPE_CHECKING:

__all__ = [
    "ProductManager",
    "InventoryOptimizer",
    "DynamicPricingEngine",
    "OrderAutomation",
    "CustomerIntelligence",
    "EcommerceAnalytics",
]

__VERSION__ =  "1.0.0"
