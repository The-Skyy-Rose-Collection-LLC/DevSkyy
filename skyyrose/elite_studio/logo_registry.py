"""Logo Registry — Canonical loader for SkyyRose logo metadata + path resolution.

Reads the canonical registry at:
  wordpress-theme/skyyrose-flagship/data/logo-registry.json

The registry has two categories of logo:

1. **Centralized logos** — single file, lives under `assets/images/logos/`.
   Entry has a `file` field naming the canonical filename. Examples:
   `sr-monogram-rose-gold`, `black-roses-cloud-cluster`, `heart-rose-composite`.

2. **Per-SKU co-located patches** — same graphic copied into each using SKU's
   product folder. Entry has `co_located_per_sku: true` plus a `filename` field.
   Resolved at consumption time via:
     `assets/images/products/<sku_folders[sku]>/<filename>`
   Examples: `nfl-authentic-collection-card`, `mlb-authentic-collection-card`,
   `nba-authentic-collection-card`, `hockey-championship-card`.

This module is the only authoritative resolver. Do NOT hardcode logo paths
elsewhere — any renderer that needs a logo image should call
`LogoRegistry.image_path(sku, logo_id)`.

Typical usage:

    from skyyrose.elite_studio.logo_registry import LogoRegistry

    reg = LogoRegistry.load()
    # Centralized logo (any SKU resolution works):
    sr_path = reg.image_path(sku="br-005", logo_id="sr-monogram-rose-gold")
    # Per-SKU co-located patch:
    nfl_path = reg.image_path(sku="br-008", logo_id="nfl-authentic-collection-card")
    # Placements for a SKU:
    for placement in reg.placements_for("br-012"):
        print(placement["logo_id"], placement["position"])
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from skyyrose.core.catalog_loader import CATALOG_CSV
from skyyrose.core.paths import THEME_ROOT, WP_LOGOS_DIR, WP_PRODUCTS_DIR

REGISTRY_JSON: Path = CATALOG_CSV.parent / "logo-registry.json"


class LogoNotFoundError(KeyError):
    """Raised when a requested logo_id is not registered."""


class SkuFolderUnknownError(KeyError):
    """Raised when a per-SKU patch needs a folder mapping that is not in the registry."""


@dataclass(frozen=True)
class LogoEntry:
    logo_id: str
    description: str
    primary_color: str
    recolor_allowed: bool
    co_located_per_sku: bool
    filename: str
    collection: str | None
    category: str | None
    site_wide: bool


class LogoRegistry:
    """Read-only loader for logo-registry.json."""

    def __init__(self, raw: dict[str, Any], source: Path | None = None) -> None:
        self._raw = raw
        self._source = source
        self.version: int = int(raw.get("version", 0))
        self.brand_primary: str = raw.get("brand_primary", "")
        self._logos: dict[str, LogoEntry] = {
            logo_id: _entry_from_raw(logo_id, data)
            for logo_id, data in (raw.get("logos") or {}).items()
        }
        self._sku_folders: dict[str, str] = {
            sku: folder
            for sku, folder in (raw.get("sku_folders") or {}).items()
            if not sku.startswith("_")
        }
        self._sku_logos: dict[str, dict[str, Any]] = raw.get("sku_logos") or {}

    @classmethod
    def load(cls, path: Path | None = None) -> LogoRegistry:
        target = path or REGISTRY_JSON
        with target.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        return cls(raw, source=target)

    # ─── Logo lookups ────────────────────────────────────────────────────

    def has_logo(self, logo_id: str) -> bool:
        return logo_id in self._logos

    def get_logo(self, logo_id: str) -> LogoEntry:
        try:
            return self._logos[logo_id]
        except KeyError as exc:
            raise LogoNotFoundError(f"logo_id {logo_id!r} not in registry") from exc

    def all_logos(self) -> dict[str, LogoEntry]:
        return dict(self._logos)

    def sport_patches(self) -> dict[str, LogoEntry]:
        """All per-SKU co-located sport-patch logos."""
        return {lid: e for lid, e in self._logos.items() if e.co_located_per_sku}

    # ─── Path resolution ─────────────────────────────────────────────────

    def image_path(self, *, sku: str, logo_id: str) -> Path:
        """Return absolute filesystem path for a logo's image as it applies to ``sku``.

        For centralized logos: resolves to ``<theme>/assets/images/logos/<file>``.
        For ``co_located_per_sku`` patches: resolves to
        ``<theme>/assets/images/products/<sku_folders[sku]>/<filename>``.

        Raises:
            LogoNotFoundError: if logo_id is not in the registry
            SkuFolderUnknownError: if logo is per-SKU but the SKU has no folder mapping
        """
        entry = self.get_logo(logo_id)
        if entry.co_located_per_sku:
            folder = self._sku_folders.get(sku)
            if not folder:
                raise SkuFolderUnknownError(
                    f"logo {logo_id!r} requires a per-SKU folder mapping but "
                    f"sku {sku!r} is not in sku_folders. Add it to the registry."
                )
            return WP_PRODUCTS_DIR / folder / entry.filename
        return WP_LOGOS_DIR / entry.filename

    def sku_folder(self, sku: str) -> str | None:
        return self._sku_folders.get(sku)

    # ─── Placement lookups ───────────────────────────────────────────────

    def placements_for(self, sku: str) -> list[dict[str, Any]]:
        entry = self._sku_logos.get(sku) or {}
        return list(entry.get("placements") or [])

    def has_sku(self, sku: str) -> bool:
        return sku in self._sku_logos


def _entry_from_raw(logo_id: str, data: dict[str, Any]) -> LogoEntry:
    co_located = bool(data.get("co_located_per_sku", False))
    filename = data.get("filename") or data.get("file") or ""
    return LogoEntry(
        logo_id=logo_id,
        description=str(data.get("description", "")),
        primary_color=str(data.get("primary_color", "")),
        recolor_allowed=bool(data.get("recolor_allowed", False)),
        co_located_per_sku=co_located,
        filename=str(filename),
        collection=data.get("collection"),
        category=data.get("category"),
        site_wide=bool(data.get("site_wide", False)),
    )


__all__ = [
    "REGISTRY_JSON",
    "THEME_ROOT",
    "LogoEntry",
    "LogoNotFoundError",
    "LogoRegistry",
    "SkuFolderUnknownError",
]
