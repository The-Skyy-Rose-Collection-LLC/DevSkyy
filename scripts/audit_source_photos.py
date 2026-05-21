#!/usr/bin/env python3
"""Audit source product photography coverage and emit a structured manifest.

Scans the existing source-photo directories, infers each file's (sku, angle)
from its filename, classifies the SKU's garment type from its dossier's
``garment_type_lock``, and writes:

  * ``skyyrose/assets/images/source-products/manifest.json`` — machine-readable
    coverage matrix used by ``scripts/source_product_photos.py`` and the B2
    pipeline to gate compositor runs.
  * ``tasks/source-photo-audit-report.md`` — human-readable coverage report.
  * ``tasks/source-photo-shoot-list.md`` — sourcing plan for zero-coverage and
    under-coverage SKUs (per the resolved scope decision: techflats can stand in
    until photography ships).

Exit:
  0 always — this script reports rather than gates. CI gating lives in
  ``tests/test_source_photo_minimum.py`` (front + back required for B2).

Usage:
  python scripts/audit_source_photos.py
  python scripts/audit_source_photos.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.catalog_loader import read_catalog_rows  # noqa: E402
from skyyrose.core.dossier_loader import (  # noqa: E402
    DossierMissingError,
    get_product_with_dossier,
)

SOURCE_ROOTS = [
    ROOT / "skyyrose" / "assets" / "images" / "source-products",
    ROOT / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products",
]

MANIFEST_PATH = ROOT / "skyyrose" / "assets" / "images" / "source-products" / "manifest.json"
AUDIT_PATH = ROOT / "tasks" / "source-photo-audit-report.md"
SHOOT_LIST_PATH = ROOT / "tasks" / "source-photo-shoot-list.md"

# ---------------------------------------------------------------------------
# Required-angles policy by garment type
# ---------------------------------------------------------------------------

# Used by the compositor's pre-flight gate: a SKU must have at least
# ``MINIMUM_FOR_COMPOSITOR`` of these angles before scene compositing can run.
REQUIRED_ANGLES_BY_TYPE: dict[str, list[str]] = {
    "tee": ["front", "back", "three-quarter", "detail-graphic"],
    "hoodie": ["front", "back", "three-quarter", "detail-hood", "detail-pocket"],
    "crewneck": ["front", "back", "three-quarter", "detail-graphic"],
    "jersey": ["front", "back", "three-quarter", "detail-patch", "detail-stitching"],
    "shorts": ["front", "back", "side", "detail-pocket"],
    "joggers": ["front", "back", "side", "detail-pocket"],
    "set": ["combined-front", "top-only", "bottom-only", "back", "detail"],
    "jacket": ["front", "back", "three-quarter", "detail-hood", "detail-pocket"],
    "accessory": ["front", "back", "in-context"],
}

MINIMUM_FOR_COMPOSITOR = ["front", "back"]

# Filename pattern: ``{sku}-{any}-{angle}.{ext}`` is the dominant convention.
_ANGLE_RE = re.compile(
    r"-(front|back|side|three[-_]quarter|threequarter|"
    r"detail|detail[-_]graphic|detail[-_]hood|detail[-_]pocket|"
    r"detail[-_]patch|detail[-_]stitching|combined[-_]front|"
    r"top[-_]only|bottom[-_]only|in[-_]context|hanger|angled|"
    r"techflat|reference)\.(?:jpg|jpeg|png|webp)$",
    re.IGNORECASE,
)

_GARMENT_KEYWORDS: list[tuple[str, str]] = [
    ("crewneck", "crewneck"),
    ("hoodie", "hoodie"),
    ("sherpa jacket", "jacket"),
    ("jacket", "jacket"),
    ("bomber", "jacket"),
    ("windbreaker", "jacket"),
    ("jersey", "jersey"),
    ("baseball", "jersey"),
    ("hockey", "jersey"),
    ("basketball", "jersey"),
    ("set", "set"),
    ("shorts", "shorts"),
    ("joggers", "joggers"),
    ("pants", "joggers"),
    ("tee", "tee"),
    ("t-shirt", "tee"),
    ("hat", "accessory"),
    ("beanie", "accessory"),
    ("bag", "accessory"),
    ("wallet", "accessory"),
    ("fanny", "accessory"),
]


def _infer_garment_type(garment_lock: str, name: str) -> str:
    """Best-effort garment type from dossier garment_type_lock + product name."""
    haystack = f"{garment_lock} {name}".lower()
    for needle, gtype in _GARMENT_KEYWORDS:
        if needle in haystack:
            return gtype
    return "accessory"  # safest default — minimal angle requirements


def _required_angles(garment_type: str) -> list[str]:
    return REQUIRED_ANGLES_BY_TYPE.get(garment_type, ["front", "back", "three-quarter"])


@dataclass
class SkuPhotoCoverage:
    sku: str
    name: str
    collection: str
    garment_type: str
    required_angles: list[str]
    present_angles: list[str] = field(default_factory=list)
    missing_angles: list[str] = field(default_factory=list)
    photo_paths: dict[str, str] = field(default_factory=dict)
    has_minimum_for_compositor: bool = False
    source_type: str = "photography"  # "photography" | "techflat" | "missing"


def _scan_files() -> dict[str, dict[str, Path]]:
    """Return ``{sku: {angle: path}}`` for every matchable file across the
    source roots.
    """
    by_sku: dict[str, dict[str, Path]] = {}
    candidates: list[Path] = []
    for base in SOURCE_ROOTS:
        if base.is_dir():
            for ext in ("jpg", "jpeg", "png", "webp"):
                candidates.extend(base.rglob(f"*.{ext}"))
                candidates.extend(base.rglob(f"*.{ext.upper()}"))

    catalog_skus = sorted(
        (row["sku"] for row in read_catalog_rows() if row.get("sku")),
        key=len,
        reverse=True,  # match longest SKUs first
    )

    for path in candidates:
        name = path.name.lower()
        sku_match = next(
            (sku for sku in catalog_skus if name.startswith(sku.lower() + "-")),
            None,
        )
        if not sku_match:
            continue
        m = _ANGLE_RE.search(name)
        if not m:
            continue
        raw_angle = m.group(1).lower().replace("_", "-")
        # Normalize a few aliases to the canonical vocabulary
        if raw_angle == "threequarter":
            raw_angle = "three-quarter"
        bucket = by_sku.setdefault(sku_match, {})
        if raw_angle not in bucket:
            bucket[raw_angle] = path

    return by_sku


def _build_coverage_for(row: dict, photos_for_sku: dict[str, Path]) -> SkuPhotoCoverage:
    sku = row["sku"]
    name = row.get("name", "")
    collection = row.get("collection", "")

    garment_lock = ""
    try:
        merged = get_product_with_dossier(sku)
        garment_lock = merged["_dossier"].garment_type_lock
    except DossierMissingError:
        garment_lock = ""

    garment_type = _infer_garment_type(garment_lock, name)
    required = _required_angles(garment_type)

    present_set = set(photos_for_sku.keys())
    # Treat 'techflat' as a stand-in for 'front' per the resolved scope decision.
    if "front" not in present_set and "techflat" in present_set:
        present_set.add("front")
    if "reference" in present_set and "front" not in present_set:
        present_set.add("front")

    present = [a for a in required if a in present_set]
    missing = [a for a in required if a not in present_set]
    minimum_ok = all(a in present_set for a in MINIMUM_FOR_COMPOSITOR)

    if minimum_ok and any(
        p.startswith("front")
        for p in present_set
        if "techflat" in str(photos_for_sku.get(p, "")).lower()
    ):
        source_type = "techflat"
    elif minimum_ok:
        source_type = "photography"
    else:
        source_type = "missing"

    paths = {a: str(p.relative_to(ROOT)) for a, p in photos_for_sku.items()}

    return SkuPhotoCoverage(
        sku=sku,
        name=name,
        collection=collection,
        garment_type=garment_type,
        required_angles=required,
        present_angles=present,
        missing_angles=missing,
        photo_paths=paths,
        has_minimum_for_compositor=minimum_ok,
        source_type=source_type,
    )


def _summarize(coverages: list[SkuPhotoCoverage]) -> dict:
    total = len(coverages)
    minimum_ok = sum(1 for c in coverages if c.has_minimum_for_compositor)
    full_required = sum(1 for c in coverages if not c.missing_angles)
    by_source = {"photography": 0, "techflat": 0, "missing": 0}
    for c in coverages:
        by_source[c.source_type] = by_source.get(c.source_type, 0) + 1
    return {
        "total_active_skus": total,
        "compositor_ready": minimum_ok,
        "compositor_blocked": total - minimum_ok,
        "full_required_coverage": full_required,
        "by_source_type": by_source,
    }


def _render_audit_md(coverages: list[SkuPhotoCoverage], summary: dict) -> str:
    lines = [
        "# Source Product Photo Coverage Audit",
        "",
        "Auto-generated by `scripts/audit_source_photos.py`. ",
        "Scans `skyyrose/assets/images/source-products/` and "
        "`wordpress-theme/skyyrose-flagship/assets/images/products/`.",
        "",
        "## Summary",
        "",
        f"- Total active SKUs: **{summary['total_active_skus']}**",
        f"- Compositor-ready (front+back present): **{summary['compositor_ready']}**",
        f"- Compositor-blocked: **{summary['compositor_blocked']}**",
        f"- Full required-angle coverage: **{summary['full_required_coverage']}**",
        "",
        "### By source type",
        "",
        f"- Photography: **{summary['by_source_type'].get('photography', 0)}**",
        f"- Techflat stand-in: **{summary['by_source_type'].get('techflat', 0)}**",
        f"- Missing: **{summary['by_source_type'].get('missing', 0)}**",
        "",
        "## Per-SKU Coverage",
        "",
        "| SKU | Name | Type | Required | Present | Missing | Min ✓ | Source |",
        "|-----|------|------|----------|---------|---------|-------|--------|",
    ]
    for c in sorted(coverages, key=lambda r: (r.collection, r.sku)):
        lines.append(
            f"| `{c.sku}` | {c.name} | {c.garment_type} | "
            f"{len(c.required_angles)} | {len(c.present_angles)} | "
            f"{len(c.missing_angles)} | "
            f"{'✓' if c.has_minimum_for_compositor else '✗'} | "
            f"{c.source_type} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_shoot_list_md(coverages: list[SkuPhotoCoverage]) -> str:
    blocked = [c for c in coverages if not c.has_minimum_for_compositor]
    under = [c for c in coverages if c.has_minimum_for_compositor and c.missing_angles]
    lines = [
        "# Source Photography Shoot List",
        "",
        "Generated by `scripts/audit_source_photos.py`. ",
        "Use this as the brief for the next photo shoot or vendor handoff.",
        "",
        "## Tier 1 — Compositor-Blocked (front + back missing)",
        "",
        "These SKUs cannot run through the B2 compositor at all until at least ",
        "front + back are sourced. Per the resolved scope decision, techflats ",
        "can stand in temporarily — but real photography is the durable fix.",
        "",
    ]
    if not blocked:
        lines.append("_No compositor-blocked SKUs._")
    else:
        lines.append("| SKU | Name | Type | Missing |")
        lines.append("|-----|------|------|---------|")
        for c in sorted(blocked, key=lambda r: (r.collection, r.sku)):
            lines.append(
                f"| `{c.sku}` | {c.name} | {c.garment_type} | {', '.join(c.missing_angles)} |"
            )
    lines += [
        "",
        "## Tier 2 — Compositor-Ready, Under Required Coverage",
        "",
        "These SKUs work in B2 today (front+back are present) but are missing ",
        "detail or three-quarter angles that improve QA scores. Capture in the ",
        "next sourcing pass; not launch-blocking.",
        "",
    ]
    if not under:
        lines.append("_No SKUs in this tier._")
    else:
        lines.append("| SKU | Name | Type | Missing |")
        lines.append("|-----|------|------|---------|")
        for c in sorted(under, key=lambda r: (r.collection, r.sku)):
            lines.append(
                f"| `{c.sku}` | {c.name} | {c.garment_type} | {', '.join(c.missing_angles)} |"
            )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit source product photography")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = parser.parse_args()

    rows = list(read_catalog_rows())
    files_by_sku = _scan_files()

    coverages: list[SkuPhotoCoverage] = []
    for row in rows:
        sku = row.get("sku")
        if not sku:
            continue
        coverages.append(_build_coverage_for(row, files_by_sku.get(sku, {})))

    summary = _summarize(coverages)

    # Manifest
    manifest = {
        "version": "1.0.0",
        "generated_by": "scripts/audit_source_photos.py",
        "required_angles_by_garment_type": REQUIRED_ANGLES_BY_TYPE,
        "minimum_for_compositor": MINIMUM_FOR_COMPOSITOR,
        "summary": summary,
        "skus": {c.sku: asdict(c) for c in coverages},
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    if args.json:
        print(json.dumps(manifest, indent=2))
    else:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(_render_audit_md(coverages, summary))
        SHOOT_LIST_PATH.write_text(_render_shoot_list_md(coverages))
        print(f"Wrote manifest:    {MANIFEST_PATH.relative_to(ROOT)}")
        print(f"Wrote audit:       {AUDIT_PATH.relative_to(ROOT)}")
        print(f"Wrote shoot list:  {SHOOT_LIST_PATH.relative_to(ROOT)}")
        print(
            f"  ✓ {summary['compositor_ready']}/{summary['total_active_skus']} "
            f"SKUs compositor-ready, "
            f"{summary['compositor_blocked']} blocked, "
            f"{summary['full_required_coverage']} fully covered"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
