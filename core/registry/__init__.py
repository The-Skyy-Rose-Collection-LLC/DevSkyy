"""
Core Registry Module
====================

Dependency injection and service registry for DevSkyy.

Provides thread-safe service registration and retrieval for:
- Agent services
- ML pipeline services
- Database repositories
- External integrations
- Cache providers

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from core.registry.service_registry import (
    ServiceNotFoundError,
    ServiceRegistry,
    get_service,
    register_service,
)

__all__ = [
    "ServiceRegistry",
    "ServiceNotFoundError",
    "register_service",
    "get_service",
]
