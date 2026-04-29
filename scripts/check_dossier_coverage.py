"""Confirm every active SKU has a per-product design dossier.

Reads the canonical CSV at
`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv` and verifies
each active SKU has a matching dossier at
`wordpress-theme/skyyrose-flagship/data/dossiers/{slug}.md`.

Slug source preference:
  1. The `dossier_slug` column on the CSV row (once Task #16 lands).
  2. Otherwise computed from the `name` column.

Colorway variants (br-003-giants, br-003-oakland, br-003-white) are allowed
to share the base SKU's dossier. The mapping is hard-coded here for the
audit-pass period and should be removed once each variant has its own dossier.

Run from repo root:
    python scripts/check_dossier_coverage.py

Exits 0 if every SKU has a dossier, 1 otherwise. Suitable for CI.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv"
DOSSIERS_DIR = REPO_ROOT / "wordpress-theme/skyyrose-flagship/data/dossiers"

VARIANT_TO_BASE = {
    "br-003-oakland": "br-003",
    "br-003-giants": "br-003",
    "br-003-white": "br-003",
}


def slugify(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def resolve_slug(row: dict[str, str], base_slug_lookup: dict[str, str]) -> str:
    explicit = row.get("dossier_slug", "").strip()
    if explicit:
        return explicit
    base_sku = VARIANT_TO_BASE.get(row["sku"])
    if base_sku and base_sku in base_slug_lookup:
        return base_slug_lookup[base_sku]
    return slugify(row["name"])


def main() -> int:
    if not CSV_PATH.exists():
        print(f"error: canonical CSV not found at {CSV_PATH}", file=sys.stderr)
        return 2
    if not DOSSIERS_DIR.exists():
        print(f"error: dossiers directory not found at {DOSSIERS_DIR}", file=sys.stderr)
        return 2

    with CSV_PATH.open() as f:
        rows = list(csv.DictReader(f))

    base_slug_lookup = {
        row["sku"]: row.get("dossier_slug", "").strip() or slugify(row["name"]) for row in rows
    }

    missing: list[tuple[str, str, Path]] = []
    sharing: list[tuple[str, str]] = []
    found: list[str] = []

    for row in rows:
        sku = row["sku"]
        slug = resolve_slug(row, base_slug_lookup)
        path = DOSSIERS_DIR / f"{slug}.md"

        if not path.exists():
            missing.append((sku, row["name"], path))
            continue

        found.append(sku)
        if sku in VARIANT_TO_BASE:
            sharing.append((sku, VARIANT_TO_BASE[sku]))

    print(f"=== Dossier coverage ({len(found)}/{len(rows)}) ===\n")

    for sku, base in sharing:
        print(f"share  {sku}  →  shares dossier with {base}")
    if sharing:
        print()

    if missing:
        print("MISSING dossiers:")
        for sku, name, path in missing:
            rel = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path
            print(f"  ✗ {sku:<20} {name}")
            print(f"      expected: {rel}")
        print()
        print(f"summary: {len(missing)} dossier(s) missing of {len(rows)} active SKUs")
        return 1

    print(f"summary: every active SKU has a dossier ({len(rows)}/{len(rows)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
