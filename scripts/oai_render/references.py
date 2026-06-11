"""Reference resolution — maps each SKU to its garment / logo / patch images.

Ported from the retired nano_banana ``source_map.py`` + ``logo_refs.py`` so the
OAI pipeline is fully self-contained (nano_banana can be deleted). The maps are
engine-agnostic data: SKU → real garment photos, collection/SKU logos, and the
sport-patch PNGs.

Hard-fail policy (no silent fallback, per project rule): if a SKU has no usable
garment reference, or a jersey SKU's required sport patch is missing, building
its reference set raises ``MissingReferenceError`` — the SKU is reported and
skipped, never rendered as an incomplete image.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


class MissingReferenceError(RuntimeError):
    """Raised when a SKU lacks a required reference image (garment or patch)."""


@dataclass(frozen=True)
class ReferenceImage:
    """A single labeled reference fed to the image edit call."""

    label: str
    path: Path
    kind: str  # "garment" | "garment-back" | "logo" | "patch"


# ── Catalog ─────────────────────────────────────────────────────────────────
def load_catalog() -> dict[str, dict]:
    """Load the product catalog CSV, keyed by SKU. Single source of truth."""
    catalog: dict[str, dict] = {}
    if not config.CATALOG_CSV.exists():
        raise FileNotFoundError(f"Catalog CSV not found: {config.CATALOG_CSV}")
    with config.CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            sku = (row.get("sku") or "").strip()
            if not sku:
                continue
            catalog[sku] = {
                "name": (row.get("name") or "").strip(),
                "collection": (row.get("collection") or "").strip(),
                "is_preorder": (row.get("is_preorder") or "").strip() == "1",
                "output_slug": (row.get("render_output_slug") or "").strip() or sku,
            }
    return catalog


# ── Authoritative SKU → {front, back} garment source map ────────────────────
# Ported verbatim from nano_banana/source_map.py. ``S`` = split techflats,
# ``P`` = original product photos.
def get_source_map() -> dict[str, dict[str, Path | None]]:
    """Return the complete SKU → {front, back} garment image mapping."""
    s = config.SPLIT_DIR
    p = config.PRODUCTS_DIR
    return {
        # ── BLACK ROSE ──
        "br-001": {
            "front": s / "black-rose" / "br-crewneck-front.jpeg",
            "back": s / "black-rose" / "br-crewneck-back.jpeg",
        },
        "br-002": {
            "front": s / "black-rose" / "br-joggers-front.jpeg",
            "back": s / "black-rose" / "br-joggers-back.jpeg",
        },
        "br-003": {
            "front": s / "black-rose" / "br-jersey-baseball-black-front.jpeg",
            "back": s / "black-rose" / "br-jersey-baseball-black-back.jpeg",
        },
        "br-014": {
            "front": s / "black-rose" / "br-jersey-baseball-giants-front.jpeg",
            "back": s / "black-rose" / "br-jersey-baseball-giants-back.jpeg",
        },
        "br-015": {
            "front": s / "black-rose" / "br-jersey-baseball-white-front.jpeg",
            "back": s / "black-rose" / "br-jersey-baseball-white-back.jpeg",
        },
        "br-004": {"front": p / "black-rose-hoodie-source.jpg", "back": None},
        "br-005": {
            "front": p / "black-rose-hoodie-signature-edition-hoodie-ltd-source.jpg",
            "back": None,
        },
        "br-006": {"front": p / "black-rose-sherpa-jacket-sherpa-product.jpg", "back": None},
        "br-007": {"front": p / "br-007-real-front.jpg", "back": p / "br-007-real-back.jpg"},
        "br-008": {
            "front": s / "black-rose" / "br-jersey-football-sf-front.jpeg",
            "back": s / "black-rose" / "br-jersey-football-sf-back.jpeg",
        },
        "br-009": {
            "front": s / "black-rose" / "br-jersey-football-oakland-front.jpeg",
            "back": s / "black-rose" / "br-jersey-football-oakland-back.jpeg",
        },
        "br-010": {
            "front": s / "black-rose" / "br-jersey-basketball-front.jpeg",
            "back": s / "black-rose" / "br-jersey-basketball-back.jpeg",
        },
        "br-011": {
            "front": s / "black-rose" / "br-jersey-hockey-front.jpeg",
            "back": s / "black-rose" / "br-jersey-hockey-back.jpeg",
        },
        "br-012": {
            "front": p / "last-oakland-baseball-jersey-front.jpeg",
            "back": p / "br-012-last-oakland-baseball-back.jpeg",
        },
        # ── LOVE HURTS ──
        "lh-002": {"front": s / "love-hurts" / "lh-joggers-front.jpeg", "back": None},
        "lh-003": {"front": p / "lh-003-real-front.jpg", "back": p / "lh-003-real-back.jpg"},
        "lh-004": {
            "front": s / "love-hurts" / "lh-bomber-front.jpeg",
            "back": s / "love-hurts" / "lh-bomber-back.jpeg",
        },
        "lh-006": {"front": p / "lh-006-joggers-white.jpeg", "back": None},
        # ── SIGNATURE ──
        "sg-001": {
            "front": s / "signature" / "sg-bridge-shorts-bay-front.jpeg",
            "back": s / "signature" / "sg-bridge-shorts-bay-back.jpeg",
        },
        "sg-002": {
            "front": s / "signature" / "sg-bridge-tee-golden-front.jpeg",
            "back": s / "signature" / "sg-bridge-tee-golden-back.jpeg",
        },
        "sg-003": {
            "front": s / "signature" / "sg-bridge-shorts-golden-front.jpeg",
            "back": s / "signature" / "sg-bridge-shorts-golden-back.jpeg",
        },
        "sg-004": {"front": p / "signature-hoodie-techflat.jpeg", "back": None},
        "sg-005": {"front": p / "bay-bridge-shirt-front.jpg", "back": None},
        "sg-006": {"front": s / "signature" / "sg-mint-lav-hoodie-front.jpeg", "back": None},
        "sg-007": {"front": s / "signature" / "sg-beanie-purple.jpeg", "back": None},
        "sg-009": {"front": p / "sherpa-jacket-front.jpg", "back": None},
        "sg-011": {"front": p / "original-label-tee-white-front.webp", "back": None},
        "sg-012": {"front": p / "original-label-tee-orchid-front.webp", "back": None},
        "sg-013": {
            "front": s / "signature" / "sg-mint-lav-crewneck-front.jpeg",
            "back": s / "signature" / "sg-mint-lav-crewneck-back.jpeg",
        },
        "sg-014": {
            "front": s / "signature" / "sg-mint-lav-sweats-front.jpeg",
            "back": s / "signature" / "sg-mint-lav-sweats-back.jpeg",
        },
        # ── KIDS CAPSULE ──
        "kids-001": {
            "front": s / "kids-capsule" / "kids-red-hoodie-front.jpeg",
            "back": s / "kids-capsule" / "kids-red-hoodie-back.jpeg",
        },
        "kids-001-joggers": {
            "front": s / "kids-capsule" / "kids-red-joggers-front.jpeg",
            "back": s / "kids-capsule" / "kids-red-joggers-back.jpeg",
        },
        "kids-002": {
            "front": s / "kids-capsule" / "kids-purple-hoodie-front.jpeg",
            "back": s / "kids-capsule" / "kids-purple-hoodie-back.jpeg",
        },
        "kids-002-joggers": {
            "front": s / "kids-capsule" / "kids-purple-joggers-front.jpeg",
            "back": s / "kids-capsule" / "kids-purple-joggers-back.jpeg",
        },
    }


# ── Logo + sport-patch references ───────────────────────────────────────────
def _collection_logos() -> dict[str, Path]:
    o = config.OVERLAYS_DIR
    return {
        "black-rose": o / "br-brand-script.png",
        "love-hurts": o / "lh-logo-combined.png",
        "signature": o / "sig-brand-skyy-rose-gold.png",
    }


def _sku_logo_refs() -> dict[str, Path]:
    o = config.OVERLAYS_DIR
    t = config.TECHFLATS_DIR
    return {
        # Black Rose jerseys → sport patches (the elements that were going missing)
        "br-008": o / "br-patch-nfl-football.png",
        "br-009": o / "br-patch-nfl-football.png",
        "br-010": o / "br-patch-nba-basketball.png",
        "br-011": o / "br-patch-hockey.png",
        "br-012": o / "br-patch-mlb-baseball.png",
        "br-014": o / "br-patch-mlb-baseball.png",
        "br-003": o / "br-patch-mlb-baseball.png",
        "br-015": o / "br-patch-mlb-baseball.png",
        # Love Hurts — graffiti script
        "lh-004": t / "love-hurts" / "logo-love.jpeg",
        # Signature — gold script
        "sg-011": t / "signature" / "brand-skyy-rose-collection-gold.jpeg",
        "sg-012": t / "signature" / "brand-skyy-rose-collection-gold.jpeg",
    }


def requires_patch(sku: str) -> bool:
    """True if this SKU is a jersey (by garment source filename) and must carry a patch.

    Derived from the authoritative garment source name, NOT the logo dict — so a
    new jersey added to the source map without a patch entry still hard-fails
    instead of silently rendering patchless.
    """
    front = get_source_map().get(sku, {}).get("front")
    return front is not None and "jersey" in front.name.lower()


def has_back_source(sku: str) -> bool:
    """True if the SKU has a dedicated back garment source → it earns a ghost-back render."""
    back = get_source_map().get(sku, {}).get("back")
    return back is not None and back.exists()


# ── Paired-look registry (founder-confirmed 2026-06-08) ─────────────────────
# Coordinating SKUs shown together on ONE model (paired look) but SOLD
# SEPARATELY. The on-model shot for a paired SKU is the PAIR; ghost-mannequin
# shots stay per-SKU (product cards). A SKU may belong to more than one pair
# (e.g. lh-004 bomber pairs with both jogger colorways).
@dataclass(frozen=True)
class Pair:
    """A two-garment coordinated on-model look (the pieces are sold separately)."""

    pair_id: str
    collection: str
    skus: tuple[str, str]
    label: str


PAIRS: tuple[Pair, ...] = (
    Pair("br-rose-set", "black-rose", ("br-001", "br-002"), "BLACK Rose Crewneck + Joggers"),
    Pair(
        "sg-baybridge-set",
        "signature",
        ("sg-001", "sg-005"),
        "Bridge Series 'The Bay Bridge' Shorts + Shirt",
    ),
    Pair(
        "sg-staygolden-set",
        "signature",
        ("sg-002", "sg-003"),
        "Bridge Series 'Stay Golden' Shirt + Shorts",
    ),
    Pair(
        "sg-mintlav-set",
        "signature",
        ("sg-013", "sg-014"),
        "Mint & Lavender Crewneck + Sweatpants",
    ),
    Pair(
        "lh-bomber-black", "love-hurts", ("lh-004", "lh-002"), "Love Hurts Bomber + Joggers (Black)"
    ),
    Pair(
        "lh-bomber-white", "love-hurts", ("lh-004", "lh-006"), "Love Hurts Bomber + Joggers (White)"
    ),
    Pair(
        "kids-red-set",
        "kids-capsule",
        ("kids-001", "kids-001-joggers"),
        "Kids Colorblock Red — Hoodie + Joggers",
    ),
    Pair(
        "kids-purple-set",
        "kids-capsule",
        ("kids-002", "kids-002-joggers"),
        "Kids Colorblock Purple — Hoodie + Joggers",
    ),
)


def get_pairs_for_sku(sku: str) -> list[Pair]:
    """Return every pair that includes this SKU (a SKU can belong to more than one)."""
    return [p for p in PAIRS if sku in p.skus]


def get_logo_reference(sku: str, collection: str) -> Path | None:
    """Return the logo/patch reference for a SKU. SKU-specific > collection default."""
    sku_refs = _sku_logo_refs()
    if sku in sku_refs:
        path = sku_refs[sku]
        if path.exists():
            return path
        log.warning("Logo/patch reference missing for %s: %s", sku, path)
        return None
    default = _collection_logos().get(collection)
    return default if default and default.exists() else None


def find_flatlay_photo(sku: str) -> Path | None:
    """Find a real product photo for a SKU (ground truth) in product-references/.

    Searches the curated ``data/product-references/`` first, then the theme
    products dir, excluding generated renders.
    """
    # Sibling SKUs that extend this one (e.g. kids-001 → kids-001-joggers); their
    # photos must NOT be picked up by this SKU's prefix glob.
    longer = [k for k in get_source_map() if k != sku and k.startswith(f"{sku}-")]
    for base in (config.PRODUCT_REFERENCES_DIR, config.PRODUCTS_DIR):
        if not base.exists():
            continue
        for pattern in (
            f"{sku}-*real*front*",
            f"{sku}-*real*",
            f"{sku}-*front*",
            f"{sku}-*",
            f"{sku}.*",
        ):
            for match in sorted(base.glob(pattern)):
                stem = match.stem.lower()
                if match.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                    continue
                if any(
                    tag in stem
                    for tag in (
                        "-front-model",
                        "-back-model",
                        "-branding",
                        "-composite",
                        "variant",  # multi-variant comparison shots (e.g. *-variants.jpeg)
                        "-and-",  # multi-SKU composites (e.g. sg-001-and-sg-003-*)
                    )
                ):
                    continue  # skip generated renders / composites — we want one real garment
                if any(stem.startswith(lk) for lk in longer):
                    continue  # belongs to a longer sibling SKU, not this one
                return match
    return None


def build_dossier_index() -> dict[str, Path]:
    """Map SKU → dossier markdown path by parsing each dossier's frontmatter ``sku:``."""
    index: dict[str, Path] = {}
    if not config.DOSSIER_DIR.exists():
        return index
    for md in sorted(config.DOSSIER_DIR.glob("*.md")):
        if md.name.startswith("_"):
            continue  # skip _template.md
        try:
            text = md.read_text(encoding="utf-8")
        except OSError:
            continue
        # Frontmatter is the first --- ... --- block.
        if not text.startswith("---"):
            continue
        end = text.find("---", 3)
        if end == -1:
            continue
        for line in text[3:end].splitlines():
            if line.strip().lower().startswith("sku:"):
                sku = line.split(":", 1)[1].strip()
                if sku and sku.upper() != "REPLACE-WITH-SKU":
                    index[sku] = md
                break
    return index


