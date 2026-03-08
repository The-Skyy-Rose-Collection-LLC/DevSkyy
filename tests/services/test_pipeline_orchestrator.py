# tests/services/test_pipeline_orchestrator.py
"""Unit tests for PipelineOrchestrator."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from services.ml.pipeline_orchestrator import (
    DEFAULT_TIMEOUT_SECONDS,
    PipelineError,
    PipelineEvent,
    PipelineJob,
    PipelineOrchestrator,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
    ProcessingProfile,
    StageCheckpoint,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def orchestrator() -> PipelineOrchestrator:
    """Create pipeline orchestrator for testing."""
    return PipelineOrchestrator(timeout_seconds=5)


@pytest.fixture
def success_handler() -> Any:
    """Create handler that always succeeds."""

    async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
        return f"{input_url}?processed=true"

    return handler


@pytest.fixture
def failing_handler() -> Any:
    """Create handler that always fails."""

    async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
        raise ValueError("Stage failed")

    return handler


@pytest.fixture
def slow_handler() -> Any:
    """Create handler that times out."""

    async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
        await asyncio.sleep(10)
        return input_url

    return handler


# =============================================================================
# Model Tests
# =============================================================================


class TestPipelineStage:
    """Test PipelineStage enum."""

    def test_ingest_value(self) -> None:
        """PipelineStage.INGEST should have correct value."""
        assert PipelineStage.INGEST.value == "ingest"

    def test_validate_value(self) -> None:
        """PipelineStage.VALIDATE should have correct value."""
        assert PipelineStage.VALIDATE.value == "validate"

    def test_background_removal_value(self) -> None:
        """PipelineStage.BACKGROUND_REMOVAL should have correct value."""
        assert PipelineStage.BACKGROUND_REMOVAL.value == "background_removal"

    def test_lighting_value(self) -> None:
        """PipelineStage.LIGHTING should have correct value."""
        assert PipelineStage.LIGHTING.value == "lighting"

    def test_upscale_value(self) -> None:
        """PipelineStage.UPSCALE should have correct value."""
        assert PipelineStage.UPSCALE.value == "upscale"

    def test_format_value(self) -> None:
        """PipelineStage.FORMAT should have correct value."""
        assert PipelineStage.FORMAT.value == "format"

    def test_complete_value(self) -> None:
        """PipelineStage.COMPLETE should have correct value."""
        assert PipelineStage.COMPLETE.value == "complete"


class TestPipelineStatus:
    """Test PipelineStatus enum."""

    def test_pending_value(self) -> None:
        """PipelineStatus.PENDING should have correct value."""
        assert PipelineStatus.PENDING.value == "pending"

    def test_running_value(self) -> None:
        """PipelineStatus.RUNNING should have correct value."""
        assert PipelineStatus.RUNNING.value == "running"

    def test_succeeded_value(self) -> None:
        """PipelineStatus.SUCCEEDED should have correct value."""
        assert PipelineStatus.SUCCEEDED.value == "succeeded"

    def test_failed_value(self) -> None:
        """PipelineStatus.FAILED should have correct value."""
        assert PipelineStatus.FAILED.value == "failed"

    def test_cancelled_value(self) -> None:
        """PipelineStatus.CANCELLED should have correct value."""
        assert PipelineStatus.CANCELLED.value == "cancelled"


class TestProcessingProfile:
    """Test ProcessingProfile enum."""

    def test_full_value(self) -> None:
        """ProcessingProfile.FULL should have correct value."""
        assert ProcessingProfile.FULL.value == "full"

    def test_quick_value(self) -> None:
        """ProcessingProfile.QUICK should have correct value."""
        assert ProcessingProfile.QUICK.value == "quick"

    def test_background_only_value(self) -> None:
        """ProcessingProfile.BACKGROUND_ONLY should have correct value."""
        assert ProcessingProfile.BACKGROUND_ONLY.value == "background_only"

    def test_reformat_value(self) -> None:
        """ProcessingProfile.REFORMAT should have correct value."""
        assert ProcessingProfile.REFORMAT.value == "reformat"


class TestStageCheckpoint:
    """Test StageCheckpoint dataclass."""

    def test_checkpoint_creation(self) -> None:
        """Should create checkpoint with required fields."""
        checkpoint = StageCheckpoint(
            stage=PipelineStage.BACKGROUND_REMOVAL,
            completed_at="2026-01-21T12:00:00Z",
            input_url="https://example.com/input.jpg",
            output_url="https://example.com/output.jpg",
            duration_ms=1500,
        )

        assert checkpoint.stage == PipelineStage.BACKGROUND_REMOVAL
        assert checkpoint.duration_ms == 1500


class TestPipelineJob:
    """Test PipelineJob model."""

    def test_job_defaults(self) -> None:
        """Should have sensible defaults."""
        job = PipelineJob(
            job_id="job-123",
            input_url="https://example.com/image.jpg",
        )

        assert job.status == PipelineStatus.PENDING.value
        assert job.current_stage == PipelineStage.INGEST.value
        assert job.progress_percent == 0


class TestPipelineResult:
    """Test PipelineResult model."""

    def test_successful_result(self) -> None:
        """Should represent successful pipeline completion."""
        result = PipelineResult(
            job_id="job-123",
            success=True,
            input_url="https://example.com/input.jpg",
            output_urls={"format": "https://example.com/output.jpg"},
            stages_completed=["ingest", "format"],
            stages_skipped=[],
            total_duration_ms=5000,
            stage_durations={"ingest": 100, "format": 4900},
            validation_passed=True,
            correlation_id="corr-123",
        )

        assert result.success is True
        assert len(result.output_urls) == 1


class TestPipelineEvent:
    """Test PipelineEvent model."""

    def test_event_creation(self) -> None:
        """Should create event with all fields."""
        event = PipelineEvent(
            event_type="stage_completed",
            job_id="job-123",
            stage="background_removal",
            timestamp="2026-01-21T12:00:00Z",
            data={"output_url": "https://example.com/output.jpg"},
            correlation_id="corr-123",
        )

        assert event.event_type == "stage_completed"
        assert event.stage == "background_removal"


class TestPipelineError:
    """Test PipelineError class."""

    def test_error_with_context(self) -> None:
        """Error should include context fields."""
        error = PipelineError(
            "Test error",
            job_id="job-123",
            stage="background_removal",
            correlation_id="corr-123",
        )

        assert error.context["job_id"] == "job-123"
        assert error.context["stage"] == "background_removal"

    def test_error_is_retryable(self) -> None:
        """PipelineError should be retryable."""
        error = PipelineError("Test error")
        assert error.retryable is True


# =============================================================================
# Service Tests
# =============================================================================


class TestOrchestratorInit:
    """Test orchestrator initialization."""

    def test_default_timeout(self) -> None:
        """Should use default timeout."""
        orchestrator = PipelineOrchestrator()
        assert orchestrator._timeout_seconds == DEFAULT_TIMEOUT_SECONDS

    def test_custom_timeout(self) -> None:
        """Should accept custom timeout."""
        orchestrator = PipelineOrchestrator(timeout_seconds=30)
        assert orchestrator._timeout_seconds == 30

    def test_event_callback(self) -> None:
        """Should accept event callback."""
        callback = MagicMock()
        orchestrator = PipelineOrchestrator(on_event=callback)
        assert orchestrator._on_event is callback


class TestRegisterHandler:
    """Test handler registration."""

    def test_register_handler(self, orchestrator: PipelineOrchestrator) -> None:
        """Should register handler for stage."""

        async def handler(input_url: str, config: dict[str, Any], correlation_id: str) -> str:
            return input_url

        orchestrator.register_handler(PipelineStage.BACKGROUND_REMOVAL, handler)

        assert PipelineStage.BACKGROUND_REMOVAL in orchestrator._handlers


class TestRunPipeline:
    """Test pipeline execution."""

    @pytest.mark.asyncio
    async def test_pipeline_with_no_handlers(self, orchestrator: PipelineOrchestrator) -> None:
        """Should complete with skipped stages when no handlers."""
        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        assert result.success is True
        # INGEST and FORMAT stages - INGEST passes through, FORMAT skipped (no handler)
        assert "ingest" in result.stages_completed

    @pytest.mark.asyncio
    async def test_pipeline_with_handler(
        self, orchestrator: PipelineOrchestrator, success_handler: Any
    ) -> None:
        """Should run stages with registered handlers."""
        orchestrator.register_handler(PipelineStage.FORMAT, success_handler)

        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        assert result.success is True
        assert "format" in result.stages_completed
        assert "format" in result.output_urls

    @pytest.mark.asyncio
    async def test_pipeline_stage_failure(
        self, orchestrator: PipelineOrchestrator, failing_handler: Any
    ) -> None:
        """Should fail when stage handler fails."""
        orchestrator.register_handler(PipelineStage.FORMAT, failing_handler)

        with pytest.raises(PipelineError) as exc_info:
            await orchestrator.run_pipeline(
                "https://example.com/image.jpg",
                profile=ProcessingProfile.REFORMAT,
            )

        assert "format" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_pipeline_timeout(
        self, orchestrator: PipelineOrchestrator, slow_handler: Any
    ) -> None:
        """Should fail when stage times out."""
        orchestrator.register_handler(PipelineStage.FORMAT, slow_handler)

        with pytest.raises(PipelineError) as exc_info:
            await orchestrator.run_pipeline(
                "https://example.com/image.jpg",
                profile=ProcessingProfile.REFORMAT,
            )

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_pipeline_custom_stages(
        self, orchestrator: PipelineOrchestrator, success_handler: Any
    ) -> None:
        """Should run custom stages."""
        orchestrator.register_handler(PipelineStage.BACKGROUND_REMOVAL, success_handler)

        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.CUSTOM,
            custom_stages=[PipelineStage.INGEST, PipelineStage.BACKGROUND_REMOVAL],
        )

        assert result.success is True
        assert "background_removal" in result.stages_completed

    @pytest.mark.asyncio
    async def test_pipeline_with_product_id(self, orchestrator: PipelineOrchestrator) -> None:
        """Should track product ID."""
        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
            product_id="PROD-123",
        )

        job = orchestrator.get_job(result.job_id)
        assert job is not None
        assert job.product_id == "PROD-123"

    @pytest.mark.asyncio
    async def test_pipeline_emits_events(self, success_handler: Any) -> None:
        """Should emit events during processing."""
        events: list[PipelineEvent] = []

        def on_event(event: PipelineEvent) -> None:
            events.append(event)

        orchestrator = PipelineOrchestrator(timeout_seconds=5, on_event=on_event)
        orchestrator.register_handler(PipelineStage.FORMAT, success_handler)

        await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        event_types = [e.event_type for e in events]
        assert "pipeline_started" in event_types
        assert "pipeline_completed" in event_types


class TestGetJob:
    """Test job retrieval."""

    @pytest.mark.asyncio
    async def test_get_existing_job(self, orchestrator: PipelineOrchestrator) -> None:
        """Should return existing job."""
        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        job = orchestrator.get_job(result.job_id)
        assert job is not None
        assert job.job_id == result.job_id

    def test_get_nonexistent_job(self, orchestrator: PipelineOrchestrator) -> None:
        """Should return None for nonexistent job."""
        job = orchestrator.get_job("nonexistent-id")
        assert job is None


class TestGetJobs:
    """Test job listing."""

    @pytest.mark.asyncio
    async def test_get_all_jobs(self, orchestrator: PipelineOrchestrator) -> None:
        """Should return all jobs."""
        await orchestrator.run_pipeline(
            "https://example.com/image1.jpg",
            profile=ProcessingProfile.REFORMAT,
        )
        await orchestrator.run_pipeline(
            "https://example.com/image2.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        jobs = orchestrator.get_jobs()
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_get_jobs_by_status(self, orchestrator: PipelineOrchestrator) -> None:
        """Should filter jobs by status."""
        await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        jobs = orchestrator.get_jobs(status=PipelineStatus.SUCCEEDED)
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_get_jobs_with_limit(self, orchestrator: PipelineOrchestrator) -> None:
        """Should respect limit parameter."""
        for i in range(5):
            await orchestrator.run_pipeline(
                f"https://example.com/image{i}.jpg",
                profile=ProcessingProfile.REFORMAT,
            )

        jobs = orchestrator.get_jobs(limit=3)
        assert len(jobs) == 3


class TestCancelPipeline:
    """Test pipeline cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_nonexistent(self, orchestrator: PipelineOrchestrator) -> None:
        """Should return False for nonexistent job."""
        result = await orchestrator.cancel_pipeline("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_completed(self, orchestrator: PipelineOrchestrator) -> None:
        """Should return False for completed job."""
        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        cancelled = await orchestrator.cancel_pipeline(result.job_id)
        assert cancelled is False


class TestResumePipeline:
    """Test pipeline resume functionality."""

    @pytest.mark.asyncio
    async def test_resume_nonexistent(self, orchestrator: PipelineOrchestrator) -> None:
        """Should raise error for nonexistent job."""
        with pytest.raises(PipelineError):
            await orchestrator.resume_pipeline("nonexistent-id")

    @pytest.mark.asyncio
    async def test_resume_non_failed(self, orchestrator: PipelineOrchestrator) -> None:
        """Should raise error for non-failed job."""
        result = await orchestrator.run_pipeline(
            "https://example.com/image.jpg",
            profile=ProcessingProfile.REFORMAT,
        )

        with pytest.raises(PipelineError):
            await orchestrator.resume_pipeline(result.job_id)


class TestConstants:
    """Test module constants."""

    def test_default_timeout(self) -> None:
        """Default timeout should be reasonable."""
        assert DEFAULT_TIMEOUT_SECONDS >= 60
        assert DEFAULT_TIMEOUT_SECONDS <= 300
