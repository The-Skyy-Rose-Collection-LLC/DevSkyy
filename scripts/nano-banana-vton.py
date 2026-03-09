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
IMAGEN_MODEL_ID = "imagen-4.0-ultra-generate-001"
FLUX_MODEL_ID = "black-forest-labs/FLUX.2-pro"
FLUX_MODEL_FREE = "black-forest-labs/FLUX.1-schnell-Free"
GPT_IMAGE_MODEL = "gpt-image-1.5"
GPT_VISION_MODEL = "gpt-4.1"
MIN_FILE_SIZE_KB = 50
MAX_RETRIES = 3
RETRY_DELAY_SEC = 5

# -- Product catalog (SOURCE OF TRUTH: products.csv) -------------------------
# Every SKU, name, and collection comes directly from the canonical CSV.
# Do NOT add products here that are not in products.csv.

PRODUCT_CATALOG = {
    # ── Black Rose Collection ──────────────────────────────────────────────
    # Every SKU has explicit source_override to prevent auto-glob picking up
    # AI-generated outputs (*-model-*.webp) as source images (feedback loop).
    "br-001": {
        "name": "BLACK Rose Crewneck",
        "collection": "black-rose",
        "source_override": "br-001-techflat-v4.jpg",
    },
    "br-002": {
        "name": "BLACK Rose Joggers",
        "collection": "black-rose",
        "source_override": "br-002-joggers-source.jpg",
    },
    "br-003": {
        "name": "BLACK is Beautiful Jersey",
        "collection": "black-rose",
        "source_override": "br-003-jersey-front-techflat.jpg",
    },
    "br-004": {
        "name": "BLACK Rose Hoodie",
        "collection": "black-rose",
        "source_override": "br-004-hoodie-product.jpg",
    },
    "br-005": {
        "name": "BLACK Rose Hoodie — Signature Edition",
        "collection": "black-rose",
        "source_override": "br-005-hoodie-ltd-source.jpg",
    },
    "br-006": {
        "name": "BLACK Rose Sherpa Jacket",
        "collection": "black-rose",
        "source_override": "br-006-sherpa-product.jpg",
    },
    "br-007": {
        "name": "BLACK Rose × Love Hurts Basketball Shorts",
        "collection": "black-rose",
        "source_override": "br-007-shorts-front-source.jpg",
    },
    "br-008": {
        "name": "Women's BLACK Rose Hooded Dress",
        "collection": "black-rose",
        "source_override": "br-008-hooded-dress.webp",
    },
    # ── Love Hurts Collection ──────────────────────────────────────────────
    "lh-001": {
        "name": "The Fannie",
        "collection": "love-hurts",
        "source_override": "lh-001-fannie-pack-photo.jpg",
    },
    "lh-002": {
        "name": "Love Hurts Joggers",
        "collection": "love-hurts",
        "source_override": "lh-002-joggers-variants.jpg",
    },
    "lh-003": {
        "name": "Love Hurts Basketball Shorts",
        "collection": "love-hurts",
        "source_override": "lh-003-shorts-front-closeup.jpg",
    },
    "lh-004": {
        "name": "Love Hurts Varsity Jacket",
        "collection": "love-hurts",
        "source_override": "lh-004-varsity-source.jpg",
    },
    "lh-005": {
        "name": "Love Hurts Windbreaker",
        "collection": "love-hurts",
        "source_override": "lh-005-bomber.webp",
    },
    # ── Signature Collection ───────────────────────────────────────────────
    "sg-001": {
        "name": "The Bay Set",
        "collection": "signature",
        "source_override": "sg-001-bay-set.webp",
    },
    "sg-002": {
        "name": "Stay Golden Set",
        "collection": "signature",
        "source_override": "sg-002-techflat-v4.jpg",
    },
    "sg-003": {
        "name": "The Signature Tee",
        "collection": "signature",
        "source_override": "sg-003.webp",
    },
    "sg-004": {
        "name": "The Signature Hoodie",
        "collection": "signature",
        "source_override": "sg-004-signature-hoodie.webp",
    },
    "sg-005": {
        "name": "Stay Golden Tee",
        "collection": "signature",
        "source_override": "sg-005-stay-golden-tee.webp",
    },
    "sg-006": {
        "name": "Mint & Lavender Hoodie",
        "collection": "signature",
        "source_override": "sg-006-hoodie-source.jpg",
    },
    "sg-007": {
        "name": "The Signature Beanie",
        "collection": "signature",
        "source_override": "sg-007-beanie-source.jpg",
    },
    "sg-008": {
        "name": "Signature Beanie (Forest Green)",
        "collection": "signature",
        "source_override": "sg-008-beanie-green.jpg",
    },
    "sg-009": {
        "name": "The Sherpa Jacket",
        "collection": "signature",
        "source_override": "sg-009-sherpa-jacket.webp",
    },
    "sg-010": {
        "name": "The Bridge Series Shorts",
        "collection": "signature",
        "source_override": "sg-010-bridge-shorts-variants.jpg",
    },
    "sg-011": {
        "name": "Original Label Tee (White)",
        "collection": "signature",
        "source_override": "sg-011-label-tee-white.webp",
    },
    "sg-012": {
        "name": "Original Label Tee (Orchid)",
        "collection": "signature",
        "source_override": "sg-012-label-tee-orchid.webp",
    },
    # ── Pre-Order Products ─────────────────────────────────────────────────
    "po-001": {
        "name": "Red #80 Football Jersey",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-red.jpg",
        "is_preorder": True,
    },
    "po-002": {
        "name": '"THE BAY" Basketball Tank',
        "collection": "black-rose",
        "source_override": "br-design-basketball-jersey.jpg",
        "is_preorder": True,
    },
    "po-003": {
        "name": "White #32 Football Jersey",
        "collection": "black-rose",
        "source_override": "br-design-football-jersey-white.jpg",
        "is_preorder": True,
    },
    "po-004": {
        "name": "Black & Teal Hockey Jersey",
        "collection": "black-rose",
        "source_override": "br-design-hockey-jersey.jpg",
        "is_preorder": True,
    },
    "po-005": {
        "name": "Purple GG Bridge Mesh Shorts",
        "collection": "signature",
        "source_override": "po-005-bridge-shorts-source.jpg",
        "is_preorder": True,
    },
    "po-006": {
        "name": "Black Rose Crewneck & Joggers",
        "collection": "black-rose",
        "source_override": "po-006-techflat.jpg",
        "is_preorder": True,
    },
    "po-007": {
        "name": "Black Rose Beanie",
        "collection": "black-rose",
        "source_override": "po-007-beanie-source.jpg",
        "is_preorder": True,
    },
    "po-009": {
        "name": "SR Monogram Slides",
        "collection": "black-rose",
        "source_override": "po-009-slides-source.jpg",
        "is_preorder": True,
    },
    "po-010": {
        "name": "Love Hurts Slides",
        "collection": "love-hurts",
        "source_override": "po-010-slides-source.jpg",
        "is_preorder": True,
    },
    "po-011": {
        "name": "Black Rose Slides",
        "collection": "black-rose",
        "source_override": "po-011-slides-source.jpg",
        "is_preorder": True,
    },
}

