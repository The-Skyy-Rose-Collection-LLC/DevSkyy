#!/usr/bin/env python3
"""PIPELINE 1: Product Card & Gallery Renders.

This is the product-photography pipeline only. Output is clean garment
shots (front, back, accessory hero) that go into product cards and
gallery views on the storefront. NO models, NO scenes, NO brand voice
copy in the rendered image — that's Pipeline 2's job.

Inputs:
  - Catalog SKU (read from skyyrose-catalog.csv)
  - Source product photo (tech-flat or real product shot)

Outputs:
  - renders/gated/<sku>/<sku>-<view>-attemptN.png
  - tasks/gated-render-log.json (audit trail)

Quality gate:
  - DINOv2 brand-style centroid (image-vs-centroid cosine)
  - CLIP text-image alignment vs the GARMENT prompt block
  - Resolution sanity check (>=512px on each axis)

Three-block prompt structure (see render_prompt_builder):
  GARMENT block  = CLIP-friendly garment description (the SCORING surface)
  SCENE block    = neutral studio / clean product photography backdrop
  FIDELITY block = instruction directives (copy reference exactly)

For the lifestyle / editorial / model / Oakland-scene pipeline
see Pipeline 2: skyyrose/elite_studio/agents/compositor_agent.py
For the brand copy / marketing text pipeline
see Pipeline 3: TBD (currently scattered across orchestration/brand_*.py)

Cost-safe defaults:
  - dry-run shows the prompts + cost manifest WITHOUT calling paid APIs
  - --execute is required to actually call nano-banana; prints a STOP
    confirmation showing per-SKU and total estimated cost

Usage:
    # SAFE: see what would happen, no money spent
    python3 scripts/pipeline_product_renders.py --skus br-002,br-004,sg-013

    # GENERATE (requires explicit cost confirmation)
    python3 scripts/pipeline_product_renders.py --skus br-002 --execute --max-retries 2

    # Use the SHIP list from the existing renders report — only retry the gaps
    python3 scripts/pipeline_product_renders.py --target-needs-regen
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.elite_studio.quality.render_prompt_builder import build_render_prompt  # noqa: E402
from skyyrose.elite_studio.quality.render_quality import (  # noqa: E402
    Verdict,
    evaluate_render,
)

DEFAULT_CENTROID = ROOT / "skyyrose/elite_studio/data/brand_centroid_dino.npz"
DEFAULT_OUTPUT_DIR = ROOT / "renders/gated"

# Estimated cost per nano-banana call (informational only — confirm against
# your actual billing).
NANO_BANANA_COST_USD = 0.025


def _load_existing_report() -> dict:
    """Load the existing render-quality report (DINOv2). Used to find which
    SKUs already have ship-ready renders so we don't waste money regenerating."""
    report_path = ROOT / "tasks/render-quality-report-dino.json"
    if not report_path.exists():
        return {"by_sku": {}}
    return json.loads(report_path.read_text())


def _skus_needing_regen(report: dict) -> set[str]:
    """SKUs from the canonical catalog that have ZERO ship verdicts in the report."""
    catalog_skus = {row["sku"] for row in read_catalog_rows()}
    has_ship: set[str] = set()
    for sku, rows in report.get("by_sku", {}).items():
        if any(r.get("verdict") == "ship" for r in rows):
            has_ship.add(sku)
    return catalog_skus - has_ship


def _build_plan(skus: list[str], catalog_by_sku: dict[str, dict]) -> list[dict]:
    """Build the per-SKU prompt + cost manifest."""
    plan = []
    for sku in skus:
        product = catalog_by_sku.get(sku)
        if not product:
            print(f"  skip {sku}: not in catalog", file=sys.stderr)
            continue
        is_accessory = bool(product.get("is_accessory"))
        views = ["front"] if is_accessory else ["front", "back"]
        for view in views:
            rp = build_render_prompt(product, view=view)
            plan.append(
                {
                    "sku": sku,
                    "view": view,
                    "name": product["name"],
                    "collection": product["collection"],
                    "garment_block": rp.garment,
                    "full_prompt": rp.full,
                    "cost_estimate_usd": NANO_BANANA_COST_USD,
                }
            )
    return plan


def _print_dry_run(plan: list[dict], total_cost: float) -> None:
    print("=" * 78)
    print("DRY RUN — no API calls made, no money spent")
    print("=" * 78)
    for entry in plan:
        print(f"\n[{entry['sku']} {entry['view']}]  {entry['name']}")
        print(f"  GARMENT (scoring surface): {entry['garment_block']!r}")
        print(f"  cost if executed: ${entry['cost_estimate_usd']:.3f}")
    print()
    print(f"TOTAL: {len(plan)} renders × ${NANO_BANANA_COST_USD:.3f} = ${total_cost:.2f}")
    print()
    print("To execute:  re-run with --execute")


