"""End-to-end: CopyEvaluator -> EvaluationCore -> judge -> Verdict.

Mirrors tests/quality/test_render_fidelity_e2e.py. Four scenarios:
1. Deterministic hard-fail (retired tagline) — blocks the paid judge entirely.
2. Clean copy — full pass-through to a fake judge, verdict passes.
3. gate() revise loop — first judge call fails, regenerate, second passes (attempts=1).
4. gate() cap — judge never passes, attempts caps at the configured limit.
"""

from __future__ import annotations

import pytest

from evaluation.agents import CopyEvaluator
from evaluation.domains.copy import CopyAdapter, CopyBrief


def _brief(collection: str | None = "black_rose") -> CopyBrief:
    return CopyBrief(
        collection=collection,
        content_type="product_description",
        product_name="Black Rose Crewneck",
        brand_voice_context="Declarative fragments. Refusal as posture.",
        additional_direction="",
    )


def _good_output(**overrides) -> dict:
    out = {
        "brand_analysis": "Declarative, no hedging, garment named.",
        "brand_voice_fidelity": 5,
        "correct_collection_canon": 5,
        "garment_as_protagonist": 5,
        "no_urgency_theatre": 5,
        "no_related_products_push": 5,
        "name_not_sku_referencing": 5,
        "canonical_tagline_only": 5,
        "oakland_anchoring": 5,
        "failure_tags": [],
        "reason": "clean",
    }
    out.update(overrides)
    return out


@pytest.mark.asyncio
async def test_deterministic_hard_fail_blocks_judge():
    """Retired tagline trips the deterministic gate; the paid judge is never invoked."""
    called = {"judge": False}

    def judge(req):
        called["judge"] = True
        return ({}, 0.0)

    agent = CopyEvaluator(judge_fn=judge)
    v = await agent.evaluate(subject="Where Love Meets Luxury.", ref=_brief())

    assert v.passed is False
    assert "retired_tagline_present" in v.failure_tags
    assert called["judge"] is False


@pytest.mark.asyncio
async def test_clean_copy_passes_through_judge():
    """No deterministic failures -> judge called -> verdict passes with score 1.0."""

    def judge(req):
        return (_good_output(brand_analysis="navy crewneck, declarative voice"), 0.012)

    agent = CopyEvaluator(judge_fn=judge)
    v = await agent.evaluate(
        subject="Luxury Grows from Concrete. The Black Rose Crewneck is armor.",
        ref=_brief(),
    )

    assert v.passed is True
    assert v.score == 1.0
    assert v.cost_usd == 0.012
    assert v.detail["brand_analysis"].startswith("navy")


@pytest.mark.asyncio
async def test_gate_revises_once_then_passes():
    """First score fails on voice; revise regenerates; second score passes (attempts=1)."""
    calls = {"judge": 0, "regen": 0}

    def judge(req):
        calls["judge"] += 1
        if calls["judge"] == 1:
            return (_good_output(brand_voice_fidelity=1, correct_collection_canon=1), 0.004)
        return (_good_output(), 0.004)

    async def regenerate_fn(ref, critique):
        calls["regen"] += 1
        return "Luxury Grows from Concrete. The Black Rose Crewneck is armor."

    async def producer(ref):
        return "Initial draft, weak voice."

    agent = CopyEvaluator(judge_fn=judge, adapter=CopyAdapter(regenerate_fn=regenerate_fn))
    v = await agent.gate(ref=_brief(), producer=producer, cap=2)

    assert v.passed is True
    assert v.attempts == 1
    assert calls["regen"] == 1


@pytest.mark.asyncio
async def test_gate_caps_revisions_when_never_passes():
    """Judge never passes -> attempts caps at `cap` and the verdict stays failed."""

    def judge(req):
        return (_good_output(brand_voice_fidelity=0, correct_collection_canon=0), 0.004)

    async def regenerate_fn(ref, critique):
        return "still weak draft"

    async def producer(ref):
        return "weak draft"

    agent = CopyEvaluator(judge_fn=judge, adapter=CopyAdapter(regenerate_fn=regenerate_fn))
    v = await agent.gate(ref=_brief(), producer=producer, cap=2)

    assert v.passed is False
    assert v.attempts == 2
