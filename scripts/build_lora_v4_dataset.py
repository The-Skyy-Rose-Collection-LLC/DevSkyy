#!/usr/bin/env python3
"""
Build SkyyRose LoRA v4 Training Dataset.

v3 Problem: Single trigger word 'skyyrose' for 390 images — model learned brand aesthetic
but couldn't distinguish individual products.

v4 Solution: Per-SKU trigger words + detailed captions from tech flats.
Each product gets its own trigger (e.g., 'skyyrose_br001') so generation prompts
can target SPECIFIC products.

Dataset structure:
  datasets/skyyrose_lora_v4/
    images/           # All training images (tech flats + good model shots)
    captions/         # Per-image .txt caption files
    metadata.jsonl    # HuggingFace-compatible metadata

Usage:
    source .venv-lora/bin/activate
    python scripts/build_lora_v4_dataset.py
"""

import json
import shutil
from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
DATASET_DIR = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4"
IMAGES_DIR = DATASET_DIR / "images"
CAPTIONS_DIR = DATASET_DIR / "captions"

# ─── Per-SKU Product Definitions ───────────────────────────────────────────────
# Each product has:
#   trigger: unique trigger word for this product
#   name: human-readable product name
#   caption: detailed description for training (what the model needs to learn)
#   techflat: filename of the tech flat image
#   model_shots: list of model shot filenames to include (good matches only)

