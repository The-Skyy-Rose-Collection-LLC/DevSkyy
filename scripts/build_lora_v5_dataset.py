#!/usr/bin/env python3
"""
Build SkyyRose LoRA v5 Training Dataset.

v4 Problem: Hardcoded PRODUCTS dict drifted from the canonical catalog.
After the April 2026 SKU consolidation, lh-002/003/004 triggers trained
on completely wrong garment types. sg-004/sg-d01/sg-d03/sg-d04 were retired
SKUs that had no business being in the training set.

v5 Solution: SKU list is read directly from skyyrose-catalog.csv (the single
source of truth). Only manually-authored sections below are:
  - CAPTION_OVERRIDES: detailed garment descriptions per SKU
  - TECHFLAT_OVERRIDES: when techflat filename doesn't follow {sku}-techflat.jpeg
  - MODEL_SHOTS: Gemini-verified model shot filenames per SKU

Trigger word format: skyyrose_{sku_no_hyphens}  e.g. br-001 → skyyrose_br001

Dataset: datasets/skyyrose_lora_v5/
Usage:
    source .venv-lora/bin/activate
    python scripts/build_lora_v5_dataset.py [--dry-run] [--skus br-001 lh-002]
"""

import argparse
import csv
import json
import shutil
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).parent.parent
CATALOG_CSV = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "skyyrose-catalog.csv"
)
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
DATASET_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v5"
IMAGES_DIR = DATASET_DIR / "images"
CAPTIONS_DIR = DATASET_DIR / "captions"


def sku_to_trigger(sku: str) -> str:
    """br-001 → skyyrose_br001"""
    return "skyyrose_" + sku.replace("-", "")


