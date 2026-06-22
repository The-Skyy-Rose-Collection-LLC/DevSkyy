"""Individual pipeline stages.

Each stage is an async callable producing a :class:`StageReport`. The
:class:`~pipelines.clothing_3d.pipeline.ClothingPipeline` orchestrator
composes them and decides whether to continue based on the report.

Stages return tuples of ``(stage_report, stage_output)`` where the output is
fed to the next stage via the :class:`PipelineContext`. The orchestrator
owns timing, retries, and event emission; stages stay focused on one job.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from services.three_d.provider_interface import OutputFormat, ThreeDRequest, ThreeDResponse
from services.three_d.trellis.config import TrellisConfig
from services.three_d.trellis.garment_aware import GarmentCategory, classify_garment
from services.three_d.trellis.provider import TrellisProvider

from pipelines.clothing_3d.models import (
    PipelineQualityReport,
    PipelineRequest,
    PipelineStage,
    StageReport,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline context — mutable state threaded through stages
# =============================================================================


@dataclass(slots=True)
class PipelineContext:
    """Mutable bag of state passed between stages."""

    request: PipelineRequest
    correlation_id: str
    artifact_id: str

    # Filled in progressively
    local_image_path: str | None = None
    image_size: tuple[int, int] | None = None
    garment_category: GarmentCategory = GarmentCategory.UNKNOWN
    three_d_response: ThreeDResponse | None = None
    reports: list[StageReport] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(cls, request: PipelineRequest) -> PipelineContext:
        corr = request.correlation_id or str(uuid.uuid4())
        artifact_id = request.product_sku or f"art_{corr[:12]}"
        return cls(request=request, correlation_id=corr, artifact_id=artifact_id)


# =============================================================================
# Stage runner helper
# =============================================================================


def _start_report(stage: PipelineStage) -> tuple[datetime, float]:
    return datetime.now(UTC), time.time()


def _finish_report(
    stage: PipelineStage,
    started_at: datetime,
    started_perf: float,
    *,
    success: bool,
    detail: dict[str, Any] | None = None,
    error: str | None = None,
    warnings: list[str] | None = None,
) -> StageReport:
    return StageReport(
        stage=stage,
        started_at=started_at,
        finished_at=datetime.now(UTC),
        success=success,
        duration_seconds=round(time.time() - started_perf, 4),
        detail=detail or {},
        error=error,
        warnings=warnings or [],
    )


# =============================================================================
# Stage 1: ingest
# =============================================================================


async def stage_ingest(ctx: PipelineContext) -> StageReport:
    """Validate inputs, resolve image path, capture image metadata."""
    started_at, started_perf = _start_report(PipelineStage.INGEST)
    warnings: list[str] = []

    request = ctx.request
    if not (request.image_url or request.image_path or request.prompt):
        return _finish_report(
            PipelineStage.INGEST,
            started_at,
            started_perf,
            success=False,
            error="No input provided",
        )

    if request.image_path:
        path = Path(request.image_path)
        if not path.exists():
            return _finish_report(
                PipelineStage.INGEST,
                started_at,
                started_perf,
                success=False,
                error=f"image_path not found: {request.image_path}",
            )
        ctx.local_image_path = str(path)

    elif request.image_url:
        # Provider will download as needed; just record the URL.
        ctx.local_image_path = request.image_url

    # Classify before generation so we can route + tune sampling
    ctx.image_size = _safe_image_size(ctx.local_image_path)
    ctx.garment_category = classify_garment(
        image_path=request.image_path,
        image_size=ctx.image_size,
        declared_category=request.garment_type,
        product_name=request.product_name,
    )

    detail = {
        "input_kind": "image" if request.has_image else "text",
        "garment_category": ctx.garment_category.value,
        "image_size": ctx.image_size,
    }
    return _finish_report(
        PipelineStage.INGEST,
        started_at,
        started_perf,
        success=True,
        detail=detail,
        warnings=warnings,
    )


def _safe_image_size(path_or_url: str | None) -> tuple[int, int] | None:
    if not path_or_url:
        return None
    if path_or_url.startswith(("http://", "https://")):
        return None
    if not Path(path_or_url).exists():
        return None
    try:
        from PIL import Image

        with Image.open(path_or_url) as im:
            return im.size
    except Exception:  # noqa: BLE001
        return None


# =============================================================================
# Stage 2 + 3 + 4: provider call
#
# Preprocessing + generation + postprocessing happen inside the TrellisProvider
# because they need to share intermediate files. We expose them here as a
# single stage to keep the orchestrator boundaries clean.
# =============================================================================


async def stage_generate(
    ctx: PipelineContext,
    provider: TrellisProvider,
) -> StageReport:
    """Run preprocess → TRELLIS → postprocess via the provider."""
    started_at, started_perf = _start_report(PipelineStage.GENERATE)
    request = ctx.request

    three_d_request = ThreeDRequest(
        prompt=request.prompt,
        image_url=request.image_url,
        image_path=request.image_path,
        output_format=OutputFormat.GLB,
        product_name=request.product_name,
        collection=request.collection,
        garment_type=(
            request.garment_type
            or (
                ctx.garment_category.value
                if ctx.garment_category != GarmentCategory.UNKNOWN
                else None
            )
        ),
        correlation_id=ctx.correlation_id,
        metadata={
            "artifact_id": ctx.artifact_id,
            "quality": request.quality.value,
            **request.metadata,
        },
    )

    try:
        if request.has_image:
            response = await provider.generate_from_image(three_d_request)
        else:
            response = await provider.generate_from_text(three_d_request)
    except Exception as exc:  # noqa: BLE001 — captured in report
        return _finish_report(
            PipelineStage.GENERATE,
            started_at,
            started_perf,
            success=False,
            error=f"{type(exc).__name__}: {exc}",
        )

    ctx.three_d_response = response
    detail = {
        "provider": response.provider,
        "task_id": response.task_id,
        "polycount": response.polycount,
        "file_size_bytes": response.file_size_bytes,
        "duration_seconds": response.duration_seconds,
    }
    return _finish_report(
        PipelineStage.GENERATE,
        started_at,
        started_perf,
        success=True,
        detail=detail,
    )


# =============================================================================
# Stage 5: QC
# =============================================================================


@dataclass(frozen=True, slots=True)
class QCThresholds:
    """Acceptance bounds for the QC stage."""

    min_polycount: int = 8_000
    max_polycount: int = 250_000
    min_file_kb: int = 20
    max_file_kb: int = 25_000
    require_thumbnail: bool = False


async def stage_qc(
    ctx: PipelineContext,
    *,
    thresholds: QCThresholds | None = None,
) -> tuple[StageReport, PipelineQualityReport]:
    """Inspect the generated artifact and decide whether it's shippable."""
    started_at, started_perf = _start_report(PipelineStage.QC)
    thresholds = thresholds or QCThresholds()
    response = ctx.three_d_response

    if response is None or not response.model_path:
        report = PipelineQualityReport(
            accepted=False,
            score=0.0,
            issues=["No generated artifact to QC"],
        )
        stage_report = _finish_report(
            PipelineStage.QC,
            started_at,
            started_perf,
            success=False,
            detail=report.model_dump(),
            error="missing artifact",
        )
        return stage_report, report

    issues: list[str] = []

    polycount = response.polycount
    if polycount is not None:
        if polycount < thresholds.min_polycount:
            issues.append(f"polycount {polycount} below floor {thresholds.min_polycount}")
        elif polycount > thresholds.max_polycount:
            issues.append(f"polycount {polycount} above ceiling {thresholds.max_polycount}")

    file_kb: int | None = None
    if response.file_size_bytes:
        file_kb = response.file_size_bytes // 1024
        if file_kb < thresholds.min_file_kb:
            issues.append(f"file {file_kb} KB below floor {thresholds.min_file_kb} KB")
        elif file_kb > thresholds.max_file_kb:
            issues.append(f"file {file_kb} KB above ceiling {thresholds.max_file_kb} KB")

    if thresholds.require_thumbnail and not response.thumbnail_url:
        issues.append("missing thumbnail")

    # Score: 1.0 if no issues, penalize 0.2 each.
    score = max(0.0, 1.0 - 0.2 * len(issues))
    accepted = not issues or ctx.request.skip_qc

    report = PipelineQualityReport(
        accepted=accepted,
        score=round(score, 3),
        polycount=polycount,
        file_size_kb=file_kb,
        texture_size=response.metadata.get("texture_size") if response.metadata else None,
        issues=issues,
    )
    stage_report = _finish_report(
        PipelineStage.QC,
        started_at,
        started_perf,
        success=True,  # QC ran; acceptance is in the report
        detail=report.model_dump(),
        warnings=issues,
    )
    return stage_report, report


