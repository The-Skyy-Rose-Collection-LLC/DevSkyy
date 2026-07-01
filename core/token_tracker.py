"""
Centralized Token Usage Tracking
=================================

Provides unified token accounting across all LLM providers with:
- Per-request token tracking
- Aggregation by model, task, agent
- Cost calculation
- Token budget enforcement
- Metrics for monitoring

Integrates with all providers: OpenAI, Anthropic, Google, Mistral, Cohere, Groq.
"""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TaskType(StrEnum):
    """Task categories for token usage tracking."""

    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    CHAT = "chat"
    REASON = "reason"
    GENERATE = "generate"
    EXTRACT = "extract"
    TRANSLATE = "translate"
    CODE = "code"
    EMBED = "embed"  # OBS-wire: server-side image/text embedding encode
    GATE = "gate"  # OBS-wire: brand-centroid gate verdict (cosine score vs centroid)


# Provider cost per 1M tokens (as of 2026-01-08)
PROVIDER_COSTS = {
    # OpenAI
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "o1": {"input": 15.00, "output": 60.00},
    "o1-mini": {"input": 3.00, "output": 12.00},
    # Anthropic
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 1.00, "output": 5.00},
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00},
    # Google
    "gemini-2.0-flash-exp": {"input": 0.00, "output": 0.00},  # Free tier
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    # Mistral
    "mistral-large-latest": {"input": 2.00, "output": 6.00},
    "mistral-small-latest": {"input": 0.20, "output": 0.60},
    # Cohere
    "command-r-plus": {"input": 3.00, "output": 15.00},
    "command-r": {"input": 0.50, "output": 1.50},
    # Groq
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "mixtral-8x7b-32768": {"input": 0.24, "output": 0.24},
    # Embeddings (local weights — no per-token API cost; listed so EMBED rows
    # don't log a spurious unknown_model_cost warning on every encode).
    "openai/clip-vit-base-patch32": {"input": 0.0, "output": 0.0},
    "facebook/dinov2-base": {"input": 0.0, "output": 0.0},
}


@dataclass
class TokenUsage:
    """Token usage for a single LLM request."""

    provider: str
    model: str
    task_type: TaskType
    agent_id: str | None = None
    correlation_id: str | None = None
    # Token counts
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    # Metadata
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float = 0.0
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def calculate_cost(self) -> float:
        """Calculate USD cost for this usage."""
        if self.model not in PROVIDER_COSTS:
            logger.warning("unknown_model_cost", model=self.model)
            return 0.0

        costs = PROVIDER_COSTS[self.model]
        input_cost = (self.input_tokens / 1_000_000) * costs["input"]
        output_cost = (self.output_tokens / 1_000_000) * costs["output"]

        return input_cost + output_cost


