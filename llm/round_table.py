"""
LLM Round Table with Database Persistence
==========================================

Enhanced tournament system where ALL LLMs compete on every task.

Flow:
1. All LLMs generate responses in parallel
2. Score and rank using 4 metrics
3. Select top 2 for A/B comparison
4. Judge LLM determines winner
5. Persist results to Neon PostgreSQL database
6. Implement winning response

Author: DevSkyy Platform Team
Version: 2.0.0."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from llm.adaptive_learning import AdaptiveLearningEngine
from llm.evaluation_metrics import AdvancedMetrics
from llm.round_table_metrics import (
    active_competitions,
    record_ab_test,
    record_competition,
    record_provider_result,
    record_scoring_components,
    set_system_info,
)
from llm.statistics import StatisticalAnalyzer

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================


class LLMProvider(str, Enum):
    """LLM providers participating in Round Table."""

    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    LLAMA = "llama"
    MISTRAL = "mistral"
    COHERE = "cohere"


class CompetitionStatus(str, Enum):
    """Status of a Round Table competition."""

    PENDING = "pending"
    GENERATING = "generating"
    SCORING = "scoring"
    AB_TESTING = "ab_testing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass(slots=True)
class LLMResponse:
    """Response from an LLM provider. Memory-optimized with __slots__."""

    provider: LLMProvider
    content: str
    latency_ms: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: str | None = None
    tool_calls: list[dict[str, Any]] | None = None


@dataclass(slots=True)
class ResponseScores:
    """Scoring breakdown for a response. Memory-optimized with __slots__."""

    # Heuristic metrics (60% total)
    relevance: float = 0.0  # How relevant to the prompt (20%)
    quality: float = 0.0  # Overall output quality (15%)
    completeness: float = 0.0  # Task completion (10%)
    efficiency: float = 0.0  # Token/cost efficiency (10%)
    brand_alignment: float = 0.0  # Brand voice adherence (5%)
    tool_usage_quality: float = 0.0  # Tool calling quality (10%)

    # ML-based metrics (30% total)
    coherence: float = 0.0  # Semantic coherence (10%)
    factuality: float = 0.0  # Grounding in context (10%)
    hallucination_risk: float = 0.0  # Lower = higher risk (5%)
    safety: float = 0.0  # Toxicity/bias detection (5%)

    @property
    def total(self) -> float:
        """Weighted total score with heuristic (60%) + ML-based (30%) metrics."""
        return (
            # Heuristic metrics (60%)
            self.relevance * 0.20
            + self.quality * 0.15
            + self.completeness * 0.10
            + self.efficiency * 0.10
            + self.brand_alignment * 0.05
            + self.tool_usage_quality * 0.10
            # ML-based metrics (30%)
            + self.coherence * 0.10
            + self.factuality * 0.10
            + self.hallucination_risk * 0.05
            + self.safety * 0.05
        )


@dataclass
class RoundTableEntry:
    """Entry in the Round Table competition."""

    provider: LLMProvider
    response: LLMResponse
    scores: ResponseScores = field(default_factory=ResponseScores)
    rank: int = 0

    @property
    def total_score(self) -> float:
        return self.scores.total


@dataclass
class ABTestResult:
    """Result from A/B testing between top 2."""

    entry_a: RoundTableEntry
    entry_b: RoundTableEntry
    winner: RoundTableEntry
    judge_provider: LLMProvider
    judge_reasoning: str
    confidence: float
    tested_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Statistical analysis (optional)
    statistical_p_value: float | None = None
    statistical_effect_size: float | None = None
    bayesian_probability: float | None = None
    is_statistically_significant: bool = False


@dataclass
class RoundTableResult:
    """Complete result from a Round Table competition."""

    id: str
    task_id: str
    prompt: str
    prompt_hash: str
    entries: list[RoundTableEntry]
    top_two: list[RoundTableEntry]
    ab_test: ABTestResult | None
    winner: RoundTableEntry | None
    status: CompetitionStatus
    total_duration_ms: float
    total_cost_usd: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "prompt_hash": self.prompt_hash,
            "prompt_preview": self.prompt[:500],
            "winner_provider": self.winner.provider.value if self.winner else None,
            "winner_score": self.winner.total_score if self.winner else None,
            "runner_up_provider": self.top_two[1].provider.value if len(self.top_two) > 1 else None,
            "runner_up_score": self.top_two[1].total_score if len(self.top_two) > 1 else None,
            "all_scores": {
                e.provider.value: {
                    "total": e.total_score,
                    "latency_ms": e.response.latency_ms,
                    "cost_usd": e.response.cost_usd,
                }
                for e in self.entries
            },
            "ab_test_reasoning": self.ab_test.judge_reasoning if self.ab_test else None,
            "ab_test_confidence": self.ab_test.confidence if self.ab_test else None,
            "status": self.status.value,
            "total_duration_ms": self.total_duration_ms,
            "total_cost_usd": self.total_cost_usd,
            "created_at": self.created_at.isoformat(),
        }


# =============================================================================
# Database Persistence Layer
# =============================================================================


class RoundTableDatabase:
    """Database persistence for Round Table results.

    Uses Neon PostgreSQL for serverless storage.
    """

    # Schema definition
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS round_table_results (
        id UUID PRIMARY KEY,
        task_id VARCHAR(64) NOT NULL,
        prompt_hash VARCHAR(64) NOT NULL,
        prompt_preview TEXT,
        winner_provider VARCHAR(50) NOT NULL,
        winner_score FLOAT NOT NULL,
        winner_response TEXT,
        runner_up_provider VARCHAR(50),
        runner_up_score FLOAT,
        all_scores JSONB,
        ab_test_reasoning TEXT,
        ab_test_confidence FLOAT,
        status VARCHAR(20) NOT NULL,
        total_duration_ms FLOAT,
        total_cost_usd FLOAT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

        -- Indexes
        CONSTRAINT idx_prompt_hash UNIQUE (prompt_hash, task_id)
    );

    CREATE INDEX IF NOT EXISTS idx_round_table_created
        ON round_table_results(created_at DESC);

    CREATE INDEX IF NOT EXISTS idx_round_table_winner
        ON round_table_results(winner_provider);

    CREATE INDEX IF NOT EXISTS idx_round_table_task
        ON round_table_results(task_id);"""

    def __init__(self, connection_string: str | None = None):
        """Initialize database with connection string.

        Args:
            connection_string: PostgreSQL connection string, defaults to DATABASE_URL env var.
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self._pool = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database connection and schema."""
        if not self.connection_string:
            logger.warning("No database connection string configured")
            return

        try:
            import asyncpg

            self._pool = await asyncpg.create_pool(self.connection_string, min_size=2, max_size=10)

            # Type guard for pool
            if self._pool is None:
                raise RuntimeError("Failed to create connection pool")

            # Create schema
            async with self._pool.acquire() as conn:
                await conn.execute(self.SCHEMA)

            self._initialized = True
            logger.info("Round Table database initialized")

        except ImportError:
            logger.warning("asyncpg not installed - database persistence disabled")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")

    async def save_result(self, result: RoundTableResult) -> bool:
        """Save Round Table result to database."""
        if not self._initialized or not self._pool:
            return False

        try:
            data = result.to_dict()

            async with self._pool.acquire() as conn:
                # Safe content extraction with guards
                winner_content = ""
                if result.winner and result.winner.response and result.winner.response.content:
                    content = result.winner.response.content
                    winner_content = str(content)[:5000] if content else ""

                await conn.execute(
                    """
                    INSERT INTO round_table_results (
                        id, task_id, prompt_hash, prompt_preview,
                        winner_provider, winner_score, winner_response,
                        runner_up_provider, runner_up_score,
                        all_scores, ab_test_reasoning, ab_test_confidence,
                        status, total_duration_ms, total_cost_usd, created_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    ON CONFLICT (prompt_hash, task_id) DO UPDATE SET
                        winner_provider = EXCLUDED.winner_provider,
                        winner_score = EXCLUDED.winner_score,
                        winner_response = EXCLUDED.winner_response,
                        all_scores = EXCLUDED.all_scores,
                        status = EXCLUDED.status,
                        total_duration_ms = EXCLUDED.total_duration_ms,
                        total_cost_usd = EXCLUDED.total_cost_usd""",
                    data["id"],
                    data["task_id"],
                    data["prompt_hash"],
                    data["prompt_preview"],
                    data["winner_provider"],
                    data["winner_score"],
                    winner_content,
                    data["runner_up_provider"],
                    data["runner_up_score"],
                    json.dumps(data["all_scores"]),
                    data["ab_test_reasoning"],
                    data["ab_test_confidence"],
                    data["status"],
                    data["total_duration_ms"],
                    data["total_cost_usd"],
                    result.created_at,
                )

            result.persisted = True
            return True

        except Exception as e:
            logger.error(f"Failed to save Round Table result: {e}")
            return False

    async def get_result(self, result_id: str) -> dict | None:
        """Get a specific Round Table result."""
        if not self._initialized or not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM round_table_results WHERE id = $1", result_id
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None

    async def get_history(
        self, limit: int = 100, task_id: str | None = None, provider: str | None = None
    ) -> list[dict]:
        """Get Round Table history."""
        if not self._initialized or not self._pool:
            return []

        try:
            query = "SELECT * FROM round_table_results"
            params = []
            conditions = []

            if task_id:
                conditions.append(f"task_id = ${len(params) + 1}")
                params.append(task_id)

            if provider:
                conditions.append(f"winner_provider = ${len(params) + 1}")
                params.append(provider)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" ORDER BY created_at DESC LIMIT ${len(params) + 1}"
            params.append(limit)

            async with self._pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []

    async def get_provider_stats(self) -> dict[str, dict]:
        """Get aggregated statistics per provider."""
        if not self._initialized or not self._pool:
            return {}

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        winner_provider,
                        COUNT(*) as wins,
                        AVG(winner_score) as avg_score,
                        AVG(total_duration_ms) as avg_latency,
                        AVG(total_cost_usd) as avg_cost
                    FROM round_table_results
                    WHERE status = 'completed'
                    GROUP BY winner_provider
                    ORDER BY wins DESC."""
                )

                return {
                    row["winner_provider"]: {
                        "wins": row["wins"],
                        "avg_score": float(row["avg_score"]),
                        "avg_latency_ms": float(row["avg_latency"]),
                        "avg_cost_usd": float(row["avg_cost"]),
                    }
                    for row in rows
                }

        except Exception as e:
            logger.error(f"Failed to get provider stats: {e}")
            return {}

    async def close(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()


# =============================================================================
# Response Scorer
# =============================================================================


class ResponseScorer:
    """Scores LLM responses on quality metrics."""

    # Brand-positive keywords for SkyyRose
    BRAND_POSITIVE = [
        "luxury",
        "premium",
        "elegant",
        "sophisticated",
        "rose",
        "gold",
        "exclusive",
        "limited",
        "quality",
        "crafted",
        "timeless",
        "love",
        "oakland",
        "street",
        "elevated",
        "refined",
        "meticulous",
    ]

    # Brand-negative keywords to avoid
    BRAND_NEGATIVE = [
        "cheap",
        "discount",
        "basic",
        "simple",
        "ordinary",
        "generic",
        "budget",
        "low-cost",
        "mass-produced",
    ]

    def __init__(self, enable_ml_scoring: bool = True):
        """Initialize ResponseScorer with optional ML-based metrics.

        Args:
            enable_ml_scoring: Whether to enable ML-based scoring metrics
                              Set to False to disable for faster scoring."""
        self.enable_ml_scoring = enable_ml_scoring
        self.advanced_metrics: AdvancedMetrics | None = None

        if enable_ml_scoring:
            try:
                self.advanced_metrics = AdvancedMetrics()
            except Exception as e:
                logger.warning(f"Failed to initialize ML metrics, disabling: {e}")
                self.enable_ml_scoring = False

    async def initialize(self) -> None:
        """Initialize ML models asynchronously.

        Call this after creating the scorer to load ML models.
        Safe to call multiple times (idempotent).."""
        if self.enable_ml_scoring and self.advanced_metrics:
            try:
                await self.advanced_metrics.initialize()
            except Exception as e:
                logger.warning(f"Failed to initialize ML models: {e}")
                self.enable_ml_scoring = False

    async def score_response(
        self,
        response: LLMResponse,
        prompt: str,
        task_context: dict | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> ResponseScores:
        """Score a response on all metrics including tool usage and ML-based metrics."""
        content = response.content or ""

        if not content.strip() or response.error:
            return ResponseScores()

        # Heuristic scoring (always enabled)
        scores = ResponseScores(
            relevance=self._score_relevance(content, prompt),
            quality=self._score_quality(content),
            completeness=self._score_completeness(content, prompt, task_context),
            efficiency=self._score_efficiency(response),
            brand_alignment=self._score_brand_alignment(content),
            tool_usage_quality=self._score_tool_usage(response, tools, prompt),
        )

        # ML-based scoring (optional, graceful degradation)
        if self.enable_ml_scoring and self.advanced_metrics:
            try:
                scores.coherence = await self.advanced_metrics.score_coherence(content)
                scores.factuality = await self.advanced_metrics.score_factuality(
                    content, task_context
                )
                scores.hallucination_risk = await self.advanced_metrics.score_hallucination_risk(
                    content
                )
                scores.safety = await self.advanced_metrics.score_safety(content)
            except Exception as e:
                logger.warning(f"ML scoring failed, using heuristics only: {e}")
                # ML metrics default to 0.0, which is neutral in weighted average

        return scores

    def _score_relevance(self, content: str, prompt: str) -> float:
        """Score how relevant the response is to the prompt."""
        prompt_words = set(prompt.lower().split())
        content_words = set(content.lower().split())

        # Remove common words
        stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
        }
        prompt_words -= stop_words
        content_words -= stop_words

        if not prompt_words:
            return 50.0

        overlap = len(prompt_words & content_words)
        score = (overlap / len(prompt_words)) * 100

        return min(100.0, max(0.0, score))

    def _score_quality(self, content: str) -> float:
        """Score overall quality of the response."""
        score = 50.0  # Base score

        word_count = len(content.split())

        # Length scoring
        if 50 <= word_count <= 500:
            score += 25
        elif word_count > 500:
            score += 15
        elif word_count < 50:
            score -= 10

        # Structure scoring
        if "\n\n" in content:
            score += 5  # Has paragraphs
        if any(p in content for p in ["1.", "2.", "- ", "* ", "•"]):
            score += 5  # Has lists
        if any(h in content for h in ["##", "**", "__"]):
            score += 3  # Has formatting

        # Completion indicators
        if any(c in content.lower() for c in ["therefore", "in conclusion", "finally"]):
            score += 7

        # Penalize issues
        if content.count("...") > 5:
            score -= 10
        if "error" in content.lower() and "error" not in content[:50].lower():
            score -= 15

        return min(100.0, max(0.0, score))

    def _score_completeness(self, content: str, prompt: str, task_context: dict | None) -> float:
        """Score task completion."""
        score = 60.0  # Base for non-empty
        prompt_lower = prompt.lower()

        # Check for code if code task
        if any(kw in prompt_lower for kw in ["code", "implement", "function", "class"]):
            if "```" in content or "def " in content or "class " in content:
                score += 25
            else:
                score -= 15

        # Check for description if describe task
        if "descri" in prompt_lower:
            if len(content) > 200:
                score += 20
            elif len(content) > 100:
                score += 10

        # Check for list if list task
        if any(kw in prompt_lower for kw in ["list", "enumerate", "items"]):
            if any(p in content for p in ["1.", "2.", "- ", "•"]):
                score += 20

        # Check for analysis if analysis task
        if any(kw in prompt_lower for kw in ["analyze", "analysis", "examine"]):
            if len(content) > 300 and "\n" in content:
                score += 15

        return min(100.0, max(0.0, score))

    def _score_efficiency(self, response: LLMResponse) -> float:
        """Score efficiency based on latency and cost."""
        score = 50.0

        # Handle None values gracefully
        latency_ms = response.latency_ms if response.latency_ms is not None else 5000.0
        cost_usd = response.cost_usd if response.cost_usd is not None else 0.02

        # Latency scoring (ideal: 1-3 seconds)
        if latency_ms < 1000:
            score += 25
        elif latency_ms < 3000:
            score += 20
        elif latency_ms < 5000:
            score += 10
        elif latency_ms > 10000:
            score -= 15

        # Cost scoring (ideal: < $0.01)
        if cost_usd < 0.005:
            score += 25
        elif cost_usd < 0.01:
            score += 20
        elif cost_usd < 0.05:
            score += 10
        elif cost_usd > 0.10:
            score -= 15

        return min(100.0, max(0.0, score))

    def _score_brand_alignment(self, content: str) -> float:
        """Score adherence to SkyyRose brand voice."""
        content_lower = content.lower()
        score = 50.0

        # Positive keywords
        for kw in self.BRAND_POSITIVE:
            if kw in content_lower:
                score += 4

        # Negative keywords
        for kw in self.BRAND_NEGATIVE:
            if kw in content_lower:
                score -= 8

        return min(100.0, max(0.0, score))

    def _score_tool_usage(
        self,
        response: LLMResponse,
        tools: list[dict[str, Any]] | None,
        prompt: str,
    ) -> float:
        """Score quality of tool usage (0-100).

        Evaluates 4 dimensions:
        - Appropriateness (30%): Did agent call relevant tools?
        - Argument validity (30%): Are tool arguments correct?
        - Result integration (25%): Did agent use tool results well?
        - Efficiency (15%): Minimal unnecessary tool calls

        Args:
            response: LLM response with potential tool calls
            tools: Available tools for the task
            prompt: Original prompt for context

        Returns:
            Score 0-100 (higher is better)."""
        # No tools scenario - neutral score
        if not tools:
            return 100.0

        tool_calls = response.tool_calls if hasattr(response, "tool_calls") else None

        # Tools available but not used
        if not tool_calls:
            # Check if tools were likely needed based on prompt
            prompt_lower = prompt.lower()
            tool_keywords = ["search", "find", "lookup", "get", "fetch", "calculate", "analyze"]
            if any(kw in prompt_lower for kw in tool_keywords):
                return 50.0  # Penalty for not using tools when needed
            return 100.0  # No tools needed, neutral

        # Score each dimension
        appropriateness = self._score_tool_appropriateness(tool_calls, tools, prompt)
        validity = self._score_argument_validity(tool_calls, tools)
        integration = self._score_result_integration(response.content or "", tool_calls)
        efficiency = self._score_tool_efficiency(tool_calls, tools)

        # Weighted average
        total = appropriateness * 0.30 + validity * 0.30 + integration * 0.25 + efficiency * 0.15

        return min(100.0, max(0.0, total))

    def _score_tool_appropriateness(
        self,
        tool_calls: list[dict],
        tools: list[dict[str, Any]],
        prompt: str,
    ) -> float:
        """Score whether the called tools are appropriate for the task (0-100)."""
        if not tool_calls:
            return 100.0

        # Create mapping of tool names for validation
        available_tool_names = {tool.get("name") for tool in tools if "name" in tool}
        score = 50.0  # Base score

        valid_calls = 0
        for call in tool_calls:
            tool_name = call.get("name") or call.get("function", {}).get("name")
            if not tool_name:
                continue

            # Check if tool exists
            if tool_name in available_tool_names:
                valid_calls += 1
                score += 10
            else:
                score -= 15  # Penalty for calling non-existent tool

        # Bonus for using multiple appropriate tools
        if len(tool_calls) > 1 and valid_calls > 1:
            score += 10

        return min(100.0, max(0.0, score))

    def _score_argument_validity(
        self,
        tool_calls: list[dict],
        tools: list[dict[str, Any]],
    ) -> float:
        """Score whether tool arguments are valid (0-100)."""
        if not tool_calls:
            return 100.0

        score = 50.0
        valid_count = 0

        # Create tool schema lookup
        tool_schemas = {tool.get("name"): tool for tool in tools if "name" in tool}

        for call in tool_calls:
            tool_name = call.get("name") or call.get("function", {}).get("name")
            arguments = call.get("arguments") or call.get("function", {}).get("arguments", {})

            if not tool_name or tool_name not in tool_schemas:
                continue

            schema = tool_schemas[tool_name]
            parameters = schema.get("parameters", {})
            required = parameters.get("required", [])
            properties = parameters.get("properties", {})

            # Check required parameters present
            if isinstance(arguments, dict):
                missing_required = set(required) - set(arguments.keys())
                if not missing_required:
                    score += 15
                    valid_count += 1
                else:
                    score -= 10  # Missing required args

                # Check for extra/invalid parameters
                valid_params = set(properties.keys())
                invalid_params = set(arguments.keys()) - valid_params
                if invalid_params:
                    score -= 5  # Invalid parameters

            else:
                score -= 10  # Arguments not a dict

        # Bonus for all calls having valid arguments
        if valid_count == len(tool_calls) and valid_count > 0:
            score += 20

        return min(100.0, max(0.0, score))

    def _score_result_integration(self, content: str, tool_calls: list[dict]) -> float:
        """Score how well tool results are integrated into the response (0-100)."""
        if not tool_calls or not content:
            return 100.0

        score = 50.0  # Base score

        # Check if response references tool usage
        tool_indicators = [
            "found",
            "searched",
            "calculated",
            "retrieved",
            "fetched",
            "analyzed",
            "using",
            "based on",
            "according to",
            "result",
        ]

        content_lower = content.lower()
        indicator_count = sum(1 for indicator in tool_indicators if indicator in content_lower)

        if indicator_count > 0:
            score += min(25, indicator_count * 5)  # Up to 25 bonus

        # Check if response is substantive (not just echoing tool calls)
        word_count = len(content.split())
        if word_count > 50:
            score += 15
        elif word_count > 20:
            score += 10
        elif word_count < 10:
            score -= 15  # Too brief to integrate results

        # Penalty if response just lists tool calls without integration
        if content.count("tool_call") > len(tool_calls):
            score -= 20  # Over-mentioning tools

        return min(100.0, max(0.0, score))

    def _score_tool_efficiency(
        self,
        tool_calls: list[dict],
        tools: list[dict[str, Any]],
    ) -> float:
        """Score efficiency of tool usage (0-100)."""
        if not tool_calls:
            return 100.0

        score = 50.0

        # Ideal: 1-3 tool calls
        call_count = len(tool_calls)
        if call_count <= 3:
            score += 30
        elif call_count <= 5:
            score += 20
        elif call_count <= 7:
            score += 10
        else:
            score -= 10  # Too many calls

        # Check for duplicate calls (inefficient)
        call_signatures = []
        for call in tool_calls:
            tool_name = call.get("name") or call.get("function", {}).get("name")
            arguments = call.get("arguments") or call.get("function", {}).get("arguments")
            # Simple signature: name + sorted arg keys
            if tool_name and isinstance(arguments, dict):
                sig = f"{tool_name}:{','.join(sorted(arguments.keys()))}"
                call_signatures.append(sig)

        # Penalty for duplicate calls
        if len(call_signatures) != len(set(call_signatures)):
            duplicates = len(call_signatures) - len(set(call_signatures))
            score -= duplicates * 15

        # Bonus for concise, targeted tool use
        if call_count == 1:
            score += 20  # Single precise call

        return min(100.0, max(0.0, score))


# =============================================================================
# LRU Cache (Enterprise Hardening)
# =============================================================================


class LRUHistory:
    """
    LRU cache for Round Table history.

    Enterprise hardening: Prevents memory leak from unbounded history growth.
    Maintains fixed-size cache with least-recently-used eviction policy.

    Args:
        maxsize: Maximum number of entries (default: 1000)
    """

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self.cache: OrderedDict[str, RoundTableResult] = OrderedDict()

    def add(self, result: RoundTableResult) -> None:
        """
        Add result to cache, evicting oldest if full.

        Args:
            result: Round table result to cache
        """
        # Remove if exists (to update access order)
        if result.id in self.cache:
            del self.cache[result.id]

        # Add to end (most recent)
        self.cache[result.id] = result

        # Evict oldest if over limit
        if len(self.cache) > self.maxsize:
            oldest_key = next(iter(self.cache))
            evicted = self.cache.pop(oldest_key)
            logger.debug(
                f"LRU cache evicted oldest result: {evicted.result_id} "
                f"(cache size: {len(self.cache)}/{self.maxsize})"
            )

    def get(self, result_id: str) -> RoundTableResult | None:
        """
        Get result by ID, updating access order.

        Args:
            result_id: Result identifier

        Returns:
            Result if found, None otherwise
        """
        if result_id not in self.cache:
            return None

        # Move to end (most recent)
        self.cache.move_to_end(result_id)
        return self.cache[result_id]

    def get_all(self) -> list[RoundTableResult]:
        """Get all cached results (most recent first)."""
        return list(reversed(self.cache.values()))

    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()

    def __len__(self) -> int:
        """Get cache size."""
        return len(self.cache)


# =============================================================================
# LLM Round Table
# =============================================================================


class LLMRoundTable:
    """LLM Round Table Competition System.

    All registered LLMs compete on every task:
    1. Parallel generation from all LLMs
    2. Scoring on 5 metrics
    3. Top 2 go to A/B testing
    4. Judge determines winner
    5. Results persisted to database

    Example:
        round_table = LLMRoundTable()
        await round_table.initialize()

        # Register providers
        round_table.register_provider(LLMProvider.CLAUDE, claude_generator)
        round_table.register_provider(LLMProvider.GPT4, gpt4_generator)

        # Run competition
        result = await round_table.compete("Write product description")
        print(f"Winner: {result.winner.provider}")
    """

    def __init__(
        self,
        db_url: str | None = None,
        enable_ml_scoring: bool = True,
        enable_adaptive_learning: bool = True,
        enable_statistical_analysis: bool = True,
    ):
        """Initialize Round Table with configuration.

        Args:
            db_url: Database connection string, defaults to DATABASE_URL env var.
            enable_ml_scoring: Enable ML-based evaluation metrics.
            enable_adaptive_learning: Enable provider profiling and adaptive selection.
            enable_statistical_analysis: Enable Bayesian analysis for A/B tests.
        """
        self._providers: dict[LLMProvider, Callable] = {}
        self._judge_provider: LLMProvider = LLMProvider.CLAUDE
        self._scorer = ResponseScorer(enable_ml_scoring=enable_ml_scoring)
        self._db = RoundTableDatabase(db_url)
        # Enterprise hardening: LRU cache prevents unbounded memory growth
        self._history: LRUHistory = LRUHistory(maxsize=1000)
        self._initialized = False

        # Statistical analysis and adaptive learning
        self._enable_adaptive_learning = enable_adaptive_learning
        self._enable_statistical_analysis = enable_statistical_analysis
        self._adaptive_engine = AdaptiveLearningEngine() if enable_adaptive_learning else None
        self._statistical_analyzer = StatisticalAnalyzer() if enable_statistical_analysis else None

    async def initialize(self) -> None:
        """Initialize Round Table, database, and ML models."""
        await self._db.initialize()
        await self._scorer.initialize()  # Initialize ML models
        self._initialized = True

        # Set system info for Prometheus metrics
        set_system_info(
            version="3.0.0",
            providers=[p.value for p in self._providers],
            ml_enabled=self._scorer.enable_ml_scoring,
        )

        logger.info(
            f"LLM Round Table initialized with {len(self._providers)} providers, "
            f"ML scoring: {self._scorer.enable_ml_scoring}, "
            f"Adaptive learning: {self._enable_adaptive_learning}"
        )

    def register_provider(
        self, provider: LLMProvider, generator: Callable[[str, dict | None], Any]
    ) -> None:
        """Register an LLM provider.

        Args:
            provider: Provider enum value
            generator: Async function that takes (prompt, context) and returns response.
        """
        self._providers[provider] = generator
        logger.info(f"Registered provider: {provider.value}")

    def set_judge(self, provider: LLMProvider) -> None:
        """Set the judge provider for A/B testing."""
        self._judge_provider = provider

    @property
    def registered_providers(self) -> list[LLMProvider]:
        """Get list of registered providers."""
        return list(self._providers.keys())

    async def compete(
        self,
        prompt: str,
        task_id: str | None = None,
        providers: list[LLMProvider] | None = None,
        context: dict | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
        persist: bool = True,
    ) -> RoundTableResult:
        """Run Round Table competition with optional tool calling.

        Args:
            prompt: The task prompt
            task_id: Optional task identifier
            providers: Providers to include (default: all registered)
            context: Additional context for generation
            tools: Optional tools for LLM tool calling
            tool_choice: Tool choice strategy ("auto", "required", "none")
            persist: Whether to save to database

        Returns:
            RoundTableResult with winner and all entries
        """
        start_time = time.time()
        result_id = str(uuid4())
        task_id = task_id or f"task_{int(time.time())}"
        prompt_hash = hashlib.md5(prompt.encode(), usedforsecurity=False).hexdigest()

        # Use specified providers or all registered
        active_providers = providers or list(self._providers.keys())

        if not active_providers:
            raise ValueError("No providers registered for competition")

        logger.info(f"Starting Round Table with {len(active_providers)} providers")

        # Track active competitions metric
        active_competitions.inc()

        try:
            # Phase 1: Generate responses from all providers
            entries = await self._generate_all(
                prompt, active_providers, context, tools, tool_choice
            )

            if not entries:
                return self._create_failed_result(
                    result_id,
                    task_id,
                    prompt,
                    prompt_hash,
                    "No providers generated responses",
                    start_time,
                )

            # Phase 2: Score all responses
            scored_entries = await self._score_all(entries, prompt, context, tools)

            # Phase 3: Rank and select top 2
            # Handle None scores (failed providers) by treating them as 0
            ranked_entries = sorted(
                scored_entries,
                key=lambda e: e.total_score if e.total_score is not None else 0.0,
                reverse=True,
            )
            for i, entry in enumerate(ranked_entries):
                entry.rank = i + 1

            top_two = ranked_entries[:2]

            # Phase 4: A/B test between top 2
            ab_result = None
            if len(top_two) >= 2:
                ab_result = await self._ab_test(prompt, top_two)
                winner = ab_result.winner
            else:
                winner = top_two[0]

            # Calculate totals with guards for None values
            total_duration_ms = (time.time() - start_time) * 1000
            total_cost_usd = sum(
                (e.response.cost_usd or 0.0) if e.response else 0.0 for e in entries
            )

            # Create result
            result = RoundTableResult(
                id=result_id,
                task_id=task_id,
                prompt=prompt,
                prompt_hash=prompt_hash,
                entries=ranked_entries,
                top_two=top_two,
                ab_test=ab_result,
                winner=winner,
                status=CompetitionStatus.COMPLETED,
                total_duration_ms=total_duration_ms,
                total_cost_usd=total_cost_usd,
            )

            # Persist to database
            if persist and self._db._initialized:
                await self._db.save_result(result)

            # Add to in-memory history (LRU cache handles eviction automatically)
            self._history.add(result)

            # Record competition metrics
            task_category = context.get("category", "unknown") if context else "unknown"
            record_competition(
                duration_seconds=total_duration_ms / 1000,
                task_category=task_category,
                provider_count=len(active_providers),
            )

            # Record provider results and update adaptive learning
            for entry in ranked_entries:
                won = entry == winner
                entry_score = entry.total_score if entry.total_score is not None else 0.0
                record_provider_result(
                    provider=entry.provider.value,
                    won=won,
                    score=entry_score,
                    latency_ms=entry.response.latency_ms,
                    cost_usd=entry.response.cost_usd,
                    task_category=task_category,
                )

                # Update adaptive learning
                if self._adaptive_engine:
                    await self._adaptive_engine.update_from_competition(
                        provider=entry.provider.value,
                        won=won,
                        score=entry_score,
                        latency_ms=entry.response.latency_ms,
                        cost=entry.response.cost_usd,
                        category=task_category,
                    )

                # Record scoring components
                scores_dict = {
                    "relevance": entry.scores.relevance,
                    "quality": entry.scores.quality,
                    "completeness": entry.scores.completeness,
                    "efficiency": entry.scores.efficiency,
                    "brand_alignment": entry.scores.brand_alignment,
                    "tool_usage_quality": entry.scores.tool_usage_quality,
                    "coherence": entry.scores.coherence,
                    "factuality": entry.scores.factuality,
                    "hallucination_risk": entry.scores.hallucination_risk,
                    "safety": entry.scores.safety,
                }
                record_scoring_components(entry.provider.value, scores_dict)

            winner_score = winner.total_score if winner.total_score is not None else 0.0
            logger.info(
                f"Round Table completed: Winner={winner.provider.value}, "
                f"Score={winner_score:.2f}, Duration={total_duration_ms:.0f}ms"
            )

            return result
        finally:
            # Decrement active competitions
            active_competitions.dec()

    async def _generate_all(
        self,
        prompt: str,
        providers: list[LLMProvider],
        context: dict | None,
        tools: list[dict[str, Any]] | None,
        tool_choice: str,
    ) -> list[RoundTableEntry]:
        """Generate responses from all providers in parallel with optional tools."""
        entries = []

        async def generate_one(provider: LLMProvider) -> RoundTableEntry | None:
            generator = self._providers.get(provider)
            if not generator:
                return None

            start = time.time()
            try:
                # Call generator with tools if provided
                if tools:
                    result = await generator(prompt, context, tools=tools, tool_choice=tool_choice)
                else:
                    result = await generator(prompt, context)
                latency = (time.time() - start) * 1000

                # Handle different response formats
                if isinstance(result, dict):
                    content = result.get("content") or result.get("text") or str(result)
                    tokens = result.get("total_tokens", 0) or result.get("tokens_used", 0)
                    cost = result.get("cost_usd") or 0.0
                    model = result.get("model", "")
                elif hasattr(result, "content"):
                    content = result.content
                    # CompletionResponse uses total_tokens, not tokens_used
                    tokens = getattr(result, "total_tokens", 0) or getattr(result, "tokens_used", 0)
                    cost = getattr(result, "cost_usd", None) or 0.0
                    model = getattr(result, "model", "")
                else:
                    content = str(result)
                    tokens = 0
                    cost = 0.0
                    model = ""

                response = LLMResponse(
                    provider=provider,
                    content=content,
                    latency_ms=latency,
                    tokens_used=tokens,
                    cost_usd=cost,
                    model=model,
                )

                return RoundTableEntry(provider=provider, response=response)

            except Exception as e:
                logger.error(f"Provider {provider.value} failed: {e}")
                latency = (time.time() - start) * 1000
                response = LLMResponse(
                    provider=provider,
                    content="",
                    latency_ms=latency,
                    error=str(e),
                )
                return RoundTableEntry(provider=provider, response=response)

        # Run all generators concurrently
        tasks = [generate_one(p) for p in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, RoundTableEntry) and not result.response.error:
                entries.append(result)

        return entries

    async def _score_all(
        self,
        entries: list[RoundTableEntry],
        prompt: str,
        context: dict | None,
        tools: list[dict[str, Any]] | None,
    ) -> list[RoundTableEntry]:
        """Score all entries with optional tool usage and ML-based evaluation."""
        for entry in entries:
            entry.scores = await self._scorer.score_response(entry.response, prompt, context, tools)
        return entries

    async def _ab_test(self, prompt: str, top_two: list[RoundTableEntry]) -> ABTestResult:
        """A/B test between top 2 entries with statistical analysis."""
        entry_a, entry_b = top_two[0], top_two[1]

        # Statistical analysis using historical data
        p_value = None
        effect_size = None
        bayesian_prob = None
        is_significant = False

        if self._statistical_analyzer and len(self._history) >= 10:
            # Gather historical scores for both providers (filter out None values)
            scores_a = [
                e.total_score
                for result in self._history[-50:]  # Last 50 competitions
                for e in result.entries
                if e.provider == entry_a.provider and e.total_score is not None
            ]
            scores_b = [
                e.total_score
                for result in self._history[-50:]
                for e in result.entries
                if e.provider == entry_b.provider and e.total_score is not None
            ]

            # Run statistical analysis if enough samples
            if len(scores_a) >= 3 and len(scores_b) >= 3:
                try:
                    stat_result = self._statistical_analyzer.analyze_ab_test(
                        scores_a=scores_a,
                        scores_b=scores_b,
                        provider_a=entry_a.provider.value,
                        provider_b=entry_b.provider.value,
                    )
                    p_value = stat_result.p_value
                    effect_size = stat_result.effect_size
                    bayesian_prob = stat_result.bayesian_probability
                    is_significant = stat_result.is_significant

                    logger.info(
                        f"Statistical analysis: {entry_a.provider.value} vs {entry_b.provider.value}, "
                        f"p={p_value:.4f}, effect={effect_size:.3f}, "
                        f"significant={is_significant}"
                    )

                    # Record AB test metrics
                    record_ab_test(
                        provider_a=entry_a.provider.value,
                        provider_b=entry_b.provider.value,
                        p_value=p_value,
                        effect_size=effect_size,
                        winner=stat_result.winner,
                    )
                except Exception as e:
                    logger.warning(f"Statistical analysis failed: {e}")

        # Create judge prompt
        judge_prompt = f"""You are judging a competition between two AI responses.

