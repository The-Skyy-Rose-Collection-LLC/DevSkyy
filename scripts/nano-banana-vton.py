#!/usr/bin/env python3
"""
Nano Banana 2 — SkyyRose Product Image Generator

Uses Gemini image generation to create front + back model shots and
branding/editorial photos for all SkyyRose products.

Outputs:
  {sku}-front-model.webp   — Model wearing garment, front-facing
  {sku}-back-model.webp    — Model wearing garment, back-facing
  {sku}-branding.webp      — Lifestyle/editorial shot matching collection aesthetic

Usage:
    source .venv-imagery/bin/activate
    python scripts/nano-banana-vton.py --dry-run
    python scripts/nano-banana-vton.py --sku br-001
    python scripts/nano-banana-vton.py --step all
    python scripts/nano-banana-vton.py --step branding
"""

import argparse
import concurrent.futures
import io
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("nano-banana-vton")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PRODUCTS_DIR = (
    PROJECT_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)

MODEL_ID = "gemini-2.5-flash-image"
FLUX_MODEL_ID = "black-forest-labs/FLUX.2-pro"
FLUX_MODEL_FREE = "black-forest-labs/FLUX.1-schnell-Free"
GPT_IMAGE_MODEL = "gpt-image-1.5"
GPT_VISION_MODEL = "gpt-4.1"
MIN_FILE_SIZE_KB = 50
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# -- Product catalog — loaded from data/product-catalog.csv at startup -------
# Catalog fields (name, collection, price, is_preorder, output_slug,
# source_override) come from the CSV.  Logo treatments and quality flags
# (BAD_SOURCE_SKUS) live below as image-pipeline-only augmentation.


