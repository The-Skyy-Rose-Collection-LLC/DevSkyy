#!/usr/bin/env python3
# scripts/oai-render-qc-eval.py
"""Calibrate the imagery judge against founder labels.

Loads labeled examples (review-state.json via ImageryAdapter.load_ground_truth), runs the
Claude vision judge on each example image, compares the judge pass/fail to the human label,
and reports Cohen's kappa + the recommended mode.

Usage:
  python scripts/oai-render-qc-eval.py --images-dir renders/oai --report renders/oai/_qc-eval.json
PAID: makes one Claude vision judge call per labeled image with a resolvable render PNG.
Prints a cost estimate and requires --yes before any paid call (STOP-AND-SHOW).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evaluation.calibration import cohen_kappa, decide_mode  # noqa: E402


def kappa_from_pairs(judge: list[int], human: list[int]) -> float:
    return cohen_kappa(judge, human)


def mode_for(kappa: float) -> str:
    return decide_mode(kappa)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--images-dir", default="renders/oai")
    ap.add_argument("--report", default="renders/oai/_qc-eval.json")
    ap.add_argument("--yes", action="store_true", help="confirm paid Claude judge calls")
    args = ap.parse_args(argv)

    from evaluation.domains.imagery import ImageryAdapter
    from evaluation.judge import ClaudeJudge, make_client
    from scripts.oai_render import config
    from scripts.oai_render.qc import RenderExpectation, deterministic_checks

    adapter = ImageryAdapter()
    images_dir = Path(args.images_dir)
    labeled = adapter.load_ground_truth()
    resolvable = [g for g in labeled if (images_dir / g["subject_id"]).exists()]
    print(f"labeled={len(labeled)} resolvable_on_disk={len(resolvable)}")
    if not resolvable:
        print("No labeled images on disk — re-render a calibration subset first.")
        return 2

    est = len(resolvable) * 0.01
    print(f"STOP-AND-SHOW: {len(resolvable)} paid Claude judge calls, est ${est:.2f}")
    if not args.yes:
        print("Re-run with --yes to proceed.")
        return 2

    judge = ClaudeJudge(
        client=make_client(),
        model=config.QC_JUDGE_ANTHROPIC_MODEL,
        max_tokens=config.QC_JUDGE_ANTHROPIC_MAX_TOKENS,
    )
    judge_pass: list[int] = []
    human_pass: list[int] = []
    rows = []
    for g in resolvable:
        subject = (images_dir / g["subject_id"]).read_bytes()
        slug = g["subject_id"].split("/")[0]
        exp = RenderExpectation(
            sku=slug,
            name=slug,
            style="ghost",
            view="front",
            is_pair=False,
            is_patch=False,
            reference_paths=(),
        )
        det = deterministic_checks(subject)
        if det:
            verdict_pass = False
            cost = 0.0
        else:
            req = adapter.build_judge_request(subject, exp)
            output, cost = judge.run(messages=req["messages"], tool=req["tool"])
            verdict_pass = adapter.parse_verdict(output, det_failures=[]).passed
        judge_pass.append(int(verdict_pass))
        human_pass.append(int(g["label_pass"]))
        rows.append(
            {
                "subject_id": g["subject_id"],
                "judge_pass": verdict_pass,
                "human_pass": g["label_pass"],
                "cost_usd": cost,
            }
        )

    k = cohen_kappa(judge_pass, human_pass)
    report = {
        "n": len(rows),
        "kappa": k,
        "recommended_mode": decide_mode(k),
        "total_cost_usd": sum(r["cost_usd"] for r in rows),
        "rows": rows,
    }
    Path(args.report).write_text(json.dumps(report, indent=2))
    print(f"kappa={k:.3f} mode={decide_mode(k)} report={args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
