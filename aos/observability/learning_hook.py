"""LearningHook — batched per-agent-type trace flusher.

Buffers completed execution traces and periodically flushes them to each
agent's SelfLearningModule. Flush triggers:
    - per-agent_type buffer reaches batch_size (default 10)
    - explicit kernel.shutdown() (flushes everything)
"""

from __future__ import annotations

import asyncio
from typing import Any

from pydantic import BaseModel, Field


class LearningTrace(BaseModel):
    """One execution trace queued for ingestion by an agent's learning module."""

    model_config = {"frozen": True, "arbitrary_types_allowed": True}

    agent_type: str
    prompt: str
    result: Any | None = None
    success: bool
    error: str | None = None
    retry_count: int = 0
    heal_categories: tuple[str, ...] = ()
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class LearningHook:
    """Batches LearningTrace by agent_type and flushes to learning_modules.

    learning_module_resolver(agent_type) returns the per-agent SelfLearningModule
    (or None if the agent doesn't support learning). Resolver returning None means
    traces are dropped on flush — the buffer still empties.
    """

    def __init__(
        self,
        *,
        batch_size: int = 10,
        learning_module_resolver: Any | None = None,
    ) -> None:
        self._buffers: dict[str, list[LearningTrace]] = {}
        self._lock = asyncio.Lock()
        self._batch_size = batch_size
        self._resolver = learning_module_resolver
        self._flushed_count = 0

    @property
    def flushed_count(self) -> int:
        return self._flushed_count

    async def record(self, trace: LearningTrace) -> tuple[bool, int]:
        """Append a trace; flush this agent_type if its buffer hits batch_size.

        Returns (flushed, flushed_count).
        """
        async with self._lock:
            buf = self._buffers.setdefault(trace.agent_type, [])
            buf.append(trace)
            if len(buf) >= self._batch_size:
                drained = self._buffers.pop(trace.agent_type)
            else:
                return False, 0
        return True, await self._dispatch(trace.agent_type, drained)

    async def flush_all(self) -> int:
        """Flush every agent_type's buffer immediately. Returns total traces flushed."""
        async with self._lock:
            snapshot = self._buffers
            self._buffers = {}
        total = 0
        for agent_type, batch in snapshot.items():
            total += await self._dispatch(agent_type, batch)
        return total

    async def pending_count(self) -> int:
        """How many traces are buffered but not yet flushed."""
        async with self._lock:
            return sum(len(b) for b in self._buffers.values())

    async def _dispatch(self, agent_type: str, batch: list[LearningTrace]) -> int:
        """Hand a batch to the agent's learning_module (best-effort)."""
        if self._resolver is None:
            self._flushed_count += len(batch)
            return len(batch)
        module = self._resolver(agent_type)
        if module is None:
            self._flushed_count += len(batch)
            return len(batch)
        for trace in batch:
            await _ingest_one(module, trace)
        self._flushed_count += len(batch)
        return len(batch)


async def _ingest_one(module: Any, trace: LearningTrace) -> None:
    """Adapt a LearningTrace into a SelfLearningModule.record_execution() call.

    Tolerates a missing/incompatible signature: failure is silent (best-effort).
    """
    record_fn = getattr(module, "record_execution", None)
    if record_fn is None:
        return
    try:
        result = record_fn(
            prompt=trace.prompt,
            result=trace.result,
            success=trace.success,
            error=trace.error,
            cost_usd=trace.cost_usd,
            latency_ms=trace.latency_ms,
            retry_count=trace.retry_count,
            heal_categories=trace.heal_categories,
            metadata=trace.metadata,
        )
        if asyncio.iscoroutine(result):
            await result
    except TypeError:
        # Signature mismatch — fall back to single positional arg
        try:
            result = record_fn(trace.model_dump())
            if asyncio.iscoroutine(result):
                await result
        except Exception:  # noqa: BLE001 — best effort
            return
    except Exception:  # noqa: BLE001 — best effort
        return
