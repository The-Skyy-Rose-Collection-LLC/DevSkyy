"""Propose catalog amendments from the learning loops' history.

Produces `data/agent-learning/proposals.md` — a human-readable digest
of pending edits. The system never auto-applies; humans approve via
catalog/dossier edit + commit. This keeps the brand-canon authoring
loop in human hands while the data-gathering happens automatically.

Run weekly (or after every full-catalog run):
    python -m agents.render_pipeline.learning.proposals
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEARNING_ROOT = REPO / "data" / "agent-learning"


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def propose_engine_overrides(min_runs: int = 3, min_score: float = 80.0) -> list[dict]:
    """Loop 1 digest: per-SKU recommended engine_override.

    Rule: a SKU gets a proposed override when one engine has scored
    ≥`min_score` on ≥`min_runs` separate runs AND no other engine
    has equal or higher consistency. The system surfaces the proposal;
    the human edits the catalog CSV's `engine_override` column.

    Returns a list of {sku, proposed_engine, evidence_runs, alt_engines}
    dicts — also written to proposals.md.
    """
    proposals = []
    winrate_dir = LEARNING_ROOT / "engine-winrate"
    if not winrate_dir.exists():
        return proposals

    for jsonl_path in sorted(winrate_dir.glob("*.jsonl")):
        sku = jsonl_path.stem
        runs = _read_jsonl(jsonl_path)
        # Group successful runs by engine
        by_engine: dict[str, list[float]] = defaultdict(list)
        for r in runs:
            if r.get("qa_score", 0) >= min_score:
                by_engine[r["engine"]].append(r["qa_score"])
        # Find engine(s) with ≥min_runs successful entries
        winners = {e: s for e, s in by_engine.items() if len(s) >= min_runs}
        if not winners:
            continue
        # Pick the engine with highest median; surface alternates
        ranked = sorted(
            winners.items(),
            key=lambda kv: (sum(kv[1]) / len(kv[1]), len(kv[1])),
            reverse=True,
        )
        proposed_engine, scores = ranked[0]
        alt_engines = [e for e, _ in ranked[1:]]
        proposals.append(
            {
                "sku": sku,
                "proposed_engine": proposed_engine,
                "evidence_runs": len(scores),
                "median_score": round(sum(scores) / len(scores), 1),
                "alt_engines": alt_engines,
            }
        )
    return proposals


def digest_failure_modes(min_failures: int = 5) -> list[dict]:
    """Loop 3 digest: SKUs with persistent failure patterns.

    Returns SKUs with ≥`min_failures` recorded failure entries, plus
    the most common issue-keywords across those failures. Useful for
    surfacing "this SKU's dossier may need amendment" candidates.
    """
    digests = []
    fm_dir = LEARNING_ROOT / "failure-modes"
    if not fm_dir.exists():
        return digests

    for jsonl_path in sorted(fm_dir.glob("*.jsonl")):
        sku = jsonl_path.stem
        runs = _read_jsonl(jsonl_path)
        if len(runs) < min_failures:
            continue
        # Extract recurring issue keywords (very simple frequency count)
        keyword_counts: dict[str, int] = defaultdict(int)
        for r in runs:
            for issue in r.get("issues", []):
                # Naive: split on comma + dash, lowercase, count substrings
                for kw in issue.lower().split():
                    if len(kw) >= 5:
                        keyword_counts[kw.strip(".,;:")] += 1
        # Top 5 recurring keywords
        top_kw = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        digests.append(
            {
                "sku": sku,
                "total_failures": len(runs),
                "recurring_keywords": top_kw,
                "recent_score": runs[-1].get("qa_score"),
                "recent_veto": runs[-1].get("hallucination_veto"),
            }
        )
    return digests


def write_proposals_markdown() -> Path:
    """Render all loop digests as a single markdown report."""
    LEARNING_ROOT.mkdir(parents=True, exist_ok=True)
    out = LEARNING_ROOT / "proposals.md"
    lines = ["# RenderPipeline Learning Digest\n"]

    overrides = propose_engine_overrides()
    if overrides:
        lines.append("## Engine-override proposals (catalog amendment candidates)\n")
        lines.append("| SKU | Proposed engine | Median score | Evidence | Alt engines |")
        lines.append("|-----|-----------------|--------------|----------|-------------|")
        for p in overrides:
            alts = ", ".join(p["alt_engines"]) or "(none)"
            lines.append(
                f"| {p['sku']} | `{p['proposed_engine']}` | {p['median_score']} | "
                f"{p['evidence_runs']} runs | {alts} |"
            )
    else:
        lines.append(
            "## Engine-override proposals\n\n_No proposals yet — need ≥3 successful runs per SKU._\n"
        )

    failures = digest_failure_modes()
    if failures:
        lines.append("\n## Recurring failure modes (dossier-amendment candidates)\n")
        for f in failures:
            lines.append(f"### {f['sku']} — {f['total_failures']} failures")
            kws = ", ".join(f"`{k}` ({c})" for k, c in f["recurring_keywords"])
            lines.append(f"- Recurring keywords: {kws}")
            lines.append(f"- Recent score: {f['recent_score']} (veto={f['recent_veto']})\n")
    else:
        lines.append("\n## Recurring failure modes\n\n_No SKUs with ≥5 recorded failures._\n")

    out.write_text("\n".join(lines))
    return out


if __name__ == "__main__":
    path = write_proposals_markdown()
    print(f"Wrote {path.relative_to(REPO)}")
