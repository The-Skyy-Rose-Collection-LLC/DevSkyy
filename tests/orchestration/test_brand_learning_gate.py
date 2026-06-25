"""Security gate tests: BrandLearningLoop must not mutate live brand DNA without approval.

``BrandAdaptor.apply_insight()`` rewrites the ``brand_dict`` that ``BrandContextInjector``
injects into every agent prompt across all stages. Per the project STOP-AND-SHOW protocol,
brand-DNA adaptations fail closed — with no approval gate wired, the loop records insights
but does NOT propagate them to the live brand context.

Regression target: brand_learning.py previously applied adaptations unconditionally whenever
a brand_dict was connected (obs #18175 — ungated store path).
"""

from __future__ import annotations

from aos.governance.approval import ApprovalGate, RiskLevel
from orchestration.brand_learning import (
    BrandInsight,
    BrandLearningLoop,
    InsightCategory,
    InsightConfidence,
)


def _high_voice_insight() -> BrandInsight:
    """A HIGH-confidence insight that BrandAdaptor._adapt_voice turns into one adaptation."""
    return BrandInsight(
        category=InsightCategory.VOICE_PATTERN,
        title="anthropic excels at brand voice",
        description="provider routing hint",
        evidence_count=30,
        confidence=InsightConfidence.HIGH,
    )


async def test_adaptation_fails_closed_without_gate(tmp_path):
    """No approval gate => HIGH-confidence adaptation is NOT applied to the live brand dict."""
    loop = BrandLearningLoop(db_path=str(tmp_path / "bl.db"))
    brand: dict = {}
    loop.connect(brand_dict=brand)

    applied = await loop._apply_adaptations([_high_voice_insight()])

    assert applied == 0
    assert "_routing_hints" not in brand  # live brand DNA untouched


async def test_adaptation_applied_when_gate_approves(tmp_path):
    """A wired gate that approves => adaptation propagates to the live brand dict."""
    gate = ApprovalGate()
    gate.set_auto_approve(RiskLevel.HIGH)  # auto-approve HIGH and below
    loop = BrandLearningLoop(db_path=str(tmp_path / "bl.db"), approval_gate=gate)
    brand: dict = {}
    loop.connect(brand_dict=brand)

    applied = await loop._apply_adaptations([_high_voice_insight()])

    assert applied == 1
    assert brand["_routing_hints"]["preferred_brand_provider"] == "anthropic"


async def test_adaptation_blocked_when_gate_denies(tmp_path):
    """A wired gate that never approves (times out) => no mutation."""
    gate = ApprovalGate()  # no auto-approve; nobody resolves it -> expires
    loop = BrandLearningLoop(
        db_path=str(tmp_path / "bl.db"),
        approval_gate=gate,
        approval_timeout=0.01,
    )
    brand: dict = {}
    loop.connect(brand_dict=brand)

    applied = await loop._apply_adaptations([_high_voice_insight()])

    assert applied == 0
    assert "_routing_hints" not in brand
