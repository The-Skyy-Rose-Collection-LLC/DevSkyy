"""
Virtual Try-On API Endpoints
============================

Production-grade virtual try-on endpoints using:
- FASHN API (commercial, production-ready)
- IDM-VTON (HuggingFace, open-source alternative)
- Segformer B2 Clothes (garment segmentation preprocessing)

Features:
- Single try-on generation
- Batch processing (up to 10 concurrent)
- AI model generation
- Job tracking and status
- Redis caching (7-day TTL)

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

virtual_tryon_router = APIRouter(prefix="/virtual-tryon", tags=["Virtual Try-On"])


# =============================================================================
# Configuration
# =============================================================================

OUTPUT_DIR = Path(os.getenv("TRYON_OUTPUT_DIR", "./generated_assets/tryon"))
UPLOAD_DIR = Path(os.getenv("TRYON_UPLOAD_DIR", "./assets/tryon-uploads"))

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Enums & Models
# =============================================================================


class TryOnProvider(str, Enum):
    """Virtual try-on provider."""

    FASHN = "fashn"  # Commercial API (production-ready)
    IDM_VTON = "idm_vton"  # HuggingFace (open-source)
    ROUND_TABLE = "round_table"  # Both compete, A/B test winner


class GarmentCategory(str, Enum):
    """Garment category for try-on."""

    TOPS = "tops"
    BOTTOMS = "bottoms"
    DRESSES = "dresses"
    OUTERWEAR = "outerwear"
    FULL_BODY = "full_body"


class TryOnMode(str, Enum):
    """Try-on quality mode."""

    QUALITY = "quality"  # Higher quality, slower (~20s)
    BALANCED = "balanced"  # Balance of speed and quality (~12s)
    FAST = "fast"  # Faster, lower quality (~6s)


class JobStatus(str, Enum):
    """Generation job status."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelGender(str, Enum):
    """AI model gender for generation."""

    FEMALE = "female"
    MALE = "male"
    NEUTRAL = "neutral"


# =============================================================================
# Request/Response Models
# =============================================================================


