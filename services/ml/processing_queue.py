# services/ml/processing_queue.py
"""
Processing Queue with Fallback Chain for DevSkyy.

Implements a robust job queue system that automatically retries
failed ML tasks with alternative models before moving to dead letter queue.

Features:
- Fallback model chains per task type
- Dead letter queue for exhausted retries
- Admin notifications
- Metrics tracking

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import deque
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from errors.production_errors import (
    DevSkyError,
    DevSkyErrorCode,
    DevSkyErrorSeverity,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY_SECONDS = 5


# =============================================================================
# Models
# =============================================================================


class JobStatus(str, Enum):
    """Status of a processing job."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


class TaskType(str, Enum):
    """Types of ML processing tasks."""

    BACKGROUND_REMOVAL = "background_removal"
    UPSCALING = "upscaling"
    LIGHTING = "lighting"
    FORMAT_OPTIMIZATION = "format_optimization"
    AUTHENTICITY_VALIDATION = "authenticity_validation"
    WATERMARKING = "watermarking"
    THREE_D_GENERATION = "3d_generation"


@dataclass
class FallbackChain:
    """Defines fallback models for a task type."""

    task_type: TaskType
    primary_model: str
    fallback_models: list[str] = field(default_factory=list)

    def get_all_models(self) -> list[str]:
        """Get all models in order."""
        return [self.primary_model] + self.fallback_models


class Job(BaseModel):
    """A processing job in the queue."""

    job_id: str
    task_type: TaskType
    input_data: dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    current_model: str | None = None
    models_tried: list[str] = []
    retry_count: int = 0
    error_messages: list[str] = []
    result: dict[str, Any] | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    correlation_id: str = ""

    class Config:
        use_enum_values = True

    @property
    def is_complete(self) -> bool:
        """Check if job is in terminal state."""
        return self.status in (
            JobStatus.SUCCEEDED,
            JobStatus.FAILED,
            JobStatus.DEAD_LETTER,
        )


class QueueMetrics(BaseModel):
    """Metrics for the processing queue."""

    total_jobs: int = 0
    pending_jobs: int = 0
    running_jobs: int = 0
    succeeded_jobs: int = 0
    failed_jobs: int = 0
    dlq_jobs: int = 0
    success_rate: float = 0.0
    fallback_rate: float = 0.0
    dlq_rate: float = 0.0
    avg_processing_time_ms: int = 0


