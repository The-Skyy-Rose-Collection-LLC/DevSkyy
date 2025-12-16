"""
DevSkyy API Module
==================

Enterprise API components:
- API versioning
- Webhook system
- GDPR compliance
- AI agents
- Rate limiting
- Request validation
"""

from .agents import (  # Enums; Service; Router
    AgentCategory,
    AgentService,
    Priority,
    TaskStatus,
    agent_service,
    agents_router,
)
from .gdpr import (  # Enums; Service; Router
    DataCategory,
    GDPRService,
    LegalBasis,
    RequestStatus,
    RequestType,
    gdpr_router,
    gdpr_service,
)
from .speed_insights import (  # Classes; Instances; Router; Factory
    SpeedInsightsMetrics,
    SpeedInsightsMiddleware,
    create_speed_insights_middleware,
    speed_insights_metrics,
    speed_insights_router,
)
from .versioning import (  # Config; Models; Classes; Dependencies; Decorators; Router; Setup
    APIVersion,
    APIVersionFactory,
    RequireVersion,
    VersionConfig,
    VersionedAPIRouter,
    VersionExtractor,
    VersionInfo,
    VersionMiddleware,
    VersionStatus,
    get_api_version,
    setup_api_versioning,
    version_router,
    versioned,
)
from .webhooks import (  # Config; Models; Classes; Instances; Router
    DeliveryStatus,
    WebhookConfig,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEndpointCreate,
    WebhookEndpointResponse,
    WebhookEvent,
    WebhookEventType,
    WebhookManager,
    WebhookReceiver,
    WebhookSigner,
    webhook_manager,
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
    # Speed Insights
    "SpeedInsightsMetrics",
    "SpeedInsightsMiddleware",
    "create_speed_insights_middleware",
    "speed_insights_metrics",
    "speed_insights_router",
    # GDPR
    "DataCategory",
    "LegalBasis",
    "RequestType",
    "RequestStatus",
    "GDPRService",
    "gdpr_service",
    "gdpr_router",
    # Agents
    "AgentCategory",
    "TaskStatus",
    "Priority",
    "AgentService",
    "agent_service",
    "agents_router",
]