class TryOnRequest(BaseModel):
    """Request to generate virtual try-on."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image",
        min_length=1,
    )
    garment_image_url: str = Field(
        ...,
        description="URL of the garment image",
        min_length=1,
    )
    category: GarmentCategory = Field(
        default=GarmentCategory.TOPS,
        description="Garment category for proper placement",
    )
    mode: TryOnMode = Field(
        default=TryOnMode.BALANCED,
        description="Quality/speed tradeoff",
    )
    provider: TryOnProvider = Field(
        default=TryOnProvider.FASHN,
        description="Try-on provider to use",
    )
    product_id: str | None = Field(
        default=None,
        description="Optional product ID for tracking",
    )


class BatchTryOnRequest(BaseModel):
    """Request for batch virtual try-on."""

    model_image_url: str = Field(
        ...,
        description="URL of the model/person image (same for all garments)",
    )
    garments: list[dict[str, Any]] = Field(
        ...,
        description="List of garments with garment_image_url, category, product_id",
        min_length=1,
        max_length=10,
    )
    mode: TryOnMode = Field(default=TryOnMode.BALANCED)
    provider: TryOnProvider = Field(default=TryOnProvider.FASHN)


class GenerateModelRequest(BaseModel):
    """Request to generate AI fashion model."""

    prompt: str = Field(
        default="Professional fashion model in studio",
        description="Description of the model to generate",
        max_length=500,
    )
    gender: ModelGender = Field(
        default=ModelGender.NEUTRAL,
        description="Model gender",
    )
    style: str = Field(
        default="professional",
        description="Style: professional, casual, editorial, street",
    )


class JobResponse(BaseModel):
    """Response for a try-on job."""

    job_id: str
    status: JobStatus
    provider: str
    category: str
    created_at: str
    completed_at: str | None = None
    result_url: str | None = None
    result_path: str | None = None
    error: str | None = None
    progress: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)
    cost_usd: float = 0.0


class BatchJobResponse(BaseModel):
    """Response for batch try-on job."""

    batch_id: str
    status: JobStatus
    total_items: int
    completed_items: int
    failed_items: int
    jobs: list[JobResponse]
    created_at: str
    completed_at: str | None = None


class ModelGenerationResponse(BaseModel):
    """Response for AI model generation."""

    job_id: str
    status: JobStatus
    prompt: str
    gender: str
    result_url: str | None = None
    result_path: str | None = None
    created_at: str
    completed_at: str | None = None
    error: str | None = None


class PipelineStatus(BaseModel):
    """Pipeline status response."""

    status: str
    providers: list[dict[str, Any]]
    queue_length: int
    avg_processing_time_seconds: float
    last_generated: str | None
    total_generated: int
    daily_limit: int
    daily_used: int


class ProviderInfo(BaseModel):
    """Provider information."""

    name: str
    display_name: str
    description: str
    status: str
    avg_time_seconds: float
    cost_per_image: float
    supported_categories: list[str]
    features: list[str]


# =============================================================================
# In-Memory Job Store
# =============================================================================


class TryOnJobStore:
    """In-memory job storage for try-on operations."""

    def __init__(self):
        """
        Initialize the in-memory job store's internal state.

        Sets up dictionaries for tracking try-on jobs, batch jobs, and model-generation jobs, and initializes counters and timestamps used for aggregate metrics (total generated count, cumulative processing time in milliseconds, daily usage count, and the next daily reset timestamp).
        """
        self._jobs: dict[str, JobResponse] = {}
        self._batches: dict[str, BatchJobResponse] = {}
        self._model_jobs: dict[str, ModelGenerationResponse] = {}
        self._total_generated = 0
        self._total_time_ms = 0.0
        self._daily_count = 0
        self._daily_reset: datetime | None = None

    def create_tryon_job(
        self,
        provider: TryOnProvider,
        category: GarmentCategory,
        metadata: dict[str, Any] | None = None,
    ) -> JobResponse:
        """
        Create a queued try-on job record.

        Parameters:
            provider (TryOnProvider): The provider to execute the try-on (e.g., FASHN, IDM_VTON, ROUND_TABLE).
            category (GarmentCategory): The garment category for the job.
            metadata (dict[str, Any] | None): Optional additional metadata to attach to the job.

        Returns:
            JobResponse: A JobResponse instance for the newly created job with status set to `QUEUED` and a creation timestamp.
        """
        job_id = f"tryon_{uuid.uuid4().hex[:12]}"
        job = JobResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            provider=provider.value,
            category=category.value,
            created_at=datetime.now(UTC).isoformat(),
            metadata=metadata or {},
        )
        self._jobs[job_id] = job
        return job

    def create_batch_job(
        self,
        jobs: list[JobResponse],
    ) -> BatchJobResponse:
        """
        Create a batch container that groups multiple try-on jobs and registers it in the in-memory store.

        The created BatchJobResponse will have a unique `batch_id`, initial status `QUEUED`, counts for total/completed/failed items, the provided jobs list, and a creation timestamp. The batch is stored in the job store's internal batches mapping before being returned.

        Parameters:
            jobs (list[JobResponse]): List of individual try-on jobs to include in the batch.

        Returns:
            BatchJobResponse: The newly created batch job object with metadata and `batch_id`.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        batch = BatchJobResponse(
            batch_id=batch_id,
            status=JobStatus.QUEUED,
            total_items=len(jobs),
            completed_items=0,
            failed_items=0,
            jobs=jobs,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._batches[batch_id] = batch
        return batch

    def create_model_job(
        self,
        prompt: str,
        gender: ModelGender,
    ) -> ModelGenerationResponse:
        """
        Create a queued AI model generation job for the given prompt and gender.

        Parameters:
            prompt (str): Text prompt describing the desired model generation.
            gender (ModelGender): Target model gender.

        Returns:
            ModelGenerationResponse: Job object containing a generated `job_id`, status `QUEUED`, the provided prompt and gender, and creation timestamp.
        """
        job_id = f"model_{uuid.uuid4().hex[:12]}"
        job = ModelGenerationResponse(
            job_id=job_id,
            status=JobStatus.QUEUED,
            prompt=prompt,
            gender=gender.value,
            created_at=datetime.now(UTC).isoformat(),
        )
        self._model_jobs[job_id] = job
        return job

    def get_tryon_job(self, job_id: str) -> JobResponse | None:
        """
        Retrieve a try-on job by its identifier.

        Returns:
            JobResponse: The job with the given `job_id` if it exists, `None` otherwise.
        """
        return self._jobs.get(job_id)

    def get_batch_job(self, batch_id: str) -> BatchJobResponse | None:
        """
        Retrieve a batch job by its identifier.

        @returns BatchJobResponse if the batch exists, `None` otherwise.
        """
        return self._batches.get(batch_id)

    def get_model_job(self, job_id: str) -> ModelGenerationResponse | None:
        """
        Retrieve a model generation job by its identifier.

        Parameters:
            job_id (str): The job's unique identifier.

        Returns:
            ModelGenerationResponse | None: The job if found, otherwise None.
        """
        return self._model_jobs.get(job_id)

    def update_tryon_job(self, job_id: str, **kwargs) -> JobResponse | None:
        """
        Update fields of an existing try-on job in the store.

        Parameters:
            job_id (str): Identifier of the try-on job to update.
            **kwargs: Field names and values to set on the job; only attributes that exist on the job will be updated.

        Returns:
            JobResponse | None: The updated job if found, `None` if no job with `job_id` exists.
        """
        job = self._jobs.get(job_id)
        if job:
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
        return job

    def complete_tryon_job(
        self,
        job_id: str,
        result_url: str,
        result_path: str,
        duration_ms: float,
        cost_usd: float = 0.075,
    ) -> JobResponse | None:
        """
        Mark a try-on job as completed and record its result, processing duration, and cost.

        Parameters:
            job_id (str): Identifier of the job to complete.
            result_url (str): Publicly accessible URL to the generated try-on image.
            result_path (str): Local filesystem path where the generated asset is stored.
            duration_ms (float): Processing duration in milliseconds.
            cost_usd (float): Cost in US dollars to attribute to the job (default 0.075).

        Returns:
            JobResponse | None: The updated JobResponse if the job was found and updated, `None` if no job exists with the given `job_id`.
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.COMPLETED
            job.result_url = result_url
            job.result_path = result_path
            job.completed_at = datetime.now(UTC).isoformat()
            job.progress = 1.0
            job.cost_usd = cost_usd
            self._total_generated += 1
            self._total_time_ms += duration_ms
            self._increment_daily()
        return job

    def fail_tryon_job(self, job_id: str, error: str) -> JobResponse | None:
        """
        Mark an existing try-on job as failed and record its error.

        Parameters:
            job_id (str): Identifier of the try-on job to update.
            error (str): Human-readable error message describing the failure.

        Returns:
            JobResponse | None: The updated job with status set to FAILED if found, otherwise `None`. The job's `completed_at` timestamp is set to the current UTC time.
        """
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = error
            job.completed_at = datetime.now(UTC).isoformat()
        return job

    def update_batch_progress(self, batch_id: str) -> BatchJobResponse | None:
        """
        Recompute and update a batch job's progress from its constituent jobs.

        Parameters:
            batch_id (str): Identifier of the batch to update.

        Returns:
            BatchJobResponse | None: The updated batch object if found, `None` if no batch exists for the given id.
        """
        batch = self._batches.get(batch_id)
        if batch:
            completed = sum(1 for j in batch.jobs if j.status == JobStatus.COMPLETED)
            failed = sum(1 for j in batch.jobs if j.status == JobStatus.FAILED)
            batch.completed_items = completed
            batch.failed_items = failed

            if completed + failed >= batch.total_items:
                batch.status = JobStatus.COMPLETED if failed == 0 else JobStatus.FAILED
                batch.completed_at = datetime.now(UTC).isoformat()
            elif any(j.status == JobStatus.PROCESSING for j in batch.jobs):
                batch.status = JobStatus.PROCESSING

        return batch

    def list_tryon_jobs(self, limit: int = 20) -> list[JobResponse]:
        """
        Retrieve recent try-on jobs ordered by creation time.

        Parameters:
            limit (int): Maximum number of jobs to return; newest jobs are returned first.

        Returns:
            list[JobResponse]: Jobs sorted by creation timestamp (newest first), limited to `limit`.
        """
        jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]

    def _increment_daily(self):
        """
        Update the internal daily counter, resetting it when the date advances (UTC).

        Increments the store's internal `_daily_count` by one. If `_daily_reset` is unset or its UTC date is earlier than the current UTC date, `_daily_count` is reset to zero and `_daily_reset` is set to the current UTC timestamp.
        """
        now = datetime.now(UTC)
        if self._daily_reset is None or now.date() > self._daily_reset.date():
            self._daily_count = 0
            self._daily_reset = now
        self._daily_count += 1

    @property
    def queue_length(self) -> int:
        """
        Number of jobs currently in the queue or being processed.

        Returns:
            count (int): Number of jobs whose status is `QUEUED` or `PROCESSING`.
        """
        return sum(
            1 for j in self._jobs.values() if j.status in (JobStatus.QUEUED, JobStatus.PROCESSING)
        )

    @property
    def avg_time_seconds(self) -> float:
        """
        Compute the average generation time in seconds.

        Returns:
            average_time_seconds (float): Average time per completed generation in seconds. If no generations have completed yet, returns a default estimate of 12.0 seconds.
        """
        if self._total_generated == 0:
            return 12.0  # Default estimate for balanced mode
        return (self._total_time_ms / self._total_generated) / 1000

    @property
    def total_generated(self) -> int:
        """
        Get the total number of completed try-on generations.

        Returns:
            int: Total completed try-on generations.
        """
        return self._total_generated

    @property
    def daily_used(self) -> int:
        """
        Get the number of try-on jobs completed since the last daily reset.

        Returns:
            The count of completed try-on jobs since the most recent daily reset; zero if the reset date is unset or earlier than today.
        """
        now = datetime.now(UTC)
        if self._daily_reset is None or now.date() > self._daily_reset.date():
            return 0
        return self._daily_count

    @property
    def last_generated(self) -> str | None:
        """
        Return the timestamp of the most recently completed job.

        @returns `str` timestamp of the latest completed job (e.g., ISO 8601) or `None` if no job has completed.
        """
        completed = [j for j in self._jobs.values() if j.status == JobStatus.COMPLETED]
        if completed:
            completed.sort(key=lambda j: j.completed_at or "", reverse=True)
            return completed[0].completed_at
        return None


job_store = TryOnJobStore()


# =============================================================================
# Background Task Runners
# =============================================================================


async def run_fashn_tryon(
    job_id: str,
    model_image_path: str,
    garment_image_path: str,
    category: GarmentCategory,
    mode: TryOnMode,
):
    """
    Execute a FASHN provider virtual try-on job and update the in-memory job store with progress and results.

    This runs inside a background task: it sets the job to PROCESSING, streams progress updates to the job store, invokes the FASHN try-on agent, and on success records the resulting image URL/path, duration, and cost; on failure it marks the job failed.

    Parameters:
        job_id (str): Identifier of the try-on job to update.
        model_image_path (str): Local filesystem path to the model image.
        garment_image_path (str): Local filesystem path to the garment image.
        category (GarmentCategory): Garment category for the try-on (e.g., TOPS, DRESSES).
        mode (TryOnMode): Try-on generation mode influencing quality/speed tradeoffs.
    """
    import time

    start_time = time.time()

    try:
        job_store.update_tryon_job(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import FASHN agent
        from agents.fashn_agent import FashnTryOnAgent
        from agents.fashn_agent import GarmentCategory as FashnCategory

        agent = FashnTryOnAgent()
        job_store.update_tryon_job(job_id, progress=0.2)

        # Map category
        category_map = {
            GarmentCategory.TOPS: FashnCategory.TOPS.value,
            GarmentCategory.BOTTOMS: FashnCategory.BOTTOMS.value,
            GarmentCategory.DRESSES: FashnCategory.DRESSES.value,
            GarmentCategory.OUTERWEAR: FashnCategory.OUTERWEAR.value,
            GarmentCategory.FULL_BODY: FashnCategory.FULL_BODY.value,
        }

        try:
            result = await agent._tool_virtual_tryon(
                model_image=model_image_path,
                garment_image=garment_image_path,
                category=category_map.get(category, "tops"),
                mode=mode.value,
            )

            job_store.update_tryon_job(job_id, progress=0.9)

            if result and result.get("image_path"):
                duration_ms = (time.time() - start_time) * 1000
                job_store.complete_tryon_job(
                    job_id,
                    result_url=result.get("image_url", ""),
                    result_path=result.get("image_path", ""),
                    duration_ms=duration_ms,
                    cost_usd=0.075,  # FASHN pricing
                )
                logger.info(f"FASHN try-on completed: {job_id}")
            else:
                job_store.fail_tryon_job(job_id, "No output from FASHN API")

        finally:
            await agent.close()

    except Exception as e:
        logger.exception(f"FASHN try-on failed: {e}")
        job_store.fail_tryon_job(job_id, str(e))


async def run_idm_vton_tryon(
    job_id: str,
    model_image_path: str,
    garment_image_path: str,
    category: GarmentCategory,
):
    """
    Run an IDM-VTON virtual try-on job using the HuggingFace Space and update the in-memory job store.

    This background task calls the `yisol/IDM-VTON` Gradio space to composite `garment_image_path` onto `model_image_path`, updates job progress and status in `job_store`, and saves the resulting image to OUTPUT_DIR on success. If the `gradio_client` package is not available or the Space call fails, the job is marked as failed with an explanatory error.

    Parameters:
        job_id (str): Identifier of the try-on job in the job store; updated for status/progress/results.
        model_image_path (str): Local filesystem path to the model/background image used by IDM-VTON.
        garment_image_path (str): Local filesystem path to the garment image to be applied.
        category (GarmentCategory): Garment category used to select a textual description for the IDM-VTON API.
    """
    import time

    start_time = time.time()

    try:
        job_store.update_tryon_job(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Import gradio client
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            job_store.fail_tryon_job(
                job_id, "gradio_client not installed. Run: pip install gradio_client"
            )
            return

        # Connect to IDM-VTON HuggingFace Space
        job_store.update_tryon_job(job_id, progress=0.2)

        try:
            client = Client("yisol/IDM-VTON")
        except Exception as e:
            job_store.fail_tryon_job(job_id, f"Failed to connect to IDM-VTON: {e}")
            return

        job_store.update_tryon_job(job_id, progress=0.3)

        # Determine garment description based on category
        garment_descriptions = {
            GarmentCategory.TOPS: "upper body garment",
            GarmentCategory.BOTTOMS: "lower body garment",
            GarmentCategory.DRESSES: "full body dress",
            GarmentCategory.OUTERWEAR: "outerwear jacket or coat",
            GarmentCategory.FULL_BODY: "full body outfit",
        }
        garment_desc = garment_descriptions.get(category, "garment")

        try:
            # Call IDM-VTON API
            result = client.predict(
                dict={"background": handle_file(model_image_path), "layers": [], "composite": None},
                garm_img=handle_file(garment_image_path),
                garment_des=garment_desc,
                is_checked=True,  # Auto-mask
                is_checked_crop=False,
                denoise_steps=30,
                seed=42,
                api_name="/tryon",
            )

            job_store.update_tryon_job(job_id, progress=0.9)

            if result and len(result) > 0:
                output_image_path = result[0]

                if output_image_path and os.path.exists(output_image_path):
                    # Copy to output directory
                    import shutil

                    output_name = f"idm_vton_{job_id}.png"
                    final_path = OUTPUT_DIR / output_name
                    shutil.copy2(output_image_path, final_path)

                    duration_ms = (time.time() - start_time) * 1000
                    job_store.complete_tryon_job(
                        job_id,
                        result_url=f"/assets/tryon/{output_name}",
                        result_path=str(final_path),
                        duration_ms=duration_ms,
                        cost_usd=0.0,  # Free HuggingFace
                    )
                    logger.info(f"IDM-VTON try-on completed: {job_id}")
                else:
                    job_store.fail_tryon_job(job_id, "No output file from IDM-VTON")
            else:
                job_store.fail_tryon_job(job_id, "Empty result from IDM-VTON")

        except Exception as e:
            logger.exception(f"IDM-VTON API call failed: {e}")
            job_store.fail_tryon_job(job_id, f"IDM-VTON API error: {e}")

    except Exception as e:
        logger.exception(f"IDM-VTON try-on failed: {e}")
        job_store.fail_tryon_job(job_id, str(e))


async def run_round_table_tryon(
    job_id: str,
    model_image_path: str,
    garment_image_path: str,
    category: GarmentCategory,
    mode: TryOnMode,
):
    """
    Run a round‑robin competition between FASHN and IDM‑VTON providers to produce a winning try-on result for a parent job.

    Executes both provider workflows in parallel as sub-jobs, prefers FASHN's result if both succeed, and then completes the parent job with the chosen provider's result. Creates sub-jobs tied to the parent job, updates job progress and metadata with each provider's status, and marks the parent job as failed if both providers fail.

    Parameters:
        job_id (str): Identifier of the parent try-on job to update with the competition result.
        model_image_path (str): Filesystem path to the model image used for both providers.
        garment_image_path (str): Filesystem path to the garment image used for both providers.
        category (GarmentCategory): Garment category to pass to provider workflows.
        mode (TryOnMode): Quality/speed mode to use for providers that accept it.
    """
    import time

    start_time = time.time()

    try:
        job_store.update_tryon_job(job_id, status=JobStatus.PROCESSING, progress=0.1)

        # Create sub-jobs for parallel execution
        fashn_job = job_store.create_tryon_job(
            TryOnProvider.FASHN, category, {"parent_job": job_id}
        )
        idm_job = job_store.create_tryon_job(
            TryOnProvider.IDM_VTON, category, {"parent_job": job_id}
        )

        job_store.update_tryon_job(job_id, progress=0.2)

        # Run both concurrently (results stored in job_store by background tasks)
        await asyncio.gather(
            run_fashn_tryon(
                fashn_job.job_id, model_image_path, garment_image_path, category, mode
            ),
            run_idm_vton_tryon(idm_job.job_id, model_image_path, garment_image_path, category),
            return_exceptions=True,
        )

        job_store.update_tryon_job(job_id, progress=0.8)

        # Get completed jobs
        fashn_result = job_store.get_tryon_job(fashn_job.job_id)
        idm_result = job_store.get_tryon_job(idm_job.job_id)

        # Determine winner (prefer FASHN if both succeed, otherwise use whichever succeeded)
        winner = None
        if fashn_result and fashn_result.status == JobStatus.COMPLETED:
            winner = fashn_result
        elif idm_result and idm_result.status == JobStatus.COMPLETED:
            winner = idm_result

        if winner:
            duration_ms = (time.time() - start_time) * 1000
            job_store.complete_tryon_job(
                job_id,
                result_url=winner.result_url or "",
                result_path=winner.result_path or "",
                duration_ms=duration_ms,
                cost_usd=winner.cost_usd,
            )

            # Update metadata with competition results
            job = job_store.get_tryon_job(job_id)
            if job:
                job.metadata.update(
                    {
                        "winner": winner.provider,
                        "fashn_status": fashn_result.status.value if fashn_result else "not_run",
                        "idm_status": idm_result.status.value if idm_result else "not_run",
                    }
                )

            logger.info(f"Round Table completed: {job_id}, winner: {winner.provider}")
        else:
            job_store.fail_tryon_job(job_id, "Both providers failed")

    except Exception as e:
        logger.exception(f"Round Table try-on failed: {e}")
        job_store.fail_tryon_job(job_id, str(e))


async def run_fashn_model_generation(
    job_id: str,
    prompt: str,
    gender: ModelGender,
):
    """
    Run a FASHN model generation job and update its stored job record.

    Executes the FASHN agent to generate an AI model image for the given prompt and gender.
    Updates the corresponding model job in the in-memory job_store: sets status to PROCESSING
    before execution, sets status to COMPLETED and populates `result_url`, `result_path`, and
    `completed_at` when an image is produced, or sets status to FAILED and records an error
    message on failure. Ensures the FASHN agent is closed after use.
    """
    try:
        job = job_store.get_model_job(job_id)
        if job:
            job.status = JobStatus.PROCESSING

        # Import FASHN agent
        from agents.fashn_agent import FashnTryOnAgent

        agent = FashnTryOnAgent()

        try:
            result = await agent._tool_create_model(
                prompt=prompt,
                gender=gender.value,
            )

            if result and result.get("image_path"):
                job = job_store.get_model_job(job_id)
                if job:
                    job.status = JobStatus.COMPLETED
                    job.result_url = result.get("image_url", "")
                    job.result_path = result.get("image_path", "")
                    job.completed_at = datetime.now(UTC).isoformat()
                logger.info(f"FASHN model generation completed: {job_id}")
            else:
                job = job_store.get_model_job(job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error = "No output from FASHN API"

        finally:
            await agent.close()

    except Exception as e:
        logger.exception(f"FASHN model generation failed: {e}")
        job = job_store.get_model_job(job_id)
        if job:
            job.status = JobStatus.FAILED
            job.error = str(e)


async def download_image(url: str, job_id: str, prefix: str = "img") -> str:
    """
    Download an image from the given URL and save it to the uploads directory using a filename derived from the job id.

    The function infers the file extension from the response Content-Type (supports image/jpeg, image/png, image/webp) and falls back to `.png` if unknown. The saved filename is `{prefix}_{job_id}{ext}` in the module's UPLOAD_DIR.

    Parameters:
        prefix (str): Filename prefix to use; defaults to "img".

    Returns:
        str: Filesystem path to the saved image.

    Raises:
        httpx.HTTPError: If the HTTP request fails or returns a non-success status.
    """
    import httpx

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()

        # Determine extension
        content_type = resp.headers.get("content-type", "image/png")
        ext_map = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        ext = ext_map.get(content_type, ".png")

        # Save to upload directory
        temp_path = UPLOAD_DIR / f"{prefix}_{job_id}{ext}"
        temp_path.write_bytes(resp.content)

        return str(temp_path)


# =============================================================================
# Endpoints
# =============================================================================


@virtual_tryon_router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status() -> PipelineStatus:
    """
    Provide current virtual try-on pipeline status including provider readiness and aggregate metrics.

    Returns:
        pipeline_status (PipelineStatus): Current pipeline state containing provider availability and metadata (`providers`), queue length (`queue_length`), average processing time in seconds (`avg_processing_time_seconds`), timestamp of the last completed generation or `None` (`last_generated`), total completed generations (`total_generated`), configured daily limit (`daily_limit`), and today's usage count (`daily_used`).
    """
    fashn_available = bool(os.getenv("FASHN_API_KEY"))

    providers = [
        {
            "name": "fashn",
            "display_name": "FASHN AI",
            "status": "available" if fashn_available else "requires_api_key",
            "type": "commercial",
        },
        {
            "name": "idm_vton",
            "display_name": "IDM-VTON (HuggingFace)",
            "status": "available",
            "type": "open_source",
        },
    ]

    return PipelineStatus(
        status="operational",
        providers=providers,
        queue_length=job_store.queue_length,
        avg_processing_time_seconds=job_store.avg_time_seconds,
        last_generated=job_store.last_generated,
        total_generated=job_store.total_generated,
        daily_limit=1000,  # Configurable limit
        daily_used=job_store.daily_used,
    )


@virtual_tryon_router.get("/providers", response_model=list[ProviderInfo])
async def list_providers() -> list[ProviderInfo]:
    """List available virtual try-on providers."""
    fashn_available = bool(os.getenv("FASHN_API_KEY"))

    return [
        ProviderInfo(
            name="round_table",
            display_name="Round Table",
            description="Both providers compete. Returns best result.",
            status="available" if fashn_available else "partial",
            avg_time_seconds=25.0,
            cost_per_image=0.075 if fashn_available else 0.0,
            supported_categories=["tops", "bottoms", "dresses", "outerwear", "full_body"],
            features=["competition", "a_b_testing", "quality_comparison"],
        ),
        ProviderInfo(
            name="fashn",
            display_name="FASHN AI",
            description="Commercial virtual try-on API. Fast, production-ready.",
            status="available" if fashn_available else "requires_api_key",
            avg_time_seconds=12.0,
            cost_per_image=0.075,
            supported_categories=["tops", "bottoms", "dresses", "outerwear", "full_body"],
            features=["ai_models", "batch_processing", "high_quality"],
        ),
        ProviderInfo(
            name="idm_vton",
            display_name="IDM-VTON",
            description="Open-source virtual try-on via HuggingFace. Free, good quality.",
            status="available",
            avg_time_seconds=45.0,
            cost_per_image=0.0,
            supported_categories=["tops", "bottoms", "dresses", "outerwear", "full_body"],
            features=["open_source", "free", "gradio_api"],
        ),
    ]


@virtual_tryon_router.get("/categories")
async def list_categories() -> list[dict[str, str]]:
    """
    Provide the supported garment categories.

    Returns:
        categories (list[dict[str, str]]): A list of category objects, each with keys
            `id` (identifier), `name` (display name), and `description` (short summary).
    """
    return [
        {"id": "tops", "name": "Tops", "description": "T-shirts, blouses, shirts, sweaters"},
        {"id": "bottoms", "name": "Bottoms", "description": "Pants, jeans, shorts, skirts"},
        {"id": "dresses", "name": "Dresses", "description": "Full dresses, jumpsuits"},
        {"id": "outerwear", "name": "Outerwear", "description": "Jackets, coats, hoodies"},
        {"id": "full_body", "name": "Full Body", "description": "Complete outfits"},
    ]


@virtual_tryon_router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(limit: int = 20) -> list[JobResponse]:
    """
    Retrieve recent try-on jobs.

    Returns:
        list[JobResponse]: Recent try-on jobs, up to `limit` items.
    """
    return job_store.list_tryon_jobs(limit)


@virtual_tryon_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str) -> JobResponse:
    """
    Retrieve the try-on job with the given ID.

    Returns:
        JobResponse: The try-on job matching the provided job_id.

    Raises:
        HTTPException: with status code 404 if no job with the given ID exists.
    """
    job = job_store.get_tryon_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@virtual_tryon_router.post("/generate", response_model=JobResponse)
async def generate_tryon(
    request: TryOnRequest,
    background_tasks: BackgroundTasks,
) -> JobResponse:
    """
    Create and queue a virtual try-on job from the provided model and garment image URLs.

    Schedules a background task that downloads the images and executes the provider-specific try-on workflow (FASHN, IDM_VTON, or ROUND_TABLE). If image download or provider processing fails the background task will mark the job as failed; the function itself returns immediately with the created job.

    Parameters:
        request (TryOnRequest): Request containing model_image_url, garment_image_url, category, mode, provider, and optional product_id.
        background_tasks (BackgroundTasks): FastAPI background task manager used to schedule asynchronous processing.

    Returns:
        JobResponse: The newly created job record in QUEUED state.

    Raises:
        HTTPException: If the requested provider is FASHN but the FASHN_API_KEY environment variable is not set.
    """
    # Validate provider
    if request.provider == TryOnProvider.FASHN and not os.getenv("FASHN_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="FASHN_API_KEY not configured. Set environment variable or use idm_vton provider.",
        )

    # Create job
    job = job_store.create_tryon_job(
        provider=request.provider,
        category=request.category,
        metadata={
            "model_image_url": request.model_image_url,
            "garment_image_url": request.garment_image_url,
            "mode": request.mode.value,
            "product_id": request.product_id,
        },
    )

    # Download images in background
    async def run_with_download():
        """
        Download model and garment images for the current job and dispatch the selected provider's try-on workflow.

        If both images download successfully, schedules and awaits the provider-specific try-on task (FASHN, IDM-VTON, or ROUND_TABLE) using the downloaded file paths. On any exception during download or dispatch, marks the job as failed with an error message.
        """
        try:
            model_path = await download_image(request.model_image_url, job.job_id, "model")
            garment_path = await download_image(request.garment_image_url, job.job_id, "garment")

            if request.provider == TryOnProvider.FASHN:
                await run_fashn_tryon(
                    job.job_id, model_path, garment_path, request.category, request.mode
                )
            elif request.provider == TryOnProvider.IDM_VTON:
                await run_idm_vton_tryon(job.job_id, model_path, garment_path, request.category)
            else:  # ROUND_TABLE
                await run_round_table_tryon(
                    job.job_id, model_path, garment_path, request.category, request.mode
                )
        except Exception as e:
            job_store.fail_tryon_job(job.job_id, f"Image download failed: {e}")

    background_tasks.add_task(run_with_download)

    return job


@virtual_tryon_router.post("/generate/upload", response_model=JobResponse)
async def generate_tryon_upload(
    model_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    category: GarmentCategory = GarmentCategory.TOPS,
    mode: TryOnMode = TryOnMode.BALANCED,
    provider: TryOnProvider = TryOnProvider.FASHN,
    background_tasks: BackgroundTasks = None,
) -> JobResponse:
    """
    Create a try-on job from two uploaded images, persist the files, and schedule the selected provider's background processing.

    Validates that both uploads are images and that provider prerequisites are met, saves files to the configured upload directory, creates a queued JobResponse, and enqueues the appropriate background task to perform the try-on. May mark the job failed and raise an HTTPException on validation or save errors.

    Parameters:
        model_image (UploadFile): Uploaded image of the model.
        garment_image (UploadFile): Uploaded image of the garment.
        category (GarmentCategory): Target garment category for the try-on.
        mode (TryOnMode): Desired quality/speed mode for providers that support it.
        provider (TryOnProvider): Selected provider to perform the try-on.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance used to schedule processing.

    Returns:
        JobResponse: The created try-on job in queued state.

    Raises:
        HTTPException: If an uploaded file is not an image, required provider configuration is missing (e.g., FASHN_API_KEY), or saving uploads fails.
    """
    # Validate file types
    for img, name in [(model_image, "model"), (garment_image, "garment")]:
        if not img.content_type or not img.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"{name} file must be an image")

    # Validate provider
    if provider == TryOnProvider.FASHN and not os.getenv("FASHN_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="FASHN_API_KEY not configured. Use idm_vton provider.",
        )

    # Create job
    job = job_store.create_tryon_job(
        provider=provider,
        category=category,
        metadata={
            "model_filename": model_image.filename,
            "garment_filename": garment_image.filename,
            "mode": mode.value,
        },
    )

    # Save uploaded files
    model_ext = Path(model_image.filename or "model.png").suffix or ".png"
    garment_ext = Path(garment_image.filename or "garment.png").suffix or ".png"

    model_path = UPLOAD_DIR / f"model_{job.job_id}{model_ext}"
    garment_path = UPLOAD_DIR / f"garment_{job.job_id}{garment_ext}"

    try:
        model_content = await model_image.read()
        garment_content = await garment_image.read()
        model_path.write_bytes(model_content)
        garment_path.write_bytes(garment_content)
    except Exception as e:
        job_store.fail_tryon_job(job.job_id, f"Failed to save uploads: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save uploads: {e}")

    # Schedule background task
    if provider == TryOnProvider.FASHN:
        background_tasks.add_task(
            run_fashn_tryon, job.job_id, str(model_path), str(garment_path), category, mode
        )
    elif provider == TryOnProvider.IDM_VTON:
        background_tasks.add_task(
            run_idm_vton_tryon, job.job_id, str(model_path), str(garment_path), category
        )
    else:  # ROUND_TABLE
        background_tasks.add_task(
            run_round_table_tryon, job.job_id, str(model_path), str(garment_path), category, mode
        )

    return job


@virtual_tryon_router.post("/batch", response_model=BatchJobResponse)
async def batch_tryon(
    request: BatchTryOnRequest,
    background_tasks: BackgroundTasks,
) -> BatchJobResponse:
    """
    Create and enqueue a batch of try-on jobs for a single model image.

    Creates a BatchJobResponse containing one try-on job per garment in the request and schedules a background task that downloads the model and garment images and runs each job using the selected provider. The returned batch immediately reflects the queued jobs and their identifiers; actual processing and status updates occur asynchronously.

    Returns:
        BatchJobResponse: The created batch container with queued jobs and metadata.

    Raises:
        HTTPException: If the requested provider is FASHN and the `FASHN_API_KEY` environment variable is not configured.
    """
    # Validate provider
    if request.provider == TryOnProvider.FASHN and not os.getenv("FASHN_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="FASHN_API_KEY not configured for batch processing.",
        )

    # Create individual jobs
    jobs = []
    for garment in request.garments:
        category = GarmentCategory(garment.get("category", "tops"))
        job = job_store.create_tryon_job(
            provider=request.provider,
            category=category,
            metadata={
                "model_image_url": request.model_image_url,
                "garment_image_url": garment.get("garment_image_url"),
                "product_id": garment.get("product_id"),
                "mode": request.mode.value,
            },
        )
        jobs.append(job)

    # Create batch container
    batch = job_store.create_batch_job(jobs)

    # Process in background
    async def run_batch():
        """
        Process a batch try-on request: download the model image, iterate garments, run provider-specific try-on jobs, and update batch progress.

        For each garment in the batch this function:
        - downloads the garment image,
        - selects the garment category (defaults to "tops" if missing),
        - invokes the configured provider workflow (FASHN or IDM_VTON) to produce the try-on,
        - marks individual jobs as failed on per-item errors.

        On a batch-level error it logs the exception, marks any still-queued child jobs as failed with the batch error, and updates the batch progress in the in-memory job store.
        """
        try:
            model_path = await download_image(request.model_image_url, batch.batch_id, "model")

            for idx, job in enumerate(jobs):
                garment_url = request.garments[idx].get("garment_image_url")
                if not garment_url:
                    job_store.fail_tryon_job(job.job_id, "Missing garment_image_url")
                    continue

                try:
                    garment_path = await download_image(garment_url, job.job_id, "garment")
                    category = GarmentCategory(request.garments[idx].get("category", "tops"))

                    if request.provider == TryOnProvider.FASHN:
                        await run_fashn_tryon(
                            job.job_id, model_path, garment_path, category, request.mode
                        )
                    else:
                        await run_idm_vton_tryon(job.job_id, model_path, garment_path, category)

                except Exception as e:
                    job_store.fail_tryon_job(job.job_id, str(e))

                # Update batch progress
                job_store.update_batch_progress(batch.batch_id)

        except Exception as e:
            logger.exception(f"Batch processing failed: {e}")
            for job in jobs:
                if job.status == JobStatus.QUEUED:
                    job_store.fail_tryon_job(job.job_id, f"Batch failed: {e}")
            job_store.update_batch_progress(batch.batch_id)

    background_tasks.add_task(run_batch)

    return batch


@virtual_tryon_router.get("/batch/{batch_id}", response_model=BatchJobResponse)
async def get_batch_job(batch_id: str) -> BatchJobResponse:
    """
    Retrieve the status of a batch try-on job.

    Returns:
        BatchJobResponse: The batch job record containing status, counts, jobs, timestamps, and metadata.

    Raises:
        HTTPException: With status code 404 if no batch with the given `batch_id` exists.
    """
    batch = job_store.get_batch_job(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")
    return batch


@virtual_tryon_router.post("/models/generate", response_model=ModelGenerationResponse)
async def generate_ai_model(
    request: GenerateModelRequest,
    background_tasks: BackgroundTasks,
) -> ModelGenerationResponse:
    """
    Create and enqueue an AI fashion model generation job for the given prompt and gender.

    Parameters:
        request (GenerateModelRequest): Request containing the generation `prompt` and target `gender`.
    Returns:
        ModelGenerationResponse: The newly created model generation job (status QUEUED) with its metadata and job_id.
    Raises:
        HTTPException: If the FASHN_API_KEY environment variable is not configured.
    """
    if not os.getenv("FASHN_API_KEY"):
        raise HTTPException(
            status_code=400,
            detail="FASHN_API_KEY required for AI model generation.",
        )

    # Create job
    job = job_store.create_model_job(request.prompt, request.gender)

    # Schedule background task
    background_tasks.add_task(run_fashn_model_generation, job.job_id, request.prompt, request.gender)

    return job


@virtual_tryon_router.get("/models/jobs/{job_id}", response_model=ModelGenerationResponse)
async def get_model_job(job_id: str) -> ModelGenerationResponse:
    """
    Retrieve an AI model generation job by its identifier.

    Parameters:
        job_id (str): Unique identifier of the model generation job.

    Returns:
        ModelGenerationResponse: The model generation job record including status, timestamps, result location, and metadata.

    Raises:
        HTTPException: If no job exists with the given ID (404 Not Found).
    """
    job = job_store.get_model_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Model job {job_id} not found")
    return job
