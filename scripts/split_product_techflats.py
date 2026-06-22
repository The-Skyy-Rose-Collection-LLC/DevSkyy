"""Split / reassign product techflats per the Gemini vision analysis.

Consumes product-references/techflat-vision-analysis.json (written by
scripts/vision_inspect_techflats.py) and crops each region by its detected
bounding box into correctly-named, correctly-assigned techflat files:

    {sku}-techflat-front.jpeg
    {sku}-techflat-back.jpeg

The Love Hurts techflats were filename-scrambled. The founder-confirmed
rotation (2026-05-27):

  lh-002-techflat.jpeg  IS the bomber  -> lh-004 front+back
  lh-003-techflat.jpeg  IS the joggers -> lh-006 front (white) + lh-002 front (black)
  lh-004-techflat.jpeg  IS the shorts  -> lh-003 front (whole image, single view)
  sg-013-..-set         crewneck+sweats -> sg-013 f/b + sg-014 f/b

sg-007 (4 beanies) is deferred — not handled here.

After writing the corrected files, the mislabeled source originals are
git-removed so the scaffolder's {sku}*-techflat.* glob can't pick up a wrong
image. All crops use the exact normalized bboxes from the analysis (with a
small safety pad), not naive halving.

Usage:
    .venv/bin/python scripts/split_product_techflats.py            # execute
    .venv/bin/python scripts/split_product_techflats.py --dry-run  # preview
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.core.paths import THEME_ROOT  # noqa: E402

PRODUCT_REFERENCES_DIR = THEME_ROOT / "data" / "product-references"
ANALYSIS_JSON = PRODUCT_REFERENCES_DIR / "techflat-vision-analysis.json"

_PAD = 0.015  # 1.5% safety pad around each bbox so edges aren't clipped

# region-crop reassignment: source filename -> [(region_index, dest_sku, view)]
REGION_REASSIGN: dict[str, list[tuple[int, str, str]]] = {
    "lh-002-techflat.jpeg": [  # actually the bomber, TB layout
        (0, "lh-004", "front"),
        (1, "lh-004", "back"),
    ],
    "lh-003-techflat.jpeg": [  # actually the joggers, LR, both front
        (0, "lh-006", "front"),  # white (left)
        (1, "lh-002", "front"),  # black (right)
    ],
    "sg-013-mint-lavender-crewneck-set-techflat.jpeg": [  # 2x2
        (0, "sg-013", "front"),  # crewneck front
        (1, "sg-013", "back"),  # crewneck back
        (2, "sg-014", "front"),  # sweats front
        (3, "sg-014", "back"),  # sweats back
    ],
}

# whole-file copy (no crop): source filename -> (dest_sku, view)
WHOLE_COPY: dict[str, tuple[str, str]] = {
    "lh-004-techflat.jpeg": ("lh-003", "front"),  # the shorts -> lh-003
}

# originals to remove once their correct splits are written
REMOVE_ORIGINALS = [
    "lh-002-techflat.jpeg",
    "lh-003-techflat.jpeg",
    "lh-004-techflat.jpeg",
    "sg-013-mint-lavender-crewneck-set-techflat.jpeg",
]


def _crop_norm(img: Image.Image, bbox: list[float]) -> Image.Image:
    """Crop a normalized bbox [x0,y0,x1,y1] with a small safety pad."""
    w, h = img.size
    x0, y0, x1, y1 = bbox
    x0 = max(0.0, x0 - _PAD)
    y0 = max(0.0, y0 - _PAD)
    x1 = min(1.0, x1 + _PAD)
    y1 = min(1.0, y1 + _PAD)
    return img.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)))


def _save(img: Image.Image, sku: str, view: str, *, dry_run: bool) -> Path:
    dest = PRODUCT_REFERENCES_DIR / f"{sku}-techflat-{view}.jpeg"
    if dry_run:
        print(f"  [dry-run] would write {dest.name} ({img.size[0]}x{img.size[1]})")
        return dest
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dest, "JPEG", quality=95, optimize=True)
    print(f"  wrote {dest.name} ({img.size[0]}x{img.size[1]})")
    return dest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not ANALYSIS_JSON.is_file():
        print(f"missing analysis: {ANALYSIS_JSON} — run vision_inspect_techflats.py first")
        return 2
    analysis = json.loads(ANALYSIS_JSON.read_text(encoding="utf-8"))

    written = 0

    # ── region crops ────────────────────────────────────────────────────
    for src_name, assignments in REGION_REASSIGN.items():
        src = PRODUCT_REFERENCES_DIR / src_name
        if not src.is_file():
            print(f"SKIP {src_name}: source not found")
            continue
        a = analysis.get(src_name, {})
        regions = a.get("regions", [])
        print(f"\n{src_name} ({len(regions)} regions detected):")
        with Image.open(src) as img:
            img.load()
            for region_idx, sku, view in assignments:
                if region_idx >= len(regions):
                    print(f"  SKIP region {region_idx} for {sku}/{view}: not in analysis")
                    continue
                bbox = regions[region_idx].get("bbox")
                if not bbox or len(bbox) != 4:
                    print(f"  SKIP region {region_idx}: no valid bbox")
                    continue
                crop = _crop_norm(img, bbox)
                _save(crop, sku, view, dry_run=args.dry_run)
                written += 1

    # ── whole-file copies ───────────────────────────────────────────────
    for src_name, (sku, view) in WHOLE_COPY.items():
        src = PRODUCT_REFERENCES_DIR / src_name
        if not src.is_file():
            print(f"SKIP {src_name}: source not found")
            continue
        print(f"\n{src_name} (whole copy -> {sku}/{view}):")
        with Image.open(src) as img:
            img.load()
            _save(img, sku, view, dry_run=args.dry_run)
            written += 1

    # ── remove mislabeled originals (git rm) ────────────────────────────
    print("\nremoving mislabeled originals:")
    for name in REMOVE_ORIGINALS:
        p = PRODUCT_REFERENCES_DIR / name
        if not p.is_file():
            print(f"  (already gone) {name}")
            continue
        if args.dry_run:
            print(f"  [dry-run] would git rm {name}")
            continue
        rel = str(p.relative_to(_REPO_ROOT))
        res = subprocess.run(
            ["git", "rm", "-q", rel], cwd=_REPO_ROOT, capture_output=True, text=True
        )
        if res.returncode == 0:
            print(f"  git rm {name}")
        else:
            # not tracked — plain unlink
            p.unlink()
            print(f"  unlink {name} (was untracked)")

    print(f"\n{'[dry-run] ' if args.dry_run else ''}DONE: {written} techflat files written")
    if not args.dry_run:
        print("Next: update scaffolder to prefer *-techflat-front/back, then re-scaffold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
