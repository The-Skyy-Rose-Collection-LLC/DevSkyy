"""Tests for the Layer 1 feedback-loop wiring: refinement prompt builder.

Three tiers, each must be reachable independently:
1. Synthesis-aware (Opus ran successfully with fixes)
2. Vision-pair fallback (synthesis missing/failed but all_fixes present)
3. Catchall (no fix data anywhere)

Plus the hallucination_veto override should always inject the strong
negative constraint when fired.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

from nano_banana.pipeline import _build_refinement_prompt
from nano_banana.tournament import JudgmentScore, TournamentResult


def _make_synth(
    *,
    overall: int = 60,
    issues: list[str] | None = None,
    fixes: list[str] | None = None,
    veto: bool = False,
) -> JudgmentScore:
    return JudgmentScore(
        judge="claude-opus-4-7",
        garment_type=80,
        color_accuracy=70,
        text_accuracy=80,
        logo_accuracy=75,
        construction_accuracy=80,
        no_hallucinations=70,
        overall=overall,
        issues=issues or [],
        suggested_fixes=fixes or [],
        raw_response="",
        rationale="...",
        vision_consensus="partial",
        hallucination_veto=veto,
    )


def _make_result(
    *,
    score: float = 60.0,
    judges: list[JudgmentScore] | None = None,
    all_fixes: list[str] | None = None,
) -> TournamentResult:
    return TournamentResult(
        candidate_path="/tmp/test.png",
        judges=judges or [],
        aggregate_score=score,
        passed_98=score >= 98.0,
        top_issues=[],
        all_fixes=all_fixes or [],
        vision_pair_mean=score,
        synthesis_overall=score if judges else None,
    )


def test_tier1_synthesis_aware_uses_synth_fixes():
    """Synthesis available with fixes — synthesis text dominates."""
    synth = _make_synth(
        issues=["white ribbing instead of black", "multi-tone rose"],
        fixes=["render uniform #0a0a0a black", "remove cloud elements"],
    )
    result = _make_result(score=45.0, judges=[synth])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "br-001" in prompt
    assert "45/100" in prompt
    assert "white ribbing instead of black" in prompt
    assert "render uniform #0a0a0a black" in prompt
    assert "REQUIRED CORRECTIONS" in prompt
    assert "DEFECTS PRESENT" in prompt
    # Tier 2/3 markers absent
    assert "Make all branding crisp" not in prompt


def test_tier1_hallucination_veto_injects_critical_block():
    """Veto fired — strong negative constraint prepended."""
    synth = _make_synth(
        overall=45,
        issues=["hallucinated cloud elements"],
        fixes=["remove all cloud and wave decorations"],
        veto=True,
    )
    result = _make_result(score=45.0, judges=[synth])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "CRITICAL" in prompt
    assert "hallucinated decorative elements" in prompt
    assert "must be completely removed" in prompt


def test_tier1_no_veto_skips_critical_block():
    """No veto — no CRITICAL block emitted (avoid noise on clean refines)."""
    synth = _make_synth(issues=["color drift"], fixes=["match base color exactly"], veto=False)
    result = _make_result(score=70.0, judges=[synth])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "CRITICAL" not in prompt
    assert "hallucinated" not in prompt


def test_tier2_synthesis_failed_falls_back_to_all_fixes():
    """Synthesis judge ran but failed (overall=0) — drop to all_fixes."""
    failed_synth = _make_synth(overall=0, issues=["synthesis error: ..."], fixes=[])
    result = _make_result(
        score=50.0,
        judges=[failed_synth],
        all_fixes=["fix from gpt", "fix from gemini"],
    )
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    # Tier 2 markers
    assert "fix from gpt" in prompt
    assert "fix from gemini" in prompt
    assert "REQUIRED CORRECTIONS" in prompt
    # Tier 1 markers absent
    assert "DEFECTS PRESENT" not in prompt
    assert "CRITICAL" not in prompt


def test_tier2_no_synthesis_judge_uses_all_fixes():
    """No synthesis judge present at all — drop to all_fixes."""
    result = _make_result(score=55.0, judges=[], all_fixes=["correct the logo position"])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "correct the logo position" in prompt
    assert "REQUIRED CORRECTIONS" in prompt


def test_tier3_no_data_uses_catchall():
    """No synthesis, no all_fixes — generic catchall prompt."""
    result = _make_result(score=60.0, judges=[], all_fixes=[])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "Fix the text and logo accuracy on this Black Rose Crewneck" in prompt
    assert "Make all branding crisp and legible" in prompt
    # No data = no specific fix list
    assert "REQUIRED CORRECTIONS" not in prompt


def test_top_5_truncation():
    """Lists are capped at 5 to avoid prompt bloat."""
    synth = _make_synth(
        issues=[f"issue {i}" for i in range(10)],
        fixes=[f"fix {i}" for i in range(10)],
    )
    result = _make_result(score=40.0, judges=[synth])
    prompt = _build_refinement_prompt("Black Rose Crewneck", "br-001", result)

    assert "issue 0" in prompt
    assert "issue 4" in prompt
    assert "issue 5" not in prompt  # truncated
    assert "fix 4" in prompt
    assert "fix 5" not in prompt


def test_synthesis_judge_property_returns_opus_only():
    """Tournament result's synthesis_judge property finds the Opus judge."""
    gpt = JudgmentScore("gpt-5.5-pro", 80, 80, 80, 80, 80, 80, 80, [], [], "")
    gemini = JudgmentScore("gemini-3.1-pro-preview", 80, 80, 80, 80, 80, 80, 80, [], [], "")
    opus = _make_synth(overall=70)

    result = _make_result(score=70.0, judges=[gpt, gemini, opus])
    assert result.synthesis_judge is opus

    result_no_synth = _make_result(score=70.0, judges=[gpt, gemini])
    assert result_no_synth.synthesis_judge is None
