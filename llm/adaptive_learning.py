"""Adaptive learning for provider profiling and optimization.

This module learns from Round Table competition history to:
- Build performance profiles for each LLM provider
- Identify provider strengths and weaknesses by task category
- Recommend optimal provider selection for new tasks
- Track performance trends over time

Used to continuously improve Round Table provider routing decisions.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class PerformanceTrend(str, Enum):
    """Provider performance trend classification."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass
class ProviderProfile:
    """Performance profile for an LLM provider.

    Tracks comprehensive metrics to understand provider behavior
    and optimize future selection decisions.

    Attributes:
        provider: Provider identifier
        total_competitions: Total number of competitions participated in
        wins: Number of wins
        win_rate: Percentage of wins (0-1)
        avg_score: Exponential moving average of scores
        avg_latency_ms: Average response latency
        avg_cost_usd: Average cost per request
        strengths: Task categories where provider excels
        weaknesses: Task categories where provider underperforms
        trend: Performance trend (improving/stable/declining)
        last_updated: Timestamp of last profile update
        category_performance: Win rate by task category
    """

    provider: str
    total_competitions: int = 0
    wins: int = 0
    win_rate: float = 0.0
    avg_score: float = 0.0
    avg_latency_ms: float = 0.0
    avg_cost_usd: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    trend: PerformanceTrend = PerformanceTrend.INSUFFICIENT_DATA
    last_updated: datetime = field(default_factory=datetime.now)
    category_performance: dict[str, float] = field(default_factory=dict)

    def update(
        self,
        won: bool,
        score: float,
        latency_ms: float,
        cost: float,
        category: str | None = None,
    ) -> None:
        """Update profile after a competition.

        Uses exponential moving average for smooth metric updates.

        Args:
            won: Whether provider won this competition
            score: Provider's score (0-100)
            latency_ms: Response latency in milliseconds
            cost: Cost in USD
            category: Optional task category for category-specific tracking
        """
        self.total_competitions += 1
        if won:
            self.wins += 1

        self.win_rate = self.wins / self.total_competitions

        # Exponential moving average (alpha=0.1 for smoothing)
        alpha = 0.1
        if self.avg_score == 0.0:
            # First update
            self.avg_score = score
            self.avg_latency_ms = latency_ms
            self.avg_cost_usd = cost
        else:
            self.avg_score = alpha * score + (1 - alpha) * self.avg_score
            self.avg_latency_ms = alpha * latency_ms + (1 - alpha) * self.avg_latency_ms
            self.avg_cost_usd = alpha * cost + (1 - alpha) * self.avg_cost_usd

        # Update category-specific performance
        if category:
            if category not in self.category_performance:
                self.category_performance[category] = 1.0 if won else 0.0
            else:
                # Exponential moving average for category win rate
                current = self.category_performance[category]
                new_value = 1.0 if won else 0.0
                self.category_performance[category] = alpha * new_value + (1 - alpha) * current

        self.last_updated = datetime.now()

    def get_category_rank(self, category: str) -> float:
        """Get win rate for specific category.

        Args:
            category: Task category

        Returns:
            Win rate for category (0-1), or overall win rate if no data
        """
        return self.category_performance.get(category, self.win_rate)


@dataclass
class RecommendationResult:
    """Provider recommendation result.

    Attributes:
        recommended_providers: Ordered list of recommended provider names
        confidence: Confidence in recommendation (0-1)
        reasoning: Human-readable explanation of recommendation
        category_match: Whether recommendation based on category performance
    """

    recommended_providers: list[str]
    confidence: float
    reasoning: str
    category_match: bool = False


