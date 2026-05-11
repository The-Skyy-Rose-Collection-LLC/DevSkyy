"""Per-product design dossier loader — shared by all four catalog readers.

Reads markdown dossiers from
`wordpress-theme/skyyrose-flagship/data/dossiers/{slug}.md` and parses them
into a structured dict consumed by:
  - skyyrose.core.catalog_loader.get_product_with_dossier()
  - nano_banana.catalog
  - skyyrose.elite_studio.catalog
  - skyyrose.elite_studio.agents.three_d_agent (RAS prompt construction)

Hard-fails on missing dossier (H1 from plan): the canonical CSV's thin
`branding_spec` column is NOT a fallback — adding one is a backdoor that lets
us forget to author.

The parser is deliberately tolerant of the markdown indentation inside list
items but strict on the section headings and the technique vocabulary (caught
upstream by scripts/validate_dossier.py).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from skyyrose.core.catalog_loader import CATALOG_CSV, read_catalog_rows

DOSSIERS_DIR = CATALOG_CSV.parent / "dossiers"


class DossierMissingError(FileNotFoundError):
    """Raised when a product's dossier markdown file is not found.

    The pipeline fails loudly rather than fall back to the thin CSV
    `branding_spec` column. Author the dossier before rendering.
    """


@dataclass
class Dossier:
    sku: str
    name: str
    collection: str
    slug: str
    garment_type_lock: str
    branding_block: str
    negative_block: str
    scene_pose: str = ""
    scene_setting: str = ""
    logo_reference: str = ""
    extra_logos: list[str] = field(default_factory=list)
    raw: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return {
            "sku": self.sku,
            "name": self.name,
            "collection": self.collection,
            "slug": self.slug,
            "garment_type_lock": self.garment_type_lock,
            "branding_block": self.branding_block,
            "negative_block": self.negative_block,
            "scene_pose": self.scene_pose,
            "scene_setting": self.scene_setting,
            "logo_reference": self.logo_reference,
            "extra_logos": list(self.extra_logos),
        }


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip()
    rest = text[end + 4 :].lstrip("\n")
    fm: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, rest


# Compiled once at module load. The list-key pattern matches a YAML key
# followed by one-or-more indented bullets; the item pattern then extracts
# each bullet's value from the captured block.
_FRONTMATTER_LIST_KEY_RE = re.compile(
    r"^(\w[\w\-]*):\s*\n((?:[ \t]+-\s+.+\n?)+)",
    re.MULTILINE,
)
_FRONTMATTER_LIST_ITEM_RE = re.compile(
    r"^[ \t]+-\s+(.+?)\s*$",
    re.MULTILINE,
)


def _parse_frontmatter_lists(text: str) -> dict[str, list[str]]:
    """Extract YAML-list-style frontmatter values that `_parse_frontmatter` skips.

    Matches the canonical pattern:
        key:
          - item-one
          - item-two

    Returns a dict mapping key → list of stripped item strings. Keys whose
    values are scalar (already captured by `_parse_frontmatter`) are not
    returned here.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out: dict[str, list[str]] = {}
    for match in _FRONTMATTER_LIST_KEY_RE.finditer(block):
        key = match.group(1)
        bullets_block = match.group(2)
        items = [
            m.group(1).strip().strip('"').strip("'")
            for m in _FRONTMATTER_LIST_ITEM_RE.finditer(bullets_block)
        ]
        if items:
            out[key] = items
    return out


def _extract_section(body: str, heading_pattern: str) -> str:
    pattern = rf"^##\s+{heading_pattern}.*?$(.*?)(?=^##\s|\Z)"
    match = re.search(pattern, body, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_garment_lock(body: str) -> str:
    match = re.search(r"\*\*Garment type lock:\*\*\s*(.+?)(?:\n\n|\n##|\Z)", body, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_scene_field(scene_section: str, label: str) -> str:
    pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+?)(?:\n-|\n\n|\Z)"
    match = re.search(pattern, scene_section, re.DOTALL)
    return match.group(1).strip() if match else ""


def parse_dossier_markdown(text: str) -> Dossier:
    """Parse a dossier markdown string into a structured Dossier object."""
    fm, body = _parse_frontmatter(text)
    fm_lists = _parse_frontmatter_lists(text)

    branding_section = _extract_section(body, r"Branding")
    negative_section = _extract_section(body, r"Negative")
    scene_section = _extract_section(body, r"Scene direction")

    garment_lock = _extract_garment_lock(body)

    return Dossier(
        sku=fm.get("sku", ""),
        name=fm.get("name", ""),
        collection=fm.get("collection", ""),
        slug=fm.get("slug", ""),
        garment_type_lock=garment_lock,
        branding_block=branding_section,
        negative_block=negative_section,
        scene_pose=_extract_scene_field(scene_section, "Pose"),
        scene_setting=_extract_scene_field(scene_section, "Setting"),
        logo_reference=fm.get("logo_reference", ""),
        extra_logos=fm_lists.get("extra_logos", []),
        raw=text,
    )


@cache
def load_dossier(slug: str, dossiers_dir: Path | None = None) -> Dossier:
    """Load and parse a dossier by slug. Raises DossierMissingError if absent.

    Memoized: callers should treat the returned Dossier as read-only —
    mutating fields mutates the shared cache.
    """
    base = dossiers_dir or DOSSIERS_DIR
    path = base / f"{slug}.md"
    if not path.exists():
        raise DossierMissingError(
            f"No dossier at {path}. Author the dossier before rendering. "
            f"CSV branding_spec is not a fallback."
        )
    dossier = parse_dossier_markdown(path.read_text(encoding="utf-8"))
    if not dossier.slug:
        dossier.slug = slug
    return dossier


def get_product_with_dossier(sku: str) -> dict:
    """Return the canonical CSV row for `sku` merged with its parsed dossier.

    Raises:
        KeyError if SKU is not in the canonical CSV.
        DossierMissingError if the SKU's dossier file does not exist.
    """
    rows = {row["sku"]: row for row in read_catalog_rows()}
    if sku not in rows:
        raise KeyError(f"SKU {sku!r} not found in {CATALOG_CSV}")
    row = rows[sku]
    slug = (row.get("dossier_slug") or "").strip()
    if not slug:
        raise DossierMissingError(
            f"SKU {sku!r} has no dossier_slug in {CATALOG_CSV}. "
            f"Add the dossier_slug column value before loading."
        )
    dossier = load_dossier(slug)
    return {**row, "dossier": dossier.to_dict(), "_dossier": dossier}


__all__ = [
    "DOSSIERS_DIR",
    "Dossier",
    "DossierMissingError",
    "parse_dossier_markdown",
    "load_dossier",
    "get_product_with_dossier",
]
