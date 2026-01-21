# tests/services/test_processing_queue.py
"""Unit tests for ProcessingQueue."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from services.ml.processing_queue import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_DELAY_SECONDS,
    FallbackChain,
    Job,
    JobStatus,
    ProcessingQueue,
    ProcessingQueueError,
    QueueMetrics,
    TaskType,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def queue() -> ProcessingQueue:
    """Create processing queue with fast retry for testing."""
    return ProcessingQueue(
        max_retries=2,
        retry_delay_seconds=0,  # No delay for tests
        max_concurrent_jobs=5,
    )


@pytest.fixture
def success_handler() -> MagicMock:
    """Create handler that always succeeds."""

    async def handler(
        input_data: dict[str, Any], model: str, correlation_id: str
    ) -> dict[str, Any]:
        return {"result_url": "https://example.com/result.jpg", "model": model}

    return handler


@pytest.fixture
def failing_handler() -> MagicMock:
    """Create handler that always fails."""

    async def handler(
        input_data: dict[str, Any], model: str, correlation_id: str
    ) -> dict[str, Any]:
        raise ValueError(f"Model {model} failed")

    return handler


# =============================================================================
# Model Tests
# =============================================================================


class TestJobStatus:
    """Test JobStatus enum."""

    def test_pending_value(self) -> None:
        """JobStatus.PENDING should have correct value."""
        assert JobStatus.PENDING.value == "pending"

    def test_running_value(self) -> None:
        """JobStatus.RUNNING should have correct value."""
        assert JobStatus.RUNNING.value == "running"

    def test_succeeded_value(self) -> None:
        """JobStatus.SUCCEEDED should have correct value."""
        assert JobStatus.SUCCEEDED.value == "succeeded"

    def test_failed_value(self) -> None:
        """JobStatus.FAILED should have correct value."""
        assert JobStatus.FAILED.value == "failed"

    def test_retrying_value(self) -> None:
        """JobStatus.RETRYING should have correct value."""
        assert JobStatus.RETRYING.value == "retrying"

    def test_dead_letter_value(self) -> None:
        """JobStatus.DEAD_LETTER should have correct value."""
        assert JobStatus.DEAD_LETTER.value == "dead_letter"


class TestTaskType:
    """Test TaskType enum."""

    def test_background_removal_value(self) -> None:
        """TaskType.BACKGROUND_REMOVAL should have correct value."""
        assert TaskType.BACKGROUND_REMOVAL.value == "background_removal"

    def test_upscaling_value(self) -> None:
        """TaskType.UPSCALING should have correct value."""
        assert TaskType.UPSCALING.value == "upscaling"

    def test_lighting_value(self) -> None:
        """TaskType.LIGHTING should have correct value."""
        assert TaskType.LIGHTING.value == "lighting"

    def test_format_optimization_value(self) -> None:
        """TaskType.FORMAT_OPTIMIZATION should have correct value."""
        assert TaskType.FORMAT_OPTIMIZATION.value == "format_optimization"

    def test_authenticity_validation_value(self) -> None:
        """TaskType.AUTHENTICITY_VALIDATION should have correct value."""
        assert TaskType.AUTHENTICITY_VALIDATION.value == "authenticity_validation"

    def test_watermarking_value(self) -> None:
        """TaskType.WATERMARKING should have correct value."""
        assert TaskType.WATERMARKING.value == "watermarking"

    def test_3d_generation_value(self) -> None:
        """TaskType.THREE_D_GENERATION should have correct value."""
        assert TaskType.THREE_D_GENERATION.value == "3d_generation"


class TestFallbackChain:
    """Test FallbackChain dataclass."""

    def test_get_all_models_with_fallbacks(self) -> None:
        """Should return primary plus fallback models."""
        chain = FallbackChain(
            task_type=TaskType.BACKGROUND_REMOVAL,
            primary_model="model-a",
            fallback_models=["model-b", "model-c"],
        )

        models = chain.get_all_models()

        assert models == ["model-a", "model-b", "model-c"]

    def test_get_all_models_no_fallbacks(self) -> None:
        """Should return only primary when no fallbacks."""
        chain = FallbackChain(
            task_type=TaskType.UPSCALING,
            primary_model="model-a",
            fallback_models=[],
        )

        models = chain.get_all_models()

        assert models == ["model-a"]


class TestJob:
    """Test Job model."""

    def test_is_complete_when_succeeded(self) -> None:
        """is_complete should return True for succeeded status."""
        job = Job(
            job_id="job-123",
            task_type=TaskType.BACKGROUND_REMOVAL,
            input_data={"image_url": "https://example.com/image.jpg"},
            status=JobStatus.SUCCEEDED,
        )
        assert job.is_complete is True

    def test_is_complete_when_failed(self) -> None:
        """is_complete should return True for failed status."""
        job = Job(
            job_id="job-123",
            task_type=TaskType.BACKGROUND_REMOVAL,
            input_data={"image_url": "https://example.com/image.jpg"},
            status=JobStatus.FAILED,
        )
        assert job.is_complete is True

    def test_is_complete_when_dead_letter(self) -> None:
        """is_complete should return True for dead letter status."""
        job = Job(
            job_id="job-123",
            task_type=TaskType.BACKGROUND_REMOVAL,
            input_data={"image_url": "https://example.com/image.jpg"},
            status=JobStatus.DEAD_LETTER,
        )
        assert job.is_complete is True

    def test_is_complete_when_pending(self) -> None:
        """is_complete should return False for pending status."""
        job = Job(
            job_id="job-123",
            task_type=TaskType.BACKGROUND_REMOVAL,
            input_data={"image_url": "https://example.com/image.jpg"},
            status=JobStatus.PENDING,
        )
        assert job.is_complete is False

    def test_is_complete_when_running(self) -> None:
        """is_complete should return False for running status."""
        job = Job(
            job_id="job-123",
            task_type=TaskType.BACKGROUND_REMOVAL,
            input_data={"image_url": "https://example.com/image.jpg"},
            status=JobStatus.RUNNING,
        )
        assert job.is_complete is False


class TestQueueMetrics:
    """Test QueueMetrics model."""

    def test_default_values(self) -> None:
        """Should have sensible defaults."""
        metrics = QueueMetrics()
        assert metrics.total_jobs == 0
        assert metrics.pending_jobs == 0
        assert metrics.running_jobs == 0
        assert metrics.succeeded_jobs == 0
        assert metrics.failed_jobs == 0
        assert metrics.dlq_jobs == 0
        assert metrics.success_rate == 0.0
        assert metrics.fallback_rate == 0.0
        assert metrics.dlq_rate == 0.0
        assert metrics.avg_processing_time_ms == 0


class TestProcessingQueueError:
    """Test ProcessingQueueError class."""

    def test_error_with_context(self) -> None:
        """Error should include context fields."""
        error = ProcessingQueueError(
            "Test error",
            job_id="job-123",
            task_type="background_removal",
            correlation_id="corr-123",
        )
        assert error.context["job_id"] == "job-123"
        assert error.context["task_type"] == "background_removal"

    def test_error_is_retryable(self) -> None:
        """ProcessingQueueError should be retryable."""
        error = ProcessingQueueError("Test error")
        assert error.retryable is True


# =============================================================================
# Service Tests
# =============================================================================


class TestQueueInit:
    """Test queue initialization."""

    def test_default_max_retries(self) -> None:
        """Should use default max retries."""
        queue = ProcessingQueue()
        assert queue._max_retries == DEFAULT_MAX_RETRIES

    def test_default_retry_delay(self) -> None:
        """Should use default retry delay."""
        queue = ProcessingQueue()
        assert queue._retry_delay_seconds == DEFAULT_RETRY_DELAY_SECONDS

    def test_custom_max_retries(self) -> None:
        """Should accept custom max retries."""
        queue = ProcessingQueue(max_retries=5)
        assert queue._max_retries == 5

    def test_custom_retry_delay(self) -> None:
        """Should accept custom retry delay."""
        queue = ProcessingQueue(retry_delay_seconds=10)
        assert queue._retry_delay_seconds == 10

    def test_custom_max_concurrent(self) -> None:
        """Should accept custom max concurrent jobs."""
        queue = ProcessingQueue(max_concurrent_jobs=20)
        assert queue._max_concurrent == 20

    def test_dlq_notification_callback(self) -> None:
        """Should accept DLQ notification callback."""
        callback = MagicMock()
        queue = ProcessingQueue(on_dlq_notification=callback)
        assert queue._on_dlq_notification is callback


class TestRegisterHandler:
    """Test handler registration."""

    def test_register_handler(self, queue: ProcessingQueue) -> None:
        """Should register handler for task type."""

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            return {}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        assert TaskType.BACKGROUND_REMOVAL in queue._handlers
        assert queue._handlers[TaskType.BACKGROUND_REMOVAL] is handler


class TestSetFallbackChain:
    """Test fallback chain configuration."""

    def test_set_custom_chain(self, queue: ProcessingQueue) -> None:
        """Should set custom fallback chain."""
        chain = FallbackChain(
            task_type=TaskType.BACKGROUND_REMOVAL,
            primary_model="custom-model",
            fallback_models=["fallback-1", "fallback-2"],
        )

        queue.set_fallback_chain(chain)

        assert queue._fallback_chains[TaskType.BACKGROUND_REMOVAL] is chain


class TestSubmitJob:
    """Test job submission."""

    @pytest.mark.asyncio
    async def test_submit_job_returns_id(self, queue: ProcessingQueue) -> None:
        """Should return job ID."""
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        assert job_id is not None
        assert len(job_id) > 0

    @pytest.mark.asyncio
    async def test_submit_job_creates_job(self, queue: ProcessingQueue) -> None:
        """Should create job in queue."""
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        job = queue.get_job(job_id)
        assert job is not None
        assert job.task_type == TaskType.BACKGROUND_REMOVAL.value

    @pytest.mark.asyncio
    async def test_submit_job_with_correlation_id(self, queue: ProcessingQueue) -> None:
        """Should use provided correlation ID."""
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
            correlation_id="test-corr-123",
        )

        job = queue.get_job(job_id)
        assert job is not None
        assert job.correlation_id == "test-corr-123"

    @pytest.mark.asyncio
    async def test_submit_job_updates_metrics(self, queue: ProcessingQueue) -> None:
        """Should update metrics on submit."""
        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        metrics = queue.get_metrics()
        assert metrics.total_jobs == 1


class TestGetJob:
    """Test job retrieval."""

    @pytest.mark.asyncio
    async def test_get_existing_job(self, queue: ProcessingQueue) -> None:
        """Should return existing job."""
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        job = queue.get_job(job_id)
        assert job is not None
        assert job.job_id == job_id

    def test_get_nonexistent_job(self, queue: ProcessingQueue) -> None:
        """Should return None for nonexistent job."""
        job = queue.get_job("nonexistent-id")
        assert job is None


class TestGetJobs:
    """Test job listing."""

    @pytest.mark.asyncio
    async def test_get_all_jobs(self, queue: ProcessingQueue) -> None:
        """Should return all jobs."""
        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image1.jpg"},
        )
        await queue.submit_job(
            TaskType.UPSCALING,
            {"image_url": "https://example.com/image2.jpg"},
        )

        jobs = queue.get_jobs()
        assert len(jobs) == 2

    @pytest.mark.asyncio
    async def test_get_jobs_by_task_type(self, queue: ProcessingQueue) -> None:
        """Should filter jobs by task type."""
        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image1.jpg"},
        )
        await queue.submit_job(
            TaskType.UPSCALING,
            {"image_url": "https://example.com/image2.jpg"},
        )

        jobs = queue.get_jobs(task_type=TaskType.BACKGROUND_REMOVAL)
        assert len(jobs) == 1
        assert jobs[0].task_type == TaskType.BACKGROUND_REMOVAL.value

    @pytest.mark.asyncio
    async def test_get_jobs_with_limit(self, queue: ProcessingQueue) -> None:
        """Should respect limit parameter."""
        for i in range(5):
            await queue.submit_job(
                TaskType.BACKGROUND_REMOVAL,
                {"image_url": f"https://example.com/image{i}.jpg"},
            )

        jobs = queue.get_jobs(limit=3)
        assert len(jobs) == 3


class TestJobProcessing:
    """Test job processing."""

    @pytest.mark.asyncio
    async def test_job_succeeds_with_primary_model(self, queue: ProcessingQueue) -> None:
        """Should succeed with primary model."""
        success_count = 0

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            nonlocal success_count
            success_count += 1
            return {"result_url": "https://example.com/result.jpg"}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        job = queue.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.SUCCEEDED.value
        assert job.result is not None
        assert success_count == 1

    @pytest.mark.asyncio
    async def test_job_uses_fallback_on_failure(self, queue: ProcessingQueue) -> None:
        """Should try fallback model when primary fails."""
        call_count = 0

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Primary failed")
            return {"result_url": "https://example.com/result.jpg"}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        job = queue.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.SUCCEEDED.value
        assert len(job.models_tried) == 2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_job_moves_to_dlq_when_all_fail(self, queue: ProcessingQueue) -> None:
        """Should move to DLQ when all models fail."""

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError(f"Model {model} failed")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        job = queue.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.DEAD_LETTER.value
        assert len(job.error_messages) > 0

    @pytest.mark.asyncio
    async def test_dlq_notification_called(self, queue: ProcessingQueue) -> None:
        """Should call DLQ notification callback."""
        notification_received = []

        def on_dlq(job: Job) -> None:
            notification_received.append(job.job_id)

        queue._on_dlq_notification = on_dlq

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError("Always fails")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        # Wait for processing
        await asyncio.sleep(0.5)

        assert job_id in notification_received


class TestRetryDLQJob:
    """Test DLQ retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_dlq_job_requeues(self, queue: ProcessingQueue) -> None:
        """Should requeue job from DLQ."""

        # First make a job fail to DLQ
        async def always_fail(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError("Fail")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, always_fail)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        # Now retry it
        success = await queue.retry_dlq_job(job_id)
        assert success is True

        job = queue.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.PENDING.value
        assert job.retry_count == 0
        assert len(job.models_tried) == 0

    @pytest.mark.asyncio
    async def test_retry_nonexistent_job(self, queue: ProcessingQueue) -> None:
        """Should return False for nonexistent job."""
        success = await queue.retry_dlq_job("nonexistent-id")
        assert success is False

    @pytest.mark.asyncio
    async def test_retry_non_dlq_job(self, queue: ProcessingQueue) -> None:
        """Should return False for job not in DLQ."""
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        success = await queue.retry_dlq_job(job_id)
        assert success is False


