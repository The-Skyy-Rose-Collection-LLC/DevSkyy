"""Frozen-contract test: pins the public API the live render path depends on.

The embeddings reframe (Phase 2) re-points these modules onto the new package.
These signatures + dataclass field sets MUST NOT change. inspect-only — importing
these modules does not load any model (encoders are lazy singletons).
"""

from __future__ import annotations

import inspect
from dataclasses import fields

import pytest

pytestmark = pytest.mark.unit


def _param_names(fn) -> list[str]:
    return list(inspect.signature(fn).parameters)


def test_embedding_gate_contract() -> None:
    from skyyrose.elite_studio.quality import embedding_gate as m

    assert _param_names(m.score_against_centroid) == ["image", "centroid"]
    assert _param_names(m.evaluate) == ["image", "centroid"]
    assert {f.name for f in fields(m.GateVerdict)} == {
        "accepted",
        "score",
        "threshold",
        "reason",
    }


def test_brand_centroid_contract() -> None:
    from skyyrose.elite_studio.quality import brand_centroid as m

    assert _param_names(m.load_centroid) == ["path"]
    assert {f.name for f in fields(m.BrandCentroid)} == {
        "centroid",
        "threshold",
        "sample_count",
        "model_id",
        "sample_paths",
    }


def test_clip_alignment_contract() -> None:
    from skyyrose.elite_studio.quality import clip_alignment as m

    assert _param_names(m.score_alignment) == ["prompt", "image"]
    assert _param_names(m.score_alignment_batch) == ["prompts", "image"]


def test_render_quality_contract() -> None:
    from skyyrose.elite_studio.quality import render_quality as m

    params = inspect.signature(m.evaluate_render).parameters
    assert list(params) == [
        "render_path",
        "prompt",
        "centroid_path",
        "min_dimension",
        "alignment_threshold",
    ]
    assert params["min_dimension"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["min_dimension"].default == 512
    assert params["alignment_threshold"].default == 0.20
    assert {f.name for f in fields(m.RenderVerdict)} == {
        "verdict",
        "brand_centroid_score",
        "alignment_score",
        "threshold_centroid",
        "threshold_alignment",
        "width",
        "height",
        "reason",
    }
    assert [v.value for v in m.Verdict] == ["ship", "review", "kill"]


def test_fidelity_metrics_contract() -> None:
    from skyyrose.elite_studio.platform.fidelity import metrics as m

    cs = inspect.signature(m.composite_score).parameters
    assert list(cs) == ["dino", "clip", "ssim"]
    assert all(p.kind == inspect.Parameter.KEYWORD_ONLY for p in cs.values())
    sv = inspect.signature(m.score_view).parameters
    assert list(sv) == ["render_path", "reference_path", "sku", "angle"]
    assert {f.name for f in fields(m.VisibleScore)} == {
        "angle",
        "dino",
        "clip",
        "ssim",
        "composite",
    }


def test_stage_g_gate_contract() -> None:
    from skyyrose.elite_studio.agents.compositor import stage_g_visual_qa as m

    params = inspect.signature(m.maybe_apply_gate).parameters
    assert list(params) == [
        "shadow_path",
        "scene_name",
        "collection",
        "analyze_vision",
        "centroid_path",
    ]
    assert params["analyze_vision"].kind == inspect.Parameter.KEYWORD_ONLY
    assert params["centroid_path"].default is None
