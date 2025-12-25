"""
Tournament-Style LLM Consensus
==============================

Multi-LLM tournament selection for highest quality responses.

Process:
1. Round 1: Parallel generation from all available LLMs
2. Round 2: Quality scoring (coherence, accuracy, brand alignment)
3. Round 3: Head-to-head judge comparison of top 2

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from llm.base import CompletionResponse, Message
from llm.router import LLMRouter, ModelProvider

# Alias for clarity
ModelResponse = CompletionResponse

logger = logging.getLogger(__name__)


# =============================================================================
# Response Scoring
# =============================================================================


@dataclass(slots=True)
class ResponseScore:
    """Quality scores for an LLM response. Memory-optimized with __slots__."""

    provider: ModelProvider
    model: str
    response: ModelResponse

    # Scores (0-100)
    coherence: float = 0.0
    accuracy: float = 0.0
    brand_alignment: float = 0.0
    task_completion: float = 0.0

    # Computed
    total_score: float = field(init=False)
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        # Weighted average
        self.total_score = (
            self.coherence * 0.25
            + self.accuracy * 0.30
            + self.brand_alignment * 0.20
            + self.task_completion * 0.25
        )


@dataclass(slots=True)
class TournamentResult:
    """Result of a tournament. Memory-optimized with __slots__."""

    winner: ResponseScore
    runner_up: ResponseScore | None = None
    all_scores: list[ResponseScore] = field(default_factory=list)
    confidence: float = 0.0
    judge_reasoning: str = ""
    total_duration_ms: float = 0.0


class ResponseScorer:
    """
    Scores LLM responses on quality metrics.

    Uses heuristics for fast scoring, optionally uses judge LLM for accuracy.
    """

    def __init__(
        self, use_judge: bool = False, judge_provider: ModelProvider = ModelProvider.ANTHROPIC
    ):
        self.use_judge = use_judge
        self.judge_provider = judge_provider
        self.router = LLMRouter() if use_judge else None

    def score_coherence(self, response: ModelResponse) -> float:
        """Score logical flow and readability (0-100)."""
        content = response.content or ""

        if not content.strip():
            return 0.0

        score = 50.0  # Base score

        # Length checks
        word_count = len(content.split())
        if 10 <= word_count <= 500:
            score += 20
        elif word_count > 500:
            score += 10

        # Structure indicators
        if any(c in content for c in [".", "!", "?"]):
            score += 10  # Has sentence endings
        if "\n" in content:
            score += 5  # Has paragraphs
        if any(content.startswith(p) for p in ["1.", "- ", "* ", "##"]):
            score += 5  # Has structure

        # Penalize issues
        if content.count("...") > 3:
            score -= 10
        if "error" in content.lower() or "sorry" in content.lower():
            score -= 15

        return min(100.0, max(0.0, score))

    def score_task_completion(self, response: ModelResponse, task_hint: str = "") -> float:
        """Score how well the response completes the task (0-100)."""
        content = response.content or ""

        if not content.strip():
            return 0.0

        score = 60.0  # Base score for non-empty response

        # Check for code if task mentions code
        if any(kw in task_hint.lower() for kw in ["code", "function", "class", "implement"]):
            if "```" in content or "def " in content or "class " in content:
                score += 25
            else:
                score -= 20

        # Check for descriptions if task mentions describe
        if "descri" in task_hint.lower() and len(content) > 100:
            score += 20

        # Length heuristic
        if len(content) > 50:
            score += 10

        return min(100.0, max(0.0, score))

    def score_brand_alignment(self, response: ModelResponse) -> float:
        """Score adherence to SkyyRose brand voice (0-100)."""
        content = response.content or ""
        content_lower = content.lower()

        score = 50.0  # Neutral base

        # Positive brand keywords
        brand_positive = [
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
        ]
        for kw in brand_positive:
            if kw in content_lower:
                score += 5

        # Negative/avoid keywords
        brand_negative = ["cheap", "discount", "basic", "simple", "ordinary", "generic"]
        for kw in brand_negative:
            if kw in content_lower:
                score -= 10

        return min(100.0, max(0.0, score))

    async def score_accuracy_with_judge(
        self,
        response: ModelResponse,
        original_prompt: str,
    ) -> tuple[float, str]:
        """Use judge LLM to score accuracy. Returns (score, reasoning)."""
        if not self.router:
            return 70.0, "Judge not enabled"

        judge_prompt = f"""Score the following response for accuracy and quality.

