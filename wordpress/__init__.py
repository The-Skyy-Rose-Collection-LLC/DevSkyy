"""
WordPress Integration Package
==============================

Python client library for WordPress REST API operations,
Elementor template generation, and 3D asset management.

For SkyyRose: Where Love Meets Luxury

Modules:
- client: Base WordPress REST API client
- collection_page_manager: Collection page CRUD and design templates
- elementor: Elementor template builder and brand kit
- page_builders: Page-type-specific builders (home, product, collection, etc.)
- media_3d_sync: 3D model upload and sync with WordPress media library
- threed_viewer_plugin: WordPress 3D viewer plugin generator
"""

from wordpress.client import WordPressClient, WordPressError
from wordpress.collection_page_manager import (
    CollectionDesignTemplates,
    CollectionType,
    WordPressCollectionPageManager,
    WordPressConfig,
)
from wordpress.elementor import (
    SKYYROSE_BRAND_KIT,
    ElementorBuilder,
    ElementorConfig,
    ElementorTemplate,
    PageSpec,
    PageType,
)
from wordpress.media_3d_sync import WordPress3DMediaSync
from wordpress.threed_viewer_plugin import (
    ViewerConfig,
    WordPressPluginGenerator,
    generate_shortcode_html,
    generate_viewer_css,
    generate_viewer_javascript,
)

__all__ = [
    # Client
    "WordPressClient",
    "WordPressError",
    # Collection Page Manager
    "CollectionType",
    "CollectionDesignTemplates",
    "WordPressCollectionPageManager",
    "WordPressConfig",
    # Elementor
    "ElementorBuilder",
    "ElementorConfig",
    "ElementorTemplate",
    "PageSpec",
    "PageType",
    "SKYYROSE_BRAND_KIT",
    # Media 3D Sync
    "WordPress3DMediaSync",
    # 3D Viewer Plugin
    "ViewerConfig",
    "WordPressPluginGenerator",
    "generate_viewer_javascript",
    "generate_viewer_css",
    "generate_shortcode_html",
]

__version__ = "1.0.0"