PRODUCTS = {
    # ═══ BLACK ROSE COLLECTION ═══
    "br-001": {
        "trigger": "skyyrose_br001",
        "name": "Black Rose Crewneck & Jogger Set",
        "caption": (
            "skyyrose_br001 black crewneck sweatshirt and jogger pants set, "
            "Black Rose Collection by SkyyRose, black fabric with large white and gray "
            "rose graphic on front of crewneck, matching jogger pants with subtle rose pattern, "
            "luxury streetwear, dark gothic aesthetic, premium cotton blend"
        ),
        "techflat": "br-001-techflat.jpeg",
        # Gemini vision: br-001-model-f/m confirmed 100%, br-002-model-f/m also br-001 at 100%
        "model_shots": [
            "br-001-model-f.webp",
            "br-001-model-m.webp",
            "br-002-model-f.webp",  # Mislabeled as br-002, actually br-001 (100%)
            "br-002-model-m.webp",  # Mislabeled as br-002, actually br-001 (100%)
        ],
    },
    "br-003-oakland": {
        "trigger": "skyyrose_br003_oakland",
        "name": "Last Oakland Black Is Beautiful Baseball Jersey (Green/Gold)",
        "caption": (
            "skyyrose_br003_oakland dark green baseball jersey with gold trim and piping, "
            "'BLACK IS BEAUTIFUL' text in gold arched across chest, button-front, "
            "back features large white and black rose emerging from gold clouds graphic, "
            "small 'SR' monogram on back collar, Oakland A's green and gold colorway, "
            "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
        ),
        "techflat": "br-003-techflat-oakland.jpeg",
        "model_shots": [],  # Model shots have wrong trim color (orange instead of gold)
    },
    "br-003-giants": {
        "trigger": "skyyrose_br003_giants",
        "name": "Black Is Beautiful Baseball Jersey (Black/Orange - Giants)",
        "caption": (
            "skyyrose_br003_giants black baseball jersey with orange trim and piping, "
            "'BLACK IS BEAUTIFUL' text in orange arched across chest, button-front, "
            "white V-neck insert, back features large white rose emerging from clouds graphic, "
            "'SR' monogram on back collar, San Francisco Giants black and orange colorway, "
            "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
        ),
        "techflat": "br-003-techflat-giants.jpeg",
        # Gemini vision: br-003-model-m confirmed 100%
        "model_shots": ["br-003-model-m.webp"],
    },
    "br-003-white": {
        "trigger": "skyyrose_br003_white",
        "name": "Black Is Beautiful Baseball Jersey (White)",
        "caption": (
            "skyyrose_br003_white white baseball jersey with black trim and piping, "
            "'BLACK IS BEAUTIFUL' text in black arched across chest, button-front, "
            "back features black rose emerging from clouds graphic, "
            "'SR' monogram on back collar, clean white colorway, "
            "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
        ),
        "techflat": "br-003-techflat-white.jpeg",
        "model_shots": [],
    },
    "br-003-black": {
        "trigger": "skyyrose_br003_black",
        "name": "Black Is Beautiful Baseball Jersey (Black/White)",
        "caption": (
            "skyyrose_br003_black black baseball jersey with white trim and piping, "
            "'BLACK IS BEAUTIFUL' text in white arched across chest, button-front, "
            "back features white rose emerging from clouds graphic, "
            "'SR' monogram on back collar, monochrome black and white colorway, "
            "Black Rose Collection by SkyyRose, luxury streetwear baseball jersey"
        ),
        "techflat": "br-003-techflat-black.jpeg",
        "model_shots": [],
    },
    "br-007": {
        "trigger": "skyyrose_br007",
        "name": "Oakland Black Rose Shorts",
        "caption": (
            "skyyrose_br007 black athletic shorts with 'OAKLAND' text in white across front, "
            "rose pattern print throughout, 'Bay Area' script overlay, white drawstring waistband, "
            "white side panels with geometric diamond shapes, small rose-in-clouds patch on left leg, "
            "Black Rose Collection by SkyyRose, luxury streetwear shorts"
        ),
        "techflat": "br-007-techflat.jpeg",
        "model_shots": [],  # Model shots show wrong product (hoodie instead of shorts)
    },
    "br-d02": {
        "trigger": "skyyrose_brd02",
        "name": "Black Rose Football Jersey (Red #80)",
        "caption": (
            "skyyrose_brd02 red football jersey with number 80, "
            "'BLACK IS BEAUTIFUL' text across chest in alternating rose-filled and plain numbers, "
            "V-neck collar, short sleeves with black and white stripe details, "
            "back has large number 80 with 'BLACK IS BEAUTIFUL' nameplate, "
            "Black Rose Collection by SkyyRose, luxury streetwear football jersey"
        ),
        "techflat": "br-d02-techflat.jpeg",
        "model_shots": ["br-d02-model-f.webp", "br-d02-model-m.webp"],
    },
    "br-d03": {
        "trigger": "skyyrose_brd03",
        "name": "Black Rose Football Jersey (White #32)",
        "caption": (
            "skyyrose_brd03 white football jersey with number 32, "
            "'BLACK IS BEAUTIFUL' text across chest, black numbers with rose fill pattern, "
            "V-neck collar, short sleeves, clean white base with black accents, "
            "back has large number 32 with nameplate, "
            "Black Rose Collection by SkyyRose, luxury streetwear football jersey"
        ),
        "techflat": "br-d03-techflat.jpeg",
        # Gemini vision: br-d03-model-f/m confirmed 100%
        "model_shots": ["br-d03-model-f.webp", "br-d03-model-m.webp"],
    },
    "br-d04": {
        "trigger": "skyyrose_brd04",
        "name": "Black Rose Basketball Jersey (The Bay)",
        "caption": (
            "skyyrose_brd04 white basketball jersey with 'THE BAY' text in gold on front, "
            "circular rose logo with rose-in-clouds emblem, large grayscale rose pattern "
            "gradient fading from bottom, 'BLACK IS BEAUTIFUL' text in gold on back, "
            "V-neck sleeveless design, small gold SR patch, "
            "Black Rose Collection by SkyyRose, luxury streetwear basketball jersey"
        ),
        "techflat": "br-d04-techflat.jpeg",
        "model_shots": ["br-d04-model-f.webp", "br-d04-model-m.webp"],
    },
    # ═══ LOVE HURTS COLLECTION ═══
    "lh-002": {
        "trigger": "skyyrose_lh002",
        "name": "Love Hurts Varsity Jacket",
        "caption": (
            "skyyrose_lh002 white varsity jacket with black sleeves, "
            "'Love Hurts' in red script on front, red and white striped cuffs and hem, "
            "hooded with orange and white floral lining, snap button front closure, "
            "back features red heart wrapped in roses graphic, "
            "Love Hurts Collection by SkyyRose, passionate luxury streetwear varsity jacket"
        ),
        "techflat": "lh-002-techflat.jpeg",
        # Gemini vision: lh-004-model-f/m are ACTUALLY wearing lh-002 (100%)
        "model_shots": [
            "lh-004-model-f.webp",  # Mislabeled as lh-004, actually lh-002 (100%)
            "lh-004-model-m.webp",  # Mislabeled as lh-004, actually lh-002 (100%)
        ],
    },
    "lh-002-set": {
        "trigger": "skyyrose_lh002_set",
        "name": "Love Hurts Varsity Jacket Full Set",
        "caption": (
            "skyyrose_lh002_set Love Hurts varsity jacket displayed as full outfit set, "
            "front and back views of black and red varsity jacket with matching pants, "
            "letterman style with chenille patches, "
            "Love Hurts Collection by SkyyRose, complete streetwear set"
        ),
        "techflat": "lh-002-techflat-set.jpeg",
        "model_shots": [],
    },
    "lh-003": {
        "trigger": "skyyrose_lh003",
        "name": "Love Hurts Track Pants",
        "caption": (
            "skyyrose_lh003 black track pants with white side stripes, "
            "white drawstring waistband, embroidered red rose heart and ribbon graphic "
            "on left thigh, zippered ankle openings, two colorways available, "
            "Love Hurts Collection by SkyyRose, passionate luxury streetwear track pants"
        ),
        "techflat": "lh-003-techflat.jpeg",
        # Gemini vision: lh-002 model shots are ACTUALLY wearing lh-003 (80-90%)
        "model_shots": [
            "lh-002-back-model.webp",  # Mislabeled as lh-002, actually lh-003 (85%)
            "lh-002-front-model.webp",  # Mislabeled as lh-002, actually lh-003 (90%)
            "lh-002-model-f.webp",  # Mislabeled as lh-002, actually lh-003 (80%)
            "lh-002-model-m.webp",  # Mislabeled as lh-002, actually lh-003 (80%)
        ],
    },
    "lh-004": {
        "trigger": "skyyrose_lh004",
        "name": "Love Hurts Shorts",
        "caption": (
            "skyyrose_lh004 Love Hurts Collection athletic shorts, "
            "mesh or woven fabric, elastic waistband with drawstring, "
            "Love Hurts branding with rose motifs, side pockets, "
            "Love Hurts Collection by SkyyRose, passionate luxury streetwear shorts"
        ),
        "techflat": "lh-004-techflat.jpeg",
        "model_shots": [],  # lh-004 model shots are mislabeled (show jacket, not shorts)
    },
    "lh-004-photo": {
        "trigger": "skyyrose_lh004",
        "name": "Love Hurts Shorts (Real Photo)",
        "caption": (
            "skyyrose_lh004 Love Hurts Collection shorts real product photograph, "
            "actual fabric and construction details, "
            "Love Hurts Collection by SkyyRose, luxury streetwear shorts"
        ),
        "techflat": "lh-004-techflat-photo.jpeg",
        "model_shots": [],
    },
    "lh-005-hoodie-set": {
        "trigger": "skyyrose_lh005_hoodie",
        "name": "Love Hurts Windbreaker Hoodie Set",
        "caption": (
            "skyyrose_lh005_hoodie Love Hurts windbreaker hoodie set, "
            "zip-up windbreaker jacket with hood and matching pants, "
            "Love Hurts branding, multi-panel colorblock design, "
            "Love Hurts Collection by SkyyRose, luxury streetwear windbreaker set"
        ),
        "techflat": "lh-005-techflat-hoodie-set.jpeg",
        "model_shots": [],  # Model shot is pink/green, not red/black/white
    },
    "lh-005-purple": {
        "trigger": "skyyrose_lh005_purple",
        "name": "Love Hurts Windbreaker (Purple Colorway)",
        "caption": (
            "skyyrose_lh005_purple Love Hurts windbreaker in purple colorway, "
            "zip-up jacket with bold purple panels and Love Hurts branding, "
            "Love Hurts Collection by SkyyRose, luxury streetwear windbreaker"
        ),
        "techflat": "lh-005-techflat-purple.jpeg",
        "model_shots": [],
    },
    # ═══ SIGNATURE COLLECTION ═══
    "sg-002": {
        "trigger": "skyyrose_sg002",
        "name": "Signature Tee + Bridge Shorts (Purple)",
        "caption": (
            "skyyrose_sg002 white tee with purple rose graphic and Golden Gate Bridge "
            "nighttime photo-print shorts in purple, detailed rose explosion graphic "
            "with purple red orange and black tones on tee, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear set"
        ),
        "techflat": "sg-002-techflat.jpeg",
        # Gemini vision: sg-005 model shots are ACTUALLY wearing sg-002 (90%)
        "model_shots": [
            "sg-005-back-model.webp",  # Mislabeled as sg-005, actually sg-002 (90%)
            "sg-005-front-model.webp",  # Mislabeled as sg-005, actually sg-002 (90%)
        ],
    },
    "sg-004": {
        "trigger": "skyyrose_sg004",
        "name": "Signature Crewneck",
        "caption": (
            "skyyrose_sg004 Signature Collection crewneck sweatshirt, "
            "SkyyRose branding and graphic design on front, "
            "ribbed collar cuffs and hem, premium cotton blend, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear"
        ),
        "techflat": "sg-004-techflat.jpeg",
        "model_shots": [],  # Model shows plain blue shorts, not bridge print
    },
    "sg-005": {
        "trigger": "skyyrose_sg005",
        "name": "Signature Tee",
        "caption": (
            "skyyrose_sg005 Signature Collection t-shirt, "
            "SkyyRose branding and graphic on front, crew neck, short sleeves, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear tee"
        ),
        "techflat": "sg-005-techflat.jpeg",
        "model_shots": [],  # sg-005 model-f wears sg-002 tee, not these shorts
    },
    "sg-006": {
        "trigger": "skyyrose_sg006",
        "name": "Signature Joggers",
        "caption": (
            "skyyrose_sg006 Signature Collection jogger pants, "
            "elastic waistband with drawstring, tapered leg, side pockets, "
            "SkyyRose branding, premium cotton blend, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear joggers"
        ),
        "techflat": "sg-006-techflat.jpeg",
        "model_shots": [],  # sg-006 model is actually wearing sg-d04 mint hooded dress
    },
    "sg-007-008": {
        "trigger": "skyyrose_sg007",
        "name": "Signature Beanies (Black & Forest Green)",
        "caption": (
            "skyyrose_sg007 ribbed knit beanies with SkyyRose rose logo patch on cuff, "
            "cuffed brim style, unisex fit, four styles with different rose patches, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear beanie"
        ),
        "techflat": "sg-007-008-techflat-beanies.jpeg",
        # Gemini vision: sg-007-model-f/m confirmed 90-100%, sg-008-model-m also sg-007 (80%)
        "model_shots": [
            "sg-007-model-f.webp",  # Confirmed sg-007 (100%)
            "sg-007-model-m.webp",  # Confirmed sg-007 (90%)
            "sg-008-model-m.webp",  # Mislabeled as sg-008, actually sg-007 beanie (80%)
        ],
    },
    "sg-d01": {
        "trigger": "skyyrose_sgd01",
        "name": "Multi-Colored Windbreaker Set",
        "caption": (
            "skyyrose_sgd01 multi-colored windbreaker set with pastel V-chevron pattern, "
            "pink hood, white base jacket with colorful panels, matching pants, "
            "zip-up front, lightweight nylon fabric, small rose graphic on chest, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear windbreaker"
        ),
        "techflat": "sg-d01-techflat.jpeg",
        # Gemini vision: sg-d01-model-f/m confirmed 100%
        "model_shots": ["sg-d01-model-f.webp", "sg-d01-model-m.webp"],
    },
    "sg-d03": {
        "trigger": "skyyrose_sgd03",
        "name": "Mint Crewneck & Jogger Set",
        "caption": (
            "skyyrose_sgd03 mint green crewneck sweatshirt and jogger pants set, "
            "large purple and pink rose graphic on front of crewneck, "
            "matching mint jogger pants with small logo, ribbed cuffs and hem, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear set"
        ),
        "techflat": "sg-d03-techflat.jpeg",
        # Gemini vision: sg-d03-model-f/m confirmed 100%
        "model_shots": ["sg-d03-model-f.webp", "sg-d03-model-m.webp"],
    },
    "sg-d04": {
        "trigger": "skyyrose_sgd04",
        "name": "Mint Hooded Dress",
        "caption": (
            "skyyrose_sgd04 mint green hooded dress with large purple rose graphic on front, "
            "purple drawstrings, long sleeves, knee-length hem, "
            "relaxed oversized fit, premium cotton, "
            "Signature Collection by SkyyRose, Bay Area luxury streetwear hooded dress"
        ),
        "techflat": "sg-d04-techflat.jpeg",
        # Gemini vision: sg-d04-model-f/m confirmed 98-100%
        "model_shots": ["sg-d04-model-f.webp", "sg-d04-model-m.webp"],
    },
}