Original request: {original_prompt}

Response to evaluate:
{response.content}

Provide a score from 0-100 and brief reasoning.
Format: SCORE: [number]
REASONING: [brief explanation]"""

        try:
            judge_response = await self.router.complete(
                messages=[Message.user(judge_prompt)],
                provider=self.judge_provider,
                max_tokens=200,
            )

            # Parse score from response
            content = judge_response.content
            if "SCORE:" in content:
                score_line = content.split("SCORE:")[1].split("\n")[0]
                score = float("".join(c for c in score_line if c.isdigit() or c == "."))
                reasoning = (
                    content.split("REASONING:")[-1].strip() if "REASONING:" in content else ""
                )
                return min(100.0, max(0.0, score)), reasoning

            return 70.0, "Could not parse judge response"
        except Exception as e:
            logger.warning(f"Judge scoring failed: {e}")
            return 70.0, f"Judge error: {e}"

    async def score_response(
        self,
        response: ModelResponse,
        provider: ModelProvider,
        task_hint: str = "",
        original_prompt: str = "",
    ) -> ResponseScore:
        """Generate full score for a response."""
        coherence = self.score_coherence(response)
        task_completion = self.score_task_completion(response, task_hint)
        brand_alignment = self.score_brand_alignment(response)

        # Accuracy - use judge if enabled
        if self.use_judge and original_prompt:
            accuracy, _ = await self.score_accuracy_with_judge(response, original_prompt)
        else:
            accuracy = 70.0  # Default moderate accuracy

        return ResponseScore(
            provider=provider,
            model=response.model,
            response=response,
            coherence=coherence,
            accuracy=accuracy,
            brand_alignment=brand_alignment,
            task_completion=task_completion,
            latency_ms=response.latency_ms,
        )


# =============================================================================
# Tournament Orchestrator
# =============================================================================


class LLMTournament:
    """
    Tournament-style LLM selection.

    Usage:
        tournament = LLMTournament()

        result = await tournament.run(
            messages=[Message.user("Write a product description...")],
            task_hint="product_description",
        )

        print(f"Winner: {result.winner.provider.value}")
        print(f"Response: {result.winner.response.content}")
    """

    DEFAULT_PROVIDERS = [
        ModelProvider.OPENAI,
        ModelProvider.ANTHROPIC,
        ModelProvider.GOOGLE,
        ModelProvider.MISTRAL,
        ModelProvider.GROQ,
        ModelProvider.COHERE,
    ]

    def __init__(
        self,
        providers: list[ModelProvider] | None = None,
        use_judge: bool = True,
        judge_provider: ModelProvider = ModelProvider.ANTHROPIC,
        timeout_seconds: float = 30.0,
    ):
        self.providers = providers or self.DEFAULT_PROVIDERS
        self.timeout = timeout_seconds
        self.router = LLMRouter()
        self.scorer = ResponseScorer(use_judge=use_judge, judge_provider=judge_provider)

    async def _generate_round_1(
        self,
        messages: list[Message],
        **kwargs: Any,
    ) -> list[tuple[ModelProvider, ModelResponse | Exception]]:
        """Round 1: Parallel generation from all providers."""

        async def generate_one(
            provider: ModelProvider,
        ) -> tuple[ModelProvider, ModelResponse | Exception]:
            try:
                response = await asyncio.wait_for(
                    self.router.complete(messages=messages, provider=provider, **kwargs),
                    timeout=self.timeout,
                )
                return (provider, response)
            except Exception as e:
                logger.warning(f"{provider.value} failed: {e}")
                return (provider, e)

        tasks = [generate_one(p) for p in self.providers]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def _score_round_2(
        self,
        responses: list[tuple[ModelProvider, ModelResponse]],
        task_hint: str = "",
        original_prompt: str = "",
    ) -> list[ResponseScore]:
        """Round 2: Score all responses."""
        scores = []
        for provider, response in responses:
            score = await self.scorer.score_response(response, provider, task_hint, original_prompt)
            scores.append(score)
            logger.info(
                f"{provider.value}: total={score.total_score:.1f} "
                f"(coh={score.coherence:.0f}, acc={score.accuracy:.0f}, "
                f"brand={score.brand_alignment:.0f}, task={score.task_completion:.0f})"
            )

        # Sort by total score
        scores.sort(key=lambda s: s.total_score, reverse=True)
        return scores

    async def _judge_round_3(
        self,
        top_2: list[ResponseScore],
        original_prompt: str,
    ) -> tuple[ResponseScore, float, str]:
        """Round 3: Head-to-head comparison of top 2."""
        if len(top_2) < 2:
            return top_2[0], 0.9, "Only one valid response"

        a, b = top_2[0], top_2[1]

        judge_prompt = f"""Compare these two responses and pick the better one.

