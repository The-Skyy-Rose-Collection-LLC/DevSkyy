"""Integration test: compositor invokes embedding gate before Gemini QA."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality.brand_centroid import (
    BrandCentroid,
    load_centroid,
    save_centroid,
)

# Network/model-download integration tests — these pull CLIP/DINO weights from
# HF Hub at runtime. Excluded from the fast gate (CI runs `-m "not slow and not
# integration"`) so a transient HF outage cannot flake main red; run on demand
# with `-m integration`.
pytestmark = pytest.mark.integration


@pytest.fixture
def fake_centroid_file(tmp_path: Path) -> Path:
    rng = np.random.default_rng(0)
    v = rng.standard_normal(512).astype(np.float32)
    v = v / np.linalg.norm(v)
    # threshold 0.99 forces rejection for any synthetic image
    centroid = BrandCentroid(centroid=v, threshold=0.99, sample_count=5, model_id="test")
    out = tmp_path / "brand_centroid.npz"
    save_centroid(centroid, out)
    return out


def test_compositor_skips_gemini_when_gate_rejects(
    fake_centroid_file: Path, tmp_path: Path
) -> None:
    """When the gate rejects, compositor stages QA as 'fail' without calling Gemini."""
    from skyyrose.elite_studio.agents import compositor_agent

    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with patch.object(compositor_agent, "_visual_qa_gemini") as mock_gemini:
        verdict = compositor_agent._maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
        )
        assert verdict["status"] == "fail"
        assert "below brand threshold" in verdict["reason"].lower()
        mock_gemini.assert_not_called()


def test_compositor_calls_gemini_when_gate_accepts(
    fake_centroid_file: Path, tmp_path: Path
) -> None:
    """When the gate accepts, compositor proceeds to Gemini QA."""
    from skyyrose.elite_studio.agents import compositor_agent

    centroid = load_centroid(fake_centroid_file)
    centroid.threshold = -1.0  # force acceptance
    save_centroid(centroid, fake_centroid_file)

    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with patch.object(
        compositor_agent, "_visual_qa_gemini", return_value={"status": "pass"}
    ) as mock_gemini:
        verdict = compositor_agent._maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
        )
        assert verdict["status"] == "pass"
        mock_gemini.assert_called_once()