# SKUs that are accessories (not wearable on a model's body)
ACCESSORY_SKUS = {
    "lh-001",  # The Fannie (fanny pack)
    "sg-007",  # The Signature Beanie (Black)
    "sg-008",  # The Signature Beanie (Forest Green)
    "po-007",  # Black Rose Beanie
    "po-009",  # SR Monogram Slides
    "po-010",  # Love Hurts Slides
    "po-011",  # Black Rose Slides
}

# SKUs with known bad source images — skipped by default.
# Audited 2026-03-05 by visual inspection of every source file.
BAD_SOURCE_SKUS = set()  # All sources verified clean as of 2026-03-05

# -- Imagen 4 Ultra: text-heavy product descriptions -------------------------
# Products with prominent text ("BLACK IS BEAUTIFUL", "THE BAY") that Gemini
# drops or garbles. Imagen renders text accurately from text prompts.
# Descriptions sourced from products.csv — the canonical product database.

TEXT_HEAVY_SKUS = {"br-003", "po-001", "po-002", "po-003", "po-004"}

# -- FLUX.2 via Together AI: tech flat → photorealistic conversion -----------
# Products that only have vector/design mockup tech flats (not real photos).
# FLUX excels at: (1) converting flat designs → realistic product shots,
# (2) accurate text rendering, (3) exact hex color matching.
# In "auto" mode, these get routed to FLUX instead of Gemini.
TECH_FLAT_SKUS = {
    "br-001",  # Tech flat only (br-001-techflat-v4.jpg)
    "sg-002",  # Tech flat only (sg-002-techflat-v4.jpg)
    "po-006",  # Tech flat only (po-006-techflat.jpg)
}

