"""
Job type definitions for the Elite Studio async queue.

Pydantic V2 models for job data and results flowing through the queue.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator


class EliteStudioJobData(BaseModel):
    """Input payload for a single Elite Studio render job."""

    sku: str
    view: str = "front"
    enable_compositor: bool = False
    max_retries: int = 2
    priority: int = Field(default=5, ge=1, le=10)  # 1-10, higher = sooner
    submitted_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    @field_validator("view")
    @classmethod
    def validate_view(cls, v: str) -> str:
        if v not in {"front", "back"}:
            raise ValueError(f"view must be 'front' or 'back', got: {v!r}")
        return v

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise ValueError("sku must not be empty")
        return v


class EliteStudioJobResult(BaseModel):
    """Result payload stored in Redis after a job completes."""

    job_id: str
    sku: str
    status: str  # "queued", "running", "success", "error", "skipped"
    output_path: str = ""
    error: str = ""
    completed_at: str = ""
    stage_timings: dict[str, float] = Field(default_factory=dict)
    cost_usd: float = 0.0

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"queued", "running", "success", "error", "skipped"}
        if v not in valid:
            raise ValueError(f"status must be one of {valid}, got: {v!r}")
        return v
