"""Pydantic models for the clothing 3D pipeline."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator

from services.three_d.trellis.config import TrellisBackend, TrellisQualityPreset


# =============================================================================
# Enums
# =============================================================================


class PipelineStage(StrEnum):
    """Discrete pipeline stages — order matters."""

    INGEST = "ingest"
    PREPROCESS = "preprocess"
    GENERATE = "generate"
    POSTPROCESS = "postprocess"
    QC = "qc"
    STORE = "store"


class PipelineStatus(StrEnum):
    """Terminal & intermediate pipeline statuses."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REJECTED = "rejected"  # passed generation but failed QC


# =============================================================================
# Request / response
# =============================================================================


class PipelineRequest(BaseModel):
    """Public input contract for the clothing pipeline.

    Provide one of ``image_url`` / ``image_path`` / ``prompt``. All other fields
    are optional but improve output fidelity.
    """

    # Input — one of (image* OR prompt)
    image_url: str | None = Field(default=None)
    image_path: str | None = Field(default=None)
    prompt: str | None = Field(
        default=None,
        description="Free-form description; required when no image is provided.",
    )

    # Garment / catalog metadata
    product_name: str | None = Field(default=None)
    product_sku: str | None = Field(default=None)
    collection: str | None = Field(default=None)
    garment_type: str | None = Field(default=None)

    # Pipeline switches
    quality: TrellisQualityPreset = TrellisQualityPreset.STANDARD
    backend: TrellisBackend | None = Field(
        default=None,
        description="Force a TRELLIS backend; defaults to config.",
    )
    skip_qc: bool = False
    callback_url: str | None = Field(default=None)

    # Tracing
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _at_least_one_input(self) -> PipelineRequest:
        if not (self.image_url or self.image_path or self.prompt):
            raise ValueError("PipelineRequest requires image_url, image_path, or prompt")
        return self

    @property
    def has_image(self) -> bool:
        return bool(self.image_url or self.image_path)


# =============================================================================
# Reports
# =============================================================================


class StageReport(BaseModel):
    """Per-stage execution report (success or failure)."""

    stage: PipelineStage
    started_at: datetime
    finished_at: datetime
    success: bool
    duration_seconds: float
    detail: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    warnings: list[str] = Field(default_factory=list)


class PipelineQualityReport(BaseModel):
    """Quality-gate verdict + supporting metrics."""

    accepted: bool
    score: float
    polycount: int | None = None
    file_size_kb: int | None = None
    texture_size: int | None = None
    issues: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    """Final pipeline output returned to callers."""

    status: PipelineStatus
    artifact_id: str
    correlation_id: str

    # Primary output
    glb_url: str | None = None
    glb_path: str | None = None
    usdz_url: str | None = None
    usdz_path: str | None = None
    thumbnail_url: str | None = None

    # Diagnostics
    garment_category: str | None = None
    quality: PipelineQualityReport | None = None
    stages: list[StageReport] = Field(default_factory=list)
    total_duration_seconds: float = 0.0

    # Free-form metadata for downstream tools (web viewer, AR, analytics)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        return self.status == PipelineStatus.SUCCEEDED


__all__ = [
    "PipelineStage",
    "PipelineStatus",
    "PipelineRequest",
    "StageReport",
    "PipelineQualityReport",
    "PipelineResult",
]