Original request: {original_prompt}

Response A ({a.provider.value}):
{a.response.content[:1000]}

Response B ({b.provider.value}):
{b.response.content[:1000]}

Which is better? Reply with:
WINNER: A or B
CONFIDENCE: 0.0-1.0
REASONING: [brief explanation]"""

        try:
            judge_response = await self.router.complete(
                messages=[Message.user(judge_prompt)],
                provider=ModelProvider.ANTHROPIC,
                max_tokens=300,
            )

            content = judge_response.content
            winner = a if "WINNER: A" in content.upper() else b

            confidence = 0.75
            if "CONFIDENCE:" in content:
                conf_line = content.split("CONFIDENCE:")[1].split("\n")[0]
                with contextlib.suppress(ValueError):
                    confidence = float("".join(c for c in conf_line if c.isdigit() or c == "."))

            reasoning = ""
            if "REASONING:" in content:
                reasoning = content.split("REASONING:")[-1].strip()[:200]

            return winner, confidence, reasoning

        except Exception as e:
            logger.warning(f"Judge comparison failed: {e}")
            # Fall back to score-based decision
            return a, 0.6, f"Judge failed, using scores: {e}"

    async def run(
        self,
        messages: list[Message],
        task_hint: str = "",
        skip_judge: bool = False,
        **kwargs: Any,
    ) -> TournamentResult:
        """
        Run full tournament.

        Args:
            messages: Chat messages
            task_hint: Hint about task type for scoring
            skip_judge: Skip Round 3 judge comparison
            **kwargs: Additional args for LLM

        Returns:
            TournamentResult with winner and metadata
        """
        start = time.time()
        original_prompt = messages[-1].content if messages else ""

        logger.info(f"🏆 Tournament starting with {len(self.providers)} providers")

        # Round 1: Parallel generation
        logger.info("Round 1: Parallel generation...")
        round_1_results = await self._generate_round_1(messages, **kwargs)

        # Filter successful responses
        valid_responses = [
            (provider, resp)
            for provider, resp in round_1_results
            if isinstance(resp, ModelResponse)
        ]

        if not valid_responses:
            raise RuntimeError("All providers failed in Round 1")

        logger.info(f"Round 1 complete: {len(valid_responses)}/{len(self.providers)} succeeded")

        # Round 2: Scoring
        logger.info("Round 2: Quality scoring...")
        scores = await self._score_round_2(valid_responses, task_hint, original_prompt)

        # Round 3: Judge (optional)
        if not skip_judge and len(scores) >= 2:
            logger.info("Round 3: Head-to-head judge...")
            winner, confidence, reasoning = await self._judge_round_3(scores[:2], original_prompt)
            runner_up = scores[1] if winner == scores[0] else scores[0]
        else:
            winner = scores[0]
            runner_up = scores[1] if len(scores) > 1 else None
            confidence = 0.8
            reasoning = "Based on quality scores"

        duration = (time.time() - start) * 1000

        logger.info(f"🏆 Winner: {winner.provider.value} (confidence: {confidence:.2f})")

        return TournamentResult(
            winner=winner,
            runner_up=runner_up,
            all_scores=scores,
            confidence=confidence,
            judge_reasoning=reasoning,
            total_duration_ms=duration,
        )

    async def close(self) -> None:
        """Close resources."""
        await self.router.close()
        if self.scorer.router:
            await self.scorer.router.close()


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    "LLMTournament",
    "ResponseScorer",
    "ResponseScore",
    "TournamentResult",
]
