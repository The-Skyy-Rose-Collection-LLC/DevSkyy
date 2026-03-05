#!/usr/bin/env python3
"""
Vision-based product matching: Tech Flat → Model Shot.

Uses Gemini vision to analyze each model shot and match it to the correct
tech flat / product SKU. This replaces manual (bad) human matching.

Usage:
    source .venv-lora/bin/activate
    python scripts/vision_match_products.py
"""

import base64
import json
import os
import time
from pathlib import Path

from google import genai

PROJECT_ROOT = Path(__file__).parent.parent
PRODUCTS_DIR = PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"

# Load env
for env_file in [PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.hf"]:
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    value = value.strip().strip('"').strip("'")
                    if value:
                        os.environ.setdefault(key.strip(), value)

# Tech flat catalog — what each product ACTUALLY looks like
TECH_FLATS = {
    "br-001": {"file": "br-001-techflat.jpeg", "desc": "Black crewneck & jogger set, white/gray rose graphic on front"},
    "br-003-oakland": {"file": "br-003-techflat-oakland.jpeg", "desc": "Dark green baseball jersey, GOLD trim, 'BLACK IS BEAUTIFUL' in gold"},
    "br-003-giants": {"file": "br-003-techflat-giants.jpeg", "desc": "Black baseball jersey, ORANGE trim, 'BLACK IS BEAUTIFUL' in orange"},
    "br-003-white": {"file": "br-003-techflat-white.jpeg", "desc": "White baseball jersey, black trim, 'BLACK IS BEAUTIFUL' in black"},
    "br-003-black": {"file": "br-003-techflat-black.jpeg", "desc": "Black baseball jersey, white trim, 'BLACK IS BEAUTIFUL' in white"},
    "br-007": {"file": "br-007-techflat.jpeg", "desc": "Black athletic shorts, 'OAKLAND' text, rose pattern, white side panels"},
    "br-d02": {"file": "br-d02-techflat.jpeg", "desc": "RED football jersey #80, rose fill in numbers, stripe sleeves"},
    "br-d03": {"file": "br-d03-techflat.jpeg", "desc": "WHITE football jersey #32, rose fill in numbers, black stripe sleeves"},
    "br-d04": {"file": "br-d04-techflat.jpeg", "desc": "White basketball jersey 'THE BAY' in gold, grayscale rose gradient bottom"},
    "lh-002": {"file": "lh-002-techflat.jpeg", "desc": "Varsity jacket white body black sleeves, 'Love Hurts' script, red heart/roses on back"},
    "lh-003": {"file": "lh-003-techflat.jpeg", "desc": "Track pants, two colorways (white/black waistband), small red rose logo"},
    "lh-004": {"file": "lh-004-techflat.jpeg", "desc": "White shorts with all-over red rose bouquet pattern, 'Love Hurts' script"},
    "lh-005-red": {"file": "lh-005-techflat-hoodie-set.jpeg", "desc": "Red/black/white colorblock hoodie set with matching pants"},
    "lh-005-purple": {"file": "lh-005-techflat-purple.jpeg", "desc": "Purple/pink/navy colorblock hoodie set with matching pants"},
    "sg-002": {"file": "sg-002-techflat.jpeg", "desc": "White tee with purple rose graphic + Golden Gate Bridge NIGHT shorts (purple)"},
    "sg-004": {"file": "sg-004-techflat.jpeg", "desc": "White tee with blue rose graphic + Bay Bridge DAY shorts (blue sky)"},
    "sg-005": {"file": "sg-005-techflat.jpeg", "desc": "Bay Bridge daytime photo-print mesh shorts (real product photo)"},
    "sg-006": {"file": "sg-006-techflat.jpeg", "desc": "Golden Gate Bridge nighttime photo-print shorts (real product photo)"},
    "sg-007": {"file": "sg-007-008-techflat-beanies.jpeg", "desc": "4 black beanies with different rose patches on cuff"},
    "sg-d01": {"file": "sg-d01-techflat.jpeg", "desc": "Pastel V-chevron windbreaker set, pink hood, white base, matching pants"},
    "sg-d03": {"file": "sg-d03-techflat.jpeg", "desc": "Mint green crewneck & jogger set with purple/pink rose graphic"},
    "sg-d04": {"file": "sg-d04-techflat.jpeg", "desc": "Mint green hooded DRESS (long, knee-length) with purple rose graphic, purple drawstrings"},
}


def encode_image(path: Path) -> dict:
    """Encode image as base64 for Gemini API."""
    data = path.read_bytes()
    mime = "image/jpeg" if path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"
    return {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}}