def build_references(
    sku: str, collection: str, *, include_back: bool = True, view: str = "front"
) -> list[ReferenceImage]:
    """Resolve the ordered, labeled reference set for a SKU.

    Order (first image is the primary canvas — masks apply to it, and per the
    OpenAI cookbook the first image gets the finest detail preservation):
      1. Real product photo (ground truth) — if available
      2. Garment front source (techflat / split)
      3. Garment back source — if available AND ``include_back`` (front-only on-model
         renders pass ``include_back=False`` to avoid back-view / multi-panel collage)
      4. Logo / sport-patch close-up — if applicable

    For ``view="back"`` the back techflat is promoted to FIRST position so the
    view-primary reference leads — best-available mitigation for mirrored-front
    hallucination on rear renders (no verified deterministic fix exists).

    Raises MissingReferenceError when no usable garment reference exists, or
    when a jersey SKU's required sport patch is missing (no silent fallback).
    """
    smap = get_source_map().get(sku, {})
    front = smap.get("front")
    back = smap.get("back")
    flatlay = find_flatlay_photo(sku)

    refs: list[ReferenceImage] = []

    if flatlay and flatlay.exists():
        refs.append(
            ReferenceImage(
                label=(
                    "REFERENCE IMAGE {n} — REAL PRODUCT PHOTO (GROUND TRUTH): actual photograph "
                    "of the real garment. Match its fabric, colors, and logo appearance EXACTLY; "
                    "this image is the ultimate authority."
                ),
                path=flatlay,
                kind="garment",
            )
        )

    if front and front.exists():
        refs.append(
            ReferenceImage(
                label=(
                    "REFERENCE IMAGE {n} — GARMENT TECH FLAT (FRONT VIEW): front-facing design "
                    "illustration showing front panel layout, graphic placement, silhouette, "
                    "and construction."
                ),
                path=front,
                kind="garment",
            )
        )

    # Must have at least one garment reference — otherwise hard-fail.
    if not refs:
        raise MissingReferenceError(
            f"{sku}: no usable garment reference (front={front}, flatlay=None)."
        )

    if include_back and back and back.exists():
        refs.append(
            ReferenceImage(
                label=(
                    "REFERENCE IMAGE {n} — GARMENT TECH FLAT (BACK VIEW): rear-facing design "
                    "illustration showing back panel layout and graphics."
                ),
                path=back,
                kind="garment-back",
            )
        )

    logo = get_logo_reference(sku, collection)
    patch_required = requires_patch(sku)
    if logo and logo.exists():
        is_patch = "patch" in logo.name.lower()
        if patch_required and not is_patch:
            raise MissingReferenceError(
                f"{sku}: jersey requires a sport patch, but the resolved logo "
                f"'{logo.name}' is not a patch — refusing to render patchless."
            )
        refs.append(
            ReferenceImage(
                label=(
                    "REFERENCE IMAGE {n} — "
                    + ("SPORT PATCH" if is_patch else "LOGO/BRANDING")
                    + " CLOSE-UP: the EXACT graphic on the garment. Reproduce it at the EXACT "
                    "position and size shown in the tech flat. Do NOT resize, reposition, "
                    "duplicate, omit, or alter it."
                ),
                path=logo,
                kind="patch" if is_patch else "logo",
            )
        )
    elif patch_required:
        # Jersey whose sport patch is missing → must not render patchless.
        raise MissingReferenceError(
            f"{sku}: required sport patch reference is missing; refusing to render a "
            "patchless jersey (100%-replicated rule)."
        )

    if view == "back":
        # View-primary ordering: the back techflat leads for back renders.
        refs.sort(key=lambda r: 0 if r.kind == "garment-back" else 1)

    capped = refs[: config.MAX_REFERENCE_IMAGES]
    # Re-number the {n} placeholders in display order.
    return [
        ReferenceImage(label=r.label.format(n=i + 1), path=r.path, kind=r.kind)
        for i, r in enumerate(capped)
    ]