def _load_catalog() -> dict:
    """Load product catalog from data/product-catalog.csv.

    Returns a dict keyed by SKU that preserves the same structure previously
    hardcoded here, so all downstream code (find_source_image, load_products,
    get_back_source) works without modification.
    """
    import csv as _csv

    catalog: dict = {}
    csv_path = PROJECT_ROOT / "data" / "product-catalog.csv"
    with csv_path.open(newline="", encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            sku = row["sku"].strip()
            if not sku:
                continue
            entry: dict = {
                "name": row["name"].strip(),
                "collection": row["collection_slug"].strip(),
                "is_preorder": row["is_preorder"].strip() == "1",
                "output_slug": row["render_output_slug"].strip() or sku,
                "is_tech_flat": row["render_is_tech_flat"].strip() == "1",
                "is_accessory": row["render_is_accessory"].strip() == "1",
            }
            if row["render_source_override"].strip():
                entry["source_override"] = row["render_source_override"].strip()
            if row["render_back_source_override"].strip():
                entry["back_source_override"] = row["render_back_source_override"].strip()
            if row["render_variant_of"].strip():
                entry["variant_of"] = row["render_variant_of"].strip()
            catalog[sku] = entry
    return catalog


PRODUCT_CATALOG = _load_catalog()

# Derived sets — no manual maintenance required; driven by CSV columns.
ACCESSORY_SKUS = {sku for sku, p in PRODUCT_CATALOG.items() if p["is_accessory"]}
TECH_FLAT_SKUS = {sku for sku, p in PRODUCT_CATALOG.items() if p["is_tech_flat"]}

# SKUs with known bad source images — skipped by default.
# Audited 2026-03-05 by visual inspection of every source file.
BAD_SOURCE_SKUS = set()  # All sources verified clean as of 2026-03-05

# -- Logo treatment metadata (real product material) -------------------------
# Used by --step composite to tell Gemini what the REAL logo looks like.
# Products not listed get a generic "match the reference" prompt.
# Logo visual reference (from brand assets — describe EXACTLY so the model renders them correctly):
#
#  ROSE-ONLY:  3D dimensional rose, layered spiral petals opening outward, curved stem with two
#              broad leaves at base; brushed rose-gold (#B76E79) metallic with specular highlights.
#              Appears as embroidery (raised thread, shadow depth) or silicone patch (smooth gloss).
#
#  SR MONOGRAM + ROSE:  Intertwined serif S and R with flowing calligraphic curves; 3D rose bloom
#              attached lower-right with short stem and leaf; rose-gold metallic finish.
#
#  SR MONOGRAM (GOLD):  Same S-R interlock, no rose — gold/champagne metallic, used as smaller
#              back-neck or secondary marks.
#
#  LOVE HURTS WORDMARK:  Bold red graffiti/bubble-script 'Love Hurts', heavy black outline and
#              shadow; thorned cracked red heart floating above the text with blood-splash drips
#              — street-art tattoo style, very high contrast.
#
#  LOVE HURTS HEART GRAPHIC:  Cracked red heart tightly wrapped in thick dark thorny branches;
#              three full red roses with green stems growing upward from the heart; blood splatter
#              dripping from bottom — cartoon tattoo art style, black outlines, vivid reds/greens.
#
#  SKYROSE COLLECTION SCRIPT:  Gold foil wordmark: 'THE' in small serifed caps; 'Skyy Rose' in
#              ornate italic cursive script; 'Collection' in spaced gold small-caps below; the 'o'
#              in 'Rose' is replaced by a small rose bloom in rose-gold.
#
#  ROSES FROM CONCRETE:  Three large roses growing upward from a broken concrete/cloud base;
#              thorny green stems, large fully-opened blooms; grey/charcoal colorway (Black Rose)
#              or red colorway — illustrative style.

LOGO_TREATMENTS = {
    # ── Black Rose Collection ────────────────────────────────────────────────
    "br-001": (
        "front chest center (~10 in): the ROSE-ONLY logo — 3D dimensional rose, layered spiral "
        "petals, curved stem with two broad leaves, brushed rose-gold metallic; embossed into "
        "fabric creating dimensional raised relief with subtle drop shadow at base"
    ),
    "br-002": (
        "left thigh: the ROSE-ONLY logo as a silicone patch — same 3D rose shape, glossy smooth "
        "finish, sharply die-cut edges, rose-gold metallic color, catches strong specular highlights"
    ),
    "br-003": (
        "front: 'BLACK IS BEAUTIFUL' bold block text across chest in white/gold; custom baseball "
        "patch at lower-hem (circular, team-style); "
        "back: large ROSE-ONLY embroidered logo centered — raised thread texture, rose-gold tone"
    ),
    "br-003-oakland": (
        "front: 'BLACK IS BEAUTIFUL' text — the letter A in 'BLACK' is black, remaining letters "
        "are gold; custom baseball patch at lower-hem; "
        "back: large ROSE-ONLY embroidered logo centered, rose-gold thread"
    ),
    "br-003-giants": (
        "front: 'BLACK IS BEAUTIFUL' block text in orange/black Giants colorway across chest; "
        "custom baseball circular patch at hem; "
        "back: large ROSE-ONLY embroidered logo centered, rose-gold thread"
    ),
    "br-003-white": (
        "front: 'BLACK IS BEAUTIFUL' block text in black on white jersey; custom baseball patch "
        "at hem; "
        "back: large ROSE-ONLY embroidered logo centered, rose-gold thread"
    ),
    "br-004": (
        "front chest center: the ROSE-ONLY logo — 3D layered spiral rose, embroidered in rose-gold "
        "thread, raised texture with visible shadow depth between petal layers"
    ),
    "br-005": (
        "right chest: ROSE-ONLY logo as a silicone cut-out patch — glossy rose-gold, dimensionally "
        "raised, precise cut edges; "
        "left side body panel (not on arm/sleeve): second ROSE-ONLY logo embroidered in thread"
    ),
    "br-006": (
        "left chest: ROSE-ONLY embroidered logo, rose-gold thread (~5 in); "
        "back panel center: large ROSE-ONLY embroidered logo (~12 in), rose-gold thread with "
        "dark shadow depth — black satin outer shell, black sherpa lining visible at cuffs and hood"
    ),
    "br-007": (
        "front waistband: tackle-twill cut-out letters 'OAKLAND' stitched in block font; "
        "throughout fabric: sublimated ROSE-ONLY graphic repeating; "
        "left exterior panel: large sublimated LOVE HURTS WORDMARK (red graffiti 'Love Hurts' "
        "with thorned heart above); mesh side panels: embroidered 'Love Hurts' text and rose marks"
    ),
    "br-008": (
        "football jersey #80 — jersey-style stitched numbers, ~8 in tall; "
        "FRONT: digit '8' has rose-gold rose fill inside the numeral, digit '0' is plain white; "
        "BACK: reversed — digit '8' is plain white, digit '0' has rose-gold rose fill; "
        "bottom-left corner: custom circular football patch"
    ),
    "br-009": (
        "football jersey #32 — jersey-style stitched numbers, ~8 in tall, white with black border; "
        "FRONT: digit '3' has rose-gold rose fill, digit '2' is plain white; "
        "BACK: reversed — digit '3' is plain white, digit '2' has rose-gold rose fill; "
        "bottom-left corner: custom circular football patch"
    ),
    "br-010": (
        "sleeveless basketball tank; front chest: 'THE BAY' in bold gold block text; "
        "below text: circular ROSE-ONLY graphic in rose-gold; "
        "lower half of jersey: grey/silver gradient rose fade sublimation; "
        "SkyyRose SR monogram (gold) at back neck; wide shoulder straps"
    ),
    "br-011": (
        "hooded hockey jersey, black-and-teal colorway; "
        "front chest: large circular rose crest (ROSE-ONLY logo in teal/cyan ring); "
        "back upper: 'BLACK IS BEAUTIFUL' in cyan/teal block text; "
        "back number: rose-filled #0 numeral in teal; "
        "hem and cuffs: gradient stripe panels in teal/cyan"
    ),
    # ── Love Hurts Collection ────────────────────────────────────────────────
    "lh-002": (
        "left thigh: LOVE HURTS HEART GRAPHIC — cracked red heart tightly wrapped in thick dark "
        "thorny branches, three full red roses with green stems growing upward from the heart, "
        "blood-splash drips at bottom, cartoon tattoo art style with heavy black outlines; "
        "comes in two colorways: white joggers with black side stripe, or black joggers with "
        "white side stripe"
    ),
    "lh-003": (
        "throughout shorts fabric: sublimated LOVE HURTS HEART GRAPHIC repeating; "
        "left exterior panel: large sublimated LOVE HURTS WORDMARK (red graffiti bubble-script "
        "'Love Hurts', heavy black outline, thorned heart above, blood-splash); "
        "mesh side panels: embroidered love-hurts text marks and rose details"
    ),
    "lh-004": (
        "front chest: LOVE HURTS WORDMARK — bold red graffiti bubble-script 'Love Hurts', "
        "heavy black outline and shadow, thorned cracked heart floating above the text; "
        "inside hood lining: sublimated LOVE HURTS HEART GRAPHIC; "
        "back center: large LOVE HURTS HEART GRAPHIC — cracked red heart wrapped in thorny "
        "branches, three red roses growing upward, blood-splash drips — dominant back print"
    ),
    "lh-006": (
        "front face of fanny pack: LOVE HURTS HEART GRAPHIC — cracked red heart tightly wrapped "
        "in dark thorny branches, three red roses with green stems growing upward from top, "
        "blood-splash drips at bottom; positioned prominently on the front leather panel, "
        "printed/embossed; the heart graphic occupies most of the front face"
    ),
    # ── Signature Collection ─────────────────────────────────────────────────
    "sg-001": (
        "entire shorts fabric: sublimated Bay Bridge panorama photo covering front and back panels; "
        "bottom-left hem: ROSE-ONLY embroidered logo in blue thread (~3 in), matching bay water tones"
    ),
    "sg-002": (
        "front chest: ROSE-ONLY embroidered logo (~6 in) in gold thread; within the rose petals: "
        "miniature Golden Gate Bridge imagery stitched into the petal faces — bridge cables and "
        "towers visible inside the bloom"
    ),
    "sg-003": (
        "entire shorts fabric: sublimated Golden Gate Bridge panorama; "
        "bottom-left hem: ROSE-ONLY embroidered logo in purple thread (~3 in)"
    ),
    "sg-004": (
        "front chest center: SR MONOGRAM + ROSE — intertwined serif S-R with rose bloom on right, "
        "rose-gold metallic embroidered (~5 in); "
        "back neck: small SR MONOGRAM (gold) embroidered label, ~1.5 in"
    ),
    "sg-005": (
        "front chest: ROSE-ONLY embroidered logo (~6 in) in navy/gold thread; within rose petals: "
        "miniature Bay Bridge imagery stitched into petal faces — bridge span and cables visible"
    ),
    "sg-006": (
        "front chest center: ROSE-ONLY logo in lavender thread (~6 in) — same 3D layered spiral "
        "rose shape, embroidered, lavender-to-purple gradient thread on mint/lavender colorblock fabric"
    ),
    "sg-007": (
        "brim fold, slightly left of center: ROSE-ONLY logo as a small silicone patch (~2 in) — "
        "die-cut rose shape, smooth glossy finish; "
        "comes in three colorways: rose-gold/red rose, grey-black rose, or purple rose"
    ),
    "sg-009": (
        "front chest left: ROSE-ONLY embroidered logo (~5 in) in red thread — "
        "raised thread texture against cream sherpa; "
        "lining: white sherpa fleece visible at cuffs, collar, and hem"
    ),
    "sg-011": (
        "front chest: THE SKYROSE COLLECTION SCRIPT — gold foil wordmark: 'THE' in small serifed "
        "caps, 'Skyy Rose' in ornate italic cursive, 'Collection' in spaced caps; the 'o' in Rose "
        "is a small rose bloom; printed small (~4 in wide) on clean white fabric"
    ),
    "sg-012": (
        "front chest: THE SKYROSE COLLECTION SCRIPT — same gold foil wordmark as sg-011; "
        "printed small (~4 in wide) on rich orchid fabric — gold contrasts strongly against purple"
    ),
    "sg-013": (
        "front chest center: ROSE-ONLY embroidered logo in lavender thread (~6 in), same spiral "
        "rose shape, raised thread depth; "
        "back neck exterior: small SR MONOGRAM (gold) embroidered, ~1.5 in"
    ),
    "sg-014": (
        "left thigh panel: ROSE-ONLY embroidered logo (~4 in) in lavender thread — "
        "positioned mid-thigh on the mint/lavender colorblock sweatpants"
    ),
    # ── Kids Capsule ─────────────────────────────────────────────────────────
    "kids-001": (
        "left chest: ROSE-ONLY embroidered logo (~3 in) in black thread on red fabric; "
        "left thigh of jogger: matching ROSE-ONLY embroidered logo (~3 in); "
        "right sleeve: circular woven patch (~2.5 in) — white background, black outline border, "
        "black rose center, 'Skyy Rose' arched text on top half, 'Collection' on bottom half"
    ),
    "kids-002": (
        "left chest: ROSE-ONLY embroidered logo (~3 in) in black thread on purple fabric; "
        "left thigh of jogger: matching ROSE-ONLY embroidered logo (~3 in); "
        "right sleeve: circular woven patch (~2.5 in) — white background, black outline border, "
        "black rose center, 'Skyy Rose' arched text on top half, 'Collection' on bottom half"
    ),
}


def get_back_source(sku: str, product: dict) -> Path | None:
    """Return a back-specific source image path for a SKU, if available.

    Checks product catalog for a back_source_override filename. If the file is
    a 2-panel techflat (width > height * 1.5), crops the RIGHT half using PIL
    and returns the path to a temp file. Otherwise returns the path as-is.

    Returns None if no back source is configured or the file doesn't exist.
    """
    import tempfile

    info = PRODUCT_CATALOG.get(sku, {})
    back_override = info.get("back_source_override")
    if not back_override:
        return None

    # Check PRODUCTS_DIR first, then source-products tree
    _source_dir = PROJECT_ROOT / "skyyrose" / "assets" / "images" / "source-products"
    back_path = PRODUCTS_DIR / back_override
    if not back_path.exists():
        back_path = _source_dir / back_override
    if not back_path.exists():
        log.warning("back_source_override %s not found for %s", back_override, sku)
        return None

    # Check if this is a 2-panel techflat (side-by-side front+back layout)
    try:
        from PIL import Image

        img = Image.open(back_path)
        w, h = img.size
        if w > h * 1.1:
            # Wide image — crop right half (the back panel)
            right_half = img.crop((w // 2, 0, w, h))
            tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
            right_half.save(tmp.name, format="JPEG", quality=95)
            tmp.close()
            log.debug("Cropped right half of 2-panel techflat %s -> %s", back_override, tmp.name)
            return Path(tmp.name)
    except Exception as exc:
        log.warning("Could not inspect/crop back source %s: %s", back_override, exc)

    return back_path


def find_source_image(sku: str) -> Path | None:
    """Find the best available source image for a SKU.

    Checks source_override first, then falls back to globbing by output_slug.
    For products with no source (only existing model renders), tries to use
    the existing front-model render as a reference for regeneration.
    """
    info = PRODUCT_CATALOG.get(sku, {})

    # Check for explicit source override in catalog
    if "source_override" in info:
        override_path = PRODUCTS_DIR / info["source_override"]
        if override_path.exists():
            return override_path
        log.warning("source_override %s not found for %s", info["source_override"], sku)

    # Fall back to globbing by output_slug (product-name-based filenames)
    slug = info.get("output_slug", sku)
    extensions = (".webp", ".jpg", ".jpeg", ".png")
    candidates = []
    for ext in extensions:
        candidates.extend(PRODUCTS_DIR.glob(f"{slug}*{ext}"))

    # Filter out generated model shots — we want flat-lay/product source only
    source_candidates = [
        p
        for p in candidates
        if "-front-model" not in p.stem
        and "-back-model" not in p.stem
        and "-branding" not in p.stem
    ]
    if source_candidates:
        # Prefer source/techflat/product files, then shorter filenames
        source_candidates.sort(
            key=lambda p: (
                "source" not in p.stem and "techflat" not in p.stem and "product" not in p.stem,
                len(p.name),
            )
        )
        return source_candidates[0]

    # Last resort: use existing front-model render as reference
    front_model = PRODUCTS_DIR / f"{slug}-front-model.webp"
    if front_model.exists():
        log.info("Using existing front-model render as source for %s", sku)
        return front_model

    return None


def load_products(sku_filter: str | None = None, include_bad: bool = False) -> list[dict]:
    """Load product catalog, resolve source images, apply filter.

    By default skips SKUs in BAD_SOURCE_SKUS. Pass --include-bad or
    a specific --sku to override.
    """
    products = []
    skus = [sku_filter] if sku_filter else sorted(PRODUCT_CATALOG.keys())

    for sku in skus:
        if sku not in PRODUCT_CATALOG:
            log.error("Unknown SKU: %s", sku)
            continue

        # Skip known-bad source images unless explicitly requested
        if sku in BAD_SOURCE_SKUS and not include_bad and not sku_filter:
            log.info("SKIP %s: bad source image (use --include-bad to override)", sku)
            continue

        info = PRODUCT_CATALOG[sku]
        src = find_source_image(sku)

        products.append(
            {
                "sku": sku,
                "name": info["name"],
                "collection": info["collection"],
                "output_slug": info.get("output_slug", sku),
                "source_image": src,
                "is_accessory": sku in ACCESSORY_SKUS,
                "is_preorder": info.get("is_preorder", False),
                "is_variant": "variant_of" in info,
            }
        )

    return products


def get_together_client():
    """Create a Together AI client for FLUX generation."""
    key = os.environ.get("TOGETHER_API_KEY")
    if not key:
        # Try .env.hf
        env_path = PROJECT_ROOT / ".env.hf"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("TOGETHER_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        log.error("No TOGETHER_API_KEY found. Set it in .env.hf or export TOGETHER_API_KEY")
        return None
    from together import Together

    return Together(api_key=key)


def get_openai_client():
    """Create an OpenAI client for vision analysis + gpt-image generation."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env_path = PROJECT_ROOT / ".env.hf"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
                    break
    if not key:
        log.error("No OPENAI_API_KEY found. Set it in .env.hf or export OPENAI_API_KEY")
        return None
    from openai import OpenAI

    return OpenAI(api_key=key)


def get_api_key() -> str:
    """Load Google API key from config/settings.py or environment."""
    # Try the project's central settings first
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from config.settings import GOOGLE_API_KEY

        if GOOGLE_API_KEY:
            log.info("Loaded GOOGLE_API_KEY from config/settings.py")
            return GOOGLE_API_KEY
    except (ImportError, Exception) as exc:
        log.debug("Could not import config.settings: %s", exc)

    # Fall back to env vars
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key:
        log.info("Loaded API key from environment variable")
        return key

    # Fall back to .env.hf
    env_path = PROJECT_ROOT / ".env.hf"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GOOGLE_API_KEY="):
                key = line.split("=", 1)[1].strip()
                if key:
                    log.info("Loaded GOOGLE_API_KEY from .env.hf")
                    return key

    log.error(
        "No Google API key found. Set GOOGLE_API_KEY in .env / .env.hf "
        "or export GOOGLE_API_KEY / GEMINI_API_KEY"
    )
    sys.exit(1)


# -- Prompt templates --------------------------------------------------------
# All prompts are functions that take the product name so the model knows
# EXACTLY what garment it's looking at (not just "this garment").


def front_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — FRONT VIEW ONLY.\n"
        "The provided image is the source tech flat. Reproduce every detail exactly.\n\n"
        "VIEW RULE: Show ONLY the front panel. "
        "Do NOT render the back of the garment. "
        "Do NOT show through to the reverse side. "
        "One side visible — the front.\n\n"
        "PRESENTATION: No model, no person, no mannequin. "
        "Garment floating naturally on an invisible form, full 3D shape and drape. "
        "Clean white/light gray studio background, subtle floor shadow. "
        "Professional e-commerce lighting — soft key light upper-left, fill right, "
        "rim light for edge definition.\n\n"
        "FIDELITY: Match the reference exactly — same colors, same text, same numbers, "
        "same logo placement, same panels, same stripes. Change NOTHING." + ANTI_HALLUCINATION
    )


def back_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — BACK VIEW ONLY.\n"
        "The provided image is the back-panel tech flat. Reproduce every detail exactly.\n\n"
        "VIEW RULE: Show ONLY the back panel. "
        "Do NOT render the front of the garment. "
        "Do NOT show through to the front side. "
        "One side visible — the back. Garment facing away from camera.\n\n"
        "PRESENTATION: No model, no person, no mannequin. "
        "Garment floating naturally on an invisible form, back-facing, full 3D drape. "
        "Clean white/light gray studio background, subtle floor shadow. "
        "Professional e-commerce lighting.\n\n"
        "FIDELITY: Match the back reference exactly — same colors, same text, same numbers, "
        "same logo placement, same back graphics. Change NOTHING." + ANTI_HALLUCINATION
    )


def accessory_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — FRONT VIEW.\n"
        "The provided image is the source reference. Reproduce every detail exactly.\n\n"
        "PRESENTATION: No model, no person. "
        "Item displayed cleanly on white/light gray studio background with subtle shadow. "
        "Professional product photography lighting.\n\n"
        "FIDELITY: Match the reference exactly — same colors, same details. Change NOTHING."
        + ANTI_HALLUCINATION
    )


BRANDING_TEMPLATES = {
    "black-rose": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a dark, moody editorial setting — black marble "
        "surfaces, dramatic shadows, rose gold accent lighting. Gothic luxury "
        "aesthetic. The {name} must be 100% identical to the reference — same "
        "colors, same cut, same logos. Do NOT change the garment type. Deep "
        "blacks, dramatic contrast, cathedral of fashion. Rose gold (#B76E79) "
        "tones in the lighting. Cinematic composition, 3/4 body shot."
    ),
    "love-hurts": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a passionate, romantic editorial setting — red "
        "roses, velvet textures, warm dramatic lighting. The {name} must be "
        "100% identical to the reference — same colors, same cut, same logos. "
        "Do NOT change the garment type. Rich reds and deep burgundy tones, "
        "luxury castle backdrop. Rose petals, silk fabric in background. "
        "Cinematic composition, 3/4 body shot."
    ),
    "signature": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a Bay Area urban editorial setting — golden hour "
        "light, city skyline or Golden Gate Bridge silhouette in background. "
        "The {name} must be 100% identical to the reference — same colors, "
        "same cut, same logos. Do NOT change the garment type. Warm golden "
        "tones, California luxury vibes. Golden (#D4AF37) accent lighting. "
        "Cinematic composition, 3/4 body shot."
    ),
    "kids-capsule": (
        "The reference image shows a {name}. Generate a CHILD model (age 8-12) "
        "wearing this EXACT {name}, front-facing, playful yet premium editorial "
        "photography, bright studio lighting, clean background. The {name} must "
        "be 100% identical to the reference — same colors, same cut, same logos. "
        "Do NOT change the garment type. Vibrant, youthful energy with luxury "
        "quality. Cinematic composition, 3/4 body shot."
    ),
}

ACCESSORY_BRANDING_TEMPLATES = {
    "love-hurts": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "passionate, romantic editorial setting — red roses, velvet textures, "
        "warm dramatic lighting. The {name} must be 100% identical to the "
        "reference. Do NOT change the item type. Product photography meets "
        "luxury editorial. Cinematic lighting."
    ),
    "signature": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "Bay Area urban editorial setting — golden hour light, warm golden "
        "tones. The {name} must be 100% identical to the reference. Do NOT "
        "change the item type. California luxury vibes, premium product "
        "photography. Golden (#D4AF37) accents."
    ),
}

# -- Anti-hallucination constraints ------------------------------------------
# Appended to EVERY prompt to prevent AI from inventing details.

ANTI_HALLUCINATION = (
    "\n\nSTRICT RULES — NON-NEGOTIABLE:\n"
    "• Render ONLY the side specified (front or back). Never show both sides simultaneously.\n"
    "• Do NOT add text, logos, patches, or branding absent from the reference image.\n"
    "• Do NOT invent pockets, panels, zippers, or design details not in the reference.\n"
    "• Do NOT change the garment type, silhouette, or cut.\n"
    "• Do NOT add sponsor logos, team names, league marks, or athlete names.\n"
    "• Do NOT alter colors — match hex values from the reference exactly.\n"
    "• Do NOT change stitching, seam placement, or construction.\n"
    "• If a detail is unclear in the reference, leave it out — never guess.\n"
    "• This is a luxury fashion brand. Accuracy is the only standard."
)

ENHANCED_PROMPT_SUFFIX = (
    " CRITICAL: The item in the output MUST be pixel-accurate to the "
    "reference. Do not change any colors, patterns, logos, or design "
    "elements. Do NOT substitute a different garment type. "
    "This is a luxury fashion brand — accuracy is everything." + ANTI_HALLUCINATION
)


# -- Composite prompts --------------------------------------------------------
# For --step composite: merge real product branding into AI lifestyle shots.


def composite_prompt(name: str, sku: str, view: str = "front") -> str:
    """Build a prompt for compositing real branding onto an AI lifestyle shot."""
    treatment = LOGO_TREATMENTS.get(sku, "")
    treatment_note = f" The real product's logo/branding is {treatment}." if treatment else ""
    return (
        f"I am providing TWO images. "
        f"IMAGE 1 (the AI render): A professional fashion photo of a model wearing a {name}. "
        f"This is the composition, pose, lighting, and background you MUST keep. "
        f"IMAGE 2 (the REAL product): The actual {name} showing the TRUE logo, branding, "
        f"and material treatment.{treatment_note} "
        f"YOUR TASK: Generate a new image that keeps the EXACT same model, pose, body position, "
        f"lighting, and background from Image 1 — but corrects the garment's logo and branding "
        f"details to match Image 2 exactly. Study the logo in Image 2 closely: how does light "
        f"hit it? Does it cast shadows? Is it raised or flat? Does it have a glossy or matte finish? "
        f"Does the fabric change texture around the logo? Reproduce these VISUAL properties exactly. "
        f"Pay close attention to: logo placement, size, how light interacts with the logo surface, "
        f"shadow depth, edge sharpness, surface finish (matte/glossy/textured), and color accuracy. "
        f"Everything about the model and background stays IDENTICAL. Only the garment branding changes."
    )


def generate_composite(
    client,
    ai_render_path: Path,
    source_image_path: Path,
    prompt: str,
) -> bytes | None:
    """Generate a composite image: AI lifestyle + real product branding.

    Sends both images to Gemini and asks it to merge accurate branding
    from the real product into the AI lifestyle shot's composition.

    Returns WebP image bytes on success, None on failure.
    """
    from google.genai import types
    from PIL import Image as PILImage

    # Load both images
    ai_img = PILImage.open(ai_render_path).convert("RGB")
    src_img = enhance_source_image(source_image_path)

    try:
        response = _call_with_deadline(
            client.models.generate_content,
            model=MODEL_ID,
            contents=[
                "IMAGE 1 — the AI-generated lifestyle photo (keep this composition):",
                ai_img,
                "IMAGE 2 — the REAL product reference (match this branding exactly):",
                src_img,
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
    except concurrent.futures.TimeoutError:
        log.warning("Composite generation timed out after %ds (socket hang)", _GENAI_CALL_TIMEOUT)
        return None
    except Exception as exc:
        log.error("Composite API call failed: %s", exc)
        return None

    if not response or not response.parts:
        log.warning("Empty response from composite API")
        return None

    for part in response.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            raw = part.inline_data.data
            if isinstance(raw, str):
                import base64

                raw = base64.b64decode(raw)
            # Convert to WebP
            img = PILImage.open(io.BytesIO(raw))
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=92)
            return buf.getvalue()

    log.warning("No image in composite response")
    return None


def render3d_front_prompt(name: str) -> str:
    """Prompt for photorealistic 3D product render — front view."""
    return (
        f"The reference image shows a {name}. Create a photorealistic 3D "
        f"product render of this EXACT {name}, FRONT VIEW. "
        "NO model, NO person, NO mannequin visible — just the garment "
        "itself displayed naturally showing its 3D shape, volume, and fabric "
        "drape as if floating on an invisible form. "
        "Light gray (#E8E8E8) studio background with subtle floor reflection. "
        "Professional product photography lighting — soft key light from "
        "upper-left, fill light from right, slight rim light for edge definition. "
        "The garment must be a PIXEL-PERFECT replica of the reference — "
        "same exact colors, same exact graphics, same exact logos, same exact "
        "text, same exact patterns, same exact stitching. "
        "Change absolutely NOTHING about the design." + ANTI_HALLUCINATION
    )


def render3d_back_prompt(name: str) -> str:
    """Prompt for photorealistic 3D product render — back view."""
    return (
        f"The reference image shows a {name}. Create a photorealistic 3D "
        f"product render of this EXACT {name}, BACK VIEW. "
        "NO model, NO person, NO mannequin visible — just the garment "
        "itself displayed naturally showing its 3D shape, volume, and fabric "
        "drape as if floating on an invisible form. Show the BACK side. "
        "Light gray (#E8E8E8) studio background with subtle floor reflection. "
        "Professional product photography lighting. "
        "The garment must be a PIXEL-PERFECT replica of the reference — "
        "same exact colors, same exact back graphics, same exact logos, "
        "same exact text, same exact patterns. "
        "Change absolutely NOTHING about the design." + ANTI_HALLUCINATION
    )


def render3d_branding_prompt(name: str, collection: str) -> str:
    """Prompt for 3D product render with branding context."""
    collection_vibe = {
        "black-rose": (
            "Dark, moody studio background — black marble surface, "
            "dramatic shadows, rose gold accent lighting (#B76E79). "
            "Gothic luxury aesthetic."
        ),
        "love-hurts": (
            "Warm romantic studio — deep red velvet backdrop, "
            "rose gold and burgundy accent lighting."
        ),
        "signature": (
            "Golden hour California studio — warm golden backdrop, "
            "Bay Area luxury vibes, gold (#D4AF37) accent lighting."
        ),
    }
    vibe = collection_vibe.get(collection, collection_vibe["black-rose"])
    return (
        f"The reference image is a flat design mockup of a {name}. "
        f"Convert this EXACT design into a photorealistic 3D product render. "
        f"The garment on an invisible mannequin with natural 3D shape. "
        f"{vibe} "
        f"Every detail MUST be preserved exactly from the design: colors, "
        f"logos, numbers, text, stripes, patches. Do NOT change anything. "
        f"Cinematic product photography, slight floor reflection." + ANTI_HALLUCINATION
    )


# -- Image enhancement -------------------------------------------------------

ENHANCE_TARGET_PX = 1536  # Upscale short edge to this for a crisp reference


def enhance_source_image(image_path: Path):
    """Upscale, sharpen, and boost contrast on the source image.

    Returns a PIL Image ready to be sent as reference.
    """
    from PIL import Image, ImageEnhance, ImageFilter

    img = Image.open(image_path).convert("RGB")

    # Upscale so the short edge is at least ENHANCE_TARGET_PX
    w, h = img.size
    short_edge = min(w, h)
    if short_edge < ENHANCE_TARGET_PX:
        scale = ENHANCE_TARGET_PX / short_edge
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        log.debug("Upscaled %s: %dx%d -> %dx%d", image_path.name, w, h, new_w, new_h)

    # Sharpen to bring out logo/print details
    img = img.filter(ImageFilter.SHARPEN)

    # Slight contrast boost so colors pop in the reference
    img = ImageEnhance.Contrast(img).enhance(1.15)

    # Slight color saturation boost
    img = ImageEnhance.Color(img).enhance(1.1)

    return img


# -- Socket-hang guard -------------------------------------------------------
# Issue #1893: gemini-2.5-flash can stall at socket level indefinitely.
# http_options timeout does NOT catch this — the socket stays open with no data.
# ThreadPoolExecutor.result(timeout=N) enforces a wall-clock deadline regardless.
_GENAI_CALL_TIMEOUT = 90  # seconds wall-clock per attempt
_GENAI_MAX_RETRIES = 2  # retry socket hangs with backoff before giving up
_GENAI_BACKOFF_BASE = 10  # seconds; backoff = base * 2^attempt


def _call_with_deadline(fn, *args, timeout: int = _GENAI_CALL_TIMEOUT, **kwargs):
    """Run fn(*args, **kwargs) with a wall-clock deadline and exponential backoff.

    Retries up to _GENAI_MAX_RETRIES times on socket hang (TimeoutError).
    Raises the last TimeoutError if all retries exhausted.
    """
    last_exc = None
    for attempt in range(_GENAI_MAX_RETRIES + 1):
        if attempt > 0:
            backoff = _GENAI_BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning(
                "Socket hang retry %d/%d — waiting %ds before retry",
                attempt,
                _GENAI_MAX_RETRIES,
                backoff,
            )
            time.sleep(backoff)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(fn, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError as exc:
                last_exc = exc
                log.warning(
                    "API call timed out after %ds (attempt %d/%d)",
                    timeout,
                    attempt + 1,
                    _GENAI_MAX_RETRIES + 1,
                )
    raise last_exc


# -- Image generation --------------------------------------------------------


def generate_image(
    client,
    source_image_path: Path,
    prompt: str,
    attempt: int = 1,
) -> bytes | None:
    """Generate a single image using Gemini.

    Returns WebP image bytes on success, None on failure.
    """
    from google.genai import types

    src_img = enhance_source_image(source_image_path)

    full_prompt = prompt
    if attempt > 1:
        full_prompt += ENHANCED_PROMPT_SUFFIX

    try:
        response = _call_with_deadline(
            client.models.generate_content,
            model=MODEL_ID,
            contents=[
                "REFERENCE PHOTO of the exact product (study every detail):",
                src_img,
                full_prompt,
            ],
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspectRatio="3:4",
                ),
            ),
        )
    except concurrent.futures.TimeoutError:
        log.warning(
            "generate_image timed out after %ds (socket hang — skipping)", _GENAI_CALL_TIMEOUT
        )
        return None
    except Exception as exc:
        log.error("API call failed (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.parts:
        log.warning("Empty response from API (attempt %d)", attempt)
        return None

    for part in response.parts:
        if part.inline_data:
            # as_image() returns a genai Image — .save() takes a file path
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                tmp_path = tmp.name
            part.as_image().save(tmp_path)
            data = Path(tmp_path).read_bytes()
            Path(tmp_path).unlink(missing_ok=True)
            return data

    log.warning("No image in response parts (attempt %d)", attempt)
    return None


def flux_render_prompt(
    name: str,
    view: str,
    source_desc: str = "",
) -> str:
    """Build a FLUX prompt for converting tech flats to photorealistic product shots.

    FLUX excels at: text rendering, color fidelity, and prompt adherence.
    """
    view_label = {
        "front": "FRONT VIEW",
        "back": "BACK VIEW",
        "branding": "cinematic editorial shot",
        "render3d_front": "FRONT VIEW",
        "render3d_back": "BACK VIEW",
        "render3d_branding": "cinematic editorial shot",
    }.get(view, "FRONT VIEW")

    base = (
        f"Professional e-commerce product photography of a {name} "
        f"on an invisible ghost mannequin, {view_label}. "
    )

    if source_desc:
        base += f"{source_desc} "

    if "branding" in view:
        base += (
            "Dark moody studio background — black marble surface, dramatic "
            "shadows, rose gold (#B76E79) accent lighting. Gothic luxury "
            "aesthetic. Cinematic composition, slight floor reflection. "
        )
    else:
        base += (
            "Light gray (#E8E8E8) studio background with subtle floor "
            "reflection. Professional product photography lighting — soft "
            "key light from upper-left, fill light from right, slight rim "
            "light. "
        )

    base += (
        "Photorealistic fabric texture showing natural 3D shape and drape. "
        "All text, logos, and embroidery must be perfectly legible and "
        "spelled exactly as described. Luxury streetwear brand, premium quality. "
        "4K resolution, sharp details."
    )

    base += ANTI_HALLUCINATION
    return base


def generate_image_flux(
    together_client,
    prompt: str,
    source_image_path: Path | None = None,
    attempt: int = 1,
    use_free: bool = False,
) -> bytes | None:
    """Generate an image using FLUX via Together AI.

    If source_image_path is provided, encodes it as a reference hint in the prompt.
    Returns WebP image bytes on success, None on failure.
    """
    import base64

    model = FLUX_MODEL_FREE if use_free else FLUX_MODEL_ID

    # Build the prompt — FLUX doesn't have native reference-image in the basic API,
    # but FLUX.2 supports it via Together's image input parameter
    full_prompt = prompt
    if attempt > 1:
        full_prompt += (
            " CRITICAL: Reproduce the garment EXACTLY as described. "
            "Do not change colors, patterns, or text."
        )

    try:
        gen_kwargs = {
            "model": model,
            "prompt": full_prompt,
            "width": 768,
            "height": 1024,  # 3:4 aspect ratio to match other providers
            "response_format": "b64_json",  # Avoid 403 on URL downloads
        }

        response = together_client.images.generate(**gen_kwargs)
    except Exception as exc:
        log.error("FLUX API call failed (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.data:
        log.warning("Empty FLUX response (attempt %d)", attempt)
        return None

    img_data = response.data[0]

    # Together returns either b64_json or url
    raw_bytes = None
    if hasattr(img_data, "b64_json") and img_data.b64_json:
        raw_bytes = base64.b64decode(img_data.b64_json)
    elif hasattr(img_data, "url") and img_data.url:
        import urllib.request

        try:
            req = urllib.request.Request(img_data.url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()
        except urllib.error.HTTPError as e:
            log.error("Image URL download failed (%s %s)", e.code, e.reason)
            return None

    if not raw_bytes:
        log.warning("No image data in FLUX response (attempt %d)", attempt)
        return None

    # Convert to WebP for consistency with other providers
    try:
        from PIL import Image

        pil_img = Image.open(io.BytesIO(raw_bytes))
        buf = io.BytesIO()
        pil_img.save(buf, format="WEBP", quality=92)
        return buf.getvalue()
    except Exception:
        return raw_bytes


def analyze_source_image(openai_client, source_path: Path, product_name: str) -> dict | None:
    """Vision pre-pass: analyze source image with GPT-4.1 to extract structured details.

    Returns a dict with garment details (colors, text, materials, branding, construction)
    that can be injected into generation prompts for better accuracy.
    """
    import base64

    if not source_path or not source_path.exists():
        return None

    b64_image = base64.b64encode(source_path.read_bytes()).decode("utf-8")
    mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"

    try:
        response = openai_client.responses.create(
            model=GPT_VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"You are analyzing a product photo for '{product_name}' "
                                "from the luxury streetwear brand SkyyRose. "
                                "Extract ONLY what you can see — do NOT guess or invent details.\n\n"
                                "Return valid JSON with these fields:\n"
                                "{\n"
                                '  "garment_type": "e.g. hoodie, jersey, shorts",\n'
                                '  "colors": ["list of hex color codes you see, e.g. #B76E79"],\n'
                                '  "color_names": ["human-readable color names, e.g. rose gold, black"],\n'
                                '  "text_on_garment": ["exact text visible, e.g. BLACK IS BEAUTIFUL"],\n'
                                '  "numbers_on_garment": ["any jersey numbers, e.g. #80"],\n'
                                '  "logos_branding": ["SR monogram", "rose embroidery", etc],\n'
                                '  "material": "mesh, fleece, satin, etc",\n'
                                '  "construction": ["V-neck", "sleeveless", "hood attached", etc],\n'
                                '  "patches": ["gold NFL patch on sleeve", etc],\n'
                                '  "design_elements": ["stripe trim on sleeves", "gradient hem", etc],\n'
                                '  "overall_description": "1-2 sentence summary"\n'
                                "}\n\n"
                                "ONLY return the JSON object, no markdown fences or explanation."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{mime};base64,{b64_image}",
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        log.error("Vision analysis failed for %s: %s", product_name, exc)
        return None

    # Parse the JSON response
    text = response.output_text.strip()
    # Strip markdown fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        log.warning("Could not parse vision analysis as JSON for %s", product_name)
        log.debug("Raw vision response: %s", text[:500])
        return {"overall_description": text}


def analysis_to_prompt_detail(analysis: dict) -> str:
    """Convert vision analysis JSON into a prompt-friendly description string."""
    parts = []

    if analysis.get("color_names"):
        parts.append(f"Colors: {', '.join(analysis['color_names'])}.")

    if analysis.get("colors"):
        hex_list = ", ".join(analysis["colors"][:5])
        parts.append(f"Exact hex: {hex_list}.")

    if analysis.get("text_on_garment"):
        texts = ", ".join(f'"{t}"' for t in analysis["text_on_garment"])
        parts.append(f"Text on garment: {texts} — must be spelled exactly.")

    if analysis.get("numbers_on_garment"):
        nums = ", ".join(analysis["numbers_on_garment"])
        parts.append(f"Numbers: {nums}.")

    if analysis.get("logos_branding"):
        parts.append(f"Branding: {', '.join(analysis['logos_branding'])}.")

    if analysis.get("material"):
        parts.append(f"Material: {analysis['material']}.")

    if analysis.get("construction"):
        parts.append(f"Construction: {', '.join(analysis['construction'])}.")

    if analysis.get("patches"):
        parts.append(f"Patches/tags: {', '.join(analysis['patches'])}.")

    if analysis.get("design_elements"):
        parts.append(f"Design: {', '.join(analysis['design_elements'])}.")

    return " ".join(parts)


def generate_image_gpt(
    openai_client,
    prompt: str,
    source_image_path: Path | None = None,
    attempt: int = 1,
) -> bytes | None:
    """Generate an image using GPT-Image-1.5 with optional reference image.

    Supports reference-based editing: give it a source photo and instructions,
    it preserves details (text, logos, colors) while transforming context.
    Returns WebP image bytes on success, None on failure.
    """
    import base64

    full_prompt = prompt
    if attempt > 1:
        full_prompt += (
            " CRITICAL: Reproduce every detail EXACTLY. Do not change any "
            "colors, text, logos, or patterns from the reference."
        )

    try:
        kwargs = {
            "model": GPT_IMAGE_MODEL,
            "prompt": full_prompt,
            "size": "1024x1536",  # 2:3 portrait (closest to 3:4)
            "quality": "high",
        }

        # If source image provided, use image editing mode
        if source_image_path and source_image_path.exists():
            kwargs["image"] = [
                {
                    "type": "base64",
                    "media_type": (
                        "image/jpeg"
                        if source_image_path.suffix.lower() in (".jpg", ".jpeg")
                        else "image/webp"
                    ),
                    "data": base64.b64encode(source_image_path.read_bytes()).decode("utf-8"),
                }
            ]

        response = openai_client.images.generate(**kwargs)
    except Exception as exc:
        log.error("GPT-Image API call failed (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.data:
        log.warning("Empty GPT-Image response (attempt %d)", attempt)
        return None

    img_data = response.data[0]

    raw_bytes = None
    if hasattr(img_data, "b64_json") and img_data.b64_json:
        raw_bytes = base64.b64decode(img_data.b64_json)
    elif hasattr(img_data, "url") and img_data.url:
        import urllib.request

        try:
            req = urllib.request.Request(img_data.url)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_bytes = resp.read()
        except urllib.error.HTTPError as e:
            log.error("Image URL download failed (%s %s)", e.code, e.reason)
            return None

    if not raw_bytes:
        log.warning("No image data in GPT-Image response (attempt %d)", attempt)
        return None

    # Convert to WebP for consistency
    try:
        from PIL import Image

        pil_img = Image.open(io.BytesIO(raw_bytes))
        buf = io.BytesIO()
        pil_img.save(buf, format="WEBP", quality=92)
        return buf.getvalue()
    except Exception:
        return raw_bytes


def qa_check_image(
    openai_client,
    source_path: Path,
    generated_path: Path,
    product_name: str,
    analysis: dict | None = None,
) -> dict:
    """Post-generation QA: compare source vs generated image using GPT-4.1 vision.

    Returns dict with pass/fail status and detailed comparison notes.
    """
    import base64

    src_b64 = base64.b64encode(source_path.read_bytes()).decode("utf-8")
    gen_b64 = base64.b64encode(generated_path.read_bytes()).decode("utf-8")
    src_mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"
    gen_mime = "image/webp"  # all generated images are webp

    analysis_context = ""
    if analysis:
        if analysis.get("text_on_garment"):
            analysis_context += f"\nExpected text: {analysis['text_on_garment']}"
        if analysis.get("colors"):
            analysis_context += f"\nExpected colors: {analysis['colors']}"
        if analysis.get("logos_branding"):
            analysis_context += f"\nExpected branding: {analysis['logos_branding']}"

    try:
        response = openai_client.responses.create(
            model=GPT_VISION_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                f"You are a QA inspector for SkyyRose luxury streetwear.\n"
                                f"Product: {product_name}\n"
                                f"{analysis_context}\n\n"
                                "IMAGE 1 = SOURCE (the real product)\n"
                                "IMAGE 2 = GENERATED (AI-created product shot)\n\n"
                                "Compare them and return JSON:\n"
                                "{\n"
                                '  "pass": true/false,\n'
                                '  "color_match": true/false,\n'
                                '  "text_match": true/false (or null if no text),\n'
                                '  "garment_type_match": true/false,\n'
                                '  "logo_match": true/false,\n'
                                '  "issues": ["list of specific problems"],\n'
                                '  "confidence": 0.0-1.0,\n'
                                '  "notes": "brief summary"\n'
                                "}\n\n"
                                "Be STRICT. Flag any hallucinated text, wrong colors, "
                                "missing logos, or garment type changes. "
                                "ONLY return JSON, no markdown."
                            ),
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{src_mime};base64,{src_b64}",
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:{gen_mime};base64,{gen_b64}",
                        },
                    ],
                }
            ],
        )
    except Exception as exc:
        log.error("QA check failed for %s: %s", product_name, exc)
        return {"pass": False, "issues": [f"QA API error: {exc}"], "confidence": 0.0}

    text = response.output_text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"pass": False, "issues": ["Could not parse QA response"], "notes": text[:300]}


def gemini_vision_compare(
    client,
    source_path: Path,
    generated_bytes: bytes,
    product_name: str,
    garment_spec: str = "",
    view: str = "front",
) -> dict:
    """Compare generated render against source tech flat using Gemini Flash vision.

    Called inline within the generation retry loop. On failure, issues are injected
    as corrective feedback into the next attempt's prompt, triggering regeneration.

    Returns dict with pass/fail, score (0-100), and specific issues for prompt feedback.
    """
    from google.genai import types as genai_types

    src_bytes = source_path.read_bytes()
    src_mime = "image/jpeg" if source_path.suffix.lower() in (".jpg", ".jpeg") else "image/webp"
    spec_context = f"\nProduct spec: {garment_spec}" if garment_spec else ""

    view_label = view.upper()
    view_rule = (
        "IMAGE 2 shows the FRONT of the garment only. "
        "Do NOT flag missing back-panel content — the back is intentionally not shown."
        if view == "front"
        else "IMAGE 2 shows the BACK of the garment only. "
        "Do NOT flag missing front-panel content — the front is intentionally not shown."
    )

    prompt = (
        f"You are a strict QA inspector comparing a SOURCE tech flat vs an AI-generated "
        f"{view_label} VIEW render of '{product_name}'.{spec_context}\n\n"
        "IMAGE 1 = SOURCE tech flat (ground truth — what the product MUST look like)\n"
        f"IMAGE 2 = GENERATED {view_label} VIEW render (evaluate against IMAGE 1)\n\n"
        f"IMPORTANT: {view_rule}\n\n"
        "Evaluate ONLY these criteria:\n"
        "  1. BASE COLORS — garment color(s) must match source exactly\n"
        "  2. TEXT — all visible text must be correct (content, color, placement)\n"
        "  3. NUMBERS — jersey numbers must be exact\n"
        "  4. LOGOS — presence, placement, and color must match (not 3D material texture)\n"
        "  5. GARMENT TYPE — must be the correct garment (jersey, hoodie, shorts, etc.)\n"
        "  6. DESIGN ELEMENTS — panels, stripes, patterns must match\n\n"
        "DO NOT penalize for: logo embossing/3D depth, fabric drape, lighting/shadows, "
        "material gloss level, or content from the opposite side of the garment.\n\n"
        "Return ONLY this JSON (no markdown):\n"
        "{\n"
        '  "pass": true/false,\n'
        '  "score": 0-100,\n'
        '  "color_match": true/false,\n'
        '  "text_match": true/false,\n'
        '  "garment_match": true/false,\n'
        "score=100 means all 6 criteria match. Be strict on colors, text, numbers."
    )

    # Native JSON schema output — guaranteed valid, no markdown stripping needed.
    _vision_schema = {
        "type": "OBJECT",
        "properties": {
            "pass": {"type": "BOOLEAN"},
            "score": {"type": "INTEGER"},
            "color_match": {"type": "BOOLEAN"},
            "text_match": {"type": "BOOLEAN"},
            "garment_match": {"type": "BOOLEAN"},
            "logo_match": {"type": "BOOLEAN"},
            "issues": {"type": "ARRAY", "items": {"type": "STRING"}},
            "notes": {"type": "STRING"},
        },
        "required": [
            "pass",
            "score",
            "color_match",
            "text_match",
            "garment_match",
            "logo_match",
            "issues",
            "notes",
        ],
    }

    try:
        response = _call_with_deadline(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[
                prompt,
                genai_types.Part(inline_data=genai_types.Blob(mime_type=src_mime, data=src_bytes)),
                genai_types.Part(
                    inline_data=genai_types.Blob(mime_type="image/webp", data=generated_bytes)
                ),
            ],
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_vision_schema,
            ),
        )
    except concurrent.futures.TimeoutError:
        log.warning(
            "Vision compare timed out after %ds (socket hang) — treating as pass to avoid infinite retry",
            _GENAI_CALL_TIMEOUT,
        )
        return {
            "pass": True,
            "score": -1,
            "issues": [],
            "notes": "Vision timeout — socket hang (Issue #1893)",
        }
    except Exception as exc:
        log.error("Vision compare failed: %s", exc)
        return {"pass": True, "score": 0, "issues": [], "notes": f"Vision API error: {exc}"}

    return json.loads(response.text)


def quality_gate(image_bytes: bytes, sku: str, view: str) -> bool:
    """Check if generated image passes quality requirements."""
    size_kb = len(image_bytes) / 1024
    if size_kb < MIN_FILE_SIZE_KB:
        log.warning(
            "REJECT %s %s: %.1fKB < %dKB minimum",
            sku,
            view,
            size_kb,
            MIN_FILE_SIZE_KB,
        )
        return False
    log.info("PASS %s %s: %.1fKB", sku, view, size_kb)
    return True


def get_prompt(product: dict, view: str) -> str:
    """Select the right prompt for a product + view combination."""
    is_accessory = product["is_accessory"]
    collection = product["collection"]
    name = product["name"]

    # 3D product render mode
    if view == "render3d_front":
        return render3d_front_prompt(name)
    if view == "render3d_back":
        return render3d_back_prompt(name)
    if view == "render3d_branding":
        return render3d_branding_prompt(name, collection)

    if view == "branding":
        if is_accessory:
            tpl = ACCESSORY_BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES[collection])
            return tpl.format(name=name)
        return BRANDING_TEMPLATES[collection].format(name=name)

    if is_accessory:
        return accessory_prompt(name)

    if view == "front":
        return front_prompt(name)
    return back_prompt(name)


def get_output_filename(sku: str, view: str) -> str:
    """Map view to output filename using product-name-based slugs."""
    info = PRODUCT_CATALOG.get(sku, {})
    slug = info.get("output_slug", sku)

    if view.startswith("render3d_"):
        suffix = view.replace("render3d_", "")
        return f"{slug}-{suffix}-model.webp"
    return f"{slug}-{view}-model.webp" if view != "branding" else f"{slug}-branding.webp"


def process_product(
    client,
    product: dict,
    views: list[str],
    engine: str = "gemini",
    together_client=None,
    openai_client=None,
    analysis: dict | None = None,
) -> dict:
    """Generate images for a single product. Returns results dict.

    engine: "gemini" | "flux" | "gpt-image" | "auto"
    In auto mode:
      - FLUX.2 for TECH_FLAT_SKUS (tech flat → photorealistic)
      - Gemini for everything else (reference-based ghost mannequin)
    """
    sku = product["sku"]
    name = product["name"]
    src = product["source_image"]
    results = {"sku": sku, "name": name, "views": {}}

    # Determine which engine to use for this product
    use_flux = engine == "flux" or (engine == "auto" and sku in TECH_FLAT_SKUS)
    use_gpt_image = engine == "gpt-image"

    # Validate engine requirements
    if use_gpt_image and not openai_client:
        log.warning("SKIP %s: gpt-image requested but no OpenAI client", sku)
        use_gpt_image = False
    if use_flux and not together_client:
        log.warning("SKIP %s: FLUX requested but no Together client (missing API key?)", sku)
        use_flux = False

    if not use_flux and not use_gpt_image and not src:
        log.warning("SKIP %s (%s): no source image found", sku, name)
        results["status"] = "no_source"
        return results

    if use_flux and not src:
        log.info("FLUX text-to-image mode for %s (no source image)", sku)

    engine_label = "GPT-Image-1.5" if use_gpt_image else "FLUX.2" if use_flux else "Gemini"

    # Build analysis-enhanced prompt detail.
    # Priority: passed-in analysis dict > garment-analysis.json cache > nothing.
    analysis_detail = ""
    if analysis:
        analysis_detail = analysis_to_prompt_detail(analysis)
        log.info("Vision analysis (passed-in) available for %s — enhancing prompts", sku)
    else:
        # Auto-load from garment-analysis.json (written by vision_batch.py)
        ga_path = PROJECT_ROOT / "skyyrose" / "assets" / "data" / "garment-analysis.json"
        if ga_path.exists():
            try:
                ga_data = json.loads(ga_path.read_text(encoding="utf-8"))
                ga_entry = ga_data.get("products", {}).get(sku)
                if ga_entry and ga_entry.get("garmentAnalysis"):
                    analysis_detail = f"PRE-VISION SPEC: {ga_entry['garmentAnalysis'][:600]}"
                    log.info("Loaded garment-analysis.json spec for %s", sku)
            except Exception as exc:
                log.debug("Could not load garment-analysis.json for %s: %s", sku, exc)
    log.info("Engine: %s for %s", engine_label, sku)

    for view in views:
        # Accessories skip back-model view
        if product["is_accessory"] and view == "back":
            log.info("SKIP %s back view (accessory)", sku)
            results["views"][view] = "skipped_accessory"
            continue

        out_path = PRODUCTS_DIR / get_output_filename(sku, view)
        log.info("Generating %s %s (%s) [%s]...", sku, view, name, engine_label)

        # For back view, use back-specific source if available
        view_src = src
        has_back_ref = False  # True only when we have a dedicated back reference image
        if view == "back":
            back_src = get_back_source(sku, PRODUCT_CATALOG.get(sku, {}))
            if back_src:
                view_src = back_src
                has_back_ref = True
                log.info("Using back source for %s: %s", sku, back_src.name)
            else:
                log.debug(
                    "%s has no back_source_override — back vision compare skipped (plain back)", sku
                )

        success = False
        vision_feedback = ""  # Corrective feedback from vision compare — injected on retry
        best_image_bytes: bytes | None = None  # Best result by vision score across all attempts
        best_vision_score: int = -1
        for attempt in range(1, MAX_RETRIES + 1):
            if use_gpt_image:
                prompt = get_prompt(product, view)
                if analysis_detail:
                    prompt += f" VERIFIED DETAILS: {analysis_detail}"
                if vision_feedback:
                    prompt += f" {vision_feedback}"
                image_bytes = generate_image_gpt(
                    openai_client,
                    prompt,
                    view_src,
                    attempt,
                )
            elif use_flux:
                prompt = flux_render_prompt(name, view, source_desc=analysis_detail)
                if vision_feedback:
                    prompt += f" {vision_feedback}"
                image_bytes = generate_image_flux(
                    together_client,
                    prompt,
                    view_src,
                    attempt,
                )
            else:
                prompt = get_prompt(product, view)
                if analysis_detail:
                    prompt += f" VERIFIED DETAILS: {analysis_detail}"
                if vision_feedback:
                    prompt += f" {vision_feedback}"
                image_bytes = generate_image(client, view_src, prompt, attempt)

            if image_bytes and quality_gate(image_bytes, sku, view):
                # ── Vision compare: generated render vs source tech flat ──────
                # Compare the render against the source design. On failure, inject
                # specific issues as corrective feedback and retry generation.
                # Skip for back views without a dedicated back reference — the front
                # techflat is not a valid comparison target for a plain back.
                run_vision = view_src and (view != "back" or has_back_ref)
                if run_vision:
                    logo_spec = LOGO_TREATMENTS.get(sku, "")
                    vision = gemini_vision_compare(
                        client, view_src, image_bytes, name, logo_spec, view
                    )
                    v_score = vision.get("score", 100)
                    v_pass = vision.get("pass", True)
                    v_issues = vision.get("issues", [])
                    log.info(
                        "VISION %s %s: %s score=%d%s",
                        sku,
                        view,
                        "PASS" if v_pass else "FAIL",
                        v_score,
                        f" | {'; '.join(v_issues[:2])}" if v_issues else "",
                    )
                    if not v_pass and attempt < MAX_RETRIES:
                        vision_feedback = (
                            "CRITICAL CORRECTIONS — fix ALL of the following before anything else: "
                            + " | ".join(v_issues)
                            + " Match the source image exactly. Do not change anything not listed."
                        )
                        log.info(
                            "Vision FAIL — retry %d/%d with corrective feedback",
                            attempt + 1,
                            MAX_RETRIES,
                        )
                        time.sleep(RETRY_DELAY_SEC)
                        continue  # Regenerate with feedback injected
                # ── Vision passed (or no-source) — save ──────────────────────
                out_path.write_bytes(image_bytes)
                log.info(
                    "SAVED %s (%.1fKB) [%s]", out_path.name, len(image_bytes) / 1024, engine_label
                )
                results["views"][view] = "success"
                success = True
                break

            if attempt < MAX_RETRIES:
                log.info(
                    "Retry %d/%d for %s %s...",
                    attempt + 1,
                    MAX_RETRIES,
                    sku,
                    view,
                )
                time.sleep(RETRY_DELAY_SEC)

        if not success:
            log.error("FAILED %s %s after %d attempts", sku, view, MAX_RETRIES)
            results["views"][view] = "failed"

        # Rate limiting between API calls
        time.sleep(2)

    skippable = {"skipped_accessory"}
    view_statuses = list(results["views"].values())
    if all(v == "success" or v in skippable for v in view_statuses):
        results["status"] = "success"
    elif any(v == "success" for v in view_statuses):
        results["status"] = "partial"
    else:
        results["status"] = "failed"

    return results


# -- CLI commands ------------------------------------------------------------


def resolve_views(step: str) -> list[str]:
    """Map --step argument to list of views."""
    mapping = {
        "front": ["front"],
        "back": ["back"],
        "branding": ["branding"],
        "models": ["front", "back"],
        "all": ["front", "back", "branding"],
        "render3d": ["render3d_front", "render3d_back", "render3d_branding"],
        "render3d_front": ["render3d_front"],
        "render3d_back": ["render3d_back"],
    }
    return mapping[step]


def cmd_dry_run(args):
    """List all products and their source images."""
    products = load_products(args.sku, include_bad=args.include_bad)
    views = resolve_views(args.step)

    print(f"\n{'SKU':<10} {'Name':<45} {'Source Image':<40} {'Status'}")
    print("-" * 120)

    found = 0
    missing = 0
    for p in products:
        src = p["source_image"]
        if src:
            src_str = src.name
            status = "ACCESSORY" if p["is_accessory"] else "READY"
            found += 1
        else:
            src_str = "---"
            status = "NO SOURCE"
            missing += 1

        print(f"{p['sku']:<10} {p['name']:<45} {src_str:<40} {status}")

    # Count actual images to generate
    img_count = 0
    for p in products:
        if not p["source_image"]:
            continue
        for v in views:
            if p["is_accessory"] and v == "back":
                continue
            img_count += 1

    print(f"\nTotal: {len(products)} | Ready: {found} | Missing source: {missing}")
    print(f"Views: {', '.join(views)}")
    print(f"Images to generate: {img_count}")


def cmd_analyze(args):
    """Run vision pre-pass only — analyze source images without generating."""
    openai_client = get_openai_client()
    if not openai_client:
        log.error("OpenAI client required for --analyze. Set OPENAI_API_KEY.")
        sys.exit(1)

    products = load_products(args.sku, include_bad=args.include_bad)
    analyses = {}

    log.info("Starting vision analysis for %d products...", len(products))

    for i, product in enumerate(products, 1):
        sku = product["sku"]
        src = product["source_image"]
        if not src:
            log.warning("[%d/%d] SKIP %s: no source image", i, len(products), sku)
            continue

        log.info("[%d/%d] Analyzing %s (%s)...", i, len(products), sku, product["name"])
        analysis = analyze_source_image(openai_client, src, product["name"])

        if analysis:
            analyses[sku] = analysis
            desc = analysis.get("overall_description", "no description")
            colors = analysis.get("color_names", [])
            text = analysis.get("text_on_garment", [])
            print(f"  {sku:<10} {product['name']:<35} colors={colors}  text={text}")
            print(f"  {'':>10} {desc[:80]}")
        else:
            print(f"  {sku:<10} {product['name']:<35} ANALYSIS FAILED")

        time.sleep(1)  # rate limit

    # Save analysis results
    analysis_path = PROJECT_ROOT / "scripts" / "nano-banana-analysis.json"
    with open(analysis_path, "w") as f:
        json.dump(analyses, f, indent=2)
    print(f"\nAnalysis saved to {analysis_path}")
    print(f"Analyzed: {len(analyses)}/{len(products)} products")

    return analyses


def cmd_composite(args):
    """Composite real branding onto AI-generated lifestyle shots.

    For each product, takes the existing AI render (front-model.webp) and the
    real product source image, sends both to Gemini, and asks it to fix the
    logo/branding to match the real material treatment (embossed, silicone
    rubber, etc.) while keeping the lifestyle composition.
    """
    from google import genai

    api_key = get_api_key()
    client = genai.Client(api_key=api_key, http_options={"timeout": 300000})  # 5 min in ms
    products = load_products(args.sku, include_bad=args.include_bad)

    # Determine which views to composite
    composite_views = ["front"]
    if args.step == "composite_all":
        composite_views = ["front", "back", "branding"]

    log.info(
        "Starting composite: %d products, views=%s, model=%s",
        len(products),
        composite_views,
        MODEL_ID,
    )

    all_results = []
    success_count = 0
    skip_count = 0

    for i, product in enumerate(products, 1):
        sku = product["sku"]
        name = product["name"]
        source = product["source_image"]

        if not source:
            log.warning("[%d/%d] SKIP %s: no source image", i, len(products), sku)
            all_results.append({"sku": sku, "name": name, "status": "no_source"})
            skip_count += 1
            continue

        results = {"sku": sku, "name": name, "views": {}}

        for view in composite_views:
            # Find the existing AI render
            view_suffix = {
                "front": "front-model.webp",
                "back": "back-model.webp",
                "branding": "branding.webp",
            }[view]
            ai_render = PRODUCTS_DIR / f"{sku}-{view_suffix}"

            if not ai_render.exists():
                log.warning(
                    "[%d/%d] SKIP %s %s: no AI render at %s",
                    i,
                    len(products),
                    sku,
                    view,
                    ai_render.name,
                )
                results["views"][view] = "no_ai_render"
                continue

            log.info(
                "[%d/%d] Compositing %s %s — merging real branding...",
                i,
                len(products),
                sku,
                view,
            )

            prompt = composite_prompt(name, sku, view)
            image_bytes = None

            for attempt in range(1, MAX_RETRIES + 1):
                image_bytes = generate_composite(client, ai_render, source, prompt)

                if image_bytes and quality_gate(image_bytes, sku, f"composite_{view}"):
                    break

                if attempt < MAX_RETRIES:
                    log.info("Retry %d/%d for %s %s", attempt, MAX_RETRIES, sku, view)
                    time.sleep(RETRY_DELAY_SEC)
                image_bytes = None

            if image_bytes:
                # Save as composite version (don't overwrite originals)
                out_path = PRODUCTS_DIR / f"{sku}-composite-{view}.webp"
                out_path.write_bytes(image_bytes)
                size_kb = len(image_bytes) / 1024
                log.info(
                    "  -> Saved %s (%.0fKB)",
                    out_path.name,
                    size_kb,
                )
                results["views"][view] = "success"
            else:
                log.error("  FAILED %s %s after %d attempts", sku, view, MAX_RETRIES)
                results["views"][view] = "failed"

            # Rate limit
            time.sleep(3)

        # Status
        view_statuses = list(results["views"].values())
        if all(v == "success" for v in view_statuses):
            results["status"] = "success"
            success_count += 1
        elif any(v == "success" for v in view_statuses):
            results["status"] = "partial"
            success_count += 1
        else:
            results["status"] = "failed"

        all_results.append(results)

    # Summary
    log.info("=" * 60)
    log.info(
        "COMPOSITE COMPLETE: %d/%d products, %d skipped",
        success_count,
        len(products) - skip_count,
        skip_count,
    )

    # Save results
    results_path = PROJECT_ROOT / "scripts" / "nano-banana-composite-results.json"
    with open(results_path, "w") as f:
        json.dump(
            {
                "model": MODEL_ID,
                "step": args.step,
                "total": len(products),
                "results": all_results,
            },
            f,
            indent=2,
        )
    log.info("Results saved to %s", results_path)


def cmd_generate(args):
    """Generate images."""
    from google import genai

    api_key = get_api_key()
    client = genai.Client(api_key=api_key, http_options={"timeout": 300000})  # 5 min in ms
    products = load_products(args.sku, include_bad=args.include_bad)
    views = resolve_views(args.step)
    engine = args.engine

    # Initialize Together client for FLUX if needed
    together_client = None
    if engine in ("flux", "auto"):
        together_client = get_together_client()
        if engine == "flux" and not together_client:
            log.error("FLUX engine requested but no Together API key. Aborting.")
            sys.exit(1)
        if engine == "auto" and not together_client:
            log.warning("No Together API key — TECH_FLAT_SKUS will fall back to Gemini")

    # Initialize OpenAI client for gpt-image engine or --analyze/--qa
    openai_client = None
    if engine == "gpt-image" or args.analyze or args.qa:
        openai_client = get_openai_client()
        if engine == "gpt-image" and not openai_client:
            log.error("GPT-Image engine requested but no OpenAI API key. Aborting.")
            sys.exit(1)

    engine_label = {
        "gemini": f"Gemini ({MODEL_ID})",
        "flux": f"FLUX.2 ({FLUX_MODEL_ID})",
        "gpt-image": f"GPT-Image ({GPT_IMAGE_MODEL})",
        "auto": (
            f"Auto (FLUX for {len(TECH_FLAT_SKUS)} tech-flat SKUs, Gemini for everything else)"
        ),
    }[engine]

    log.info(
        "Starting generation: %d products, views=%s, engine=%s",
        len(products),
        views,
        engine_label,
    )

    # -- Phase 1: Vision Pre-Pass (if --analyze) --
    analyses = {}
    if args.analyze and openai_client:
        log.info("=== PHASE 1: Vision Pre-Pass ===")
        # Try loading cached analysis first
        analysis_path = PROJECT_ROOT / "scripts" / "nano-banana-analysis.json"
        if analysis_path.exists() and not args.sku:
            log.info("Loading cached analysis from %s", analysis_path)
            with open(analysis_path) as f:
                analyses = json.load(f)
            log.info("Loaded %d cached analyses", len(analyses))
        else:
            for i, product in enumerate(products, 1):
                src = product["source_image"]
                if not src:
                    continue
                log.info(
                    "[%d/%d] Analyzing %s...",
                    i,
                    len(products),
                    product["sku"],
                )
                result = analyze_source_image(openai_client, src, product["name"])
                if result:
                    analyses[product["sku"]] = result
                time.sleep(1)
            # Cache the analysis
            with open(analysis_path, "w") as f:
                json.dump(analyses, f, indent=2)
            log.info("Saved %d analyses to %s", len(analyses), analysis_path)

        log.info("=== PHASE 2: Generation (with enhanced prompts) ===")

    # -- Phase 2: Generation --
    all_results = []
    for i, product in enumerate(products, 1):
        sku = product["sku"]
        use_flux = engine == "flux" or (engine == "auto" and sku in TECH_FLAT_SKUS)
        use_gpt_image = engine == "gpt-image"
        if product["source_image"] or use_flux or use_gpt_image:
            pass  # OK to proceed
        elif not product["source_image"]:
            log.warning(
                "[%d/%d] SKIP %s: no source image",
                i,
                len(products),
                sku,
            )
            all_results.append({"sku": sku, "name": product["name"], "status": "no_source"})
            continue

        log.info(
            "[%d/%d] Processing %s (%s)",
            i,
            len(products),
            sku,
            product["name"],
        )
        result = process_product(
            client,
            product,
            views,
            engine=engine,
            together_client=together_client,
            openai_client=openai_client,
            analysis=analyses.get(sku),
        )
        all_results.append(result)

        if i < len(products):
            time.sleep(3)

    # -- Phase 3: QA Pass (if --qa) --
    qa_results = {}
    if args.qa and openai_client:
        log.info("=== PHASE 3: Quality Audit ===")
        qa_pass = 0
        qa_fail = 0
        for result in all_results:
            sku = result["sku"]
            if result.get("status") != "success":
                continue
            src = find_source_image(sku)
            if not src:
                continue
            for view, status in result.get("views", {}).items():
                if status != "success":
                    continue
                gen_path = PRODUCTS_DIR / get_output_filename(sku, view)
                if not gen_path.exists():
                    continue
                log.info("QA checking %s %s...", sku, view)
                qa = qa_check_image(
                    openai_client,
                    src,
                    gen_path,
                    result["name"],
                    analyses.get(sku),
                )
                qa_results[f"{sku}_{view}"] = qa
                passed = qa.get("pass", False)
                confidence = qa.get("confidence", 0)
                issues = qa.get("issues", [])
                icon = "PASS" if passed else "FAIL"
                print(
                    f"  [{icon}] {sku} {view} "
                    f"(confidence: {confidence:.0%}) "
                    f"{'| '.join(issues[:2]) if issues else 'clean'}"
                )
                if passed:
                    qa_pass += 1
                else:
                    qa_fail += 1
                time.sleep(1)

        print(f"\nQA Results: {qa_pass} passed, {qa_fail} failed")

    # -- Summary --
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)

    counts = {}
    for r in all_results:
        s = r.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    parts = [f"{k.title()}: {v}" for k, v in sorted(counts.items())]
    print(" | ".join(parts))
    print()

    for r in all_results:
        icon = {
            "success": "OK",
            "partial": "PARTIAL",
            "failed": "FAIL",
            "no_source": "SKIP",
        }.get(r.get("status", "?"), "?")
        views_str = ""
        if "views" in r:
            views_str = " | ".join(f"{v}={s}" for v, s in r["views"].items())
        print(f"  [{icon:>7}] {r['sku']:<10} {r['name']:<40} {views_str}")

    # Save results log
    log_path = PROJECT_ROOT / "scripts" / "nano-banana-results.json"
    result_data = {
        "model": MODEL_ID,
        "step": args.step,
        "engine": engine,
        "analyze": args.analyze,
        "qa": args.qa,
        "total": len(all_results),
        "results": all_results,
    }
    if qa_results:
        result_data["qa_results"] = qa_results
    with open(log_path, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"\nResults saved to {log_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Nano Banana 2 — Generate product images for SkyyRose"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List products and source images without generating",
    )
    parser.add_argument(
        "--sku",
        type=str,
        default=None,
        help="Process a single SKU (e.g. br-001)",
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=[
            "front",
            "back",
            "branding",
            "models",
            "all",
            "render3d",
            "render3d_front",
            "render3d_back",
            "composite",
            "composite_all",
        ],
        default="all",
        help=(
            "What to generate: front, back, branding, models (front+back), all, "
            "render3d (3D product shots), composite (fix logos on front renders), "
            "composite_all (fix logos on all renders)"
        ),
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["gemini", "flux", "gpt-image", "auto"],
        default="auto",
        help=(
            "Image generation engine: gemini (reference-based), "
            "flux (FLUX.2 via Together AI, tech flat conversion), "
            "gpt-image (GPT-Image-1.5, reference editing + text), "
            "auto (FLUX for tech-flat SKUs, Gemini for everything else — default)"
        ),
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override Gemini model ID",
    )
    parser.add_argument(
        "--include-bad",
        action="store_true",
        help="Include SKUs with known bad source images (normally skipped)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help=(
            "Run GPT-4.1 vision pre-pass on source images before generation. "
            "Extracts colors, text, logos, materials and injects into prompts "
            "for more accurate renders. Results cached to nano-banana-analysis.json."
        ),
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Run vision analysis ONLY (no generation). Saves to nano-banana-analysis.json.",
    )
    parser.add_argument(
        "--qa",
        action="store_true",
        help=(
            "Run GPT-4.1 vision QA after generation — compares source vs output "
            "to flag hallucinated text, wrong colors, or missing details."
        ),
    )

    args = parser.parse_args()

    global MODEL_ID
    if args.model:
        MODEL_ID = args.model

    if args.dry_run:
        cmd_dry_run(args)
    elif args.analyze_only:
        cmd_analyze(args)
    elif args.step in ("composite", "composite_all"):
        cmd_composite(args)
    else:
        cmd_generate(args)


if __name__ == "__main__":
    main()
