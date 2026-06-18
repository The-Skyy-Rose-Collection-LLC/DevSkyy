"""
Tripo asset_extraction spike — compares Tripo's template=asset_extraction
output against the current 6-stage compositor's stage-2 background-removal
output for a single SKU.

Implements stage 2 ("Template & Stylization") of Tripo's official 5-stage
product-design flow (see docs/images/product-design-en.png):
    Input → Template & Stylization → Image Gen → 3D Gen → Output

Uses the official `tripo3d` Python SDK (handles upload + task creation +
polling). Verified against SDK source v0.x at
https://github.com/VAST-AI-Research/tripo-python-sdk.

Usage:
    pip install tripo3d
    export TRIPO_API_KEY=...   # .ai region key
    python scripts/tripo_spike_asset_extraction.py --sku br-001 [--execute]

Default is dry-run (prints STOP manifest, no API call). Pass --execute to
actually dispatch the paid call.
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
OUTPUT_DIR = REPO_ROOT / "renders/output/tripo_spike"

# Template slug — advanced docs page uses underscores; SDK docstring uses
# hyphens. Underscored form per docs.tripo3d.ai/image-generation/advanced-image-generation.html.
# If API rejects, retry with hyphenated form ("asset-extraction").
DEFAULT_TEMPLATE = "asset_extraction"
DEFAULT_MODEL = "flux.1_kontext_pro"  # 10 credits


def load_catalog_row(sku: str) -> dict[str, str]:
    with CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["sku"] == sku:
                return row
    raise SystemExit(f"SKU {sku!r} not found in {CATALOG_CSV}")


def resolve_source_image(row: dict[str, str]) -> Path:
    override = row.get("render_source_override", "").strip()
    if override and "/" not in override:
        # Filename-only override → canonical products dir
        image_rel = f"assets/images/products/{override}"
    elif override:
        image_rel = override
    else:
        image_rel = row["image"]
    return THEME_ROOT / image_rel


def show_manifest(
    row: dict[str, str],
    image_path: Path,
    template: str,
    model_version: str,
    prompt: str | None,
    dry_run: bool,
) -> None:
    print()
    print("=" * 64)
    print("STOP — Confirm before proceeding:")
    print("=" * 64)
    print(f"  Action       : Tripo generate_image (template={template})")
    print("  Region       : .ai (https://api.tripo3d.ai/v2/openapi)")
    print(f"  SKU          : {row['sku']}")
    print(f"  Name         : {row['name']}")
    print(f"  Source       : {image_path}")
    if image_path.exists():
        size_kb = image_path.stat().st_size / 1024
        print(f"  Source size  : {size_kb:.1f} KB")
    else:
        print("  Source size  : MISSING — file does not exist")
    print(f"  Model        : {model_version}")
    print(f"  Template     : {template}")
    print(f"  Prompt       : {prompt or '(none — template + file is sufficient)'}")
    print("  Cost         : ~10 credits (~$0.040 on Professional plan)")
    print(f"  Output       : {OUTPUT_DIR / (row['sku'] + '_' + template + '.png')}")
    print("=" * 64)
    if dry_run:
        print("DRY RUN — no API call dispatched. Re-run with --execute to proceed.")
    print()


async def run_spike(
    sku: str,
    image_path: Path,
    template: str,
    model_version: str,
    prompt: str | None,
) -> int:
    try:
        from tripo3d import TaskStatus, TripoClient
    except ImportError:
        print("ERROR: `tripo3d` SDK not installed. Run: pip install tripo3d", file=sys.stderr)
        return 10

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with TripoClient() as client:
        print("[1/3] Creating generate_image task...")
        task_id = await client.generate_image(
            prompt=prompt,
            model_version=model_version,
            file=str(image_path),
            template=template,
        )
        print(f"      task_id={task_id}")

        print("[2/3] Polling task...")
        task = await client.wait_for_task(task_id, verbose=True)

        if task.status != TaskStatus.SUCCESS:
            print(f"ERROR: task ended with status={task.status}", file=sys.stderr)
            return 4

        print("[3/3] Downloading output...")
        downloaded = await client.download_task_models(task, str(OUTPUT_DIR))
        for kind, path in downloaded.items():
            if path:
                print(f"      {kind}: {path}")

        print(f"\nDONE — outputs in {OUTPUT_DIR}")
        return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sku", required=True)
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--model-version", default=DEFAULT_MODEL)
    ap.add_argument(
        "--prompt",
        default=None,
        help="Optional. Template + file is enough for asset_extraction.",
    )
    ap.add_argument(
        "--execute",
        action="store_true",
        help="Actually dispatch the paid API call (default is dry-run)",
    )
    args = ap.parse_args()

    row = load_catalog_row(args.sku)
    image_path = resolve_source_image(row)

    show_manifest(
        row=row,
        image_path=image_path,
        template=args.template,
        model_version=args.model_version,
        prompt=args.prompt,
        dry_run=not args.execute,
    )

    if not args.execute:
        return 0

    if not os.environ.get("TRIPO_API_KEY"):
        print("ERROR: TRIPO_API_KEY env var not set", file=sys.stderr)
        return 2

    if not image_path.exists():
        print(f"ERROR: source image not found: {image_path}", file=sys.stderr)
        return 3

    return asyncio.run(
        run_spike(
            sku=args.sku,
            image_path=image_path,
            template=args.template,
            model_version=args.model_version,
            prompt=args.prompt,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