class TokenTracker:
    """
    Centralized token usage tracker.

    Tracks token usage across all LLM providers and aggregates by:
    - Provider (openai, anthropic, google, etc.)
    - Model (gpt-4o, claude-3-5-sonnet, etc.)
    - Task type (classify, summarize, chat, etc.)
    - Agent ID
    - Time period

    Usage:
        tracker = TokenTracker()

        # Record usage
        usage = TokenUsage(
            provider="openai",
            model="gpt-4o-mini",
            task_type=TaskType.CLASSIFY,
            input_tokens=100,
            output_tokens=50,
        )
        tracker.record(usage)

        # Get metrics
        total_cost = tracker.get_total_cost()
        by_model = tracker.get_usage_by_model()
    """

    def __init__(self) -> None:
        """Initialize token tracker."""
        self._usages: list[TokenUsage] = []
        logger.info("token_tracker_initialized")

    def record(self, usage: TokenUsage) -> None:
        """
        Record token usage.

        Args:
            usage: TokenUsage instance with token counts
        """
        # Calculate total if not provided
        if usage.total_tokens == 0:
            usage.total_tokens = usage.input_tokens + usage.output_tokens

        self._usages.append(usage)

        # Log with structured data
        logger.info(
            "token_usage_recorded",
            provider=usage.provider,
            model=usage.model,
            task_type=usage.task_type.value,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=usage.calculate_cost(),
            agent_id=usage.agent_id,
            correlation_id=usage.correlation_id,
        )

    def get_total_cost(self, since: datetime | None = None) -> float:
        """
        Get total USD cost.

        Args:
            since: Optional datetime to filter from

        Returns:
            Total cost in USD
        """
        usages = self._usages if not since else [u for u in self._usages if u.timestamp >= since]
        return sum(u.calculate_cost() for u in usages)

    def get_total_tokens(self, since: datetime | None = None) -> dict[str, int]:
        """
        Get total token counts.

        Args:
            since: Optional datetime to filter from

        Returns:
            Dict with input_tokens, output_tokens, total_tokens
        """
        usages = self._usages if not since else [u for u in self._usages if u.timestamp >= since]

        return {
            "input_tokens": sum(u.input_tokens for u in usages),
            "output_tokens": sum(u.output_tokens for u in usages),
            "total_tokens": sum(u.total_tokens for u in usages),
        }

    def get_usage_by_model(self, since: datetime | None = None) -> dict[str, dict[str, Any]]:
        """
        Get aggregated usage by model.

        Args:
            since: Optional datetime to filter from

        Returns:
            Dict mapping model -> {tokens, cost, requests}
        """
        usages = self._usages if not since else [u for u in self._usages if u.timestamp >= since]

        by_model: dict[str, dict[str, Any]] = {}

        for usage in usages:
            if usage.model not in by_model:
                by_model[usage.model] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "requests": 0,
                }

            by_model[usage.model]["input_tokens"] += usage.input_tokens
            by_model[usage.model]["output_tokens"] += usage.output_tokens
            by_model[usage.model]["total_tokens"] += usage.total_tokens
            by_model[usage.model]["cost_usd"] += usage.calculate_cost()
            by_model[usage.model]["requests"] += 1

        return by_model

    def get_usage_by_task_type(
        self, since: datetime | None = None
    ) -> dict[TaskType, dict[str, Any]]:
        """
        Get aggregated usage by task type.

        Args:
            since: Optional datetime to filter from

        Returns:
            Dict mapping TaskType -> {tokens, cost, requests}
        """
        usages = self._usages if not since else [u for u in self._usages if u.timestamp >= since]

        by_task: dict[TaskType, dict[str, Any]] = {}

        for usage in usages:
            if usage.task_type not in by_task:
                by_task[usage.task_type] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "requests": 0,
                }

            by_task[usage.task_type]["input_tokens"] += usage.input_tokens
            by_task[usage.task_type]["output_tokens"] += usage.output_tokens
            by_task[usage.task_type]["total_tokens"] += usage.total_tokens
            by_task[usage.task_type]["cost_usd"] += usage.calculate_cost()
            by_task[usage.task_type]["requests"] += 1

        return by_task

    def get_usage_by_agent(self, since: datetime | None = None) -> dict[str, dict[str, Any]]:
        """
        Get aggregated usage by agent ID.

        Args:
            since: Optional datetime to filter from

        Returns:
            Dict mapping agent_id -> {tokens, cost, requests}
        """
        usages = self._usages if not since else [u for u in self._usages if u.timestamp >= since]

        by_agent: dict[str, dict[str, Any]] = {}

        for usage in usages:
            agent_id = usage.agent_id or "unknown"

            if agent_id not in by_agent:
                by_agent[agent_id] = {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "requests": 0,
                }

            by_agent[agent_id]["input_tokens"] += usage.input_tokens
            by_agent[agent_id]["output_tokens"] += usage.output_tokens
            by_agent[agent_id]["total_tokens"] += usage.total_tokens
            by_agent[agent_id]["cost_usd"] += usage.calculate_cost()
            by_agent[agent_id]["requests"] += 1

        return by_agent

    def records(self, since: datetime | None = None) -> list[TokenUsage]:
        """Return a snapshot copy of recorded usages, optionally filtered by time.

        A copy is returned so consumers (e.g. the fleet observer) can iterate without
        racing concurrent ``record()`` appends — the backing list is not locked. Use
        this instead of touching ``_usages`` directly.
        """
        if since is None:
            return list(self._usages)
        return [u for u in self._usages if u.timestamp >= since]

    def clear(self) -> None:
        """Clear all tracked usage (useful for testing)."""
        self._usages.clear()
        logger.info("token_tracker_cleared")


# Global singleton instance
_global_tracker: TokenTracker | None = None


