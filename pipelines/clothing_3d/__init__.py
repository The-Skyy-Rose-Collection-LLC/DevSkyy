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
from pipelines.clothing_3d.models import (
    PipelineQualityReport,
    PipelineRequest,
    PipelineResult,
    PipelineStage,
    PipelineStatus,
    StageReport,
)
from pipelines.clothing_3d.pipeline import ClothingPipeline
from pipelines.clothing_3d.storage import (
    ArtifactBundle,
    ArtifactStore,
    LocalArtifactStore,
)

__all__ = [
    "ArtifactBundle",
    "ArtifactStore",
    "ClothingPipeline",
    "LocalArtifactStore",
    "PipelineEvent",
    "PipelineEventBus",
    "PipelineQualityReport",
    "PipelineRequest",
    "PipelineResult",
    "PipelineStage",
    "PipelineStatus",
    "StageReport",
]
