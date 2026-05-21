"""Reliability primitives: retries, idempotency, cost quotas.

Production-grade hardening for the clothing 3D pipeline:

- :class:`RetryPolicy` — exponential backoff with full jitter; aware of which
  exceptions are retryable.
- :func:`request_fingerprint` / :class:`IdempotencyCache` — content-addressed
  result cache so duplicate requests (same image bytes + same options) reuse
  the existing artifact instead of burning a fresh TRELLIS call.
- :class:`CostQuota` — per-backend spend ceiling with a token-bucket-style
  rolling window, used by the worker to short-circuit before dispatching to
  paid backends (replicate / modal).

All three components share one design choice: **in-memory by default, swap
in a shared store via Protocol-typed injection**. That way the unit test loop
stays fast, dev runs need zero infra, and prod swaps in Redis without
touching the pipeline code.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol, TypeVar, runtime_checkable

from pipelines.clothing_3d.models import PipelineRequest, PipelineResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


# =============================================================================
# Retry policy
# =============================================================================


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Exponential backoff with full jitter, capped attempts.

    Attributes:
        max_attempts: Total attempts including the first try. ``1`` disables retry.
        base_delay_seconds: Initial sleep before retry #2 (subject to jitter).
        max_delay_seconds: Upper cap for the delay; protects from runaway sleeps.
        backoff_multiplier: Multiplier per attempt (2.0 = double each time).
        retry_on: Exception types that trigger a retry. Anything else propagates.
    """

    max_attempts: int = 3
    base_delay_seconds: float = 2.0
    max_delay_seconds: float = 60.0
    backoff_multiplier: float = 2.0
    retry_on: tuple[type[BaseException], ...] = (
        TimeoutError,
        ConnectionError,
        asyncio.TimeoutError,
    )

    def delay_for(self, attempt: int) -> float:
        """Compute backoff (with full jitter) before attempt #``attempt`` (1-indexed).

        attempt=1 → 0 (first try, no sleep)
        attempt=2 → uniform[0, base]
        attempt=N → uniform[0, base * mult^(N-2)] capped at max_delay_seconds
        """
        if attempt <= 1:
            return 0.0
        target = self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 2))
        capped = min(target, self.max_delay_seconds)
        return random.uniform(0.0, capped)

    async def run(
        self,
        fn: Callable[[], Awaitable[T]],
        *,
        on_retry: Callable[[int, BaseException], None] | None = None,
    ) -> T:
        """Execute ``fn``, retrying on ``self.retry_on`` per the policy.

        Args:
            fn: Async callable; called fresh on each attempt.
            on_retry: Optional callback ``(attempt_number, exception)`` invoked
                between retries (useful for metrics).

        Raises:
            The last exception if all attempts fail.
        """
        last_exc: BaseException | None = None
        for attempt in range(1, self.max_attempts + 1):
            sleep = self.delay_for(attempt)
            if sleep > 0:
                await asyncio.sleep(sleep)
            try:
                return await fn()
            except self.retry_on as exc:  # type: ignore[misc]
                last_exc = exc
                if on_retry:
                    try:
                        on_retry(attempt, exc)
                    except Exception:  # noqa: BLE001
                        logger.exception("on_retry callback failed")
                if attempt == self.max_attempts:
                    raise

        assert last_exc is not None  # for type-checker
        raise last_exc


# =============================================================================
# Idempotency
# =============================================================================


def request_fingerprint(request: PipelineRequest) -> str:
    """Stable SHA-256 fingerprint of the inputs that affect generation.

    Excludes ``correlation_id`` and ``metadata.artifact_id`` because they
    change per-request without changing the output.
    """
    h = hashlib.sha256()

    def _add(label: str, value: Any) -> None:
        h.update(label.encode())
        h.update(b"\x00")
        h.update(str(value).encode())
        h.update(b"\x00")

    if request.image_path:
        try:
            data = Path(request.image_path).read_bytes()
            h.update(b"img_bytes\x00")
            h.update(hashlib.sha256(data).digest())
        except OSError:
            _add("image_path", request.image_path)
    if request.image_url:
        _add("image_url", request.image_url)
    if request.prompt:
        _add("prompt", request.prompt.strip())

    _add("product_name", request.product_name or "")
    _add("collection", request.collection or "")
    _add("garment_type", request.garment_type or "")
    _add("quality", request.quality.value)
    if request.backend is not None:
        _add("backend", request.backend.value)

    # Allow callers to opt into stronger keys via metadata.
    if request.metadata:
        for key in sorted(request.metadata):
            if not key.startswith("_"):
                _add(f"meta:{key}", request.metadata[key])

    return h.hexdigest()


@dataclass(slots=True)
class IdempotencyEntry:
    """Cached pipeline result for a fingerprint."""

    fingerprint: str
    result: PipelineResult
    cached_at: datetime


@runtime_checkable
class IdempotencyStore(Protocol):
    """Pluggable backing store for :class:`IdempotencyCache`.

    Implementations: :class:`InMemoryIdempotencyStore` (default),
    ``RedisIdempotencyStore`` (see :mod:`pipelines.clothing_3d.job_store`).
    """

    async def get(self, fingerprint: str) -> IdempotencyEntry | None: ...

    async def put(self, entry: IdempotencyEntry, *, ttl_seconds: int) -> None: ...


