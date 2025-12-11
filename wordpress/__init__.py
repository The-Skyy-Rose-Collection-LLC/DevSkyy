"""
DevSkyy WordPress/WooCommerce Integration Module
=================================================

Complete integration with WordPress REST API and WooCommerce.

Components:
- client.py: Base WordPress REST API client
- products.py: WooCommerce product management
- media.py: Media library operations
- elementor.py: Elementor template generation

Usage:
    from wordpress import WordPressClient, WooCommerceProducts

    client = WordPressClient(
        url="https://skyyrose.co",
        username="admin",
        app_password="xxxx-xxxx-xxxx-xxxx"
    )
"""

from .client import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    WordPressClient,
    WordPressConfig,
    WordPressError,
)
from .elementor import (
    ElementorSection,
    ElementorTemplateGenerator,
    ElementorWidget,
    TemplateType,
)
from .media import (
    MediaItem,
    MediaManager,
    MediaType,
)
from .products import (
    Product,
    ProductCategory,
    ProductStatus,
    ProductType,
    ProductVariation,
    StockStatus,
    WooCommerceProducts,
)

__all__ = [
    # Client
    "WordPressClient",
    "WordPressConfig",
    "WordPressError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    # Products
    "WooCommerceProducts",
    "Product",
    "ProductVariation",
    "ProductCategory",
    "ProductStatus",
    "ProductType",
    "StockStatus",
    # Media
    "MediaManager",
    "MediaItem",
    "MediaType",
    # Elementor
    "ElementorTemplateGenerator",
    "TemplateType",
    "ElementorWidget",
    "ElementorSection",
]
