"""Tests for core/ralph_integration.py — ADK agents to ralph-tui adapter.

This module bridges ralph_wiggums resilience with the Elite Web Builder
agent execution loop. Every external call goes through ralph-loop.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ralph_integration import (
    RalphConfig,
    RalphExecutor,
    ExecutionResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def executor() -> RalphExecutor:
    return RalphExecutor(config=RalphConfig())


@pytest.fixture
def custom_executor() -> RalphExecutor:
    return RalphExecutor(config=RalphConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=30.0,
    ))


# ---------------------------------------------------------------------------
# RalphConfig
# ---------------------------------------------------------------------------


class TestRalphConfig:
    def test_default_config(self) -> None:
        config = RalphConfig()
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0

    def test_custom_config(self) -> None:
        config = RalphConfig(max_attempts=5, base_delay=0.5)
        assert config.max_attempts == 5
        assert config.base_delay == 0.5


# ---------------------------------------------------------------------------
# Execute with retry
# ---------------------------------------------------------------------------


class TestExecuteWithRetry:
    @pytest.mark.asyncio
    async def test_success_first_try(self, executor: RalphExecutor) -> None:
        operation = AsyncMock(return_value="success")
        result = await executor.execute(operation)
        assert result.success is True
        assert result.value == "success"
        assert result.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, executor: RalphExecutor) -> None:
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("down")
            return "recovered"

        result = await executor.execute(flaky)
        assert result.success is True
        assert result.value == "recovered"
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries(self, executor: RalphExecutor) -> None:
        operation = AsyncMock(side_effect=ConnectionError("always down"))
        result = await executor.execute(operation)
        assert result.success is False
        assert result.error is not None
        assert result.attempts == 3

    @pytest.mark.asyncio
    async def test_custom_max_attempts(self, custom_executor: RalphExecutor) -> None:
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 5:
                raise TimeoutError("slow")
            return "ok"

        result = await custom_executor.execute(flaky)
        assert result.success is True
        assert result.attempts == 5


# ---------------------------------------------------------------------------
# Execute with fallback
# ---------------------------------------------------------------------------


class TestExecuteWithFallback:
    @pytest.mark.asyncio
    async def test_primary_succeeds(self, executor: RalphExecutor) -> None:
        primary = AsyncMock(return_value="primary-result")
        fallback = AsyncMock(return_value="fallback-result")

        result = await executor.execute_with_fallback(primary, [fallback])
        assert result.success is True
        assert result.value == "primary-result"
        fallback.assert_not_called()

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, executor: RalphExecutor) -> None:
        primary = AsyncMock(side_effect=RuntimeError("primary down"))
        fallback = AsyncMock(return_value="fallback-result")

        result = await executor.execute_with_fallback(primary, [fallback])
        assert result.success is True
        assert result.value == "fallback-result"

    @pytest.mark.asyncio
    async def test_all_fail(self, executor: RalphExecutor) -> None:
        primary = AsyncMock(side_effect=RuntimeError("down"))
        fallback1 = AsyncMock(side_effect=RuntimeError("also down"))
        fallback2 = AsyncMock(side_effect=RuntimeError("all down"))

        result = await executor.execute_with_fallback(
            primary, [fallback1, fallback2]
        )
        assert result.success is False

    @pytest.mark.asyncio
    async def test_second_fallback_succeeds(self, executor: RalphExecutor) -> None:
        primary = AsyncMock(side_effect=RuntimeError("down"))
        fallback1 = AsyncMock(side_effect=RuntimeError("also down"))
        fallback2 = AsyncMock(return_value="third-time")

        result = await executor.execute_with_fallback(
            primary, [fallback1, fallback2]
        )
        assert result.success is True
        assert result.value == "third-time"


# ---------------------------------------------------------------------------
# ExecutionResult
# ---------------------------------------------------------------------------


class TestExecutionResult:
    def test_success_result(self) -> None:
        result = ExecutionResult(success=True, value="data", attempts=1)
        assert result.success is True
        assert result.error is None

    def test_failure_result(self) -> None:
        result = ExecutionResult(
            success=False,
            error="connection refused",
            attempts=3,
        )
        assert result.success is False
        assert result.value is None

    def test_to_dict(self) -> None:
        result = ExecutionResult(success=True, value="ok", attempts=1)
        d = result.to_dict()
        assert d["success"] is True
        assert d["attempts"] == 1
