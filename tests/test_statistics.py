"""Tests for statistical analysis module.

This test suite covers:
- A/B test analysis with p-values and confidence intervals
- Effect size calculations (Cohen's d, Cliff's delta)
- Bayesian posterior probability estimation
- Statistical significance detection
- Edge cases (small samples, equal means, zero variance)
"""

from __future__ import annotations

import pytest

from llm.statistics import ABTestResult, StatisticalAnalyzer

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def analyzer():
    """Create StatisticalAnalyzer instance."""
    return StatisticalAnalyzer(significance_level=0.05, min_samples=3)


@pytest.fixture
def significant_scores():
    """Generate scores with clear significant difference."""
    return {
        "scores_a": [75.0, 77.0, 76.0, 78.0, 74.0],
        "scores_b": [88.0, 90.0, 89.0, 91.0, 87.0],
    }


@pytest.fixture
def non_significant_scores():
    """Generate scores with no significant difference."""
    return {
        "scores_a": [80.0, 82.0, 81.0, 79.0, 83.0],
        "scores_b": [81.0, 83.0, 80.0, 82.0, 84.0],
    }


# =============================================================================
# A/B Test Analysis Tests
# =============================================================================


def test_ab_test_significant_difference(analyzer, significant_scores):
    """Test A/B test with statistically significant difference."""
    result = analyzer.analyze_ab_test(
        scores_a=significant_scores["scores_a"],
        scores_b=significant_scores["scores_b"],
        provider_a="claude",
        provider_b="gpt4",
    )

    assert isinstance(result, ABTestResult)
    assert result.is_significant
    assert result.winner == "gpt4"  # B has higher mean
    assert result.p_value < 0.05
    assert result.mean_b > result.mean_a


def test_ab_test_no_significant_difference(analyzer, non_significant_scores):
    """Test A/B test with no significant difference."""
    result = analyzer.analyze_ab_test(
        scores_a=non_significant_scores["scores_a"],
        scores_b=non_significant_scores["scores_b"],
        provider_a="claude",
        provider_b="gpt4",
    )

    assert isinstance(result, ABTestResult)
    assert not result.is_significant
    assert result.winner is None
    assert result.p_value >= 0.05


def test_ab_test_insufficient_samples(analyzer):
    """Test error with insufficient samples."""
    with pytest.raises(ValueError, match="Need at least 3 samples"):
        analyzer.analyze_ab_test(
            scores_a=[80.0, 85.0],  # Only 2 samples
            scores_b=[90.0, 95.0, 92.0],
            provider_a="claude",
            provider_b="gpt4",
        )


def test_ab_test_provider_a_wins(analyzer):
    """Test case where provider A wins."""
    result = analyzer.analyze_ab_test(
        scores_a=[90.0, 92.0, 91.0, 93.0, 89.0],  # Higher than B
        scores_b=[75.0, 77.0, 76.0, 78.0, 74.0],
        provider_a="claude",
        provider_b="gpt4",
    )

    assert result.is_significant
    assert result.winner == "claude"
    assert result.mean_a > result.mean_b


# =============================================================================
# Confidence Interval Tests
# =============================================================================


def test_confidence_interval_normal_data(analyzer):
    """Test confidence interval calculation with normal data."""
    scores = [80.0, 82.0, 81.0, 83.0, 79.0]
    ci = analyzer.compute_confidence_interval(scores)

    assert isinstance(ci, tuple)
    assert len(ci) == 2
    lower, upper = ci

    # CI should contain the mean
    mean = sum(scores) / len(scores)
    assert lower < mean < upper

    # CI bounds should be reasonable
    assert lower > 0
    assert upper < 100


def test_confidence_interval_single_value(analyzer):
    """Test CI with single value (edge case)."""
    scores = [85.0]
    lower, upper = analyzer.compute_confidence_interval(scores)

    # Should return the value itself
    assert lower == 85.0
    assert upper == 85.0


