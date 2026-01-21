# services/ml/pipeline_orchestrator.py
"""
Enhancement Pipeline Orchestrator for DevSkyy.

Orchestrates the complete image enhancement workflow:
ingest → validate → background → lighting → upscale → format

Supports:
- Skipping stages via processing profile
- Checkpoint/resume for failed jobs
- Event emission for monitoring
- Configurable pipeline profiles

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections.abc import Callable
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

DEFAULT_TIMEOUT_SECONDS = 120


# =============================================================================
# Models
# =============================================================================


class PipelineStage(str, Enum):
    """Stages in the enhancement pipeline."""

    INGEST = "ingest"
    VALIDATE = "validate"
    BACKGROUND_REMOVAL = "background_removal"
    LIGHTING = "lighting"
    UPSCALE = "upscale"
    FORMAT = "format"
    COMPLETE = "complete"


class PipelineStatus(str, Enum):
    """Status of a pipeline job."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingProfile(str, Enum):
    """Predefined processing profiles."""

    FULL = "full"  # All stages
    QUICK = "quick"  # Skip lighting and upscale
    BACKGROUND_ONLY = "background_only"  # Only background removal
    REFORMAT = "reformat"  # Only format optimization
    CUSTOM = "custom"  # User-defined stages


@dataclass
class StageCheckpoint:
    """Checkpoint data for a completed stage."""

    stage: PipelineStage
    completed_at: str
    input_url: str
    output_url: str
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


class PipelineJob(BaseModel):
    """A pipeline job with all state information."""

    job_id: str
    status: PipelineStatus = PipelineStatus.PENDING
    current_stage: PipelineStage = PipelineStage.INGEST
    progress_percent: int = 0

    # Input/output
    input_url: str
    output_urls: dict[str, str] = {}  # stage -> output_url

    # Processing config
    profile: ProcessingProfile = ProcessingProfile.FULL
    stages_to_run: list[str] = []
    stages_completed: list[str] = []
    stages_skipped: list[str] = []

    # Checkpoints for resume
    checkpoints: list[dict[str, Any]] = []

    # Metadata
    product_id: str | None = None
    source: str = "api"
    correlation_id: str = ""

    # Timestamps
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None

    # Errors
    error_message: str | None = None
    error_stage: str | None = None

    # Metrics
    total_duration_ms: int = 0
    stage_durations: dict[str, int] = {}

    class Config:
        use_enum_values = True


class PipelineResult(BaseModel):
    """Result of a completed pipeline job."""

    job_id: str
    success: bool
    input_url: str
    output_urls: dict[str, str]
    stages_completed: list[str]
    stages_skipped: list[str]
    total_duration_ms: int
    stage_durations: dict[str, int]
    validation_passed: bool
    correlation_id: str


class PipelineEvent(BaseModel):
    """Event emitted during pipeline processing."""

    event_type: str  # stage_started, stage_completed, stage_failed, pipeline_completed
    job_id: str
    stage: str | None = None
    timestamp: str
    data: dict[str, Any] = {}
    correlation_id: str


