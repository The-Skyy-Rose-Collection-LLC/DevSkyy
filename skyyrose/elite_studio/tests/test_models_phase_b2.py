from dataclasses import dataclass
from skyyrose.elite_studio.models import (
    DualAgentResult,
    PreflightResult,
    GhostMannequinCompositeResult,
)

def test_dual_agent_result_fields():
    r = DualAgentResult(
        verdict="consensus",
        agent_a_output="YES: garment matches spec",
        agent_b_output="YES: confirmed hoodie",
        winner=None,
        reasoning=["both agents confirmed garment type"],
    )
    assert r.verdict == "consensus"
    assert r.winner is None

def test_preflight_result_blocked():
    r = PreflightResult(
        passed=False,
        sku="br-011",
        agent_a_verdict="NO: baseball jersey, not hockey",
        agent_b_verdict="NO: wrong sport",
        blocking_reason="Agent A: baseball jersey, not hockey",
    )
    assert not r.passed

def test_ghost_mannequin_composite_result():
    r = GhostMannequinCompositeResult(
        success=True,
        output_path="renders/output/br-004-ghost-front-composite.webp",
        front_path="renders/output/br-004-ghost-front.webp",
        back_path="renders/output/br-004-ghost-back.webp",
        neck_in_applied=True,
    )
    assert r.neck_in_applied