class ProcessingQueueError(DevSkyError):
    """Error in processing queue operations."""

    def __init__(
        self,
        message: str,
        *,
        job_id: str | None = None,
        task_type: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context: dict[str, Any] = {}
        if job_id:
            context["job_id"] = job_id
        if task_type:
            context["task_type"] = task_type

        super().__init__(
            message,
            code=DevSkyErrorCode.IMAGE_PROCESSING_FAILED,
            severity=DevSkyErrorSeverity.ERROR,
            context=context,
            cause=cause,
            correlation_id=correlation_id,
            retryable=True,
        )


# =============================================================================
# Default Fallback Chains
# =============================================================================

DEFAULT_FALLBACK_CHAINS: dict[TaskType, FallbackChain] = {
    TaskType.BACKGROUND_REMOVAL: FallbackChain(
        task_type=TaskType.BACKGROUND_REMOVAL,
        primary_model="lucataco/remove-bg:95fcc2a26d3899cd6c2691c900465aaeff466285a65c14638cc5f36f34befaf1",
        fallback_models=[
            "cjwbw/rembg:fb8af171cfa1616ddcf1242c093f9c46bcada5ad4cf6f2fbe8b81b330ec5c003",
        ],
    ),
    TaskType.UPSCALING: FallbackChain(
        task_type=TaskType.UPSCALING,
        primary_model="nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
        fallback_models=[
            "xinntao/realesrgan:1b976a4d456ed9e4d1a846597b7614e79eadad3032e9124fa63c8acb4e3b5bf4",
        ],
    ),
    TaskType.LIGHTING: FallbackChain(
        task_type=TaskType.LIGHTING,
        primary_model="tencentarc/gfpgan:9283608cc6b7be6b65a8e44983db012355fde4132009bf99d976b2f0896856a3",
        fallback_models=[
            "xinntao/realesrgan:1b976a4d456ed9e4d1a846597b7614e79eadad3032e9124fa63c8acb4e3b5bf4",
        ],
    ),
    TaskType.THREE_D_GENERATION: FallbackChain(
        task_type=TaskType.THREE_D_GENERATION,
        primary_model="stability-ai/tripo-3d:latest",
        fallback_models=[],
    ),
}


# =============================================================================
# Task Handlers Type
# =============================================================================

TaskHandler = Callable[
    [dict[str, Any], str, str],
    Coroutine[Any, Any, dict[str, Any]],
]


# =============================================================================
# Service
# =============================================================================


class ProcessingQueue:
    """
    Processing queue with automatic fallback to alternative models.

    Features:
    - Job queue management (pending, running, completed)
    - Automatic retries with fallback models
    - Dead letter queue for exhausted retries
    - Metrics tracking
    - Admin notifications (via callback)

    Usage:
        queue = ProcessingQueue()

        # Register task handler
        async def handle_background_removal(input_data, model, correlation_id):
            # Process and return result
            return {"result_url": "..."}

        queue.register_handler(TaskType.BACKGROUND_REMOVAL, handle_background_removal)

        # Submit job
        job_id = await queue.submit_job(
            TaskType.BACKGROUND_REMOVAL,
            {"image_url": "..."},
        )

        # Check status
        job = queue.get_job(job_id)
    """

    def __init__(
        self,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay_seconds: int = DEFAULT_RETRY_DELAY_SECONDS,
        max_concurrent_jobs: int = 10,
        on_dlq_notification: Callable[[Job], None] | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._max_concurrent = max_concurrent_jobs
        self._on_dlq_notification = on_dlq_notification

        # Job storage
        self._jobs: dict[str, Job] = {}
        self._pending_queue: deque[str] = deque()
        self._dead_letter_queue: deque[str] = deque()

        # Handlers
        self._handlers: dict[TaskType, TaskHandler] = {}

        # Fallback chains
        self._fallback_chains: dict[TaskType, FallbackChain] = DEFAULT_FALLBACK_CHAINS.copy()

        # Metrics
        self._metrics = QueueMetrics()
        self._processing_times: list[int] = []

        # Concurrency control
        self._running_count = 0
        self._lock = asyncio.Lock()
        self._processor_task: asyncio.Task[None] | None = None

    def register_handler(self, task_type: TaskType, handler: TaskHandler) -> None:
        """Register a handler for a task type."""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for {task_type.value}")

    def set_fallback_chain(self, chain: FallbackChain) -> None:
        """Set custom fallback chain for a task type."""
        self._fallback_chains[chain.task_type] = chain

    async def submit_job(
        self,
        task_type: TaskType,
        input_data: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> str:
        """
        Submit a new job to the queue.

        Args:
            task_type: Type of ML task
            input_data: Input data for the task
            correlation_id: Optional correlation ID

        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        correlation_id = correlation_id or job_id

        job = Job(
            job_id=job_id,
            task_type=task_type,
            input_data=input_data,
            status=JobStatus.PENDING,
            created_at=datetime.now(UTC).isoformat(),
            correlation_id=correlation_id,
        )

        async with self._lock:
            self._jobs[job_id] = job
            self._pending_queue.append(job_id)
            self._metrics.total_jobs += 1
            self._metrics.pending_jobs += 1

        logger.info(
            "Job submitted",
            extra={
                "job_id": job_id,
                "task_type": task_type.value,
                "correlation_id": correlation_id,
            },
        )

        # Start processor if not running
        if self._processor_task is None or self._processor_task.done():
            self._processor_task = asyncio.create_task(self._process_queue())

        return job_id

    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_jobs(
        self,
        status: JobStatus | None = None,
        task_type: TaskType | None = None,
        limit: int = 100,
    ) -> list[Job]:
        """Get jobs with optional filtering."""
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status.value]

        if task_type:
            jobs = [j for j in jobs if j.task_type == task_type.value]

        # Sort by created_at descending
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        return jobs[:limit]

    def get_dlq_jobs(self) -> list[Job]:
        """Get all jobs in dead letter queue."""
        return [self._jobs[jid] for jid in self._dead_letter_queue if jid in self._jobs]

    async def retry_dlq_job(self, job_id: str) -> bool:
        """
        Retry a job from the dead letter queue.

        Args:
            job_id: Job ID to retry

        Returns:
            True if job was requeued
        """
        async with self._lock:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]
            if job.status != JobStatus.DEAD_LETTER.value:
                return False

            # Reset job for retry
            job.status = JobStatus.PENDING
            job.retry_count = 0
            job.models_tried = []
            job.error_messages = []

            # Remove from DLQ, add to pending
            if job_id in self._dead_letter_queue:
                self._dead_letter_queue.remove(job_id)
                self._metrics.dlq_jobs -= 1

            self._pending_queue.append(job_id)
            self._metrics.pending_jobs += 1

        logger.info(f"Job {job_id} requeued from DLQ")
        return True

    async def skip_dlq_job(self, job_id: str) -> bool:
        """
        Mark a DLQ job as skipped (failed).

        Args:
            job_id: Job ID to skip

        Returns:
            True if job was marked as failed
        """
        async with self._lock:
            if job_id not in self._jobs:
                return False

            job = self._jobs[job_id]
            if job.status != JobStatus.DEAD_LETTER.value:
                return False

            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(UTC).isoformat()

            if job_id in self._dead_letter_queue:
                self._dead_letter_queue.remove(job_id)
                self._metrics.dlq_jobs -= 1
                self._metrics.failed_jobs += 1

        logger.info(f"Job {job_id} marked as failed (skipped)")
        return True

    def get_metrics(self) -> QueueMetrics:
        """Get current queue metrics."""
        # Update derived metrics
        completed = self._metrics.succeeded_jobs + self._metrics.failed_jobs
        if completed > 0:
            self._metrics.success_rate = self._metrics.succeeded_jobs / completed

        total_attempted = self._metrics.total_jobs
        if total_attempted > 0:
            self._metrics.dlq_rate = self._metrics.dlq_jobs / total_attempted

            # Count jobs that used fallback
            fallback_count = sum(1 for job in self._jobs.values() if len(job.models_tried) > 1)
            self._metrics.fallback_rate = fallback_count / total_attempted

        if self._processing_times:
            self._metrics.avg_processing_time_ms = int(
                sum(self._processing_times) / len(self._processing_times)
            )

        return self._metrics

    async def _process_queue(self) -> None:
        """Background task to process pending jobs."""
        while True:
            # Check for pending jobs
            job_id: str | None = None
            async with self._lock:
                if self._pending_queue and self._running_count < self._max_concurrent:
                    job_id = self._pending_queue.popleft()
                    self._running_count += 1
                    self._metrics.pending_jobs -= 1
                    self._metrics.running_jobs += 1

            if job_id:
                # Process job in background
                asyncio.create_task(self._process_job(job_id))
            else:
                # Wait a bit before checking again
                await asyncio.sleep(0.1)

                # Exit if no pending jobs and nothing running
                async with self._lock:
                    if not self._pending_queue and self._running_count == 0:
                        break

    async def _process_job(self, job_id: str) -> None:
        """Process a single job with fallback handling."""
        import time

        job = self._jobs.get(job_id)
        if not job:
            return

        start_time = time.time()
        job.started_at = datetime.now(UTC).isoformat()
        job.status = JobStatus.RUNNING

        # Get fallback chain
        chain = self._fallback_chains.get(TaskType(job.task_type))
        if not chain:
            await self._mark_job_failed(job, f"No fallback chain for task type: {job.task_type}")
            return

        # Get handler
        handler = self._handlers.get(TaskType(job.task_type))
        if not handler:
            await self._mark_job_failed(job, f"No handler for task type: {job.task_type}")
            return

        # Try each model in the chain
        models = chain.get_all_models()
        success = False

        for model in models:
            if model in job.models_tried:
                continue

            job.current_model = model
            job.models_tried.append(model)

            try:
                logger.debug(
                    f"Trying model {model} for job {job_id}",
                    extra={"correlation_id": job.correlation_id},
                )

                result = await handler(job.input_data, model, job.correlation_id)

                # Success!
                job.result = result
                job.status = JobStatus.SUCCEEDED
                job.completed_at = datetime.now(UTC).isoformat()
                success = True

                processing_time = int((time.time() - start_time) * 1000)
                self._processing_times.append(processing_time)

                async with self._lock:
                    self._running_count -= 1
                    self._metrics.running_jobs -= 1
                    self._metrics.succeeded_jobs += 1

                logger.info(
                    f"Job {job_id} succeeded with model {model}",
                    extra={
                        "processing_time_ms": processing_time,
                        "correlation_id": job.correlation_id,
                    },
                )
                break

            except Exception as e:
                error_msg = f"Model {model} failed: {e}"
                job.error_messages.append(error_msg)
                logger.warning(
                    error_msg,
                    extra={"correlation_id": job.correlation_id},
                )

                # Add delay before trying next model
                await asyncio.sleep(self._retry_delay_seconds)

        if not success:
            # All models exhausted - move to DLQ
            await self._move_to_dlq(job)

    async def _mark_job_failed(self, job: Job, error: str) -> None:
        """Mark job as failed immediately."""
        job.status = JobStatus.FAILED
        job.error_messages.append(error)
        job.completed_at = datetime.now(UTC).isoformat()

        async with self._lock:
            self._running_count -= 1
            self._metrics.running_jobs -= 1
            self._metrics.failed_jobs += 1

        logger.error(
            f"Job {job.job_id} failed: {error}",
            extra={"correlation_id": job.correlation_id},
        )

    async def _move_to_dlq(self, job: Job) -> None:
        """Move job to dead letter queue."""
        job.status = JobStatus.DEAD_LETTER
        job.completed_at = datetime.now(UTC).isoformat()

        async with self._lock:
            self._running_count -= 1
            self._metrics.running_jobs -= 1
            self._metrics.dlq_jobs += 1
            self._dead_letter_queue.append(job.job_id)

        logger.error(
            f"Job {job.job_id} moved to DLQ after all models failed",
            extra={
                "models_tried": job.models_tried,
                "correlation_id": job.correlation_id,
            },
        )

        # Notify admin
        if self._on_dlq_notification:
            try:
                self._on_dlq_notification(job)
            except Exception as e:
                logger.error(f"DLQ notification failed: {e}")


__all__ = [
    "ProcessingQueue",
    "Job",
    "JobStatus",
    "TaskType",
    "FallbackChain",
    "QueueMetrics",
    "ProcessingQueueError",
]
