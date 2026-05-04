#!/usr/bin/env python3
"""Measure the brand-centroid embedding gate against labeled render sets.

Empirical answer to the global-vs-per-collection centroid question
(see docs/adr/0002-brand-centroid-global-pending-data.md). Runs every
image under ``--good-dir`` and ``--bad-dir`` through the embedding gate
and reports false-pass / false-fail rates at the centroid's stored
threshold and across a threshold sweep.

Decision rule encoded in the report (see ADR-0002):
    false-pass < 5%   → global centroid is sufficient, keep as-is
    false-pass > 10%  → per-collection refactor is justified
    5% <= fp <= 10%   → judgment call, examine the misclassified set

Usage:
    python3 scripts/measure_brand_centroid_gate.py \\
        --good-dir tests/fixtures/known_good_renders \\
        --bad-dir  tests/fixtures/known_bad_renders \\
        --centroid skyyrose/elite_studio/data/brand_centroid.npz

    # Run both encoders for comparison:
    python3 scripts/measure_brand_centroid_gate.py \\
        --good-dir ... --bad-dir ... \\
        --centroid skyyrose/elite_studio/data/brand_centroid.npz \\
        --centroid skyyrose/elite_studio/data/brand_centroid_dino.npz

The harness is encoder-agnostic — it dispatches on the centroid's
``model_id`` to pick CLIP or DINOv2. Curate the labeled sets manually;
the harness does NOT generate test renders, only scores them.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from skyyrose.core import clip_embedder, dino_embedder
from skyyrose.elite_studio.quality.brand_centroid import (
    IMAGE_EXTS,
    BrandCentroid,
    load_centroid,
)


@dataclass
class GateResult:
    image: Path
    score: float
    accepted: bool


def _embed_for(centroid: BrandCentroid, image: Path) -> np.ndarray:
    if "dino" in centroid.model_id.lower():
        return dino_embedder.embed_image(image)
    return clip_embedder.embed_image(image)


def _score_dir(centroid: BrandCentroid, directory: Path) -> list[GateResult]:
    images = sorted(p for p in directory.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    results: list[GateResult] = []
    for img in images:
        embed = _embed_for(centroid, img)
        score = float(np.dot(embed, centroid.centroid))
        results.append(GateResult(image=img, score=score, accepted=score >= centroid.threshold))
    return results


def _summary_at_threshold(
    good: list[GateResult],
    bad: list[GateResult],
    threshold: float,
) -> dict:
    good_pass = sum(1 for r in good if r.score >= threshold)
    bad_pass = sum(1 for r in bad if r.score >= threshold)
    return {
        "threshold": round(threshold, 4),
        "good_count": len(good),
        "bad_count": len(bad),
        "good_pass_rate": round(good_pass / len(good), 4) if good else None,
        "bad_pass_rate": round(bad_pass / len(bad), 4) if bad else None,
        "false_pass_rate": round(bad_pass / len(bad), 4) if bad else None,
        "false_fail_rate": round(1 - good_pass / len(good), 4) if good else None,
    }


def _decision_from(false_pass_rate: float | None) -> str:
    if false_pass_rate is None:
        return "INDETERMINATE: no bad-set images"
    if false_pass_rate < 0.05:
        return "GLOBAL SUFFICIENT (false-pass < 5%) — keep as-is per ADR-0002"
    if false_pass_rate > 0.10:
        return "PER-COLLECTION JUSTIFIED (false-pass > 10%) — refactor warranted"
    return f"JUDGMENT CALL (false-pass {false_pass_rate:.1%}) — review misclassified set"


def _run_one_centroid(centroid_path: Path, good_dir: Path, bad_dir: Path) -> dict:
    centroid = load_centroid(centroid_path)
    print(f"\n=== {centroid_path.name} ===")
    print(f"    encoder model: {centroid.model_id}")
    print(f"    sample_count : {centroid.sample_count}")
    print(f"    threshold    : {centroid.threshold:.4f}")

    good = _score_dir(centroid, good_dir)
    bad = _score_dir(centroid, bad_dir)
    print(f"    scored {len(good)} good + {len(bad)} bad renders")

    if good:
        gscores = [r.score for r in good]
        print(
            f"    good scores  : min={min(gscores):.3f} "
            f"median={statistics.median(gscores):.3f} max={max(gscores):.3f}"
        )
    if bad:
        bscores = [r.score for r in bad]
        print(
            f"    bad scores   : min={min(bscores):.3f} "
            f"median={statistics.median(bscores):.3f} max={max(bscores):.3f}"
        )

    at_threshold = _summary_at_threshold(good, bad, centroid.threshold)
    print(f"\n    AT STORED THRESHOLD ({centroid.threshold:.4f}):")
    print(f"      good pass rate    : {at_threshold['good_pass_rate']}")
    print(f"      false-pass rate   : {at_threshold['false_pass_rate']}")
    print(f"      false-fail rate   : {at_threshold['false_fail_rate']}")
    print(f"      decision          : {_decision_from(at_threshold['false_pass_rate'])}")

    sweep = [_summary_at_threshold(good, bad, t) for t in np.arange(0.50, 0.96, 0.05)]
    print("\n    THRESHOLD SWEEP:")
    print(f"      {'thresh':>7} {'good_pass':>10} {'false_pass':>11} {'false_fail':>11}")
    for s in sweep:
        print(
            f"      {s['threshold']:>7.2f} "
            f"{(s['good_pass_rate'] or 0):>10.4f} "
            f"{(s['false_pass_rate'] or 0):>11.4f} "
            f"{(s['false_fail_rate'] or 0):>11.4f}"
        )

    return {
        "centroid_path": str(centroid_path),
        "model_id": centroid.model_id,
        "sample_count": centroid.sample_count,
        "stored_threshold": centroid.threshold,
        "at_stored_threshold": at_threshold,
        "decision": _decision_from(at_threshold["false_pass_rate"]),
        "sweep": sweep,
        "good_scores": [r.score for r in good],
        "bad_scores": [r.score for r in bad],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--good-dir", type=Path, required=True, help="Dir of known-good (on-brand) renders"
    )
    parser.add_argument(
        "--bad-dir", type=Path, required=True, help="Dir of known-bad (off-brand) renders"
    )
    parser.add_argument(
        "--centroid",
        type=Path,
        action="append",
        required=True,
        help="Path to brand_centroid*.npz (may be repeated to compare encoders)",
    )
    parser.add_argument("--json-out", type=Path, default=None, help="Write full report as JSON")
    args = parser.parse_args()

    if not args.good_dir.is_dir():
        print(f"FATAL: --good-dir not found: {args.good_dir}", file=sys.stderr)
        return 2
    if not args.bad_dir.is_dir():
        print(f"FATAL: --bad-dir not found: {args.bad_dir}", file=sys.stderr)
        return 2

    reports = [_run_one_centroid(c, args.good_dir, args.bad_dir) for c in args.centroid]

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps({"reports": reports}, indent=2) + "\n")
        print(f"\nWrote full report -> {args.json_out}")

    # Exit code reflects worst decision across encoders.
    has_perfail = any("PER-COLLECTION JUSTIFIED" in r["decision"] for r in reports)
    return 1 if has_perfail else 0


if __name__ == "__main__":
    sys.exit(main())
