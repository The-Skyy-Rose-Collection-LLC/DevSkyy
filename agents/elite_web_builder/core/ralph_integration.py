"""
Ralph-TUI execution loop adapter.

Bridges the ralph_wiggums resilience pattern with Elite Web Builder agents.
Every external call (LLM API, file I/O, network) goes through this adapter
for retry, fallback, and circuit-breaker protection.

Design principle: NO BLOCKING. Errors ralph-loop until pass or exhaust.

Usage:
    executor = RalphExecutor(config=RalphConfig(max_attempts=3))
    result = await executor.execute(my_async_operation)
    if not result.success:
        logger.error("All attempts exhausted: %s", result.error)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Config and result models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RalphConfig:
    """Configuration for ralph-loop execution."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0


@dataclass
class ExecutionResult:
    """Result of a ralph-loop execution."""

    success: bool
    value: Any = None
    error: str | None = None
    attempts: int = 0
    elapsed_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "value": str(self.value)[:200] if self.value is not None else None,
            "error": self.error,
            "attempts": self.attempts,
            "elapsed_ms": round(self.elapsed_ms, 1),
        }


# ---------------------------------------------------------------------------
# Ralph Executor
# ---------------------------------------------------------------------------


class RalphExecutor:
    """
    Resilient execution engine — retry with exponential backoff.

    Wraps any async operation with ralph-loop resilience:
    - Retry with exponential backoff
    - Fallback chain support
    - Timing and attempt tracking
    - No blocking — errors loop until pass or exhaust

    This is a standalone implementation that mirrors utils/ralph_wiggums.py
    patterns but is self-contained within the elite_web_builder package
    (no dependency on DevSkyy root).
    """

    def __init__(self, config: RalphConfig | None = None) -> None:
        self._config = config or RalphConfig()

    async def execute(
        self,
        operation: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute an async operation with retry and exponential backoff.

        Args:
            operation: Async callable to execute
            *args, **kwargs: Passed to the operation

        Returns:
            ExecutionResult with success/failure, value, and attempt count
        """
        start = time.time()
        last_error: str | None = None

        for attempt in range(1, self._config.max_attempts + 1):
            try:
                result = await operation(*args, **kwargs)
                elapsed = (time.time() - start) * 1000

                logger.debug(
                    "ralph-execute: success on attempt %d/%d (%.1fms)",
                    attempt,
                    self._config.max_attempts,
                    elapsed,
                )

                return ExecutionResult(
                    success=True,
                    value=result,
                    attempts=attempt,
                    elapsed_ms=elapsed,
                )

            except Exception as exc:
                last_error = str(exc)
                logger.warning(
                    "ralph-execute: attempt %d/%d failed: %s",
                    attempt,
                    self._config.max_attempts,
                    exc,
                )

                if attempt < self._config.max_attempts:
                    delay = min(
                        self._config.base_delay * (self._config.backoff_factor ** (attempt - 1)),
                        self._config.max_delay,
                    )
                    await asyncio.sleep(delay)

        elapsed = (time.time() - start) * 1000
        logger.error(
            "ralph-execute: exhausted %d attempts (%.1fms). Last error: %s",
            self._config.max_attempts,
            elapsed,
            last_error,
        )

        return ExecutionResult(
            success=False,
            error=last_error,
            attempts=self._config.max_attempts,
            elapsed_ms=elapsed,
        )

    async def execute_with_fallback(
        self,
        primary: Callable[..., Awaitable[Any]],
        fallbacks: list[Callable[..., Awaitable[Any]]],
        *args: Any,
        **kwargs: Any,
    ) -> ExecutionResult:
        """
        Execute primary operation, falling back through alternatives on failure.

        Each operation in the chain gets its own retry attempts.
        The first successful result is returned.

        Args:
            primary: Primary async callable
            fallbacks: List of fallback async callables
            *args, **kwargs: Passed to each operation

        Returns:
            ExecutionResult from the first successful operation
        """
        all_operations = [primary, *fallbacks]
        total_attempts = 0

        for idx, operation in enumerate(all_operations):
            label = "primary" if idx == 0 else f"fallback-{idx}"
            logger.info("ralph-fallback: trying %s", label)

            result = await self.execute(operation, *args, **kwargs)
            total_attempts += result.attempts

            if result.success:
                return ExecutionResult(
                    success=True,
                    value=result.value,
                    attempts=total_attempts,
                    elapsed_ms=result.elapsed_ms,
                )

            logger.warning(
                "ralph-fallback: %s failed after %d attempts",
                label,
                result.attempts,
            )

        return ExecutionResult(
            success=False,
            error=f"All {len(all_operations)} operations failed",
            attempts=total_attempts,
        )
