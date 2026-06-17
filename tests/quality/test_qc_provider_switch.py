"""Test: QCGate provider-selection — anthropic branch delegates to injected judge_fn."""

from scripts.oai_render import config
from scripts.oai_render.qc import QCGate, RenderExpectation


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


def test_anthropic_provider_uses_claude_judge(monkeypatch):
    monkeypatch.setattr(config, "QC_JUDGE_PROVIDER", "anthropic")
    calls = {}

    def fake_judge(req):
        calls["req"] = req
        return (
            {
                "visual_analysis": "v",
                "is_single_photograph": True,
                "garment_matches_reference": True,
                "view_correct": True,
                "branding_legible_and_correct": True,
                "photorealistic_not_flat": True,
                "all_garments_present": True,
                "reason": "pass",
            },
            0.02,
        )

    gate = QCGate(use_judge=True, judge_fn=fake_judge)
    monkeypatch.setattr("scripts.oai_render.qc.deterministic_checks", lambda data: [])
    verdict = gate.check(b"\x89PNG", _exp())
    assert verdict.passed is True
    assert verdict.judge_cost_usd == 0.02
    assert "req" in calls
