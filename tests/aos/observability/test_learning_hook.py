"""Tests for LearningHook."""

from __future__ import annotations

import pytest

from aos.observability.learning_hook import LearningHook, LearningTrace
from tests.aos._mocks import MockLearningModule


def _trace(agent_type: str = "commerce", success: bool = True, **kwargs) -> LearningTrace:
    return LearningTrace(
        agent_type=agent_type,
        prompt="x",
        result={"content": "ok"},
        success=success,
        retry_count=kwargs.get("retry_count", 0),
        heal_categories=kwargs.get("heal_categories", ()),
        cost_usd=kwargs.get("cost_usd", 0.0),
    )


class TestBatching:
    @pytest.mark.asyncio
    async def test_no_flush_under_batch_size(self):
        hook = LearningHook(batch_size=5)
        for _ in range(3):
            flushed, _n = await hook.record(_trace())
            assert not flushed
        assert await hook.pending_count() == 3

    @pytest.mark.asyncio
    async def test_flush_at_batch_size(self):
        hook = LearningHook(batch_size=3)
        await hook.record(_trace())
        await hook.record(_trace())
        flushed, n = await hook.record(_trace())
        assert flushed
        assert n == 3
        assert await hook.pending_count() == 0

    @pytest.mark.asyncio
    async def test_buffers_isolated_per_agent_type(self):
        hook = LearningHook(batch_size=3)
        await hook.record(_trace(agent_type="commerce"))
        await hook.record(_trace(agent_type="commerce"))
        await hook.record(_trace(agent_type="content"))
        assert await hook.pending_count() == 3
        flushed, _ = await hook.record(_trace(agent_type="commerce"))
        assert flushed
        # commerce flushed, content still buffered
        assert await hook.pending_count() == 1


class TestFlushAll:
    @pytest.mark.asyncio
    async def test_flush_all_drains_every_buffer(self):
        hook = LearningHook(batch_size=10)
        for _ in range(2):
            await hook.record(_trace(agent_type="a"))
        for _ in range(3):
            await hook.record(_trace(agent_type="b"))
        n = await hook.flush_all()
        assert n == 5
        assert await hook.pending_count() == 0


class TestResolverDispatch:
    @pytest.mark.asyncio
    async def test_resolver_called_per_trace(self):
        modules = {"commerce": MockLearningModule(), "content": MockLearningModule()}
        hook = LearningHook(batch_size=2, learning_module_resolver=modules.get)
        await hook.record(_trace(agent_type="commerce", cost_usd=0.1))
        await hook.record(_trace(agent_type="commerce", cost_usd=0.2))
        assert len(modules["commerce"].records) == 2
        assert modules["commerce"].records[0]["cost_usd"] == 0.1

    @pytest.mark.asyncio
    async def test_missing_resolver_module_drops_silently(self):
        hook = LearningHook(batch_size=1, learning_module_resolver=lambda _: None)
        await hook.record(_trace())  # would crash if dispatch wasn't tolerant
        assert hook.flushed_count == 1

    @pytest.mark.asyncio
    async def test_records_carry_retry_history(self):
        modules = {"x": MockLearningModule()}
        hook = LearningHook(batch_size=1, learning_module_resolver=modules.get)
        await hook.record(
            _trace(
                agent_type="x",
                retry_count=2,
                heal_categories=("external", "config"),
            )
        )
        rec = modules["x"].records[0]
        assert rec["retry_count"] == 2
        assert rec["heal_categories"] == ("external", "config")
