#!/usr/bin/env python3
"""Ground-truth evaluation harness for the QC judge.

The QC vision judge gates real money: a wrong verdict either discards a good
$0.40 render or ships a defective product card. This harness scores the judge
against a small Fable-audited ground-truth set (``tests/fixtures/qc_ground_truth``)
so a judge regression is caught for cents, BEFORE a paid batch — not discovered
by burning a batch and hand-auditing the output.

Each labeled render carries an ``expect`` verdict (PASS/FAIL) and a
``confidence``. ``pending_colorway`` items hinge on an unresolved colorway
ground-truth question and are reported separately so they never silently inflate
or deflate the headline accuracy.

Usage::

    python scripts/oai-render-qc-eval.py            # score the configured judge
    python scripts/oai-render-qc-eval.py --json      # machine-readable result

Running this makes one judge API call per labeled render (~$0.01 each). It does
NOT generate images. Import ``run_eval`` to score an alternative judge gate (e.g.
a future Claude adapter) without the CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from . import pipeline
from .references import build_dossier_index, load_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]  # scripts/oai_render/qc_eval.py -> repo root
LABELS_PATH = REPO_ROOT / "tests" / "fixtures" / "qc_ground_truth" / "labels.json"


@dataclass(frozen=True)
class EvalItem:
    sku: str
    render: Path
    expect: str  # "PASS" | "FAIL"
    confidence: str  # "high" | "pending_colorway" | ...
    fable_reason: str


@dataclass(frozen=True)
class EvalResult:
    sku: str
    expect: str
    got: str
    confidence: str
    matched: bool
    tags: tuple[str, ...]
    reason: str
    analysis: str = ""  # judge's forced visual_analysis (auditable reasoning)


def load_labels(path: Path = LABELS_PATH) -> list[EvalItem]:
    """Load the labeled ground-truth set. Raises if the file is missing/corrupt.

    Render paths in ``labels.json`` are repo-relative and resolve against
    :data:`REPO_ROOT`, independent of where the labels file itself lives.
    """
    doc = json.loads(path.read_text(encoding="utf-8"))
    items: list[EvalItem] = []
    for row in doc.get("labels", []):
        render = REPO_ROOT / row["render"]
        if not render.exists():
            raise FileNotFoundError(f"ground-truth render missing: {render}")
        items.append(
            EvalItem(
                sku=row["sku"],
                render=render,
                expect=row["expect"].upper(),
                confidence=row.get("confidence", "high"),
                fable_reason=row.get("fable_reason", ""),
            )
        )
    if not items:
        raise ValueError(f"no labels found in {path}")
    return items


def run_eval(gate=None, *, items: list[EvalItem] | None = None) -> list[EvalResult]:
    """Score a QC gate against the ground-truth set.

    Args:
        gate: a ``QCGate`` (or compatible ``.check(bytes, expectation)``). Built
            from config when omitted, so this scores the currently-configured judge.
        items: labeled set; loaded from disk when omitted.

    Returns one :class:`EvalResult` per labeled render. Makes one judge call each.
    """
    if items is None:
        items = load_labels()
    if gate is None:
        from .qc import QCGate

        gate = QCGate()
    catalog = load_catalog()
    dossier_index = build_dossier_index()

    results: list[EvalResult] = []
    for item in items:
        plan = pipeline.plan_sku(item.sku, catalog, dossier_index, style="ghost", view="front")
        expectation = pipeline.expectation_for(plan)
        verdict = gate.check(item.render.read_bytes(), expectation)
        got = "PASS" if verdict.passed else "FAIL"
        results.append(
            EvalResult(
                sku=item.sku,
                expect=item.expect,
                got=got,
                confidence=item.confidence,
                matched=(got == item.expect),
                tags=tuple(verdict.failure_tags),
                reason=verdict.reason,
                analysis=getattr(verdict, "analysis", ""),
            )
        )
    return results


def summarize(results: list[EvalResult]) -> dict:
    """Headline accuracy over high-confidence items; pending items reported apart."""
    high = [r for r in results if r.confidence == "high"]
    pending = [r for r in results if r.confidence != "high"]
    high_ok = sum(r.matched for r in high)
    return {
        "high_confidence_matched": high_ok,
        "high_confidence_total": len(high),
        "high_confidence_accuracy": (high_ok / len(high)) if high else None,
        "pending_matched": sum(r.matched for r in pending),
        "pending_total": len(pending),
        "passing": bool(high) and high_ok == len(high),
    }


def _format(results: list[EvalResult], summary: dict) -> str:
    lines = ["sku      expect  got   match  confidence        tags"]
    for r in sorted(results, key=lambda x: (x.confidence != "high", x.sku)):
        mark = "OK " if r.matched else "XX "
        lines.append(f"{r.sku:8} {r.expect:6} {r.got:5} {mark:5}  {r.confidence:16} {list(r.tags)}")
        if not r.matched:
            lines.append(f"         -> {r.reason[:120]}")
            if r.analysis:  # the judge's eyes — what it claims it saw before misranking
                lines.append(f"         analysis: {r.analysis[:400]}")
    acc = summary["high_confidence_accuracy"]
    acc_s = f"{acc:.0%}" if acc is not None else "n/a"
    lines.append("")
    lines.append(
        f"high-confidence accuracy: {summary['high_confidence_matched']}/"
        f"{summary['high_confidence_total']} ({acc_s})  "
        f"| pending-colorway: {summary['pending_matched']}/{summary['pending_total']}"
    )
    lines.append("VERDICT: " + ("JUDGE FIT ✓" if summary["passing"] else "JUDGE UNFIT ✗"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="qc-eval", description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)

    results = run_eval()
    summary = summarize(results)
    if args.json:
        print(
            json.dumps(
                {"results": [r.__dict__ for r in results], "summary": summary},
                indent=2,
                default=list,
            )
        )
    else:
        print(_format(results, summary))
    # Exit non-zero when the judge misranks any high-confidence item — usable as a
    # CI/pre-batch gate.
    return 0 if summary["passing"] else 1


if __name__ == "__main__":
    sys.exit(main())