def test_confidence_interval_custom_level(analyzer):
    """Test CI with custom confidence level."""
    scores = [80.0, 82.0, 81.0, 83.0, 79.0]

    ci_95 = analyzer.compute_confidence_interval(scores, confidence=0.95)
    ci_99 = analyzer.compute_confidence_interval(scores, confidence=0.99)

    # 99% CI should be wider than 95% CI
    assert (ci_99[1] - ci_99[0]) > (ci_95[1] - ci_95[0])


# =============================================================================
# Effect Size Tests
# =============================================================================


def test_cohens_d_large_effect(analyzer):
    """Test Cohen's d with large effect size."""
    scores_a = [50.0, 52.0, 51.0, 53.0, 49.0]
    scores_b = [85.0, 87.0, 86.0, 88.0, 84.0]

    d = analyzer.calculate_cohens_d(scores_a, scores_b)

    assert d > 0.8  # Large effect
    assert analyzer.interpret_effect_size(d, "cohens_d") == "large"


def test_cohens_d_small_effect(analyzer):
    """Test Cohen's d with small to medium effect size."""
    # Higher variance to produce smaller effect size despite mean difference
    scores_a = [75.0, 80.0, 85.0, 78.0, 82.0]  # mean ~80, high variance
    scores_b = [77.0, 82.0, 87.0, 80.0, 84.0]  # mean ~82, high variance

    d = analyzer.calculate_cohens_d(scores_a, scores_b)

    # With high variance, even 2-point difference should be small/medium effect
    assert abs(d) < 0.8  # Small to medium effect
    assert analyzer.interpret_effect_size(d, "cohens_d") in ["small", "medium", "negligible"]


def test_cohens_d_zero_variance(analyzer):
    """Test Cohen's d with zero variance (edge case)."""
    scores_a = [80.0, 80.0, 80.0]
    scores_b = [80.0, 80.0, 80.0]

    d = analyzer.calculate_cohens_d(scores_a, scores_b)

    assert d == 0.0


def test_cliffs_delta_complete_dominance(analyzer):
    """Test Cliff's delta with complete dominance."""
    scores_a = [10.0, 20.0, 15.0]
    scores_b = [90.0, 95.0, 92.0]  # All B > all A

    delta = analyzer.calculate_cliffs_delta(scores_a, scores_b)

    assert delta == 1.0  # Complete dominance by B


def test_cliffs_delta_no_difference(analyzer):
    """Test Cliff's delta with identical distributions."""
    scores_a = [80.0, 85.0, 90.0]
    scores_b = [80.0, 85.0, 90.0]

    delta = analyzer.calculate_cliffs_delta(scores_a, scores_b)

    assert abs(delta) < 0.15  # Negligible


def test_cliffs_delta_negative(analyzer):
    """Test Cliff's delta when A dominates B."""
    scores_a = [90.0, 95.0, 92.0]  # All A > all B
    scores_b = [10.0, 20.0, 15.0]

    delta = analyzer.calculate_cliffs_delta(scores_a, scores_b)

    assert delta == -1.0  # Complete dominance by A


# =============================================================================
# Bayesian Analysis Tests
# =============================================================================


def test_bayesian_posterior_clear_winner(analyzer):
    """Test Bayesian analysis with clear winner."""
    scores_a = [70.0, 72.0, 71.0, 73.0, 69.0]
    scores_b = [88.0, 90.0, 89.0, 91.0, 87.0]

    prob = analyzer.calculate_bayesian_posterior(scores_a, scores_b)

    assert prob > 0.95  # Very high probability B > A


def test_bayesian_posterior_equal_distributions(analyzer):
    """Test Bayesian analysis with equal distributions."""
    scores_a = [80.0, 82.0, 81.0, 83.0, 79.0]
    scores_b = [80.0, 82.0, 81.0, 83.0, 79.0]

    prob = analyzer.calculate_bayesian_posterior(scores_a, scores_b)

    # Should be around 0.5 (coin flip)
    assert 0.4 < prob < 0.6


