"""
Algorithm Sub-Agent
====================

Algorithmic intelligence for the SkyyRose platform.

Capabilities:
- Recommendation engine: product suggestions based on browsing/purchase patterns
- Dynamic pricing: optimal price points per collection/season
- Trend scoring: weight products by social velocity, search volume, engagement
- Inventory optimization: predict demand, flag overstock/understock
- Content ranking: score and prioritize content by predicted engagement
- Brand affinity scoring: which customers align with which collections
- A/B test analysis: statistical significance for brand experiments

Integrates with the Brand Learning Loop to feed algorithmic insights
back into brand strategy and consume brand health signals.

Parent: Analytics Core Agent
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from agents.core.base import CoreAgentType
from agents.core.sub_agent import SubAgent

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================


@dataclass
class ProductScore:
    """Algorithmic score for a product."""

    sku: str
    collection: str = ""
    trend_score: float = 0.0  # 0-100: social velocity + search interest
    engagement_score: float = 0.0  # 0-100: content interaction quality
    conversion_score: float = 0.0  # 0-100: view → purchase likelihood
    brand_alignment: float = 0.0  # 0-100: how well it fits current brand direction
    composite_score: float = 0.0  # Weighted combination
    rank: int = 0
    signals_used: int = 0
    computed_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


@dataclass
class PriceRecommendation:
    """Dynamic pricing recommendation for a product."""

    sku: str
    current_price: float
    recommended_price: float
    confidence: float = 0.0  # 0-1
    reason: str = ""
    factors: dict[str, float] = field(default_factory=dict)


@dataclass
class ContentRank:
    """Ranking score for content prioritization."""

    content_id: str
    predicted_engagement: float = 0.0  # Expected engagement rate
    brand_fit_score: float = 0.0  # How well it fits brand voice
    freshness: float = 1.0  # Decay over time (1.0 = new)
    composite: float = 0.0
    platform: str = ""


@dataclass
class ABTestResult:
    """Statistical analysis of an A/B test."""

    test_name: str
    variant_a_name: str = "Control"
    variant_b_name: str = "Treatment"
    variant_a_rate: float = 0.0
    variant_b_rate: float = 0.0
    lift: float = 0.0  # (B - A) / A as percentage
    z_score: float = 0.0
    p_value: float = 0.0
    significant: bool = False  # p < 0.05
    sample_size_a: int = 0
    sample_size_b: int = 0
    recommendation: str = ""


# =============================================================================
# Algorithm Sub-Agent
# =============================================================================


class AlgorithmSubAgent(SubAgent):
    """
    Algorithmic intelligence for product ranking, pricing, and optimization.

    This agent applies mathematical models to brand, product, and engagement
    data to produce actionable recommendations.
    """

    name = "algorithm"
    parent_type = CoreAgentType.ANALYTICS
    description = (
        "Recommendation engine, dynamic pricing, trend scoring, content ranking, A/B test analysis"
    )
    capabilities = [
        "score_products",
        "rank_content",
        "recommend_price",
        "analyze_ab_test",
        "predict_demand",
        "score_brand_affinity",
    ]

    ALIASES = ["algorithm_agent", "algo", "recommendation_engine"]

    system_prompt = (
        "You are the Algorithm Agent for SkyyRose luxury fashion. "
        "You analyze data patterns and provide actionable recommendations. "
        "Focus: product scoring, trend prediction, dynamic pricing, A/B testing. "
        "Always ground recommendations in data. Express uncertainty when sample "
        "sizes are small. Use statistical methods for significance testing."
    )

    def __init__(
        self,
        *,
        parent: Any | None = None,
        correlation_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent=parent, correlation_id=correlation_id, **kwargs)
        self._learning_loop: Any = None

    # -------------------------------------------------------------------------
    # Lazy initialization
    # -------------------------------------------------------------------------

    def _get_learning_loop(self) -> Any:
        """Lazy-load the brand learning loop."""
        if self._learning_loop is None:
            try:
                from orchestration.brand_learning import create_brand_learning_loop

                self._learning_loop = create_brand_learning_loop(auto_connect=True)
            except ImportError:
                logger.debug("[%s] Brand learning loop unavailable", self.name)
        return self._learning_loop

    # -------------------------------------------------------------------------
    # Core execution
    # -------------------------------------------------------------------------

    async def execute(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """
        Route algorithm tasks.

        Supports:
        - "Score products in the Black Rose collection"
        - "Rank content for Instagram"
        - "Analyze A/B test for caption variants"
        - "Recommend pricing for br-001"
        - "Predict demand for next month"
        """
        task_lower = task.lower()

        if "a/b" in task_lower or "ab test" in task_lower:
            return self.analyze_ab_test(**kwargs)

        if "score" in task_lower and "product" in task_lower:
            return self.score_products(**kwargs)

        if "rank" in task_lower and "content" in task_lower:
            return self.rank_content(**kwargs)

        if "price" in task_lower or "pricing" in task_lower:
            return await self._recommend_pricing(task, **kwargs)

        if "demand" in task_lower or "predict" in task_lower:
            return await self._predict_demand(task, **kwargs)

        if "affinity" in task_lower:
            return self.score_brand_affinity(**kwargs)

        # Default: LLM-powered analysis
        return await self._llm_execute(task)

    # -------------------------------------------------------------------------
    # Product Scoring
    # -------------------------------------------------------------------------

    def score_products(
        self,
        *,
        products: list[dict[str, Any]] | None = None,
        engagement_data: dict[str, dict[str, float]] | None = None,
        weights: dict[str, float] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Score and rank products by composite algorithmic score.

        Args:
            products: List of {"sku": ..., "collection": ..., "price": ...}
            engagement_data: {sku: {"likes": N, "views": N, "purchases": N}}
            weights: Override default score weights

        Returns:
            Ranked list of ProductScore objects
        """
        if not products:
            return {
                "success": False,
                "error": "No products provided",
                "agent": self.name,
            }

        w = weights or {
            "trend": 0.25,
            "engagement": 0.30,
            "conversion": 0.25,
            "brand_alignment": 0.20,
        }

        engagement = engagement_data or {}
        scores: list[ProductScore] = []

        for product in products:
            sku = product.get("sku", "")
            eng = engagement.get(sku, {})

            trend = self._compute_trend_score(eng)
            engagement_s = self._compute_engagement_score(eng)
            conversion = self._compute_conversion_score(eng)
            brand_align = self._compute_brand_alignment(sku, product)

            composite = (
                w["trend"] * trend
                + w["engagement"] * engagement_s
                + w["conversion"] * conversion
                + w["brand_alignment"] * brand_align
            )

            scores.append(
                ProductScore(
                    sku=sku,
                    collection=product.get("collection", ""),
                    trend_score=round(trend, 1),
                    engagement_score=round(engagement_s, 1),
                    conversion_score=round(conversion, 1),
                    brand_alignment=round(brand_align, 1),
                    composite_score=round(composite, 1),
                    signals_used=len(eng),
                )
            )

        # Sort by composite score descending and assign ranks
        scores.sort(key=lambda s: s.composite_score, reverse=True)
        for i, score in enumerate(scores, 1):
            score.rank = i

        return {
            "success": True,
            "scores": [
                {
                    "sku": s.sku,
                    "collection": s.collection,
                    "trend_score": s.trend_score,
                    "engagement_score": s.engagement_score,
                    "conversion_score": s.conversion_score,
                    "brand_alignment": s.brand_alignment,
                    "composite_score": s.composite_score,
                    "rank": s.rank,
                }
                for s in scores
            ],
            "weights_used": w,
            "agent": self.name,
        }

    # -------------------------------------------------------------------------
    # Content Ranking
    # -------------------------------------------------------------------------

    def rank_content(
        self,
        *,
        content_items: list[dict[str, Any]] | None = None,
        platform: str = "instagram",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Rank content items by predicted engagement + brand fit.

        Args:
            content_items: List of {"id": ..., "quality_score": N, "age_hours": N}
            platform: Target platform for weight tuning

        Returns:
            Ranked list of ContentRank objects
        """
        if not content_items:
            return {"success": False, "error": "No content items", "agent": self.name}

        rankings: list[ContentRank] = []

        for item in content_items:
            content_id = item.get("id", "")
            quality = item.get("quality_score", 50.0)
            age_hours = item.get("age_hours", 0)
            brand_fit = item.get("brand_fit", quality)  # Default to quality if no brand fit

            # Time decay: half-life of 48 hours
            freshness = math.exp(-0.693 * age_hours / 48)

            # Platform-specific engagement prediction
            platform_boost = self._platform_engagement_boost(platform, item)

            predicted_engagement = quality * freshness * platform_boost / 100

            composite = (
                0.40 * predicted_engagement * 100 + 0.35 * brand_fit + 0.25 * freshness * 100
            )

            rankings.append(
                ContentRank(
                    content_id=content_id,
                    predicted_engagement=round(predicted_engagement, 3),
                    brand_fit_score=round(brand_fit, 1),
                    freshness=round(freshness, 3),
                    composite=round(composite, 1),
                    platform=platform,
                )
            )

        rankings.sort(key=lambda r: r.composite, reverse=True)

        return {
            "success": True,
            "rankings": [
                {
                    "content_id": r.content_id,
                    "predicted_engagement": r.predicted_engagement,
                    "brand_fit_score": r.brand_fit_score,
                    "freshness": r.freshness,
                    "composite": r.composite,
                    "rank": i,
                }
                for i, r in enumerate(rankings, 1)
            ],
            "platform": platform,
            "agent": self.name,
        }

    # -------------------------------------------------------------------------
    # A/B Test Analysis
    # -------------------------------------------------------------------------

    def analyze_ab_test(
        self,
        *,
        variant_a: dict[str, int] | None = None,
        variant_b: dict[str, int] | None = None,
        test_name: str = "Brand Voice A/B Test",
        variant_a_name: str = "Control",
        variant_b_name: str = "Treatment",
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Analyze A/B test results with statistical significance.

        Args:
            variant_a: {"conversions": N, "total": N}
            variant_b: {"conversions": N, "total": N}
            test_name: Name of the test
            variant_a_name: Label for variant A
            variant_b_name: Label for variant B

        Returns:
            ABTestResult with significance analysis
        """
        if not variant_a or not variant_b:
            return {"success": False, "error": "Both variants required", "agent": self.name}

        n_a = variant_a.get("total", 0)
        n_b = variant_b.get("total", 0)
        c_a = variant_a.get("conversions", 0)
        c_b = variant_b.get("conversions", 0)

        if n_a == 0 or n_b == 0:
            return {"success": False, "error": "Sample sizes must be > 0", "agent": self.name}

        rate_a = c_a / n_a
        rate_b = c_b / n_b
        lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0.0

        # Two-proportion z-test
        p_pooled = (c_a + c_b) / (n_a + n_b)
        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n_a + 1 / n_b)) if p_pooled > 0 else 0.001
        z_score = (rate_b - rate_a) / se if se > 0 else 0.0

        # Approximate p-value using standard normal CDF
        p_value = self._normal_cdf(-abs(z_score)) * 2  # Two-tailed
        significant = p_value < 0.05

        # Recommendation
        if not significant:
            recommendation = (
                f"Not statistically significant (p={p_value:.4f}). "
                f"Need more data — aim for {self._required_sample_size(rate_a, rate_b):.0f} "
                f"samples per variant."
            )
        elif lift > 0:
            recommendation = (
                f"{variant_b_name} wins with {lift:+.1f}% lift (p={p_value:.4f}). "
                f"Roll out {variant_b_name}."
            )
        else:
            recommendation = (
                f"{variant_a_name} wins — {variant_b_name} is {lift:.1f}% worse "
                f"(p={p_value:.4f}). Keep {variant_a_name}."
            )

        result = ABTestResult(
            test_name=test_name,
            variant_a_name=variant_a_name,
            variant_b_name=variant_b_name,
            variant_a_rate=round(rate_a, 4),
            variant_b_rate=round(rate_b, 4),
            lift=round(lift, 2),
            z_score=round(z_score, 4),
            p_value=round(p_value, 6),
            significant=significant,
            sample_size_a=n_a,
            sample_size_b=n_b,
            recommendation=recommendation,
        )

        # Emit brand signal if this is a brand voice test
        if significant and "brand" in test_name.lower():
            self._emit_brand_signal(result)

        return {
            "success": True,
            "result": {
                "test_name": result.test_name,
                "variant_a": {"name": result.variant_a_name, "rate": result.variant_a_rate},
                "variant_b": {"name": result.variant_b_name, "rate": result.variant_b_rate},
                "lift": f"{result.lift:+.1f}%",
                "z_score": result.z_score,
                "p_value": result.p_value,
                "significant": result.significant,
                "recommendation": result.recommendation,
            },
            "agent": self.name,
        }

    # -------------------------------------------------------------------------
    # Brand Affinity Scoring
    # -------------------------------------------------------------------------

    def score_brand_affinity(
        self,
        *,
        customer_signals: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Score customer-collection brand affinity.

        Args:
            customer_signals: List of {"customer_id": ..., "collection": ...,
                              "interaction_type": ..., "value": ...}

        Returns:
            Affinity scores per customer per collection
        """
        if not customer_signals:
            return {"success": False, "error": "No customer signals", "agent": self.name}

        # Weight interaction types
        interaction_weights = {
            "purchase": 10.0,
            "add_to_cart": 5.0,
            "wishlist": 4.0,
            "view": 1.0,
            "share": 3.0,
            "click": 0.5,
        }

        # Accumulate scores
        affinity: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))

        for signal in customer_signals:
            customer = signal.get("customer_id", "unknown")
            collection = signal.get("collection", "")
            interaction = signal.get("interaction_type", "view")
            value = signal.get("value", 1.0)

            weight = interaction_weights.get(interaction, 1.0)
            affinity[customer][collection] += weight * value

        # Normalize per customer
        results: dict[str, dict[str, float]] = {}
        for customer, collections in affinity.items():
            total = sum(collections.values())
            if total > 0:
                results[customer] = {
                    coll: round(score / total * 100, 1)
                    for coll, score in sorted(collections.items(), key=lambda x: x[1], reverse=True)
                }

        return {
            "success": True,
            "affinity_scores": results,
            "total_customers": len(results),
            "agent": self.name,
        }

    # -------------------------------------------------------------------------
    # LLM-powered predictions
    # -------------------------------------------------------------------------

    async def _recommend_pricing(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Use LLM + data to recommend pricing."""
        pricing_prompt = (
            f"As a pricing analyst for SkyyRose luxury fashion, {task}\n\n"
            "Consider: brand positioning (luxury streetwear), competitor pricing, "
            "collection exclusivity, material costs, target margins (60-70%), "
            "and customer willingness-to-pay. "
            "Format as structured recommendations with confidence levels."
        )
        return await self._llm_execute(pricing_prompt)

    async def _predict_demand(self, task: str, **kwargs: Any) -> dict[str, Any]:
        """Use LLM + data for demand prediction."""
        demand_prompt = (
            f"As a demand analyst for SkyyRose luxury fashion, {task}\n\n"
            "Consider: seasonality (Q4 peak, summer dip for hoodies), "
            "collection lifecycle, social media velocity, pre-order signals, "
            "and limited edition scarcity effects. "
            "Provide quantitative predictions with confidence intervals."
        )
        return await self._llm_execute(demand_prompt)

    # -------------------------------------------------------------------------
    # Mathematical Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def _compute_trend_score(engagement: dict[str, float]) -> float:
        """Compute trend score from social/search signals."""
        views = engagement.get("views", 0)
        shares = engagement.get("shares", 0)
        searches = engagement.get("searches", 0)

        # Weighted social velocity
        velocity = views * 0.01 + shares * 5.0 + searches * 3.0

        # Sigmoid normalization to 0-100
        return 100 * (1 - 1 / (1 + velocity / 100))

    @staticmethod
    def _compute_engagement_score(engagement: dict[str, float]) -> float:
        """Compute engagement quality score."""
        likes = engagement.get("likes", 0)
        comments = engagement.get("comments", 0)
        saves = engagement.get("saves", 0)

        quality = likes * 1.0 + comments * 3.0 + saves * 4.0
        return min(100 * (1 - 1 / (1 + quality / 50)), 100.0)

    @staticmethod
    def _compute_conversion_score(engagement: dict[str, float]) -> float:
        """Compute conversion likelihood from engagement funnel."""
        views = engagement.get("views", 0)
        carts = engagement.get("add_to_cart", 0)
        purchases = engagement.get("purchases", 0)

        if views == 0:
            return 0.0

        view_to_cart = carts / views if views > 0 else 0
        cart_to_purchase = purchases / carts if carts > 0 else 0

        # Normalize: 2% view-to-cart and 20% cart-to-purchase are "good" for luxury
        normalized = min(view_to_cart / 0.02, 1.0) * 0.5 + min(cart_to_purchase / 0.20, 1.0) * 0.5
        return round(normalized * 100, 1)

    def _compute_brand_alignment(self, sku: str, product: dict[str, Any]) -> float:
        """
        Score how well a product aligns with current brand direction.

        Uses learning loop insights if available.
        """
        base_score = 70.0  # Default: assume reasonable alignment

        loop = self._get_learning_loop()
        if loop is None:
            return base_score

        try:
            from orchestration.brand_learning import SKYYROSE_BRAND

            # Check if this product's collection needs reinforcement
            reinforcement = SKYYROSE_BRAND.get("_reinforcement_needed", [])
            collection = product.get("collection", "")
            if collection.upper().replace("-", "_") in reinforcement:
                base_score -= 15.0  # Penalty for misaligned collection
        except ImportError:
            pass

        return max(0.0, min(100.0, base_score))

    @staticmethod
    def _platform_engagement_boost(platform: str, item: dict[str, Any]) -> float:
        """Platform-specific engagement prediction multiplier."""
        boosts = {
            "instagram": 1.2,  # Strong for visual luxury fashion
            "tiktok": 1.4,  # Highest virality potential
            "twitter": 0.8,  # Lower engagement for fashion
            "facebook": 0.9,
        }
        content_type = item.get("content_type", "")
        # Reels/video content gets extra boost
        video_boost = 1.3 if content_type in ("reel", "video", "story") else 1.0
        return boosts.get(platform, 1.0) * video_boost

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximate standard normal CDF using Abramowitz & Stegun."""
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))

    @staticmethod
    def _required_sample_size(rate_a: float, rate_b: float, _power: float = 0.8) -> float:
        """Estimate required sample size per variant for given power."""
        if rate_a <= 0 or rate_b <= 0:
            return 1000.0  # Fallback
        effect = abs(rate_b - rate_a)
        if effect == 0:
            return 10000.0

        # Simplified formula for two-proportion test
        z_alpha = 1.96  # 95% confidence
        z_beta = 0.84  # 80% power
        p_bar = (rate_a + rate_b) / 2
        n = (
            z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
            + z_beta * math.sqrt(rate_a * (1 - rate_a) + rate_b * (1 - rate_b))
        ) ** 2 / effect**2
        return max(n, 30.0)

    def _emit_brand_signal(self, result: ABTestResult) -> None:
        """Emit A/B test result as a brand signal."""
        loop = self._get_learning_loop()
        if loop is None:
            return

        try:
            from orchestration.brand_learning import BrandSignal, SignalType

            loop.observe(
                BrandSignal(
                    signal_type=SignalType.QUALITY_GATE_RESULT,
                    agent_id=self.name,
                    content=result.recommendation,
                    quality_score=abs(result.lift),
                    accepted=result.significant and result.lift > 0,
                    metadata={
                        "test_name": result.test_name,
                        "lift": result.lift,
                        "p_value": result.p_value,
                    },
                )
            )
        except Exception as exc:
            logger.debug("[%s] Brand signal emission failed: %s", self.name, exc)


__all__ = ["AlgorithmSubAgent"]