# -- Logo treatment metadata (real product material) -------------------------
# Used by --step composite to tell Gemini what the REAL logo looks like.
# Products not listed get a generic "match the reference" prompt.
LOGO_TREATMENTS = {
    "br-001": "raised rose with shadow depth — fabric pressed inward along the logo outline creating a 3D relief effect, light catches the elevated edges while recessed areas sit in soft shadow",
    "br-002": "thick rubber logo standing ~2mm above the fabric surface — glossy smooth finish with sharply cut edges, catches specular highlights, casts a small shadow onto the matte fabric beneath",
    "br-004": "raised rose with shadow depth — hoodie fabric pressed inward along the logo outline, creating dimensional relief where light grazes the elevated petals and thorns",
    "br-005": "raised rose with shadow depth — hoodie fabric pressed inward along the logo outline, creating dimensional relief where light grazes the elevated petals and thorns",
    "br-006": "visible thread texture forming the rose — individual stitch lines catch light at different angles creating a satin sheen, slightly raised above the sherpa pile with thread density creating the logo shape",
    "sg-003": "flat matte ink sitting on the cotton surface — crisp sharp edges with no texture change, the print is flush with the fabric showing zero dimensionality, colors are solid and opaque",
    "sg-004": "visible thread texture forming the logo — individual stitch lines catch light creating slight sheen, raised ~1mm above the hoodie knit with visible thread direction changes at curves",
    "sg-005": "flat matte ink sitting on the cotton surface — crisp sharp edges with no texture change, the print is flush with the fabric showing zero dimensionality",
}

IMAGEN_PRODUCT_DESCRIPTIONS = {
    "br-003": {
        "garment": "jersey",
        "details": (
            "A luxury streetwear jersey. Black body with orange collar trim. "
            "Large white rose graphic (rose growing from clouds) on the back. "
            "SR monogram on the upper back. Oakland-rooted gothic luxury. "
            "SkyyRose BLACK ROSE Collection branding."
        ),
        "back_details": (
            "Back of a black jersey with orange collar trim. "
            "Large white rose graphic — a rose growing from thorns and clouds — "
            "centered on the back. SR monogram above the graphic. "
            "Black body color throughout."
        ),
    },
    "po-001": {
        "garment": "American football jersey",
        "details": (
            "Red V-neck football jersey with #80 in large block numerals on the "
            "front. The numbers are filled with a grey/silver rose, thorns & "
            "clouds graphic. V-neck athletic cut with stripe trim on the sleeves. "
            "Bold red body. SR monogram. SkyyRose BLACK ROSE Collection."
        ),
        "back_details": (
            "Back of a red V-neck football jersey. The body color is bold red "
            "throughout. 'BLACK IS BEAUTIFUL' text across the upper back. "
            "Large #80 numerals — filled with grey/silver rose, thorns & clouds "
            "graphic. SR monogram. Stripe trim on sleeves. Red body."
        ),
    },
    "po-002": {
        "garment": "sleeveless basketball tank",
        "details": (
            "White sleeveless basketball jersey / tank top. 'THE BAY' in bold "
            "gold text across the chest. Rose circle graphic below the text. "
            "Grey/silver rose fade on the lower half of the jersey. "
            "Wide shoulder straps. SkyyRose branding."
        ),
        "back_details": (
            "Back of a white sleeveless basketball tank. White body throughout. "
            "'BLACK IS BEAUTIFUL' text across the upper back. "
            "Grey/silver rose fade on lower half. Wide shoulder straps. "
            "White body color."
        ),
    },
    "po-003": {
        "garment": "American football jersey",
        "details": (
            "White V-neck football jersey with bold black #32 on the front "
            "in large block numerals. The '3' digit is filled with a black "
            "rose graphic, the '2' digit is plain black. Black stripe trim "
            "on sleeves. V-neck athletic cut. SR monogram. "
            "SkyyRose BLACK ROSE Collection."
        ),
        "back_details": (
            "Back of a white V-neck football jersey. White body throughout. "
            "'BLACK IS BEAUTIFUL' text across the upper back. Large black #32 "
            "numerals — the '2' digit is filled with a black rose graphic, "
            "the '3' digit is plain black. Black stripe trim. "
            "Shoulder numbers. White body color."
        ),
    },
    "po-004": {
        "garment": "hooded hockey jersey",
        "details": (
            "Black hooded hockey jersey with cyan/teal accents. Large circular "
            "rose crest on the front. Hood attached. Gradient stripe hem and "
            "cuffs in cyan/teal. SkyyRose BLACK ROSE Collection."
        ),
        "back_details": (
            "Back of a black hooded hockey jersey. Black body throughout. "
            "Cyan 'BLACK IS BEAUTIFUL' text across the upper back. "
            "Rose-filled #0 numeral below the text. Gradient stripe hem "
            "and cuffs in cyan/teal. Black body color."
        ),
    },
}


