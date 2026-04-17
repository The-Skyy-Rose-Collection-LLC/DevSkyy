#!/usr/bin/env python3
"""
Bootstrap the SkyyRose master registry with the 30-SKU production catalog.

Creates `pending` entries for every live SKU so the manifest tracks full catalog
coverage. No file hashes are fabricated — a SKU stays `pending` until a real master
image is locked via `Manifest.lock()`.

Re-runnable: uses overwrite=True on pending entries only. Will NEVER downgrade a
locked entry to pending. Metadata (color_spec, text_spec, collection, notes) is
refreshed on each run so this script is the single source of truth for catalog shape.

After bootstrap, lock individual SKUs as their reference imagery becomes available:

    from skyyrose.elite_studio.master_registry import Manifest
    m = Manifest.load()
    m.lock(
        sku="br-001",
        master_path="br-001.webp",            # file placed in assets/product-masters/
        master_source="photograph",
        alpha_path="br-001-alpha.png",        # optional, background-removed subject
        photographed_at="2026-04-16T12:00:00Z",
        locked_at_version="v3.2.0",
    )
    m.save()

Usage:
    python scripts/bootstrap_master_manifest.py
    python scripts/bootstrap_master_manifest.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Allow running as `python scripts/bootstrap_master_manifest.py` from repo root
# without needing the package installed.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.elite_studio.master_registry import Manifest  # noqa: E402

# ─── Brand palettes ────────────────────────────────────────────────────────────
DARK = "#0A0A0A"
ROSE_GOLD = "#B76E79"
SILVER = "#C0C0C0"
CRIMSON = "#DC143C"
GOLD = "#D4AF37"
MINT = "#B8E0D2"
LAVENDER = "#C8A8E9"
ORCHID = "#DA70D6"
WHITE = "#FFFFFF"

BRAND_MARK = "SKYY ROSE"


@dataclass
class Spec:
    sku: str
    name: str
    collection: str
    color_spec: dict[str, Any]
    text_spec: list[str]
    notes: str = ""


# ─── The 30-SKU catalog ────────────────────────────────────────────────────────
# Source of truth: .wolf memory "EXACT Product Lists Per Collection".
# Reflects the Mar 11-12 SKU purge (no lh-001, lh-005, br-d01-d04, sg-d01-d04, sg-008).

CATALOG: list[Spec] = [
    # ── Black Rose (11) ───────────────────────────────────────────────────────
    Spec(
        "br-001",
        "Crewneck",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD]},
        [BRAND_MARK],
        "$35 draft; standard crewneck silhouette",
    ),
    Spec(
        "br-002",
        "Joggers",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD]},
        [BRAND_MARK],
        "$50 pre-order",
    ),
    Spec(
        "br-003",
        "BLACK is Beautiful Jersey",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD]},
        ["BLACK IS BEAUTIFUL", BRAND_MARK],
        "$45 draft; alternating rose fill numbers (front: L=rose R=plain; back: reversed)",
    ),
    Spec(
        "br-004",
        "Hoodie",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD]},
        [BRAND_MARK],
        "$40 pre-order",
    ),
    Spec(
        "br-005",
        "Hoodie Sig Ed",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, GOLD]},
        [BRAND_MARK],
        "$65 pre-order; signature edition with gold accent detailing",
    ),
    Spec(
        "br-006",
        "Sherpa Jacket",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, SILVER]},
        [BRAND_MARK],
        "$95 pre-order",
    ),
    Spec(
        "br-007",
        "Basketball Shorts",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD]},
        [BRAND_MARK],
        "$65 pre-order",
    ),
    Spec(
        "br-008",
        "SF-Inspired Jersey",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, SILVER]},
        ["SF", BRAND_MARK],
        "$115 pre-order; exclusive, 80 pcs",
    ),
    Spec(
        "br-009",
        "LAST OAKLAND Jersey",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, SILVER]},
        ["LAST OAKLAND", BRAND_MARK],
        "$115 pre-order; exclusive, 80 pcs",
    ),
    Spec(
        "br-010",
        "THE BAY Jersey",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, SILVER]},
        ["THE BAY", BRAND_MARK],
        "$115 pre-order; exclusive, 80 pcs",
    ),
    Spec(
        "br-011",
        "THE ROSE (SHARKS) Jersey",
        "black-rose",
        {"primary": DARK, "accents": [ROSE_GOLD, SILVER]},
        ["THE ROSE", BRAND_MARK],
        "$115 pre-order; exclusive, 80 pcs",
    ),
    # ── Love Hurts (4) ────────────────────────────────────────────────────────
    Spec(
        "lh-002",
        "Love Hurts Joggers",
        "love-hurts",
        {"primary": DARK, "accents": [CRIMSON, ROSE_GOLD]},
        [BRAND_MARK],
        "$95 pre-order",
    ),
    Spec(
        "lh-003",
        "Love Hurts Basketball Shorts",
        "love-hurts",
        {"primary": DARK, "accents": [CRIMSON, ROSE_GOLD]},
        [BRAND_MARK],
        "$75 pre-order",
    ),
    Spec(
        "lh-004",
        "Love Hurts Varsity Jacket",
        "love-hurts",
        {"primary": DARK, "accents": [CRIMSON, ROSE_GOLD]},
        [BRAND_MARK],
        "$265 draft; flagship hero SKU",
    ),
    Spec(
        "lh-006",
        "The Fannie",
        "love-hurts",
        {"primary": DARK, "accents": [CRIMSON, ROSE_GOLD]},
        [BRAND_MARK],
        "$45 pre-order; fanny pack",
    ),
    # ── Signature (13) ────────────────────────────────────────────────────────
    Spec(
        "sg-001",
        "Bay Bridge Shorts",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        ["BAY BRIDGE", BRAND_MARK],
        "$195 pre-order",
    ),
    Spec(
        "sg-002",
        "Stay Golden Shirt",
        "signature",
        {"primary": DARK, "accents": [GOLD]},
        ["STAY GOLDEN", BRAND_MARK],
        "$65 pre-order",
    ),
    Spec(
        "sg-003",
        "Stay Golden Shorts",
        "signature",
        {"primary": DARK, "accents": [GOLD]},
        ["STAY GOLDEN", BRAND_MARK],
        "$65 pre-order",
    ),
    Spec(
        "sg-004",
        "Signature Hoodie",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        [BRAND_MARK],
        "$55 draft",
    ),
    Spec(
        "sg-005",
        "Bay Bridge Shirt",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        ["BAY BRIDGE", BRAND_MARK],
        "$25 pre-order",
    ),
    Spec(
        "sg-006",
        "Mint & Lavender Hoodie",
        "signature",
        {"primary": MINT, "accents": [LAVENDER, ROSE_GOLD]},
        [BRAND_MARK],
        "$45 pre-order",
    ),
    Spec(
        "sg-007",
        "Signature Beanie",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        [BRAND_MARK],
        "$25 pre-order",
    ),
    Spec(
        "sg-009",
        "Signature Sherpa Jacket",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        [BRAND_MARK],
        "$80 pre-order",
    ),
    Spec(
        "sg-010",
        "Bridge Series Shorts",
        "signature",
        {"primary": DARK, "accents": [GOLD, ROSE_GOLD]},
        ["BAY BRIDGE", BRAND_MARK],
        "$60 pre-order",
    ),
    Spec(
        "sg-011",
        "Original Label Tee (White)",
        "signature",
        {"primary": WHITE, "accents": [DARK, ROSE_GOLD]},
        ["ORIGINAL LABEL", BRAND_MARK],
        "$30 pre-order",
    ),
    Spec(
        "sg-012",
        "Original Label Tee (Orchid)",
        "signature",
        {"primary": ORCHID, "accents": [DARK, ROSE_GOLD]},
        ["ORIGINAL LABEL", BRAND_MARK],
        "$30 pre-order",
    ),
    Spec(
        "sg-013",
        "Mint & Lavender Crewneck",
        "signature",
        {"primary": MINT, "accents": [LAVENDER, ROSE_GOLD]},
        [BRAND_MARK],
        "$40 pre-order",
    ),
    Spec(
        "sg-014",
        "Mint & Lavender Sweatpants",
        "signature",
        {"primary": MINT, "accents": [LAVENDER, ROSE_GOLD]},
        [BRAND_MARK],
        "$45 pre-order",
    ),
    # ── Kids Capsule (2) ──────────────────────────────────────────────────────
    Spec(
        "kids-001",
        "Kids Red Set",
        "kids",
        {"primary": CRIMSON, "accents": [DARK, ROSE_GOLD]},
        [BRAND_MARK],
        "$40 in-stock",
    ),
    Spec(
        "kids-002",
        "Kids Purple Set",
        "kids",
        {"primary": ORCHID, "accents": [DARK, ROSE_GOLD]},
        [BRAND_MARK],
        "$40 in-stock",
    ),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap master registry for live catalog.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would change without writing the manifest.",
    )
    args = parser.parse_args()

    m = Manifest.load()
    existing_locked = [sku for sku, e in m.masters.items() if e.is_locked]
    pending_before = sum(1 for e in m.masters.values() if e.status == "pending")

    created = 0
    refreshed = 0
    skipped_locked = 0

    for spec in CATALOG:
        entry = m.get(spec.sku)
        if entry is not None and entry.is_locked:
            skipped_locked += 1
            continue
        m.register_pending(
            sku=spec.sku,
            collection=spec.collection,
            color_spec=spec.color_spec,
            text_spec=spec.text_spec,
            notes=f"{spec.name} — {spec.notes}" if spec.notes else spec.name,
            overwrite=True,
        )
        if entry is None:
            created += 1
        else:
            refreshed += 1

    total_after = len(m.masters)
    pending_after = sum(1 for e in m.masters.values() if e.status == "pending")

    print("━" * 72)
    print(f"SkyyRose master registry — bootstrap {'(DRY RUN)' if args.dry_run else ''}")
    print("━" * 72)
    print(f"  Catalog SKUs defined in script:  {len(CATALOG)}")
    print(f"  Existing locked (preserved):     {skipped_locked}")
    print(f"  Pending entries created:         {created}")
    print(f"  Pending entries refreshed:       {refreshed}")
    print(
        f"  Total entries after bootstrap:   {total_after} ({pending_after} pending, {len(existing_locked)} locked)"
    )
    print("━" * 72)

    if args.dry_run:
        print("Dry run — manifest NOT written.")
        return 0

    path = m.save()
    print(f"Manifest written: {path}")
    print("Next: lock individual SKUs via Manifest.lock() as masters become available.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
