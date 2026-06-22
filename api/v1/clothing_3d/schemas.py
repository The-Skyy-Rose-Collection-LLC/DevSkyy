"""API schemas — thin Pydantic wrappers over the pipeline models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pipelines.clothing_3d.models import PipelineRequest, PipelineResult


class GenerateRequest(PipelineRequest):
    """Request body for ``POST /v1/clothing-3d/generate``."""


class GenerateResponse(BaseModel):
    """Synchronous response envelope."""

    ok: bool
    result: PipelineResult


class JobAcceptedResponse(BaseModel):
    """Async-style accepted response (when ``async=true`` is passed)."""

    ok: bool = True
    job_id: str
    correlation_id: str
    status_url: str


class JobStatusResponse(BaseModel):
    """Job status payload returned by the polling endpoint."""

    ok: bool
    job_id: str
    status: str
    result: PipelineResult | None = None
    error: str | None = None
    submitted_at: str | None = None
    finished_at: str | None = None


class HealthResponse(BaseModel):
    """Provider health payload."""

    ok: bool
    provider: str
    status: str
    capabilities: list[str]
    backend: str | None = None
    latency_ms: float | None = None
    error: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "GenerateRequest",
    "GenerateResponse",
    "HealthResponse",
    "JobAcceptedResponse",
    "JobStatusResponse",
]
