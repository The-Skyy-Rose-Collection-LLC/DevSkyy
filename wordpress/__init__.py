"""
DevSkyy WordPress Module
========================

WordPress/WooCommerce/Elementor integration.

Components:
- WordPressClient: Core WordPress REST API client
- ElementorBuilder: Elementor template generation
- MediaManager: Media upload and management
- WooCommerceProducts: Product CRUD operations
- WordPress3DMediaSync: 3D asset sync for products

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
from .media_3d_sync import (
    InvalidAssetURLError,
    ProductNotFoundError,
    WordPress3DConfig,
    WordPress3DMediaSync,
    WordPress3DSyncError,
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
    # 3D Media Sync
    "WordPress3DMediaSync",
    "WordPress3DConfig",
    "WordPress3DSyncError",
    "ProductNotFoundError",
    "InvalidAssetURLError",
    # Products
    "WooCommerceProducts",
    "ProductCreate",
    "ProductUpdate",
    "ProductVariation",
]
