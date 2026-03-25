"""
Tests for Core Interfaces
==========================

Verify that component implementations satisfy interface contracts.

Author: DevSkyy Platform Team
Version: 1.0.0 (Phase 4 Refactoring)
"""

import pytest


class TestAgentInterfaceCompliance:
    """Verify agents implement IAgent/ISuperAgent correctly."""

    def test_agent_interfaces_importable(self):
        """Agent interfaces should be importable."""
        from core.agents import IAgent, IAgentOrchestrator, ISuperAgent

        assert IAgent is not None
        assert ISuperAgent is not None
        assert IAgentOrchestrator is not None

    def test_enhanced_super_agent_has_required_methods(self):
        """EnhancedSuperAgent should have all ISuperAgent methods."""
        from agents.base_super_agent import EnhancedSuperAgent

        # Check methods exist
        assert hasattr(EnhancedSuperAgent, "execute")
        assert hasattr(EnhancedSuperAgent, "initialize")
        assert hasattr(EnhancedSuperAgent, "execute_auto")


class TestServiceInterfaceCompliance:
    """Verify service implementations."""

    def test_service_interfaces_importable(self):
        """Service interfaces should be importable."""
        from core.services import ICacheProvider, IMLPipeline, IRAGManager

        assert IRAGManager is not None
        assert IMLPipeline is not None
        assert ICacheProvider is not None


class TestRepositoryInterfaceCompliance:
    """Verify repository implementations."""

    def test_repository_interfaces_importable(self):
        """Repository interfaces should be importable."""
        from core.repositories import (
            IOrderRepository,
            IProductRepository,
            IRepository,
            IUserRepository,
        )

        assert IRepository is not None
        assert IUserRepository is not None
        assert IProductRepository is not None
        assert IOrderRepository is not None


class TestServiceRegistryDI:
    """Test dependency injection via ServiceRegistry."""

    def test_register_and_retrieve_service(self, clean_registry):
        """Should register and retrieve typed services."""
        from core.registry import get_service, register_service

        class MockService:
            def do_something(self) -> str:
                return "done"

        register_service("mock", instance=MockService())
        service = get_service("mock")

        assert service.do_something() == "done"

    def test_lazy_initialization(self, clean_registry):
        """Lazy services should initialize on first access."""
        from core.registry import get_service, register_service

        init_count = 0

        def factory():
            nonlocal init_count
            init_count += 1
            return {"initialized": True}

        register_service("lazy_service", factory=factory, lazy=True)

        assert init_count == 0  # Not initialized yet

        service = get_service("lazy_service")
        assert init_count == 1

        # Second access should not reinitialize
        get_service("lazy_service")
        assert init_count == 1

    def test_service_not_found_error(self, clean_registry):
        """Should raise ServiceNotFoundError for missing service."""
        from core.registry import ServiceNotFoundError, get_service

        with pytest.raises(ServiceNotFoundError) as exc_info:
            get_service("nonexistent_service")

        assert "nonexistent_service" in str(exc_info.value)


@pytest.fixture
def clean_registry():
    """Clear service registry before/after test."""
    from core.registry import ServiceRegistry

    registry = ServiceRegistry()
    registry.clear()
    yield registry
    registry.clear()