def imagen_render_prompt(sku: str, view: str) -> str:
    """Build a detailed Imagen prompt for text-heavy products."""
    desc = IMAGEN_PRODUCT_DESCRIPTIONS[sku]
    garment = desc["garment"]

    if view in ("render3d_front", "front"):
        return (
            f"Professional e-commerce product photography of a {garment} on an "
            f"invisible mannequin / ghost mannequin, FRONT VIEW. "
            f"{desc['details']} "
            "Light gray (#E8E8E8) studio background with subtle floor reflection. "
            "Professional product photography lighting — soft key light from "
            "upper-left, fill light from right, slight rim light. "
            "Photorealistic, showing natural 3D shape and drape of the fabric. "
            "All text must be perfectly legible and spelled correctly. "
            "Luxury streetwear brand, premium quality."
        )
    elif view in ("render3d_back", "back"):
        return (
            f"Professional e-commerce product photography of a {garment} on an "
            f"invisible mannequin / ghost mannequin, BACK VIEW. "
            f"{desc['back_details']} "
            "Light gray (#E8E8E8) studio background with subtle floor reflection. "
            "Professional product photography lighting. "
            "Photorealistic, showing natural 3D shape and drape of the fabric. "
            "All text must be perfectly legible and spelled correctly. "
            "Luxury streetwear brand, premium quality."
        )
    else:  # branding
        return (
            f"Cinematic luxury editorial product shot of a {garment} on an "
            f"invisible mannequin. {desc['details']} "
            "Dark moody studio background — black marble surface, dramatic "
            "shadows, rose gold (#B76E79) accent lighting. Gothic luxury "
            "aesthetic. All text on the garment must be perfectly legible. "
            "Cinematic composition, slight floor reflection."
        )


def find_source_image(sku: str) -> Path | None:
    """Find the best available source image for a SKU."""
    # Check for explicit source override in catalog
    info = PRODUCT_CATALOG.get(sku, {})
    if "source_override" in info:
        override_path = PRODUCTS_DIR / info["source_override"]
        if override_path.exists():
            return override_path
        log.warning("source_override %s not found for %s", info["source_override"], sku)
        return None

    candidates = list(PRODUCTS_DIR.glob(f"{sku}*.webp")) + list(PRODUCTS_DIR.glob(f"{sku}*.jpg"))
    # Filter out generated shots — we want flat-lay/product source only
    source_candidates = [
        p
        for p in candidates
        if "-front-model" not in p.stem
        and "-back-model" not in p.stem
        and "-branding" not in p.stem
        and "-back" not in p.stem
        and "-render" not in p.stem
    ]
    if not source_candidates:
        return None
    # Prefer .webp over .jpg, then shorter filenames
    source_candidates.sort(key=lambda p: (p.suffix != ".webp", len(p.name)))
    return source_candidates[0]


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
                "source_image": src,
                "is_accessory": sku in ACCESSORY_SKUS,
                "is_preorder": info.get("is_preorder", False),
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
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing this EXACT {name}, front-facing, full body shot, "
        "luxury streetwear editorial photography, studio lighting, clean white "
        "background. The garment must be 100% identical to the reference "
        "image — same colors, same cut, same details, same logo placement, "
        "same fabric texture. Do NOT change the garment type. "
        "The model should have a confident, editorial pose." + ANTI_HALLUCINATION
    )


