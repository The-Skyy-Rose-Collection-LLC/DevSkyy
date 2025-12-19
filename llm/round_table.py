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
Version: 2.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Types
# =============================================================================


class LLMProvider(str, Enum):
    """LLM providers participating in Round Table"""
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    LLAMA = "llama"
    MISTRAL = "mistral"
    COHERE = "cohere"


class CompetitionStatus(str, Enum):
    """Status of a Round Table competition"""
    PENDING = "pending"
    GENERATING = "generating"
    SCORING = "scoring"
    AB_TESTING = "ab_testing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class LLMResponse:
    """Response from an LLM provider"""
    provider: LLMProvider
    content: str
    latency_ms: float
    tokens_used: int = 0
    cost_usd: float = 0.0
    model: str = ""
    error: str | None = None


@dataclass
class ResponseScores:
    """Scoring breakdown for a response"""
    relevance: float = 0.0       # How relevant to the prompt
    quality: float = 0.0         # Overall output quality
    completeness: float = 0.0    # Task completion
    efficiency: float = 0.0      # Token/cost efficiency
    brand_alignment: float = 0.0 # Brand voice adherence

    @property
    def total(self) -> float:
        """Weighted total score"""
        return (
            self.relevance * 0.25 +
            self.quality * 0.25 +
            self.completeness * 0.20 +
            self.efficiency * 0.15 +
            self.brand_alignment * 0.15
        )


@dataclass
class RoundTableEntry:
    """Entry in the Round Table competition"""
    provider: LLMProvider
    response: LLMResponse
    scores: ResponseScores = field(default_factory=ResponseScores)
    rank: int = 0

    @property
    def total_score(self) -> float:
        return self.scores.total


