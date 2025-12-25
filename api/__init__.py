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

from .agents import (
    AgentCategory,  # Enums; Service; Router
    AgentService,
    Priority,
    TaskStatus,
    agent_service,
    agents_router,
)
from .gdpr import (
    DataCategory,  # Enums; Service; Router
    GDPRService,
    LegalBasis,
    RequestStatus,
    RequestType,
    gdpr_router,
    gdpr_service,
)
from .versioning import (
    APIVersion,  # Config; Models; Classes; Dependencies; Decorators; Router; Setup
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
from .webhooks import (
    DeliveryStatus,  # Config; Models; Classes; Instances; Router
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