def test_bayesian_posterior_a_better(analyzer):
    """Test Bayesian analysis when A is better."""
    scores_a = [90.0, 92.0, 91.0, 93.0, 89.0]
    scores_b = [70.0, 72.0, 71.0, 73.0, 69.0]

    prob = analyzer.calculate_bayesian_posterior(scores_a, scores_b)

    assert prob < 0.05  # Very low probability B > A


# =============================================================================
# Result Formatting Tests
# =============================================================================


def test_format_result_summary(analyzer, significant_scores):
    """Test result summary formatting."""
    result = analyzer.analyze_ab_test(
        scores_a=significant_scores["scores_a"],
        scores_b=significant_scores["scores_b"],
        provider_a="claude",
        provider_b="gpt4",
    )

    summary = analyzer.format_result_summary(result)

    assert isinstance(summary, str)
    assert "claude" in summary
    assert "gpt4" in summary
    assert "p-value" in summary
    assert "Cohen's d" in summary
    assert "Cliff's delta" in summary
    assert "Winner" in summary


# =============================================================================
# Edge Cases
# =============================================================================


def test_identical_scores(analyzer):
    """Test with completely identical scores."""
    scores = [85.0, 85.0, 85.0, 85.0, 85.0]

    result = analyzer.analyze_ab_test(
        scores_a=scores,
        scores_b=scores,
        provider_a="claude",
        provider_b="gpt4",
    )

    assert not result.is_significant
    assert result.winner is None
    assert result.mean_a == result.mean_b


def test_high_variance_no_significance(analyzer):
    """Test high variance preventing significance."""
    scores_a = [10.0, 90.0, 20.0, 80.0, 30.0]  # High variance
    scores_b = [15.0, 85.0, 25.0, 75.0, 35.0]  # High variance, similar mean

    result = analyzer.analyze_ab_test(
        scores_a=scores_a,
        scores_b=scores_b,
        provider_a="claude",
        provider_b="gpt4",
    )

    # High variance should make it harder to detect significance
    assert not result.is_significant


def test_small_difference_large_sample():
    """Test small difference with large sample size."""
    # Create analyzer with min 10 samples
    analyzer = StatisticalAnalyzer(significance_level=0.05, min_samples=10)

    # Small difference (1 point) but lots of samples
    scores_a = [80.0] * 50
    scores_b = [81.0] * 50

    result = analyzer.analyze_ab_test(
        scores_a=scores_a,
        scores_b=scores_b,
        provider_a="claude",
        provider_b="gpt4",
    )

    # Even small differences can be significant with large samples
    assert result.is_significant
    assert abs(result.effect_size) < 0.5  # But effect size is still small


# =============================================================================
# Integration Tests
# =============================================================================


def test_complete_ab_test_workflow(analyzer):
    """Test complete A/B test workflow from start to finish."""
    # Simulate real competition data
    claude_scores = [85.2, 87.1, 83.5, 88.0, 84.7, 86.3, 85.9, 87.5]
    gpt4_scores = [91.3, 89.7, 92.1, 90.5, 91.8, 89.9, 92.5, 90.2]

    # Run analysis
    result = analyzer.analyze_ab_test(
        scores_a=claude_scores,
        scores_b=gpt4_scores,
        provider_a="claude",
        provider_b="gpt4",
    )

    # Verify all components
    assert result.is_significant
    assert result.winner == "gpt4"
    assert result.p_value < 0.05
    assert result.bayesian_probability > 0.95
    assert result.effect_size > 0.5  # Large effect
    assert abs(result.cliffs_delta) > 0.474  # Large effect

    # Verify confidence intervals don't overlap
    assert result.confidence_interval_a[1] < result.confidence_interval_b[0]

    # Verify summary
    summary = analyzer.format_result_summary(result)
    assert "Winner: gpt4" in summary