class AdaptiveLearningEngine:
    """Learn from competition history to optimize provider selection.

    Maintains performance profiles for all providers and uses
    historical data to make intelligent routing decisions.

    Example:
        engine = AdaptiveLearningEngine()
        await engine.update_from_competition(competition_result)

        # Get recommendations for new task
        rec = await engine.get_recommendation(
            task_category="reasoning",
            max_providers=3,
        )
        print(f"Use: {rec.recommended_providers}")
    """

    def __init__(
        self,
        lookback_days: int = 30,
        min_competitions_for_trend: int = 10,
        strength_threshold: float = 0.7,
        weakness_threshold: float = 0.3,
    ):
        """Initialize adaptive learning engine.

        Args:
            lookback_days: Days of history to consider for trends
            min_competitions_for_trend: Minimum competitions to calculate trend
            strength_threshold: Win rate threshold for identifying strengths
            weakness_threshold: Win rate threshold for identifying weaknesses
        """
        self.profiles: dict[str, ProviderProfile] = {}
        self.lookback_days = lookback_days
        self.min_competitions_for_trend = min_competitions_for_trend
        self.strength_threshold = strength_threshold
        self.weakness_threshold = weakness_threshold

        # History tracking for trend analysis
        self.competition_history: list[dict[str, Any]] = []

    def get_or_create_profile(self, provider: str) -> ProviderProfile:
        """Get existing profile or create new one.

        Args:
            provider: Provider identifier

        Returns:
            ProviderProfile instance
        """
        if provider not in self.profiles:
            self.profiles[provider] = ProviderProfile(provider=provider)
        return self.profiles[provider]

    async def update_from_competition(
        self,
        provider: str,
        won: bool,
        score: float,
        latency_ms: float,
        cost: float,
        category: str | None = None,
    ) -> None:
        """Update provider profile from competition result.

        Args:
            provider: Provider identifier
            won: Whether provider won
            score: Provider's score (0-100)
            latency_ms: Response latency
            cost: Cost in USD
            category: Optional task category
        """
        profile = self.get_or_create_profile(provider)
        profile.update(won, score, latency_ms, cost, category)

        # Store in history for trend analysis
        self.competition_history.append(
            {
                "provider": provider,
                "won": won,
                "score": score,
                "latency_ms": latency_ms,
                "cost": cost,
                "category": category,
                "timestamp": datetime.now(),
            }
        )

        # Update trends and strengths/weaknesses
        await self._update_trends()
        await self._identify_strengths_weaknesses()

    async def _update_trends(self) -> None:
        """Update performance trends for all providers.

        Compares recent performance to older performance to detect
        improving, stable, or declining trends.
        """
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        recent_history = [h for h in self.competition_history if h["timestamp"] >= cutoff]

        # Group by provider
        provider_scores: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
        for h in recent_history:
            provider_scores[h["provider"]].append((h["timestamp"], h["score"]))

        for provider, scores in provider_scores.items():
            profile = self.profiles[provider]

            if len(scores) < self.min_competitions_for_trend:
                profile.trend = PerformanceTrend.INSUFFICIENT_DATA
                continue

            # Sort by timestamp
            scores.sort(key=lambda x: x[0])

            # Compare first half to second half
            mid = len(scores) // 2
            first_half_avg = sum(s[1] for s in scores[:mid]) / mid
            second_half_avg = sum(s[1] for s in scores[mid:]) / (len(scores) - mid)

            improvement = second_half_avg - first_half_avg

            # Thresholds for trend classification
            if improvement > 5.0:
                profile.trend = PerformanceTrend.IMPROVING
            elif improvement < -5.0:
                profile.trend = PerformanceTrend.DECLINING
            else:
                profile.trend = PerformanceTrend.STABLE

    async def _identify_strengths_weaknesses(self) -> None:
        """Identify category-specific strengths and weaknesses.

        A provider has a strength in a category if win rate > threshold.
        A provider has a weakness in a category if win rate < threshold.
        """
        for profile in self.profiles.values():
            strengths = []
            weaknesses = []

            for category, win_rate in profile.category_performance.items():
                if win_rate >= self.strength_threshold:
                    strengths.append(category)
                elif win_rate <= self.weakness_threshold:
                    weaknesses.append(category)

            # Sort by win rate
            profile.strengths = sorted(
                strengths, key=lambda c: profile.category_performance[c], reverse=True
            )
            profile.weaknesses = sorted(weaknesses, key=lambda c: profile.category_performance[c])

    async def get_recommendation(
        self,
        task_category: str | None = None,
        max_providers: int = 6,
        prefer_fast: bool = False,
        prefer_cheap: bool = False,
    ) -> RecommendationResult:
        """Get provider recommendations for a new task.

        Args:
            task_category: Optional task category for category-specific routing
            max_providers: Maximum providers to recommend
            prefer_fast: Prefer low-latency providers
            prefer_cheap: Prefer low-cost providers

        Returns:
            RecommendationResult with ordered provider list
        """
        if not self.profiles:
            return RecommendationResult(
                recommended_providers=[],
                confidence=0.0,
                reasoning="No provider profiles available yet",
            )

        # Score each provider
        provider_scores: list[tuple[str, float]] = []

        for provider, profile in self.profiles.items():
            score = 0.0
            reasoning_parts = []

            # Category match (highest weight if available)
            if task_category and task_category in profile.category_performance:
                category_score = profile.category_performance[task_category] * 100
                score += category_score * 0.5  # 50% weight
                reasoning_parts.append(
                    f"{provider} has {category_score:.1f}% win rate in {task_category}"
                )
                category_match = True
            else:
                # Fall back to overall win rate
                score += profile.win_rate * 100 * 0.3  # 30% weight
                reasoning_parts.append(
                    f"{provider} has {profile.win_rate*100:.1f}% overall win rate"
                )
                category_match = False

            # Performance trend bonus/penalty
            if profile.trend == PerformanceTrend.IMPROVING:
                score += 10
                reasoning_parts.append(f"{provider} is improving")
            elif profile.trend == PerformanceTrend.DECLINING:
                score -= 10
                reasoning_parts.append(f"{provider} is declining")

            # Latency preference
            if prefer_fast and profile.avg_latency_ms > 0:
                # Lower latency = higher score
                max_latency = max(
                    p.avg_latency_ms for p in self.profiles.values() if p.avg_latency_ms > 0
                )
                if max_latency > 0:
                    latency_score = (1 - profile.avg_latency_ms / max_latency) * 20
                    score += latency_score

            # Cost preference
            if prefer_cheap and profile.avg_cost_usd > 0:
                # Lower cost = higher score
                max_cost = max(p.avg_cost_usd for p in self.profiles.values() if p.avg_cost_usd > 0)
                if max_cost > 0:
                    cost_score = (1 - profile.avg_cost_usd / max_cost) * 20
                    score += cost_score

            provider_scores.append((provider, score))

        # Sort by score descending
        provider_scores.sort(key=lambda x: x[1], reverse=True)

        # Take top N
        recommended = [p[0] for p in provider_scores[:max_providers]]

        # Calculate confidence
        if len(provider_scores) >= 2:
            top_score = provider_scores[0][1]
            second_score = provider_scores[1][1]
            # Higher gap = higher confidence
            score_gap = top_score - second_score
            confidence = min(1.0, score_gap / 50.0)  # Normalize to 0-1
        else:
            confidence = 0.5

        reasoning = "Recommended based on historical performance"
        if task_category:
            reasoning += f" in {task_category}"

        return RecommendationResult(
            recommended_providers=recommended,
            confidence=confidence,
            reasoning=reasoning,
            category_match=bool(task_category and category_match),
        )

    def get_profile(self, provider: str) -> ProviderProfile | None:
        """Get profile for specific provider.

        Args:
            provider: Provider identifier

        Returns:
            ProviderProfile or None if not found
        """
        return self.profiles.get(provider)

    def get_all_profiles(self) -> dict[str, ProviderProfile]:
        """Get all provider profiles.

        Returns:
            Dictionary mapping provider names to profiles
        """
        return self.profiles.copy()

    def get_leaderboard(self, top_n: int = 10) -> list[ProviderProfile]:
        """Get top N providers by win rate.

        Args:
            top_n: Number of top providers to return

        Returns:
            Ordered list of top provider profiles
        """
        profiles = list(self.profiles.values())
        profiles.sort(key=lambda p: p.win_rate, reverse=True)
        return profiles[:top_n]
