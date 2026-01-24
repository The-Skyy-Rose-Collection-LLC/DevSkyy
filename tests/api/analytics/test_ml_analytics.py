# tests/api/analytics/test_ml_analytics.py
"""
Unit tests for ML Pipeline Analytics API.

Tests cover:
- Model validation for all Pydantic models
- Enum value tests
- Helper function tests
- Mock data generation
- Time range calculations

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from api.v1.analytics.ml_pipelines import (
    AssetMetrics,
    DescriptionMetrics,
    JobStatus,
    LatencyPercentiles,
    MLOverviewResponse,
    MLProvider,
    PipelineMetrics,
    PipelineType,
    ProviderAnalyticsResponse,
    ProviderMetrics,
    ThreeDAnalyticsResponse,
    ThreeDMetrics,
    TimeRange,
    generate_mock_latency,
    generate_mock_pipeline_metrics,
    generate_mock_provider_metrics,
    get_time_range_start,
)

# =============================================================================
# Enum Tests
# =============================================================================


class TestEnums:
    """Tests for enum values."""

    def test_time_range_values(self) -> None:
        """Test TimeRange enum values."""
        assert TimeRange.HOUR_1.value == "1h"
        assert TimeRange.HOURS_24.value == "24h"
        assert TimeRange.DAYS_7.value == "7d"
        assert TimeRange.DAYS_30.value == "30d"
        assert TimeRange.DAYS_90.value == "90d"

    def test_ml_provider_values(self) -> None:
        """Test MLProvider enum values."""
        assert MLProvider.REPLICATE.value == "replicate"
        assert MLProvider.TRIPO.value == "tripo"
        assert MLProvider.HUGGINGFACE.value == "huggingface"
        assert MLProvider.GEMINI.value == "gemini"
        assert MLProvider.OPENAI.value == "openai"

    def test_pipeline_type_values(self) -> None:
        """Test PipelineType enum values."""
        assert PipelineType.THREE_D_GENERATION.value == "3d_generation"
        assert PipelineType.IMAGE_DESCRIPTION.value == "image_description"
        assert PipelineType.ASSET_PROCESSING.value == "asset_processing"
        assert PipelineType.EMBEDDING.value == "embedding"
        assert PipelineType.RERANKING.value == "reranking"

    def test_job_status_values(self) -> None:
        """Test JobStatus enum values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"


# =============================================================================
# Model Tests
# =============================================================================


class TestLatencyPercentiles:
    """Tests for LatencyPercentiles model."""

    def test_create_latency_percentiles(self) -> None:
        """Test creating latency percentiles."""
        latency = LatencyPercentiles(p50=0.5, p95=1.0, p99=2.0)

        assert latency.p50 == 0.5
        assert latency.p95 == 1.0
        assert latency.p99 == 2.0


class TestPipelineMetrics:
    """Tests for PipelineMetrics model."""

    def test_create_pipeline_metrics(self) -> None:
        """Test creating pipeline metrics."""
        metrics = PipelineMetrics(
            pipeline_type=PipelineType.THREE_D_GENERATION,
            total_jobs=100,
            completed_jobs=95,
            failed_jobs=5,
            success_rate=95.0,
            avg_duration_seconds=15.5,
            latency=LatencyPercentiles(p50=10.0, p95=20.0, p99=30.0),
            total_cost_usd=Decimal("50.00"),
        )

        assert metrics.pipeline_type == PipelineType.THREE_D_GENERATION
        assert metrics.total_jobs == 100
        assert metrics.success_rate == 95.0
        assert metrics.total_cost_usd == Decimal("50.00")


