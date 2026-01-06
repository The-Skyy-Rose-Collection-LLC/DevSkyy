"""API v1 Package.

This package contains all v1 API routers:
- code: Code scanning and fixing
- wordpress_theme: WordPress theme generation
- wordpress: WordPress/WooCommerce integration
- ml: Machine learning predictions
- media: 3D generation and media processing
- marketing: Marketing campaigns
- commerce: Bulk products and dynamic pricing
- orchestration: Multi-agent workflows
- monitoring: System metrics and agent directory

Version: 1.0.0
"""

from api.v1.code import router as code_router
from api.v1.commerce import router as commerce_router
from api.v1.marketing import router as marketing_router
from api.v1.media import router as media_router
from api.v1.ml import router as ml_router
from api.v1.monitoring import router as monitoring_router
from api.v1.orchestration import router as orchestration_router
from api.v1.wordpress import router as wordpress_router
from api.v1.wordpress_theme import router as wordpress_theme_router

__all__ = [
    "code_router",
    "wordpress_theme_router",
    "wordpress_router",
    "ml_router",
    "media_router",
    "marketing_router",
    "commerce_router",
    "orchestration_router",
    "monitoring_router",
]