class TestSkipDLQJob:
    """Test DLQ skip functionality."""

    @pytest.mark.asyncio
    async def test_skip_dlq_job_marks_failed(self, queue: ProcessingQueue) -> None:
        """Should mark DLQ job as failed."""

        # First make a job fail to DLQ
        async def always_fail(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError("Fail")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, always_fail)

        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        # Now skip it
        success = await queue.skip_dlq_job(job_id)
        assert success is True

        job = queue.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.FAILED.value

    @pytest.mark.asyncio
    async def test_skip_nonexistent_job(self, queue: ProcessingQueue) -> None:
        """Should return False for nonexistent job."""
        success = await queue.skip_dlq_job("nonexistent-id")
        assert success is False


class TestGetDLQJobs:
    """Test DLQ job listing."""

    @pytest.mark.asyncio
    async def test_get_dlq_jobs(self, queue: ProcessingQueue) -> None:
        """Should return jobs in DLQ."""

        async def always_fail(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError("Fail")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, always_fail)

        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        dlq_jobs = queue.get_dlq_jobs()
        assert len(dlq_jobs) == 1


class TestGetMetrics:
    """Test metrics retrieval."""

    @pytest.mark.asyncio
    async def test_metrics_update_on_success(self, queue: ProcessingQueue) -> None:
        """Should update success metrics."""

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            return {"result_url": "https://example.com/result.jpg"}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        metrics = queue.get_metrics()
        assert metrics.succeeded_jobs == 1
        assert metrics.success_rate == 1.0

    @pytest.mark.asyncio
    async def test_metrics_update_on_dlq(self, queue: ProcessingQueue) -> None:
        """Should update DLQ metrics."""

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            raise ValueError("Fail")

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        metrics = queue.get_metrics()
        assert metrics.dlq_jobs == 1
        assert metrics.dlq_rate > 0

    @pytest.mark.asyncio
    async def test_metrics_fallback_rate(self, queue: ProcessingQueue) -> None:
        """Should track fallback rate."""
        call_count = 0

        async def handler(
            input_data: dict[str, Any], model: str, correlation_id: str
        ) -> dict[str, Any]:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Primary failed")
            return {"result_url": "https://example.com/result.jpg"}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handler)

        await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "https://example.com/image.jpg"},
        )

        await asyncio.sleep(0.5)

        metrics = queue.get_metrics()
        assert metrics.fallback_rate > 0


class TestConstants:
    """Test module constants."""

    def test_default_max_retries(self) -> None:
        """Default max retries should be reasonable."""
        assert DEFAULT_MAX_RETRIES >= 2
        assert DEFAULT_MAX_RETRIES <= 10

    def test_default_retry_delay(self) -> None:
        """Default retry delay should be reasonable."""
        assert DEFAULT_RETRY_DELAY_SECONDS >= 1
        assert DEFAULT_RETRY_DELAY_SECONDS <= 60
