#!/usr/bin/env python3
"""validate_catalog_consistency.py — Read-only catalog/registry consistency checker.

Checks that all downstream files referencing SKUs or logos are consistent with
the two canonical data sources:
  1. wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv   (32 SKUs)
  2. wordpress-theme/skyyrose-flagship/data/logo-registry.json     (v4 logos)

Exit codes:
  0  — all checks pass (or all requested checks pass)
  1  — one or more checks failed
  2  — usage / argument error

Usage:
  python scripts/validate_catalog_consistency.py
  python scripts/validate_catalog_consistency.py --quiet
  python scripts/validate_catalog_consistency.py --checks jersey_skus,logo_skus
  python scripts/validate_catalog_consistency.py --json

Available check names (pass comma-separated to --checks):
  csv_readable          CSV file is present and well-formed
  registry_readable     logo-registry.json is present and valid JSON
  registry_version      registry version >= 4
  registry_changelog    changelog entries are present and have required fields
  jersey_skus           _JERSEY_SKUS frozenset in sku_resolver.py == registry sku_folders SKUs
  logo_skus             every SKU in sku_logos block exists in the CSV
  sku_folders           every SKU in sku_folders block exists in the CSV (non-comment keys)
  collocated_keys       co_located logos use filename key (not file)
  similarities_skus     every SKU key in product-similarities.json exists in CSV
  similarities_refs     every SKU in similarity arrays exists in CSV
  retired_sku_guard     no retired SKUs appear in checked downstream files
  dossier_slugs         dossier_slug values in CSV have matching .md files
  brand_primary         brand_primary logo id exists in logos block

Notes:
  jersey_skus: Compares _JERSEY_SKUS against registry sku_folders (not CSV garment_type_lock).
    The garment_type_lock column has a known data error for br-011 (shows 'hoodie', is a hockey
    jersey). The authoritative jersey set is sku_folders keys in logo-registry.json.
  sku_folders: Ignores keys starting with '_' (JSON comment convention).
  retired_sku_guard: Excludes logo-registry.json changelog text and this script's own
    _RETIRED_SKUS definition from the scan — those are documentation, not live references.
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path constants (all relative to repo root, derived from __file__ location)
# ---------------------------------------------------------------------------
# scripts/validate_catalog_consistency.py → parents[0] = scripts/ → parents[1] = repo root
_REPO_ROOT: Path = Path(__file__).resolve().parents[1]

_CATALOG_CSV: Path = (
    _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "skyyrose-catalog.csv"
)
_LOGO_REGISTRY: Path = (
    _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "logo-registry.json"
)
_SIMILARITIES_JSON: Path = (
    _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "product-similarities.json"
)
_SKU_RESOLVER_PY: Path = _REPO_ROOT / "skyyrose" / "elite_studio" / "sku_resolver.py"
_DOSSIERS_DIR: Path = _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "dossiers"

# Retired SKUs — must not appear in downstream files
_RETIRED_SKUS: frozenset[str] = frozenset({"br-013", "br-d01"})

# garment_type_lock values that identify jersey products
_JERSEY_GARMENT_TYPES: frozenset[str] = frozenset(
    {"baseball-jersey", "football-jersey", "basketball-jersey", "hockey-jersey", "jersey"}
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    results: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failure_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def add(self, result: CheckResult) -> None:
        self.results.append(result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ok(name: str, msg: str) -> CheckResult:
    return CheckResult(name=name, passed=True, message=msg)


def _fail(name: str, msg: str, details: list[str] | None = None) -> CheckResult:
    return CheckResult(name=name, passed=False, message=msg, details=details or [])


def _load_csv() -> list[dict[str, str]] | None:
    """Load catalog CSV; returns None on error."""
    if not _CATALOG_CSV.exists():
        return None
    try:
        with _CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except Exception:
        return None


def _load_registry() -> dict[str, Any] | None:
    """Load logo-registry.json; returns None on error."""
    if not _LOGO_REGISTRY.exists():
        return None
    try:
        return json.loads(_LOGO_REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return None


def _extract_jersey_skus_from_resolver() -> frozenset[str] | None:
    """Parse _JERSEY_SKUS frozenset from sku_resolver.py via AST (no import).

    Handles the canonical form:
        _JERSEY_SKUS: frozenset[str] = frozenset(
            {
                "br-003",
                ...
            }
        )

    The outer `frozenset(...)` is an ast.Call node; its first argument is an
    ast.Set node whose elements are ast.Constant string literals.
    """
    if not _SKU_RESOLVER_PY.exists():
        return None
    src = _SKU_RESOLVER_PY.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        # Handle both plain assignment and type-annotated assignment:
        #   _JERSEY_SKUS = frozenset({...})
        #   _JERSEY_SKUS: frozenset[str] = frozenset({...})
        if isinstance(node, ast.Assign):
            targets = node.targets
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value_node = node.value
        else:
            continue

        for target in targets:
            if not (isinstance(target, ast.Name) and target.id == "_JERSEY_SKUS"):
                continue
            if value_node is None:
                continue

            # Case 1: plain set literal  {  "br-003", ... }
            if isinstance(value_node, ast.Set):
                try:
                    return frozenset(ast.literal_eval(value_node))
                except (ValueError, TypeError):
                    return None

            # Case 2: frozenset({...}) — ast.Call with ast.Set as first arg
            if isinstance(value_node, ast.Call):
                args = value_node.args
                if not args:
                    return frozenset()
                inner = args[0]
                if isinstance(inner, ast.Set):
                    try:
                        return frozenset(ast.literal_eval(inner))
                    except (ValueError, TypeError):
                        return None
                # Inner arg may be something ast.literal_eval handles directly
                try:
                    val = ast.literal_eval(inner)
                    if isinstance(val, (frozenset, set)):
                        return frozenset(val)
                except (ValueError, TypeError):
                    pass

    return None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_csv_readable() -> CheckResult:
    name = "csv_readable"
    if not _CATALOG_CSV.exists():
        return _fail(name, f"CSV not found: {_CATALOG_CSV}")
    rows = _load_csv()
    if rows is None:
        return _fail(name, "CSV exists but could not be parsed")
    if not rows:
        return _fail(name, "CSV has no data rows")
    expected_cols = {"sku", "name", "collection", "garment_type_lock", "dossier_slug"}
    actual_cols = set(rows[0].keys())
    missing = expected_cols - actual_cols
    if missing:
        return _fail(name, f"CSV missing expected columns: {sorted(missing)}")
    return _ok(name, f"CSV readable — {len(rows)} rows, all required columns present")


def check_registry_readable() -> CheckResult:
    name = "registry_readable"
    if not _LOGO_REGISTRY.exists():
        return _fail(name, f"logo-registry.json not found: {_LOGO_REGISTRY}")
    reg = _load_registry()
    if reg is None:
        return _fail(name, "logo-registry.json exists but is not valid JSON")
    if "logos" not in reg:
        return _fail(name, "logo-registry.json missing top-level 'logos' key")
    return _ok(name, f"logo-registry.json readable — {len(reg.get('logos', {}))} logos")


def check_registry_version() -> CheckResult:
    name = "registry_version"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check version — registry not readable")
    version = reg.get("version", 0)
    try:
        v = int(version)
    except (TypeError, ValueError):
        return _fail(name, f"'version' is not an integer: {version!r}")
    if v < 4:
        return _fail(name, f"Registry version {v} < 4 (expected >= 4)")
    return _ok(name, f"Registry version={v} (>= 4)")


def check_registry_changelog() -> CheckResult:
    name = "registry_changelog"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check changelog — registry not readable")
    changelog = reg.get("changelog", [])
    if not changelog:
        return _fail(name, "Registry has no changelog entries")
    # Registry uses "changes" (list) not "notes" (string). Accept either.
    required_keys = {"version", "date"}
    recommended_keys = {"changes", "notes"}
    bad: list[str] = []
    for i, entry in enumerate(changelog):
        missing_required = required_keys - set(entry.keys())
        if missing_required:
            bad.append(f"entry[{i}] missing required keys: {sorted(missing_required)}")
        # At least one of changes/notes must be present
        if not (recommended_keys & set(entry.keys())):
            bad.append(f"entry[{i}] missing 'changes' or 'notes' key")
    if bad:
        return _fail(name, "Changelog entries have missing required fields", bad)
    return _ok(name, f"Changelog has {len(changelog)} valid entries")


def check_jersey_skus() -> CheckResult:
    """Verify _JERSEY_SKUS in sku_resolver.py matches the sku_folders block in logo-registry.json.

    sku_folders is the authoritative jersey list. The CSV garment_type_lock column has a known
    data error for br-011 (shows 'hoodie' but is a hockey jersey), so we do NOT use CSV as
    the source of truth for this check.
    """
    name = "jersey_skus"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check jersey SKUs — registry not readable")

    # sku_folders keys are authoritative jersey SKUs; skip _comment and other _-prefix keys
    sku_folders: dict[str, Any] = reg.get("sku_folders", {})
    registry_jersey_skus: set[str] = {k for k in sku_folders if not k.startswith("_")}

    resolver_skus = _extract_jersey_skus_from_resolver()
    if resolver_skus is None:
        return _fail(
            name,
            f"Could not parse _JERSEY_SKUS from {_SKU_RESOLVER_PY} — "
            "file missing or AST extraction failed",
        )

    extra_in_resolver = resolver_skus - registry_jersey_skus
    missing_in_resolver = registry_jersey_skus - resolver_skus

    if extra_in_resolver or missing_in_resolver:
        details = []
        if extra_in_resolver:
            details.append(
                f"In _JERSEY_SKUS but NOT in registry sku_folders: {sorted(extra_in_resolver)}"
            )
        if missing_in_resolver:
            details.append(
                f"In registry sku_folders but MISSING from _JERSEY_SKUS: {sorted(missing_in_resolver)}"
            )
        return _fail(
            name,
            "_JERSEY_SKUS in sku_resolver.py does not match registry sku_folders keys",
            details,
        )
    return _ok(
        name,
        f"_JERSEY_SKUS matches registry sku_folders exactly ({len(resolver_skus)} SKUs)",
    )


def check_logo_skus() -> CheckResult:
    name = "logo_skus"
    rows = _load_csv()
    reg = _load_registry()
    if rows is None:
        return _fail(name, "Cannot check logo_skus — CSV not readable")
    if reg is None:
        return _fail(name, "Cannot check logo_skus — registry not readable")

    csv_skus: set[str] = {row["sku"].strip() for row in rows}
    sku_logos: dict[str, Any] = reg.get("sku_logos", {})

    unknown: list[str] = [sku for sku in sku_logos if sku not in csv_skus]
    if unknown:
        return _fail(
            name,
            f"{len(unknown)} SKU(s) in sku_logos are not in the catalog CSV",
            [f"  Unknown SKU: {s}" for s in sorted(unknown)],
        )
    return _ok(name, f"All {len(sku_logos)} sku_logos SKUs are valid catalog SKUs")


def check_sku_folders() -> CheckResult:
    """Verify that every SKU key in sku_folders exists in the catalog CSV.

    Skips keys starting with '_' (e.g. '_comment') — those are JSON comment conventions.
    Does NOT enforce garment_type_lock == jersey for all entries because the CSV has a known
    data error for br-011 (garment_type_lock='hoodie' but it is a hockey jersey). The
    authoritative jersey classification lives in sku_folders itself.
    """
    name = "sku_folders"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check sku_folders — registry not readable")

    sku_folders: dict[str, str] = reg.get("sku_folders", {})
    # Exclude _-prefix keys (JSON comment convention, not real SKUs)
    real_skus: list[str] = [k for k in sku_folders if not k.startswith("_")]
    if not real_skus:
        return _ok(name, "sku_folders block has no real SKU keys — nothing to check")

    rows = _load_csv()
    if rows is None:
        return _fail(name, "Cannot check sku_folders — CSV not readable")

    csv_skus: set[str] = {row["sku"].strip() for row in rows}
    not_in_csv: list[str] = [sku for sku in real_skus if sku not in csv_skus]
    if not_in_csv:
        return _fail(
            name,
            f"{len(not_in_csv)} SKU(s) in sku_folders are not in the catalog CSV",
            [f"  Unknown SKU: {s}" for s in sorted(not_in_csv)],
        )
    return _ok(
        name,
        f"All {len(real_skus)} sku_folders SKUs exist in the catalog CSV",
    )


def check_collocated_keys() -> CheckResult:
    """All co_located_per_sku logos must use 'filename' not 'file'."""
    name = "collocated_keys"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check co-located keys — registry not readable")

    logos: dict[str, Any] = reg.get("logos", {})
    bad: list[str] = []
    for logo_id, entry in logos.items():
        if not entry.get("co_located_per_sku", False):
            continue
        if "filename" not in entry:
            bad.append(
                f"  {logo_id}: co_located_per_sku=true but missing 'filename' key"
                + (f" (has 'file': {entry['file']!r})" if "file" in entry else "")
            )
    if bad:
        return _fail(
            name,
            f"{len(bad)} co-located logo(s) use wrong key (need 'filename', not 'file')",
            bad,
        )
    co_count = sum(1 for e in logos.values() if e.get("co_located_per_sku", False))
    return _ok(name, f"All {co_count} co-located logos use 'filename' key correctly")


def check_similarities_skus() -> CheckResult:
    name = "similarities_skus"
    if not _SIMILARITIES_JSON.exists():
        return _ok(name, "product-similarities.json not present — skip")
    rows = _load_csv()
    if rows is None:
        return _fail(name, "Cannot check similarities SKUs — CSV not readable")

    csv_skus: set[str] = {row["sku"].strip() for row in rows}
    try:
        data = json.loads(_SIMILARITIES_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        return _fail(name, f"product-similarities.json is not valid JSON: {exc}")

    products: dict[str, Any] = data.get("products", {})
    unknown: list[str] = [sku for sku in products if sku not in csv_skus]
    if unknown:
        return _fail(
            name,
            f"{len(unknown)} top-level SKU(s) in product-similarities.json not in CSV",
            [f"  Unknown: {s}" for s in sorted(unknown)],
        )
    return _ok(
        name,
        f"All {len(products)} product-similarities.json top-level SKUs are valid",
    )


def check_similarities_refs() -> CheckResult:
    name = "similarities_refs"
    if not _SIMILARITIES_JSON.exists():
        return _ok(name, "product-similarities.json not present — skip")
    rows = _load_csv()
    if rows is None:
        return _fail(name, "Cannot check similarity refs — CSV not readable")

    csv_skus: set[str] = {row["sku"].strip() for row in rows}
    try:
        data = json.loads(_SIMILARITIES_JSON.read_text(encoding="utf-8"))
    except Exception:
        return _ok(name, "product-similarities.json not parseable — skipped by similarities_skus")

    products: dict[str, Any] = data.get("products", {})
    bad: list[str] = []
    for sku, product_data in products.items():
        for array_key in ("global", "same_collection"):
            for entry in product_data.get(array_key, []):
                ref_sku = entry.get("sku", "")
                if ref_sku and ref_sku not in csv_skus:
                    bad.append(f"  {sku}.{array_key}[].sku = {ref_sku!r} (not in CSV)")
    if bad:
        return _fail(
            name,
            f"{len(bad)} similarity reference(s) point to unknown SKUs",
            bad[:20],  # cap at 20 to avoid flooding
        )
    return _ok(name, "All similarity array references point to valid catalog SKUs")


def check_retired_sku_guard() -> CheckResult:
    """Scan downstream files for retired SKU strings.

    Exclusions (intentional — not bugs):
    - scripts/validate_catalog_consistency.py and scripts/sync_catalog_downstream.py are
      excluded because they legitimately contain the retired SKU as a source constant in
      _RETIRED_SKUS / sync exclusion sets. Scanning them would always produce false positives.
    - logo-registry.json changelog entries are historical records — the changelog section is
      excluded by stripping it before pattern-matching.
    """
    name = "retired_sku_guard"
    if not _RETIRED_SKUS:
        return _ok(name, "No retired SKUs configured")

    # Scripts that own the _RETIRED_SKUS constant — exclude from scan to avoid false positives
    _THIS_SCRIPT = Path(__file__).resolve()
    _SYNC_SCRIPT = _REPO_ROOT / "scripts" / "sync_catalog_downstream.py"

    # Files to scan (read-only check — do NOT add dossiers here per task constraint)
    targets: list[Path] = [
        _SIMILARITIES_JSON,
        _SKU_RESOLVER_PY,
        _REPO_ROOT / "skyyrose" / "elite_studio" / "commerce.py",
    ]

    pattern = re.compile(r"\b(" + "|".join(re.escape(s) for s in _RETIRED_SKUS) + r")\b")

    def _strip_py_comments(src: str) -> str:
        """Remove # comment lines from Python source before scanning.

        This avoids false positives from retirement-note comments like:
          # br-013 retired 2026-05-25: confirmed duplicate of br-003
        while still catching live references in string literals and code.
        We use a simple line-level approach (not a full tokenizer) — sufficient
        because SKU patterns in comments are the only known false-positive case.
        """
        stripped_lines = []
        for line in src.splitlines(keepends=True):
            # Strip inline comments too: take everything before the first unquoted '#'
            # Simple heuristic: strip from # if not inside a string
            code_part = line.split("#")[0] if "#" in line else line
            stripped_lines.append(code_part)
        return "".join(stripped_lines)

    hits: list[str] = []
    seen: set[Path] = set()

    for path in targets:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        # Skip the automation scripts that own the retired-SKU constant
        if resolved in (_THIS_SCRIPT, _SYNC_SCRIPT.resolve()):
            continue
        seen.add(resolved)
        raw_text = path.read_text(encoding="utf-8", errors="replace")
        # For Python files, strip comments before scanning to avoid retirement-note
        # false positives (e.g. "# br-013 retired 2026-05-25: ..." in sku_resolver.py)
        text = _strip_py_comments(raw_text) if path.suffix == ".py" else raw_text
        for match in pattern.finditer(text):
            lineno = raw_text[: match.start()].count("\n") + 1
            hits.append(f"  {path.relative_to(_REPO_ROOT)}:{lineno} — {match.group()!r}")

    # Scan logo-registry.json but exclude the changelog block (historical records)
    if _LOGO_REGISTRY.exists():
        try:
            reg_data = json.loads(_LOGO_REGISTRY.read_text(encoding="utf-8"))
            # Remove changelog from the data we check — it's a historical record
            reg_check = {k: v for k, v in reg_data.items() if k != "changelog"}
            reg_text = json.dumps(reg_check)
        except Exception:
            reg_text = _LOGO_REGISTRY.read_text(encoding="utf-8", errors="replace")
        for match in pattern.finditer(reg_text):
            lineno = reg_text[: match.start()].count("\n") + 1
            hits.append(f"  {_LOGO_REGISTRY.relative_to(_REPO_ROOT)}:{lineno} — {match.group()!r}")

    if hits:
        return _fail(
            name,
            f"Found {len(hits)} reference(s) to retired SKU(s) {sorted(_RETIRED_SKUS)}",
            hits,
        )
    return _ok(
        name,
        f"No references to retired SKUs {sorted(_RETIRED_SKUS)} in checked files",
    )


def check_dossier_slugs() -> CheckResult:
    name = "dossier_slugs"
    rows = _load_csv()
    if rows is None:
        return _fail(name, "Cannot check dossier slugs — CSV not readable")
    if not _DOSSIERS_DIR.exists():
        return _fail(name, f"Dossiers directory not found: {_DOSSIERS_DIR}")

    existing_slugs: set[str] = {p.stem for p in _DOSSIERS_DIR.glob("*.md")}
    missing: list[str] = []
    for row in rows:
        slug = row.get("dossier_slug", "").strip()
        if not slug:
            continue
        if slug not in existing_slugs:
            missing.append(f"  {row['sku']}: dossier_slug={slug!r} has no .md file")
    if missing:
        return _fail(
            name,
            f"{len(missing)} SKU(s) have dossier_slug values with no matching .md file",
            missing,
        )
    return _ok(name, "All dossier_slug values have matching .md files in dossiers/")


def check_brand_primary() -> CheckResult:
    name = "brand_primary"
    reg = _load_registry()
    if reg is None:
        return _fail(name, "Cannot check brand_primary — registry not readable")
    bp = reg.get("brand_primary", "")
    if not bp:
        return _fail(name, "Registry missing 'brand_primary' field")
    logos: dict[str, Any] = reg.get("logos", {})
    if bp not in logos:
        return _fail(
            name,
            f"brand_primary={bp!r} does not exist in logos block",
            [f"  Available logo IDs: {sorted(logos.keys())}"],
        )
    return _ok(name, f"brand_primary={bp!r} exists in logos block")


# ---------------------------------------------------------------------------
# Check registry
# ---------------------------------------------------------------------------

ALL_CHECKS: dict[str, Any] = {
    "csv_readable": check_csv_readable,
    "registry_readable": check_registry_readable,
    "registry_version": check_registry_version,
    "registry_changelog": check_registry_changelog,
    "jersey_skus": check_jersey_skus,
    "logo_skus": check_logo_skus,
    "sku_folders": check_sku_folders,
    "collocated_keys": check_collocated_keys,
    "similarities_skus": check_similarities_skus,
    "similarities_refs": check_similarities_refs,
    "retired_sku_guard": check_retired_sku_guard,
    "dossier_slugs": check_dossier_slugs,
    "brand_primary": check_brand_primary,
}

# Checks that must pass before others can meaningfully run
_FOUNDATION_CHECKS = ("csv_readable", "registry_readable")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_checks(
    check_names: list[str] | None = None,
    quiet: bool = False,
) -> ValidationReport:
    """Run the specified checks (or all) and return a report."""
    names = check_names if check_names else list(ALL_CHECKS.keys())

    # Validate requested check names
    unknown = [n for n in names if n not in ALL_CHECKS]
    if unknown:
        print(f"ERROR: Unknown check name(s): {unknown}", file=sys.stderr)
        print(f"Available: {sorted(ALL_CHECKS.keys())}", file=sys.stderr)
        sys.exit(2)

    report = ValidationReport()

    # Always run foundation checks first if not explicitly excluded
    foundation_results: dict[str, bool] = {}
    for fc in _FOUNDATION_CHECKS:
        if fc in ALL_CHECKS and fc not in names:
            result = ALL_CHECKS[fc]()
            foundation_results[fc] = result.passed
        elif fc in names:
            result = ALL_CHECKS[fc]()
            report.add(result)
            foundation_results[fc] = result.passed
            if not quiet:
                _print_result(result)

    # Run remaining checks
    foundation_ok = all(foundation_results.values())
    for check_name in names:
        if check_name in _FOUNDATION_CHECKS:
            continue  # Already ran above
        if not foundation_ok:
            # Skip checks that depend on readable data sources
            result = CheckResult(
                name=check_name,
                passed=False,
                message="SKIPPED — foundation checks failed (csv_readable or registry_readable)",
            )
        else:
            result = ALL_CHECKS[check_name]()
        report.add(result)
        if not quiet:
            _print_result(result)

    return report


def _print_result(result: CheckResult) -> None:
    icon = "PASS" if result.passed else "FAIL"
    print(f"  [{icon}] {result.name}: {result.message}")
    for detail in result.details:
        print(f"         {detail}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate catalog/registry consistency across the SkyyRose monorepo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available checks:\n  " + "\n  ".join(sorted(ALL_CHECKS.keys())),
    )
    parser.add_argument(
        "--checks",
        metavar="NAME[,NAME...]",
        help="Comma-separated list of check names to run (default: all)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-check output; only print summary",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON (implies --quiet for normal output)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    check_names: list[str] | None = None
    if args.checks:
        check_names = [c.strip() for c in args.checks.split(",") if c.strip()]

    quiet = args.quiet or args.json_output

    if not quiet:
        print("\nSkyyRose Catalog Consistency Validator")
        print("=" * 42)

    report = run_checks(check_names=check_names, quiet=quiet)

    if args.json_output:
        output = {
            "passed": report.passed,
            "failure_count": report.failure_count,
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details,
                }
                for r in report.results
            ],
        }
        print(json.dumps(output, indent=2))
        return 0 if report.passed else 1

    # Summary
    total = len(report.results)
    passed = total - report.failure_count
    print(f"\n{passed}/{total} checks passed", end="")
    if report.failure_count:
        print(f" — {report.failure_count} FAILED\n")
        return 1
    print(" — all clean\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
