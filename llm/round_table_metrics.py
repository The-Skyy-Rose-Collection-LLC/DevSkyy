"""Prometheus metrics for Round Table monitoring.

This module exports Prometheus metrics for observability:
- Competition counts and durations
- Provider performance metrics
- Tool calling statistics
- ML scoring performance
- Cost and latency tracking

Metrics available at /metrics endpoint for Prometheus scraping.
"""

from __future__ import annotations

import logging

from prometheus_client import Counter, Gauge, Histogram, Info

logger = logging.getLogger(__name__)


# =============================================================================
# Competition Metrics
# =============================================================================

competition_total = Counter(
    "round_table_competitions_total",
    "Total number of Round Table competitions run",
    ["task_category", "provider_count"],
)

competition_duration = Histogram(
    "round_table_competition_duration_seconds",
    "Duration of Round Table competitions in seconds",
    ["task_category"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

competition_errors = Counter(
    "round_table_competition_errors_total",
    "Total number of competition errors",
    ["error_type", "provider"],
)


# =============================================================================
# Provider Performance Metrics
# =============================================================================

provider_wins = Counter(
    "round_table_provider_wins_total",
    "Total wins by provider",
    ["provider", "task_category"],
)

provider_participations = Counter(
    "round_table_provider_participations_total",
    "Total competitions participated in by provider",
    ["provider"],
)

provider_score = Histogram(
    "round_table_provider_score",
    "Provider scores distribution",
    ["provider", "task_category"],
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

provider_latency = Histogram(
    "round_table_provider_latency_ms",
    "Provider response latency in milliseconds",
    ["provider"],
    buckets=[100, 250, 500, 1000, 2000, 5000, 10000, 30000],
)

provider_cost = Histogram(
    "round_table_provider_cost_usd",
    "Provider cost in USD",
    ["provider"],
    buckets=[0.0001, 0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)

provider_win_rate = Gauge(
    "round_table_provider_win_rate",
    "Current win rate for provider (0-1)",
    ["provider"],
)


# =============================================================================
# Scoring Metrics
# =============================================================================

scoring_component = Histogram(
    "round_table_scoring_component",
    "Individual scoring component values",
    ["component", "provider"],
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

ml_scoring_duration = Histogram(
    "round_table_ml_scoring_duration_seconds",
    "Duration of ML-based scoring",
    ["metric"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

ml_scoring_errors = Counter(
    "round_table_ml_scoring_errors_total",
    "ML scoring errors (fallback to heuristics)",
    ["metric", "error_type"],
)


# =============================================================================
# Tool Calling Metrics
# =============================================================================

tool_calls_total = Counter(
    "round_table_tool_calls_total",
    "Total tool calls made during competitions",
    ["provider", "tool_name"],
)

tool_usage_score = Histogram(
    "round_table_tool_usage_score",
    "Tool usage quality scores",
    ["provider"],
    buckets=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
)

tool_errors = Counter(
    "round_table_tool_errors_total",
    "Tool execution errors",
    ["provider", "tool_name", "error_type"],
)


# =============================================================================
# A/B Testing Metrics
# =============================================================================

ab_test_total = Counter(
    "round_table_ab_tests_total",
    "Total A/B tests conducted",
    ["provider_a", "provider_b"],
)

ab_test_significant = Counter(
    "round_table_ab_tests_significant_total",
    "A/B tests with statistically significant results",
    ["winner", "loser"],
)

ab_test_p_value = Histogram(
    "round_table_ab_test_p_value",
    "P-values from A/B tests",
    ["provider_a", "provider_b"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
)

ab_test_effect_size = Histogram(
    "round_table_ab_test_effect_size",
    "Effect sizes (Cohen's d) from A/B tests",
    buckets=[-2.0, -1.0, -0.5, -0.2, 0.0, 0.2, 0.5, 1.0, 2.0],
)


# =============================================================================
# Resource Utilization Metrics
# =============================================================================

tokens_used = Counter(
    "round_table_tokens_total",
    "Total tokens used",
    ["provider", "token_type"],  # token_type: input, output
)

database_operations = Counter(
    "round_table_database_operations_total",
    "Database operations",
    ["operation"],  # operation: insert, select, update
)

database_query_duration = Histogram(
    "round_table_database_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
)


# =============================================================================
# Cache Metrics
# =============================================================================

cache_hits = Counter(
    "round_table_cache_hits_total",
    "Cache hits",
    ["cache_type"],  # cache_type: response, profile, stats
)

cache_misses = Counter(
    "round_table_cache_misses_total",
    "Cache misses",
    ["cache_type"],
)


# =============================================================================
# System Health Metrics
# =============================================================================

active_competitions = Gauge(
    "round_table_active_competitions",
    "Currently active competitions",
)

round_table_info = Info(
    "round_table_info",
    "Round Table system information",
)


# =============================================================================
# Helper Functions
# =============================================================================


def record_competition(
    duration_seconds: float,
    task_category: str = "unknown",
    provider_count: int = 0,
) -> None:
    """Record competition metrics.

    Args:
        duration_seconds: Competition duration
        task_category: Task category
        provider_count: Number of providers that competed
    """
    competition_total.labels(
        task_category=task_category,
        provider_count=str(provider_count),
    ).inc()
    competition_duration.labels(task_category=task_category).observe(duration_seconds)


def record_provider_result(
    provider: str,
    won: bool,
    score: float,
    latency_ms: float,
    cost_usd: float,
    task_category: str = "unknown",
) -> None:
    """Record provider performance metrics.

    Args:
        provider: Provider identifier
        won: Whether provider won
        score: Provider's score (0-100)
        latency_ms: Response latency in milliseconds
        cost_usd: Cost in USD
        task_category: Task category
    """
    provider_participations.labels(provider=provider).inc()

    if won:
        provider_wins.labels(provider=provider, task_category=task_category).inc()

    provider_score.labels(provider=provider, task_category=task_category).observe(score)
    provider_latency.labels(provider=provider).observe(latency_ms)
    provider_cost.labels(provider=provider).observe(cost_usd)


def record_scoring_components(provider: str, scores: dict[str, float]) -> None:
    """Record individual scoring component values.

    Args:
        provider: Provider identifier
        scores: Dictionary of component names to scores
    """
    for component, value in scores.items():
        scoring_component.labels(component=component, provider=provider).observe(value)


def record_ml_scoring(metric: str, duration_seconds: float, error: str | None = None) -> None:
    """Record ML scoring metrics.

    Args:
        metric: ML metric name (coherence, factuality, etc.)
        duration_seconds: Scoring duration
        error: Optional error type if scoring failed
    """
    ml_scoring_duration.labels(metric=metric).observe(duration_seconds)

    if error:
        ml_scoring_errors.labels(metric=metric, error_type=error).inc()


def record_tool_call(provider: str, tool_name: str, error: str | None = None) -> None:
    """Record tool call metrics.

    Args:
        provider: Provider identifier
        tool_name: Tool that was called
        error: Optional error type if call failed
    """
    tool_calls_total.labels(provider=provider, tool_name=tool_name).inc()

    if error:
        tool_errors.labels(
            provider=provider,
            tool_name=tool_name,
            error_type=error,
        ).inc()


def record_ab_test(
    provider_a: str,
    provider_b: str,
    p_value: float,
    effect_size: float,
    winner: str | None,
) -> None:
    """Record A/B test metrics.

    Args:
        provider_a: First provider
        provider_b: Second provider
        p_value: Statistical p-value
        effect_size: Cohen's d effect size
        winner: Winning provider (None if no significant difference)
    """
    ab_test_total.labels(provider_a=provider_a, provider_b=provider_b).inc()

    if winner:
        loser = provider_b if winner == provider_a else provider_a
        ab_test_significant.labels(winner=winner, loser=loser).inc()

    ab_test_p_value.labels(provider_a=provider_a, provider_b=provider_b).observe(p_value)
    ab_test_effect_size.observe(effect_size)


def record_tokens(provider: str, input_tokens: int, output_tokens: int) -> None:
    """Record token usage.

    Args:
        provider: Provider identifier
        input_tokens: Input tokens used
        output_tokens: Output tokens generated
    """
    tokens_used.labels(provider=provider, token_type="input").inc(input_tokens)
    tokens_used.labels(provider=provider, token_type="output").inc(output_tokens)


def record_database_operation(operation: str, duration_seconds: float) -> None:
    """Record database operation metrics.

    Args:
        operation: Operation type (insert, select, update)
        duration_seconds: Operation duration
    """
    database_operations.labels(operation=operation).inc()
    database_query_duration.labels(operation=operation).observe(duration_seconds)


def set_system_info(version: str, providers: list[str], ml_enabled: bool) -> None:
    """Set system information metric.

    Args:
        version: Round Table version
        providers: List of registered providers
        ml_enabled: Whether ML scoring is enabled
    """
    round_table_info.info(
        {
            "version": version,
            "providers": ",".join(providers),
            "ml_enabled": str(ml_enabled),
        }
    )