@dataclass
class ABTestResult:
    """Result from A/B testing between top 2"""
    entry_a: RoundTableEntry
    entry_b: RoundTableEntry
    winner: RoundTableEntry
    judge_provider: LLMProvider
    judge_reasoning: str
    confidence: float
    tested_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class RoundTableResult:
    """Complete result from a Round Table competition"""
    id: str
    task_id: str
    prompt: str
    prompt_hash: str
    entries: list[RoundTableEntry]
    top_two: list[RoundTableEntry]
    ab_test: ABTestResult | None
    winner: RoundTableEntry
    status: CompetitionStatus
    total_duration_ms: float
    total_cost_usd: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    persisted: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "prompt_hash": self.prompt_hash,
            "prompt_preview": self.prompt[:500],
            "winner_provider": self.winner.provider.value,
            "winner_score": self.winner.total_score,
            "runner_up_provider": self.top_two[1].provider.value if len(self.top_two) > 1 else None,
            "runner_up_score": self.top_two[1].total_score if len(self.top_two) > 1 else None,
            "all_scores": {
                e.provider.value: {
                    "total": e.total_score,
                    "latency_ms": e.response.latency_ms,
                    "cost_usd": e.response.cost_usd
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
    """
    Database persistence for Round Table results.

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
        ON round_table_results(task_id);
    """

    def __init__(self, connection_string: str | None = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self._pool = None
        self._initialized = False

    async def initialize(self):
        """Initialize database connection and schema"""
        if not self.connection_string:
            logger.warning("No database connection string configured")
            return

        try:
            import asyncpg
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10
            )

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
        """Save Round Table result to database"""
        if not self._initialized or not self._pool:
            return False

        try:
            data = result.to_dict()

            async with self._pool.acquire() as conn:
                await conn.execute("""
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
                        total_cost_usd = EXCLUDED.total_cost_usd
                """,
                    data["id"],
                    data["task_id"],
                    data["prompt_hash"],
                    data["prompt_preview"],
                    data["winner_provider"],
                    data["winner_score"],
                    result.winner.response.content[:5000],
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
        """Get a specific Round Table result"""
        if not self._initialized or not self._pool:
            return None

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM round_table_results WHERE id = $1",
                    result_id
                )
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get result: {e}")
            return None

    async def get_history(
        self,
        limit: int = 100,
        task_id: str | None = None,
        provider: str | None = None
    ) -> list[dict]:
        """Get Round Table history"""
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
        """Get aggregated statistics per provider"""
        if not self._initialized or not self._pool:
            return {}

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT
                        winner_provider,
                        COUNT(*) as wins,
                        AVG(winner_score) as avg_score,
                        AVG(total_duration_ms) as avg_latency,
                        AVG(total_cost_usd) as avg_cost
                    FROM round_table_results
                    WHERE status = 'completed'
                    GROUP BY winner_provider
                    ORDER BY wins DESC
                """)

                return {
                    row["winner_provider"]: {
                        "wins": row["wins"],
                        "avg_score": float(row["avg_score"]),
                        "avg_latency_ms": float(row["avg_latency"]),
                        "avg_cost_usd": float(row["avg_cost"])
                    }
                    for row in rows
                }

        except Exception as e:
            logger.error(f"Failed to get provider stats: {e}")
            return {}

    async def close(self):
        """Close database connection"""
        if self._pool:
            await self._pool.close()


# =============================================================================
# Response Scorer
# =============================================================================


class ResponseScorer:
    """Scores LLM responses on quality metrics"""

    # Brand-positive keywords for SkyyRose
    BRAND_POSITIVE = [
        "luxury", "premium", "elegant", "sophisticated", "rose", "gold",
        "exclusive", "limited", "quality", "crafted", "timeless", "love",
        "oakland", "street", "elevated", "refined", "meticulous"
    ]

    # Brand-negative keywords to avoid
    BRAND_NEGATIVE = [
        "cheap", "discount", "basic", "simple", "ordinary", "generic",
        "budget", "low-cost", "mass-produced"
    ]

    def score_response(
        self,
        response: LLMResponse,
        prompt: str,
        task_context: dict | None = None
    ) -> ResponseScores:
        """Score a response on all metrics"""
        content = response.content or ""

        if not content.strip() or response.error:
            return ResponseScores()

        return ResponseScores(
            relevance=self._score_relevance(content, prompt),
            quality=self._score_quality(content),
            completeness=self._score_completeness(content, prompt, task_context),
            efficiency=self._score_efficiency(response),
            brand_alignment=self._score_brand_alignment(content),
        )

    def _score_relevance(self, content: str, prompt: str) -> float:
        """Score how relevant the response is to the prompt"""
        prompt_words = set(prompt.lower().split())
        content_words = set(content.lower().split())

        # Remove common words
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                      "and", "or", "but", "in", "on", "at", "to", "for", "of"}
        prompt_words -= stop_words
        content_words -= stop_words

        if not prompt_words:
            return 50.0

        overlap = len(prompt_words & content_words)
        score = (overlap / len(prompt_words)) * 100

        return min(100.0, max(0.0, score))

    def _score_quality(self, content: str) -> float:
        """Score overall quality of the response"""
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

    def _score_completeness(
        self,
        content: str,
        prompt: str,
        task_context: dict | None
    ) -> float:
        """Score task completion"""
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
        """Score efficiency based on latency and cost"""
        score = 50.0

        # Latency scoring (ideal: 1-3 seconds)
        if response.latency_ms < 1000:
            score += 25
        elif response.latency_ms < 3000:
            score += 20
        elif response.latency_ms < 5000:
            score += 10
        elif response.latency_ms > 10000:
            score -= 15

        # Cost scoring (ideal: < $0.01)
        if response.cost_usd < 0.005:
            score += 25
        elif response.cost_usd < 0.01:
            score += 20
        elif response.cost_usd < 0.05:
            score += 10
        elif response.cost_usd > 0.10:
            score -= 15

        return min(100.0, max(0.0, score))

    def _score_brand_alignment(self, content: str) -> float:
        """Score adherence to SkyyRose brand voice"""
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


# =============================================================================
# LLM Round Table
# =============================================================================


class LLMRoundTable:
    """
    LLM Round Table Competition System.

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

    def __init__(self, db_url: str | None = None):
        self._providers: dict[LLMProvider, Callable] = {}
        self._judge_provider: LLMProvider = LLMProvider.CLAUDE
        self._scorer = ResponseScorer()
        self._db = RoundTableDatabase(db_url)
        self._history: list[RoundTableResult] = []
        self._initialized = False

    async def initialize(self):
        """Initialize Round Table and database"""
        await self._db.initialize()
        self._initialized = True
        logger.info("LLM Round Table initialized")

    def register_provider(
        self,
        provider: LLMProvider,
        generator: Callable[[str, dict | None], Any]
    ):
        """
        Register an LLM provider.

        Args:
            provider: Provider enum value
            generator: Async function that takes (prompt, context) and returns response
        """
        self._providers[provider] = generator
        logger.info(f"Registered provider: {provider.value}")

    def set_judge(self, provider: LLMProvider):
        """Set the judge provider for A/B testing"""
        self._judge_provider = provider

    @property
    def registered_providers(self) -> list[LLMProvider]:
        """Get list of registered providers"""
        return list(self._providers.keys())

    async def compete(
        self,
        prompt: str,
        task_id: str | None = None,
        providers: list[LLMProvider] | None = None,
        context: dict | None = None,
        persist: bool = True
    ) -> RoundTableResult:
        """
        Run Round Table competition.

        Args:
            prompt: The task prompt
            task_id: Optional task identifier
            providers: Providers to include (default: all registered)
            context: Additional context for generation
            persist: Whether to save to database

        Returns:
            RoundTableResult with winner and all entries
        """
        start_time = time.time()
        result_id = str(uuid4())
        task_id = task_id or f"task_{int(time.time())}"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

        # Use specified providers or all registered
        active_providers = providers or list(self._providers.keys())

        if not active_providers:
            raise ValueError("No providers registered for competition")

        logger.info(f"Starting Round Table with {len(active_providers)} providers")

        # Phase 1: Generate responses from all providers
        entries = await self._generate_all(prompt, active_providers, context)

        if not entries:
            return self._create_failed_result(
                result_id, task_id, prompt, prompt_hash,
                "No providers generated responses", start_time
            )

        # Phase 2: Score all responses
        scored_entries = self._score_all(entries, prompt, context)

        # Phase 3: Rank and select top 2
        ranked_entries = sorted(scored_entries, key=lambda e: e.total_score, reverse=True)
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

        # Calculate totals
        total_duration_ms = (time.time() - start_time) * 1000
        total_cost_usd = sum(e.response.cost_usd for e in entries)

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

        # Add to in-memory history
        self._history.append(result)
        if len(self._history) > 1000:
            self._history = self._history[-1000:]

        logger.info(
            f"Round Table completed: Winner={winner.provider.value}, "
            f"Score={winner.total_score:.2f}, Duration={total_duration_ms:.0f}ms"
        )

        return result

    async def _generate_all(
        self,
        prompt: str,
        providers: list[LLMProvider],
        context: dict | None
    ) -> list[RoundTableEntry]:
        """Generate responses from all providers in parallel"""
        entries = []

        async def generate_one(provider: LLMProvider) -> RoundTableEntry | None:
            generator = self._providers.get(provider)
            if not generator:
                return None

            start = time.time()
            try:
                result = await generator(prompt, context)
                latency = (time.time() - start) * 1000

                # Handle different response formats
                if isinstance(result, dict):
                    content = result.get("content") or result.get("text") or str(result)
                    tokens = result.get("tokens_used", 0)
                    cost = result.get("cost_usd", 0.0)
                    model = result.get("model", "")
                elif hasattr(result, "content"):
                    content = result.content
                    tokens = getattr(result, "tokens_used", 0)
                    cost = getattr(result, "cost_usd", 0.0)
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

    def _score_all(
        self,
        entries: list[RoundTableEntry],
        prompt: str,
        context: dict | None
    ) -> list[RoundTableEntry]:
        """Score all entries"""
        for entry in entries:
            entry.scores = self._scorer.score_response(
                entry.response,
                prompt,
                context
            )
        return entries

    async def _ab_test(
        self,
        prompt: str,
        top_two: list[RoundTableEntry]
    ) -> ABTestResult:
        """A/B test between top 2 entries using judge LLM"""
        entry_a, entry_b = top_two[0], top_two[1]

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
REASONING: Your detailed explanation"""

        # Get judge's decision
        judge_generator = self._providers.get(self._judge_provider)
        confidence = 0.5
        reasoning = "Fallback to scores"
        winner = entry_a if entry_a.total_score >= entry_b.total_score else entry_b

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
                        conf_line = [line for line in judge_content.split("\n")
                                    if "CONFIDENCE:" in line.upper()][0]
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
        )

    def _create_failed_result(
        self,
        result_id: str,
        task_id: str,
        prompt: str,
        prompt_hash: str,
        error: str,
        start_time: float
    ) -> RoundTableResult:
        """Create a failed result"""
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
        """Get recent competition history from memory"""
        return self._history[-limit:]

    async def get_database_history(
        self,
        limit: int = 100,
        task_id: str | None = None
    ) -> list[dict]:
        """Get competition history from database"""
        return await self._db.get_history(limit, task_id)

    async def get_provider_stats(self) -> dict[str, dict]:
        """Get aggregated statistics per provider"""
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
                    stats[p]["total_score"] += entry.total_score

                # Count win
                if result.winner:
                    stats[result.winner.provider.value]["wins"] += 1

        # Calculate averages
        for p, s in stats.items():
            if s["total"] > 0:
                s["avg_score"] = s["total_score"] / s["total"]
            del s["total_score"]

        return stats

    async def close(self):
        """Close database connection"""
        await self._db.close()


# =============================================================================
# Factory and Exports
# =============================================================================


async def create_round_table(db_url: str | None = None) -> LLMRoundTable:
    """Factory function to create and initialize a Round Table"""
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
