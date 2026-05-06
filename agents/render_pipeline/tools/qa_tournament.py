"""Tool 6: 3-judge QA tournament + learning-loop recorder. PAID API CALLS.

Wraps `nano_banana.tournament.run_tournament` and feeds results into
the continuous-improvement subsystem (`agents.render_pipeline.learning`).

The 3 judges (verified models, 2026-05-04):
    GPT-5.5-pro                — vision judge (Responses API, json_schema)
    gemini-3.1-pro-preview     — vision judge (constrained decoding)
    claude-opus-4-7            — synthesis judge (text-only, adaptive thinking)

F5 finding (load-bearing): the tournament infrastructure is fragile —
sg-007 + lh-004 both hit Gemini 504 timeouts simultaneously across the
two vision judges (1/4 SKUs in the multi-SKU run). This tool surfaces
the infra-vs-quality distinction via `infra_failures` so the agent can
distinguish "score=0 because timeout" from "score=0 because bad output".

Learning-loop recorders:
    Loop 1 — engine winrate per SKU (always recorded)
    Loop 2 — template A/B scores (always recorded)
    Loop 3 — failure modes (only when score < 50)

State writes:
    qa_score, qa_passed, hallucination_veto, top_issues, all_fixes,
    infra_failures (list — empty on success)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from agents.render_pipeline.tools._paths import ensure_repo_paths

ensure_repo_paths()

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from google.adk.tools.tool_context import ToolContext


def _build_tournament_clients() -> dict:
    """Build the 3 judge clients. Anthropic + OpenAI + Google."""
    import os

    from nano_banana.client import get_genai_client, get_openai_client

    clients: dict = {
        "openai": None,
        "gemini": None,
        "anthropic": None,
    }

    try:
        clients["gemini"] = get_genai_client()
    except Exception as exc:
        log.warning("gemini client unavailable: %s", exc)

    try:
        clients["openai"] = get_openai_client()
    except Exception as exc:
        log.warning("openai client unavailable: %s", exc)

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key:
        try:
            import anthropic

            clients["anthropic"] = anthropic.Anthropic(api_key=anthropic_key)
        except ImportError:
            log.warning("anthropic SDK not installed — synthesis judge unavailable")

    return clients


def qa_tournament_fn(sku: str, tool_context: "ToolContext") -> dict:
    """Run the tournament, record learning signals, surface infra-vs-quality.

    Reads state: source_path, candidate_path, engine, template_id, estimated_cost_usd
    Writes state: qa_score, qa_passed, hallucination_veto, top_issues, all_fixes,
                  infra_failures, should_refine

    Returns the same fields as a flat dict for the LLM to read in its response.
    """
    from nano_banana.spec_builder import build_dna_from_sku
    from nano_banana.tournament import run_tournament

    from agents.render_pipeline.learning.recorder import (
        record_engine_outcome,
        record_failure_mode,
        record_template_score,
    )

    source_path_str = tool_context.state.get("source_path", "")
    candidate_path_str = tool_context.state.get("candidate_path", "")
    engine = tool_context.state.get("engine", "unknown")
    template_id = tool_context.state.get("template_id", "unknown")
    cost_so_far = float(tool_context.state.get("estimated_cost_usd", 0.0))

    if not source_path_str or not candidate_path_str:
        return {
            "error": (
                f"missing required state — source_path={source_path_str!r}, "
                f"candidate_path={candidate_path_str!r}. "
                f"Check that resolve_source + generate_image ran first."
            )
        }

    source_path = Path(source_path_str)
    candidate_path = Path(candidate_path_str)
    dna = build_dna_from_sku(sku)
    clients = _build_tournament_clients()

    try:
        qa_result = run_tournament(
            clients=clients,
            source_path=source_path,
            candidate_path=candidate_path,
            dna=dna,
        )
    except Exception as exc:
        log.exception("qa_tournament_fn: tournament raised")
        return {"error": f"tournament raised {type(exc).__name__}: {exc}"}

    score = float(qa_result.aggregate_score)
    synth = qa_result.synthesis_judge
    veto = bool(synth and synth.hallucination_veto)

    # F5: surface infra failures (judges with available=False)
    infra_failures: list[dict] = []
    for j in qa_result.judges:
        if not j.available:
            infra_failures.append(
                {
                    "judge": j.judge,
                    "reason": j.issues[0] if j.issues else "unknown infra failure",
                }
            )

    # Learning Loop 1 — engine winrate (always recorded)
    record_engine_outcome(
        sku=sku,
        engine=engine,
        qa_score=score,
        cost_usd=cost_so_far,
        refinement_applied=False,  # this is pre-refinement; refine_image_fn re-records post
    )

    # Learning Loop 2 — template A/B scoring
    record_template_score(template_id=template_id, sku=sku, qa_score=score, engine=engine)

    # Learning Loop 3 — failure-mode catalog (only on genuine failures)
    if score < 50:
        record_failure_mode(
            sku=sku,
            qa_score=score,
            judge_issues=qa_result.top_issues,
            suggested_fixes=qa_result.all_fixes,
            hallucination_veto=veto,
        )

    should_refine = score < 80 or veto

    tool_context.state["qa_score"] = score
    tool_context.state["qa_passed"] = qa_result.passed_98
    tool_context.state["hallucination_veto"] = veto
    tool_context.state["top_issues"] = qa_result.top_issues
    tool_context.state["all_fixes"] = qa_result.all_fixes
    tool_context.state["infra_failures"] = infra_failures
    tool_context.state["should_refine"] = should_refine

    return {
        "aggregate_score": score,
        "vision_pair_mean": qa_result.vision_pair_mean,
        "synthesis_overall": qa_result.synthesis_overall,
        "qa_passed": qa_result.passed_98,
        "hallucination_veto": veto,
        "top_issues": qa_result.top_issues[:3],
        "infra_failures": infra_failures,
        "should_refine": should_refine,
    }
