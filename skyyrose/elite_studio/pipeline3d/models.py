"""Core data types for the 3D pipeline orchestrator.

All data is immutable (frozen dataclasses). The Artifact is the chaining
handle: it carries BOTH a provider-native task_id (cheap same-provider
chaining) AND a downloadable model_url / local path (cross-provider handoff).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Stage(StrEnum):
    """Fashion-tuned pipeline stages (no rig/animate)."""

    IMAGE_TO_3D = "image_to_3d"
    TEXTURE = "texture"
    REMESH = "remesh"
    EXPORT = "export"


class TaskStatus(StrEnum):
    """Normalized cross-provider task status (Meshy UPPERCASE + Tripo lowercase -> one enum)."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


#: Canonical dependency order. Executor runs stages in this order, skipping
#: any not requested.
STAGE_ORDER: tuple[Stage, ...] = (
    Stage.IMAGE_TO_3D,
    Stage.TEXTURE,
    Stage.REMESH,
    Stage.EXPORT,
)


def ordered_stages(stages: tuple[Stage, ...]) -> tuple[Stage, ...]:
    """Return the requested stages in canonical dependency order."""
    requested = set(stages)
    return tuple(s for s in STAGE_ORDER if s in requested)


@dataclass(frozen=True)
class Artifact:
    """The chaining handle passed from stage to stage."""

    provider: str
    fmt: str = "glb"
    task_id: str | None = None
    model_url: str | None = None
    path: Path | None = None
    polycount: int | None = None
    bytes: int | None = None
    meta: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StageSpec:
    """A requested stage plus its per-stage parameters."""

    stage: Stage
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class JobSpec:
    """A complete pipeline job."""

    sku: str
    source_image: Path
    stages: tuple[Stage, ...]
    formats: tuple[str, ...] = ("glb",)
    provider_hint: str | None = None
    budget_ceiling_usd: float = 5.0
    output_dir: Path = Path("renders/3d")
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class StageResult:
    """Outcome of one stage."""

    stage: Stage
    artifact: Artifact
    cost_usd: float
    duration_ms: int
    cached: bool = False


@dataclass(frozen=True)
class PipelineResult:
    """Outcome of a whole job."""

    job_id: str
    sku: str
    status: TaskStatus
    results: tuple[StageResult, ...]
    final_artifact: Artifact | None
    total_cost_usd: float
    manifest_path: Path | None = None
    error: str | None = None