def read_catalog() -> list[dict]:
    """Return all published, non-retired SKUs from the canonical CSV."""
    rows = []
    with open(CATALOG_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("published", "").strip().lower() in ("true", "1", "yes"):
                rows.append(row)
    return rows


# ─── Caption Overrides ────────────────────────────────────────────────────────
# Manually maintained. Update when product descriptions change.
# Do NOT include the trigger prefix — it is prepended at build time.
# SKUs omitted here get a fallback caption derived from the CSV name + collection.

CAPTION_OVERRIDES: dict[str, str] = {
    # BLACK ROSE COLLECTION
    "br-001": (
        "black crewneck sweatshirt and jogger pants set, black fabric with large white and gray "
        "rose graphic on front of crewneck, matching jogger pants with subtle rose pattern, "
        "luxury streetwear, dark gothic aesthetic, premium cotton blend, "
        "Black Rose Collection by SkyyRose"
    ),
    "br-002": (
        "black jogger pants with subtle rose pattern, elastic waistband with drawstring, "
        "tapered leg with ribbed ankle cuffs, Black Rose Collection by SkyyRose, "
        "luxury streetwear joggers"
    ),
    "br-003": (
        "baseball jersey with 'BLACK IS BEAUTIFUL' text arched across chest in alternating "
        "rose-filled and plain lettering, button-front V-neck collar, back features large "
        "white rose-in-clouds graphic with 'SR' monogram, available in Oakland green/gold, "
        "SF black/orange, white/black, and solid black/white colorways, "
        "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
    ),
    "br-004": (
        "black hoodie with large white and gray rose graphic on front, drawstring hood, "
        "kangaroo pocket, ribbed cuffs and waistband, Black Rose Collection by SkyyRose, "
        "luxury streetwear hoodie"
    ),
    "br-005": (
        "black hoodie Signature Edition with detailed rose and SkyyRose monogram graphics, "
        "heavyweight premium cotton, drawstring hood, Black Rose Collection by SkyyRose, "
        "luxury limited-edition streetwear hoodie"
    ),
    "br-006": (
        "black sherpa fleece jacket with rose embroidery and SkyyRose branding, "
        "zip-up front with snap placket, plush sherpa interior lining, "
        "Black Rose Collection by SkyyRose, luxury streetwear outerwear"
    ),
    "br-007": (
        "black athletic shorts with 'OAKLAND' text in white across front, rose pattern print "
        "throughout, 'Bay Area' script overlay, white elastic drawstring waistband, "
        "white side panels with geometric diamond shapes, small rose-in-clouds patch on left leg, "
        "Black Rose Collection by SkyyRose, luxury streetwear shorts"
    ),
    "br-008": (
        "football jersey SF Inspired BLACK IS BEAUTIFUL series number 1, "
        "SF 49ers colorway with rose fill pattern in numbers, V-neck collar, "
        "short sleeves with stripe details, back nameplate reads BLACK IS BEAUTIFUL, "
        "Black Rose Collection by SkyyRose, luxury streetwear football jersey"
    ),
    "br-009": (
        "football jersey Last Oakland BLACK IS BEAUTIFUL series number 2, "
        "Oakland Raiders silver and black colorway with rose fill pattern in numbers, "
        "V-neck collar, short sleeves, Black Rose Collection by SkyyRose, "
        "luxury streetwear football jersey"
    ),
    "br-010": (
        "basketball jersey The Bay BLACK IS BEAUTIFUL series number 3, "
        "white sleeveless V-neck jersey with 'THE BAY' in gold on front, "
        "large grayscale rose pattern gradient from bottom, gold SR patch, "
        "Black Rose Collection by SkyyRose, luxury streetwear basketball jersey"
    ),
    "br-011": (
        "hockey jersey The Rose BLACK IS BEAUTIFUL series number 4, "
        "rose motif throughout, hockey-style lace-up V-neck collar, "
        "Black Rose Collection by SkyyRose, luxury streetwear hockey jersey"
    ),
    "br-012": (
        "baseball jersey Last Oakland BLACK IS BEAUTIFUL series number 5, "
        "Oakland A's green and gold colorway, button-front, rose-in-clouds graphic on back, "
        "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
    ),
    # LOVE HURTS COLLECTION
    "lh-002": (
        "black jogger pants with white side stripes and drawstring waistband, "
        "embroidered 'Love Hurts' branding, zippered ankle openings, tapered leg silhouette, "
        "Love Hurts Collection by SkyyRose, passionate luxury streetwear joggers"
    ),
    "lh-003": (
        "black basketball shorts with white side stripes, embroidered red rose heart and ribbon "
        "graphic on left thigh, elastic waistband with drawstring, mesh lining, "
        "Love Hurts Collection by SkyyRose, passionate luxury streetwear shorts"
    ),
    "lh-004": (
        "bomber jacket with satin shell, 'Love Hurts' script embroidery on chest, "
        "rose motif on back, ribbed cuffs and waistband, zip-up front, "
        "Love Hurts Collection by SkyyRose, passionate luxury streetwear bomber jacket"
    ),
    "lh-005": (
        "fanny pack belt bag with 'Love Hurts' and rose branding, adjustable crossbody strap, "
        "multiple zip compartments, Love Hurts Collection by SkyyRose, "
        "luxury streetwear accessory"
    ),
    # SIGNATURE COLLECTION
    "sg-001": (
        "athletic shorts with Golden Gate Bridge nighttime photo-print 'The Bay Bridge' design, "
        "elastic waistband with drawstring, Signature Collection by SkyyRose, "
        "Bay Area luxury streetwear shorts"
    ),
    "sg-002": (
        "white t-shirt with purple rose explosion graphic and matching Golden Gate Bridge "
        "nighttime photo-print shorts in purple, detailed multicolor rose on tee, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear set"
    ),
    "sg-003": (
        "athletic shorts with Golden Gate Bridge photo-print 'Stay Golden' design in gold colorway, "
        "elastic waistband with drawstring, Signature Collection by SkyyRose, "
        "Bay Area luxury streetwear shorts"
    ),
    "sg-005": (
        "t-shirt with Golden Gate Bridge photo-print 'The Bay Bridge' design, "
        "all-over print with bridge imagery, crew neck, short sleeves, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear tee"
    ),
    "sg-006": (
        "mint and lavender hoodie with large floral rose graphic on front, "
        "drawstring hood, kangaroo pocket, ribbed cuffs and hem, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear hoodie"
    ),
    "sg-007": (
        "ribbed knit beanie with SkyyRose rose logo woven patch on cuff, "
        "cuffed brim style, unisex fit, premium acrylic knit, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear beanie"
    ),
    "sg-009": (
        "sherpa fleece zip-up jacket with plush sherpa interior and exterior lining, "
        "SkyyRose branding, Signature Collection by SkyyRose, "
        "Bay Area luxury streetwear outerwear"
    ),
    "sg-011": (
        "white t-shirt Original Label with SkyyRose rose logo and wordmark graphic, "
        "crew neck, short sleeves, clean minimal branding, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear tee"
    ),
    "sg-012": (
        "orchid light purple t-shirt Original Label with SkyyRose rose logo and wordmark graphic, "
        "crew neck, short sleeves, Signature Collection by SkyyRose, "
        "Bay Area luxury streetwear tee"
    ),
    "sg-013": (
        "mint and lavender crewneck sweatshirt with floral rose graphic, "
        "ribbed collar cuffs and hem, Mint & Lavender colorway, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear crewneck"
    ),
    "sg-014": (
        "mint and lavender sweatpants with floral rose graphic, elastic waistband with drawstring, "
        "tapered leg, ribbed ankle cuffs, Mint & Lavender colorway, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear sweatpants"
    ),
    "sg-015": (
        "windbreaker set with zip-up jacket and matching pants, lightweight nylon shell, "
        "colorblock panels, elastic waistband, The Windbreaker Set, "
        "Signature Collection by SkyyRose, Bay Area luxury streetwear windbreaker"
    ),
    # KIDS CAPSULE
    "kids-001": (
        "kids colorblock hoodie set red and black, zip-up hoodie with matching sweatpants, "
        "SkyyRose rose logo, premium cotton blend, "
        "Kids Capsule Collection by SkyyRose, luxury children's streetwear"
    ),
    "kids-002": (
        "kids colorblock hoodie set purple and black, zip-up hoodie with matching sweatpants, "
        "SkyyRose rose logo, premium cotton blend, "
        "Kids Capsule Collection by SkyyRose, luxury children's streetwear"
    ),
}

# ─── Techflat Overrides ───────────────────────────────────────────────────────
# Every SKU listed here — actual filenames from assets/images/products/.
# Multi-colorway products list all colorway files; each becomes a separate training image.
# v4 cross-labels (br-002-model-f.webp → br-001) are NOT carried forward without re-verification.

TECHFLAT_OVERRIDES: dict[str, list[str]] = {
    # BLACK ROSE
    "br-001": ["br-001-crewneck.png"],
    "br-002": ["br-002-joggers.png"],
    "br-003": [
        "br-003-baseball-classic.jpeg",  # Base / black-white colorway
        "black-is-beautiful-jersey-techflat-black.jpeg",  # Black/White
        "black-is-beautiful-jersey-techflat-giants.jpeg",  # SF Giants black/orange
        "black-is-beautiful-jersey-techflat-white.jpeg",  # White/Black
    ],
    "br-004": ["br-004-black-rose-hoodie.jpeg"],
    "br-005": ["br-005-signature-hoodie.jpeg"],
    "br-006": ["br-006-sherpa-jacket.jpeg"],
    "br-007": ["br-007-basketball-shorts.jpeg"],
    "br-008": ["br-008-sf-inspired.jpg"],
    "br-009": ["br-009-last-oakland-football.jpg"],
    "br-010": ["br-010-the-bay-basketball.jpeg"],
    "br-011": ["br-011-the-rose-hockey.png"],
    "br-012": [
        "br-012-last-oakland-baseball-front.jpeg",
        "br-012-last-oakland-baseball-back.jpeg",
    ],
    # LOVE HURTS
    "lh-002": ["lh-002-joggers.jpeg"],
    "lh-003": ["lh-003-shorts.jpeg"],
    "lh-004": ["lh-004-bomber.png", "lh-004-bomber-back.png"],
    "lh-005": ["lh-005-fannie.jpeg"],
    # SIGNATURE
    "sg-001": ["sg-001-bay-bridge-shorts.jpeg"],
    "sg-002": ["sg-002-stay-golden-shirt.jpeg"],
    "sg-003": ["sg-003-stay-golden-shorts.jpeg"],
    "sg-005": ["sg-005-bay-bridge-shirt.jpeg"],
    "sg-006": ["sg-006-mint-lavender-hoodie.png"],
    "sg-007": ["sg-007-signature-beanie.png"],
    "sg-009": ["sg-009-sherpa-jacket.jpeg"],
    "sg-011": ["sg-011-original-label-tee-white.jpeg"],
    "sg-012": ["sg-012-original-label-tee-orchid.jpeg"],
    "sg-013": ["sg-013-mint-lavender-crewneck.jpeg"],
    "sg-014": ["sg-014-mint-lavender-sweatpants.jpeg"],
    "sg-015": ["sg-015-windbreaker-set.jpg"],
    # KIDS CAPSULE
    "kids-001": ["kids-001-red-set.jpeg"],
    "kids-002": ["kids-002-purple-set.jpeg"],
}

# ─── Verified Model Shots ─────────────────────────────────────────────────────
# Conservative: only direct {sku}-*-model.webp and {sku}-real-*.jpg files.
# Product-name-style files (love-hurts-varsity-jacket-*) need Gemini re-verification
# before adding — v4 SKU assignments changed and those labels may no longer apply.
# Add verified cross-labels back here with a Gemini confidence comment.

MODEL_SHOTS: dict[str, list[str]] = {
    # BLACK ROSE
    "br-002": ["br-002-back-model.webp"],
    "br-003": ["br-003-back-model.webp"],
    "br-004": ["br-004-back-model.webp"],
    "br-005": ["br-005-back-model.webp"],
    "br-007": [
        "br-007-back-model.webp",
        "br-007-real-front.jpg",
        "br-007-real-back.jpg",
    ],
    "br-008": ["br-008-back-model.webp"],
    # LOVE HURTS
    "lh-002": ["lh-002-back-model.webp"],
    "lh-003": [
        "lh-003-back-model.webp",
        "lh-003-real-front.jpg",
        "lh-003-real-back.jpg",
    ],
    "lh-004": ["lh-004-back-model.webp"],
    "lh-005": ["lh-005-back-model.webp"],
    # SIGNATURE
    "sg-001": ["sg-001-back-model.webp"],
    "sg-002": ["sg-002-back-model.webp"],
    "sg-003": ["sg-003-back-model.webp"],
    "sg-005": ["sg-005-back-model.webp"],
    "sg-006": ["sg-006-back-model.webp"],
    "sg-007": ["signature-beanie-front-model.webp"],
    "sg-009": ["sg-009-back-model.webp"],
    "sg-011": ["sg-011-back-model.webp", "sg-011-front-model.webp"],
    "sg-012": ["sg-012-back-model.webp", "sg-012-front-model.webp"],
    # KIDS CAPSULE
    "kids-001": ["kids-red-set-front-model.webp", "kids-red-set-back-model.webp"],
    "kids-002": ["kids-purple-set-front-model.webp", "kids-purple-set-back-model.webp"],
}


def copy_and_prepare_image(src: Path, dst_name: str, target_size: int = 1024) -> bool:
    try:
        img = Image.open(src).convert("RGB")
        img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        if img.size[0] != target_size or img.size[1] != target_size:
            padded = Image.new("RGB", (target_size, target_size), (255, 255, 255))
            offset = ((target_size - img.size[0]) // 2, (target_size - img.size[1]) // 2)
            padded.paste(img, offset)
            img = padded
        if dst_name.endswith(".webp"):
            dst_name = dst_name.rsplit(".", 1)[0] + ".jpg"
        img.save(IMAGES_DIR / dst_name, "JPEG", quality=95, optimize=True)
        return True
    except Exception as e:
        print(f"  WARNING: {src.name}: {e}")
        return False


def write_caption(image_stem: str, caption: str) -> None:
    (CAPTIONS_DIR / f"{image_stem}.txt").write_text(caption, encoding="utf-8")


def build_caption(sku: str, csv_name: str, collection: str, suffix: str = "") -> str:
    trigger = sku_to_trigger(sku)
    body = CAPTION_OVERRIDES.get(sku) or f"{csv_name}, {collection} Collection by SkyyRose"
    return f"{trigger} {body}{suffix}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SkyyRose LoRA v5 training dataset")
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files")
    parser.add_argument("--skus", nargs="+", help="Limit to specific SKUs")
    args = parser.parse_args()

    catalog = read_catalog()
    if args.skus:
        catalog = [r for r in catalog if r["sku"] in args.skus]

    if not catalog:
        print("ERROR: No published SKUs found in catalog")
        return 1

    if not args.dry_run:
        if IMAGES_DIR.exists():
            shutil.rmtree(IMAGES_DIR)
        if CAPTIONS_DIR.exists():
            shutil.rmtree(CAPTIONS_DIR)
        IMAGES_DIR.mkdir(parents=True)
        CAPTIONS_DIR.mkdir(parents=True)

    print("=" * 70)
    print("  SKYYROSE LORA V5 DATASET BUILDER")
    print(f"  Source: {CATALOG_CSV.name}  ({len(catalog)} published SKUs)")
    print("  Trigger format: skyyrose_{{sku_no_hyphens}}")
    if args.dry_run:
        print("  MODE: DRY RUN — no files written")
    print("=" * 70)

    total_images = 0
    total_products = 0
    metadata_entries: list[dict] = []
    missing: list[str] = []

    for row in catalog:
        sku = row["sku"]
        csv_name = row["name"]
        collection = row.get("collection", "")
        trigger = sku_to_trigger(sku)

        print(f"\n--- {sku}: {csv_name} ---")
        print(f"    trigger: {trigger}")
        product_images = 0

        # 1. Techflat(s) — primary training images
        techflat_files = TECHFLAT_OVERRIDES.get(sku) or [f"{sku}-techflat.jpeg"]
        for tf_file in techflat_files:
            src = PRODUCTS_DIR / tf_file
            if not src.exists():
                print(f"  ! MISSING techflat: {tf_file}")
                missing.append(f"{sku}: {tf_file}")
                continue

            stem = f"{sku}-{Path(tf_file).stem}" if len(techflat_files) > 1 else f"{sku}-techflat"
            dst = f"{stem}.jpg"
            caption = build_caption(
                sku,
                csv_name,
                collection,
                suffix=", technical flat lay illustration, product design reference",
            )

            if not args.dry_run:
                if copy_and_prepare_image(src, dst):
                    write_caption(stem, caption)
                    metadata_entries.append(
                        {
                            "file_name": dst,
                            "text": caption,
                            "sku": sku,
                            "type": "techflat",
                            "trigger": trigger,
                        }
                    )
                    product_images += 1
                    print(f"  + techflat: {tf_file}")
            else:
                print(f"  + techflat: {tf_file} → {dst}")
                product_images += 1

        # 2. Model shots — verified secondary images
        shots = MODEL_SHOTS.get(sku, [])
        for shot_file in shots:
            src = PRODUCTS_DIR / shot_file
            if not src.exists():
                print(f"  ! MISSING model: {shot_file}")
                missing.append(f"{sku}: {shot_file}")
                continue

            stem = f"{sku}-{Path(shot_file).stem}"
            dst = f"{stem}.jpg"
            caption = build_caption(
                sku,
                csv_name,
                collection,
                suffix=", fashion model wearing the garment, full body shot",
            )

            if not args.dry_run:
                if copy_and_prepare_image(src, dst):
                    write_caption(stem, caption)
                    metadata_entries.append(
                        {
                            "file_name": dst,
                            "text": caption,
                            "sku": sku,
                            "type": "model_shot",
                            "trigger": trigger,
                        }
                    )
                    product_images += 1
                    print(f"  + model: {shot_file}")
            else:
                print(f"  + model: {shot_file} → {dst}")
                product_images += 1

        total_images += product_images
        if product_images > 0:
            total_products += 1
        print(f"  = {product_images} images")

    if not args.dry_run:
        # metadata.jsonl for HuggingFace
        with open(DATASET_DIR / "metadata.jsonl", "w") as f:
            for entry in metadata_entries:
                f.write(json.dumps(entry) + "\n")

        # dataset_info.json
        info = {
            "version": "v5",
            "source": "skyyrose-catalog.csv",
            "total_images": total_images,
            "total_products": total_products,
            "trigger_format": "skyyrose_{sku_no_hyphens}",
            "trigger_words": sorted(set(e["trigger"] for e in metadata_entries)),
            "global_trigger": "skyyrose",
            "resolution": 1024,
            "format": "JPEG quality 95",
        }
        with open(DATASET_DIR / "dataset_info.json", "w") as f:
            json.dump(info, f, indent=2)

    print("\n" + "=" * 70)
    action = "PLAN" if args.dry_run else "BUILT"
    print(f"  DATASET {action}: {total_images} images across {total_products} products")
    if not args.dry_run:
        print(f"  Location: {DATASET_DIR}")

    if missing:
        print(f"\n  MISSING FILES ({len(missing)}) — add to PRODUCTS_DIR before training:")
        for m in missing:
            print(f"    {m}")

    return 0


if __name__ == "__main__":
    exit(main())
