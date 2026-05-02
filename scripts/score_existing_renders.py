#!/usr/bin/env python3
"""Score every render in renders/ against the brand centroid + canonical prompt.

For each (SKU, render) pair:
  1. Parse SKU from filename (br-001, sg-014-...).
  2. Look up canonical prompt from the catalog CSV (name + collection).
  3. Run RenderVerdict gate (centroid + alignment + resolution).
  4. Emit a row in the per-SKU report.

Output:
  - tasks/render-quality-report.md — human-readable, sorted, grouped by SKU.
  - tasks/render-quality-report.json — machine-readable, full numbers.

Usage:
  python3 scripts/score_existing_renders.py
  python3 scripts/score_existing_renders.py --renders-dir renders/3d
  python3 scripts/score_existing_renders.py --centroid skyyrose/elite_studio/data/brand_centroid.npz
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.elite_studio.quality.render_quality import (  # noqa: E402
    Verdict,
    evaluate_render,
)

# SKU prefix at start of filename (br-001, sg-014, lh-002, kids-001, br-001-twin).
_SKU_PATTERN = re.compile(r"^([a-z]+-[0-9]+(?:-[a-z0-9]+)?)", re.IGNORECASE)
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def _extract_sku(path: Path) -> str | None:
    """Pull a SKU out of either the filename or any parent directory.

    Catalog renders live in two layouts:
      renders/3d/sg-007-foo_preprocessed.png         (SKU in filename)
      renders/output/the-foo/sg-007-front/X.png      (SKU in parent dir)
    """
    # Try filename first.
    m = _SKU_PATTERN.match(path.name.lower())
    if m:
        return m.group(1)
    # Walk up the tree.
    for parent in path.parents:
        m = _SKU_PATTERN.match(parent.name.lower())
        if m:
            return m.group(1)
    return None


def _build_prompt(product: dict) -> str:
    """Build a canonical CLIP-scoring prompt from a catalog row."""
    name = product.get("name", "").strip()
    collection = product.get("collection", "").strip()
    # Plain English description; CLIP scores best with concrete garment language.
    return f"{name} from the {collection} collection on a model" if name else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--renders-dir",
        type=Path,
        default=ROOT / "renders",
        help="Directory tree to scan for render files",
    )
    parser.add_argument(
        "--centroid",
        type=Path,
        default=ROOT / "skyyrose/elite_studio/data/brand_centroid.npz",
        help="Brand centroid .npz file",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=ROOT / "tasks/render-quality-report.md",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "tasks/render-quality-report.json",
    )
    parser.add_argument(
        "--min-dimension",
        type=int,
        default=512,
        help="Minimum width/height for SHIP (below = KILL).",
    )
    parser.add_argument(
        "--alignment-threshold",
        type=float,
        default=0.20,
        help="Below this, verdict downgrades from SHIP to REVIEW.",
    )
    args = parser.parse_args()

    # Resolve to absolute so .relative_to(ROOT) works downstream.
    args.centroid = args.centroid.resolve()
    args.renders_dir = args.renders_dir.resolve()

    if not args.centroid.exists():
        print(f"FATAL: centroid not found: {args.centroid}", file=sys.stderr)
        print("Build it first: python3 scripts/build_brand_centroid.py", file=sys.stderr)
        return 2

    catalog = {row["sku"].lower(): row for row in read_catalog_rows()}
    print(f"Loaded {len(catalog)} catalog SKUs")

    # Collect renders
    renders: list[Path] = []
    for ext in _IMAGE_EXTS:
        renders.extend(args.renders_dir.rglob(f"*{ext}"))
    # Skip cache + quarantine
    renders = [p for p in renders if "cache" not in p.parts and "quarantine" not in p.parts]
    print(f"Found {len(renders)} render files in {args.renders_dir}")

    by_sku: dict[str, list[dict]] = defaultdict(list)
    no_sku: list[Path] = []

    for path in sorted(renders):
        sku = _extract_sku(path)
        # Strip trailing variant suffix (sg-007-front -> sg-007) when needed.
        if sku and sku not in catalog:
            base = re.match(r"([a-z]+-[0-9]+)", sku)
            if base and base.group(1) in catalog:
                sku = base.group(1)
        if not sku or sku not in catalog:
            no_sku.append(path)
            continue
        product = catalog[sku]
        prompt = _build_prompt(product)
        try:
            v = evaluate_render(
                render_path=path,
                prompt=prompt,
                centroid_path=args.centroid,
                min_dimension=args.min_dimension,
                alignment_threshold=args.alignment_threshold,
            )
        except Exception as exc:
            print(f"  ERROR scoring {path.name}: {exc}", file=sys.stderr)
            continue
        row = {
            "path": str(path.relative_to(ROOT)),
            "sku": sku,
            "name": product.get("name", ""),
            "collection": product.get("collection", ""),
            "prompt": prompt,
            **v.to_dict(),
        }
        by_sku[sku].append(row)

    # Emit JSON
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps({"by_sku": dict(by_sku), "unmatched": [str(p) for p in no_sku]}, indent=2)
    )

    # Emit markdown
    lines: list[str] = []
    lines.append("# Render Quality Report")
    lines.append("")
    lines.append(f"- Renders scanned: **{len(renders)}**")
    lines.append(f"- Renders matched to a SKU: **{sum(len(v) for v in by_sku.values())}**")
    lines.append(f"- Renders with no matching SKU: **{len(no_sku)}**")
    lines.append(f"- Centroid: `{args.centroid.relative_to(ROOT)}`")
    lines.append(
        f"- Thresholds: min-dim={args.min_dimension}px, alignment≥{args.alignment_threshold:.2f}"
    )
    lines.append("")

    # Verdict tally
    tally: dict[str, int] = {"ship": 0, "review": 0, "kill": 0}
    for rows in by_sku.values():
        for r in rows:
            tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1
    lines.append("## Verdict tally")
    lines.append("")
    lines.append(
        f"| SHIP | REVIEW | KILL |\n"
        f"|------|--------|------|\n"
        f"| {tally['ship']} | {tally['review']} | {tally['kill']} |"
    )
    lines.append("")

    # Per-SKU section
    lines.append("## Per-SKU rankings (best render at top)")
    lines.append("")
    for sku in sorted(by_sku.keys()):
        rows = sorted(by_sku[sku], key=lambda r: -r["combined_score"])
        product = catalog[sku]
        lines.append(f"### `{sku}` — {product.get('name', '')}")
        lines.append("")
        lines.append("| score | verdict | centroid | align | dims | path |")
        lines.append("|------:|---------|---------:|------:|------|------|")
        for r in rows:
            verdict_icon = {"ship": "✅", "review": "⚠️", "kill": "❌"}.get(r["verdict"], "?")
            lines.append(
                f"| {r['combined_score']:>5.1f} | {verdict_icon} {r['verdict']} | "
                f"{r['brand_centroid_score']:.3f} | {r['alignment_score']:.3f} | "
                f"{r['width']}×{r['height']} | `{r['path']}` |"
            )
        lines.append("")

    if no_sku:
        lines.append("## Unmatched files (no SKU in filename)")
        lines.append("")
        for p in no_sku[:50]:
            lines.append(f"- `{p.relative_to(ROOT)}`")
        if len(no_sku) > 50:
            lines.append(f"- ... and {len(no_sku) - 50} more")

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines))

    print()
    print(f"Wrote {args.output_md}")
    print(f"Wrote {args.output_json}")
    print()
    print(f"  ✅ SHIP   : {tally['ship']:>4}")
    print(f"  ⚠️  REVIEW : {tally['review']:>4}")
    print(f"  ❌ KILL   : {tally['kill']:>4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
