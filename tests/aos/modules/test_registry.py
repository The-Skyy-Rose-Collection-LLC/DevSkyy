"""Tests for ModuleRegistry."""

from __future__ import annotations

import pytest

from aos.modules.registry import DuplicateModuleError, ModuleNotFoundError, ModuleRegistry
from aos.modules.types import ModuleManifest


async def _noop_factory() -> object:
    return object()


@pytest.fixture
def registry() -> ModuleRegistry:
    return ModuleRegistry()


@pytest.fixture
def manifest_a() -> ModuleManifest:
    return ModuleManifest(
        name="alpha",
        version="1.0",
        agent_types=("worker", "analyst"),
        description="Alpha module",
    )


class TestRegisterType:
    def test_register_adds_to_registered_types(self, registry):
        registry.register_type("worker", _noop_factory)
        assert "worker" in registry.registered_types

    def test_registered_types_is_frozenset(self, registry):
        registry.register_type("x", _noop_factory)
        assert isinstance(registry.registered_types, frozenset)

    def test_get_factory_returns_registered(self, registry):
        registry.register_type("worker", _noop_factory)
        assert registry.get_factory("worker") is _noop_factory

    def test_get_factory_missing_returns_none(self, registry):
        assert registry.get_factory("unknown") is None

    def test_overwrite_replaces_factory(self, registry):
        async def factory_v2() -> object:
            return object()

        registry.register_type("worker", _noop_factory)
        registry.register_type("worker", factory_v2)
        assert registry.get_factory("worker") is factory_v2


class TestLoad:
    def test_load_registers_all_factories(self, registry, manifest_a):
        registry.load(manifest_a, {"worker": _noop_factory, "analyst": _noop_factory})
        assert "worker" in registry.registered_types
        assert "analyst" in registry.registered_types

    def test_load_is_loaded_returns_true(self, registry, manifest_a):
        registry.load(manifest_a, {})
        assert registry.is_loaded("alpha")

    def test_load_manifest_appears_in_manifests(self, registry, manifest_a):
        registry.load(manifest_a, {})
        assert manifest_a in registry.manifests

    def test_manifests_is_tuple(self, registry, manifest_a):
        registry.load(manifest_a, {})
        assert isinstance(registry.manifests, tuple)

    def test_duplicate_name_raises(self, registry, manifest_a):
        registry.load(manifest_a, {})
        with pytest.raises(DuplicateModuleError, match="alpha"):
            registry.load(manifest_a, {})

    def test_two_manifests_coexist(self, registry, manifest_a):
        manifest_b = ModuleManifest(name="beta", version="2.0", agent_types=("searcher",))
        registry.load(manifest_a, {"worker": _noop_factory})
        registry.load(manifest_b, {"searcher": _noop_factory})
        assert registry.is_loaded("alpha")
        assert registry.is_loaded("beta")
        assert len(registry.manifests) == 2

    def test_not_loaded_returns_false(self, registry):
        assert not registry.is_loaded("nonexistent")


class TestUnload:
    def test_unload_removes_factories(self, registry, manifest_a):
        registry.load(manifest_a, {"worker": _noop_factory, "analyst": _noop_factory})
        registry.unload("alpha")
        assert "worker" not in registry.registered_types
        assert "analyst" not in registry.registered_types

    def test_unload_returns_removed_types(self, registry, manifest_a):
        registry.load(manifest_a, {"worker": _noop_factory, "analyst": _noop_factory})
        removed = registry.unload("alpha")
        assert removed == frozenset({"worker", "analyst"})

    def test_unload_returns_frozenset(self, registry, manifest_a):
        registry.load(manifest_a, {"worker": _noop_factory})
        assert isinstance(registry.unload("alpha"), frozenset)

    def test_unload_clears_is_loaded(self, registry, manifest_a):
        registry.load(manifest_a, {})
        registry.unload("alpha")
        assert not registry.is_loaded("alpha")

    def test_unload_removes_from_manifests(self, registry, manifest_a):
        registry.load(manifest_a, {})
        registry.unload("alpha")
        assert manifest_a not in registry.manifests

    def test_unload_unknown_raises(self, registry):
        with pytest.raises(ModuleNotFoundError, match="ghost"):
            registry.unload("ghost")

    def test_unload_leaves_other_manifests_intact(self, registry, manifest_a):
        manifest_b = ModuleManifest(name="beta", version="1.0", agent_types=("searcher",))
        registry.load(manifest_a, {"worker": _noop_factory})
        registry.load(manifest_b, {"searcher": _noop_factory})
        registry.unload("alpha")
        assert registry.is_loaded("beta")
        assert registry.get_factory("searcher") is _noop_factory
