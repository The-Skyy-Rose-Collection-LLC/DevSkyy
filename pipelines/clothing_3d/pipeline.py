"""End-to-end clothing 3D pipeline orchestrator."""

from __future__ import annotations

import logging
import time
from typing import Any

from pipelines.clothing_3d.events import PipelineEventBus, log_event_subscriber
from pipelines.clothing_3d.models import (
    PipelineQualityReport,
    PipelineRequest,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
)
from pipelines.clothing_3d.stages import (
    PipelineContext,
    QCThresholds,
    default_thresholds_for,
    stage_generate,
    stage_ingest,
    stage_qc,
    stage_store,
)
from pipelines.clothing_3d.storage import ArtifactStore, LocalArtifactStore
from services.three_d.trellis.config import TrellisConfig
from services.three_d.trellis.provider import TrellisProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Pipeline
# =============================================================================


class ClothingPipeline:
    """Orchestrator for the clothing 3D pipeline.

    Construct with sensible defaults and call :meth:`run` per request. Inject
    a custom ``provider`` / ``store`` / ``event_bus`` for tests or alternate
    deployments.

    Args:
        config: TRELLIS configuration (defaults to env).
        provider: Pre-built TRELLIS provider — useful for tests with a stub
            backend.
        store: Artifact store. Defaults to :class:`LocalArtifactStore`.
        event_bus: Event bus. Defaults to a bus with the stdlib log subscriber.
        thresholds: QC thresholds. Defaults are tuned by quality preset.
    """

    def __init__(
        self,
        *,
        config: TrellisConfig | None = None,
        provider: TrellisProvider | None = None,
        store: ArtifactStore | None = None,
        event_bus: PipelineEventBus | None = None,
        thresholds: QCThresholds | None = None,
    ) -> None:
        self.config = config or TrellisConfig.from_env()
        self.config.ensure_dirs()
        self.provider = provider or TrellisProvider(self.config)
        self.store: ArtifactStore = store or LocalArtifactStore(base_dir=self.config.output_dir)
        self.event_bus = event_bus or self._default_event_bus()
        self.thresholds = thresholds or default_thresholds_for(self.config)

    @staticmethod
    def _default_event_bus() -> PipelineEventBus:
        bus = PipelineEventBus()
        bus.subscribe(log_event_subscriber())
        return bus

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def run(self, request: PipelineRequest) -> PipelineResult:
        """Execute the pipeline end-to-end for a single request."""
        ctx = PipelineContext.new(request)
        started_perf = time.time()

        logger.info(
            "clothing_3d.pipeline.start",
            extra={
                "correlation_id": ctx.correlation_id,
                "product_name": request.product_name,
                "has_image": request.has_image,
                "quality": request.quality.value,
            },
        )

        await self._emit(ctx, "pipeline.started", status=PipelineStatus.RUNNING)

        try:
            return await self._run_stages(ctx, started_perf)
        except Exception as exc:  # noqa: BLE001 — converted to failed result
            logger.exception(
                "clothing_3d.pipeline.unhandled",
                extra={"correlation_id": ctx.correlation_id},
            )
            await self._emit(
                ctx,
                "pipeline.failed",
                status=PipelineStatus.FAILED,
                payload={"error": str(exc)},
            )
            return self._build_failed(
                ctx,
                error=f"unhandled: {exc}",
                started_perf=started_perf,
            )

    async def close(self) -> None:
        """Release provider resources."""
        await self.provider.close()

    # ---------------------------------------------------------------------
    # Stage runner
    # ---------------------------------------------------------------------

    async def _run_stages(
        self,
        ctx: PipelineContext,
        started_perf: float,
    ) -> PipelineResult:
        # ---- 1. Ingest ----
        await self._emit(ctx, "stage.started", stage=PipelineStage.INGEST)
        ingest_report = await stage_ingest(ctx)
        ctx.reports.append(ingest_report)
        await self._emit(
            ctx,
            "stage.finished",
            stage=PipelineStage.INGEST,
            payload=ingest_report.detail,
        )
        if not ingest_report.success:
            return await self._fail(ctx, started_perf, ingest_report.error or "ingest failed")

        # ---- 2-4. Generate (preprocess + TRELLIS + postprocess) ----
        await self._emit(ctx, "stage.started", stage=PipelineStage.GENERATE)
        generate_report = await stage_generate(ctx, self.provider)
        ctx.reports.append(generate_report)
        await self._emit(
            ctx,
            "stage.finished",
            stage=PipelineStage.GENERATE,
            payload=generate_report.detail,
        )
        if not generate_report.success:
            return await self._fail(ctx, started_perf, generate_report.error or "generate failed")

        # ---- 5. QC ----
        quality_report: PipelineQualityReport | None = None
        if not ctx.request.skip_qc:
            await self._emit(ctx, "stage.started", stage=PipelineStage.QC)
            qc_report, quality_report = await stage_qc(ctx, thresholds=self.thresholds)
            ctx.reports.append(qc_report)
            await self._emit(
                ctx,
                "stage.finished",
                stage=PipelineStage.QC,
                payload=qc_report.detail,
            )
            if not quality_report.accepted:
                return await self._reject(ctx, started_perf, quality_report)

        # ---- 6. Store ----
        await self._emit(ctx, "stage.started", stage=PipelineStage.STORE)
        store_report, stored = await stage_store(ctx, store=self.store)
        ctx.reports.append(store_report)
        await self._emit(
            ctx,
            "stage.finished",
            stage=PipelineStage.STORE,
            payload=store_report.detail,
        )
        if not store_report.success or stored is None:
            return await self._fail(ctx, started_perf, store_report.error or "store failed")

        # ---- Done ----
        total = round(time.time() - started_perf, 4)
        result = PipelineResult(
            status=PipelineStatus.SUCCEEDED,
            artifact_id=stored.artifact_id,
            correlation_id=ctx.correlation_id,
            glb_url=stored.glb_url,
            glb_path=stored.glb_path,
            usdz_url=stored.usdz_url,
            usdz_path=stored.usdz_path,
            thumbnail_url=stored.thumbnail_url,
            garment_category=ctx.garment_category.value,
            quality=quality_report,
            stages=ctx.reports,
            total_duration_seconds=total,
            metadata=self._summary_metadata(ctx, stored),
        )
        await self._emit(
            ctx,
            "pipeline.succeeded",
            status=PipelineStatus.SUCCEEDED,
            payload={
                "artifact_id": stored.artifact_id,
                "glb_url": stored.glb_url,
                "duration": total,
            },
        )
        return result

    # ---------------------------------------------------------------------
    # Outcome builders
    # ---------------------------------------------------------------------

    async def _fail(
        self,
        ctx: PipelineContext,
        started_perf: float,
        error: str,
    ) -> PipelineResult:
        await self._emit(
            ctx,
            "pipeline.failed",
            status=PipelineStatus.FAILED,
            payload={"error": error},
        )
        return self._build_failed(ctx, error=error, started_perf=started_perf)

    async def _reject(
        self,
        ctx: PipelineContext,
        started_perf: float,
        quality_report: PipelineQualityReport,
    ) -> PipelineResult:
        await self._emit(
            ctx,
            "pipeline.rejected",
            status=PipelineStatus.REJECTED,
            payload={"issues": quality_report.issues, "score": quality_report.score},
        )
        return PipelineResult(
            status=PipelineStatus.REJECTED,
            artifact_id=ctx.artifact_id,
            correlation_id=ctx.correlation_id,
            garment_category=ctx.garment_category.value,
            quality=quality_report,
            stages=ctx.reports,
            total_duration_seconds=round(time.time() - started_perf, 4),
        )

    def _build_failed(
        self,
        ctx: PipelineContext,
        *,
        error: str,
        started_perf: float,
    ) -> PipelineResult:
        return PipelineResult(
            status=PipelineStatus.FAILED,
            artifact_id=ctx.artifact_id,
            correlation_id=ctx.correlation_id,
            garment_category=ctx.garment_category.value,
            stages=ctx.reports,
            total_duration_seconds=round(time.time() - started_perf, 4),
            metadata={"error": error},
        )

    def _summary_metadata(self, ctx: PipelineContext, stored) -> dict[str, Any]:
        response = ctx.three_d_response
        return {
            "backend": (response.metadata.get("backend") if response else None),
            "provider": response.provider if response else None,
            "garment_category": ctx.garment_category.value,
            "preprocess": response.metadata.get("preprocess") if response else None,
            "prompt_used": response.metadata.get("prompt_used") if response else None,
            "prompt_hint": response.metadata.get("prompt_hint") if response else None,
            "store": stored.metadata if stored else None,
        }

    # ---------------------------------------------------------------------
    # Event helper
    # ---------------------------------------------------------------------

    async def _emit(
        self,
        ctx: PipelineContext,
        name: str,
        *,
        stage: PipelineStage | None = None,
        status: PipelineStatus | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await self.event_bus.emit(
            correlation_id=ctx.correlation_id,
            name=name,
            stage=stage,
            status=status,
            payload=payload,
        )


# =============================================================================
# Module-level convenience
# =============================================================================


async def run_clothing_pipeline(
    request: PipelineRequest,
    *,
    config: TrellisConfig | None = None,
) -> PipelineResult:
    """One-shot helper for callers that don't want to manage the pipeline lifecycle."""
    pipeline = ClothingPipeline(config=config)
    try:
        return await pipeline.run(request)
    finally:
        await pipeline.close()


__all__ = ["ClothingPipeline", "run_clothing_pipeline"]