def _confirm_execute(plan: list[dict], total_cost: float) -> bool:
    """STOP-AND-SHOW gate per CLAUDE.md before paid API calls."""
    print("=" * 78)
    print("STOP — Confirm before proceeding:")
    print()
    print(f"  Action  : nano-banana generate × {len(plan)} renders")
    print(f"  SKUs    : {sorted({e['sku'] for e in plan})}")
    print(f"  Cost    : ~${total_cost:.2f}  ({len(plan)} × ${NANO_BANANA_COST_USD})")
    print(f"  Output  : {DEFAULT_OUTPUT_DIR.relative_to(ROOT)}")
    print("=" * 78)
    answer = input("Proceed? [y/N] ").strip().lower()
    return answer in ("y", "yes")


def _generate_and_score(entry: dict, centroid_path: Path, max_retries: int) -> dict:
    """Generate via nano-banana, score, retry on KILL up to max_retries.

    Returns a result dict. nano-banana imports are deferred so dry-run
    doesn't pay the import cost.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from nano_banana.catalog import find_back_source, load_catalog
    from nano_banana.client import get_genai_client
    from nano_banana.generate import GEMINI_PRO, generate_gemini
    from nano_banana.utils import quality_gate, save_image

    catalog = load_catalog()
    product = catalog[entry["sku"]]
    src = product.get("source_image")
    if entry["view"] == "back":
        back = find_back_source(entry["sku"], catalog)
        if back:
            src = back

    if not src:
        return {**entry, "outcome": "error", "reason": "no source image for SKU"}

    out_dir = DEFAULT_OUTPUT_DIR / entry["sku"]
    out_dir.mkdir(parents=True, exist_ok=True)

    genai = get_genai_client()
    history: list[dict] = []
    for attempt in range(1, max_retries + 1):
        out_path = out_dir / f"{entry['sku']}-{entry['view']}-attempt{attempt}.png"
        try:
            image_bytes = generate_gemini(
                genai, src, entry["full_prompt"], model=GEMINI_PRO, enhanced=(attempt > 1)
            )
        except Exception as exc:
            history.append({"attempt": attempt, "error": str(exc)})
            continue
        if not image_bytes or not quality_gate(image_bytes, entry["sku"], entry["view"]):
            history.append({"attempt": attempt, "error": "quality gate failed"})
            continue
        save_image(image_bytes, out_path)
        verdict = evaluate_render(
            render_path=out_path,
            prompt=entry["garment_block"],
            centroid_path=centroid_path,
        )
        history.append({"attempt": attempt, "path": str(out_path), **verdict.to_dict()})
        if verdict.verdict == Verdict.SHIP:
            return {
                **entry,
                "outcome": "ship",
                "winning_attempt": attempt,
                "winning_path": str(out_path),
                "verdict": verdict.to_dict(),
                "history": history,
            }

    return {**entry, "outcome": "no_ship", "history": history}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skus",
        type=str,
        help="Comma-separated SKU list. Mutually exclusive with --target-needs-regen.",
    )
    parser.add_argument(
        "--target-needs-regen",
        action="store_true",
        help="Use the existing render report to identify SKUs without a ship-ready render.",
    )
    parser.add_argument("--centroid", type=Path, default=DEFAULT_CENTROID)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--execute", action="store_true", help="Actually call paid APIs.")
    parser.add_argument("--output-log", type=Path, default=ROOT / "tasks/gated-render-log.json")
    args = parser.parse_args()

    if args.skus and args.target_needs_regen:
        parser.error("--skus and --target-needs-regen are mutually exclusive")

    catalog_by_sku = {row["sku"]: row for row in read_catalog_rows()}

    if args.target_needs_regen:
        report = _load_existing_report()
        target_skus = sorted(_skus_needing_regen(report))
        print(f"Targeting {len(target_skus)} SKUs without a ship-ready render: {target_skus}")
    elif args.skus:
        target_skus = [s.strip() for s in args.skus.split(",") if s.strip()]
    else:
        parser.error("specify --skus or --target-needs-regen")

    plan = _build_plan(target_skus, catalog_by_sku)
    total_cost = sum(e["cost_estimate_usd"] for e in plan)

    if not args.execute:
        _print_dry_run(plan, total_cost)
        return 0

    if not _confirm_execute(plan, total_cost):
        print("Aborted.")
        return 1

    results = []
    for entry in plan:
        print(f"  generating {entry['sku']} {entry['view']}...")
        results.append(_generate_and_score(entry, args.centroid, args.max_retries))

    args.output_log.parent.mkdir(parents=True, exist_ok=True)
    args.output_log.write_text(
        json.dumps(
            {
                "ts": datetime.now(UTC).isoformat(),
                "centroid": str(args.centroid.relative_to(ROOT)),
                "max_retries": args.max_retries,
                "results": results,
            },
            indent=2,
        )
    )

    ship = sum(1 for r in results if r["outcome"] == "ship")
    no_ship = sum(1 for r in results if r["outcome"] == "no_ship")
    err = sum(1 for r in results if r["outcome"] == "error")
    print()
    print(f"  ✅ SHIP   : {ship}")
    print(f"  ❌ NO_SHIP: {no_ship}")
    print(f"  ⚠️  ERROR  : {err}")
    print(f"Log: {args.output_log.relative_to(ROOT)}")
    return 0 if no_ship == 0 and err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
