"""
Tripo multiview dispatch — STOP-AND-SHOW gated SKU imagery generation.

Probes balance, shows a manifest (SKUs, source images, cost), and waits for
explicit "y" before dispatching any paid Tripo generate_multiview_image API
calls via the Elite Studio creative hub.

Outputs land in renders/output/tripo/<sku>/ — NOT the WordPress theme.
A second manual SFTP copy step (with its own confirmation) moves approved
images into wordpress-theme/skyyrose-flagship/assets/images/products/.

Usage:
    # Priority SKUs only (those missing both front_model_image + back_model_image)
    python scripts/tripo_dispatch.py

    # All 33 published SKUs
    python scripts/tripo_dispatch.py --all

    # Single SKU (useful for testing; defaults to dry-run)
    python scripts/tripo_dispatch.py --sku br-001
    python scripts/tripo_dispatch.py --sku br-001 --execute
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_CSV = REPO_ROOT / "wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"
THEME_ROOT = REPO_ROOT / "wordpress-theme/skyyrose-flagship"
OUTPUT_DIR = REPO_ROOT / "renders/output/tripo"
CREDITS_PER_SKU = 10  # flux.1_kontext_pro + generate_multiview_image template


def load_catalog() -> list[dict[str, str]]:
    with CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def resolve_source_image(row: dict[str, str]) -> Path:
    override = row.get("render_source_override", "").strip()
    if override and "/" not in override:
        return THEME_ROOT / "assets/images/products" / override
    if override:
        return THEME_ROOT / override
    return THEME_ROOT / row.get("image", "")


def _image_exists(row: dict[str, str], field: str) -> bool:
    val = row.get(field, "").strip()
    if not val:
        return False
    candidate = THEME_ROOT / val
    return candidate.exists()


def select_skus(
    rows: list[dict[str, str]],
    all_published: bool,
    single_sku: str | None,
) -> list[dict[str, str]]:
    published = [r for r in rows if r.get("published", "0").strip() == "1"]

    if single_sku:
        matched = [r for r in published if r["sku"] == single_sku]
        if not matched:
            sys.exit(f"SKU {single_sku!r} not found or not published in catalog.")
        return matched

    if all_published:
        return published

    # Default: priority set — SKUs that have a resolvable source image but
    # are missing at least one model image (most need Tripo the most).
    priority = []
    for r in published:
        has_source = resolve_source_image(r).exists()
        missing_front = not _image_exists(r, "front_model_image")
        missing_back = not _image_exists(r, "back_model_image")
        if has_source and (missing_front or missing_back):
            priority.append(r)
    return priority


async def _probe_balance() -> int:
    try:
        from tripo3d import TripoClient

        async with TripoClient() as client:
            result = await client.get_balance()
            if hasattr(result, "balance"):
                return int(result.balance)
            return int(result)
    except Exception as exc:
        print(f"  WARNING: balance probe failed ({exc}) — proceeding without balance check.")
        return -1


def show_manifest(
    target_rows: list[dict[str, str]],
    balance: int,
    dry_run: bool,
) -> None:
    total_credits = len(target_rows) * CREDITS_PER_SKU
    print()
    print("=" * 70)
    print("STOP — Confirm before proceeding:")
    print("=" * 70)
    print(f"  Action       : Tripo generate_multiview_image (4 views per SKU)")
    print(f"  Template     : generate_multiview_image")
    print(f"  Model        : flux.1_kontext_pro")
    print(f"  Region       : .ai (https://api.tripo3d.ai/v2/openapi)")
    print(f"  Output       : {OUTPUT_DIR}/<sku>/")
    print()
    print(f"  SKUs ({len(target_rows)}):")
    for row in target_rows:
        src = resolve_source_image(row)
        size_note = f"{src.stat().st_size / 1024:.0f} KB" if src.exists() else "MISSING"
        print(f"    {row['sku']:<22} {row['name']:<40} source={size_note}")
    print()
    print(f"  Credits      : {len(target_rows)} SKUs × {CREDITS_PER_SKU} cr = {total_credits} cr")
    if balance >= 0:
        remaining = balance - total_credits
        status = "OK" if remaining >= 0 else "INSUFFICIENT"
        print(f"  Balance      : {balance} cr  →  after dispatch: {remaining} cr  [{status}]")
        if remaining < 0:
            print(f"  WARNING: insufficient balance — top up before dispatching.")
    print(f"  NOTE: Outputs land in renders/output/tripo/ — NOT the theme.")
    print(f"        A separate SFTP step (with its own confirmation) is required")
    print(f"        to publish approved images to skyyrose.co.")
    print("=" * 70)
    if dry_run:
        print("DRY RUN — no API calls dispatched. Pass --execute to proceed.")
    print()


def dispatch_sku(row: dict[str, str]) -> dict:
    """Invoke the creative hub for a single SKU synchronously."""
    import sys

    sys.path.insert(0, str(REPO_ROOT))

    from skyyrose.elite_studio.creative.runner import run_creative

    src = resolve_source_image(row)
    return run_creative(
        intent="tripo-generate",
        params={
            "image_path": str(src),
            "model_version": "flux.1_kontext_pro",
        },
        sku=row["sku"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Tripo multiview dispatch for SkyyRose SKUs.")
    ap.add_argument("--sku", default=None, help="Single SKU to process.")
    ap.add_argument(
        "--all",
        dest="all_published",
        action="store_true",
        help="Process all published SKUs (default: priority set only).",
    )
    ap.add_argument(
        "--execute",
        action="store_true",
        help="Actually dispatch paid API calls (default is dry-run).",
    )
    args = ap.parse_args()

    if not os.environ.get("TRIPO_API_KEY"):
        print("ERROR: TRIPO_API_KEY env var not set.", file=sys.stderr)
        return 2

    rows = load_catalog()
    target_rows = select_skus(rows, all_published=args.all_published, single_sku=args.sku)

    if not target_rows:
        print("No SKUs match the selection criteria. Nothing to dispatch.")
        return 0

    print(f"Probing Tripo balance...")
    balance = asyncio.run(_probe_balance())

    show_manifest(target_rows, balance, dry_run=not args.execute)

    if not args.execute:
        return 0

    # Confirm before any paid dispatch
    answer = input("Proceed? [y/N] ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return 0

    print()
    results: list[tuple[str, bool, str]] = []
    for i, row in enumerate(target_rows, 1):
        sku = row["sku"]
        src = resolve_source_image(row)
        if not src.exists():
            print(f"[{i}/{len(target_rows)}] SKIP {sku} — source image not found: {src}")
            results.append((sku, False, f"source missing: {src}"))
            continue

        print(f"[{i}/{len(target_rows)}] Dispatching {sku}...")
        state = dispatch_sku(row)
        tripo = state.get("tripo_result") or {}
        success = tripo.get("success", False)
        views = tripo.get("views", [])
        error = tripo.get("error", state.get("error", "unknown"))

        if success:
            print(f"  OK — {len(views)} view(s) in {tripo.get('output_path', OUTPUT_DIR / sku)}")
        else:
            print(f"  FAILED — {error}")
        results.append((sku, success, error if not success else ""))

    print()
    print("=" * 70)
    ok = [r for r in results if r[1]]
    fail = [r for r in results if not r[1]]
    print(f"DONE: {len(ok)} succeeded, {len(fail)} failed.")
    if fail:
        print("Failed SKUs:")
        for sku, _, err in fail:
            print(f"  {sku}: {err}")
    print()
    print("Next step: review renders/output/tripo/ and then run the SFTP copy")
    print("step (with confirmation) to publish approved images to the theme.")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
