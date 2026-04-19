#!/usr/bin/env python3
"""Generate the SkyyRose product catalog (assets/product-masters/catalog.yaml).

THE source of truth for all live SKUs. Reads:
  - assets/product-masters/manifest.json   (color_spec, text_spec)
  - skyyrose/assets/images/source-products (authentic photos + techflats)
  - wordpress-theme/.../assets/images/products (AI renders — for inventory only)

Enriches with operational data hard-coded in this file:
  - name, price, status (verified from user's authoritative 2026-04-16 branding spec)
  - branding_summary (logo placement, technique, colors — per SKU)
  - variants (per-colorway / per-config children of a SKU)
  - aliases (legacy SKU codes still used in filenames)
  - review_flags (open questions for the next editor)

Re-runnable. Existing catalog.yaml is OVERWRITTEN; review git diff after run.

Usage:
    python scripts/generate_catalog.py
    python scripts/generate_catalog.py --output /tmp/catalog.yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = _REPO_ROOT / "assets" / "product-masters" / "catalog.yaml"
MANIFEST_PATH = _REPO_ROOT / "assets" / "product-masters" / "manifest.json"
SOURCE_DIR = _REPO_ROOT / "skyyrose" / "assets" / "images" / "source-products"
AI_RENDER_DIR = (
    _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
)
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")

CATALOG_SCHEMA_VERSION = 3


# ─── Product schema ─────────────────────────────────────────────────────────


@dataclass
class ProductMeta:
    sku: str
    name: str
    collection: str
    price_usd: float
    status: str  # draft | pre-order | live | retired
    branding_summary: str = ""  # user-authored logo/placement/technique description
    series: str | None = None  # named sub-series within collection (e.g., "Bridge Series")
    aliases: list[str] = field(default_factory=list)
    variants: list[dict] = field(default_factory=list)  # [{variant_id, name, notes?}]
    limited_pieces: int | None = None
    retirement_note: str | None = None
    review_flags: list[str] = field(default_factory=list)


# Series definitions — brand-named sub-collections that span multiple SKUs.
# Adding a series here + assigning via ProductMeta(series=...) lets prompt
# generators, email flows, and paid-media audiences treat a drop as one unit.
SERIES = {
    "The Jersey Series": {
        "collection": "black-rose",
        "description": (
            "THE JERSEY SERIES — SkyyRose's flagship sportswear line. Every SkyyRose "
            "jersey ships under this banner with a league-specific custom patch stitched "
            "to the bottom-left corner of the front. Long-term brand selling point: "
            "'Under the Jersey Series' becomes instantly identifiable to the customer.\n\n"
            "Current roster:\n"
            "  br-003  BLACK is Beautiful Jersey  (baseball patch — 4 variants)\n"
            "  br-008  SF Inspired Jersey          (football patch, limited 80)\n"
            "  br-009  LAST OAKLAND Jersey         (football patch, limited 80)\n"
            "  br-010  THE BAY Jersey              (basketball patch, limited 80)\n"
            "  br-011  SHARKS EDITION Jersey       (hockey patch, limited 80)\n\n"
            "New jersey SKUs MUST be added to this series. No 'standalone jersey' concept."
        ),
        "skus": ["br-003", "br-008", "br-009", "br-010", "br-011"],
    },
    "Bridge Series": {
        "collection": "signature",
        "description": (
            "Bay Area bridge-themed drop. Sublimated bridge imagery on shorts, "
            "embroidered rose medallions on matching shirts. Blue rose = Bay Bridge, "
            "purple rose = Golden Gate."
        ),
        "skus": ["sg-001", "sg-002", "sg-003", "sg-005"],
    },
    "Mint & Lavender": {
        "collection": "signature",
        "description": (
            "Mint-and-lavender colorway capsule. Hoodie + crewneck + sweatpants tri-piece "
            "that work as separates or as a full sweatsuit. Lavender rose embroidery."
        ),
        "skus": ["sg-006", "sg-013", "sg-014"],
        # File prefixes owned by this series (not by any single SKU — e.g., lookbook images).
        "lookbook_file_prefixes": ["sg-d03"],
    },
    "Original Label": {
        "collection": "signature",
        "description": (
            "Minimal-label tee program. Two colorways (white, orchid). "
            "Original SkyyRose label/tag styling — the brand's foundational tee."
        ),
        "skus": ["sg-011", "sg-012"],
    },
}


# ─── The authoritative product list (user-verified 2026-04-16) ──────────────


PRODUCTS: list[ProductMeta] = [
    # ── Black Rose (11) ───────────────────────────────────────────────────
    ProductMeta(
        sku="br-001",
        name="BLACK Rose Crewneck",
        collection="black-rose",
        price_usd=35.00,
        status="draft",
        branding_summary=("Embossed rose logo on front chest, approximately 10 inches across."),
    ),
    ProductMeta(
        sku="br-002",
        name="BLACK Rose Joggers",
        collection="black-rose",
        price_usd=50.00,
        status="pre-order",
        branding_summary="Silicone patch rose logo on left thigh.",
    ),
    ProductMeta(
        sku="br-003",
        name="BLACK is Beautiful Jersey",
        collection="black-rose",
        price_usd=45.00,
        status="draft",
        branding_summary=(
            "Front: 'BLACK IS BEAUTIFUL' lettering + custom baseball patch. "
            "Back: embroidered rose logo. "
            "Colorway variants differ in letter colors / patch detail."
        ),
        variants=[
            {"variant_id": "black", "name": "Black", "notes": "Default colorway."},
            {
                "variant_id": "oakland",
                "name": "Oakland",
                "notes": (
                    "'BLACK IS BEAUTIFUL' lettering: the 'A' of BLACK is black, "
                    "the rest of the letters are gold. Custom baseball patch."
                ),
            },
            {"variant_id": "giants", "name": "Giants", "notes": "San Francisco Giants inspired."},
            {"variant_id": "white", "name": "White", "notes": "White colorway."},
        ],
    ),
    ProductMeta(
        sku="br-004",
        name="BLACK Rose Hoodie",
        collection="black-rose",
        price_usd=40.00,
        status="pre-order",
        branding_summary="Embroidered rose logo on chest.",
    ),
    ProductMeta(
        sku="br-005",
        name="BLACK Rose Hoodie — Signature Edition",
        collection="black-rose",
        price_usd=65.00,
        status="pre-order",
        branding_summary=(
            "Silicone cut-out rose logo on right chest. "
            "Embroidered rose logo on the SIDE of the body (not on the arm)."
        ),
    ),
    ProductMeta(
        sku="br-006",
        name="BLACK Rose Sherpa Jacket",
        collection="black-rose",
        price_usd=95.00,
        status="pre-order",
        branding_summary=(
            "SATIN BOMBER silhouette, lined with black sherpa, hooded. "
            "Embroidered rose logo on left chest. Large embroidered rose logo on back center."
        ),
    ),
    ProductMeta(
        sku="br-007",
        name="BLACK Rose x Love Hurts Shorts",
        collection="black-rose",
        price_usd=65.00,
        status="pre-order",
        branding_summary=(
            "CROSS-COLLECTION drop. Tackle-twill cut-out letters spelling 'Oakland' "
            "stitched on front. Sublimated rose logo throughout the shorts. "
            "Large sublimated 'Love Hurts' logo on left side. "
            "Additional 'Love Hurts' + rose logos stitched on mesh side panels."
        ),
        review_flags=[
            "Previously mislabeled in catalog as 'Basketball Shorts'. This is a Black Rose × "
            "Love Hurts collab short, not the plain basketball short."
        ],
    ),
    ProductMeta(
        sku="br-008",
        name="SF Inspired Jersey",
        collection="black-rose",
        price_usd=115.00,
        status="pre-order",
        limited_pieces=80,
        aliases=["br-d02"],
        branding_summary=(
            "Jersey Series #1. Red colorway. Jersey-style stitched numbers (80) front and back. "
            "Front: the '8' contains the rose logo; '0' is plain white. "
            "Back: reversed — '8' is plain white; '0' contains the rose. "
            "Custom FOOTBALL patch at bottom-left corner (brand-assets/patch-nfl-football.jpeg)."
        ),
    ),
    ProductMeta(
        sku="br-009",
        name="LAST OAKLAND Jersey",
        collection="black-rose",
        price_usd=115.00,
        status="pre-order",
        limited_pieces=80,
        aliases=["br-d03"],
        branding_summary=(
            "Jersey Series #2. White colorway. Jersey-style stitched numbers (32) front and back. "
            "Front: the '3' contains the rose logo; '2' is plain white. "
            "Back: reversed — '3' is plain white; '2' contains the rose. "
            "Custom FOOTBALL patch at bottom-left corner (brand-assets/patch-nfl-football.jpeg)."
        ),
    ),
    ProductMeta(
        sku="br-010",
        name="THE BAY Jersey (Basketball)",
        collection="black-rose",
        price_usd=115.00,
        status="pre-order",
        limited_pieces=80,
        aliases=["br-d04"],
        branding_summary=(
            "Jersey Series #3. Basketball silhouette. "
            "Custom BASKETBALL patch at bottom-left corner (brand-assets/patch-nba-basketball.jpeg). "
            "Vision rendered the first concept well — reference that render as the starting point."
        ),
    ),
    ProductMeta(
        sku="br-011",
        name="SHARKS EDITION Jersey (Hockey)",
        collection="black-rose",
        price_usd=115.00,
        status="pre-order",
        limited_pieces=80,
        aliases=["br-d01"],
        branding_summary=(
            "Jersey Series #4. Hockey silhouette — San Jose Sharks inspired. "
            "Custom HOCKEY patch at bottom-left corner (brand-assets/patch-hockey-championship.jpeg). "
            "Vision rendered the first concept well — reference that render as the starting point."
        ),
    ),
    # ── Love Hurts (4 active, +1 retired) ─────────────────────────────────
    ProductMeta(
        sku="lh-002",
        name="Love Hurts Joggers",
        collection="love-hurts",
        price_usd=95.00,
        status="pre-order",
        branding_summary=(
            "Heart-and-rose 'Love Hurts' logo on left thigh. "
            "Ships in TWO colorway variants (same SKU, variant selector at checkout)."
        ),
        variants=[
            {
                "variant_id": "white-black-stripe",
                "name": "White with black stripe",
                "notes": "White base with contrast black side stripe.",
            },
            {
                "variant_id": "black-white-stripe",
                "name": "Black with white stripe",
                "notes": "Black base with contrast white side stripe.",
            },
        ],
    ),
    ProductMeta(
        sku="lh-003",
        name="Love Hurts Basketball Shorts",
        collection="love-hurts",
        price_usd=75.00,
        status="pre-order",
        branding_summary=(
            "Sublimated rose logo throughout. Large sublimated 'Love Hurts' logo on left side. "
            "Additional 'Love Hurts' + rose logos stitched on mesh side panels."
        ),
    ),
    ProductMeta(
        sku="lh-004",
        name="Love Hurts Varsity Jacket",
        collection="love-hurts",
        price_usd=265.00,
        status="draft",
        aliases=["lh-005"],
        branding_summary=(
            "'Love Hurts' logo lettering across the FRONT. "
            "Inside hood: sublimated rose logo lining. "
            "Back: 'Heart and Rose' logo centered."
        ),
        review_flags=[
            "Added lh-005 as alias — file content (varsity jacket) matches lh-004's product type, "
            "but the lh-005 SKU CODE was reassigned to a Love Hurts Windbreaker (since erased) "
            "during a prior catalog reshuffle. If confusion arises, note that lh-005 files here "
            "are historical mis-naming, not the windbreaker.",
            "Orphan files 'lh-falling-roses-varsity-techflat-*' may also belong to lh-004 — "
            "these have no SKU prefix so they live in orphan_brand_files until confirmed.",
        ],
    ),
    ProductMeta(
        sku="lh-006",
        name="The Fannie (Fanny Pack)",
        collection="love-hurts",
        price_usd=45.00,
        status="pre-order",
        branding_summary=(
            "High-end leather fanny pack. Heart-and-rose logo positioned where the DOT of the 'I' "
            "in 'Fannie' would be (subtle replacement detail)."
        ),
        aliases=["lh-001"],  # renumbered from lh-001 during 2026-03-11 catalog purge
    ),
    # ── Signature (13 active, 2 retired) ──────────────────────────────────
    ProductMeta(
        sku="sg-001",
        name="Bridge Series 'Bay Bridge' Shorts",
        collection="signature",
        price_usd=195.00,
        status="pre-order",
        branding_summary=(
            "Sublimated Bay Bridge image covering entire shorts. "
            "BLUE embroidered rose on bottom-left."
        ),
    ),
    ProductMeta(
        sku="sg-002",
        name="Bridge Series 'Stay Golden' Shirt",
        collection="signature",
        price_usd=65.00,
        status="pre-order",
        branding_summary=(
            "Embroidered rose with the Golden Gate Bridge imagery (sourced from sg-003 shorts) "
            "stitched INSIDE the rose silhouette."
        ),
    ),
    ProductMeta(
        sku="sg-003",
        name="Bridge Series 'Stay Golden' Shorts",
        collection="signature",
        price_usd=65.00,
        status="pre-order",
        branding_summary=(
            "Sublimated Golden Gate Bridge image covering entire shorts. "
            "PURPLE embroidered rose on bottom-left."
        ),
    ),
    ProductMeta(
        sku="sg-004",
        name="The Signature Hoodie",
        collection="signature",
        price_usd=55.00,
        status="retired",
        branding_summary="(Retired — do not regenerate assets or copy for this SKU.)",
        retirement_note="User flagged 'Delete!!!' on 2026-04-16 branding spec.",
    ),
    ProductMeta(
        sku="sg-005",
        name="Bridge Series 'Bay Bridge' Shirt",
        collection="signature",
        price_usd=25.00,
        status="pre-order",
        branding_summary=(
            "Embroidered rose with the Bay Bridge imagery (sourced from sg-001 shorts) "
            "stitched INSIDE the rose silhouette."
        ),
    ),
    ProductMeta(
        sku="sg-006",
        name="Mint & Lavender Hoodie",
        collection="signature",
        price_usd=45.00,
        status="pre-order",
        branding_summary="Lavender rose logo centered on front chest.",
    ),
    ProductMeta(
        sku="sg-007",
        name="The Signature Beanie",
        collection="signature",
        price_usd=25.00,
        status="pre-order",
        branding_summary=(
            "Small silicone patch rose logo, positioned slightly off to the left side. "
            "Four rose-color variants available (red, grey, black, purple)."
        ),
        variants=[
            {"variant_id": "red", "name": "Red Rose", "notes": "Red silicone rose patch."},
            {"variant_id": "grey", "name": "Grey Rose", "notes": "Grey silicone rose patch."},
            {"variant_id": "black", "name": "Black Rose", "notes": "Black silicone rose patch."},
            {"variant_id": "purple", "name": "Purple Rose", "notes": "Purple silicone rose patch."},
        ],
    ),
    ProductMeta(
        sku="sg-009",
        name="The Sherpa Jacket",
        collection="signature",
        price_usd=80.00,
        status="pre-order",
        branding_summary=(
            "RED rose logo on front chest. Lined with WHITE sherpa (lining — not shell)."
        ),
    ),
    ProductMeta(
        sku="sg-010",
        name="The Bridge Series Shorts",
        collection="signature",
        price_usd=60.00,
        status="retired",
        branding_summary="(Retired — duplicate of sg-001 'Bay Bridge Shorts'.)",
        retirement_note=(
            "User flagged 'Delete, Duplicate!!' on 2026-04-16. Duplicate of sg-001. "
            "Source files under sg-010-* should be migrated to sg-001 or sg-003 aliases "
            "after visual confirmation."
        ),
    ),
    ProductMeta(
        sku="sg-011",
        name="Original Label Tee (White)",
        collection="signature",
        price_usd=30.00,
        status="pre-order",
        branding_summary="(Branding detail pending — user left this field blank on 2026-04-16 spec.)",
        review_flags=["Branding detail pending — ask user to fill in placement/technique."],
    ),
    ProductMeta(
        sku="sg-012",
        name="Original Label Tee (Orchid)",
        collection="signature",
        price_usd=30.00,
        status="pre-order",
        branding_summary="(Branding detail pending — user left this field blank on 2026-04-16 spec.)",
        review_flags=["Branding detail pending — ask user to fill in placement/technique."],
    ),
    ProductMeta(
        sku="sg-013",
        name="Mint & Lavender Crewneck",
        collection="signature",
        price_usd=40.00,
        status="pre-order",
        branding_summary=(
            "Lavender rose embroidered logo centered on front. "
            "Small embroidered logo on back of neck/collar."
        ),
    ),
    ProductMeta(
        sku="sg-014",
        name="Mint & Lavender Sweatpants",
        collection="signature",
        price_usd=45.00,
        status="pre-order",
        branding_summary="Embroidered rose logo on left thigh.",
    ),
    # ── Kids Capsule (2) ──────────────────────────────────────────────────
    ProductMeta(
        sku="kids-001",
        name="Kids Red Set",
        collection="kids",
        price_usd=40.00,
        status="live",
        branding_summary=(
            "Black rose embroidered logo on left chest AND left thigh. "
            "Right arm: circular patch (white with black lettering + black rose centered). "
            "Patch reads 'SKYY ROSE' on top, 'COLLECTION' on bottom."
        ),
    ),
    ProductMeta(
        sku="kids-002",
        name="Kids Purple Set",
        collection="kids",
        price_usd=40.00,
        status="live",
        branding_summary=(
            "Black rose embroidered logo on left chest AND left thigh. "
            "Right arm: circular patch (white with black lettering + black rose centered). "
            "Patch reads 'SKYY ROSE' on top, 'COLLECTION' on bottom."
        ),
    ),
    # ── Retired draft SKUs (legacy prefixes from source-products/) ────────
    ProductMeta(
        sku="sg-d01",
        name="Retired: Signature Windbreaker Set",
        collection="signature",
        price_usd=0.00,
        status="retired",
        branding_summary="(Retired draft — no active windbreaker SKU in current Signature catalog.)",
        retirement_note=(
            "Legacy draft prefix. File: sg-d01-windbreaker-set-techflat.jpg. "
            "If this ever becomes a live SKU, assign a new SKU code and migrate this file. "
            "Kept as retired to preserve the historical asset."
        ),
    ),
    ProductMeta(
        sku="sg-d02",
        name="Retired: Collection Shorts (legacy)",
        collection="signature",
        price_usd=0.00,
        status="retired",
        branding_summary="(Retired draft — generic 'collection shorts' techflat.)",
        retirement_note=(
            "Legacy draft prefix. File: sg-d02-collection-shorts.jpeg. "
            "Filename is too generic to confidently map to sg-001/003/010. "
            "Visual review required to decide whether to alias into an active SKU."
        ),
        review_flags=[
            "Possibly belongs to sg-001 (Bay Bridge Shorts) or sg-003 (Stay Golden Shorts). "
            "Confirm visually and add 'sg-d02' to that SKU's aliases if so."
        ],
    ),
    # sg-d03 removed — file moved to series['Mint & Lavender'].lookbook_images
    ProductMeta(
        sku="sg-d04",
        name="Retired: Cream Shorts (legacy)",
        collection="signature",
        price_usd=0.00,
        status="retired",
        branding_summary="(Retired draft — cream shorts. No cream colorway in current Signature catalog.)",
        retirement_note=(
            "Legacy draft prefix. File: sg-d04-cream-shorts.jpg. "
            "No equivalent active SKU. Kept as retired to preserve the asset."
        ),
    ),
]


COLLECTION_DEFAULTS = {
    "black-rose": {
        "display_name": "BLACK ROSE",
        "theme": "gothic / Oakland / concrete luxury",
        "color_palette": {"primary": "#0A0A0A", "accents": ["#B76E79", "#C0C0C0"]},
    },
    "love-hurts": {
        "display_name": "LOVE HURTS",
        "theme": "Beauty & the Beast / enchanted rose / gothic cathedral",
        "color_palette": {"primary": "#0A0A0A", "accents": ["#DC143C", "#B76E79"]},
    },
    "signature": {
        "display_name": "SIGNATURE",
        "theme": "Bay Area / Golden Gate / fashion runway",
        "color_palette": {"primary": "#0A0A0A", "accents": ["#D4AF37", "#B76E79"]},
    },
    "kids": {
        "display_name": "KIDS CAPSULE",
        "theme": "playful luxury / junior fits",
        "color_palette": None,
    },
}


# ─── Cross-cutting catalog rules ───────────────────────────────────────────
# These are read by prompt generators, compositors, and copywriters alongside
# individual SKU branding_summary fields. Rule text should be precise enough
# to drop directly into a Gemini/FLUX prompt.

CATALOG_RULES = {
    "jerseys": {
        "universal_patch_rule": (
            "Every SkyyRose jersey has a league-specific custom patch applied to the "
            "BOTTOM-LEFT CORNER of the jersey front. The patch sport matches the jersey "
            "silhouette (baseball / football / basketball / hockey)."
        ),
        "patch_assets": {
            "baseball": "skyyrose/assets/images/source-products/brand-assets/patch-mlb-baseball.jpeg",
            "football": "skyyrose/assets/images/source-products/brand-assets/patch-nfl-football.jpeg",
            "basketball": "skyyrose/assets/images/source-products/brand-assets/patch-nba-basketball.jpeg",
            "hockey": "skyyrose/assets/images/source-products/brand-assets/patch-hockey-championship.jpeg",
        },
        "sku_to_patch": {
            "br-003": "baseball",  # BLACK is Beautiful Jersey (all 4 variants)
            "br-008": "football",  # SF Inspired
            "br-009": "football",  # LAST OAKLAND
            "br-010": "basketball",  # THE BAY
            "br-011": "hockey",  # SHARKS EDITION
        },
    },
}


# ─── File discovery helpers ────────────────────────────────────────────────


SKU_PREFIX_RE = re.compile(r"^([a-z]+-(?:d?\d{2,3}))", re.IGNORECASE)


def _gather_images(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in IMAGE_EXTS
        and not any(part.startswith(".") or part == "_references" for part in p.parts)
    )


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(_REPO_ROOT))
    except ValueError:
        return str(p)


def _file_sku_prefix(path: Path) -> str | None:
    m = SKU_PREFIX_RE.match(path.name.lower())
    return m.group(1) if m else None


def _match_files_for_sku(
    sku: str, aliases: list[str], files_by_prefix: dict[str, list[Path]]
) -> list[Path]:
    keys = [sku] + aliases
    matched: list[Path] = []
    for k in keys:
        matched.extend(files_by_prefix.get(k, []))
    return sorted(matched)


# ─── YAML emission (hand-rolled for comment control) ───────────────────────


def _y_str(s: str) -> str:
    if s == "":
        return '""'
    needs_quote = any(
        c in s
        for c in (
            ":",
            "#",
            "{",
            "}",
            "[",
            "]",
            ",",
            "&",
            "*",
            "!",
            "|",
            ">",
            "'",
            '"',
            "%",
            "@",
            "`",
        )
    )
    if needs_quote or s.strip() != s or s.lower() in ("null", "true", "false", "yes", "no"):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _y_block(text: str, indent: int) -> str:
    """Emit a YAML | block scalar with the given indent."""
    pad = " " * indent
    lines = text.rstrip("\n").split("\n")
    return "|\n" + "\n".join(f"{pad}{ln}" if ln else f"{pad}" for ln in lines)


def emit_catalog_yaml(
    products: list[ProductMeta],
    manifest: dict,
    source_files_by_prefix: dict[str, list[Path]],
    ai_renders_by_prefix: dict[str, list[Path]],
    unclaimed_sources: dict[str, list[Path]],
    orphan_sources: list[Path],
) -> str:
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    out: list[str] = []

    out.append("# SkyyRose Product Catalog — SINGLE SOURCE OF TRUTH")
    out.append("#")
    out.append("# THIS is the primary source that all calls aim toward.")
    out.append("# Tools that should read from this file:")
    out.append("#   - Vision test (scripts/vision_test_registry.py)")
    out.append("#   - Fidelity gate (skyyrose/elite_studio/fidelity.py)")
    out.append("#   - Compositor (skyyrose/elite_studio/agents/compositor_agent.py)")
    out.append("#   - Prompt generator (all Gemini / FLUX prompt assembly)")
    out.append("#   - Copywriter skill (skyyrose-product-copy)")
    out.append("#   - Manifest.json is DERIVED — never edit manifest.json directly.")
    out.append("#")
    out.append("# Editing rules:")
    out.append("#   - Never delete a SKU. Use status: retired instead.")
    out.append("#   - SKU renames: current SKU at top-level; legacy codes in aliases: [].")
    out.append("#   - Multi-colorway / multi-config: use variants: [] with variant_id + name.")
    out.append("#   - branding_summary is read by prompt generators — keep it precise.")
    out.append("#   - review_flags: [] holds open questions the next editor must resolve.")
    out.append("#")
    out.append("# Regenerate with: python scripts/generate_catalog.py")
    out.append(f"# Generated: {now}")
    out.append("")
    out.append(f"version: {CATALOG_SCHEMA_VERSION}")
    out.append(f'generated_at: "{now}"')
    out.append("")

    # Collections
    out.append("# ── Collection defaults ──")
    out.append("collections:")
    for slug, meta in COLLECTION_DEFAULTS.items():
        out.append(f"  {slug}:")
        out.append(f"    display_name: {_y_str(meta['display_name'])}")
        out.append(f"    theme: {_y_str(meta['theme'])}")
        palette = meta["color_palette"]
        if palette is None:
            out.append("    color_palette: null  # kids varies per SKU")
        else:
            accents = ", ".join(f'"{a}"' for a in palette["accents"])
            out.append(
                f'    color_palette: {{primary: "{palette["primary"]}", accents: [{accents}]}}'
            )
    out.append("")

    # Catalog rules (cross-cutting — read by prompt generators and compositors)
    out.append("# ── Catalog rules (cross-cutting) ──")
    out.append("# These apply across SKUs and supplement per-product branding_summary.")
    out.append("catalog_rules:")
    out.append("  jerseys:")
    out.append(
        f"    universal_patch_rule: {_y_block(CATALOG_RULES['jerseys']['universal_patch_rule'], 6)}"
    )
    out.append("    patch_assets:")
    for sport, asset in CATALOG_RULES["jerseys"]["patch_assets"].items():
        out.append(f"      {sport}: {asset}")
    out.append("    sku_to_patch:")
    for sku, sport in CATALOG_RULES["jerseys"]["sku_to_patch"].items():
        out.append(f"      {sku}: {sport}")
    out.append("")

    # Series (brand-named sub-collections)
    out.append("# ── Series (brand-named sub-collections) ──")
    out.append("# Series group SKUs that ship as a unified drop. Used by email flows,")
    out.append("# paid-media audiences, product-page filters, and prompt generators.")
    out.append("# lookbook_images hold series-level assets (not owned by any single SKU).")
    out.append("series:")
    for series_name, series_meta in SERIES.items():
        out.append(f"  {_y_str(series_name)}:")
        out.append(f"    collection: {series_meta['collection']}")
        out.append(f"    description: {_y_block(series_meta['description'], 6)}")
        out.append(f"    skus: [{', '.join(series_meta['skus'])}]")
        # Series-owned lookbook imagery
        lookbook_files: list[Path] = []
        for prefix in series_meta.get("lookbook_file_prefixes", []):
            lookbook_files.extend(source_files_by_prefix.get(prefix, []))
        if lookbook_files:
            out.append(f"    lookbook_images:        # {len(lookbook_files)} series-level asset(s)")
            for f in lookbook_files:
                out.append(f"      - {_rel(f)}")
        else:
            out.append("    lookbook_images: []")
    out.append("")

    # Products
    out.append(f"# ── Products ({len(products)} SKUs) ──")
    out.append("products:")

    # Build sku → series lookup for per-product emission
    sku_to_series: dict[str, str] = {
        sku: series_name for series_name, meta in SERIES.items() for sku in meta["skus"]
    }

    masters = manifest.get("masters", {})
    for p in products:
        mfst = masters.get(p.sku, {})
        color_spec = mfst.get("color_spec") or {}
        text_spec = mfst.get("text_spec") or []
        collection = mfst.get("collection") or p.collection

        patterns = [p.sku] + p.aliases
        source_files = _match_files_for_sku(p.sku, p.aliases, source_files_by_prefix)
        ai_files = _match_files_for_sku(p.sku, p.aliases, ai_renders_by_prefix)

        out.append("")
        out.append(f"  - sku: {p.sku}")
        out.append(f"    name: {_y_str(p.name)}")
        out.append(f"    collection: {collection}")
        out.append(f"    price_usd: {p.price_usd:.2f}")
        out.append(f"    status: {p.status}")
        if p.limited_pieces is not None:
            out.append(f"    limited_pieces: {p.limited_pieces}")

        series_name = sku_to_series.get(p.sku) or p.series
        if series_name:
            out.append(f"    series: {_y_str(series_name)}")

        if p.aliases:
            out.append(f"    aliases: [{', '.join(p.aliases)}]  # legacy SKU codes in filenames")
        else:
            out.append("    aliases: []")

        out.append(f"    filename_patterns: [{', '.join(patterns)}]")

        primary = color_spec.get("primary", "#000000")
        accents = color_spec.get("accents") or []
        accents_yaml = ", ".join(f'"{a}"' for a in accents)
        out.append(f'    color_spec: {{primary: "{primary}", accents: [{accents_yaml}]}}')

        text_yaml = ", ".join(_y_str(t) for t in text_spec)
        out.append(f"    text_spec: [{text_yaml}]")

        # branding_summary — read by prompt generators, copywriter, vision verifier
        if p.branding_summary:
            out.append(f"    branding_summary: {_y_block(p.branding_summary, 6)}")
        else:
            out.append('    branding_summary: ""')

        # variants
        if p.variants:
            out.append("    variants:")
            for v in p.variants:
                out.append(f"      - variant_id: {v['variant_id']}")
                out.append(f"        name: {_y_str(v['name'])}")
                if v.get("notes"):
                    out.append(f"        notes: {_y_str(v['notes'])}")
        else:
            out.append("    variants: []")

        # master slot
        out.append("    master:")
        out.append("      path: null")
        out.append("      hash: null")
        out.append("      source: pending       # pending | photograph | techflat | design")
        out.append("      photographed_at: null")
        out.append("      locked_at_version: null")

        # source_files
        if source_files:
            out.append(f"    source_files:           # {len(source_files)} file(s)")
            for f in source_files:
                out.append(f"      - {_rel(f)}")
        else:
            out.append("    source_files: []        # NO authentic source imagery found")

        # ai_renders
        if ai_files:
            out.append(
                f"    ai_renders:             # {len(ai_files)} AI-generated — NEVER use as master"
            )
            for f in ai_files:
                out.append(f"      - {_rel(f)}")
        else:
            out.append("    ai_renders: []")

        # retirement_note
        if p.retirement_note:
            out.append(f"    retirement_note: {_y_str(p.retirement_note)}")

        # review_flags
        if p.review_flags:
            out.append("    review_flags:")
            for flag in p.review_flags:
                out.append(f"      - {_y_str(flag)}")
        else:
            out.append("    review_flags: []")

    # Unclaimed legacy files
    out.append("")
    out.append("# ── Unclaimed legacy files ──")
    out.append("# Source files whose SKU prefix does not match any current SKU or alias.")
    out.append("# Resolve by adding the prefix to the appropriate product's aliases: [] above.")
    out.append("unclaimed_legacy_files:")
    if unclaimed_sources:
        for prefix in sorted(unclaimed_sources.keys()):
            paths = unclaimed_sources[prefix]
            out.append(f"  {prefix}:")
            out.append(f"    count: {len(paths)}")
            out.append("    files:")
            for f in paths:
                out.append(f"      - {_rel(f)}")
    else:
        out.append("  {}")

    # Orphan files
    out.append("")
    out.append("# ── Orphan files (no SKU prefix detected) ──")
    out.append("# Mix of brand assets (patches/tags/avatar) and possibly mislabeled product files.")
    out.append("orphan_brand_files:")
    if orphan_sources:
        out.append(f"  count: {len(orphan_sources)}")
        out.append("  files:")
        for f in orphan_sources:
            out.append(f"    - {_rel(f)}")
    else:
        out.append("  count: 0")
        out.append("  files: []")

    return "\n".join(out) + "\n"


# ─── Main ───────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    if not MANIFEST_PATH.is_file():
        print(f"ERROR: manifest.json not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text())

    # Index source files by SKU prefix
    source_files = _gather_images(SOURCE_DIR)
    source_by_prefix: dict[str, list[Path]] = {}
    orphan_sources: list[Path] = []
    for f in source_files:
        prefix = _file_sku_prefix(f)
        if prefix:
            source_by_prefix.setdefault(prefix, []).append(f)
        else:
            orphan_sources.append(f)

    # Index AI renders by SKU prefix (inventory only)
    ai_files = _gather_images(AI_RENDER_DIR)
    ai_by_prefix: dict[str, list[Path]] = {}
    for f in ai_files:
        prefix = _file_sku_prefix(f)
        if prefix:
            ai_by_prefix.setdefault(prefix, []).append(f)

    # Unclaimed legacy prefixes = in source-products but not any SKU/alias
    known_prefixes: set[str] = set()
    for p in PRODUCTS:
        known_prefixes.add(p.sku)
        known_prefixes.update(p.aliases)
    # Series-owned file prefixes (lookbook/editorial imagery not tied to any single SKU)
    for series_meta in SERIES.values():
        known_prefixes.update(series_meta.get("lookbook_file_prefixes", []))
    unclaimed: dict[str, list[Path]] = {
        prefix: paths for prefix, paths in source_by_prefix.items() if prefix not in known_prefixes
    }

    yaml_text = emit_catalog_yaml(
        PRODUCTS, manifest, source_by_prefix, ai_by_prefix, unclaimed, orphan_sources
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml_text)
    print(f"Wrote {len(yaml_text)} bytes to {_rel(args.output)}")

    # Self-validate: load the file back and refuse to "succeed" if invalid.
    # Structural errors raise ValueError; referential errors collected into .violations.
    try:
        from skyyrose.elite_studio.catalog import Catalog
    except ImportError:
        print("NOTE: catalog module not importable — skipping post-write validation")
    else:
        try:
            cat = Catalog.load(path=args.output, strict=True)
            print(f"Validated: {len(cat.products_by_sku)} products, 0 violations")
        except Exception as e:
            print(f"\nERROR: generated catalog.yaml failed validation:\n{e}", file=sys.stderr)
            return 2

    # Summary
    active = [p for p in PRODUCTS if p.status != "retired"]
    retired = [p for p in PRODUCTS if p.status == "retired"]
    covered = sum(1 for p in active if _match_files_for_sku(p.sku, p.aliases, source_by_prefix))
    print(f"\nTotal SKUs: {len(PRODUCTS)} ({len(active)} active, {len(retired)} retired)")
    print(f"Coverage (active only): {covered}/{len(active)} have source imagery")
    print(f"Unclaimed legacy prefixes: {len(unclaimed)}")
    print(f"Orphan brand files: {len(orphan_sources)}")
    print(f"Retired SKUs: {', '.join(p.sku for p in retired) or '(none)'}")

    gaps = [p.sku for p in active if not _match_files_for_sku(p.sku, p.aliases, source_by_prefix)]
    if gaps:
        print(f"\nActive SKUs with NO source imagery: {', '.join(gaps)}")

    flagged = [p for p in PRODUCTS if p.review_flags]
    if flagged:
        print(f"\nSKUs with review_flags ({len(flagged)}):")
        for p in flagged:
            print(
                f"  {p.sku}: {p.review_flags[0][:80]}{'…' if len(p.review_flags[0]) > 80 else ''}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
