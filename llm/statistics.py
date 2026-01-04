"""Statistical analysis for Round Table competitions.

This module provides Bayesian and frequentist statistical methods for:
- A/B test analysis with confidence intervals
- Effect size calculations (Cohen's d, Cliff's delta)
- Bayesian posterior probability estimation
- Statistical significance testing

Used to make Round Table competition results statistically rigorous.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class ABTestResult:
    """Results of an A/B test between two providers.

    Attributes:
        provider_a: Name of first provider
        provider_b: Name of second provider
        scores_a: List of scores for provider A
        scores_b: List of scores for provider B
        mean_a: Mean score for provider A
        mean_b: Mean score for provider B
        p_value: P-value from statistical test (lower = more significant)
        confidence_interval_a: 95% confidence interval for A
        confidence_interval_b: 95% confidence interval for B
        effect_size: Cohen's d effect size
        cliffs_delta: Cliff's delta (non-parametric effect size)
        bayesian_probability: P(B > A) from Bayesian analysis
        winner: Name of winning provider (or None if no statistical difference)
        is_significant: Whether difference is statistically significant (p < 0.05)
    """

    provider_a: str
    provider_b: str
    scores_a: list[float]
    scores_b: list[float]
    mean_a: float
    mean_b: float
    p_value: float
    confidence_interval_a: tuple[float, float]
    confidence_interval_b: tuple[float, float]
    effect_size: float  # Cohen's d
    cliffs_delta: float
    bayesian_probability: float  # P(B > A)
    winner: str | None
    is_significant: bool


class StatisticalAnalyzer:
    """Bayesian and frequentist statistical analysis for Round Table.

    Provides rigorous statistical methods to determine if performance
    differences between LLM providers are statistically significant.

    Example:
        analyzer = StatisticalAnalyzer()
        result = analyzer.analyze_ab_test(
            scores_a=[85.2, 87.1, 83.5],
            scores_b=[91.3, 89.7, 92.1],
            provider_a="claude",
            provider_b="gpt4",
        )
        if result.is_significant:
            print(f"Winner: {result.winner} with p={result.p_value:.4f}")
    """

    def __init__(self, significance_level: float = 0.05, min_samples: int = 3):
        """Initialize statistical analyzer.

        Args:
            significance_level: P-value threshold for significance (default 0.05)
            min_samples: Minimum samples required per provider (default 3)
        """
        self.significance_level = significance_level
        self.min_samples = min_samples

    def analyze_ab_test(
        self,
        scores_a: list[float],
        scores_b: list[float],
        provider_a: str,
        provider_b: str,
    ) -> ABTestResult:
        """Perform comprehensive A/B test analysis.

        Combines multiple statistical methods:
        - Welch's t-test (handles unequal variances)
        - Confidence intervals
        - Effect sizes (Cohen's d, Cliff's delta)
        - Bayesian probability estimation

        Args:
            scores_a: Scores for provider A
            scores_b: Scores for provider B
            provider_a: Name of provider A
            provider_b: Name of provider B

        Returns:
            ABTestResult with comprehensive statistical analysis

        Raises:
            ValueError: If insufficient samples provided
        """
        if len(scores_a) < self.min_samples or len(scores_b) < self.min_samples:
            raise ValueError(
                f"Need at least {self.min_samples} samples per provider, "
                f"got {len(scores_a)} for {provider_a} and {len(scores_b)} for {provider_b}"
            )

        # Basic statistics
        mean_a = float(np.mean(scores_a))
        mean_b = float(np.mean(scores_b))

        # Welch's t-test (doesn't assume equal variances)
        t_stat, p_value = stats.ttest_ind(scores_a, scores_b, equal_var=False)
        p_value = float(p_value)

        # Confidence intervals
        ci_a = self.compute_confidence_interval(scores_a)
        ci_b = self.compute_confidence_interval(scores_b)

        # Effect sizes
        effect_size = self.calculate_cohens_d(scores_a, scores_b)
        cliffs_delta = self.calculate_cliffs_delta(scores_a, scores_b)

        # Bayesian analysis
        bayesian_prob = self.calculate_bayesian_posterior(scores_a, scores_b)

        # Determine winner
        is_significant = p_value < self.significance_level
        winner = (provider_b if mean_b > mean_a else provider_a) if is_significant else None

        return ABTestResult(
            provider_a=provider_a,
            provider_b=provider_b,
            scores_a=scores_a,
            scores_b=scores_b,
            mean_a=mean_a,
            mean_b=mean_b,
            p_value=p_value,
            confidence_interval_a=ci_a,
            confidence_interval_b=ci_b,
            effect_size=effect_size,
            cliffs_delta=cliffs_delta,
            bayesian_probability=bayesian_prob,
            winner=winner,
            is_significant=is_significant,
        )

    def compute_confidence_interval(
        self, scores: list[float], confidence: float = 0.95
    ) -> tuple[float, float]:
        """Compute confidence interval for scores.

        Uses t-distribution for better accuracy with small samples.

        Args:
            scores: List of scores
            confidence: Confidence level (default 0.95 for 95% CI)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        if len(scores) < 2:
            mean = float(np.mean(scores))
            return (mean, mean)

        mean = float(np.mean(scores))
        se = float(stats.sem(scores))
        n = len(scores)

        # Use t-distribution for small samples
        t_critical = stats.t.ppf((1 + confidence) / 2, n - 1)
        margin = t_critical * se

        lower = mean - margin
        upper = mean + margin

        return (float(lower), float(upper))

    def calculate_cohens_d(self, scores_a: list[float], scores_b: list[float]) -> float:
        """Calculate Cohen's d effect size.

        Interpretation:
        - |d| < 0.2: Small effect
        - 0.2 <= |d| < 0.5: Medium effect
        - |d| >= 0.5: Large effect

        Args:
            scores_a: Scores for group A
            scores_b: Scores for group B

        Returns:
            Cohen's d (positive means B > A)
        """
        mean_a = np.mean(scores_a)
        mean_b = np.mean(scores_b)

        # Pooled standard deviation
        n_a = len(scores_a)
        n_b = len(scores_b)
        var_a = np.var(scores_a, ddof=1)
        var_b = np.var(scores_b, ddof=1)

        pooled_std = np.sqrt(((n_a - 1) * var_a + (n_b - 1) * var_b) / (n_a + n_b - 2))

        if pooled_std == 0:
            return 0.0

        cohens_d = (mean_b - mean_a) / pooled_std
        return float(cohens_d)

    def calculate_cliffs_delta(self, scores_a: list[float], scores_b: list[float]) -> float:
        """Calculate Cliff's delta (non-parametric effect size).

        Interpretation:
        - |δ| < 0.147: Negligible
        - 0.147 <= |δ| < 0.33: Small
        - 0.33 <= |δ| < 0.474: Medium
        - |δ| >= 0.474: Large

        Args:
            scores_a: Scores for group A
            scores_b: Scores for group B

        Returns:
            Cliff's delta in range [-1, 1] (positive means B > A)
        """
        n_a = len(scores_a)
        n_b = len(scores_b)

        # Count dominances
        dominance = sum(1 if b > a else (-1 if b < a else 0) for a in scores_a for b in scores_b)

        cliffs_delta = dominance / (n_a * n_b)
        return float(cliffs_delta)

    def calculate_bayesian_posterior(
        self, scores_a: list[float], scores_b: list[float], n_samples: int = 10000
    ) -> float:
        """Calculate P(B > A) using Bayesian analysis.

        Uses Monte Carlo simulation with normal priors based on observed data.

        Args:
            scores_a: Scores for provider A
            scores_b: Scores for provider B
            n_samples: Number of Monte Carlo samples (default 10000)

        Returns:
            Probability that B is better than A (0-1)
        """
        # Estimate parameters from data
        mean_a = np.mean(scores_a)
        std_a = np.std(scores_a, ddof=1) if len(scores_a) > 1 else 1.0
        mean_b = np.mean(scores_b)
        std_b = np.std(scores_b, ddof=1) if len(scores_b) > 1 else 1.0

        # Monte Carlo simulation
        samples_a: NDArray = np.random.normal(loc=mean_a, scale=std_a, size=n_samples)
        samples_b: NDArray = np.random.normal(loc=mean_b, scale=std_b, size=n_samples)

        # Calculate probability B > A
        prob_b_better = float(np.mean(samples_b > samples_a))
        return prob_b_better

    def interpret_effect_size(self, effect_size: float, metric: str = "cohens_d") -> str:
        """Interpret effect size magnitude.

        Args:
            effect_size: Calculated effect size
            metric: Type of effect size ("cohens_d" or "cliffs_delta")

        Returns:
            Human-readable interpretation
        """
        abs_effect = abs(effect_size)

        if metric == "cohens_d":
            if abs_effect < 0.2:
                return "negligible"
            elif abs_effect < 0.5:
                return "small"
            elif abs_effect < 0.8:
                return "medium"
            else:
                return "large"
        elif metric == "cliffs_delta":
            if abs_effect < 0.147:
                return "negligible"
            elif abs_effect < 0.33:
                return "small"
            elif abs_effect < 0.474:
                return "medium"
            else:
                return "large"
        else:
            return "unknown"

    def format_result_summary(self, result: ABTestResult) -> str:
        """Format A/B test result as human-readable summary.

        Args:
            result: ABTestResult to format

        Returns:
            Multi-line formatted summary
        """
        lines = [
            f"A/B Test: {result.provider_a} vs {result.provider_b}",
            "",
            "Scores:",
            f"  {result.provider_a}: {result.mean_a:.2f} (95% CI: {result.confidence_interval_a[0]:.2f}-{result.confidence_interval_a[1]:.2f})",
            f"  {result.provider_b}: {result.mean_b:.2f} (95% CI: {result.confidence_interval_b[0]:.2f}-{result.confidence_interval_b[1]:.2f})",
            "",
            "Statistical Significance:",
            f"  p-value: {result.p_value:.4f} ({'significant' if result.is_significant else 'not significant'})",
            f"  Bayesian P(B>A): {result.bayesian_probability:.2%}",
            "",
            "Effect Size:",
            f"  Cohen's d: {result.effect_size:.3f} ({self.interpret_effect_size(result.effect_size, 'cohens_d')})",
            f"  Cliff's delta: {result.cliffs_delta:.3f} ({self.interpret_effect_size(result.cliffs_delta, 'cliffs_delta')})",
            "",
        ]

        if result.winner:
            lines.append(f"Winner: {result.winner}")
        else:
            lines.append("Winner: No statistically significant difference")

        return "\n".join(lines)