class TestProviderMetrics:
    """Tests for ProviderMetrics model."""

    def test_create_provider_metrics(self) -> None:
        """Test creating provider metrics."""
        metrics = ProviderMetrics(
            provider=MLProvider.TRIPO,
            total_jobs=200,
            completed_jobs=190,
            failed_jobs=10,
            success_rate=95.0,
            avg_duration_seconds=20.0,
            latency=LatencyPercentiles(p50=15.0, p95=25.0, p99=35.0),
            total_cost_usd=Decimal("100.00"),
            cost_per_job_usd=Decimal("0.50"),
            api_errors=5,
            rate_limit_hits=2,
        )

        assert metrics.provider == MLProvider.TRIPO
        assert metrics.total_jobs == 200
        assert metrics.api_errors == 5


class TestThreeDMetrics:
    """Tests for ThreeDMetrics model."""

    def test_create_3d_metrics(self) -> None:
        """Test creating 3D generation metrics."""
        provider_metrics = ProviderMetrics(
            provider=MLProvider.TRIPO,
            total_jobs=100,
            completed_jobs=95,
            failed_jobs=5,
            success_rate=95.0,
            avg_duration_seconds=20.0,
            latency=LatencyPercentiles(p50=15.0, p95=25.0, p99=35.0),
            total_cost_usd=Decimal("50.00"),
            cost_per_job_usd=Decimal("0.50"),
            api_errors=2,
            rate_limit_hits=1,
        )

        metrics = ThreeDMetrics(
            total_models_generated=100,
            successful_models=95,
            failed_models=5,
            success_rate=95.0,
            avg_generation_time_seconds=25.0,
            avg_fidelity_score=96.5,
            models_below_threshold=3,
            total_cost_usd=Decimal("50.00"),
            by_provider=[provider_metrics],
        )

        assert metrics.total_models_generated == 100
        assert metrics.avg_fidelity_score == 96.5
        assert len(metrics.by_provider) == 1


class TestDescriptionMetrics:
    """Tests for DescriptionMetrics model."""

    def test_create_description_metrics(self) -> None:
        """Test creating description metrics."""
        metrics = DescriptionMetrics(
            total_descriptions=500,
            successful_descriptions=490,
            failed_descriptions=10,
            success_rate=98.0,
            avg_processing_time_seconds=1.5,
            avg_token_count=250,
            total_cost_usd=Decimal("10.00"),
            by_provider=[],
        )

        assert metrics.total_descriptions == 500
        assert metrics.avg_token_count == 250


class TestAssetMetrics:
    """Tests for AssetMetrics model."""

    def test_create_asset_metrics(self) -> None:
        """Test creating asset metrics."""
        metrics = AssetMetrics(
            total_assets_processed=1000,
            successful_processing=990,
            failed_processing=10,
            success_rate=99.0,
            avg_processing_time_seconds=0.5,
            total_storage_bytes=1_000_000_000,
            total_cost_usd=Decimal("1.00"),
        )

        assert metrics.total_assets_processed == 1000
        assert metrics.total_storage_bytes == 1_000_000_000


# =============================================================================
# Response Model Tests
# =============================================================================


class TestMLOverviewResponse:
    """Tests for MLOverviewResponse model."""

    def test_create_overview_response(self) -> None:
        """Test creating overview response."""
        response = MLOverviewResponse(
            time_range=TimeRange.HOURS_24,
            total_jobs=1000,
            total_completed=950,
            total_failed=50,
            overall_success_rate=95.0,
            total_cost_usd=Decimal("200.00"),
            pipelines=[],
            top_errors=[],
        )

        assert response.time_range == TimeRange.HOURS_24
        assert response.total_jobs == 1000
        assert response.generated_at is not None


class TestThreeDAnalyticsResponse:
    """Tests for ThreeDAnalyticsResponse model."""

    def test_create_3d_response(self) -> None:
        """Test creating 3D analytics response."""
        metrics = ThreeDMetrics(
            total_models_generated=100,
            successful_models=95,
            failed_models=5,
            success_rate=95.0,
            avg_generation_time_seconds=25.0,
            avg_fidelity_score=96.5,
            models_below_threshold=3,
            total_cost_usd=Decimal("50.00"),
            by_provider=[],
        )

        response = ThreeDAnalyticsResponse(
            time_range=TimeRange.DAYS_7,
            metrics=metrics,
            hourly_trend=[],
        )

        assert response.time_range == TimeRange.DAYS_7
        assert response.metrics.total_models_generated == 100


