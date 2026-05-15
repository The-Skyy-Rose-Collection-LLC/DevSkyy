"""Runtime types — resource limits and usage tracking."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ResourceLimits(BaseModel):
    """Per-process resource ceilings. Enforced by the runtime container."""

    model_config = {"frozen": True}

    max_runtime_seconds: float = 300.0
    max_memory_mb: int | None = None
    max_subprocess_count: int = 0
    max_output_bytes: int = 10 * 1024 * 1024
    max_tool_calls: int = 100


class ResourceUsage(BaseModel):
    """Observed resource consumption for an execution."""

    model_config = {"frozen": True}

    runtime_seconds: float = 0.0
    peak_memory_mb: float = 0.0
    subprocess_count: int = 0
    output_bytes: int = 0
    tool_call_count: int = 0
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: datetime | None = None

    def is_within(self, limits: ResourceLimits) -> bool:
        """Check whether observed usage stays inside the limits."""
        if self.runtime_seconds > limits.max_runtime_seconds:
            return False
        if limits.max_memory_mb is not None and self.peak_memory_mb > limits.max_memory_mb:
            return False
        if self.output_bytes > limits.max_output_bytes:
            return False
        if self.tool_call_count > limits.max_tool_calls:
            return False
        return True


class ExecutionResult(BaseModel):
    """Outcome of a container-managed execution."""

    model_config = {"frozen": True}

    success: bool
    result: Any | None = None
    error: str | None = None
    usage: ResourceUsage
    timed_out: bool = False
    killed: bool = False
