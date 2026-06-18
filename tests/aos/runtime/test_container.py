"""Tests for AgentContainer."""

from __future__ import annotations

import asyncio

import pytest

from aos.runtime.container import AgentContainer
from aos.runtime.types import ResourceLimits


class TestSuccess:
    @pytest.mark.asyncio
    async def test_run_returns_result(self):
        c = AgentContainer(ResourceLimits(max_runtime_seconds=2.0))

        async def work(_container):
            return {"answer": 42}

        out = await c.run(work)
        assert out.success
        assert out.result == {"answer": 42}
        assert not out.timed_out
        assert out.usage.runtime_seconds >= 0.0

    @pytest.mark.asyncio
    async def test_runtime_recorded(self):
        c = AgentContainer(ResourceLimits(max_runtime_seconds=2.0))

        async def work(_):
            await asyncio.sleep(0.05)
            return "ok"

        out = await c.run(work)
        assert out.usage.runtime_seconds >= 0.05


class TestTimeout:
    @pytest.mark.asyncio
    async def test_timeout_kills_execution(self):
        c = AgentContainer(ResourceLimits(max_runtime_seconds=0.1))

        async def slow(_):
            await asyncio.sleep(5.0)
            return "done"

        out = await c.run(slow)
        assert not out.success
        assert out.timed_out
        assert "timeout" in (out.error or "").lower()


class TestToolCallLimit:
    @pytest.mark.asyncio
    async def test_tool_call_counter_tracks(self):
        c = AgentContainer(ResourceLimits(max_tool_calls=5))

        async def work(container):
            for _ in range(3):
                container.register_tool_call()
            return container.tool_call_count

        out = await c.run(work)
        assert out.success
        assert out.result == 3
        assert out.usage.tool_call_count == 3

    @pytest.mark.asyncio
    async def test_tool_call_overflow_errors(self):
        c = AgentContainer(ResourceLimits(max_tool_calls=2))

        async def greedy(container):
            for _ in range(10):
                container.register_tool_call()
            return None

        out = await c.run(greedy)
        assert not out.success
        assert "Tool call limit" in (out.error or "")


class TestSubprocessLimit:
    @pytest.mark.asyncio
    async def test_subprocess_default_zero(self):
        c = AgentContainer(ResourceLimits(max_subprocess_count=0))

        async def work(container):
            container.register_subprocess()
            return None

        out = await c.run(work)
        assert not out.success
        assert "Subprocess limit" in (out.error or "")


class TestOutputCap:
    @pytest.mark.asyncio
    async def test_oversized_output_marks_failure(self):
        c = AgentContainer(ResourceLimits(max_output_bytes=10))

        async def work(_):
            return "x" * 100

        out = await c.run(work)
        assert not out.success
        assert "bytes" in (out.error or "")


class TestExceptionTrap:
    @pytest.mark.asyncio
    async def test_arbitrary_exception_caught(self):
        c = AgentContainer()

        async def boom(_):
            raise ValueError("kaboom")

        out = await c.run(boom)
        assert not out.success
        assert "ValueError" in (out.error or "")
        assert "kaboom" in (out.error or "")

    @pytest.mark.asyncio
    async def test_resource_limit_exceeded_caught(self):
        c = AgentContainer(ResourceLimits(max_tool_calls=1))

        async def work(container):
            container.register_tool_call()
            container.register_tool_call()
            return None

        out = await c.run(work)
        assert not out.success
        assert isinstance(out.error, str)
