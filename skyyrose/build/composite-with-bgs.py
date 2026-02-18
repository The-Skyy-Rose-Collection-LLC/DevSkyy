#!/usr/bin/env python3
"""
SkyyRose — Product × Collection Background Compositing
=======================================================
Takes transparent product PNGs and composites them onto
collection-themed AI-generated backgrounds.

Output per product image:
  products-ecom/{id}/{id}-product-{bg_name}-hero.jpg    (2400×2400 square)
  products-ecom/{id}/{id}-product-{bg_name}-hero.webp   (same, smaller)

Usage:
  python3 build/composite-with-bgs.py
  python3 build/composite-with-bgs.py br-001
"""

import sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance
import time

ROOT     = Path(__file__).parent.parent
ECOM_DIR = ROOT / "assets/images/products-ecom"
BG_DIR   = ROOT / "assets/images/collection-bgs"

CANVAS   = 2400
FILL     = 0.80  # product fills 80% of canvas on collection bg (slightly smaller = more atmospheric)

# Collection → background files (in priority order)
COLLECTION_BGS = {
    "black-rose": [
        "black-rose/black-rose-void.png",
        "black-rose/black-rose-garden.png",
        "black-rose/black-rose-studio.png",
    ],
    "love-hurts": [
        "love-hurts/love-hurts-crimson.png",
        "love-hurts/love-hurts-passion.png",
        "love-hurts/love-hurts-raw.png",
    ],
    "signature": [
        "signature/signature-golden.png",
        "signature/signature-marble.png",
        "signature/signature-editorial.png",
    ],
}

# Product → collection mapping
PRODUCTS = [
    dict(id="br-001", col="black-rose", files=["br-001-product"]),
    dict(id="br-002", col="black-rose", files=["br-002-product"]),
    dict(id="br-003", col="black-rose", files=["br-003-product","br-003-product-2","br-003-product-3","br-003-product-4","br-003-product-5","br-003-product-6","br-003-product-7"]),
    dict(id="br-004", col="black-rose", files=["br-004-product"]),
    dict(id="br-005", col="black-rose", files=["br-005-product"]),
    dict(id="br-006", col="black-rose", files=["br-006-product","br-006-product-2"]),
    dict(id="br-007", col="black-rose", files=["br-007-product","br-007-product-2"]),
    dict(id="br-008", col="black-rose", files=["br-008-product"]),
    dict(id="lh-001", col="love-hurts", files=["lh-001-product","lh-001-product-2"]),
    dict(id="lh-002", col="love-hurts", files=["lh-002-product"]),
    dict(id="lh-002b", col="love-hurts", files=["lh-002b-product","lh-002b-product-2"]),
    dict(id="lh-003", col="love-hurts", files=["lh-003-product","lh-003-product-2","lh-003-product-3"]),
    dict(id="lh-004", col="love-hurts", files=["lh-004-product"]),
    dict(id="sg-001", col="signature", files=["sg-001-product","sg-001-product-2"]),
    dict(id="sg-002", col="signature", files=["sg-002-product"]),
    dict(id="sg-003", col="signature", files=["sg-003-product","sg-003-product-2"]),
    dict(id="sg-004", col="signature", files=["sg-004-product","sg-004-product-2"]),
    dict(id="sg-005", col="signature", files=["sg-005-product"]),
    dict(id="sg-006", col="signature", files=["sg-006-product","sg-006-product-2","sg-006-product-3"]),
    dict(id="sg-007", col="signature", files=["sg-007-product","sg-007-product-2","sg-007-product-3"]),
    dict(id="sg-009", col="signature", files=["sg-009-product","sg-009-product-2"]),
    dict(id="sg-010", col="signature", files=["sg-010-product","sg-010-product-2"]),
]


def load_bg(bg_path: Path, size: int) -> Image.Image:
    """Load and resize a background to square canvas."""
    bg = Image.open(bg_path).convert("RGB")
    # Crop to square from center
    w, h = bg.size
    short = min(w, h)
    left  = (w - short) // 2
    top   = (h - short) // 2
    bg    = bg.crop((left, top, left + short, top + short))
    bg    = bg.resize((size, size), Image.LANCZOS)
    return bg.convert("RGBA")


def place_product(bg: Image.Image, product_png: Path, fill: float, canvas: int) -> Image.Image:
    """Place a transparent product PNG centered on background."""
    prod = Image.open(product_png).convert("RGBA")

    # Auto-crop to subject
    alpha = prod.split()[3]
    bbox  = alpha.getbbox()
    if bbox:
        prod = prod.crop(bbox)

    # Scale product to fill ratio
    pw, ph = prod.size
    target = int(canvas * fill)
    scale  = min(target / pw, target / ph)
    new_w  = int(pw * scale)
    new_h  = int(ph * scale)
    prod   = prod.resize((new_w, new_h), Image.LANCZOS)

    # Center on canvas
    paste_x = (canvas - new_w) // 2
    paste_y = (canvas - new_h) // 2

    result = bg.copy()
    result.paste(prod, (paste_x, paste_y), prod)
    return result


def enhance_composite(img: Image.Image) -> Image.Image:
    """Final color grading pass on the composite."""
    rgb = img.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.05)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.8, percent=60, threshold=3))
    return rgb


def composite_product(prod: dict, target_id: str | None):
    if target_id and prod["id"] != target_id:
        return 0

    col      = prod["col"]
    bgs_list = COLLECTION_BGS.get(col, [])
    prod_dir = ECOM_DIR / prod["id"]

    # Use primary bg (index 0) for main hero, rotate through others for variants
    bg_paths = [BG_DIR / p for p in bgs_list]
    available_bgs = [p for p in bg_paths if p.exists()]

    if not available_bgs:
        print(f"    ⚠️  No backgrounds available for {col}")
        return 0

    total = 0
    col_label = col.replace("-", " ").upper()
    print(f"\n  [{col_label}] {prod['id']}")

    for fi, stem in enumerate(prod["files"]):
        png_path = prod_dir / f"{stem}-master.png"
        if not png_path.exists():
            print(f"    ⚠️  Not found: {stem}-master.png")
            continue

        # Pair product shot with background (cycle through available bgs)
        bg_path = available_bgs[fi % len(available_bgs)]
        bg_name = bg_path.stem

        out_jpg  = prod_dir / f"{stem}-{bg_name}.jpg"
        out_webp = prod_dir / f"{stem}-{bg_name}.webp"

        try:
            bg        = load_bg(bg_path, CANVAS)
            composite = place_product(bg, png_path, FILL, CANVAS)
            final_rgb = enhance_composite(composite)

            final_rgb.save(out_jpg,  "JPEG", quality=93, optimize=True, progressive=True)
            final_rgb.save(out_webp, "WEBP", quality=87, method=6)

            jpg_kb  = out_jpg.stat().st_size  // 1024
            webp_kb = out_webp.stat().st_size // 1024
            print(f"    ✅ {stem} × {bg_name}  JPG:{jpg_kb}KB  WebP:{webp_kb}KB")
            total += 1
        except Exception as e:
            print(f"    ❌ {stem}: {e}")

    return total


def main():
    target = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

    print("\n SkyyRose — Product × Collection Background Compositing")
    print("=" * 58)

    total_ok = 0
    for prod in PRODUCTS:
        n = composite_product(prod, target)
        total_ok += n

    print("\n" + "=" * 58)
    print(f"  Done — {total_ok} composites created")
    print(f"  Output: assets/images/products-ecom/{{product-id}}/\n")


if __name__ == "__main__":
    main()
