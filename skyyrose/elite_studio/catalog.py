"""Catalog — Single source of truth loader for SkyyRose product data.

Reads the canonical CSV at:
  wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv

This replaces the previous YAML-based catalog
(`assets/product-masters/catalog.yaml`), which was retired 2026-04-19.
The ProductEntry / Catalog dataclass contract is preserved so existing
consumers (prompt generators, vision test, fidelity gate, Compositor)
keep working. Fields that the YAML carried but the CSV does not
(aliases, filename_patterns, color_spec, variants, master, etc.) are
defaulted to empty; populate in a follow-up if the pipeline needs them.

Typical usage:

    from skyyrose.elite_studio.catalog import Catalog

    cat = Catalog.load()
    p = cat.require("sg-013")
    print(p.series)             # derived from name: 'Mint & Lavender'
    print(p.branding_summary)   # logo/branding spec from CSV

Env var SKYYROSE_CATALOG_PATH overrides the default CSV path.
"""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .validation import (
    IntegrityError,
    Violation,
    validate_enum,
    validate_hex_color,
    validate_non_negative,
    validate_not_empty,
    validate_sku_format,
)

_ENV_CATALOG_PATH = "SKYYROSE_CATALOG_PATH"

PRODUCT_STATUS = {"draft", "pre-order", "live", "retired"}
MASTER_SOURCE = {"pending", "photograph", "techflat", "design"}


def default_catalog_path() -> Path:
    """Return the canonical catalog CSV path (env-overridable)."""
    override = os.getenv(_ENV_CATALOG_PATH)
    if override:
        return Path(override)
    # skyyrose/elite_studio/catalog.py → climb 2 to <repo_root>
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "wordpress-theme" / "skyyrose-flagship" / "data" / "skyyrose-catalog.csv"


# ─── Dataclasses ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProductEntry:
    sku: str
    name: str
    collection: str
    price_usd: float
    status: str  # 'draft' | 'pre-order' | 'live' | 'retired'
    branding_summary: str
    series: str | None
    aliases: tuple[str, ...]
    filename_patterns: tuple[str, ...]
    color_spec: dict[str, Any]
    text_spec: tuple[str, ...]
    variants: tuple[dict, ...]
    master: dict[str, Any]
    source_files: tuple[str, ...]
    ai_renders: tuple[str, ...]
    review_flags: tuple[str, ...]
    notes: str
    limited_pieces: int | None = None
    retirement_note: str | None = None

    def __post_init__(self) -> None:
        # Structural validation — raise loud, not silent
        p = f"products[{self.sku!r}]"
        validate_sku_format(self.sku, f"{p}.sku")
        validate_not_empty(self.name, f"{p}.name")
        validate_not_empty(self.collection, f"{p}.collection")
        validate_enum(self.status, PRODUCT_STATUS, f"{p}.status")
        validate_non_negative(self.price_usd, f"{p}.price_usd")

        primary = (self.color_spec or {}).get("primary")
        if primary is not None:
            validate_hex_color(primary, f"{p}.color_spec.primary")
        for i, accent in enumerate((self.color_spec or {}).get("accents") or []):
            validate_hex_color(accent, f"{p}.color_spec.accents[{i}]")

        for i, alias in enumerate(self.aliases):
            validate_sku_format(alias, f"{p}.aliases[{i}]")

        master_source = (self.master or {}).get("source")
        if master_source is not None:
            validate_enum(master_source, MASTER_SOURCE, f"{p}.master.source")

        if self.limited_pieces is not None:
            if not isinstance(self.limited_pieces, int) or self.limited_pieces < 1:
                raise ValueError(
                    f"{p}.limited_pieces: must be a positive int or null, got {self.limited_pieces!r}"
                )

    @property
    def is_active(self) -> bool:
        return self.status != "retired"

    @property
    def is_locked(self) -> bool:
        m = self.master or {}
        return bool(m.get("path")) and m.get("hash") is not None

    @property
    def all_filename_keys(self) -> tuple[str, ...]:
        return (self.sku,) + tuple(self.aliases)


