"""Integration test: compositor invokes embedding gate before Gemini QA.

Post-H-03 refactor (compositor_agent.py → compositor/ stage package), the
gate function lives at ``compositor.stage_g_visual_qa.maybe_apply_gate``
and the ``analyze_vision`` callable is injected explicitly (formerly a
module-level default). Tests now patch ``visual_qa_gemini`` at the stage
module's import namespace and pass a sentinel callable so the gate's
reject path can short-circuit without touching the network.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image

from skyyrose.elite_studio.quality.brand_centroid import (
    BrandCentroid,
    load_centroid,
    save_centroid,
)

# Sentinel callable — never actually invoked because the gate either rejects
# (skips Gemini path entirely) or the test patches ``visual_qa_gemini`` at
# the stage module level. Keeps the required-kwarg contract satisfied.
_SENTINEL_ANALYZE_VISION = MagicMock(name="never_called_analyze_vision")


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


def _fake_gate_verdict(*, accepted: bool, reason: str = "") -> MagicMock:
    """Mimic ``embedding_gate.GateVerdict`` shape without invoking CLIP.

    ``embedding_gate.evaluate`` would otherwise load a real CLIP model + run a
    forward pass — multi-second cold start that blows the test timeout. The
    gate's CLIP scoring is exercised in `tests/elite_studio/test_embedding_gate.py`;
    this integration test only needs the verdict's downstream branching.
    """
    verdict = MagicMock(spec_set=["accepted", "reason", "score", "threshold"])
    verdict.accepted = accepted
    verdict.reason = reason or ("below brand threshold (mocked)" if not accepted else "ok")
    verdict.score = 0.5 if accepted else 0.1
    verdict.threshold = 0.4
    return verdict


def test_compositor_skips_gemini_when_gate_rejects(
    fake_centroid_file: Path, tmp_path: Path
) -> None:
    """When the gate rejects, compositor stages QA as 'fail' without calling Gemini."""
    from skyyrose.elite_studio.agents.compositor import stage_g_visual_qa
    from skyyrose.elite_studio.quality import embedding_gate

    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with (
        patch.object(stage_g_visual_qa, "visual_qa_gemini") as mock_gemini,
        patch.object(embedding_gate, "evaluate", return_value=_fake_gate_verdict(accepted=False)),
    ):
        verdict = stage_g_visual_qa.maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
            analyze_vision=_SENTINEL_ANALYZE_VISION,
        )
        assert verdict["status"] == "fail"
        assert "below brand threshold" in verdict["reason"].lower()
        mock_gemini.assert_not_called()


def test_compositor_calls_gemini_when_gate_accepts(
    fake_centroid_file: Path, tmp_path: Path
) -> None:
    """When the gate accepts, compositor proceeds to Gemini QA."""
    from skyyrose.elite_studio.agents.compositor import stage_g_visual_qa
    from skyyrose.elite_studio.quality import embedding_gate

    centroid = load_centroid(fake_centroid_file)
    centroid.threshold = -1.0  # force acceptance
    save_centroid(centroid, fake_centroid_file)

    img = Image.new("RGB", (224, 224), color=(50, 50, 50))
    img_path = tmp_path / "shadow.png"
    img.save(img_path)

    with (
        patch.object(
            stage_g_visual_qa, "visual_qa_gemini", return_value={"status": "pass"}
        ) as mock_gemini,
        patch.object(embedding_gate, "evaluate", return_value=_fake_gate_verdict(accepted=True)),
    ):
        verdict = stage_g_visual_qa.maybe_apply_gate(
            shadow_path=str(img_path),
            scene_name="oakland_night",
            collection="black-rose",
            centroid_path=fake_centroid_file,
            analyze_vision=_SENTINEL_ANALYZE_VISION,
        )
        assert verdict["status"] == "pass"
        mock_gemini.assert_called_once()
