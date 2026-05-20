"""Clothing 3D pipeline.

End-to-end orchestration around the
:class:`~services.three_d.trellis.provider.TrellisProvider`. Coordinates:

1. Ingestion + validation (:func:`pipelines.clothing_3d.stages.ingest`)
2. Preprocessing
3. TRELLIS generation
4. Postprocessing (mesh cleanup, USDZ, thumbnail)
5. Quality gate
6. Artifact storage
7. Event emission

Entry point:

.. code-block:: python

    from pipelines.clothing_3d import ClothingPipeline, PipelineRequest

    pipeline = ClothingPipeline()
    result = await pipeline.run(
        PipelineRequest(
            image_url="https://...",
            product_name="Black Rose Hoodie",
            collection="black_rose",
            garment_type="hoodie",
        )
    )
"""

from __future__ import annotations

from pipelines.clothing_3d.events import PipelineEvent, PipelineEventBus
from pipelines.clothing_3d.job_store import (
    InMemoryJobStore,
    JobRecord,
    JobStore,
    RedisJobStore,
    build_job_store,
)
from pipelines.clothing_3d.models import (
    PipelineQualityReport,
    PipelineRequest,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
    StageReport,
)
from pipelines.clothing_3d.observability import (
    PipelineMetrics,
    configure_logging,
    get_metrics,
    metrics_event_subscriber,
    render_metrics,
)
from pipelines.clothing_3d.pipeline import ClothingPipeline
from pipelines.clothing_3d.queue import (
    InMemoryQueue,
    JobQueue,
    QueueMessage,
    RedisStreamsQueue,
    build_queue,
)
from pipelines.clothing_3d.reliability import (
    CostQuota,
    IdempotencyCache,
    IdempotencyStore,
    InMemoryIdempotencyStore,
    QuotaExceededError,
    RetryPolicy,
    request_fingerprint,
)
from pipelines.clothing_3d.runtime import (
    PipelineRuntime,
    configure,
    generate,
    get_runtime,
    preflight,
    reset_runtime,
)
from pipelines.clothing_3d.storage import (
    ArtifactBundle,
    ArtifactStore,
    LocalArtifactStore,
)
from pipelines.clothing_3d.worker import PipelineWorker

__all__ = [
    "ArtifactBundle",
    "ArtifactStore",
    "ClothingPipeline",
    "CostQuota",
    "IdempotencyCache",
    "IdempotencyStore",
    "InMemoryIdempotencyStore",
    "InMemoryJobStore",
    "InMemoryQueue",
    "JobQueue",
    "JobRecord",
    "JobStore",
    "LocalArtifactStore",
    "PipelineEvent",
    "PipelineEventBus",
    "PipelineMetrics",
    "PipelineQualityReport",
    "PipelineRequest",
    "PipelineResult",
    "PipelineRuntime",
    "PipelineStage",
    "PipelineStatus",
    "PipelineWorker",
    "QueueMessage",
    "QuotaExceededError",
    "RedisJobStore",
    "RedisStreamsQueue",
    "RetryPolicy",
    "StageReport",
    "build_job_store",
    "build_queue",
    "configure",
    "configure_logging",
    "generate",
    "get_metrics",
    "get_runtime",
    "metrics_event_subscriber",
    "preflight",
    "render_metrics",
    "request_fingerprint",
    "reset_runtime",
]
