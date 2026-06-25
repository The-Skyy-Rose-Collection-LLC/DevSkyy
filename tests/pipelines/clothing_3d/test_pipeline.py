"""End-to-end tests for :class:`ClothingPipeline` with the stub backend."""

from __future__ import annotations

from pathlib import Path

import pytest
from services.three_d.trellis import (
    TrellisConfig,
    TrellisProvider,
    TrellisQualityPreset,
)
from services.three_d.trellis.client import StubClient

from pipelines.clothing_3d import (
    ClothingPipeline,
    PipelineEventBus,
    PipelineRequest,
    PipelineStatus,
)
from pipelines.clothing_3d.events import log_event_subscriber
from pipelines.clothing_3d.stages import QCThresholds
from pipelines.clothing_3d.storage import LocalArtifactStore

pytest.importorskip("PIL.Image")


def _config(tmp_path: Path) -> TrellisConfig:
    cfg = TrellisConfig(
        cache_dir=str(tmp_path / "cache"),
        output_dir=str(tmp_path / "out"),
        enable_background_removal=False,
        enable_postprocess=False,
        export_usdz_for_ios=False,
        quality=TrellisQualityPreset.DRAFT,
    )
    cfg.ensure_dirs()
    return cfg


def _image(tmp_path: Path, name: str = "tee.png") -> Path:
    from PIL import Image

    p = tmp_path / name
    Image.new("RGB", (700, 900), (240, 240, 240)).save(p)
    return p


def _pipeline(tmp_path: Path, *, skip_qc: bool = True) -> ClothingPipeline:
    cfg = _config(tmp_path)
    provider = TrellisProvider(cfg, backend=StubClient(cfg))
    store = LocalArtifactStore(base_dir=cfg.output_dir)
    return ClothingPipeline(
        config=cfg,
        provider=provider,
        store=store,
        # Relaxed thresholds so the stub's tiny GLB passes if QC runs at all.
        thresholds=QCThresholds(
            min_polycount=0,
            max_polycount=10**9,
            min_file_kb=0,
            max_file_kb=10**9,
        ),
    )


# =============================================================================
# Happy path
# =============================================================================


@pytest.mark.asyncio
async def test_pipeline_image_to_3d_succeeds(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    request = PipelineRequest(
        image_path=str(_image(tmp_path)),
        product_name="Signature Tee",
        collection="signature",
        garment_type="tee",
        quality=TrellisQualityPreset.DRAFT,
    )

    result = await pipeline.run(request)

    assert result.status is PipelineStatus.SUCCEEDED
    assert result.glb_url is not None
    assert result.glb_path is not None
    assert Path(result.glb_path).exists()
    assert result.garment_category == "tee"

    # All stages reported
    stages = [r.stage.value for r in result.stages]
    assert "ingest" in stages
    assert "generate" in stages
    assert "store" in stages

    await pipeline.close()


@pytest.mark.asyncio
async def test_pipeline_text_to_3d_succeeds(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    request = PipelineRequest(
        prompt="oversized crimson love-hurts hoodie",
        product_name="LH Hoodie",
        collection="love_hurts",
        garment_type="hoodie",
        quality=TrellisQualityPreset.DRAFT,
    )

    result = await pipeline.run(request)

    assert result.status is PipelineStatus.SUCCEEDED
    assert result.garment_category == "hoodie"
    assert result.metadata.get("provider") == "trellis"

    await pipeline.close()


# =============================================================================
# Failure paths
# =============================================================================


@pytest.mark.asyncio
async def test_pipeline_with_missing_image_fails_in_ingest(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    request = PipelineRequest(
        image_path=str(tmp_path / "does-not-exist.png"),
        product_name="Ghost",
    )

    result = await pipeline.run(request)

    assert result.status is PipelineStatus.FAILED
    assert result.stages[0].stage.value == "ingest"
    assert "not found" in (result.stages[0].error or "").lower()

    await pipeline.close()


# =============================================================================
# Events
# =============================================================================


@pytest.mark.asyncio
async def test_pipeline_emits_lifecycle_events(tmp_path: Path) -> None:
    bus = PipelineEventBus()
    bus.subscribe(log_event_subscriber())

    received: list[str] = []

    async def collector(event) -> None:
        received.append(event.name)

    bus.subscribe(collector)

    cfg = _config(tmp_path)
    provider = TrellisProvider(cfg, backend=StubClient(cfg))
    pipeline = ClothingPipeline(
        config=cfg,
        provider=provider,
        store=LocalArtifactStore(base_dir=cfg.output_dir),
        event_bus=bus,
    )

    request = PipelineRequest(
        image_path=str(_image(tmp_path)),
        product_name="Test",
        skip_qc=True,
    )
    await pipeline.run(request)
    await pipeline.close()

    assert "pipeline.started" in received
    assert "pipeline.succeeded" in received
    assert "stage.started" in received
    assert "stage.finished" in received


# =============================================================================
# Storage
# =============================================================================


@pytest.mark.asyncio
async def test_local_store_emits_public_urls(tmp_path: Path) -> None:
    pipeline = _pipeline(tmp_path)
    request = PipelineRequest(
        image_path=str(_image(tmp_path)),
        product_name="P",
        skip_qc=True,
    )
    result = await pipeline.run(request)
    assert result.glb_url and result.glb_url.startswith("/assets/3d-models-generated/")
    await pipeline.close()