def back_prompt(name: str) -> str:
    return (
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing this EXACT {name}, BACK-FACING (showing the back of "
        "the garment), full body shot, luxury streetwear editorial photography, "
        "studio lighting, clean white background. The garment must be 100% "
        "identical to the reference — same colors, same cut, same back details, "
        "same logo placement. Do NOT change the garment type. "
        "The model is turned away from camera showing the back of the outfit." + ANTI_HALLUCINATION
    )


def accessory_prompt(name: str) -> str:
    return (
        f"The reference image shows a {name}. Generate a professional fashion "
        f"model wearing/holding this EXACT {name}, front-facing, luxury "
        "streetwear editorial photography, studio lighting, clean white "
        "background. The accessory must be 100% identical to the reference "
        "image. Do NOT change the item type." + ANTI_HALLUCINATION
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
    " STRICT RULES: "
    "Do NOT add any text, words, logos, or branding that is NOT visible "
    "in the reference image. "
    "Do NOT invent labels, patches, tags, or decorative elements. "
    "Do NOT change the garment type to a different product. "
    "Do NOT add sponsor logos, team names, or league branding. "
    "If you cannot see a detail in the reference, do NOT guess — leave it out. "
    "Only reproduce what is actually in the reference image."
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
        response = client.models.generate_content(
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
        f"The reference image is a flat design mockup of a {name}. "
        f"Convert this EXACT design into a photorealistic 3D product render "
        f"of the {name}, FRONT VIEW. The garment should appear as a "
        "professional e-commerce product shot on an invisible mannequin / "
        "ghost mannequin, showing the natural 3D shape and drape of the "
        "fabric. Light gray (#E8E8E8) studio background with subtle floor "
        "reflection. Professional product photography lighting — soft key "
        "light from upper-left, fill light from right, slight rim light. "
        "Every detail from the design mockup MUST be preserved exactly: "
        "same colors, same logos, same numbers, same text, same stripes, "
        "same patches, same patterns. Do NOT change ANY design element. "
        "The output should look like a real photograph of this garment "
        "on a mannequin form, ready for an e-commerce product page." + ANTI_HALLUCINATION
    )


def render3d_back_prompt(name: str) -> str:
    """Prompt for photorealistic 3D product render — back view."""
    return (
        f"The reference image shows both front and back views of a {name}. "
        f"Convert the BACK VIEW of this EXACT design into a photorealistic "
        f"3D product render of the {name}, BACK VIEW. The garment should "
        "appear as a professional e-commerce product shot on an invisible "
        "mannequin / ghost mannequin, showing the natural 3D shape and "
        "drape of the fabric. Light gray (#E8E8E8) studio background with "
        "subtle floor reflection. Professional product photography lighting. "
        "Every detail from the back of the design MUST be preserved exactly: "
        "same colors, same logos, same numbers, same text, same stripes. "
        "Do NOT change ANY design element. Show the BACK of the garment." + ANTI_HALLUCINATION
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
        response = client.models.generate_content(
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


def generate_image_imagen(
    client,
    sku: str,
    view: str,
    attempt: int = 1,
) -> bytes | None:
    """Generate a single image using Imagen 4 Ultra (text-to-image, no reference).

    Best for products with prominent text that Gemini struggles with.
    Returns WebP image bytes on success, None on failure.
    """
    from google.genai import types

    prompt = imagen_render_prompt(sku, view)

    if attempt > 1:
        prompt += (
            " CRITICAL: All text on the garment must be spelled exactly as "
            "described. Do not omit, abbreviate, or alter any words."
        )

    try:
        response = client.models.generate_images(
            model=IMAGEN_MODEL_ID,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="3:4",
                person_generation="allow_adult",
            ),
        )
    except Exception as exc:
        log.error("Imagen API call failed (attempt %d): %s", attempt, exc)
        return None

    if not response or not response.generated_images:
        log.warning("Empty Imagen response (attempt %d)", attempt)
        return None

    img = response.generated_images[0]
    if hasattr(img, "image") and hasattr(img.image, "image_bytes"):
        raw_bytes = img.image.image_bytes
        # Imagen returns PNG — convert to WebP for consistency
        try:
            from PIL import Image

            pil_img = Image.open(io.BytesIO(raw_bytes))
            buf = io.BytesIO()
            pil_img.save(buf, format="WEBP", quality=92)
            return buf.getvalue()
        except Exception:
            return raw_bytes  # fallback: save as-is

    log.warning("No image data in Imagen response (attempt %d)", attempt)
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
    """Map view to output filename."""
    if view.startswith("render3d_"):
        suffix = view.replace("render3d_", "")
        return f"{sku}-render-{suffix}.webp"
    return f"{sku}-{view}-model.webp" if view != "branding" else f"{sku}-branding.webp"


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

    engine: "gemini" | "imagen" | "flux" | "gpt-image" | "auto"
    In auto mode:
      - Imagen Ultra for TEXT_HEAVY_SKUS (text rendering from description)
      - FLUX.2 for TECH_FLAT_SKUS (tech flat → photorealistic)
      - Gemini for everything else (reference-based ghost mannequin)
    """
    sku = product["sku"]
    name = product["name"]
    src = product["source_image"]
    results = {"sku": sku, "name": name, "views": {}}

    # Determine which engine to use for this product
    use_imagen = engine == "imagen" or (engine == "auto" and sku in TEXT_HEAVY_SKUS)
    use_flux = engine == "flux" or (engine == "auto" and sku in TECH_FLAT_SKUS and not use_imagen)
    use_gpt_image = engine == "gpt-image"

    # Validate engine requirements
    if use_gpt_image and not openai_client:
        log.warning("SKIP %s: gpt-image requested but no OpenAI client", sku)
        use_gpt_image = False
    if use_flux and not together_client:
        log.warning("SKIP %s: FLUX requested but no Together client (missing API key?)", sku)
        use_flux = False

    if not use_imagen and not use_flux and not use_gpt_image and not src:
        log.warning("SKIP %s (%s): no source image found", sku, name)
        results["status"] = "no_source"
        return results

    if use_imagen and sku not in IMAGEN_PRODUCT_DESCRIPTIONS:
        log.warning("SKIP %s: no Imagen description defined, falling back to Gemini", sku)
        use_imagen = False
        if not src:
            log.warning("SKIP %s (%s): no source image and no Imagen desc", sku, name)
            results["status"] = "no_source"
            return results

    if use_flux and not src:
        log.info("FLUX text-to-image mode for %s (no source image)", sku)

    engine_label = (
        "GPT-Image-1.5"
        if use_gpt_image
        else "Imagen Ultra" if use_imagen else "FLUX.2" if use_flux else "Gemini"
    )

    # Build analysis-enhanced prompt detail if available
    analysis_detail = ""
    if analysis:
        analysis_detail = analysis_to_prompt_detail(analysis)
        log.info("Vision analysis available for %s — enhancing prompts", sku)
    log.info("Engine: %s for %s", engine_label, sku)

    for view in views:
        # Accessories skip back-model view
        if product["is_accessory"] and view == "back":
            log.info("SKIP %s back view (accessory)", sku)
            results["views"][view] = "skipped_accessory"
            continue

        out_path = PRODUCTS_DIR / get_output_filename(sku, view)
        log.info("Generating %s %s (%s) [%s]...", sku, view, name, engine_label)

        success = False
        for attempt in range(1, MAX_RETRIES + 1):
            if use_imagen:
                image_bytes = generate_image_imagen(client, sku, view, attempt)
            elif use_gpt_image:
                prompt = get_prompt(product, view)
                if analysis_detail:
                    prompt += f" VERIFIED DETAILS: {analysis_detail}"
                image_bytes = generate_image_gpt(
                    openai_client,
                    prompt,
                    src,
                    attempt,
                )
            elif use_flux:
                prompt = flux_render_prompt(name, view, source_desc=analysis_detail)
                image_bytes = generate_image_flux(
                    together_client,
                    prompt,
                    src,
                    attempt,
                )
            else:
                prompt = get_prompt(product, view)
                if analysis_detail:
                    prompt += f" VERIFIED DETAILS: {analysis_detail}"
                image_bytes = generate_image(client, src, prompt, attempt)

            if image_bytes and quality_gate(image_bytes, sku, view):
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
    client = genai.Client(api_key=api_key)
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
    client = genai.Client(api_key=api_key)
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
        "imagen": f"Imagen Ultra ({IMAGEN_MODEL_ID})",
        "flux": f"FLUX.2 ({FLUX_MODEL_ID})",
        "gpt-image": f"GPT-Image ({GPT_IMAGE_MODEL})",
        "auto": (
            f"Auto (Gemini + Imagen for {len(TEXT_HEAVY_SKUS)} text-heavy"
            f" + FLUX for {len(TECH_FLAT_SKUS)} tech-flat SKUs)"
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
        use_imagen = engine == "imagen" or (engine == "auto" and sku in TEXT_HEAVY_SKUS)
        use_flux = engine == "flux" or (
            engine == "auto" and sku in TECH_FLAT_SKUS and not use_imagen
        )
        use_gpt_image = engine == "gpt-image"
        needs_source = not use_imagen
        if not needs_source or product["source_image"] or use_flux or use_gpt_image:
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
        choices=["gemini", "imagen", "flux", "gpt-image", "auto"],
        default="auto",
        help=(
            "Image generation engine: gemini (reference-based), "
            "imagen (Imagen 4 Ultra, text-to-image for text-heavy), "
            "flux (FLUX.2 via Together AI, tech flat conversion + text), "
            "gpt-image (GPT-Image-1.5, reference editing + text), "
            "auto (routes each SKU to best engine — default)"
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
