"""
Service Registry for Dependency Injection
=========================================

Thread-safe service locator pattern for managing dependencies.

Features:
- Generic type-safe service registration
- Singleton and factory patterns
- Lazy initialization support
- Thread-safe operations
- Clear error messages

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ServiceNotFoundError(Exception):
    """Raised when a requested service is not registered."""

    def __init__(self, service_name: str):
        super().__init__(f"Service not found: {service_name}")
        self.service_name = service_name


class ServiceEntry(Generic[T]):
    """
    Entry in the service registry.

    Supports both singleton instances and factory functions.
    """

    def __init__(
        self,
        instance: T | None = None,
        factory: Callable[[], T] | None = None,
        lazy: bool = False,
    ):
        """
        Initialize service entry.

        Args:
            instance: Pre-created instance (singleton pattern)
            factory: Factory function to create instance (factory pattern)
            lazy: If True, factory is called only when first accessed
        """
        if instance is None and factory is None:
            raise ValueError("Either instance or factory must be provided")

        self.instance = instance
        self.factory = factory
        self.lazy = lazy
        self._initialized = instance is not None
        self._lock = threading.Lock()

    def get(self) -> T:
        """
        Get the service instance.

        For singleton: returns the instance
        For factory: creates new instance each time
        For lazy factory: creates instance on first access

        Returns:
            Service instance
        """
        if self._initialized:
            return self.instance  # type: ignore

        if self.lazy:
            with self._lock:
                # Double-check locking
                if not self._initialized:
                    self.instance = self.factory()  # type: ignore
                    self._initialized = True
                return self.instance  # type: ignore

        # Non-lazy factory: create new instance each time
        return self.factory()  # type: ignore


class ServiceRegistry:
    """
    Centralized service registry for dependency injection.

    Thread-safe singleton pattern.
    """

    _instance: ServiceRegistry | None = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-check locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._services: dict[str, ServiceEntry[Any]] = {}
                    cls._instance._registry_lock = threading.RLock()
        return cls._instance

    def register(
        self,
        service_name: str,
        instance: T | None = None,
        factory: Callable[[], T] | None = None,
        lazy: bool = False,
    ) -> None:
        """
        Register a service.

        Args:
            service_name: Unique service identifier (e.g., "ml_pipeline", "rag_manager")
            instance: Pre-created singleton instance
            factory: Factory function for creating instances
            lazy: If True, factory is called only on first access

        Examples:
            # Singleton instance
            registry.register("db", instance=database_connection)

            # Factory (new instance each time)
            registry.register("temp_dir", factory=lambda: tempfile.mkdtemp())

            # Lazy singleton (created on first access)
            registry.register("ml_pipeline", factory=create_pipeline, lazy=True)
        """
        with self._registry_lock:
            entry = ServiceEntry(instance=instance, factory=factory, lazy=lazy)
            self._services[service_name] = entry
            logger.info(f"Registered service: {service_name}")

    def get(self, service_name: str) -> Any:
        """
        Retrieve a service instance.

        Args:
            service_name: Service identifier

        Returns:
            Service instance

        Raises:
            ServiceNotFoundError: If service is not registered
        """
        with self._registry_lock:
            if service_name not in self._services:
                raise ServiceNotFoundError(service_name)
            return self._services[service_name].get()

    def get_or_none(self, service_name: str) -> Any | None:
        """
        Retrieve a service instance, returning None if not found.

        Args:
            service_name: Service identifier

        Returns:
            Service instance or None
        """
        try:
            return self.get(service_name)
        except ServiceNotFoundError:
            return None

    def is_registered(self, service_name: str) -> bool:
        """
        Check if a service is registered.

        Args:
            service_name: Service identifier

        Returns:
            True if registered, False otherwise
        """
        with self._registry_lock:
            return service_name in self._services

    def unregister(self, service_name: str) -> None:
        """
        Unregister a service.

        Args:
            service_name: Service identifier
        """
        with self._registry_lock:
            if service_name in self._services:
                del self._services[service_name]
                logger.info(f"Unregistered service: {service_name}")

    def clear(self) -> None:
        """
        Clear all registered services.

        Useful for testing.
        """
        with self._registry_lock:
            self._services.clear()
            logger.info("Cleared all registered services")

    def list_services(self) -> list[str]:
        """
        List all registered service names.

        Returns:
            List of service names
        """
        with self._registry_lock:
            return list(self._services.keys())


# Global registry instance
_registry = ServiceRegistry()


def register_service(
    service_name: str,
    instance: T | None = None,
    factory: Callable[[], T] | None = None,
    lazy: bool = False,
) -> None:
    """
    Register a service in the global registry.

    Convenience function for registry.register().
    """
    _registry.register(service_name, instance=instance, factory=factory, lazy=lazy)


def get_service(service_name: str) -> Any:
    """
    Get a service from the global registry.

    Convenience function for registry.get().
    """
    return _registry.get(service_name)
