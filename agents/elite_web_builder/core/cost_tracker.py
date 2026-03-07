"""
Cost tracker — monitors token usage and dollar costs per story.

Tracks input/output tokens for every LLM call, computes cost using
provider pricing, and generates summaries for budget visibility.

Pricing is approximate and should be updated periodically.

Usage:
    tracker = CostTracker()
    tracker.record("US-001", "anthropic", "claude-sonnet-4-6", 1500, 3000)
    tracker.record("US-002", "google", "gemini-3-pro-preview", 2000, 4000)
    print(tracker.total_cost)       # $0.0345
    print(tracker.summary())        # Formatted breakdown
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pricing (USD per 1M tokens) — updated Feb 2026
# ---------------------------------------------------------------------------

# Format: (input_per_1m, output_per_1m)
_PRICING: dict[str, tuple[float, float]] = {
    # Anthropic
    "claude-opus-4-6": (15.0, 75.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5-20250929": (3.0, 15.0),
    "claude-haiku-4-5": (0.80, 4.0),
    # Google
    "gemini-3-pro-preview": (1.25, 5.0),
    "gemini-3-flash-preview": (0.15, 0.60),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.5-flash": (0.15, 0.60),
    # OpenAI
    "gpt-4o": (2.50, 10.0),
    "gpt-4o-mini": (0.15, 0.60),
    # xAI
    "grok-3": (3.0, 15.0),
    "grok-2": (2.0, 10.0),
}

# Fallback for unknown models
_DEFAULT_PRICING: tuple[float, float] = (3.0, 15.0)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class TokenRecord:
    """A single LLM call's token usage."""

    story_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float


@dataclass
class CostSummary:
    """Aggregate cost summary."""

    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: float
    records_count: int
    by_provider: dict[str, float]
    by_model: dict[str, float]
    by_story: dict[str, float]


# ---------------------------------------------------------------------------
# Cost Tracker
# ---------------------------------------------------------------------------


class CostTracker:
    """Tracks token usage and computes dollar costs for all LLM calls."""

    def __init__(self) -> None:
        self._records: list[TokenRecord] = []

    @property
    def records(self) -> list[TokenRecord]:
        return list(self._records)

    @property
    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self._records)

    @property
    def total_input_tokens(self) -> int:
        return sum(r.input_tokens for r in self._records)

    @property
    def total_output_tokens(self) -> int:
        return sum(r.output_tokens for r in self._records)

    @staticmethod
    def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Compute cost in USD for a single call."""
        input_rate, output_rate = _PRICING.get(model, _DEFAULT_PRICING)
        cost = (input_tokens * input_rate + output_tokens * output_rate) / 1_000_000
        return round(cost, 6)

    def record(
        self,
        story_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> TokenRecord:
        """Record a single LLM call's usage."""
        cost = self.compute_cost(model, input_tokens, output_tokens)
        rec = TokenRecord(
            story_id=story_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
        )
        self._records.append(rec)
        logger.debug(
            "CostTracker: %s %s/%s — %d in, %d out, $%.4f",
            story_id,
            provider,
            model,
            input_tokens,
            output_tokens,
            cost,
        )
        return rec

    def summary(self) -> CostSummary:
        """Generate aggregate cost summary."""
        by_provider: dict[str, float] = {}
        by_model: dict[str, float] = {}
        by_story: dict[str, float] = {}

        for r in self._records:
            by_provider[r.provider] = by_provider.get(r.provider, 0) + r.cost_usd
            by_model[r.model] = by_model.get(r.model, 0) + r.cost_usd
            by_story[r.story_id] = by_story.get(r.story_id, 0) + r.cost_usd

        return CostSummary(
            total_input_tokens=self.total_input_tokens,
            total_output_tokens=self.total_output_tokens,
            total_cost_usd=self.total_cost,
            records_count=len(self._records),
            by_provider=by_provider,
            by_model=by_model,
            by_story=by_story,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON output."""
        s = self.summary()
        return {
            "total_cost_usd": round(s.total_cost_usd, 4),
            "total_input_tokens": s.total_input_tokens,
            "total_output_tokens": s.total_output_tokens,
            "calls": s.records_count,
            "by_provider": {k: round(v, 4) for k, v in s.by_provider.items()},
            "by_model": {k: round(v, 4) for k, v in s.by_model.items()},
            "by_story": {k: round(v, 4) for k, v in s.by_story.items()},
        }

    def reset(self) -> None:
        """Clear all records."""
        self._records.clear()
