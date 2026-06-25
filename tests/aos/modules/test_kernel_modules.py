"""Integration tests for Kernel module lifecycle methods."""

from __future__ import annotations

import pytest

from aos.governance.types import AuditEventType
from aos.kernel.kernel import Kernel
from aos.modules.registry import DuplicateModuleError, ModuleNotFoundError
from aos.modules.types import ModuleManifest


async def _noop_factory() -> object:
    return object()


@pytest.fixture
async def kernel(tmp_path):
    k = Kernel(audit_db_path=str(tmp_path / "audit.db"), system_budget_usd=100.0)
    await k.boot()
    return k


@pytest.fixture
def manifest_alpha():
    return ModuleManifest(
        name="alpha",
        version="2.0",
        agent_types=("worker", "analyst"),
        description="Alpha test module",
    )


class TestRegisterAgentFactory:
    @pytest.mark.asyncio
    async def test_emits_agent_registered_event(self, kernel):
        await kernel.register_agent_factory("worker", _noop_factory)
        events = await kernel.audit.query(event_type=AuditEventType.AGENT_REGISTERED)
        assert len(events) == 1
        assert events[0].details["agent_type"] == "worker"

    @pytest.mark.asyncio
    async def test_factory_available_via_registry(self, kernel):
        await kernel.register_agent_factory("analyst", _noop_factory)
        assert kernel.modules.get_factory("analyst") is _noop_factory

    @pytest.mark.asyncio
    async def test_requires_boot(self, tmp_path):
        unbooted = Kernel(audit_db_path=str(tmp_path / "b.db"))
        with pytest.raises(RuntimeError, match="not booted"):
            await unbooted.register_agent_factory("x", _noop_factory)


class TestLoadModule:
    @pytest.mark.asyncio
    async def test_emits_module_loaded_event(self, kernel, manifest_alpha):
        await kernel.load_module(manifest_alpha, {"worker": _noop_factory})
        events = await kernel.audit.query(event_type=AuditEventType.MODULE_LOADED)
        assert len(events) == 1
        assert events[0].details["module"] == "alpha"
        assert events[0].details["version"] == "2.0"
        assert "worker" in events[0].details["agent_types"]

    @pytest.mark.asyncio
    async def test_factories_registered_after_load(self, kernel, manifest_alpha):
        await kernel.load_module(
            manifest_alpha, {"worker": _noop_factory, "analyst": _noop_factory}
        )
        assert kernel.modules.get_factory("worker") is _noop_factory
        assert kernel.modules.get_factory("analyst") is _noop_factory

    @pytest.mark.asyncio
    async def test_is_loaded_true_after_load(self, kernel, manifest_alpha):
        await kernel.load_module(manifest_alpha, {})
        assert kernel.modules.is_loaded("alpha")

    @pytest.mark.asyncio
    async def test_duplicate_load_raises(self, kernel, manifest_alpha):
        await kernel.load_module(manifest_alpha, {})
        with pytest.raises(DuplicateModuleError, match="alpha"):
            await kernel.load_module(manifest_alpha, {})

    @pytest.mark.asyncio
    async def test_requires_boot(self, tmp_path, manifest_alpha):
        unbooted = Kernel(audit_db_path=str(tmp_path / "c.db"))
        with pytest.raises(RuntimeError, match="not booted"):
            await unbooted.load_module(manifest_alpha, {})


class TestUnloadModule:
    @pytest.mark.asyncio
    async def test_emits_module_unloaded_event(self, kernel, manifest_alpha):
        await kernel.load_module(manifest_alpha, {"worker": _noop_factory})
        await kernel.unload_module("alpha")
        events = await kernel.audit.query(event_type=AuditEventType.MODULE_UNLOADED)
        assert len(events) == 1
        assert events[0].details["module"] == "alpha"
        assert "worker" in events[0].details["removed_types"]

    @pytest.mark.asyncio
    async def test_returns_removed_types(self, kernel, manifest_alpha):
        await kernel.load_module(
            manifest_alpha, {"worker": _noop_factory, "analyst": _noop_factory}
        )
        removed = await kernel.unload_module("alpha")
        assert removed == frozenset({"worker", "analyst"})

    @pytest.mark.asyncio
    async def test_factories_unavailable_after_unload(self, kernel, manifest_alpha):
        await kernel.load_module(manifest_alpha, {"worker": _noop_factory})
        await kernel.unload_module("alpha")
        assert kernel.modules.get_factory("worker") is None

    @pytest.mark.asyncio
    async def test_unknown_module_raises(self, kernel):
        with pytest.raises(ModuleNotFoundError, match="ghost"):
            await kernel.unload_module("ghost")

    @pytest.mark.asyncio
    async def test_requires_boot(self, tmp_path):
        unbooted = Kernel(audit_db_path=str(tmp_path / "d.db"))
        with pytest.raises(RuntimeError, match="not booted"):
            await unbooted.unload_module("anything")
