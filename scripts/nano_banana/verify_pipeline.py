"""Verified Generation Pipeline — full end-to-end orchestration.

Runs the complete pipeline for a single SKU+view:
  1. Load DNA (from data/product-dna/{sku}.json)
  2. Build deterministic prompt
  3. Generate N candidates (Phase 3)
  4. Run quantitative metrics (Phase 4a)
  5. Run 3-judge tournament (Phase 4b)
  6. Pick winner; if aggregate < 98%, build feedback prompt + regenerate (max 3 cycles)
  7. Save winner to production directory + log results
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "verify-results"
MAX_REGEN_CYCLES = 3
CANDIDATES_PER_CYCLE = 3
PASSING_THRESHOLD = 92.0  # Tournament aggregate score threshold (start realistic, tune up)


@dataclass
class VerifyResult:
    """Result of verified generation for one SKU/view."""
    sku: str
    view: str
    cycles_run: int
    winner_path: str
    winner_score: float
    passed_98: bool
    all_scores: list
    total_candidates: int


def load_clients():
    """Load all vision + generation clients."""
    from nano_banana.client import get_genai_client, get_openai_client
    import os
    # Read .env.hf keys
    env_path = PROJECT_ROOT / ".env.hf"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    clients = {
        "gemini": get_genai_client(),
        "openai": get_openai_client(),
    }
    try:
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if key:
            clients["anthropic"] = anthropic.Anthropic(api_key=key)
    except ImportError:
        pass

    return clients


def verify_generate(
    sku: str,
    view: str,
    source_path: Path,
    collection: str = "black-rose",
    max_cycles: int = MAX_REGEN_CYCLES,
    n_candidates: int = CANDIDATES_PER_CYCLE,
    passing_threshold: float = PASSING_THRESHOLD,
) -> VerifyResult:
    """Run the full verified generation pipeline for one SKU/view."""
    from nano_banana.dna_prompts import load_dna, build_prompt_from_dna, build_feedback_prompt
    from nano_banana.candidates import generate_candidates, save_candidate_manifest
    from nano_banana.tournament import run_tournament, pick_winner

    # Load DNA
    dna = load_dna(sku)
    if not dna:
        raise ValueError(f"No DNA found for SKU {sku} — run product_dna_extract.py first")

    # Initialize clients
    clients = load_clients()
    if not clients.get("gemini"):
        raise RuntimeError("Gemini client required for generation")

    # Build initial prompt
    base_prompt = build_prompt_from_dna(dna, view=view, collection=collection)
    current_prompt = base_prompt

    all_candidates = []
    all_tournament_results = []
    best_result = None
    cycles_run = 0

    for cycle in range(1, max_cycles + 1):
        cycles_run = cycle
        log.info("=" * 60)
        log.info("CYCLE %d/%d — %s %s", cycle, max_cycles, sku, view)
        log.info("=" * 60)

        # Generate candidates
        feedback_applied = cycle > 1
        candidates = generate_candidates(
            clients, sku, view, source_path, current_prompt,
            n=n_candidates, attempt=cycle, feedback_applied=feedback_applied,
        )
        save_candidate_manifest(sku, view, candidates)
        all_candidates.extend(candidates)

        if not candidates:
            log.warning("No candidates generated in cycle %d", cycle)
            continue

        # Tournament: judge each candidate
        cycle_results = []
        for i, cand in enumerate(candidates):
            log.info("Judging candidate %d/%d...", i+1, len(candidates))
            result = run_tournament(clients, source_path, PROJECT_ROOT / cand.path, dna, passing_threshold=98.0)
            cycle_results.append(result)
            all_tournament_results.append(result)
            log.info("  aggregate=%.1f (%s)", result.aggregate_score, "PASS" if result.passed_98 else "fail")

        # Pick cycle winner
        cycle_winner = pick_winner(cycle_results)
        if cycle_winner is None:
            continue

        # Update best overall
        if best_result is None or cycle_winner.aggregate_score > best_result.aggregate_score:
            best_result = cycle_winner

        log.info("Cycle %d winner: %.1f — %s", cycle, cycle_winner.aggregate_score, cycle_winner.candidate_path)

        # Check if we've passed threshold
        if best_result.aggregate_score >= passing_threshold:
            log.info("THRESHOLD %s REACHED — stopping early", passing_threshold)
            break

        # Build feedback prompt for next cycle
        if cycle < max_cycles:
            log.info("Top issues: %s", cycle_winner.top_issues[:3])
            log.info("Suggested fixes: %s", cycle_winner.all_fixes[:3])
            feedback_metrics = {"issues": {"list": cycle_winner.top_issues, "fixes": cycle_winner.all_fixes}}
            current_prompt = base_prompt + _format_feedback(cycle_winner)

    # If all cycles failed on text/logos, try composite fallback
    if best_result and not best_result.passed_98:
        from nano_banana.composite_fallback import should_use_composite_fallback, hybrid_composite_from_dna
        if should_use_composite_fallback(best_result) and clients.get("anthropic"):
            log.info("Triggering hybrid composite fallback (text/logo scores low)")
            try:
                composite_path = hybrid_composite_from_dna(
                    base_image_path=PROJECT_ROOT / best_result.candidate_path,
                    source_image_path=source_path,
                    dna=dna,
                    anthropic_client=clients["anthropic"],
                )
                if composite_path:
                    # Re-judge composite
                    composite_result = run_tournament(
                        clients, source_path, composite_path, dna, passing_threshold=98.0
                    )
                    log.info("Composite fallback score: %.1f", composite_result.aggregate_score)
                    if composite_result.aggregate_score > best_result.aggregate_score:
                        best_result = composite_result
                        all_tournament_results.append(composite_result)
            except Exception as exc:
                log.error("Composite fallback failed: %s", exc)

    # Summary
    passed_98 = best_result and best_result.aggregate_score >= 98.0

    return VerifyResult(
        sku=sku,
        view=view,
        cycles_run=cycles_run,
        winner_path=best_result.candidate_path if best_result else "",
        winner_score=best_result.aggregate_score if best_result else 0.0,
        passed_98=passed_98,
        all_scores=[r.aggregate_score for r in all_tournament_results],
        total_candidates=len(all_candidates),
    )


def _format_feedback(result) -> str:
    """Format tournament feedback into prompt addendum."""
    lines = ["\n\nTARGETED CORRECTIONS from previous attempt:"]
    if result.top_issues:
        lines.append("Issues to fix:")
        for issue in result.top_issues[:5]:
            lines.append(f"  - {issue}")
    if result.all_fixes:
        lines.append("Specific fixes to apply:")
        for fix in result.all_fixes[:5]:
            lines.append(f"  - {fix}")
    return "\n".join(lines)


def save_verify_result(result: VerifyResult) -> Path:
    """Save verify result to data/verify-results/."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"{result.sku}_{result.view}_{ts}.json"
    out_path.write_text(json.dumps({
        "sku": result.sku,
        "view": result.view,
        "cycles_run": result.cycles_run,
        "winner_path": result.winner_path,
        "winner_score": result.winner_score,
        "passed_98": result.passed_98,
        "all_scores": result.all_scores,
        "total_candidates": result.total_candidates,
        "completed_at": datetime.now().isoformat(),
    }, indent=2) + "\n")
    return out_path


def promote_winner_to_production(result: VerifyResult, output_slug: str) -> Path | None:
    """Copy the winning candidate to the production products directory."""
    if not result.winner_path:
        return None
    from nano_banana.utils import get_output_filename
    from nano_banana.catalog import PRODUCTS_DIR
    import shutil

    winner = PROJECT_ROOT / result.winner_path
    if not winner.exists():
        log.error("Winner not found: %s", winner)
        return None

    filename = get_output_filename(result.sku, result.view, output_slug)
    dest = PRODUCTS_DIR / filename
    shutil.copy2(winner, dest)
    log.info("Promoted to production: %s", dest.relative_to(PROJECT_ROOT))
    return dest
