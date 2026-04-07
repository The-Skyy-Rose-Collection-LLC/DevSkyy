#!/usr/bin/env python3
"""Split composite techflat images into individual front/back views.

Analyzes each techflat layout and crops into separate images:
- 2-across: left = front, right = back
- 2x2 grid: top-left = item1 front, top-right = item1 back,
            bottom-left = item2 front, bottom-right = item2 back
- Vertical stack: split by row

Output goes to assets/techflats/split/ with clear naming:
  {collection}/{product}-front.jpeg
  {collection}/{product}-back.jpeg
"""

import sys
from pathlib import Path
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TECHFLATS = PROJECT_ROOT / "assets" / "techflats"
SPLIT_DIR = TECHFLATS / "split"


def split_horizontal(img, name_left, name_right, collection, out_dir):
    """Split a side-by-side image into left (front) and right (back)."""
    w, h = img.size
    mid = w // 2

    left = img.crop((0, 0, mid, h))
    right = img.crop((mid, 0, w, h))

    col_dir = out_dir / collection
    col_dir.mkdir(parents=True, exist_ok=True)

    left.save(col_dir / f"{name_left}.jpeg", "JPEG", quality=95)
    right.save(col_dir / f"{name_right}.jpeg", "JPEG", quality=95)
    print(f"  -> {name_left}.jpeg + {name_right}.jpeg")


def split_2x2(img, names, collection, out_dir):
    """Split a 2x2 grid into 4 images.

    names = [top_left, top_right, bottom_left, bottom_right]
    """
    w, h = img.size
    mid_x = w // 2
    mid_y = h // 2

    crops = [
        (0, 0, mid_x, mid_y),          # top-left
        (mid_x, 0, w, mid_y),          # top-right
        (0, mid_y, mid_x, h),          # bottom-left
        (mid_x, mid_y, w, h),          # bottom-right
    ]

    col_dir = out_dir / collection
    col_dir.mkdir(parents=True, exist_ok=True)

    for name, box in zip(names, crops):
        cropped = img.crop(box)
        cropped.save(col_dir / f"{name}.jpeg", "JPEG", quality=95)
        print(f"  -> {name}.jpeg")


def split_vertical(img, names, collection, out_dir):
    """Split a vertically stacked image into N rows."""
    w, h = img.size
    n = len(names)
    row_h = h // n

    col_dir = out_dir / collection
    col_dir.mkdir(parents=True, exist_ok=True)

    for i, name in enumerate(names):
        top = i * row_h
        bottom = (i + 1) * row_h if i < n - 1 else h
        cropped = img.crop((0, top, w, bottom))
        cropped.save(col_dir / f"{name}.jpeg", "JPEG", quality=95)
        print(f"  -> {name}.jpeg")


def split_top_bottom_with_sides(img, top_names, bottom_name, collection, out_dir):
    """Split: top row is side-by-side, bottom is single centered."""
    w, h = img.size

    # Top half: two items side by side
    top_h = h // 2
    mid_x = w // 2

    col_dir = out_dir / collection
    col_dir.mkdir(parents=True, exist_ok=True)

    top_left = img.crop((0, 0, mid_x, top_h))
    top_right = img.crop((mid_x, 0, w, top_h))
    bottom = img.crop((0, top_h, w, h))

    top_left.save(col_dir / f"{top_names[0]}.jpeg", "JPEG", quality=95)
    print(f"  -> {top_names[0]}.jpeg")
    top_right.save(col_dir / f"{top_names[1]}.jpeg", "JPEG", quality=95)
    print(f"  -> {top_names[1]}.jpeg")
    bottom.save(col_dir / f"{bottom_name}.jpeg", "JPEG", quality=95)
    print(f"  -> {bottom_name}.jpeg")


