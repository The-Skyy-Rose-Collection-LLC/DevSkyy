#!/usr/bin/env python3
"""Lint a single dossier file and report schema status + warnings.

Usage:
  python scripts/lint_dossier.py --slug black-rose-crewneck
  python scripts/lint_dossier.py --sku br-001
  python scripts/lint_dossier.py --file path/to/dossier.md

Exit code:
  0 — schema OK (warnings allowed and printed)
  1 — schema failure or file missing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from skyyrose.core.dossier_loader import (  # noqa: E402
    DossierMissingError,
    load_dossier,
    parse_dossier_markdown,
)
from skyyrose.core.dossier_schema import (  # noqa: E402
    DossierSchema,
    DossierSchemaError,
    coverage_for,
    load_validated_for_sku,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a single dossier")
    parser.add_argument("--slug", help="Dossier slug (e.g. black-rose-crewneck)")
    parser.add_argument("--sku", help="SKU (e.g. br-001)")
    parser.add_argument("--file", type=Path, help="Direct path to a dossier .md file")
    args = parser.parse_args()

    if not (args.slug or args.sku or args.file):
        parser.error("provide one of --slug / --sku / --file")

    try:
        if args.sku:
            schema = load_validated_for_sku(args.sku)
        elif args.slug:
            raw = load_dossier(args.slug)
            schema = DossierSchema.from_raw(raw)
        else:
            raw = parse_dossier_markdown(args.file.read_text(encoding="utf-8"))
            schema = DossierSchema.from_raw(raw)
    except DossierMissingError as exc:
        print(f"MISSING: {exc}", file=sys.stderr)
        return 1
    except DossierSchemaError as exc:
        print(f"SCHEMA FAIL: {exc}", file=sys.stderr)
        return 1

    coverage = coverage_for(schema)
    print(f"PASS schema: {schema.sku} — {schema.name} ({schema.collection})")
    print(f"  regions: {coverage.region_count}")
    print(f"  hex coverage: {coverage.hex_coverage_pct}%")
    print(f"  pantone coverage: {coverage.pantone_coverage_pct}%")
    if coverage.warnings:
        print("  warnings:")
        for w in coverage.warnings:
            print(f"    - {w}")
    else:
        print("  warnings: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
