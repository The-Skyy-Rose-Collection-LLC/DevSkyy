"""Pydantic schema for per-product design dossiers.

Layers structured validation over the markdown dossiers at
``wordpress-theme/skyyrose-flagship/data/dossiers/{slug}.md``. The markdown
format stays the source of truth for human authoring; this module parses it
into a strongly-typed model that downstream agents (compositor prompt synth,
brand guardian, vision audit) can consume without re-parsing.

Schema invariants enforced here:
  * Every active SKU must have at least one ``BrandingRegion`` with a non-empty
    technique + description.
  * Negative-prompt list must be non-empty (per ``MEMORY.md`` no-silent-fallback
    rule — every dossier MUST exclude something).
  * ``garment_type_lock`` must be non-empty (drives the FLUX prompt clause).
  * Color codes (hex / Pantone) are OPTIONAL but warned-on-missing — the
    Phase 8 plan promotes them to required after Corey's first backfill PR.

Schema MISSES (deliberate, captured for follow-up):
  * Color values are prose-named (``rose gold``, ``tonal white``) rather than
    hex/Pantone. The schema accepts ``color_named`` only; ``color_hex`` /
    ``color_pantone`` are nullable. ``audit_dossier_coverage.py`` reports the
    coverage % so we can track backfill.
  * Region vocabulary is open-ended (we don't enum-restrict it). The compositor
    treats any string region name as a free-form prompt placement hint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "pydantic v2 is required for skyyrose.core.dossier_schema. "
        "Install via `pip install 'pydantic>=2.0'`."
    ) from exc

from skyyrose.core.dossier_loader import Dossier as RawDossier

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class BrandingRegion(BaseModel):
    """One placement region (front-chest, back-neck, sleeve cuff, etc.)."""

    region: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    # Technique is intentionally generous — dossiers carry parenthetical
    # detail like "embroidered (wordmark in white thread + red rose detail)"
    # that the prompt synthesizer wants to preserve verbatim.
    technique: str = Field(..., min_length=1, max_length=250)
    color_named: str | None = None
    color_hex: str | None = None
    color_pantone: str | None = None
    dimensions: str | None = None

    @field_validator("color_hex")
    @classmethod
    def _validate_hex(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not re.match(r"^#[0-9A-Fa-f]{6}$", v):
            raise ValueError(f"color_hex must match #RRGGBB (got {v!r})")
        return v.upper()


class DossierSchema(BaseModel):
    """Structured dossier. Built from the parsed markdown via ``from_raw()``."""

    sku: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    collection: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    garment_type_lock: str = Field(..., min_length=1)
    branding: list[BrandingRegion] = Field(..., min_length=1)
    negative: list[str] = Field(..., min_length=1)
    scene_pose: str = ""
    scene_setting: str = ""

    @classmethod
    def from_raw(cls, raw: RawDossier) -> DossierSchema:
        """Build a schema instance from the markdown-parsed raw Dossier.

        Raises ``DossierSchemaError`` if any required field can't be extracted.
        """
        branding = parse_branding_regions(raw.branding_block)
        negative = parse_negative_list(raw.negative_block)
        try:
            return cls(
                sku=raw.sku,
                name=raw.name,
                collection=raw.collection,
                slug=raw.slug,
                garment_type_lock=raw.garment_type_lock,
                branding=branding,
                negative=negative,
                scene_pose=raw.scene_pose,
                scene_setting=raw.scene_setting,
            )
        except Exception as exc:
            raise DossierSchemaError(
                f"dossier {raw.sku} ({raw.slug}) failed schema validation: {exc}"
            ) from exc


class DossierSchemaError(ValueError):
    """Raised when a dossier fails schema validation."""


# ---------------------------------------------------------------------------
# Markdown parsers
# ---------------------------------------------------------------------------

# A branding bullet looks like:
#   - **front-chest** (~10in × 5in): description. **Technique:** embossed.
#     **Color:** tonal black-on-black.
#
# Parser rules:
#   - region name is the first **bold** segment in the bullet
#   - dimensions is parens content immediately after the region name (optional)
#   - Technique is the first **Technique:** segment
#   - Color is the first **Color:** segment
#   - Hex is detected as #RRGGBB anywhere in the line (optional)
#   - Pantone is detected as "PMS <code>" or "Pantone <code>" (optional)


_BULLET_RE = re.compile(r"^\s*-\s+\*\*(?P<region>[^*]+)\*\*", re.MULTILINE)
_DIMENSIONS_RE = re.compile(r"\(([^)]*\d[^)]*)\)")
_TECHNIQUE_RE = re.compile(r"\*\*Technique:\*\*\s*([^.\n]+)", re.IGNORECASE)
_COLOR_RE = re.compile(r"\*\*Color:\*\*\s*([^.\n]+)", re.IGNORECASE)
_HEX_RE = re.compile(r"#[0-9A-Fa-f]{6}")
_PANTONE_RE = re.compile(
    r"\b(?:PMS|Pantone)[\s-]*([0-9A-Za-z][0-9A-Za-z\-]*)",
    re.IGNORECASE,
)


def parse_branding_regions(branding_block: str) -> list[BrandingRegion]:
    """Extract one BrandingRegion per bullet item from the Branding section.

    The block is expected to contain markdown bullets following the pattern
    documented above. Bullets that don't carry a Technique field are skipped
    silently (they're typically informational notes about the logo art, not
    placement specs).
    """
    if not branding_block.strip():
        return []

    regions: list[BrandingRegion] = []
    # Split on top-level bullets; tolerate nested indentation.
    bullets = _split_bullets(branding_block)
    for bullet in bullets:
        region_match = _BULLET_RE.search(bullet)
        if not region_match:
            continue
        technique_match = _TECHNIQUE_RE.search(bullet)
        if not technique_match:
            # Skip informational bullets that don't declare a placement spec.
            continue

        region_name = region_match.group("region").strip()
        technique = technique_match.group(1).strip().rstrip(".").strip()

        color_match = _COLOR_RE.search(bullet)
        color_named: str | None = None
        if color_match:
            color_named = color_match.group(1).strip().rstrip(".").strip()

        dim_match = _DIMENSIONS_RE.search(bullet)
        dimensions = dim_match.group(1).strip() if dim_match else None

        hex_match = _HEX_RE.search(bullet)
        color_hex = hex_match.group(0).upper() if hex_match else None

        pantone_match = _PANTONE_RE.search(bullet)
        color_pantone = f"PMS {pantone_match.group(1).strip()}" if pantone_match else None

        # Description is the bullet body sans the bold-region prefix and the
        # Technique / Color trailing labels — keep raw for now.
        description = bullet.strip()

        try:
            regions.append(
                BrandingRegion(
                    region=region_name,
                    description=description,
                    technique=technique,
                    color_named=color_named,
                    color_hex=color_hex,
                    color_pantone=color_pantone,
                    dimensions=dimensions,
                )
            )
        except Exception as exc:  # pragma: no cover - schema raises ValidationError
            raise DossierSchemaError(
                f"branding region {region_name!r} failed validation: {exc}"
            ) from exc

    return regions


def parse_negative_list(negative_block: str) -> list[str]:
    """Extract the bulleted negative list as a plain list of strings."""
    if not negative_block.strip():
        return []
    items: list[str] = []
    for line in negative_block.splitlines():
        s = line.strip()
        if s.startswith("- ") or s.startswith("* "):
            items.append(s[2:].strip())
    return items


def _split_bullets(block: str) -> list[str]:
    """Split a markdown block into top-level bullets.

    Top-level bullets start with ``- `` at indentation 0–2; nested content
    (indented further) belongs to the parent bullet.
    """
    bullets: list[list[str]] = []
    current: list[str] | None = None
    for line in block.splitlines():
        if re.match(r"^[ \t]{0,3}- ", line) and not line.lstrip(" \t-").startswith("- "):
            if current is not None:
                bullets.append(current)
            current = [line]
        elif current is not None:
            # continuation of the current bullet
            if line.strip() == "" or line.startswith(" ") or line.startswith("\t"):
                current.append(line)
            else:
                bullets.append(current)
                current = None
    if current is not None:
        bullets.append(current)
    return ["\n".join(b) for b in bullets]


# ---------------------------------------------------------------------------
# Coverage helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DossierCoverage:
    """Per-dossier coverage report row."""

    sku: str
    name: str
    collection: str
    slug: str
    region_count: int
    hex_coverage_pct: float
    pantone_coverage_pct: float
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": self.name,
            "collection": self.collection,
            "slug": self.slug,
            "region_count": self.region_count,
            "hex_coverage_pct": self.hex_coverage_pct,
            "pantone_coverage_pct": self.pantone_coverage_pct,
            "warnings": list(self.warnings),
        }


def coverage_for(schema: DossierSchema) -> DossierCoverage:
    """Compute color-code coverage and warnings for a parsed dossier."""
    total = len(schema.branding)
    hex_n = sum(1 for r in schema.branding if r.color_hex)
    pantone_n = sum(1 for r in schema.branding if r.color_pantone)
    warnings: list[str] = []
    if total == 0:
        warnings.append("no branding regions detected")
    if hex_n < total:
        warnings.append(f"{total - hex_n} region(s) missing color_hex")
    if not schema.scene_pose:
        warnings.append("scene_pose empty")
    if not schema.scene_setting:
        warnings.append("scene_setting empty")
    return DossierCoverage(
        sku=schema.sku,
        name=schema.name,
        collection=schema.collection,
        slug=schema.slug,
        region_count=total,
        hex_coverage_pct=round(100.0 * hex_n / total, 1) if total else 0.0,
        pantone_coverage_pct=round(100.0 * pantone_n / total, 1) if total else 0.0,
        warnings=tuple(warnings),
    )


def load_validated_dossier(slug: str) -> DossierSchema:
    """Load and validate a dossier by slug.

    Raises ``DossierMissingError`` if absent, ``DossierSchemaError`` on schema
    failure.
    """
    from skyyrose.core.dossier_loader import load_dossier

    raw = load_dossier(slug)
    return DossierSchema.from_raw(raw)


def load_validated_for_sku(sku: str) -> DossierSchema:
    """Load and validate the dossier for a SKU via the canonical CSV reader."""
    from skyyrose.core.dossier_loader import get_product_with_dossier

    merged = get_product_with_dossier(sku)
    raw: RawDossier = merged["_dossier"]
    return DossierSchema.from_raw(raw)


__all__ = [
    "BrandingRegion",
    "DossierSchema",
    "DossierSchemaError",
    "DossierCoverage",
    "coverage_for",
    "load_validated_dossier",
    "load_validated_for_sku",
    "parse_branding_regions",
    "parse_negative_list",
]