class PipelineError(DevSkyError):
    """Error during pipeline processing."""

    def __init__(
        self,
        message: str,
        *,
        job_id: str | None = None,
        stage: str | None = None,
        correlation_id: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        context: dict[str, Any] = {}
        if job_id:
            context["job_id"] = job_id
        if stage:
            context["stage"] = stage

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
# Stage Handler Type
# =============================================================================

StageHandler = Callable[
    [str, dict[str, Any], str],  # input_url, config, correlation_id
    Any,  # Coroutine returning output_url
]


# =============================================================================
# Default Profile Configurations
# =============================================================================

PROFILE_STAGES: dict[ProcessingProfile, list[PipelineStage]] = {
    ProcessingProfile.FULL: [
        PipelineStage.INGEST,
        PipelineStage.VALIDATE,
        PipelineStage.BACKGROUND_REMOVAL,
        PipelineStage.LIGHTING,
        PipelineStage.UPSCALE,
        PipelineStage.FORMAT,
    ],
    ProcessingProfile.QUICK: [
        PipelineStage.INGEST,
        PipelineStage.VALIDATE,
        PipelineStage.BACKGROUND_REMOVAL,
        PipelineStage.FORMAT,
    ],
    ProcessingProfile.BACKGROUND_ONLY: [
        PipelineStage.INGEST,
        PipelineStage.VALIDATE,
        PipelineStage.BACKGROUND_REMOVAL,
    ],
    ProcessingProfile.REFORMAT: [
        PipelineStage.INGEST,
        PipelineStage.FORMAT,
    ],
}


# =============================================================================
# Service
# =============================================================================


class PipelineOrchestrator:
    """
    Orchestrates the complete image enhancement pipeline.

    Features:
    - Sequential stage execution with intermediate storage
    - Checkpoint/resume for failed jobs
    - Event emission for monitoring
    - Configurable processing profiles
    - Stage skipping

    Usage:
        orchestrator = PipelineOrchestrator()

        # Register stage handlers
        orchestrator.register_handler(PipelineStage.BACKGROUND_REMOVAL, bg_handler)
        orchestrator.register_handler(PipelineStage.LIGHTING, lighting_handler)

        # Run pipeline
        result = await orchestrator.run_pipeline(
            image_url="https://example.com/product.jpg",
            profile=ProcessingProfile.FULL,
        )
    """

    def __init__(
        self,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        on_event: Callable[[PipelineEvent], None] | None = None,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._on_event = on_event

        # Stage handlers
        self._handlers: dict[PipelineStage, StageHandler] = {}

        # Job storage
        self._jobs: dict[str, PipelineJob] = {}

        # Lock for job operations
        self._lock = asyncio.Lock()

    def register_handler(self, stage: PipelineStage, handler: StageHandler) -> None:
        """Register a handler for a pipeline stage."""
        self._handlers[stage] = handler
        logger.info(f"Registered handler for stage: {stage.value}")

    def get_job(self, job_id: str) -> PipelineJob | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def get_jobs(
        self,
        status: PipelineStatus | None = None,
        limit: int = 100,
    ) -> list[PipelineJob]:
        """Get jobs with optional filtering."""
        jobs = list(self._jobs.values())

        if status:
            jobs = [j for j in jobs if j.status == status.value]

        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    async def run_pipeline(
        self,
        image_url: str,
        *,
        profile: ProcessingProfile = ProcessingProfile.FULL,
        custom_stages: list[PipelineStage] | None = None,
        product_id: str | None = None,
        source: str = "api",
        config: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ) -> PipelineResult:
        """
        Run the complete enhancement pipeline.

        Args:
            image_url: URL of the input image
            profile: Processing profile to use
            custom_stages: Custom stages (only for CUSTOM profile)
            product_id: Optional product ID for tracking
            source: Source of the image (api, woocommerce, etc.)
            config: Stage-specific configuration
            correlation_id: Optional correlation ID

        Returns:
            PipelineResult with all output URLs

        Raises:
            PipelineError: If processing fails
        """
        import time

        # Create job
        job_id = str(uuid.uuid4())
        correlation_id = correlation_id or job_id
        config = config or {}

        # Determine stages to run
        if profile == ProcessingProfile.CUSTOM and custom_stages:
            stages_to_run = custom_stages
        else:
            stages_to_run = PROFILE_STAGES.get(profile, PROFILE_STAGES[ProcessingProfile.FULL])

        # Create job record
        job = PipelineJob(
            job_id=job_id,
            input_url=image_url,
            profile=profile,
            stages_to_run=[s.value for s in stages_to_run],
            product_id=product_id,
            source=source,
            correlation_id=correlation_id,
            created_at=datetime.now(UTC).isoformat(),
        )

        async with self._lock:
            self._jobs[job_id] = job

        logger.info(
            "Starting pipeline",
            extra={
                "job_id": job_id,
                "profile": profile.value,
                "stages": [s.value for s in stages_to_run],
                "correlation_id": correlation_id,
            },
        )

        start_time = time.time()
        job.status = PipelineStatus.RUNNING
        job.started_at = datetime.now(UTC).isoformat()

        self._emit_event("pipeline_started", job)

        # Track current URL through pipeline
        current_url = image_url
        validation_passed = True

        try:
            for stage in stages_to_run:
                stage_start = time.time()
                job.current_stage = stage
                job.progress_percent = int((stages_to_run.index(stage) / len(stages_to_run)) * 100)

                # Check if handler exists
                handler = self._handlers.get(stage)
                if handler is None:
                    # Skip stages without handlers (like INGEST which is a pass-through)
                    if stage in (PipelineStage.INGEST, PipelineStage.COMPLETE):
                        job.stages_completed.append(stage.value)
                        job.output_urls[stage.value] = current_url
                        continue

                    logger.warning(
                        f"No handler for stage {stage.value}, skipping",
                        extra={"correlation_id": correlation_id},
                    )
                    job.stages_skipped.append(stage.value)
                    continue

                self._emit_event("stage_started", job, stage=stage.value)

                try:
                    # Run stage with timeout
                    output_url = await asyncio.wait_for(
                        handler(current_url, config.get(stage.value, {}), correlation_id),
                        timeout=self._timeout_seconds,
                    )

                    # Update tracking
                    stage_duration = int((time.time() - stage_start) * 1000)
                    job.stage_durations[stage.value] = stage_duration
                    job.stages_completed.append(stage.value)
                    job.output_urls[stage.value] = output_url

                    # Save checkpoint
                    checkpoint = StageCheckpoint(
                        stage=stage,
                        completed_at=datetime.now(UTC).isoformat(),
                        input_url=current_url,
                        output_url=output_url,
                        duration_ms=stage_duration,
                    )
                    job.checkpoints.append(checkpoint.__dict__)

                    # Update current URL for next stage
                    current_url = output_url

                    self._emit_event(
                        "stage_completed",
                        job,
                        stage=stage.value,
                        data={"output_url": output_url, "duration_ms": stage_duration},
                    )

                    logger.debug(
                        f"Stage {stage.value} completed",
                        extra={
                            "duration_ms": stage_duration,
                            "correlation_id": correlation_id,
                        },
                    )

                except TimeoutError:
                    raise PipelineError(
                        f"Stage {stage.value} timed out after {self._timeout_seconds}s",
                        job_id=job_id,
                        stage=stage.value,
                        correlation_id=correlation_id,
                    )

                except Exception as e:
                    self._emit_event(
                        "stage_failed",
                        job,
                        stage=stage.value,
                        data={"error": str(e)},
                    )
                    raise PipelineError(
                        f"Stage {stage.value} failed: {e}",
                        job_id=job_id,
                        stage=stage.value,
                        correlation_id=correlation_id,
                        cause=e,
                    )

            # Pipeline completed successfully
            job.status = PipelineStatus.SUCCEEDED
            job.current_stage = PipelineStage.COMPLETE
            job.progress_percent = 100
            job.completed_at = datetime.now(UTC).isoformat()
            job.total_duration_ms = int((time.time() - start_time) * 1000)

            self._emit_event("pipeline_completed", job)

            logger.info(
                "Pipeline completed successfully",
                extra={
                    "job_id": job_id,
                    "total_duration_ms": job.total_duration_ms,
                    "correlation_id": correlation_id,
                },
            )

            return PipelineResult(
                job_id=job_id,
                success=True,
                input_url=image_url,
                output_urls=job.output_urls,
                stages_completed=job.stages_completed,
                stages_skipped=job.stages_skipped,
                total_duration_ms=job.total_duration_ms,
                stage_durations=job.stage_durations,
                validation_passed=validation_passed,
                correlation_id=correlation_id,
            )

        except PipelineError:
            job.status = PipelineStatus.FAILED
            job.completed_at = datetime.now(UTC).isoformat()
            job.total_duration_ms = int((time.time() - start_time) * 1000)
            raise

        except Exception as e:
            job.status = PipelineStatus.FAILED
            job.error_message = str(e)
            job.error_stage = (
                job.current_stage.value
                if isinstance(job.current_stage, PipelineStage)
                else job.current_stage
            )
            job.completed_at = datetime.now(UTC).isoformat()
            job.total_duration_ms = int((time.time() - start_time) * 1000)

            self._emit_event(
                "pipeline_failed",
                job,
                data={"error": str(e)},
            )

            raise PipelineError(
                f"Pipeline failed: {e}",
                job_id=job_id,
                correlation_id=correlation_id,
                cause=e,
            )

    async def resume_pipeline(
        self,
        job_id: str,
        *,
        config: dict[str, Any] | None = None,
    ) -> PipelineResult:
        """
        Resume a failed pipeline from last checkpoint.

        Args:
            job_id: Job ID to resume
            config: Optional updated configuration

        Returns:
            PipelineResult

        Raises:
            PipelineError: If job not found or cannot be resumed
        """
        job = self._jobs.get(job_id)
        if not job:
            raise PipelineError(
                f"Job {job_id} not found",
                job_id=job_id,
            )

        if job.status not in (PipelineStatus.FAILED.value, PipelineStatus.PAUSED.value):
            raise PipelineError(
                f"Job {job_id} cannot be resumed (status: {job.status})",
                job_id=job_id,
            )

        # Get last checkpoint
        if not job.checkpoints:
            # No checkpoints, restart from beginning
            return await self.run_pipeline(
                job.input_url,
                profile=ProcessingProfile(job.profile),
                product_id=job.product_id,
                source=job.source,
                config=config,
                correlation_id=job.correlation_id,
            )

        last_checkpoint = job.checkpoints[-1]
        last_stage = PipelineStage(last_checkpoint["stage"])
        resume_url = last_checkpoint["output_url"]

        # Determine remaining stages
        all_stages = [PipelineStage(s) for s in job.stages_to_run]
        try:
            start_idx = all_stages.index(last_stage) + 1
        except ValueError:
            start_idx = 0

        remaining_stages = all_stages[start_idx:]

        if not remaining_stages:
            # All stages already completed
            job.status = PipelineStatus.SUCCEEDED
            return PipelineResult(
                job_id=job_id,
                success=True,
                input_url=job.input_url,
                output_urls=job.output_urls,
                stages_completed=job.stages_completed,
                stages_skipped=job.stages_skipped,
                total_duration_ms=job.total_duration_ms,
                stage_durations=job.stage_durations,
                validation_passed=True,
                correlation_id=job.correlation_id,
            )

        logger.info(
            f"Resuming pipeline from stage {remaining_stages[0].value}",
            extra={
                "job_id": job_id,
                "correlation_id": job.correlation_id,
            },
        )

        # Run remaining stages
        return await self.run_pipeline(
            resume_url,
            profile=ProcessingProfile.CUSTOM,
            custom_stages=remaining_stages,
            product_id=job.product_id,
            source=job.source,
            config=config,
            correlation_id=job.correlation_id,
        )

    async def cancel_pipeline(self, job_id: str) -> bool:
        """
        Cancel a running pipeline job.

        Args:
            job_id: Job ID to cancel

        Returns:
            True if cancelled, False if not found or already complete
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False

            if job.status in (
                PipelineStatus.SUCCEEDED.value,
                PipelineStatus.FAILED.value,
                PipelineStatus.CANCELLED.value,
            ):
                return False

            job.status = PipelineStatus.CANCELLED
            job.completed_at = datetime.now(UTC).isoformat()

        self._emit_event("pipeline_cancelled", job)
        logger.info(f"Pipeline {job_id} cancelled")
        return True

    def _emit_event(
        self,
        event_type: str,
        job: PipelineJob,
        stage: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Emit a pipeline event."""
        if self._on_event is None:
            return

        event = PipelineEvent(
            event_type=event_type,
            job_id=job.job_id,
            stage=stage,
            timestamp=datetime.now(UTC).isoformat(),
            data=data or {},
            correlation_id=job.correlation_id,
        )

        try:
            self._on_event(event)
        except Exception as e:
            logger.error(f"Event handler failed: {e}")


__all__ = [
    "PipelineOrchestrator",
    "PipelineJob",
    "PipelineResult",
    "PipelineEvent",
    "PipelineError",
    "PipelineStage",
    "PipelineStatus",
    "ProcessingProfile",
    "StageCheckpoint",
]
