"""
DevSkyy WordPress Module
========================

WordPress/WooCommerce/Elementor integration.

Components:
- WordPressClient: Core WordPress REST API client
- ElementorBuilder: Elementor template generation
- MediaManager: Media upload and management
- WooCommerceProducts: Product CRUD operations

Integration:
- WordPress REST API v2
- WooCommerce REST API v3
- Elementor Kit/Template format
"""

from .client import (
    AuthenticationError,
    NotFoundError,
    WordPressClient,
    WordPressConfig,
    WordPressError,
)
from .elementor import (
    BrandKit,
    ElementorBuilder,
    ElementorConfig,
    ElementorTemplate,
    PageSpec,
    SectionLayout,
    WidgetType,
    generate_template,
)
from .media import (
    ImageOptimizer,
    MediaManager,
    MediaUpload,
)
from .products import (
    ProductCreate,
    ProductUpdate,
    ProductVariation,
    WooCommerceProducts,
)

__all__ = [
    # Client
    "WordPressClient",
    "WordPressConfig",
    "WordPressError",
    "AuthenticationError",
    "NotFoundError",
    # Elementor
    "ElementorBuilder",
    "ElementorConfig",
    "BrandKit",
    "PageSpec",
    "WidgetType",
    "SectionLayout",
    "ElementorTemplate",
    "generate_template",
    # Media
    "MediaManager",
    "MediaUpload",
    "ImageOptimizer",
    # Products
    "WooCommerceProducts",
    "ProductCreate",
    "ProductUpdate",
    "ProductVariation",
]
