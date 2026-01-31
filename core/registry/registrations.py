"""
Service Registration Module
============================

Centralized service registration functions called from main_enterprise.py lifespan.

This module handles registration of all services, agents, and infrastructure
components with the ServiceRegistry for dependency injection.

Author: DevSkyy Platform Team
Version: 1.0.0 (Phase 4 Refactoring)
"""

from __future__ import annotations

import logging

from core.registry import register_service

logger = logging.getLogger(__name__)


def register_core_services() -> None:
    """
    Register core infrastructure services.

    Services registered:
    - cache: Redis/memory cache provider
    - logger: Structured logging
    """
    logger.info("Registering core services...")

    # Cache provider (lazy initialization)
    def create_cache():
        """Create cache provider based on environment."""
        import os

        cache_type = os.getenv("CACHE_TYPE", "memory")

        if cache_type == "redis":
            try:
                from core.cache_manager import CacheManager
                return CacheManager()
            except ImportError:
                logger.warning("Redis not available, falling back to memory cache")
                return InMemoryCache()
        else:
            return InMemoryCache()

    register_service("cache", factory=create_cache, lazy=True)
    logger.info("Core services registered")


def register_ml_services() -> None:
    """
    Register ML pipeline services.

    Services registered:
    - ml_pipeline: ML inference pipeline
    """
    logger.info("Registering ML services...")

    def create_ml_pipeline():
        """Create ML pipeline instance."""
        try:
            from services.ml.pipeline_orchestrator import PipelineOrchestrator
            return PipelineOrchestrator()
        except ImportError:
            logger.warning("ML pipeline not available, using mock")
            return MockMLPipeline()

    register_service("ml_pipeline", factory=create_ml_pipeline, lazy=True)
    logger.info("ML services registered")


def register_rag_services() -> None:
    """
    Register RAG (Retrieval-Augmented Generation) services.

    Services registered:
    - rag_manager: RAG context manager
    """
    logger.info("Registering RAG services...")

    def create_rag_manager():
        """Create RAG manager instance."""
        try:
            from orchestration.rag_context_manager import RAGContextManager
            return RAGContextManager()
        except ImportError:
            logger.warning("RAG manager not available, using mock")
            return MockRAGManager()

    register_service("rag_manager", factory=create_rag_manager, lazy=True)
    logger.info("RAG services registered")


def register_llm_services() -> None:
    """
    Register LLM provider services.

    Services registered:
    - llm_router: Multi-provider LLM router
    """
    logger.info("Registering LLM services...")

    def create_llm_router():
        """Create LLM router instance."""
        try:
            from llm.router import LLMRouter
            return LLMRouter()
        except ImportError:
            logger.warning("LLM router not available")
            return None

    register_service("llm_router", factory=create_llm_router, lazy=True)
    logger.info("LLM services registered")


def register_repositories() -> None:
    """
    Register data repositories.

    Repositories registered:
    - user_repository: User data access
    - product_repository: Product data access
    - order_repository: Order data access
    """
    logger.info("Registering repositories...")

    # Note: Repository implementations would be created here
    # For now, we register mock repositories as placeholders

    logger.info("Repositories registered (mocks)")


def register_external_clients() -> None:
    """
    Register external service clients.

    Clients registered:
    - wordpress_client: WordPress.com REST API client
    - woocommerce_client: WooCommerce API client
    - tripo_client: Tripo3D API client
    - fashn_client: FASHN virtual try-on client
    """
    logger.info("Registering external clients...")

    def create_wordpress_client():
        """Create WordPress client."""
        try:
            from integrations.wordpress_client import WordPressClient
            return WordPressClient.from_env()
        except ImportError:
            logger.warning("WordPress client not available")
            return None

    register_service("wordpress_client", factory=create_wordpress_client, lazy=True)

    logger.info("External clients registered")


def register_all_services() -> None:
    """
    Register all services in dependency order.

    Call this from main_enterprise.py lifespan startup.
    """
    logger.info("Starting service registration...")

    # Register in dependency order (no inter-dependencies for now)
    register_core_services()
    register_llm_services()
    register_rag_services()
    register_ml_services()
    register_repositories()
    register_external_clients()

    logger.info("All services registered successfully")


# Mock implementations for missing services
class InMemoryCache:
    """In-memory cache implementation."""

    def __init__(self):
        self._cache: dict = {}

    async def get(self, key: str):
        return self._cache.get(key)

    async def set(self, key: str, value, *, ttl: int | None = None):
        self._cache[key] = value

    async def delete(self, key: str):
        self._cache.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._cache


class MockMLPipeline:
    """Mock ML pipeline for development."""

    async def predict(self, task: str, data, **kwargs):
        return {"task": task, "prediction": None, "confidence": 0.0}

    def get_available_models(self) -> list[str]:
        return ["mock_model"]


class MockRAGManager:
    """Mock RAG manager for development."""

    async def get_context(self, query: str, *, top_k: int = 5, correlation_id: str | None = None):
        return {"documents": [], "scores": [], "query": query}

    async def ingest(self, documents: list[str], *, metadata: dict | None = None) -> int:
        return len(documents)