def main():
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0

    # ── BLACK ROSE ──────────────────────────────────────────────

    # Crewneck + Joggers (2x2: crewneck front/back top, joggers front/back bottom)
    print("\nblack-rose/crewneck-and-joggers.jpeg")
    img = Image.open(TECHFLATS / "black-rose" / "crewneck-and-joggers.jpeg")
    split_2x2(img, [
        "br-crewneck-front",
        "br-crewneck-back",
        "br-joggers-front",
        "br-joggers-back",
    ], "black-rose", SPLIT_DIR)
    total += 4

    # Jerseys (all are front+back side by side)
    for jersey_file, prefix in [
        ("bib-baseball-black.jpeg", "br-jersey-baseball-black"),
        ("bib-baseball-giants.jpeg", "br-jersey-baseball-giants"),
        ("bib-baseball-last-oakland.jpeg", "br-jersey-baseball-oakland"),
        ("bib-baseball-white.jpeg", "br-jersey-baseball-white"),
        ("bib-basketball.jpeg", "br-jersey-basketball"),
        ("bib-football-last-oakland.jpeg", "br-jersey-football-oakland"),
        ("bib-football-sf-inspired.jpeg", "br-jersey-football-sf"),
        ("bib-hockey-jersey.jpg", "br-jersey-hockey"),
    ]:
        path = TECHFLATS / "black-rose" / jersey_file
        if path.exists():
            print(f"\nblack-rose/{jersey_file}")
            img = Image.open(path)
            split_horizontal(img, f"{prefix}-front", f"{prefix}-back", "black-rose", SPLIT_DIR)
            total += 2

    # ── LOVE HURTS ──────────────────────────────────────────────

    # Bomber (front+back side by side)
    print("\nlove-hurts/bomber.jpeg")
    img = Image.open(TECHFLATS / "love-hurts" / "bomber.jpeg")
    split_horizontal(img, "lh-bomber-front", "lh-bomber-back", "love-hurts", SPLIT_DIR)
    total += 2

    # Bombers + Joggers (top: bomber front+back, bottom: joggers)
    print("\nlove-hurts/bombers-and-joggers.jpeg")
    img = Image.open(TECHFLATS / "love-hurts" / "bombers-and-joggers.jpeg")
    split_top_bottom_with_sides(img,
        ["lh-bomber-joggers-front", "lh-bomber-joggers-back"],
        "lh-joggers-front",
        "love-hurts", SPLIT_DIR)
    total += 3

    # Shorts (single image — just copy)
    print("\nlove-hurts/shorts.jpeg")
    img = Image.open(TECHFLATS / "love-hurts" / "shorts.jpeg")
    col_dir = SPLIT_DIR / "love-hurts"
    col_dir.mkdir(parents=True, exist_ok=True)
    img.save(col_dir / "lh-shorts-front.jpeg", "JPEG", quality=95)
    print(f"  -> lh-shorts-front.jpeg (single)")
    total += 1

    # ── SIGNATURE ───────────────────────────────────────────────

    # Bridge Series Golden (t-shirt + shorts, 2x2)
    print("\nsignature/bridge-series-golden.jpeg")
    img = Image.open(TECHFLATS / "signature" / "bridge-series-golden.jpeg")
    split_2x2(img, [
        "sg-bridge-tee-golden-front",
        "sg-bridge-tee-golden-back",
        "sg-bridge-shorts-golden-front",
        "sg-bridge-shorts-golden-back",
    ], "signature", SPLIT_DIR)
    total += 4

    # Bridge Shorts Bay (single front+back)
    path = TECHFLATS / "signature" / "bridge-shorts-bay.jpeg"
    if path.exists():
        print("\nsignature/bridge-shorts-bay.jpeg")
        img = Image.open(path)
        split_horizontal(img, "sg-bridge-shorts-bay-front", "sg-bridge-shorts-bay-back", "signature", SPLIT_DIR)
        total += 2

    # Bridge Shorts Golden (single front+back)
    path = TECHFLATS / "signature" / "bridge-shorts-golden.jpeg"
    if path.exists():
        print("\nsignature/bridge-shorts-golden.jpeg")
        img = Image.open(path)
        split_horizontal(img, "sg-shorts-golden-front", "sg-shorts-golden-back", "signature", SPLIT_DIR)
        total += 2

    # Bridge Shorts Variants (2x2: Bay Bridge top, Golden Gate bottom)
    print("\nsignature/bridge-shorts-variants.jpg")
    img = Image.open(TECHFLATS / "signature" / "bridge-shorts-variants.jpg")
    split_2x2(img, [
        "sg-shorts-bay-v2-front",
        "sg-shorts-bay-v2-back",
        "sg-shorts-golden-v2-front",
        "sg-shorts-golden-v2-back",
    ], "signature", SPLIT_DIR)
    total += 4

    # Mint Lavender Crewneck + Sweats (2x2)
    print("\nsignature/mint-lavender-crewneck-sweats.jpeg")
    img = Image.open(TECHFLATS / "signature" / "mint-lavender-crewneck-sweats.jpeg")
    split_2x2(img, [
        "sg-mint-lav-crewneck-front",
        "sg-mint-lav-crewneck-back",
        "sg-mint-lav-sweats-front",
        "sg-mint-lav-sweats-back",
    ], "signature", SPLIT_DIR)
    total += 4

    # Mint Lavender Hoodie (single — copy or split if front+back)
    path = TECHFLATS / "signature" / "mint-lavender-hoodie.jpeg"
    if path.exists():
        print("\nsignature/mint-lavender-hoodie.jpeg")
        img = Image.open(path)
        col_dir = SPLIT_DIR / "signature"
        col_dir.mkdir(parents=True, exist_ok=True)
        img.save(col_dir / "sg-mint-lav-hoodie-front.jpeg", "JPEG", quality=95)
        print(f"  -> sg-mint-lav-hoodie-front.jpeg (single)")
        total += 1

    # Windbreaker Set (2x2)
    print("\nsignature/windbreaker-set.jpeg")
    img = Image.open(TECHFLATS / "signature" / "windbreaker-set.jpeg")
    split_2x2(img, [
        "sg-windbreaker-front",
        "sg-windbreaker-back",
        "sg-windbreaker-joggers-front",
        "sg-windbreaker-joggers-back",
    ], "signature", SPLIT_DIR)
    total += 4

    # Beanies (4 vertical)
    print("\nsignature/beanies.jpeg")
    img = Image.open(TECHFLATS / "signature" / "beanies.jpeg")
    split_vertical(img, [
        "sg-beanie-purple",
        "sg-beanie-black-silver",
        "sg-beanie-red",
        "sg-beanie-red-large",
    ], "signature", SPLIT_DIR)
    total += 4

    # ── KIDS CAPSULE ────────────────────────────────────────────

    # Red Set (2x2: hoodie front/back top, joggers front/back bottom)
    print("\nkids-capsule/colorblock-red.jpeg")
    img = Image.open(TECHFLATS / "kids-capsule" / "colorblock-red.jpeg")
    split_2x2(img, [
        "kids-red-hoodie-front",
        "kids-red-hoodie-back",
        "kids-red-joggers-front",
        "kids-red-joggers-back",
    ], "kids-capsule", SPLIT_DIR)
    total += 4

    # Purple Set (2x2)
    print("\nkids-capsule/colorblock-purple.jpeg")
    img = Image.open(TECHFLATS / "kids-capsule" / "colorblock-purple.jpeg")
    split_2x2(img, [
        "kids-purple-hoodie-front",
        "kids-purple-hoodie-back",
        "kids-purple-joggers-front",
        "kids-purple-joggers-back",
    ], "kids-capsule", SPLIT_DIR)
    total += 4

    print(f"\n{'=' * 50}")
    print(f"SPLIT COMPLETE: {total} images generated")
    print(f"Output: {SPLIT_DIR}")


if __name__ == "__main__":
    main()
