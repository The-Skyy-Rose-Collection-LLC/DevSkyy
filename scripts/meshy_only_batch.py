#!/usr/bin/env python3
"""Meshy-only 3D batch — canonical-catalog-sourced image->3D meshes.

Path 1 (founder-chosen 2026-05-30): generate ONLY the Meshy .glb per SKU from the
canonical catalog source image. No FLUX synthesis (that's the stage that fails QC on
detailed garments). The mesh is textured from the real product photo -> faithful.

Sources resolve through the canonical catalog CSV (per the canonical-sources rule).
Output: renders/3d/<sku>.glb  (skips SKUs that already have a mesh).

Usage:
    python scripts/meshy_only_batch.py --limit 1            # test one (cheapest SKU first)
    python scripts/meshy_only_batch.py --skus br-007        # a specific SKU
    python scripts/meshy_only_batch.py                      # all remaining (skip-existing)
    python scripts/meshy_only_batch.py --dry-run            # preview, no spend
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load both env files; MESHY_API_KEY lives in .env.hf.
load_dotenv(PROJECT_ROOT / ".env.hf")
load_dotenv(PROJECT_ROOT / ".env")

THEME = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship"
CATALOG = THEME / "data" / "skyyrose-catalog.csv"
PRODUCTS = THEME / "assets" / "images" / "products"
OUT_DIR = PROJECT_ROOT / "renders" / "3d"

EST_COST_PER_SKU_USD = 0.50  # Meshy image-to-3D estimate (matches br-006 observed)


def _existing_skus() -> set[str]:
    """SKUs that already have a top-level renders/3d/<sku>.glb."""
    found: set[str] = set()
    for p in OUT_DIR.glob("*.glb"):
        stem = p.stem
        for prefix in ("br-", "lh-", "sg-", "kids-"):
            if stem.startswith(prefix):
                # normalise br-006-sherpa-jacket_meshy -> br-006
                parts = stem.split("-")
                if prefix == "kids-":
                    found.add(f"kids-{parts[1].split('_')[0]}")
                else:
                    found.add(f"{parts[0]}-{parts[1].split('_')[0]}")
    return found


def _resolve_targets(args: argparse.Namespace) -> list[dict]:
    rows = list(csv.DictReader(open(CATALOG)))
    have = _existing_skus()
    if args.skus:
        want = {s.strip() for s in args.skus.split(",")}
        rows = [r for r in rows if r["sku"] in want]
    else:
        rows = [r for r in rows if r["sku"] not in have]
    targets = []
    for r in rows:
        # catalog `image` is already relative to the theme root
        # (e.g. "assets/images/products/br-007.jpg").
        src = THEME / r["image"]
        targets.append({"sku": r["sku"], "name": r["name"], "src": src, "src_ok": src.exists()})
    if args.limit > 0:
        targets = targets[: args.limit]
    return targets


async def _generate_one(client, t: dict) -> dict:
    from ai_3d.providers.meshy import MeshyArtStyle

    sku = t["sku"]
    try:
        result = await client.generate_from_image(
            image_path=str(t["src"]),
            output_dir=str(OUT_DIR),
            output_format="glb",
            art_style=MeshyArtStyle.REALISTIC,
            target_polycount=30000,
        )
        model_path = result.get("model_path") if isinstance(result, dict) else None
        if model_path and Path(model_path).exists():
            final = OUT_DIR / f"{sku}.glb"
            shutil.copyfile(model_path, final)
            size_mb = final.stat().st_size / (1024 * 1024)
            return {"sku": sku, "ok": True, "path": str(final), "size_mb": round(size_mb, 1)}
        return {"sku": sku, "ok": False, "error": "no model_path in result"}
    except Exception as exc:  # noqa: BLE001 — per-SKU isolation, never abort the batch
        return {"sku": sku, "ok": False, "error": str(exc)}


async def _run(args: argparse.Namespace) -> int:
    targets = _resolve_targets(args)
    missing_src = [t["sku"] for t in targets if not t["src_ok"]]
    runnable = [t for t in targets if t["src_ok"]]

    print(
        f"Meshy-only 3D batch — {len(runnable)} SKU(s) to generate "
        f"(est ${len(runnable) * EST_COST_PER_SKU_USD:.2f}); "
        f"{len(missing_src)} skipped (missing source)."
    )
    for t in runnable:
        print(f"  {t['sku']:9} <- {t['src'].name}")
    if missing_src:
        print(f"  MISSING SOURCE (skipped): {missing_src}")

    if args.dry_run:
        print("[DRY RUN] no spend.")
        return 0

    if len(runnable) * EST_COST_PER_SKU_USD > args.max_cost:
        print(
            f"ABORT: est ${len(runnable) * EST_COST_PER_SKU_USD:.2f} exceeds "
            f"--max-cost ${args.max_cost:.2f}. Narrow with --limit/--skus or raise the cap."
        )
        return 2

    from ai_3d.providers.meshy import MeshyClient

    results = []
    async with MeshyClient() as client:
        for i, t in enumerate(runnable):
            print(f"[{i + 1}/{len(runnable)}] {t['sku']} generating...", flush=True)
            res = await _generate_one(client, t)
            results.append(res)
            print(
                f"    {'OK ' + str(res.get('size_mb')) + 'MB' if res['ok'] else 'FAIL: ' + res.get('error', '')}"
            )
            if i < len(runnable) - 1:
                await asyncio.sleep(8)  # 429 avoidance

    ok = [r for r in results if r["ok"]]
    fail = [r for r in results if not r["ok"]]
    print(
        f"\nDONE: {len(ok)} ok, {len(fail)} failed. "
        f"Est spend ~${len(ok) * EST_COST_PER_SKU_USD:.2f}."
    )
    if fail:
        print("FAILED:", [(r["sku"], r.get("error", "")[:60]) for r in fail])
    return 0 if not fail else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--limit", type=int, default=0, help="Cap number of SKUs (0=all)")
    parser.add_argument("--skus", default="", help="Comma-separated SKUs (overrides skip-existing)")
    parser.add_argument("--dry-run", action="store_true", help="Preview, no spend")
    parser.add_argument("--max-cost", type=float, default=20.0, help="Hard cost ceiling (USD)")
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
