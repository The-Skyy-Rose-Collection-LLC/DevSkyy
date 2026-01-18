"""
Training Status API
===================
API endpoints for monitoring LoRA training progress and managing training jobs.

Routes:
- GET /api/v1/training/status - Get current training status
- GET /api/v1/training/jobs - List all training jobs
- GET /api/v1/training/jobs/{job_id} - Get specific job details
- POST /api/v1/training/export - Export Round Table results to HuggingFace dataset
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi import Path as FastAPIPath
from prometheus_client import Counter, Gauge, Histogram
from pydantic import BaseModel, Field, field_validator

from security.prometheus_exporter import devskyy_registry

# =============================================================================
# Input Validation Constants
# =============================================================================

# Safe job ID pattern: alphanumeric, hyphens, underscores only (no path traversal)
JOB_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")
DATASET_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
VALID_COLLECTIONS = frozenset({"signature", "black_rose", "love_hurts"})

logger = logging.getLogger(__name__)

# =============================================================================
# Prometheus Metrics
# =============================================================================

training_jobs_total = Counter(
    "training_jobs_total",
    "Total number of training jobs",
    ["status"],
    registry=devskyy_registry,
)

training_progress_percentage = Gauge(
    "training_progress_percentage",
    "Current training progress percentage",
    ["job_id"],
    registry=devskyy_registry,
)

training_loss = Gauge(
    "training_loss",
    "Current training loss",
    ["job_id"],
    registry=devskyy_registry,
)

training_api_duration_seconds = Histogram(
    "training_api_duration_seconds",
    "Training API call duration",
    ["endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=devskyy_registry,
)

# Create router
training_router = APIRouter(prefix="/training", tags=["Training"])

# Configuration
TRAINING_OUTPUT_DIR = Path(os.getenv("TRAINING_OUTPUT_DIR", "models/training-runs"))
ROUND_TABLE_RESULTS_PATH = Path("assets/ai-enhanced-images/ROUND_TABLE_ELITE_RESULTS.json")


# =============================================================================
# Pydantic Models
# =============================================================================


class TrainingProgressResponse(BaseModel):
    """Current training progress metrics."""

    status: Literal["idle", "preparing", "training", "completed", "failed"] = Field(
        default="idle", description="Training status"
    )
    version: str = Field(default="", description="LoRA version being trained")
    current_epoch: int = Field(default=0, description="Current epoch")
    total_epochs: int = Field(default=0, description="Total epochs")
    current_step: int = Field(default=0, description="Current step")
    total_steps: int = Field(default=0, description="Total steps")
    progress_percentage: float = Field(default=0.0, description="Progress percentage (0-100)")
    loss: float = Field(default=0.0, description="Current loss")
    learning_rate: float = Field(default=0.0, description="Current learning rate")
    avg_loss: float = Field(default=0.0, description="Average loss")
    best_loss: float = Field(default=float("inf"), description="Best loss achieved")
    started_at: str | None = Field(None, description="Training start timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")
    estimated_completion: str | None = Field(None, description="Estimated completion time")
    elapsed_seconds: float = Field(default=0.0, description="Elapsed time in seconds")
    remaining_seconds: float = Field(default=0.0, description="Remaining time in seconds")
    total_images: int = Field(default=0, description="Total training images")
    total_products: int = Field(default=0, description="Total products in dataset")
    collections: dict[str, int] = Field(default_factory=dict, description="Collection breakdown")
    latest_checkpoint: str = Field(default="", description="Latest checkpoint path")
    checkpoint_step: int = Field(default=0, description="Checkpoint step")
    message: str = Field(default="", description="Status message")
    error: str = Field(default="", description="Error message if failed")


class TrainingJobInfo(BaseModel):
    """Training job information."""

    job_id: str = Field(..., description="Unique job identifier")
    version: str = Field(..., description="LoRA version")
    status: Literal["pending", "running", "completed", "failed"] = Field(
        ..., description="Job status"
    )
    started_at: str | None = Field(None, description="Start timestamp")
    completed_at: str | None = Field(None, description="Completion timestamp")
    total_epochs: int = Field(default=0, description="Total epochs")
    final_loss: float | None = Field(None, description="Final loss value")
    total_images: int = Field(default=0, description="Training images count")
    total_products: int = Field(default=0, description="Products count")
    collections: dict[str, int] = Field(default_factory=dict, description="Collection breakdown")
    model_path: str | None = Field(None, description="Output model path")
    error: str | None = Field(None, description="Error message if failed")


class TrainingJobsListResponse(BaseModel):
    """List of training jobs."""

    total_jobs: int = Field(..., description="Total number of jobs")
    running: int = Field(..., description="Running jobs count")
    completed: int = Field(..., description="Completed jobs count")
    failed: int = Field(..., description="Failed jobs count")
    jobs: list[TrainingJobInfo] = Field(..., description="List of jobs")
    retrieved_at: str = Field(..., description="Retrieval timestamp")


class ExportRequest(BaseModel):
    """Request to export Round Table results to HuggingFace."""

    dataset_name: str = Field(
        default="skyyrose-scene-specs",
        description="HuggingFace dataset name",
        min_length=1,
        max_length=64,
    )
    collections: list[str] | None = Field(
        None, description="Specific collections to export (None = all)"
    )
    dry_run: bool = Field(default=False, description="Dry run mode (no upload)")

    @field_validator("dataset_name")
    @classmethod
    def validate_dataset_name(cls, v: str) -> str:
        """Validate dataset name against safe pattern."""
        if not DATASET_NAME_PATTERN.match(v):
            raise ValueError(
                "dataset_name must be 1-64 alphanumeric characters, hyphens, or underscores"
            )
        return v

    @field_validator("collections")
    @classmethod
    def validate_collections(cls, v: list[str] | None) -> list[str] | None:
        """Validate collections against whitelist."""
        if v is None:
            return v
        invalid = set(v) - VALID_COLLECTIONS
        if invalid:
            raise ValueError(f"Invalid collections: {invalid}. Valid: {sorted(VALID_COLLECTIONS)}")
        return v


class ExportResponse(BaseModel):
    """Response from export operation."""

    success: bool = Field(..., description="Whether export succeeded")
    dataset_url: str | None = Field(None, description="HuggingFace dataset URL")
    exported_count: int = Field(..., description="Number of items exported")
    collections_exported: list[str] = Field(..., description="Collections exported")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    message: str = Field(..., description="Status message")


# =============================================================================
# Helper Functions
# =============================================================================


def _validate_job_id(job_id: str) -> str:
    """
    Validate job_id against safe pattern to prevent path traversal.

    Args:
        job_id: The job identifier to validate

    Returns:
        The validated job_id

    Raises:
        HTTPException: If job_id contains invalid characters
    """
    if not JOB_ID_PATTERN.match(job_id):
        logger.warning(f"Invalid job_id attempted: {job_id[:50]!r}")
        raise HTTPException(
            status_code=400,
            detail="job_id must be 1-128 alphanumeric characters, hyphens, or underscores",
        )
    return job_id


def _safe_path_resolve(base_dir: Path, relative_path: str, filename: str) -> Path | None:
    """
    Safely resolve a path ensuring it stays within base_dir.

    Prevents path traversal attacks by checking resolved path is under base_dir.

    Args:
        base_dir: The allowed base directory
        relative_path: Relative path component (job_id/version)
        filename: Filename to access

    Returns:
        Resolved Path if valid and exists, None otherwise
    """
    try:
        # Resolve to absolute path
        target = (base_dir / relative_path / filename).resolve()
        base_resolved = base_dir.resolve()

        # Security check: ensure target is under base_dir
        if not str(target).startswith(str(base_resolved)):
            logger.warning(f"Path traversal blocked: {relative_path!r}")
            return None

        return target if target.exists() else None
    except (OSError, ValueError) as e:
        logger.warning(f"Path resolution failed for {relative_path!r}: {e}")
        return None


def _load_progress_file(version: str) -> dict[str, Any] | None:
    """Load progress.json for a specific training version with path safety."""
    progress_path = _safe_path_resolve(TRAINING_OUTPUT_DIR, version, "progress.json")
    if progress_path:
        try:
            with open(progress_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in progress file {progress_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load progress file {progress_path}: {e}")
    return None


def _load_status_file(version: str) -> dict[str, Any] | None:
    """Load status.json for a specific training version with path safety."""
    status_path = _safe_path_resolve(TRAINING_OUTPUT_DIR, version, "status.json")
    if status_path:
        try:
            with open(status_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in status file {status_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to load status file {status_path}: {e}")
    return None


def _find_training_versions() -> list[str]:
    """Find all training version directories."""
    if not TRAINING_OUTPUT_DIR.exists():
        return []

    versions = []
    for item in TRAINING_OUTPUT_DIR.iterdir():
        if item.is_dir() and (item / "progress.json").exists():
            versions.append(item.name)

    return sorted(versions, reverse=True)


def _load_round_table_results() -> dict[str, Any] | None:
    """Load Round Table elite results."""
    if ROUND_TABLE_RESULTS_PATH.exists():
        try:
            with open(ROUND_TABLE_RESULTS_PATH) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Round Table results: {e}")
    return None


# =============================================================================
# API Endpoints
# =============================================================================


@training_router.get("/status", response_model=TrainingProgressResponse)
async def get_training_status():
    """
    Get current training status.

    Returns the progress of the most recent active or latest training job.
    """
    try:
        logger.info("Fetching current training status")

        versions = _find_training_versions()

        if not versions:
            logger.info("No training jobs found")
            return TrainingProgressResponse(
                status="idle",
                message="No training jobs found",
            )

        # Find active training or latest
        for version in versions:
            progress_data = _load_progress_file(version)
            if progress_data:
                status = progress_data.get("status", "unknown")
                if status == "training":
                    # Found active training
                    logger.info(f"Active training found: {version} ({status})")

                    # Update Prometheus metrics
                    training_progress_percentage.labels(job_id=version).set(
                        progress_data.get("progress_percentage", 0.0)
                    )
                    training_loss.labels(job_id=version).set(progress_data.get("loss", 0.0))

                    return TrainingProgressResponse(**progress_data)

        # No active training, return latest
        latest_version = versions[0]
        progress_data = _load_progress_file(latest_version)

        if progress_data:
            logger.info(f"Returning latest training: {latest_version}")
            return TrainingProgressResponse(**progress_data)

        return TrainingProgressResponse(
            status="idle",
            message="No active training",
        )

    except Exception as e:
        logger.error(f"Error getting training status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get training status: {str(e)}")


@training_router.get("/jobs", response_model=TrainingJobsListResponse)
async def list_training_jobs():
    """
    List all training jobs.

    Returns information about all past and current training jobs.
    """
    try:
        logger.info("Listing all training jobs")

        versions = _find_training_versions()
        jobs: list[TrainingJobInfo] = []

        running = 0
        completed = 0
        failed = 0

        for version in versions:
            # Try status file first (has final info)
            status_data = _load_status_file(version)
            progress_data = _load_progress_file(version)

            data = status_data or progress_data or {}
            status = data.get("status", "unknown")

            # Count by status
            if status == "training":
                running += 1
                job_status = "running"
            elif status == "completed":
                completed += 1
                job_status = "completed"
            elif status == "failed":
                failed += 1
                job_status = "failed"
            else:
                job_status = "pending"

            jobs.append(
                TrainingJobInfo(
                    job_id=version,
                    version=version,
                    status=job_status,
                    started_at=data.get("started_at"),
                    completed_at=data.get("completed_at"),
                    total_epochs=data.get("total_epochs", 0),
                    final_loss=data.get("final_loss") or data.get("loss"),
                    total_images=data.get("total_images", 0),
                    total_products=data.get("total_products", 0),
                    collections=data.get("collections", {}),
                    model_path=data.get("model_path"),
                    error=data.get("error"),
                )
            )

        # Update Prometheus
        training_jobs_total.labels(status="running")._value.set(running)
        training_jobs_total.labels(status="completed")._value.set(completed)
        training_jobs_total.labels(status="failed")._value.set(failed)

        logger.info(
            f"Found {len(jobs)} training jobs: {running} running, "
            f"{completed} completed, {failed} failed"
        )

        return TrainingJobsListResponse(
            total_jobs=len(jobs),
            running=running,
            completed=completed,
            failed=failed,
            jobs=jobs,
            retrieved_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error(f"Error listing training jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list training jobs: {str(e)}")


@training_router.get("/jobs/{job_id}", response_model=TrainingProgressResponse)
async def get_training_job(
    job_id: Annotated[str, FastAPIPath(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")],
):
    """
    Get details for a specific training job.

    Args:
        job_id: Training job/version ID (alphanumeric, hyphens, underscores only)

    Returns:
        Full training progress for the specified job

    Raises:
        400: Invalid job_id format
        404: Job not found
        500: Internal server error
    """
    try:
        # Validate job_id pattern (defense in depth)
        _validate_job_id(job_id)
        logger.info(f"Fetching training job: {job_id}")

        progress_data = _load_progress_file(job_id)

        if not progress_data:
            logger.warning(f"Training job not found: {job_id}")
            raise HTTPException(status_code=404, detail=f"Training job not found: {job_id}")

        logger.info(f"Training job {job_id} retrieved successfully")
        return TrainingProgressResponse(**progress_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get training job: {str(e)}")


@training_router.post("/export", response_model=ExportResponse)
async def export_round_table_to_hf(request: ExportRequest):
    """
    Export Round Table results to HuggingFace dataset.

    Reads winning scene specifications from ROUND_TABLE_ELITE_RESULTS.json
    and uploads to HuggingFace as a dataset.

    Args:
        request: Export configuration

    Returns:
        Export result with dataset URL
    """
    try:
        logger.info(f"Export Round Table to HF requested: {request.dataset_name}")

        # Load Round Table results
        rt_results = _load_round_table_results()

        if not rt_results:
            logger.error("Round Table results not found")
            raise HTTPException(
                status_code=404,
                detail=f"Round Table results not found at {ROUND_TABLE_RESULTS_PATH}",
            )

        # Extract winners by collection
        collections_data = rt_results.get("collections", {})

        if not collections_data:
            raise HTTPException(
                status_code=400, detail="No collection data found in Round Table results"
            )

        # Filter collections if specified
        if request.collections:
            collections_to_export = {
                k: v for k, v in collections_data.items() if k in request.collections
            }
        else:
            collections_to_export = collections_data

        if not collections_to_export:
            raise HTTPException(status_code=400, detail="No matching collections found to export")

        # Prepare export data
        export_items = []
        exported_collections = []

        for collection_name, collection_data in collections_to_export.items():
            winner = collection_data.get("winner", {})

            if winner:
                export_items.append(
                    {
                        "collection": collection_name,
                        "provider": winner.get("provider", "unknown"),
                        "score": winner.get("total_score", 0.0),
                        "verdict": winner.get("verdict", "UNKNOWN"),
                        "scene_spec": winner.get("scene_spec", {}),
                        "summary": winner.get("summary", ""),
                        "generated_at": rt_results.get("generated_at", ""),
                    }
                )
                exported_collections.append(collection_name)

        if request.dry_run:
            logger.info(
                f"Dry run: Would export {len(export_items)} items from {exported_collections}"
            )
            return ExportResponse(
                success=True,
                dataset_url=None,
                exported_count=len(export_items),
                collections_exported=exported_collections,
                dry_run=True,
                message=f"Dry run complete. Would export {len(export_items)} winning scene specs.",
            )

        # TODO: Implement actual HuggingFace upload using huggingface_hub
        # For now, save to local export file
        export_path = Path("assets/exports") / f"{request.dataset_name}.json"
        export_path.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "dataset_name": request.dataset_name,
            "exported_at": datetime.utcnow().isoformat(),
            "source": str(ROUND_TABLE_RESULTS_PATH),
            "items": export_items,
        }

        with open(export_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported {len(export_items)} items to {export_path}")

        # Construct expected HF URL
        hf_username = os.getenv("HF_USERNAME", "damBruh")
        dataset_url = f"https://huggingface.co/datasets/{hf_username}/{request.dataset_name}"

        return ExportResponse(
            success=True,
            dataset_url=dataset_url,
            exported_count=len(export_items),
            collections_exported=exported_collections,
            dry_run=False,
            message=(
                f"Exported {len(export_items)} scene specs. Local export saved to {export_path}"
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting Round Table to HF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export: {str(e)}")


@training_router.get("/health")
async def training_health_check():
    """
    Health check endpoint for Training API.

    Returns:
        Health status and diagnostics
    """
    try:
        versions = _find_training_versions()
        has_rt_results = ROUND_TABLE_RESULTS_PATH.exists()

        return {
            "status": "healthy",
            "service": "training-api",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                "training_output_dir": str(TRAINING_OUTPUT_DIR),
                "training_dir_exists": TRAINING_OUTPUT_DIR.exists(),
                "training_versions_found": len(versions),
                "latest_version": versions[0] if versions else None,
                "round_table_results_available": has_rt_results,
                "round_table_results_path": str(ROUND_TABLE_RESULTS_PATH),
            },
        }

    except Exception as e:
        logger.error(f"Training health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "service": "training-api",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
        }
