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

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class TaskType(str, Enum):
    """Task categories for token usage tracking."""

    CLASSIFY = "classify"
    SUMMARIZE = "summarize"
    CHAT = "chat"
    REASON = "reason"
    GENERATE = "generate"
    EXTRACT = "extract"
    TRANSLATE = "translate"
    CODE = "code"


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
            logger.warning(f"Unknown model cost: {self.model}")
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
