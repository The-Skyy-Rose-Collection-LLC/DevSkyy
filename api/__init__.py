"""
DevSkyy API Module
==================

Enterprise API components:
- API versioning
- Webhook system
- Rate limiting
- Request validation
"""

from .versioning import (
    # Config
    VersionConfig,
    VersionStatus,
    
    # Models
    APIVersion,
    VersionInfo,
    
    # Classes
    VersionExtractor,
    VersionMiddleware,
    VersionedAPIRouter,
    RequireVersion,
    APIVersionFactory,
    
    # Dependencies
    get_api_version,
    
    # Decorators
    versioned,
    
    # Router
    version_router,
    
    # Setup
    setup_api_versioning,
)

from .webhooks import (
    # Config
    WebhookConfig,
    WebhookEventType,
    DeliveryStatus,
    
    # Models
    WebhookEndpoint,
    WebhookEvent,
    WebhookDelivery,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    
    # Classes
    WebhookSigner,
    WebhookManager,
    WebhookReceiver,
    
    # Instances
    webhook_manager,
    
    # Router
    webhook_router,
)

__all__ = [
    # Versioning
    "VersionConfig",
    "VersionStatus",
    "APIVersion",
    "VersionInfo",
    "VersionExtractor",
    "VersionMiddleware",
    "VersionedAPIRouter",
    "RequireVersion",
    "APIVersionFactory",
    "get_api_version",
    "versioned",
    "version_router",
    "setup_api_versioning",
    
    # Webhooks
    "WebhookConfig",
    "WebhookEventType",
    "DeliveryStatus",
    "WebhookEndpoint",
    "WebhookEvent",
    "WebhookDelivery",
    "WebhookEndpointCreate",
    "WebhookEndpointResponse",
    "WebhookSigner",
    "WebhookManager",
    "WebhookReceiver",
    "webhook_manager",
    "webhook_router",
]
