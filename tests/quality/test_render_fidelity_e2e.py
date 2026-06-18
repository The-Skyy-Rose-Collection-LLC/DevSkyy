"""End-to-end test: RenderFidelityEvaluator -> EvaluationCore -> judge -> Verdict.

Two scenarios:
1. Excluded SKU (sg-015) — deterministic gate must block the paid judge entirely.
2. Clean render (br-001) — full pass-through to a fake vision judge, verdict passes.
"""

import pytest

from evaluation.agents import RenderFidelityEvaluator
from scripts.oai_render.qc import RenderExpectation


def _exp(sku: str) -> RenderExpectation:
    return RenderExpectation(
        sku=sku,
        name="X",
        style="ghost",
        view="front",
        is_pair=False,
        is_patch=False,
        reference_paths=(),
    )


@pytest.mark.asyncio
async def test_excluded_sku_blocks_before_judge():
    """Deterministic gate returns 'excluded_sku' and short-circuits — judge never called."""
    called = {"judge": False}

    def judge(req):
        called["judge"] = True
        return ({}, 0.0)

    agent = RenderFidelityEvaluator(judge_fn=judge)
    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp("sg-015"))  # excluded SKU

    assert v.passed is False
    assert "excluded_sku" in v.failure_tags
    assert called["judge"] is False  # cost-protection: paid judge was never invoked


@pytest.mark.asyncio
async def test_clean_render_passes_through_vision_judge(monkeypatch):
    """Full chain: no det failures -> judge called -> verdict passes with score=1.0."""
    monkeypatch.setattr("evaluation.domains.imagery.deterministic_checks", lambda d: [])

    def judge(req):
        return (
            {
                "visual_analysis": "navy bomber white script matches reference",
                "is_single_photograph": True,
                "garment_matches_reference": True,
                "view_correct": True,
                "branding_legible_and_correct": True,
                "photorealistic_not_flat": True,
                "all_garments_present": True,
                "reason": "pass",
            },
            0.012,
        )

    agent = RenderFidelityEvaluator(judge_fn=judge)
    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp("br-001"))

    assert v.passed is True
    assert v.score == 1.0
    assert v.cost_usd == 0.012
    assert v.detail["visual_analysis"].startswith("navy")
