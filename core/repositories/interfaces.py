"""
Repository Component Interfaces
================================

Generic repository pattern interfaces for data access.

Author: DevSkyy Platform Team
Version: 1.0.0 (Phase 4 Refactoring)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """
    Generic repository interface for data access.

    Type parameter T represents the entity type.
    """

    @abstractmethod
    async def get_by_id(self, id: str, **kwargs) -> T | None:
        """
        Retrieve entity by ID.

        Args:
            id: Entity identifier
            **kwargs: Additional query parameters

        Returns:
            Entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def create(self, entity: T, **kwargs) -> T:
        """
        Create new entity.

        Args:
            entity: Entity to create
            **kwargs: Additional parameters

        Returns:
            Created entity with generated fields (ID, timestamps)
        """
        ...

    @abstractmethod
    async def update(self, id: str, entity: T, **kwargs) -> T:
        """
        Update existing entity.

        Args:
            id: Entity identifier
            entity: Updated entity data
            **kwargs: Additional parameters

        Returns:
            Updated entity

        Raises:
            NotFoundError: If entity doesn't exist
        """
        ...

    @abstractmethod
    async def delete(self, id: str, **kwargs) -> None:
        """
        Delete entity.

        Args:
            id: Entity identifier
            **kwargs: Additional parameters

        Raises:
            NotFoundError: If entity doesn't exist
        """
        ...

    @abstractmethod
    async def list(
        self, filters: dict[str, Any] | None = None, limit: int = 100, **kwargs
    ) -> list[T]:
        """
        List entities with optional filtering.

        Args:
            filters: Filter criteria (field: value pairs)
            limit: Maximum number of results
            **kwargs: Additional query parameters

        Returns:
            List of entities matching filters
        """
        ...


class IUserRepository(IRepository[Any]):
    """User-specific repository interface."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Any | None:
        """Get user by email address."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Any | None:
        """Get user by username."""
        ...


class IProductRepository(IRepository[Any]):
    """Product-specific repository interface."""

    @abstractmethod
    async def get_by_sku(self, sku: str) -> Any | None:
        """Get product by SKU."""
        ...

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[Any]:
        """Search products by query."""
        ...


class IOrderRepository(IRepository[Any]):
    """Order-specific repository interface."""

    @abstractmethod
    async def get_by_user(self, user_id: str, limit: int = 100) -> list[Any]:
        """Get orders for a user."""
        ...

    @abstractmethod
    async def get_by_status(self, status: str, limit: int = 100) -> list[Any]:
        """Get orders by status."""
        ...
