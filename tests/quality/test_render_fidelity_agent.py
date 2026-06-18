"""Task 9 — Step 1 (failing test).

Tests RenderFidelityEvaluator, the job-title agent that binds ImageryAdapter
to EvaluationCore.  deterministic_checks is monkeypatched so the test exercises
the judge path (the raw bytes b"\x89PNG" are not a valid PNG and would
short-circuit to passed=False without the patch).
"""

from evaluation.agents import RenderFidelityEvaluator
from scripts.oai_render.qc import RenderExpectation


def _exp():
    return RenderExpectation(
        sku="br-001",
        name="X",
        style="ghost",
        view="front",
        is_pair=False,
        is_patch=False,
        reference_paths=(),
    )


async def test_agent_scores_via_core_and_judge(monkeypatch):
    # Patch out deterministic_checks inside the imagery adapter so the
    # fake bytes don't short-circuit before the judge is called.
    monkeypatch.setattr(
        "evaluation.domains.imagery.deterministic_checks",
        lambda data: [],
    )

    captured = {}

    def fake_judge(req):
        captured["req"] = req
        return (
            {
                "visual_analysis": "ok",
                "is_single_photograph": True,
                "garment_matches_reference": True,
                "view_correct": True,
                "branding_legible_and_correct": True,
                "photorealistic_not_flat": True,
                "all_garments_present": True,
                "reason": "pass",
            },
            0.03,
        )

    agent = RenderFidelityEvaluator(judge_fn=fake_judge)
    assert agent.job_title == "Render Fidelity Evaluator"

    v = await agent.evaluate(subject=b"\x89PNG", ref=_exp())

    assert v.passed is True
    assert v.domain == "imagery"
    assert v.cost_usd == 0.03
    assert "tool" in captured["req"]
