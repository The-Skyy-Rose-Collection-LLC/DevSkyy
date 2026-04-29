"""Re-derive Stage 2 decoration masks for specific SKUs using fixed MaskDeriver.

Overwrites the existing stage1-base-mask.png files in-place so that
rerun_stage3.py picks them up on the next run.

Usage:
    python scripts/regen_masks.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skyyrose.core.dossier_loader import get_product_with_dossier
from skyyrose.elite_studio.synthesis.stages.mask_deriver import MaskDeriver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_DIR = ROOT / "renders" / "output"

# SKU/view pairs whose masks need regeneration because the old masks were
# generated before the STATIC_REGION_BOXES alias fix landed.
TARGETS: list[tuple[str, str]] = [
    ("sg-014", "front"),
    ("sg-015", "front"),
]


def _stage_dir(sku: str, view: str, name: str) -> Path:
    name_slug = name.lower().replace(" ", "-").replace("&", "&")
    return OUTPUT_DIR / name_slug / f"{sku}-{view}"


def regen_one(sku: str, view: str) -> bool:
    product = get_product_with_dossier(sku)
    if not product or not product.get("dossier"):
        logger.error("no dossier for %s", sku)
        return False

    dossier = product["dossier"]
    name = dossier["name"]
    stage_dir = _stage_dir(sku, view, name)
    base = stage_dir / f"{sku}-{view}-stage1-base.png"

    if not base.is_file():
        logger.error("Stage 1 base missing: %s", base)
        return False

    logger.info("=== %s %s — re-deriving mask ===", sku, view)
    deriver = MaskDeriver()
    result = deriver.derive(
        image_path=base,
        dossier=dossier,
        view=view,
        out_dir=stage_dir,
    )
    logger.info(
        "mask written: %s  method=%s  coverage=%.3f  boxes=%d",
        result.mask_path,
        result.method,
        result.coverage_frac,
        len(result.region_boxes),
    )
    for box in result.region_boxes:
        logger.info("  %s", box)
    for w in result.warnings:
        logger.warning("  WARN: %s", w)

    return True


def main() -> None:
    ok = 0
    for sku, view in TARGETS:
        if regen_one(sku, view):
            ok += 1

    print(f"\nMask regen: {ok}/{len(TARGETS)} succeeded")


if __name__ == "__main__":
    main()
