"""Unit tests for :class:`TrellisProvider` using the stub backend.

These tests don't touch the network, GPU, or any optional deps beyond Pillow.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from services.three_d.provider_interface import (
    ThreeDProviderError,
    ThreeDRequest,
)
from services.three_d.trellis import (
    TrellisConfig,
    TrellisProvider,
    TrellisQualityPreset,
)
from services.three_d.trellis.client import StubClient

pil = pytest.importorskip("PIL.Image")


def _make_image(path: Path) -> Path:
    from PIL import Image

    Image.new("RGB", (640, 800), (200, 200, 200)).save(path)
    return path


def _make_provider(tmp_path: Path) -> TrellisProvider:
    cfg = TrellisConfig(
        cache_dir=str(tmp_path / "cache"),
        output_dir=str(tmp_path / "out"),
        enable_background_removal=False,
        enable_postprocess=False,
        export_usdz_for_ios=False,
        quality=TrellisQualityPreset.DRAFT,
    )
    cfg.ensure_dirs()
    return TrellisProvider(cfg, backend=StubClient(cfg))


# =============================================================================
# generate_from_image
# =============================================================================


@pytest.mark.asyncio
async def test_generate_from_image_returns_glb(tmp_path: Path) -> None:
    provider = _make_provider(tmp_path)
    img = _make_image(tmp_path / "hoodie.png")

    response = await provider.generate_from_image(
        ThreeDRequest(
            image_path=str(img),
            product_name="Black Rose Hoodie",
            collection="black_rose",
            garment_type="hoodie",
        )
    )

    assert response.success
    assert response.model_path is not None
    assert Path(response.model_path).exists()
    assert response.provider == "trellis"
    assert response.metadata["garment_category"] == "hoodie"
    assert response.metadata["backend"] == "stub"


@pytest.mark.asyncio
async def test_generate_from_image_missing_input_raises(tmp_path: Path) -> None:
    provider = _make_provider(tmp_path)
    with pytest.raises(ThreeDProviderError):
        await provider.generate_from_image(ThreeDRequest(prompt="hoodie"))


# =============================================================================
# generate_from_text
# =============================================================================


@pytest.mark.asyncio
async def test_generate_from_text_uses_clothing_prompt(tmp_path: Path) -> None:
    provider = _make_provider(tmp_path)

    response = await provider.generate_from_text(
        ThreeDRequest(
            prompt="silver chrome bomber jacket",
            product_name="BR Bomber",
            collection="black_rose",
            garment_type="jacket",
        )
    )

    assert response.success
    assert response.metadata["garment_category"] == "jacket"
    # Brand + category hints should be in the composed prompt
    prompt = response.metadata["prompt_used"]
    assert "jacket" in prompt.lower()


@pytest.mark.asyncio
async def test_text_requires_prompt(tmp_path: Path) -> None:
    provider = _make_provider(tmp_path)
    with pytest.raises(ThreeDProviderError):
        await provider.generate_from_text(ThreeDRequest())


# =============================================================================
# Health
# =============================================================================


@pytest.mark.asyncio
async def test_health_check_with_stub(tmp_path: Path) -> None:
    provider = _make_provider(tmp_path)
    health = await provider.health_check()
    assert health.is_available
    assert health.provider == "trellis"
