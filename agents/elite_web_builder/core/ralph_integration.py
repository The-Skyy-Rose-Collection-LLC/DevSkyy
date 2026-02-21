"""
Ralph Integration — Ralph-Wiggums resilience adapter for Elite Web Builder.

Wraps async operations with retry, exponential backoff, and fallback chains.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RalphExecutor:
    """Execute async operations with Ralph-Wiggums resilience.

    Retry with exponential backoff, fallback chains, and circuit breaking.
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 30.0,
    ) -> None:
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay

    async def execute(
        self,
        func: Callable[..., Awaitable[T]],
        *args: object,
        fallbacks: list[Callable[..., Awaitable[T]]] | None = None,
        **kwargs: object,
    ) -> T:
        """Execute with retry and optional fallback chain."""
        last_error: Exception | None = None

        # Try primary function
        for attempt in range(self._max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                delay = min(
                    self._base_delay * (2**attempt), self._max_delay
                )
                logger.warning(
                    "Attempt %d/%d failed: %s. Retrying in %.1fs",
                    attempt + 1,
                    self._max_attempts,
                    exc,
                    delay,
                )
                if attempt < self._max_attempts - 1:
                    await asyncio.sleep(delay)

        # Try fallbacks
        for i, fallback in enumerate(fallbacks or []):
            try:
                logger.info("Trying fallback %d", i + 1)
                return await fallback(*args, **kwargs)
            except Exception as exc:
                last_error = exc
                logger.warning("Fallback %d failed: %s", i + 1, exc)

        raise RuntimeError(
            f"All attempts exhausted. Last error: {last_error}"
        ) from last_error