def get_token_tracker() -> TokenTracker:
    """Get global token tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenTracker()
    return _global_tracker


# Per-agent attribution for telemetry across the async call chain. An agent sets this
# before dispatching an LLM call; the LLM-router emitter reads it when recording usage.
# ContextVars are task-local, so concurrent agents attribute correctly.
current_agent_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_agent_id", default=None
)


def record_llm_usage(
    *,
    provider: str,
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    total_tokens: int = 0,
    latency_ms: float = 0.0,
    success: bool = True,
    error: str | None = None,
    task_type: TaskType = TaskType.CHAT,
    agent_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Record one LLM call into the global tracker, attributed to the current agent.

    ``agent_id`` falls back to the ``current_agent_id`` ContextVar (set by the dispatching
    agent) when not given. NEVER raises — telemetry must not break the LLM call path.
    """
    try:
        get_token_tracker().record(
            TokenUsage(
                provider=provider,
                model=model,
                task_type=task_type,
                agent_id=agent_id if agent_id is not None else current_agent_id.get(),
                correlation_id=correlation_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                latency_ms=latency_ms,
                success=success,
                error=error,
            )
        )
    except Exception:  # noqa: BLE001 — telemetry must never break the call path
        logger.warning("record_llm_usage_failed", exc_info=True)


def record_embedding_usage(
    *,
    model: str,
    latency_ms: float = 0.0,
    success: bool = True,
    cache_hit: bool = False,
    dim: int | None = None,
    count: int = 1,
    agent_id: str | None = None,
    error: str | None = None,
) -> None:
    """Record one embedding encode (or cache hit) into the global tracker.

    OBS-wire: the embedding encode path emitted zero telemetry, so FleetObserver
    was blind to its cost/latency/errors. One row per encode (``task_type=EMBED``)
    with latency, cache-hit, success. Embeddings are token-free (local weights), so
    token counts are 0 and cost resolves to 0. ``agent_id`` falls back to the
    ``current_agent_id`` ContextVar. NEVER raises — telemetry must not break the
    encode path.
    """
    try:
        meta: dict[str, Any] = {"cache_hit": cache_hit, "count": count}
        if dim is not None:
            meta["dim"] = dim
        get_token_tracker().record(
            TokenUsage(
                provider="embeddings",
                model=model,
                task_type=TaskType.EMBED,
                agent_id=agent_id if agent_id is not None else current_agent_id.get(),
                input_tokens=0,
                output_tokens=0,
                latency_ms=latency_ms,
                success=success,
                error=error,
                metadata=meta,
            )
        )
    except Exception:  # noqa: BLE001 — telemetry must never break the encode path
        logger.warning("record_embedding_usage_failed", exc_info=True)


def record_gate_score(
    *,
    model: str,
    score: float,
    accepted: bool,
    threshold: float,
    subject: str | None = None,
    agent_id: str | None = None,
) -> None:
    """Record one brand-centroid gate verdict into the global tracker.

    OBS-wire: ``embedding_gate.evaluate`` produced a cosine score per render but emitted
    nothing, so ``EmbeddingObserver`` (PSI drift) had no signal. One ``TaskType.GATE`` row
    per evaluate carries ``score``/``accepted``/``threshold`` in metadata; ``gate_scores``
    reads them back. Gate scoring uses local embedding weights, so token counts and cost
    are 0. NEVER raises — telemetry must not break the gate.
    """
    try:
        meta: dict[str, Any] = {
            "score": float(score),
            "accepted": bool(accepted),
            "threshold": float(threshold),
        }
        if subject is not None:
            meta["subject"] = subject
        get_token_tracker().record(
            TokenUsage(
                provider="embeddings",
                model=model,
                task_type=TaskType.GATE,
                agent_id=agent_id if agent_id is not None else current_agent_id.get(),
                input_tokens=0,
                output_tokens=0,
                metadata=meta,
            )
        )
    except Exception:  # noqa: BLE001 — telemetry must never break the gate
        logger.warning("record_gate_score_failed", exc_info=True)


def gate_scores(since: datetime | None = None) -> list[float]:
    """Cosine scores from recorded ``TaskType.GATE`` rows, oldest-first.

    The read path the ``EmbeddingObserver`` consumes as ``live_scores`` for PSI drift.
    Filters out non-gate rows (EMBED encodes, LLM calls) and any malformed gate row.
    """
    out: list[float] = []
    for u in get_token_tracker().records(since):
        if u.task_type is TaskType.GATE and "score" in u.metadata:
            try:
                out.append(float(u.metadata["score"]))
            except (TypeError, ValueError):
                continue
    return out
