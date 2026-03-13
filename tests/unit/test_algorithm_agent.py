"""
Tests for the Algorithm Sub-Agent.
"""

from __future__ import annotations


import pytest

from agents.core.analytics.sub_agents.algorithm_agent import (
    AlgorithmSubAgent,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def agent() -> AlgorithmSubAgent:
    return AlgorithmSubAgent()


# =============================================================================
# Product Scoring
# =============================================================================


class TestProductScoring:
    def test_scores_products_by_composite(self, agent: AlgorithmSubAgent):
        products = [
            {"sku": "br-001", "collection": "black-rose", "price": 35},
            {"sku": "sg-002", "collection": "signature", "price": 65},
        ]
        engagement = {
            "br-001": {"views": 1000, "likes": 50, "shares": 10, "purchases": 5},
            "sg-002": {"views": 500, "likes": 200, "comments": 30, "purchases": 20},
        }

        result = agent.score_products(products=products, engagement_data=engagement)
        assert result["success"] is True
        assert len(result["scores"]) == 2

        # Scores should be ranked
        scores = result["scores"]
        assert scores[0]["rank"] == 1
        assert scores[1]["rank"] == 2
        assert scores[0]["composite_score"] >= scores[1]["composite_score"]

    def test_empty_products_returns_error(self, agent: AlgorithmSubAgent):
        result = agent.score_products(products=[])
        assert result["success"] is False

    def test_custom_weights(self, agent: AlgorithmSubAgent):
        products = [{"sku": "br-001", "collection": "black-rose"}]
        weights = {"trend": 0.5, "engagement": 0.5, "conversion": 0.0, "brand_alignment": 0.0}

        result = agent.score_products(products=products, weights=weights)
        assert result["success"] is True
        assert result["weights_used"] == weights


# =============================================================================
# Content Ranking
# =============================================================================


class TestContentRanking:
    def test_ranks_by_composite(self, agent: AlgorithmSubAgent):
        items = [
            {"id": "post-1", "quality_score": 90, "age_hours": 1, "brand_fit": 85},
            {"id": "post-2", "quality_score": 70, "age_hours": 72, "brand_fit": 95},
            {"id": "post-3", "quality_score": 95, "age_hours": 24, "brand_fit": 60},
        ]

        result = agent.rank_content(content_items=items, platform="instagram")
        assert result["success"] is True
        assert len(result["rankings"]) == 3

        # First item should have rank 1
        assert result["rankings"][0]["rank"] == 1

    def test_freshness_decay(self, agent: AlgorithmSubAgent):
        """Older content should score lower."""
        items = [
            {"id": "fresh", "quality_score": 80, "age_hours": 1},
            {"id": "stale", "quality_score": 80, "age_hours": 168},
        ]

        result = agent.rank_content(content_items=items)
        rankings = result["rankings"]

        fresh = next(r for r in rankings if r["content_id"] == "fresh")
        stale = next(r for r in rankings if r["content_id"] == "stale")

        assert fresh["freshness"] > stale["freshness"]

    def test_empty_content_returns_error(self, agent: AlgorithmSubAgent):
        result = agent.rank_content(content_items=[])
        assert result["success"] is False


# =============================================================================
# A/B Test Analysis
# =============================================================================


class TestABTestAnalysis:
    def test_significant_result(self, agent: AlgorithmSubAgent):
        result = agent.analyze_ab_test(
            variant_a={"conversions": 50, "total": 1000},
            variant_b={"conversions": 80, "total": 1000},
            test_name="Caption Test",
        )

        assert result["success"] is True
        r = result["result"]
        assert r["variant_a"]["rate"] == 0.05
        assert r["variant_b"]["rate"] == 0.08
        assert r["significant"] is True
        assert float(r["lift"].rstrip("%").lstrip("+")) > 0

    def test_nonsignificant_result(self, agent: AlgorithmSubAgent):
        result = agent.analyze_ab_test(
            variant_a={"conversions": 5, "total": 50},
            variant_b={"conversions": 6, "total": 50},
            test_name="Small Test",
        )

        assert result["success"] is True
        r = result["result"]
        # With such small samples, should not be significant
        assert r["significant"] is False

    def test_missing_variants_returns_error(self, agent: AlgorithmSubAgent):
        result = agent.analyze_ab_test(variant_a={"conversions": 10, "total": 100})
        assert result["success"] is False

    def test_zero_sample_size_returns_error(self, agent: AlgorithmSubAgent):
        result = agent.analyze_ab_test(
            variant_a={"conversions": 0, "total": 0},
            variant_b={"conversions": 0, "total": 0},
        )
        assert result["success"] is False

    def test_recommendation_includes_winner(self, agent: AlgorithmSubAgent):
        result = agent.analyze_ab_test(
            variant_a={"conversions": 30, "total": 1000},
            variant_b={"conversions": 80, "total": 1000},
            variant_a_name="Classic Voice",
            variant_b_name="Edgy Voice",
        )

        r = result["result"]
        if r["significant"]:
            assert "Edgy Voice" in r["recommendation"] or "Classic Voice" in r["recommendation"]


# =============================================================================
# Brand Affinity Scoring
# =============================================================================


class TestBrandAffinity:
    def test_scores_customer_affinity(self, agent: AlgorithmSubAgent):
        signals = [
            {"customer_id": "c1", "collection": "black-rose", "interaction_type": "purchase"},
            {"customer_id": "c1", "collection": "black-rose", "interaction_type": "view"},
            {"customer_id": "c1", "collection": "signature", "interaction_type": "view"},
            {"customer_id": "c2", "collection": "love-hurts", "interaction_type": "purchase"},
        ]

        result = agent.score_brand_affinity(customer_signals=signals)
        assert result["success"] is True
        assert result["total_customers"] == 2

        # Customer 1 should have higher affinity for black-rose
        c1 = result["affinity_scores"]["c1"]
        assert c1["black-rose"] > c1["signature"]

    def test_empty_signals_returns_error(self, agent: AlgorithmSubAgent):
        result = agent.score_brand_affinity(customer_signals=[])
        assert result["success"] is False


# =============================================================================
# Mathematical Helpers
# =============================================================================


class TestMathHelpers:
    def test_trend_score_sigmoid(self, agent: AlgorithmSubAgent):
        # Zero engagement = zero score
        assert agent._compute_trend_score({}) == 0.0

        # High engagement should approach 100
        high = agent._compute_trend_score({"views": 10000, "shares": 500, "searches": 200})
        assert high > 90

    def test_conversion_score(self, agent: AlgorithmSubAgent):
        # Perfect conversion funnel
        perfect = agent._compute_conversion_score({"views": 100, "add_to_cart": 5, "purchases": 2})
        assert perfect > 50

        # No views = zero
        assert agent._compute_conversion_score({"views": 0}) == 0.0

    def test_normal_cdf(self, agent: AlgorithmSubAgent):
        # CDF(0) should be 0.5
        assert abs(agent._normal_cdf(0) - 0.5) < 0.01

        # CDF(-inf) → 0, CDF(+inf) → 1
        assert agent._normal_cdf(-10) < 0.001
        assert agent._normal_cdf(10) > 0.999

    def test_required_sample_size(self, agent: AlgorithmSubAgent):
        # Should return a reasonable number for moderate effect sizes
        n = agent._required_sample_size(0.05, 0.08)
        assert 100 < n < 10000

        # Smaller effect = larger sample needed
        n_small = agent._required_sample_size(0.05, 0.055)
        assert n_small > n
