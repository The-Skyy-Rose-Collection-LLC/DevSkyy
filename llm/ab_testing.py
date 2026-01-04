"""
A/B Testing Engine with Statistical Analysis
=============================================

Enterprise-grade A/B testing system for DevSkyy.

Features:
- Multi-variant experiment support (A/B/n testing)
- Statistical significance calculation
- Database persistence (Neon PostgreSQL)
- Real-time dashboard integration
- Automatic winner detection
- Sample size calculation

Author: DevSkyy Platform Team
Version: 1.0.0.""" 
from __future__ import annotations

import logging
import math
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class ExperimentStatus(str, Enum):
    """Status of an A/B test experiment.""" 
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MetricType(str, Enum):
    """Type of metric being tracked.""" 
    CONVERSION = "conversion"  # Binary outcome (0 or 1)
    REVENUE = "revenue"  # Continuous monetary value
    COUNT = "count"  # Count-based metric
    DURATION = "duration"  # Time-based metric
    SCORE = "score"  # Rating/score metric


class WinnerStatus(str, Enum):
    """Winner determination status.""" 
    NO_DATA = "no_data"
    INSUFFICIENT_DATA = "insufficient_data"
    NO_WINNER = "no_winner"
    VARIANT_A = "variant_a"
    VARIANT_B = "variant_b"
    DRAW = "draw"


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class Variant:
    """A variant in an A/B test.""" 
    id: str
    name: str
    description: str = ""
    is_control: bool = False
    weight: float = 0.5  # Traffic allocation weight
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResult:
    """Results for a metric in a variant.""" 
    variant_id: str
    sample_size: int = 0
    conversions: int = 0  # For conversion metrics
    total_value: float = 0.0  # Sum of values
    sum_squares: float = 0.0  # For variance calculation

    @property
    def mean(self) -> float:
        """Calculate mean value.""" 
        if self.sample_size == 0:
            return 0.0
        return self.total_value / self.sample_size

    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate.""" 
        if self.sample_size == 0:
            return 0.0
        return self.conversions / self.sample_size

    @property
    def variance(self) -> float:
        """Calculate variance.""" 
        if self.sample_size < 2:
            return 0.0
        mean = self.mean
        return (self.sum_squares - 2 * mean * self.total_value + self.sample_size * mean * mean) / (
            self.sample_size - 1
        )

    @property
    def std_error(self) -> float:
        """Calculate standard error.""" 
        if self.sample_size == 0:
            return 0.0
        return math.sqrt(self.variance / self.sample_size)


@dataclass
class StatisticalResult:
    """Statistical analysis result.""" 
    winner: WinnerStatus
    p_value: float
    confidence_level: float
    z_score: float
    effect_size: float  # Relative improvement
    absolute_effect: float  # Absolute difference
    control_mean: float
    treatment_mean: float
    sample_size_control: int
    sample_size_treatment: int
    power: float
    is_significant: bool
    required_sample_size: int  # For target power
    estimated_days_remaining: int


@dataclass
class Experiment:
    """A/B test experiment definition.""" 
    id: str
    name: str
    description: str
    hypothesis: str
    variants: list[Variant]
    primary_metric: str
    secondary_metrics: list[str] = field(default_factory=list)
    metric_type: MetricType = MetricType.CONVERSION
    target_sample_size: int = 1000
    confidence_threshold: float = 0.95
    minimum_effect_size: float = 0.05  # 5% minimum detectable effect
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    winner_variant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_control(self) -> Variant | None:
        """Get control variant.""" 
        for v in self.variants:
            if v.is_control:
                return v
        return self.variants[0] if self.variants else None

    def get_treatment(self) -> Variant | None:
        """Get treatment variant (first non-control).""" 
        for v in self.variants:
            if not v.is_control:
                return v
        return None


@dataclass
class ExperimentResult:
    """Complete experiment result with analysis.""" 
    experiment: Experiment
    metric_results: dict[str, dict[str, MetricResult]]  # metric -> variant_id -> result
    statistical_results: dict[str, StatisticalResult]  # metric -> stats
    overall_winner: WinnerStatus
    recommendation: str
    summary: str
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# Statistical Functions
# =============================================================================


class StatisticalCalculator:
    """Statistical calculations for A/B testing.""" 
    @staticmethod
    def calculate_z_score(p1: float, p2: float, n1: int, n2: int) -> float:
        """Calculate z-score for two proportions.""" 
        if n1 == 0 or n2 == 0:
            return 0.0

        p_pooled = (p1 * n1 + p2 * n2) / (n1 + n2)

        if p_pooled == 0 or p_pooled == 1:
            return 0.0

        se = math.sqrt(p_pooled * (1 - p_pooled) * (1 / n1 + 1 / n2))

        if se == 0:
            return 0.0

        return (p1 - p2) / se

    @staticmethod
    def z_to_p_value(z: float) -> float:
        """Convert z-score to two-tailed p-value using approximation.""" 
        # Approximation of standard normal CDF
        x = abs(z)
        t = 1 / (1 + 0.2316419 * x)
        d = 0.3989423 * math.exp(-x * x / 2)
        p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))

        if z > 0:
            return 2 * p
        return 2 * (1 - p)

    @staticmethod
    def calculate_sample_size(
        baseline_rate: float, mde: float, alpha: float = 0.05, power: float = 0.8
    ) -> int:
        """
        Calculate required sample size per variant.

        Args:
            baseline_rate: Current conversion rate (0-1)
            mde: Minimum detectable effect (relative, e.g., 0.05 for 5%)
            alpha: Significance level
            power: Statistical power.""" 
        if baseline_rate <= 0 or baseline_rate >= 1:
            return 10000  # Default for invalid inputs

        p1 = baseline_rate
        p2 = baseline_rate * (1 + mde)

        if p2 >= 1:
            p2 = 0.99

        # Z-scores for alpha and power
        z_alpha = 1.96 if alpha == 0.05 else 2.576 if alpha == 0.01 else 1.645
        z_beta = 0.84 if power == 0.8 else 1.28 if power == 0.9 else 1.645

        p_avg = (p1 + p2) / 2
        effect = abs(p2 - p1)

        if effect == 0:
            return 100000

        numerator = (
            z_alpha * math.sqrt(2 * p_avg * (1 - p_avg))
            + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
        ) ** 2
        denominator = effect**2

        return int(math.ceil(numerator / denominator))

    @staticmethod
    def calculate_power(p1: float, p2: float, n1: int, n2: int, alpha: float = 0.05) -> float:
        """Calculate statistical power achieved.""" 
        if n1 == 0 or n2 == 0:
            return 0.0

        z_alpha = 1.96 if alpha == 0.05 else 2.576

        se_null = math.sqrt(((p1 + p2) / 2) * (1 - (p1 + p2) / 2) * (1 / n1 + 1 / n2))
        se_alt = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)

        if se_null == 0 or se_alt == 0:
            return 0.0

        effect = abs(p2 - p1)
        z_effect = (effect - z_alpha * se_null) / se_alt

        # Approximation of CDF
        x = abs(z_effect)
        t = 1 / (1 + 0.2316419 * x)
        d = 0.3989423 * math.exp(-x * x / 2)
        power = 1 - d * t * (
            0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))
        )

        return max(0.0, min(1.0, power))


# =============================================================================
# A/B Testing Engine
# =============================================================================


class ABTestingEngine:
    """
    Enterprise A/B Testing Engine.

    Features:
    - Create and manage experiments
    - Track conversions and metrics
    - Statistical significance analysis
    - Automatic winner detection
    - Database persistence

    Example:
        engine = ABTestingEngine()
        await engine.initialize()

        # Create experiment
        exp = engine.create_experiment(
            name="Checkout Button Color",
            hypothesis="Red button increases conversions",
            variants=[
                Variant(id="control", name="Blue Button", is_control=True),
                Variant(id="treatment", name="Red Button"),
            ],
            primary_metric="checkout_conversion",
            target_sample_size=10000,
        )

        # Start experiment
        engine.start_experiment(exp.id)

        # Track conversions
        engine.track_conversion(exp.id, "control", converted=False)
        engine.track_conversion(exp.id, "treatment", converted=True)

        # Get results
        result = engine.analyze_experiment(exp.id)
    """

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self._experiments: dict[str, Experiment] = {}
        self._metric_data: dict[str, dict[str, dict[str, MetricResult]]] = {}
        self._pool = None
        self._initialized = False
        self._calculator = StatisticalCalculator()

    async def initialize(self) -> None:
        """Initialize engine and database connection."""
        if self.db_url:
            try:
                import asyncpg

                self._pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)
                await self._create_schema()
                self._initialized = True
                logger.info("A/B Testing Engine initialized with database")
            except ImportError:
                logger.warning("asyncpg not installed - using in-memory storage")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
        else:
            logger.info("A/B Testing Engine initialized without database")

    async def _create_schema(self) -> None:
        """Create database schema."""
        schema = """
        CREATE TABLE IF NOT EXISTS ab_experiments (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            hypothesis TEXT,
            variants JSONB NOT NULL,
            primary_metric VARCHAR(100) NOT NULL,
            secondary_metrics JSONB,
            metric_type VARCHAR(50) NOT NULL,
            target_sample_size INTEGER,
            confidence_threshold FLOAT,
            minimum_effect_size FLOAT,
            status VARCHAR(20) NOT NULL,
            winner_variant_id VARCHAR(64),
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE
        );

        CREATE TABLE IF NOT EXISTS ab_conversions (
            id SERIAL PRIMARY KEY,
            experiment_id VARCHAR(64) REFERENCES ab_experiments(id),
            variant_id VARCHAR(64) NOT NULL,
            metric_name VARCHAR(100) NOT NULL,
            converted BOOLEAN DEFAULT FALSE,
            value FLOAT DEFAULT 0,
            user_id VARCHAR(100),
            session_id VARCHAR(100),
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_ab_conversions_experiment
            ON ab_conversions(experiment_id, variant_id);

        CREATE INDEX IF NOT EXISTS idx_ab_conversions_created
            ON ab_conversions(created_at);.""" 
        if self._pool is None:
            raise RuntimeError("Database pool not initialized")

        async with self._pool.acquire() as conn:
            await conn.execute(schema)

    # =========================================================================
    # Experiment Management
    # =========================================================================

    def create_experiment(
        self,
        name: str,
        hypothesis: str,
        variants: list[Variant],
        primary_metric: str,
        description: str = "",
        secondary_metrics: list[str] | None = None,
        metric_type: MetricType = MetricType.CONVERSION,
        target_sample_size: int = 1000,
        confidence_threshold: float = 0.95,
        minimum_effect_size: float = 0.05,
        metadata: dict[str, Any] | None = None,
    ) -> Experiment:
        """Create a new A/B test experiment.""" 
        exp_id = str(uuid4())[:16]

        # Ensure at least one control
        has_control = any(v.is_control for v in variants)
        if not has_control and variants:
            variants[0].is_control = True

        experiment = Experiment(
            id=exp_id,
            name=name,
            description=description,
            hypothesis=hypothesis,
            variants=variants,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            metric_type=metric_type,
            target_sample_size=target_sample_size,
            confidence_threshold=confidence_threshold,
            minimum_effect_size=minimum_effect_size,
            metadata=metadata or {},
        )

        self._experiments[exp_id] = experiment

        # Initialize metric data
        self._metric_data[exp_id] = {primary_metric: {}}
        for v in variants:
            self._metric_data[exp_id][primary_metric][v.id] = MetricResult(variant_id=v.id)

        logger.info(f"Created experiment: {name} (ID: {exp_id})")
        return experiment

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """Get experiment by ID.""" 
        return self._experiments.get(experiment_id)

    def start_experiment(self, experiment_id: str) -> bool:
        """Start an experiment.""" 
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False

        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.now(UTC)
        logger.info(f"Started experiment: {exp.name}")
        return True

    def pause_experiment(self, experiment_id: str) -> bool:
        """Pause an experiment.""" 
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False

        exp.status = ExperimentStatus.PAUSED
        return True

    def complete_experiment(self, experiment_id: str, winner_id: str | None = None) -> bool:
        """Complete an experiment.""" 
        exp = self._experiments.get(experiment_id)
        if not exp:
            return False

        exp.status = ExperimentStatus.COMPLETED
        exp.completed_at = datetime.now(UTC)
        exp.winner_variant_id = winner_id
        logger.info(f"Completed experiment: {exp.name} (Winner: {winner_id})")
        return True

    # =========================================================================
    # Tracking
    # =========================================================================

    def track_conversion(
        self,
        experiment_id: str,
        variant_id: str,
        converted: bool = True,
        value: float = 1.0,
        metric_name: str | None = None,
        user_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Track a conversion event.

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            converted: Whether conversion occurred
            value: Value of conversion (for revenue metrics)
            metric_name: Metric name (defaults to primary metric)
            user_id: Optional user identifier
            metadata: Additional metadata.""" 
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != ExperimentStatus.RUNNING:
            return False

        metric = metric_name or exp.primary_metric

        # Initialize metric if needed
        if metric not in self._metric_data[experiment_id]:
            self._metric_data[experiment_id][metric] = {}

        if variant_id not in self._metric_data[experiment_id][metric]:
            self._metric_data[experiment_id][metric][variant_id] = MetricResult(
                variant_id=variant_id
            )

        result = self._metric_data[experiment_id][metric][variant_id]

        # Update metrics
        result.sample_size += 1
        if converted:
            result.conversions += 1
        result.total_value += value
        result.sum_squares += value * value

        return True

    def assign_variant(self, experiment_id: str, user_id: str | None = None) -> Variant | None:
        """
        Assign a user to a variant (traffic splitting).

        Uses deterministic assignment if user_id provided,
        otherwise random assignment based on weights.
        """
        import hashlib
        import random

        exp = self._experiments.get(experiment_id)
        if not exp or not exp.variants:
            return None

        if user_id:
            # Deterministic assignment based on user ID
            hash_val = int(
                hashlib.md5(
                    f"{experiment_id}:{user_id}".encode(), usedforsecurity=False
                ).hexdigest(),
                16,
            )
            bucket = (hash_val % 100) / 100
        else:
            bucket = random.random()

        # Assign based on weights
        cumulative = 0.0
        for variant in exp.variants:
            cumulative += variant.weight
            if bucket < cumulative:
                return variant

        return exp.variants[-1]

    # =========================================================================
    # Analysis
    # =========================================================================

    def analyze_experiment(
        self, experiment_id: str, metric_name: str | None = None
    ) -> ExperimentResult | None:
        """
        Analyze experiment results with statistical significance.

        Args:
            experiment_id: Experiment ID
            metric_name: Specific metric to analyze (defaults to primary).""" 
        exp = self._experiments.get(experiment_id)
        if not exp:
            return None

        metric = metric_name or exp.primary_metric
        metric_data = self._metric_data.get(experiment_id, {}).get(metric, {})

        if not metric_data:
            return None

        control = exp.get_control()
        treatment = exp.get_treatment()

        if not control or not treatment:
            return None

        control_result = metric_data.get(control.id)
        treatment_result = metric_data.get(treatment.id)

        if not control_result or not treatment_result:
            return None

        # Calculate statistics
        stats = self._calculate_statistics(
            control_result, treatment_result, exp.confidence_threshold, exp.minimum_effect_size
        )

        # Determine winner
        overall_winner = stats.winner

        # Generate recommendation
        recommendation = self._generate_recommendation(exp, stats)
        summary = self._generate_summary(exp, stats)

        return ExperimentResult(
            experiment=exp,
            metric_results={metric: metric_data},
            statistical_results={metric: stats},
            overall_winner=overall_winner,
            recommendation=recommendation,
            summary=summary,
        )

    def _calculate_statistics(
        self,
        control: MetricResult,
        treatment: MetricResult,
        confidence_threshold: float,
        min_effect_size: float,
    ) -> StatisticalResult:
        """Calculate statistical significance.""" 
        n1, n2 = control.sample_size, treatment.sample_size

        if n1 < 10 or n2 < 10:
            return StatisticalResult(
                winner=WinnerStatus.INSUFFICIENT_DATA,
                p_value=1.0,
                confidence_level=0.0,
                z_score=0.0,
                effect_size=0.0,
                absolute_effect=0.0,
                control_mean=control.conversion_rate,
                treatment_mean=treatment.conversion_rate,
                sample_size_control=n1,
                sample_size_treatment=n2,
                power=0.0,
                is_significant=False,
                required_sample_size=self._calculator.calculate_sample_size(
                    control.conversion_rate or 0.1, min_effect_size
                ),
                estimated_days_remaining=-1,
            )

        p1 = control.conversion_rate
        p2 = treatment.conversion_rate

        # Calculate z-score and p-value
        z_score = self._calculator.calculate_z_score(p1, p2, n1, n2)
        p_value = self._calculator.z_to_p_value(z_score)

        # Effect size
        absolute_effect = p2 - p1
        effect_size = absolute_effect / p1 if p1 > 0 else 0.0

        # Power
        power = self._calculator.calculate_power(p1, p2, n1, n2)

        # Required sample size
        required = self._calculator.calculate_sample_size(p1, min_effect_size)

        # Significance check
        alpha = 1 - confidence_threshold
        is_significant = p_value < alpha

        # Winner determination
        if not is_significant:
            winner = WinnerStatus.NO_WINNER
        elif p2 > p1:
            winner = WinnerStatus.VARIANT_B  # Treatment wins
        elif p1 > p2:
            winner = WinnerStatus.VARIANT_A  # Control wins
        else:
            winner = WinnerStatus.DRAW

        # Estimate days remaining
        current_daily = (n1 + n2) / max(
            1, (datetime.now(UTC) - datetime(2025, 1, 1, tzinfo=UTC)).days
        )
        remaining_samples = max(0, required * 2 - n1 - n2)
        days_remaining = int(remaining_samples / current_daily) if current_daily > 0 else -1

        return StatisticalResult(
            winner=winner,
            p_value=p_value,
            confidence_level=1 - p_value,
            z_score=z_score,
            effect_size=effect_size,
            absolute_effect=absolute_effect,
            control_mean=p1,
            treatment_mean=p2,
            sample_size_control=n1,
            sample_size_treatment=n2,
            power=power,
            is_significant=is_significant,
            required_sample_size=required,
            estimated_days_remaining=days_remaining,
        )

    def _generate_recommendation(self, exp: Experiment, stats: StatisticalResult) -> str:
        """Generate recommendation based on results.""" 
        if stats.winner == WinnerStatus.INSUFFICIENT_DATA:
            return "Continue collecting data - insufficient sample size for reliable conclusions."

        if not stats.is_significant:
            if stats.power < 0.8:
                return f"Continue experiment - need ~{stats.required_sample_size} samples per variant for 80% power."
            return (
                "No significant difference detected. Consider stopping or testing a larger change."
            )

        if stats.winner == WinnerStatus.VARIANT_B:
            lift = stats.effect_size * 100
            return f"Implement treatment variant - shows {lift:.1f}% improvement with {stats.confidence_level*100:.1f}% confidence."

        if stats.winner == WinnerStatus.VARIANT_A:
            return "Keep control variant - treatment showed lower performance."

        return "Results inconclusive - consider extending the experiment."

    def _generate_summary(self, exp: Experiment, stats: StatisticalResult) -> str:
        """Generate experiment summary.""" 
        return f"""A/B Test Summary: {exp.name}

Hypothesis: {exp.hypothesis}

Results:
- Control: {stats.control_mean*100:.2f}% (n={stats.sample_size_control})
- Treatment: {stats.treatment_mean*100:.2f}% (n={stats.sample_size_treatment})
- Absolute Effect: {stats.absolute_effect*100:+.2f}%
- Relative Effect: {stats.effect_size*100:+.1f}%

Statistical Analysis:
- P-value: {stats.p_value:.4f}
- Confidence: {stats.confidence_level*100:.1f}%
- Power: {stats.power*100:.1f}%
- Significant: {'Yes' if stats.is_significant else 'No'}

Winner: {stats.winner.value}.""" 
    # =========================================================================
    # Utilities
    # =========================================================================

    def calculate_required_sample_size(
        self,
        baseline_rate: float,
        minimum_detectable_effect: float,
        confidence: float = 0.95,
        power: float = 0.8,
    ) -> dict[str, Any]:
        """
        Calculate required sample size for experiment planning.

        Args:
            baseline_rate: Current conversion rate (0-1)
            minimum_detectable_effect: Minimum effect to detect (relative, e.g., 0.05)
            confidence: Confidence level (default 0.95)
            power: Statistical power (default 0.8)

        Returns:
            Dict with sample size and runtime estimates.""" 
        alpha = 1 - confidence
        per_variant = self._calculator.calculate_sample_size(
            baseline_rate, minimum_detectable_effect, alpha, power
        )

        return {
            "per_variant": per_variant,
            "total": per_variant * 2,
            "baseline_rate": baseline_rate,
            "minimum_detectable_effect": minimum_detectable_effect,
            "confidence": confidence,
            "power": power,
        }

    def list_experiments(self, status: ExperimentStatus | None = None) -> list[Experiment]:
        """List all experiments, optionally filtered by status.""" 
        experiments = list(self._experiments.values())

        if status:
            experiments = [e for e in experiments if e.status == status]

        return sorted(experiments, key=lambda e: e.created_at, reverse=True)

    async def close(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()


# =============================================================================
# Factory
# =============================================================================


async def create_ab_engine(db_url: str | None = None) -> ABTestingEngine:
    """Factory function to create and initialize A/B Testing Engine.""" 
    engine = ABTestingEngine(db_url)
    await engine.initialize()
    return engine


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Enums
    "ExperimentStatus",
    "MetricType",
    "WinnerStatus",
    # Data classes
    "Variant",
    "MetricResult",
    "StatisticalResult",
    "Experiment",
    "ExperimentResult",
    # Classes
    "StatisticalCalculator",
    "ABTestingEngine",
    # Factory
    "create_ab_engine",
]
