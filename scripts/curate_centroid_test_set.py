#!/usr/bin/env python3
"""Curate the labeled good/bad render fixtures the centroid harness needs.

Classifies images that already live in the repo into GOOD (on-brand hero
renders held out from centroid training) and BAD (visually distinct
archetypes that should fail an on-brand gate). Symlinks them into
``tests/fixtures/centroid_gate/{good,bad}/`` so the harness has a flat
directory of files to score, while the underlying bytes stay where they
already live in the repo.

This is intentionally conservative: it does NOT generate new renders. The
test set is a snapshot of what's already in the working tree, classified
by filename pattern + source path. Re-run anytime — the script is
idempotent and writes a manifest recording every classification decision.

Usage:
    python3 scripts/curate_centroid_test_set.py
    python3 scripts/curate_centroid_test_set.py --clean   # wipe and rebuild
    python3 scripts/curate_centroid_test_set.py --output tests/fixtures/centroid_gate

Classification rules (see ADR-0002 for context):

GOOD (held out from centroid training):
  * wordpress-theme/skyyrose-flagship/assets/images/products/*-back-model.webp
      → back-angle hero renders; same aesthetic as front renders, different angle
  * skyyrose/elite_studio/assets/golden/<sku>/front.jpg
      → golden-fixture front hero shots (different fidelity, on-brand)
  * skyyrose/elite_studio/assets/golden/<sku>/reference.jpg
      → reference turntable shots (on-brand by definition)

BAD (visually distinct from hero renders):
  * wordpress-theme/skyyrose-flagship/assets/images/products/*-techflat-*.jpeg
      → orthographic technical flats on white background
  * wordpress-theme/skyyrose-flagship/assets/images/products/*-source.jpg
      → raw product photography (no model, no scene)
  * wordpress-theme/skyyrose-flagship/assets/images/products/*-design.jpg
      → design previews / flat mockup art
  * wordpress-theme/skyyrose-flagship/assets/images/products/*-branding.webp
      → branding/sleeve detail closeups (distinct framing)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PRODUCTS = REPO / "wordpress-theme" / "skyyrose-flagship" / "assets" / "images" / "products"
GOLDEN = REPO / "skyyrose" / "elite_studio" / "assets" / "golden"


@dataclass
class Candidate:
    source: Path
    label: str  # "good" or "bad"
    category: str  # finer-grained: back-model, golden-front, techflat, source, design, branding


@dataclass
class CurationResult:
    good: list[Candidate] = field(default_factory=list)
    bad: list[Candidate] = field(default_factory=list)


def _discover_good() -> list[Candidate]:
    out: list[Candidate] = []
    for p in sorted(PRODUCTS.glob("*-back-model.webp")):
        out.append(Candidate(source=p, label="good", category="back-model"))
    for sku_dir in sorted(GOLDEN.iterdir()) if GOLDEN.is_dir() else []:
        if not sku_dir.is_dir():
            continue
        for fname in ("front.jpg", "reference.jpg"):
            cand = sku_dir / fname
            if cand.is_file():
                category = "golden-front" if fname == "front.jpg" else "golden-reference"
                out.append(Candidate(source=cand, label="good", category=category))
    return out


def _discover_bad() -> list[Candidate]:
    out: list[Candidate] = []
    if not PRODUCTS.is_dir():
        return out
    patterns = (
        ("*-techflat-*.jpeg", "techflat"),
        ("*-techflat-*.jpg", "techflat"),
        ("*-techflat-*.png", "techflat"),
        ("*-techflat-*.webp", "techflat"),
        ("*-source.jpg", "source"),
        ("*-source.jpeg", "source"),
        ("*-source.png", "source"),
        ("*-source.webp", "source"),
        ("*-design.jpg", "design"),
        ("*-design.jpeg", "design"),
        ("*-design.png", "design"),
        ("*-design.webp", "design"),
        ("*-branding.webp", "branding"),
        ("*-branding.jpg", "branding"),
        ("*-branding.jpeg", "branding"),
        ("*-branding.png", "branding"),
    )
    seen: set[Path] = set()
    for glob, category in patterns:
        for p in sorted(PRODUCTS.glob(glob)):
            if p in seen:
                continue
            seen.add(p)
            out.append(Candidate(source=p, label="bad", category=category))
    return out


def _unique_target_name(source: Path) -> str:
    """Choose a flat-dir filename that disambiguates source location.

    Two candidates can have the same basename (e.g., golden/<sku>/front.jpg
    appears once per SKU). Prefix the SKU directory name to disambiguate.
    """
    if source.parent.name and source.parent != PRODUCTS:
        return f"{source.parent.name}__{source.name}"
    return source.name


def _materialize(candidates: list[Candidate], target_dir: Path) -> list[dict]:
    target_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries: list[dict] = []
    for c in candidates:
        link_name = _unique_target_name(c.source)
        link_path = target_dir / link_name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        rel_target = os.path.relpath(c.source, start=link_path.parent)
        os.symlink(rel_target, link_path)
        manifest_entries.append(
            {
                "fixture_filename": link_name,
                "source_path": str(c.source.relative_to(REPO)),
                "label": c.label,
                "category": c.category,
                "size_bytes": c.source.stat().st_size,
            }
        )
    return manifest_entries


def _wipe(target_dir: Path) -> None:
    if not target_dir.exists():
        return
    for entry in target_dir.iterdir():
        if entry.is_symlink() or entry.is_file():
            entry.unlink()


def _write_manifest(output_dir: Path, good_entries: list[dict], bad_entries: list[dict]) -> Path:
    manifest = {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "repo_root": str(REPO),
        "good_count": len(good_entries),
        "bad_count": len(bad_entries),
        "good": good_entries,
        "bad": bad_entries,
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path


def _write_readme(output_dir: Path, good_entries: list[dict], bad_entries: list[dict]) -> None:
    by_cat_good: dict[str, int] = {}
    by_cat_bad: dict[str, int] = {}
    for e in good_entries:
        by_cat_good[e["category"]] = by_cat_good.get(e["category"], 0) + 1
    for e in bad_entries:
        by_cat_bad[e["category"]] = by_cat_bad.get(e["category"], 0) + 1

    readme = output_dir / "README.md"
    lines = [
        "# Centroid gate test fixtures",
        "",
        "Generated by `scripts/curate_centroid_test_set.py`. Do not edit by hand —",
        "re-run the script to refresh.",
        "",
        "These directories contain symlinks to existing repo images, classified into",
        "GOOD (on-brand hero renders held out from centroid training) and BAD",
        "(visually distinct image archetypes). The brand-centroid measurement harness",
        "(`scripts/measure_brand_centroid_gate.py`) reads them to compute false-pass",
        "and false-fail rates per ADR-0002.",
        "",
        f"## good/  ({len(good_entries)} files)",
        "",
    ]
    for cat, n in sorted(by_cat_good.items()):
        lines.append(f"- {cat}: {n}")
    lines += [
        "",
        f"## bad/  ({len(bad_entries)} files)",
        "",
    ]
    for cat, n in sorted(by_cat_bad.items()):
        lines.append(f"- {cat}: {n}")
    lines += [
        "",
        "## Provenance",
        "",
        "Full per-file source paths are recorded in `manifest.json`. The classification",
        "decisions are documented in the curate script's docstring.",
        "",
    ]
    readme.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO / "tests" / "fixtures" / "centroid_gate",
        help="Output directory (will contain good/ and bad/ subdirs)",
    )
    parser.add_argument(
        "--clean", action="store_true", help="Wipe existing fixture dirs before regenerating"
    )
    args = parser.parse_args()

    good_dir = args.output / "good"
    bad_dir = args.output / "bad"

    if args.clean:
        _wipe(good_dir)
        _wipe(bad_dir)

    good_candidates = _discover_good()
    bad_candidates = _discover_bad()

    if not good_candidates:
        print("FATAL: no good candidates discovered", file=sys.stderr)
        return 2
    if not bad_candidates:
        print("FATAL: no bad candidates discovered", file=sys.stderr)
        return 2

    good_entries = _materialize(good_candidates, good_dir)
    bad_entries = _materialize(bad_candidates, bad_dir)

    manifest_path = _write_manifest(args.output, good_entries, bad_entries)
    _write_readme(args.output, good_entries, bad_entries)

    print(f"Curated {len(good_entries)} good + {len(bad_entries)} bad fixtures")
    print(f"  good/ : {good_dir}")
    print(f"  bad/  : {bad_dir}")
    print(f"  manifest: {manifest_path}")

    cat_good: dict[str, int] = {}
    cat_bad: dict[str, int] = {}
    for e in good_entries:
        cat_good[e["category"]] = cat_good.get(e["category"], 0) + 1
    for e in bad_entries:
        cat_bad[e["category"]] = cat_bad.get(e["category"], 0) + 1
    print("  good categories:", dict(sorted(cat_good.items())))
    print("  bad categories: ", dict(sorted(cat_bad.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