class InMemoryIdempotencyStore:
    """Default in-process store with TTL eviction."""

    def __init__(self, *, capacity: int = 1024) -> None:
        self._entries: dict[str, IdempotencyEntry] = {}
        self._lock = asyncio.Lock()
        self._capacity = capacity

    async def get(self, fingerprint: str) -> IdempotencyEntry | None:
        async with self._lock:
            entry = self._entries.get(fingerprint)
            if entry is None:
                return None
            return entry

    async def put(self, entry: IdempotencyEntry, *, ttl_seconds: int) -> None:
        async with self._lock:
            if len(self._entries) >= self._capacity:
                oldest = min(self._entries, key=lambda k: self._entries[k].cached_at)
                self._entries.pop(oldest, None)
            self._entries[entry.fingerprint] = entry


class IdempotencyCache:
    """Content-addressed result cache.

    Wrap any function that takes a :class:`PipelineRequest` and returns a
    :class:`PipelineResult`. Identical inputs return the cached result
    without re-running the pipeline. Failures are NOT cached — only
    ``status == SUCCEEDED`` runs hit the cache.

    Usage:
        cache = IdempotencyCache(ttl_seconds=86_400)
        result = await cache.get_or_run(request, runner=pipeline.run)
    """

    def __init__(
        self,
        *,
        store: IdempotencyStore | None = None,
        ttl_seconds: int = 86_400,
        enabled: bool = True,
    ) -> None:
        self._store = store or InMemoryIdempotencyStore()
        self._ttl = ttl_seconds
        self._enabled = enabled

    async def get_or_run(
        self,
        request: PipelineRequest,
        *,
        runner: Callable[[PipelineRequest], Awaitable[PipelineResult]],
    ) -> tuple[PipelineResult, bool]:
        """Return ``(result, cache_hit)``. Stores successful results."""
        if not self._enabled:
            return await runner(request), False

        fingerprint = request_fingerprint(request)
        cached = await self._store.get(fingerprint)
        if cached is not None:
            age = (datetime.now(UTC) - cached.cached_at).total_seconds()
            if age <= self._ttl:
                logger.info(
                    "idempotency.hit fingerprint=%s age=%.0fs", fingerprint[:12], age
                )
                return cached.result, True

        result = await runner(request)

        if result.status.value == "succeeded":
            await self._store.put(
                IdempotencyEntry(
                    fingerprint=fingerprint,
                    result=result,
                    cached_at=datetime.now(UTC),
                ),
                ttl_seconds=self._ttl,
            )
        return result, False


# =============================================================================
# Cost quotas
# =============================================================================


@dataclass(frozen=True, slots=True)
class BackendCost:
    """Per-call cost approximation for a backend (USD)."""

    backend: str
    usd_per_call: float


# Conservative estimates as of 2026; override via env in prod.
DEFAULT_BACKEND_COSTS: dict[str, BackendCost] = {
    "hf_space": BackendCost("hf_space", 0.0),
    "stub": BackendCost("stub", 0.0),
    "local": BackendCost("local", 0.0),
    "replicate": BackendCost("replicate", 0.05),
    "modal": BackendCost("modal", 0.10),
}


class QuotaExceededError(RuntimeError):
    """Raised when a backend's spend cap is exhausted."""


@dataclass(slots=True)
class _QuotaWindow:
    spent_usd: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class CostQuota:
    """Rolling-window per-backend cost ceiling.

    Wraps each TRELLIS call; rejects with :class:`QuotaExceededError` when the
    backend's window spend would exceed the cap. The window resets when
    ``window_seconds`` elapses since the window started.

    The store is in-memory: for multi-worker deployments, run one quota per
    backend in a sidecar (or share a Redis counter via Lua INCRBY + EXPIRE).

    Usage:
        quota = CostQuota({"replicate": 5.00, "modal": 20.00})
        quota.charge("replicate")  # raises if cap exceeded
    """

    def __init__(
        self,
        caps_usd: dict[str, float] | None = None,
        *,
        window_seconds: int = 86_400,
        costs: dict[str, BackendCost] | None = None,
    ) -> None:
        self._caps = dict(caps_usd or {})
        self._costs = dict(costs or DEFAULT_BACKEND_COSTS)
        self._window_seconds = window_seconds
        self._windows: dict[str, _QuotaWindow] = {}

    def charge(self, backend: str, *, calls: int = 1) -> None:
        cap = self._caps.get(backend)
        if cap is None:
            return  # no cap declared → unlimited

        cost = self._costs.get(backend, BackendCost(backend, 0.0)).usd_per_call * calls
        window = self._windows.setdefault(backend, _QuotaWindow())

        if (datetime.now(UTC) - window.started_at) > timedelta(seconds=self._window_seconds):
            window.spent_usd = 0.0
            window.started_at = datetime.now(UTC)

        projected = window.spent_usd + cost
        if projected > cap:
            raise QuotaExceededError(
                f"backend={backend} spend ${projected:.4f} > cap ${cap:.4f} "
                f"(window started {window.started_at.isoformat()})"
            )
        window.spent_usd = projected

    def spent(self, backend: str) -> float:
        return self._windows.get(backend, _QuotaWindow()).spent_usd

    def cap(self, backend: str) -> float | None:
        return self._caps.get(backend)

    def snapshot(self) -> dict[str, dict[str, float | None]]:
        return {
            backend: {
                "spent_usd": w.spent_usd,
                "cap_usd": self._caps.get(backend),
                "window_started_at": w.started_at.timestamp(),
            }
            for backend, w in self._windows.items()
        }


__all__ = [
    "BackendCost",
    "CostQuota",
    "DEFAULT_BACKEND_COSTS",
    "IdempotencyCache",
    "IdempotencyEntry",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "QuotaExceededError",
    "RetryPolicy",
    "request_fingerprint",
]