# =============================================================================
# Stage 6: store
# =============================================================================


async def stage_store(
    ctx: PipelineContext,
    *,
    store,
):
    """Persist artifacts via the configured :class:`ArtifactStore`."""
    from pipelines.clothing_3d.storage import ArtifactBundle  # local import to avoid cycle

    started_at, started_perf = _start_report(PipelineStage.STORE)
    response = ctx.three_d_response
    if response is None or not response.model_path:
        return (
            _finish_report(
                PipelineStage.STORE,
                started_at,
                started_perf,
                success=False,
                error="No artifact to store",
            ),
            None,
        )

    meta = response.metadata or {}
    bundle = ArtifactBundle(
        artifact_id=ctx.artifact_id,
        glb_path=response.model_path,
        usdz_path=meta.get("usdz_path"),
        thumbnail_path=meta.get("thumbnail_path"),
        splat_path=meta.get("splat_path"),
        extra={
            "category": ctx.garment_category.value,
            "collection": ctx.request.collection or "",
            "product_name": ctx.request.product_name or "",
        },
    )

    try:
        stored = await store.store(bundle)
    except Exception as exc:  # noqa: BLE001
        return (
            _finish_report(
                PipelineStage.STORE,
                started_at,
                started_perf,
                success=False,
                error=f"{type(exc).__name__}: {exc}",
            ),
            None,
        )

    detail = {
        "glb_url": stored.glb_url,
        "usdz_url": stored.usdz_url,
        "thumbnail_url": stored.thumbnail_url,
        "metadata": stored.metadata,
    }
    return (
        _finish_report(
            PipelineStage.STORE,
            started_at,
            started_perf,
            success=True,
            detail=detail,
        ),
        stored,
    )


# =============================================================================
# Stage factory exports
# =============================================================================


def default_thresholds_for(config: TrellisConfig) -> QCThresholds:
    """Tune QC thresholds based on the active TRELLIS quality preset."""
    quality = config.quality.value
    if quality == "draft":
        return QCThresholds(min_polycount=4_000, max_polycount=120_000, min_file_kb=10)
    if quality == "production":
        return QCThresholds(
            min_polycount=20_000,
            max_polycount=300_000,
            min_file_kb=50,
            require_thumbnail=False,
        )
    return QCThresholds()


__all__ = [
    "PipelineContext",
    "QCThresholds",
    "default_thresholds_for",
    "stage_generate",
    "stage_ingest",
    "stage_qc",
    "stage_store",
]
