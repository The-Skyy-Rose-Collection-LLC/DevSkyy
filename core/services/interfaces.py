"""
Service Component Interfaces
============================

Abstract base classes for core services.

Author: DevSkyy Platform Team
Version: 1.0.0 (Phase 4 Refactoring)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IRAGManager(ABC):
    """RAG context retrieval interface."""

    @abstractmethod
    async def get_context(
        self, query: str, *, top_k: int = 5, correlation_id: str | None = None
    ) -> Any:
        """
        Retrieve relevant context for query.

        Args:
            query: Search query
            top_k: Number of results to return
            correlation_id: Optional correlation ID

        Returns:
            RAGContext with documents and scores
        """
        ...

    @abstractmethod
    async def ingest(self, documents: list[str], *, metadata: dict | None = None) -> int:
        """
        Ingest documents into RAG system.

        Args:
            documents: List of document texts
            metadata: Optional metadata per document

        Returns:
            Number of documents ingested
        """
        ...


class IMLPipeline(ABC):
    """ML inference interface."""

    @abstractmethod
    async def predict(self, task: str, data: Any, **kwargs) -> Any:
        """
        Run ML prediction.

        Args:
            task: Task type (e.g., "classification", "generation")
            data: Input data
            **kwargs: Task-specific parameters

        Returns:
            MLPrediction with results
        """
        ...

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        List available ML models.

        Returns:
            List of model names
        """
        ...


class ICacheProvider(ABC):
    """Cache interface for Redis/memory."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, *, ttl: int | None = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiry)
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """
        Delete value from cache.

        Args:
            key: Cache key
        """
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        ...
