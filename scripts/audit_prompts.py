#!/usr/bin/env python3
"""Audit nano-banana prompts against real product images.

For each SKU + view combination:
  1. Build the prompt nano-banana would use (via get_prompt).
  2. Score it (full + simplified) against the actual product image.
  3. Score a hand-crafted MINIMAL prompt (garment-only) as a baseline.

Output: prompt-by-prompt comparison + recommendations for weak prompts.

Usage:
  python3 scripts/audit_prompts.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

# nano_banana imports (path injection above lets these resolve)
from nano_banana.prompts import (  # noqa: E402
    accessory_prompt,
    back_prompt,
    flux_prompt,
    front_prompt,
)

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.elite_studio.quality.clip_alignment import score_alignment  # noqa: E402
from skyyrose.elite_studio.quality.prompt_simplifier import simplify_for_clip  # noqa: E402

PRODUCTS_DIR = ROOT / "wordpress-theme/skyyrose-flagship/assets/images/products"


def _find_image_for_sku(sku: str, slug: str) -> Path | None:
    """Find a representative product image for the SKU."""
    candidates = [
        PRODUCTS_DIR / f"{slug}-front-model.webp",
        PRODUCTS_DIR / f"{slug}-front.jpg",
        PRODUCTS_DIR / f"{slug}.jpg",
        PRODUCTS_DIR / f"{slug}.webp",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _minimal_prompt(product: dict) -> str:
    """A hand-crafted minimal CLIP-friendly prompt — the baseline to beat."""
    name = product.get("name", "").lower()
    # Strip brand words manually for the minimal version.
    for term in ("skyyrose", "black rose", "love hurts", "signature edition"):
        name = name.replace(term, "").strip()
    # Pull out the garment word if it's there.
    return f"a {name} garment on a model" if name else "a garment on a model"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-md", type=Path, default=ROOT / "tasks/prompt-audit-report.md")
    parser.add_argument("--output-json", type=Path, default=ROOT / "tasks/prompt-audit-report.json")
    args = parser.parse_args()

    catalog = list(read_catalog_rows())
    print(f"Loaded {len(catalog)} catalog SKUs")

    rows: list[dict] = []
    for product in catalog:
        sku = product["sku"]
        # The image filename uses the dossier_slug or output_slug.
        slug = product.get("dossier_slug") or product.get("output_slug") or sku
        image = _find_image_for_sku(sku, slug)
        if not image:
            print(f"  skip {sku}: no image found")
            continue

        # Build prompts. accessory products use accessory_prompt.
        is_accessory = product.get("is_accessory") in ("1", "true", True)
        front = accessory_prompt(product) if is_accessory else front_prompt(product)
        back = back_prompt(product) if not is_accessory else None
        flux = flux_prompt(product["name"], "front")
        minimal = _minimal_prompt(product)

        # Score each variant.
        front_full = score_alignment(front, image)
        front_simplified = score_alignment(simplify_for_clip(front), image)
        flux_score = score_alignment(flux, image)
        minimal_score = score_alignment(minimal, image)
        back_score = score_alignment(back, image) if back else None

        row = {
            "sku": sku,
            "name": product["name"],
            "collection": product["collection"],
            "image": str(image.relative_to(ROOT)),
            "scores": {
                "front_full": round(front_full, 4),
                "front_simplified": round(front_simplified, 4),
                "flux_compact": round(flux_score, 4),
                "minimal_baseline": round(minimal_score, 4),
                "back": round(back_score, 4) if back_score is not None else None,
            },
            "prompt_lengths": {
                "front_full": len(front),
                "front_simplified": len(simplify_for_clip(front)),
                "flux_compact": len(flux),
                "minimal_baseline": len(minimal),
            },
        }
        rows.append(row)

    # Aggregate stats
    def _mean(key: str) -> float:
        vals = [r["scores"][key] for r in rows if r["scores"][key] is not None]
        return sum(vals) / len(vals) if vals else 0.0

    summary = {
        "n_skus": len(rows),
        "mean_scores": {
            "front_full": _mean("front_full"),
            "front_simplified": _mean("front_simplified"),
            "flux_compact": _mean("flux_compact"),
            "minimal_baseline": _mean("minimal_baseline"),
        },
    }
    print()
    print("=== Mean alignment per prompt template ===")
    for k, v in summary["mean_scores"].items():
        print(f"  {k:<20}  {v:.4f}")

    # Find SKUs where the minimal baseline beats the production prompt — those
    # are the ones where the prompt template is HURTING discrimination.
    underperformers = [
        r for r in rows if r["scores"]["minimal_baseline"] > r["scores"]["front_full"] + 0.02
    ]
    underperformers.sort(
        key=lambda r: r["scores"]["minimal_baseline"] - r["scores"]["front_full"],
        reverse=True,
    )

    # Markdown report
    lines: list[str] = []
    lines.append("# Prompt Audit Report")
    lines.append("")
    lines.append(f"- SKUs scored: **{len(rows)}**")
    lines.append("")
    lines.append("## Mean alignment per prompt template")
    lines.append("")
    lines.append("| template | length | mean cosine |")
    lines.append("|---------|-------:|------------:|")
    for k, v in summary["mean_scores"].items():
        avg_len = sum(r["prompt_lengths"][k] for r in rows) // max(len(rows), 1)
        lines.append(f"| `{k}` | {avg_len} chars | {v:.4f} |")
    lines.append("")
    lines.append("**Read:** lower mean cosine = template carries more signal CLIP doesn't ground.")
    lines.append(
        "If `minimal_baseline` mean is highest, the production prompts are too brand-heavy."
    )
    lines.append("")

    if underperformers:
        lines.append(f"## ⚠️  Underperforming production prompts ({len(underperformers)} SKUs)")
        lines.append("")
        lines.append(
            "Production `front_full` prompt scores at least 0.02 BELOW the minimal baseline."
        )
        lines.append("These prompts are likely hurting render quality — the renderer can't extract")
        lines.append("the core garment description through the brand language.")
        lines.append("")
        lines.append("| sku | name | full | minimal | gap |")
        lines.append("|-----|------|-----:|--------:|----:|")
        for r in underperformers[:20]:
            full = r["scores"]["front_full"]
            mn = r["scores"]["minimal_baseline"]
            lines.append(
                f"| `{r['sku']}` | {r['name']} | {full:.3f} | {mn:.3f} | +{mn - full:.3f} |"
            )
        lines.append("")

    # Per-SKU full table
    lines.append("## Per-SKU prompt alignment (sorted by full-prompt score, low first)")
    lines.append("")
    lines.append("| sku | name | full | simpl | flux | minim |")
    lines.append("|-----|------|-----:|------:|-----:|------:|")
    for r in sorted(rows, key=lambda x: x["scores"]["front_full"]):
        s = r["scores"]
        lines.append(
            f"| `{r['sku']}` | {r['name'][:40]} | "
            f"{s['front_full']:.3f} | "
            f"{s['front_simplified']:.3f} | "
            f"{s['flux_compact']:.3f} | "
            f"{s['minimal_baseline']:.3f} |"
        )
    lines.append("")

    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text("\n".join(lines))
    args.output_json.write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))
    print()
    print(f"Wrote {args.output_md.relative_to(ROOT)}")
    print(f"Wrote {args.output_json.relative_to(ROOT)}")
    print()
    print(f"  Underperformers: {len(underperformers)} SKUs (production prompt < minimal+0.02)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