def copy_and_prepare_image(src: Path, dst_name: str, target_size: int = 1024) -> bool:
    """Copy and resize image to dataset, preserving aspect ratio with padding."""
    try:
        img = Image.open(src).convert("RGB")

        # Resize preserving aspect ratio
        img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)

        # Pad to square with white background
        if img.size[0] != target_size or img.size[1] != target_size:
            padded = Image.new("RGB", (target_size, target_size), (255, 255, 255))
            offset = ((target_size - img.size[0]) // 2, (target_size - img.size[1]) // 2)
            padded.paste(img, offset)
            img = padded

        # Save as high-quality JPEG
        output_path = IMAGES_DIR / dst_name
        if dst_name.endswith(".webp"):
            # Convert webp to jpg for training compatibility
            dst_name = dst_name.rsplit(".", 1)[0] + ".jpg"
            output_path = IMAGES_DIR / dst_name

        img.save(output_path, "JPEG", quality=95, optimize=True)
        return True
    except Exception as e:
        print(f"  WARNING: Failed to process {src.name}: {e}")
        return False


def write_caption(image_name: str, caption: str):
    """Write caption .txt file matching image name (Replicate convention)."""
    stem = Path(image_name).stem
    if image_name.endswith(".webp"):
        stem = Path(image_name).stem  # already correct
    caption_path = CAPTIONS_DIR / f"{stem}.txt"
    caption_path.write_text(caption)


def main():
    print("=" * 70)
    print("  SKYYROSE LORA V4 DATASET BUILDER")
    print("  Per-SKU trigger words + detailed tech flat captions")
    print("=" * 70)

    # Clean and recreate
    if IMAGES_DIR.exists():
        shutil.rmtree(IMAGES_DIR)
    if CAPTIONS_DIR.exists():
        shutil.rmtree(CAPTIONS_DIR)
    IMAGES_DIR.mkdir(parents=True)
    CAPTIONS_DIR.mkdir(parents=True)

    total_images = 0
    total_products = 0
    metadata_entries = []

    for sku, product in PRODUCTS.items():
        print(f"\n--- {sku}: {product['name']} ---")
        product_images = 0

        # 1. Tech flat (PRIMARY training image — this is the ground truth)
        techflat_path = PRODUCTS_DIR / product["techflat"]
        if techflat_path.exists():
            img_name = f"{sku}-techflat.jpg"
            if copy_and_prepare_image(techflat_path, img_name):
                # Tech flats get extra weight: repeat caption 3x for emphasis
                tech_caption = f"{product['caption']}, technical flat lay illustration, product design reference"
                write_caption(img_name, tech_caption)
                metadata_entries.append(
                    {
                        "file_name": img_name,
                        "text": tech_caption,
                        "sku": sku,
                        "type": "techflat",
                        "trigger": product["trigger"],
                    }
                )
                product_images += 1
                print(f"  + techflat: {product['techflat']}")
        else:
            print(f"  ! MISSING techflat: {product['techflat']}")

        # 2. Model shots (SECONDARY — only include verified good matches)
        for model_file in product["model_shots"]:
            model_path = PRODUCTS_DIR / model_file
            if model_path.exists():
                img_name = f"{sku}-{model_file.replace('.webp', '.jpg')}"
                if copy_and_prepare_image(model_path, img_name):
                    model_caption = (
                        f"{product['caption']}, fashion model wearing the garment, full body shot"
                    )
                    write_caption(img_name, model_caption)
                    metadata_entries.append(
                        {
                            "file_name": img_name,
                            "text": model_caption,
                            "sku": sku,
                            "type": "model_shot",
                            "trigger": product["trigger"],
                        }
                    )
                    product_images += 1
                    print(f"  + model: {model_file}")
            else:
                print(f"  ! MISSING model: {model_file}")

        total_images += product_images
        if product_images > 0:
            total_products += 1
        print(f"  = {product_images} images for {sku}")

    # Also check for sg-d01 alternate filename
    alt_windbreaker = PRODUCTS_DIR / "sg-d01-windbreaker-set-techflat.jpg"
    if alt_windbreaker.exists() and not (IMAGES_DIR / "sg-d01-techflat.jpg").exists():
        img_name = "sg-d01-techflat.jpg"
        if copy_and_prepare_image(alt_windbreaker, img_name):
            caption = (
                PRODUCTS["sg-d01"]["caption"]
                + ", technical flat lay illustration, product design reference"
            )
            write_caption(img_name, caption)
            metadata_entries.append(
                {
                    "file_name": img_name,
                    "text": caption,
                    "sku": "sg-d01",
                    "type": "techflat",
                    "trigger": PRODUCTS["sg-d01"]["trigger"],
                }
            )
            total_images += 1
            print("\n  + alt techflat: sg-d01-windbreaker-set-techflat.jpg")

    # Write metadata.jsonl
    metadata_path = DATASET_DIR / "metadata.jsonl"
    with open(metadata_path, "w") as f:
        for entry in metadata_entries:
            f.write(json.dumps(entry) + "\n")

    # Write dataset info
    info = {
        "version": "v4",
        "total_images": total_images,
        "total_products": total_products,
        "trigger_words": sorted(set(p["trigger"] for p in PRODUCTS.values())),
        "global_trigger": "skyyrose",
        "strategy": "per-SKU trigger words with detailed captions from tech flats",
        "resolution": 1024,
        "format": "JPEG quality 95",
        "collections": {
            "black_rose": [k for k in PRODUCTS if k.startswith("br-")],
            "love_hurts": [k for k in PRODUCTS if k.startswith("lh-")],
            "signature": [k for k in PRODUCTS if k.startswith("sg-")],
        },
    }
    info_path = DATASET_DIR / "dataset_info.json"
    with open(info_path, "w") as f:
        json.dump(info, f, indent=2)

    print("\n" + "=" * 70)
    print(f"  DATASET BUILT: {total_images} images across {total_products} products")
    print(f"  Location: {DATASET_DIR}")
    print(f"  Metadata: {metadata_path}")
    print(f"  Trigger words: {len(set(p['trigger'] for p in PRODUCTS.values()))} unique")
    print("=" * 70)

    # Summary by collection
    br_count = sum(1 for e in metadata_entries if e["sku"].startswith("br-"))
    lh_count = sum(1 for e in metadata_entries if e["sku"].startswith("lh-"))
    sg_count = sum(1 for e in metadata_entries if e["sku"].startswith("sg-"))
    print(f"\n  Black Rose:  {br_count} images")
    print(f"  Love Hurts:  {lh_count} images")
    print(f"  Signature:   {sg_count} images")

    return 0


if __name__ == "__main__":
    exit(main())