class TestProviderAnalyticsResponse:
    """Tests for ProviderAnalyticsResponse model."""

    def test_create_provider_response(self) -> None:
        """Test creating provider analytics response."""
        response = ProviderAnalyticsResponse(
            time_range=TimeRange.DAYS_30,
            providers=[],
            total_cost_usd=Decimal("500.00"),
        )

        assert response.time_range == TimeRange.DAYS_30
        assert response.total_cost_usd == Decimal("500.00")


# =============================================================================
# Helper Function Tests
# =============================================================================


class TestGetTimeRangeStart:
    """Tests for get_time_range_start function."""

    def test_hour_1(self) -> None:
        """Test 1 hour time range."""
        now = datetime.now(UTC)
        start = get_time_range_start(TimeRange.HOUR_1)

        assert start <= now
        assert (now - start).total_seconds() >= 3600 - 5  # Allow 5 second tolerance
        assert (now - start).total_seconds() <= 3600 + 5

    def test_hours_24(self) -> None:
        """Test 24 hours time range."""
        now = datetime.now(UTC)
        start = get_time_range_start(TimeRange.HOURS_24)

        assert start <= now
        delta = now - start
        assert delta.days == 0 or (delta.days == 1 and delta.seconds < 60)

    def test_days_7(self) -> None:
        """Test 7 days time range."""
        now = datetime.now(UTC)
        start = get_time_range_start(TimeRange.DAYS_7)

        assert start <= now
        delta = now - start
        assert 6 <= delta.days <= 7

    def test_days_30(self) -> None:
        """Test 30 days time range."""
        now = datetime.now(UTC)
        start = get_time_range_start(TimeRange.DAYS_30)

        assert start <= now
        delta = now - start
        assert 29 <= delta.days <= 30

    def test_days_90(self) -> None:
        """Test 90 days time range."""
        now = datetime.now(UTC)
        start = get_time_range_start(TimeRange.DAYS_90)

        assert start <= now
        delta = now - start
        assert 89 <= delta.days <= 90


class TestGenerateMockLatency:
    """Tests for generate_mock_latency function."""

    def test_generates_valid_latency(self) -> None:
        """Test that mock latency is valid."""
        latency = generate_mock_latency()

        assert latency.p50 > 0
        assert latency.p95 >= latency.p50
        assert latency.p99 >= latency.p95


class TestGenerateMockPipelineMetrics:
    """Tests for generate_mock_pipeline_metrics function."""

    def test_generates_valid_metrics(self) -> None:
        """Test that mock pipeline metrics are valid."""
        metrics = generate_mock_pipeline_metrics(
            PipelineType.THREE_D_GENERATION,
            TimeRange.HOURS_24,
        )

        assert metrics.pipeline_type == PipelineType.THREE_D_GENERATION
        assert metrics.total_jobs > 0
        assert metrics.completed_jobs + metrics.failed_jobs == metrics.total_jobs
        assert 0 <= metrics.success_rate <= 100
        assert metrics.total_cost_usd >= 0


class TestGenerateMockProviderMetrics:
    """Tests for generate_mock_provider_metrics function."""

    def test_generates_valid_metrics(self) -> None:
        """Test that mock provider metrics are valid."""
        metrics = generate_mock_provider_metrics(
            MLProvider.TRIPO,
            TimeRange.DAYS_7,
        )

        assert metrics.provider == MLProvider.TRIPO
        assert metrics.total_jobs > 0
        assert metrics.completed_jobs + metrics.failed_jobs == metrics.total_jobs
        assert 0 <= metrics.success_rate <= 100
        assert metrics.cost_per_job_usd >= 0
        assert metrics.api_errors >= 0
        assert metrics.rate_limit_hits >= 0