@dataclass(frozen=True)
class SeriesEntry:
    name: str
    collection: str
    description: str
    skus: tuple[str, ...]
    lookbook_images: tuple[str, ...]


@dataclass(frozen=True)
class Catalog:
    version: int
    generated_at: str
    collections: dict[str, Any]
    catalog_rules: dict[str, Any]
    series_by_name: dict[str, SeriesEntry]
    products_by_sku: dict[str, ProductEntry]
    unclaimed_legacy_files: dict[str, Any]
    orphan_brand_files: dict[str, Any]
    violations: tuple[Violation, ...] = ()

    # ─── Loading ────────────────────────────────────────────────────────

    @classmethod
    def load(cls, path: Path | str | None = None, *, strict: bool = False) -> Catalog:
        """Load the canonical catalog CSV."""
        p = Path(path) if path else default_catalog_path()
        if not p.is_file():
            raise FileNotFoundError(f"Catalog not found at {p}")
        rows = _read_csv_rows(p)
        return cls._from_csv_rows(rows, source_path=p, strict=strict)

    @classmethod
    def _from_csv_rows(
        cls, rows: list[dict[str, str]], *, source_path: Path, strict: bool = False
    ) -> Catalog:
        products_by_sku: dict[str, ProductEntry] = {}
        series_index: dict[str, list[str]] = {}

        for i, raw in enumerate(rows):
            sku = raw.get("sku", "").strip()
            if not sku:
                continue

            status = _status_from_csv(raw)
            series_name = _series_from_name(raw.get("name", ""))
            if series_name:
                series_index.setdefault(series_name, []).append(sku)

            ai_renders = tuple(
                v
                for v in (
                    raw.get("image", "").strip(),
                    raw.get("front_model_image", "").strip(),
                    raw.get("back_image", "").strip(),
                    raw.get("back_model_image", "").strip(),
                )
                if v
            )

            source_files = tuple(
                v
                for v in (
                    raw.get("render_source_override", "").strip(),
                    raw.get("render_back_source_override", "").strip(),
                )
                if v
            )

            products_by_sku[sku] = ProductEntry(
                sku=sku,
                name=raw.get("name", "").strip(),
                collection=raw.get("collection", "").strip(),
                price_usd=float(raw.get("price") or 0.0),
                status=status,
                branding_summary=raw.get("branding_spec", "").strip(),
                series=series_name,
                aliases=(),
                filename_patterns=(),
                color_spec={},
                text_spec=(),
                variants=(),
                master={},
                source_files=source_files,
                ai_renders=ai_renders,
                review_flags=(),
                notes="",
                limited_pieces=_parse_edition_size(raw.get("edition_size", "")),
                retirement_note=None,
            )

        # Derive collections block from distinct slugs
        collections: dict[str, Any] = {}
        for p in products_by_sku.values():
            if p.collection and p.collection not in collections:
                collections[p.collection] = {"slug": p.collection}

        # Build series entries from the product-name-derived index
        series_by_name: dict[str, SeriesEntry] = {
            name: SeriesEntry(
                name=name,
                collection=(products_by_sku[skus[0]].collection if skus else ""),
                description="",
                skus=tuple(skus),
                lookbook_images=(),
            )
            for name, skus in series_index.items()
        }

        violations = cls._validate_integrity(
            collections=collections,
            series_by_name=series_by_name,
            products_by_sku=products_by_sku,
        )
        if strict and violations:
            raise IntegrityError(list(violations))

        return cls(
            version=1,
            generated_at=source_path.stat().st_mtime.__str__(),
            collections=collections,
            catalog_rules={},
            series_by_name=series_by_name,
            products_by_sku=products_by_sku,
            unclaimed_legacy_files={},
            orphan_brand_files={},
            violations=tuple(violations),
        )

    @staticmethod
    def _validate_integrity(
        collections: dict[str, Any],
        series_by_name: dict[str, SeriesEntry],
        products_by_sku: dict[str, ProductEntry],
    ) -> list[Violation]:
        """Cross-reference checks. Returns violations list (empty = clean)."""
        viols: list[Violation] = []

        declared_collections = set(collections.keys())
        for sku, p in products_by_sku.items():
            if p.collection not in declared_collections:
                viols.append(
                    Violation(
                        severity="referential",
                        code="unknown_collection",
                        path=f"products[{sku!r}].collection",
                        message=(
                            f"collection {p.collection!r} not declared in collections block "
                            f"(declared: {sorted(declared_collections)})"
                        ),
                    )
                )

        for sname, s in series_by_name.items():
            for sku in s.skus:
                if sku not in products_by_sku:
                    viols.append(
                        Violation(
                            severity="referential",
                            code="series_unknown_sku",
                            path=f"series[{sname!r}].skus",
                            message=f"series references unknown SKU {sku!r}",
                        )
                    )

        return viols

    # ─── Queries ────────────────────────────────────────────────────────

    def list_skus(self, active_only: bool = False) -> list[str]:
        skus = list(self.products_by_sku.keys())
        if active_only:
            skus = [s for s in skus if self.products_by_sku[s].is_active]
        return skus

    def get(self, sku: str) -> ProductEntry | None:
        return self.products_by_sku.get(sku)

    def require(self, sku: str) -> ProductEntry:
        p = self.products_by_sku.get(sku)
        if p is None:
            raise KeyError(f"SKU {sku!r} not found in catalog")
        return p

    def resolve_sku(self, sku_or_alias: str) -> ProductEntry | None:
        if sku_or_alias in self.products_by_sku:
            return self.products_by_sku[sku_or_alias]
        for p in self.products_by_sku.values():
            if sku_or_alias in p.aliases:
                return p
        return None

    def get_series(self, name: str) -> SeriesEntry | None:
        return self.series_by_name.get(name)

    def products_in_series(self, name: str) -> list[ProductEntry]:
        s = self.series_by_name.get(name)
        if not s:
            return []
        return [self.products_by_sku[sku] for sku in s.skus if sku in self.products_by_sku]

    def products_in_collection(
        self, collection: str, active_only: bool = False
    ) -> list[ProductEntry]:
        out = [p for p in self.products_by_sku.values() if p.collection == collection]
        if active_only:
            out = [p for p in out if p.is_active]
        return out

    def jersey_patch_for(self, sku: str) -> str | None:
        """Return patch sport for a jersey SKU, inferred from product name."""
        name = self.products_by_sku[sku].name.lower() if sku in self.products_by_sku else ""
        for sport in ("baseball", "football", "basketball", "hockey"):
            if sport in name:
                return sport
        return None


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _status_from_csv(row: dict[str, str]) -> str:
    """Map the CSV's is_preorder / badge / published triple to the legacy enum."""
    badge = (row.get("badge") or "").strip().lower()
    is_preorder = (row.get("is_preorder") or "").strip() == "1"
    published = (row.get("published") or "").strip() == "1"

    if badge == "retired":
        return "retired"
    if is_preorder:
        return "pre-order"
    if badge == "draft":
        return "draft"
    if published:
        return "live"
    return "draft"


def _series_from_name(name: str) -> str | None:
    """Derive series name from the product name for grouping purposes."""
    n = (name or "").lower()
    if "jersey series" in n:
        return "The Jersey Series"
    if "bridge series" in n:
        return "The Bridge Series"
    if n.startswith("mint & lavender") or "mint & lavender" in n:
        return "Mint & Lavender"
    if "original label tee" in n:
        return "Original Label"
    return None


def _parse_edition_size(value: str) -> int | None:
    v = (value or "").strip()
    if not v:
        return None
    try:
        n = int(v)
    except ValueError:
        return None
    return n if n >= 1 else None