def analyze_model_shot(client, model_shot_path: Path, tech_flat_catalog: str) -> dict:
    """Ask Gemini to identify which product a model shot shows."""

    prompt = f"""You are a fashion product identification expert for SkyyRose streetwear brand.

I'm showing you a MODEL SHOT photo - a person wearing a SkyyRose product.

Your job: identify EXACTLY which product(s) the model is wearing from this catalog:

{tech_flat_catalog}

IMPORTANT RULES:
- Focus on the GARMENT the model is wearing, not the background
- Look at: color, pattern, graphics, text, garment type (jersey, hoodie, shorts, etc.)
- A model may be wearing MULTIPLE products from the catalog (e.g., a top AND bottom)
- Be SPECIFIC about colors - green/gold is NOT the same as black/orange
- If the product doesn't match ANY tech flat well, say "NO_MATCH"
- If it's a PARTIAL match (right type but wrong details), note what's different

Respond in this exact JSON format:
{{
  "primary_match": "sku or NO_MATCH",
  "primary_confidence": 0.0-1.0,
  "primary_notes": "what matches and what doesn't",
  "secondary_match": "sku of second product if model wears two, or null",
  "secondary_confidence": 0.0-1.0,
  "secondary_notes": "details about second product",
  "garment_description": "brief description of what the model is actually wearing"
}}"""

    img_data = model_shot_path.read_bytes()
    mime = "image/jpeg" if model_shot_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            {"role": "user", "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(img_data).decode()}},
            ]}
        ],
    )

    # Parse JSON from response
    text = response.text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        elif "```" in text:
            text = text[:text.rfind("```")]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": text, "primary_match": "PARSE_ERROR"}


def main():
    print("=" * 70)
    print("  VISION-BASED PRODUCT MATCHING")
    print("  Using Gemini to match model shots → tech flats")
    print("=" * 70)

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in .env.hf")
        return 1

    client = genai.Client(api_key=api_key)

    # Build catalog text
    catalog_lines = []
    for sku, info in TECH_FLATS.items():
        catalog_lines.append(f"  {sku}: {info['desc']}")
    catalog_text = "\n".join(catalog_lines)

    # Find all model shots
    model_shots = sorted(PRODUCTS_DIR.glob("*-model-*.webp")) + sorted(PRODUCTS_DIR.glob("*-model.webp"))
    # Also get front-model and back-model
    model_shots += sorted(PRODUCTS_DIR.glob("*-front-model.webp"))
    model_shots += sorted(PRODUCTS_DIR.glob("*-back-model.webp"))
    # Deduplicate
    model_shots = sorted(set(model_shots))

    print(f"\nFound {len(model_shots)} model shots to analyze\n")

    results = {}
    for i, shot_path in enumerate(model_shots):
        filename = shot_path.name
        print(f"[{i+1}/{len(model_shots)}] Analyzing {filename}...", end=" ", flush=True)

        try:
            result = analyze_model_shot(client, shot_path, catalog_text)
            results[filename] = result

            match = result.get("primary_match", "?")
            conf = result.get("primary_confidence", 0)
            desc = result.get("garment_description", "")
            secondary = result.get("secondary_match")

            status = f"{match} ({conf:.0%})"
            if secondary and secondary != "null":
                sec_conf = result.get("secondary_confidence", 0)
                status += f" + {secondary} ({sec_conf:.0%})"

            print(f"→ {status}")
            if desc:
                print(f"    {desc}")

        except Exception as e:
            print(f"ERROR: {e}")
            results[filename] = {"error": str(e), "primary_match": "ERROR"}

        time.sleep(1)  # Rate limit

    # Save results
    output_path = PROJECT_ROOT / "datasets" / "skyyrose_lora_v4" / "vision_matches.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved: {output_path}")

    # Summary
    print("\n" + "=" * 70)
    print("  MATCHING SUMMARY")
    print("=" * 70)

    # Group by assigned SKU (from filename) vs detected SKU
    mismatches = []
    matches = []
    no_matches = []

    for filename, result in sorted(results.items()):
        # Extract assumed SKU from filename (e.g., "br-001-model-f.webp" → "br-001")
        parts = filename.replace("-model-f.webp", "").replace("-model-m.webp", "")
        parts = parts.replace("-front-model.webp", "").replace("-back-model.webp", "")
        assumed_sku = parts

        detected = result.get("primary_match", "?")
        conf = result.get("primary_confidence", 0)

        if detected == "NO_MATCH" or detected == "ERROR":
            no_matches.append((filename, assumed_sku, detected))
        elif detected == assumed_sku or detected.startswith(assumed_sku):
            matches.append((filename, assumed_sku, detected, conf))
        else:
            mismatches.append((filename, assumed_sku, detected, conf))

    print(f"\n  CORRECT ({len(matches)}):")
    for fn, assumed, detected, conf in matches:
        print(f"    {fn} → {detected} ({conf:.0%})")

    print(f"\n  MISLABELED ({len(mismatches)}):")
    for fn, assumed, detected, conf in mismatches:
        print(f"    {fn} labeled as [{assumed}] but actually [{detected}] ({conf:.0%})")

    print(f"\n  NO MATCH ({len(no_matches)}):")
    for fn, assumed, detected in no_matches:
        print(f"    {fn} [{assumed}] → {detected}")

    return 0


if __name__ == "__main__":
    exit(main())
