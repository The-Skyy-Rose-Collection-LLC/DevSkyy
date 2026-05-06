"""Append-only structured recorders for the three learning loops.

Each `record_*` function appends a single JSONL line to the relevant
log under `data/agent-learning/`. Append-only means: never edit, never
delete, never overwrite. The history IS the knowledge. Bad runs are
just as valuable as good runs — they tell us what to fix.

Called from the agent's tools at QA-tournament boundaries. Cheap (one
JSONL append per call) and side-effect-only (returns None).
"""

from __future__ import annotations

import json
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LEARNING_ROOT = REPO / "data" / "agent-learning"


def _append_jsonl(path: Path, payload: dict) -> None:
    """Append a single JSON object as one line. Creates parent dirs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": int(time.time()), **payload}
    with path.open("a") as f:
        f.write(json.dumps(payload) + "\n")


def record_engine_outcome(
    sku: str,
    engine: str,
    qa_score: float,
    vision_keywords: list[str] | None = None,
    refinement_applied: bool = False,
    cost_usd: float = 0.0,
) -> None:
    """Loop 1 — engine-routing winrate.

    Recorded after every QA tournament. Over time, builds a per-SKU
    history that informs `propose_engine_overrides`.
    """
    _append_jsonl(
        LEARNING_ROOT / "engine-winrate" / f"{sku}.jsonl",
        {
            "engine": engine,
            "qa_score": qa_score,
            "vision_keywords": vision_keywords or [],
            "refinement_applied": refinement_applied,
            "cost_usd": cost_usd,
        },
    )


def record_template_score(
    template_id: str,
    sku: str,
    qa_score: float,
    engine: str,
) -> None:
    """Loop 2 — prompt-template A/B scoring.

    Mirror of PromptRegistry.record_score but persisted to disk so
    learning survives across processes. Registry's in-memory avg_score
    is fine for in-process A/B; this log enables cross-session digests.
    """
    _append_jsonl(
        LEARNING_ROOT / "template-scores" / f"{template_id}.jsonl",
        {"sku": sku, "qa_score": qa_score, "engine": engine},
    )


def record_failure_mode(
    sku: str,
    qa_score: float,
    judge_issues: list[str],
    suggested_fixes: list[str],
    hallucination_veto: bool = False,
) -> None:
    """Loop 3 — failure-mode catalog.

    Only records SKUs scoring <50. The system isn't interested in
    "passed cleanly" — it's interested in "what went wrong, again,
    on this SKU?" After ≥5 failure entries on the same SKU, the log
    becomes a structured signal for dossier amendments.
    """
    if qa_score >= 50:
        return  # only record genuine failures
    _append_jsonl(
        LEARNING_ROOT / "failure-modes" / f"{sku}.jsonl",
        {
            "qa_score": qa_score,
            "issues": judge_issues[:5],
            "suggested_fixes": suggested_fixes[:5],
            "hallucination_veto": hallucination_veto,
        },
    )
