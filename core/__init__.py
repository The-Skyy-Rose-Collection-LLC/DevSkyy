"""
DevSkyy Core Module
===================

Foundation layer providing shared types, interfaces, and utilities
with zero dependencies on outer application layers (api, agents, services).

Modules:
- auth: Authentication types, models, and interfaces
- registry: Service registry for dependency injection
- agents: Agent interfaces (IAgent, ISuperAgent, IAgentOrchestrator)
- services: Service interfaces (IRAGManager, IMLPipeline, ICacheProvider)
- repositories: Repository interfaces (IRepository, IUserRepository, etc.)

Design Principles:
1. Zero Circular Dependencies: Core never imports from api/, security/, agents/, or services/
2. Type-Only Exports: Provides types and interfaces, not implementations
3. Dependency Inversion: Outer layers depend on core abstractions, not vice versa
"""

from . import agents, auth, registry, repositories, services

__all__ = ["auth", "registry", "agents", "services", "repositories"]