ORIGINAL PROMPT:
{prompt[:1000]}

RESPONSE A ({entry_a.provider.value}):
{entry_a.response.content[:2000]}

RESPONSE B ({entry_b.provider.value}):
{entry_b.response.content[:2000]}

Evaluate both responses on:
1. Accuracy and correctness
2. Completeness of answer
3. Clarity and structure
4. Practical usefulness

Respond in this exact format:
WINNER: A or B
CONFIDENCE: 0.0 to 1.0
REASONING: Your detailed explanation."""

        # Get judge's decision
        judge_generator = self._providers.get(self._judge_provider)
        confidence = 0.5
        reasoning = "Fallback to scores"
        score_a = entry_a.total_score if entry_a.total_score is not None else 0.0
        score_b = entry_b.total_score if entry_b.total_score is not None else 0.0
        winner = entry_a if score_a >= score_b else entry_b

        if judge_generator:
            try:
                result = await judge_generator(judge_prompt, None)

                if isinstance(result, dict):
                    judge_content = result.get("content") or result.get("text") or ""
                elif hasattr(result, "content"):
                    judge_content = result.content
                else:
                    judge_content = str(result)

                # Parse winner
                if "WINNER: A" in judge_content.upper():
                    winner = entry_a
                elif "WINNER: B" in judge_content.upper():
                    winner = entry_b

                # Parse confidence
                if "CONFIDENCE:" in judge_content.upper():
                    try:
                        conf_line = [
                            line
                            for line in judge_content.split("\n")
                            if "CONFIDENCE:" in line.upper()
                        ][0]
                        confidence = float(conf_line.split(":")[-1].strip())
                    except (ValueError, IndexError):
                        pass

                # Parse reasoning
                if "REASONING:" in judge_content.upper():
                    try:
                        reasoning = judge_content.split("REASONING:")[-1].strip()
                    except (ValueError, IndexError):
                        reasoning = judge_content

            except Exception as e:
                logger.error(f"Judge evaluation failed: {e}")

        return ABTestResult(
            entry_a=entry_a,
            entry_b=entry_b,
            winner=winner,
            judge_provider=self._judge_provider,
            judge_reasoning=reasoning,
            confidence=confidence,
            statistical_p_value=p_value,
            statistical_effect_size=effect_size,
            bayesian_probability=bayesian_prob,
            is_statistically_significant=is_significant,
        )

    def _create_failed_result(
        self,
        result_id: str,
        task_id: str,
        prompt: str,
        prompt_hash: str,
        error: str,
        start_time: float,
    ) -> RoundTableResult:
        """Create a failed result."""
        return RoundTableResult(
            id=result_id,
            task_id=task_id,
            prompt=prompt,
            prompt_hash=prompt_hash,
            entries=[],
            top_two=[],
            ab_test=None,
            winner=None,
            status=CompetitionStatus.FAILED,
            total_duration_ms=(time.time() - start_time) * 1000,
            total_cost_usd=0.0,
        )

    # =========================================================================
    # Analytics and History
    # =========================================================================

    def get_history(self, limit: int = 100) -> list[RoundTableResult]:
        """Get recent competition history from memory (LRU cache)."""
        all_results = self._history.get_all()  # Most recent first
        return all_results[:limit]

    async def get_database_history(
        self, limit: int = 100, task_id: str | None = None
    ) -> list[dict]:
        """Get competition history from database."""
        return await self._db.get_history(limit, task_id)

    async def get_provider_stats(self) -> dict[str, dict]:
        """Get aggregated statistics per provider."""
        # Try database first
        db_stats = await self._db.get_provider_stats()
        if db_stats:
            return db_stats

        # Fallback to in-memory stats
        stats: dict[str, dict] = {
            p.value: {"wins": 0, "total": 0, "avg_score": 0.0, "total_score": 0.0}
            for p in LLMProvider
        }

        for result in self._history:
            if result.status == CompetitionStatus.COMPLETED:
                # Count participation
                for entry in result.entries:
                    p = entry.provider.value
                    stats[p]["total"] += 1
                    # Guard against None total_score
                    score = entry.total_score if entry.total_score is not None else 0.0
                    stats[p]["total_score"] += score

                # Count win
                if result.winner:
                    stats[result.winner.provider.value]["wins"] += 1

        # Calculate averages
        for _p, s in stats.items():
            if s["total"] > 0:
                s["avg_score"] = s["total_score"] / s["total"]
            del s["total_score"]

        return stats

    async def close(self) -> None:
        """Close database connection."""
        await self._db.close()


# =============================================================================
# Factory and Exports
# =============================================================================


async def create_round_table(db_url: str | None = None) -> LLMRoundTable:
    """Factory function to create and initialize a Round Table."""
    rt = LLMRoundTable(db_url)
    await rt.initialize()
    return rt


__all__ = [
    # Enums
    "LLMProvider",
    "CompetitionStatus",
    # Data classes
    "LLMResponse",
    "ResponseScores",
    "RoundTableEntry",
    "ABTestResult",
    "RoundTableResult",
    # Classes
    "RoundTableDatabase",
    "ResponseScorer",
    "LLMRoundTable",
    # Factory
    "create_round_table",
]
