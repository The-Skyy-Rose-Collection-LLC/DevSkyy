"""AgentContainer — wraps agent coroutines with resource enforcement.

The container is the single enforcement boundary for runtime limits.
Every kernel-spawned execution must run inside a container.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any

from aos.runtime.types import ExecutionResult, ResourceLimits, ResourceUsage


class AgentContainer:
    """Lightweight execution sandbox.

    Not OS-level isolation (no cgroups/namespaces). It enforces:
      - hard timeout via asyncio.wait_for
      - tool-call quota via a counter the agent must increment
      - output-size cap when the result is bytes/str
    Returns a structured ExecutionResult either way (no exceptions escape).
    """

    def __init__(self, limits: ResourceLimits | None = None) -> None:
        self.limits = limits or ResourceLimits()
        self._tool_calls = 0
        self._subprocess_count = 0
        self._started_at: float | None = None

    @property
    def tool_call_count(self) -> int:
        """Read the current tool-call count."""
        return self._tool_calls

    def register_tool_call(self) -> None:
        """Increment the tool-call counter. Raises if over the limit."""
        self._tool_calls += 1
        if self._tool_calls > self.limits.max_tool_calls:
            msg = f"Tool call limit exceeded: {self._tool_calls} > {self.limits.max_tool_calls}"
            raise ResourceLimitExceeded(msg)

    def register_subprocess(self) -> None:
        """Track a subprocess spawn. Raises if over the limit."""
        self._subprocess_count += 1
        if self._subprocess_count > self.limits.max_subprocess_count:
            msg = (
                f"Subprocess limit exceeded: "
                f"{self._subprocess_count} > {self.limits.max_subprocess_count}"
            )
            raise ResourceLimitExceeded(msg)

    async def run(
        self,
        coro_factory: Callable[[AgentContainer], Awaitable[Any]],
    ) -> ExecutionResult:
        """Execute the agent coroutine inside the container with all limits enforced.

        The factory receives the container so the agent can call register_tool_call().
        """
        start = time.monotonic()
        started_at = datetime.now(timezone.utc)
        self._started_at = start

        timed_out = False
        success = False
        result: Any | None = None
        error: str | None = None

        try:
            result = await asyncio.wait_for(
                coro_factory(self),
                timeout=self.limits.max_runtime_seconds,
            )
            success = True
        except asyncio.TimeoutError:
            timed_out = True
            error = f"Execution exceeded {self.limits.max_runtime_seconds}s timeout"
        except ResourceLimitExceeded as exc:
            error = str(exc)
        except Exception as exc:  # noqa: BLE001 — container is the catch-all boundary
            error = f"{type(exc).__name__}: {exc}"

        runtime = time.monotonic() - start
        output_bytes = _measure_output(result)

        usage = ResourceUsage(
            runtime_seconds=runtime,
            output_bytes=output_bytes,
            subprocess_count=self._subprocess_count,
            tool_call_count=self._tool_calls,
            started_at=started_at,
            ended_at=datetime.now(timezone.utc),
        )

        if success and output_bytes > self.limits.max_output_bytes:
            success = False
            error = f"Output {output_bytes} bytes > limit {self.limits.max_output_bytes}"

        return ExecutionResult(
            success=success,
            result=result if success else None,
            error=error,
            usage=usage,
            timed_out=timed_out,
        )


class ResourceLimitExceeded(RuntimeError):
    """Raised inside the container when a hard limit is hit."""


def _measure_output(value: Any) -> int:
    """Best-effort size measurement for the execution output."""
    if value is None:
        return 0
    if isinstance(value, (bytes, bytearray)):
        return len(value)
    if isinstance(value, str):
        return len(value.encode("utf-8"))
    try:
        import json

        return len(json.dumps(value, default=str).encode("utf-8"))
    except (TypeError, ValueError):
        return len(repr(value).encode("utf-8"))
