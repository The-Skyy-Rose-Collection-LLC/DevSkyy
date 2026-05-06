"""Per-SKU generator-prompt dumper — diagnostic, NO paid calls.

For each SKU in the catalog (or a filtered subset), reconstructs the
exact generator prompt the production pipeline would send to the
image model. Shows three layers separately so the user can see what
each layer contributes:

  Layer 0: registry-built prompt (from inferred Gemini-vision DNA)
  Layer 3: canonical-positive prefix (garment_type_lock + branding_block)
  Layer 2: canonical-negative suffix (DO NOT RENDER block)

Output: a long markdown report at `tasks/per-sku-prompts-{ts}.md` plus
a summary table to stdout. Useful for verifying that the pipeline is
sending the right things to the generator BEFORE spending money on a
paid validator run.

Usage:
    python scripts/nano_banana/_dump_per_sku_prompts.py
    python scripts/nano_banana/_dump_per_sku_prompts.py --skus br-001,lh-004
    python scripts/nano_banana/_dump_per_sku_prompts.py --collection signature
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from nano_banana.catalog import load_catalog  # noqa: E402
from nano_banana.prompt_registry import PromptRegistry  # noqa: E402
from nano_banana.router import route_product  # noqa: E402
from nano_banana.spec_builder import (  # noqa: E402
    augment_prompt_with_dossier_negatives,
    augment_prompt_with_dossier_positives,
    build_dna_from_sku,
)
from nano_banana.vision_context import VisionContext  # noqa: E402


def _load_vision_cache(sku: str) -> dict:
    """Load Gemini-vision cache if present, else empty dict."""
    cache_path = REPO / "data/product-vision" / f"{sku}-vision.json"
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _build_prompt_for_sku(sku: str, product: dict, view: str = "front") -> dict:
    """Reconstruct what pipeline.run_single would send the generator.

    Returns a dict with structured intermediate state:
      vision_cache: inferred Gemini-vision DNA (may be empty)
      canonical_loaded: bool — did build_dna_from_sku succeed
      route_decision: top-1 RouteDecision (engine + reason)
      registry_template_id: which A/B template fired
      layer0_prompt: registry output (no augmentation)
      layer3_prompt: layer0 + canonical positives prepended
      final_prompt: layer3 + canonical negatives appended (production output)
      layer3_added_chars: how many chars Layer 3 contributed
      layer2_added_chars: how many chars Layer 2 contributed
    """
    # 1. Vision cache (Gemini-vision describing the on-disk image)
    inferred = _load_vision_cache(sku)
    catalog_fields = {k: v for k, v in product.items() if k != "_dossier"}
    ctx = VisionContext(inferred=inferred, catalog=catalog_fields)

    # 2. Try canonical dossier merge (production path)
    try:
        canonical = build_dna_from_sku(sku)
        ctx.spec = canonical.spec
        ctx.dossier = canonical.dossier
        canonical_loaded = True
    except Exception as exc:
        canonical_loaded = False
        canonical_err = f"{type(exc).__name__}: {exc}"
        return {
            "sku": sku,
            "canonical_loaded": False,
            "canonical_error": canonical_err,
            "vision_cache_present": bool(inferred),
            "final_prompt": None,
        }

    # 3. Routing decision
    decisions = route_product(product, ctx, view)
    if not decisions:
        return {
            "sku": sku,
            "canonical_loaded": True,
            "route_failure": "no decisions returned",
            "final_prompt": None,
        }
    decision = decisions[0]

    # 4. Registry prompt (Layer 0)
    registry = PromptRegistry.load()
    layer0_prompt, template_id = registry.get_prompt(ctx, product, view, decision.engine)

    # 5. Layer 3 (positives prepend)
    layer3_prompt = augment_prompt_with_dossier_positives(layer0_prompt, ctx)

    # 6. Layer 2 (negatives append) — production final
    final_prompt = augment_prompt_with_dossier_negatives(layer3_prompt, ctx)

    return {
        "sku": sku,
        "canonical_loaded": canonical_loaded,
        "vision_cache_present": bool(inferred),
        "route": {
            "engine": decision.engine,
            "model_id": decision.model_id,
            "reason": decision.reason,
            "estimated_cost": decision.estimated_cost,
        },
        "registry_template_id": template_id,
        "inferred_summary": _summarize_inferred(inferred),
        "layer0_prompt": layer0_prompt,
        "layer3_prompt": layer3_prompt,
        "final_prompt": final_prompt,
        "layer0_chars": len(layer0_prompt),
        "layer3_added_chars": len(layer3_prompt) - len(layer0_prompt),
        "layer2_added_chars": len(final_prompt) - len(layer3_prompt),
        "final_chars": len(final_prompt),
    }


def _summarize_inferred(inferred: dict) -> str:
    """Compact one-paragraph summary of inferred DNA fields."""
    if not inferred:
        return "(no vision cache — generator prompt would lack inferred DNA detail)"
    lines = []
    if inferred.get("garment_type"):
        lines.append(f"garment={inferred['garment_type']}")
    if inferred.get("fabric_appearance"):
        lines.append(f"fabric={inferred['fabric_appearance'][:80]}")
    gfx = inferred.get("graphics", [])
    if gfx:
        g = gfx[0]
        lines.append(f"graphic-type={g.get('type', '')!r}")
        lines.append(f"graphic-colors={g.get('colors', [])[:5]}")
    branding = inferred.get("branding", {})
    if branding.get("logo_technique"):
        lines.append(f"branding-technique={branding['logo_technique']!r}")
    return " | ".join(lines)


def _emit_markdown(results: list[dict], out_path: Path) -> None:
    """Write a long markdown report with full per-SKU prompts."""
    with out_path.open("w") as f:
        f.write("# Per-SKU Generator Prompts\n\n")
        f.write(f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total SKUs:** {len(results)}\n")
        loaded = sum(1 for r in results if r.get("canonical_loaded"))
        f.write(f"**Canonical dossier loaded:** {loaded}/{len(results)}\n")
        cached = sum(1 for r in results if r.get("vision_cache_present"))
        f.write(f"**Vision cache present:** {cached}/{len(results)}\n\n")
        f.write("---\n\n")

        for r in results:
            f.write(f"## {r['sku']}\n\n")
            if not r.get("canonical_loaded"):
                f.write(
                    f"⚠ **Canonical dossier failed to load:** `{r.get('canonical_error', '?')}`\n\n"
                )
                f.write("---\n\n")
                continue
            if r.get("route_failure"):
                f.write(f"⚠ **Route failure:** {r['route_failure']}\n\n---\n\n")
                continue

            f.write(f"**Vision cache:** {'present' if r['vision_cache_present'] else 'MISSING'}\n")
            f.write(f"**Inferred DNA:** {r['inferred_summary']}\n")
            f.write(
                f"**Engine route:** `{r['route']['engine']}` ({r['route']['model_id']}) — {r['route']['reason']}\n"
            )
            f.write(f"**Registry template:** `{r['registry_template_id']}`\n")
            f.write(
                f"**Prompt length:** Layer-0={r['layer0_chars']}c → +Layer-3={r['layer3_added_chars']}c "
                f"→ +Layer-2={r['layer2_added_chars']}c → final={r['final_chars']}c\n\n"
            )

            f.write("### Final prompt sent to generator\n\n")
            f.write("```\n")
            f.write(r["final_prompt"])
            f.write("\n```\n\n")

            f.write("---\n\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--skus", type=str, default="all", help="Comma-separated SKUs or 'all'")
    parser.add_argument("--collection", type=str, default="", help="Filter by collection")
    parser.add_argument(
        "--out",
        type=str,
        default="",
        help="Output markdown path (default: tasks/per-sku-prompts-{ts}.md)",
    )
    args = parser.parse_args()

    catalog = load_catalog()
    if args.skus.strip().lower() == "all":
        skus = sorted(
            sku
            for sku, row in catalog.items()
            if not args.collection or row.get("collection", "") == args.collection
        )
    else:
        skus = [s.strip() for s in args.skus.split(",") if s.strip()]

    results = []
    for sku in skus:
        row = catalog.get(sku, {})
        product = {
            "sku": sku,
            "name": row.get("name", sku),
            "collection": row.get("collection", ""),
            **row,
        }
        result = _build_prompt_for_sku(sku, product, view="front")
        results.append(result)
        # Compact stdout per-SKU summary
        if result.get("canonical_loaded") and result.get("final_prompt"):
            print(
                f"{sku:<14} {row.get('collection', ''):<14} "
                f"vision={'Y' if result['vision_cache_present'] else 'N'}  "
                f"L0={result['layer0_chars']}c  +L3={result['layer3_added_chars']}c  "
                f"+L2={result['layer2_added_chars']}c  final={result['final_chars']}c  "
                f"engine={result['route']['engine']}"
            )
        else:
            print(
                f"{sku:<14} ⚠ {result.get('canonical_error') or result.get('route_failure', '?')}"
            )

    out_path = (
        Path(args.out) if args.out else REPO / "tasks" / f"per-sku-prompts-{int(time.time())}.md"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _emit_markdown(results, out_path)
    print(f"\nFull report: {out_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
