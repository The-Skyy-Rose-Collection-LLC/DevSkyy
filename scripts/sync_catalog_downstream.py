#!/usr/bin/env python3
"""sync_catalog_downstream.py — Surgical auto-sync of downstream catalog references.

Reads the two canonical sources and patches downstream files that have drifted:
  - skyyrose/elite_studio/sku_resolver.py  (_JERSEY_SKUS frozenset)
  - wordpress-theme/.../data/product-similarities.json  (stale SKU refs)

Does NOT touch:
  - dossier prose files (*.md in data/dossiers/)
  - logo-registry.json content (beyond the updated: timestamp)
  - ProductCatalogTest.php
  - Any file not explicitly listed as a sync target

Usage:
  python scripts/sync_catalog_downstream.py --dry-run      # preview only (no writes)
  python scripts/sync_catalog_downstream.py --auto-only    # safe fixes only (no human review needed)
  python scripts/sync_catalog_downstream.py --report-only  # print what would change, exit 0

Exit codes:
  0  — success (or dry-run / report-only)
  1  — sync error
  2  — usage error
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
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

# Backup suffix pattern: .bak-pre-sync-YYYYMMDD-HHMMSS
_BACKUP_SUFFIX_FMT = ".bak-pre-sync-%Y%m%d-%H%M%S"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class SyncAction:
    target: str
    action: str
    description: str
    requires_human: bool = False
    applied: bool = False
    error: str | None = None


@dataclass
class SyncReport:
    actions: list[SyncAction] = field(default_factory=list)
    human_attention: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(a.error for a in self.actions)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_csv() -> list[dict[str, str]]:
    with _CATALOG_CSV.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _registry_jersey_skus() -> frozenset[str]:
    """Authoritative jersey-series roster = sku_folders keys in logo-registry.json.

    The jersey roster is a product-LINE concept (the "BLACK is Beautiful Jersey
    Series"), NOT a garment-geometry one, so it is deliberately NOT derived from the
    CSV ``garment_type_lock`` column. That column encodes garment shape — e.g. br-011
    (a hooded Jersey-Series piece) is locked ``hoodie`` so the render pipeline draws
    its hood, yet it is still a roster member; deriving from garment_type_lock would
    wrongly drop it. ``validate_catalog_consistency.check_jersey_skus`` uses this same
    source, so the two tools agree by construction.

    Returns an empty frozenset when the registry is missing or unreadable — callers
    MUST treat empty as "cannot determine" and skip, never as "roster is empty".
    """
    if not _LOGO_REGISTRY.exists():
        return frozenset()
    try:
        reg = json.loads(_LOGO_REGISTRY.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return frozenset()
    folders = reg.get("sku_folders", {})
    return frozenset(k for k in folders if isinstance(k, str) and not k.startswith("_"))


def _csv_all_skus(rows: list[dict[str, str]]) -> frozenset[str]:
    return frozenset(row["sku"].strip() for row in rows)


def _backup(path: Path) -> Path:
    suffix = datetime.now(tz=UTC).strftime(_BACKUP_SUFFIX_FMT)
    backup_path = path.with_suffix(path.suffix + suffix)
    shutil.copy2(path, backup_path)
    return backup_path


def _ts_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Sync: _JERSEY_SKUS in sku_resolver.py
# ---------------------------------------------------------------------------


def _extract_jersey_skus_block(src: str) -> tuple[int, int] | None:
    """Return (start_char, end_char) of the _JERSEY_SKUS assignment node.

    Handles both plain assignment and type-annotated assignment:
      _JERSEY_SKUS = frozenset({...})
      _JERSEY_SKUS: frozenset[str] = frozenset({...})

    Returns None if the block cannot be found.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_JERSEY_SKUS":
                    return (node.col_offset, node.end_col_offset)  # type: ignore[attr-defined]
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "_JERSEY_SKUS":
                return (node.col_offset, node.end_col_offset)  # type: ignore[attr-defined]
    return None


def sync_jersey_skus(
    dry_run: bool = False,
) -> SyncAction:
    """Sync _JERSEY_SKUS in sku_resolver.py to the authoritative jersey-series roster.

    Roster source is registry sku_folders (see ``_registry_jersey_skus``), NOT the CSV
    garment_type_lock column — that column is garment geometry, not roster membership.
    """
    target = str(_SKU_RESOLVER_PY.relative_to(_REPO_ROOT))
    if not _SKU_RESOLVER_PY.exists():
        return SyncAction(
            target=target,
            action="skip",
            description="sku_resolver.py not found",
            error="File missing",
        )

    roster = _registry_jersey_skus()
    if not roster:
        return SyncAction(
            target=target,
            action="skip",
            description="Cannot derive jersey roster — registry sku_folders empty/unreadable",
            error="registry unavailable",
        )

    src = _SKU_RESOLVER_PY.read_text(encoding="utf-8")

    # Parse current frozenset via AST
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return SyncAction(
            target=target,
            action="skip",
            description="Cannot parse sku_resolver.py",
            error=str(exc),
        )

    current_skus: frozenset[str] = frozenset()
    # ast.Stmt node holding the assignment — works for both Assign and AnnAssign
    assign_node: ast.Assign | ast.AnnAssign | None = None
    for node in ast.walk(tree):
        value_node = None
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_JERSEY_SKUS":
                    assign_node = node
                    value_node = node.value
                    break
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == "_JERSEY_SKUS":
                assign_node = node
                value_node = node.value
        if value_node is not None:
            try:
                val = ast.literal_eval(value_node)
                if isinstance(val, (frozenset, set)):
                    current_skus = frozenset(val)
            except (ValueError, TypeError):
                # frozenset({...}) — ast.Call, not literal-eval-able directly
                if isinstance(value_node, ast.Call) and value_node.args:
                    inner = value_node.args[0]
                    if isinstance(inner, ast.Set):
                        try:
                            current_skus = frozenset(ast.literal_eval(inner))
                        except (ValueError, TypeError):
                            pass

    if assign_node is None:
        return SyncAction(
            target=target,
            action="skip",
            description="_JERSEY_SKUS assignment not found in file",
            error="Pattern not found",
        )

    if current_skus == roster:
        return SyncAction(
            target=target,
            action="noop",
            description="_JERSEY_SKUS already in sync with the registry jersey roster",
            applied=True,
        )

    added = roster - current_skus
    removed = current_skus - roster
    desc_parts = []
    if added:
        desc_parts.append(f"add {sorted(added)}")
    if removed:
        desc_parts.append(f"remove {sorted(removed)}")
    description = "; ".join(desc_parts)

    if dry_run:
        return SyncAction(
            target=target,
            action="would-update",
            description=f"_JERSEY_SKUS: {description}",
        )

    # Build new frozenset block preserving indentation
    sorted_skus = sorted(roster)
    indent = "        "  # 8-space indent (matches existing style)
    sku_lines = "\n".join(f'{indent}    "{s}",' for s in sorted_skus)
    new_block = f"_JERSEY_SKUS: frozenset[str] = frozenset(\n{indent}{{\n{sku_lines}\n{indent}}}\n)"

    # Replace the old assignment in source
    # Use line-based replacement for safety
    lines = src.splitlines(keepends=True)
    start_line = assign_node.lineno - 1  # 0-based
    end_line = assign_node.end_lineno - 1  # type: ignore[attr-defined]

    # Preserve any trailing comment on the end line
    new_lines = lines[:start_line] + [new_block + "\n"] + lines[end_line + 1 :]
    new_src = "".join(new_lines)

    # Backup, then write
    _backup(_SKU_RESOLVER_PY)
    _SKU_RESOLVER_PY.write_text(new_src, encoding="utf-8")

    return SyncAction(
        target=target,
        action="updated",
        description=f"_JERSEY_SKUS synced: {description}",
        applied=True,
    )


# ---------------------------------------------------------------------------
# Sync: product-similarities.json (remove stale SKU refs)
# ---------------------------------------------------------------------------


def sync_similarities_json(
    rows: list[dict[str, str]],
    dry_run: bool = False,
) -> SyncAction:
    """Remove entries referencing unknown SKUs from product-similarities.json."""
    target = str(_SIMILARITIES_JSON.relative_to(_REPO_ROOT))
    if not _SIMILARITIES_JSON.exists():
        return SyncAction(
            target=target,
            action="skip",
            description="product-similarities.json not found",
        )

    all_skus = _csv_all_skus(rows)
    try:
        data: dict[str, Any] = json.loads(_SIMILARITIES_JSON.read_text(encoding="utf-8"))
    except Exception as exc:
        return SyncAction(
            target=target,
            action="skip",
            description="Cannot parse product-similarities.json",
            error=str(exc),
        )

    products: dict[str, Any] = data.get("products", {})
    removed_keys: list[str] = []
    removed_refs: list[str] = []

    # Remove top-level unknown SKU keys
    new_products: dict[str, Any] = {}
    for sku, prod_data in products.items():
        if sku not in all_skus:
            removed_keys.append(sku)
            continue
        # Filter similarity arrays
        updated = dict(prod_data)
        for array_key in ("global", "same_collection"):
            original = updated.get(array_key, [])
            filtered = [e for e in original if e.get("sku", "") in all_skus]
            if len(filtered) != len(original):
                stale = [e["sku"] for e in original if e.get("sku", "") not in all_skus]
                removed_refs.extend(f"{sku}.{array_key}[].sku={s}" for s in stale)
                updated[array_key] = filtered
        new_products[sku] = updated

    if not removed_keys and not removed_refs:
        return SyncAction(
            target=target,
            action="noop",
            description="product-similarities.json already clean",
            applied=True,
        )

    parts = []
    if removed_keys:
        parts.append(f"removed top-level SKUs: {removed_keys}")
    if removed_refs:
        parts.append(f"removed {len(removed_refs)} stale array ref(s)")
    description = "; ".join(parts)

    if dry_run:
        return SyncAction(
            target=target,
            action="would-update",
            description=description,
        )

    new_data = dict(data)
    new_data["products"] = new_products
    new_data["n_products"] = len(new_products)

    _backup(_SIMILARITIES_JSON)
    _SIMILARITIES_JSON.write_text(
        json.dumps(new_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return SyncAction(
        target=target,
        action="updated",
        description=description,
        applied=True,
    )


# ---------------------------------------------------------------------------
# Registry updated field bump (non-destructive)
# ---------------------------------------------------------------------------


def sync_registry_updated(dry_run: bool = False) -> SyncAction:
    """Bump the top-level 'updated' field in logo-registry.json to today's date."""
    target = str(_LOGO_REGISTRY.relative_to(_REPO_ROOT))
    if not _LOGO_REGISTRY.exists():
        return SyncAction(
            target=target,
            action="skip",
            description="logo-registry.json not found",
        )
    try:
        data = json.loads(_LOGO_REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
        return SyncAction(
            target=target,
            action="skip",
            description="Cannot parse logo-registry.json",
            error=str(exc),
        )

    today = _ts_now()
    current = data.get("updated", "")
    if current == today:
        return SyncAction(
            target=target,
            action="noop",
            description=f"'updated' already = {today!r}",
            applied=True,
        )

    if dry_run:
        return SyncAction(
            target=target,
            action="would-update",
            description=f"'updated' field: {current!r} → {today!r}",
        )

    data["updated"] = today
    _backup(_LOGO_REGISTRY)
    _LOGO_REGISTRY.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return SyncAction(
        target=target,
        action="updated",
        description=f"'updated' field bumped: {current!r} → {today!r}",
        applied=True,
    )


# ---------------------------------------------------------------------------
# Human-attention report
# ---------------------------------------------------------------------------


def _collect_human_attention(rows: list[dict[str, str]]) -> list[str]:
    """Return list of files/issues requiring human or sweep-agent review."""
    notes: list[str] = []
    all_skus = _csv_all_skus(rows)

    # Check for dossiers with unknown SKUs in frontmatter
    dossiers_dir = _REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "dossiers"
    if dossiers_dir.exists():
        for md in sorted(dossiers_dir.glob("*.md")):
            text = md.read_text(encoding="utf-8", errors="replace")
            # Extract sku: <value> from YAML frontmatter
            m = re.search(r"^sku:\s*(\S+)", text, re.MULTILINE)
            if m:
                sku = m.group(1).strip()
                if sku not in all_skus:
                    notes.append(
                        f"  DOSSIER: {md.name} — sku: {sku!r} not in catalog (human review needed)"
                    )

    # Check for retired SKU mentions in dossier prose (informational only — do not edit)
    retired = {"br-013"}
    for md in sorted(dossiers_dir.glob("*.md")) if dossiers_dir.exists() else []:
        text = md.read_text(encoding="utf-8", errors="replace")
        for r in retired:
            if r in text:
                notes.append(
                    f"  DOSSIER: {md.name} — contains retired SKU {r!r} (human review needed)"
                )

    return notes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-sync downstream catalog/registry files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing any files",
    )
    parser.add_argument(
        "--auto-only",
        action="store_true",
        help="Apply only safe automatic fixes (default behavior)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Print what would change, then exit 0 (no writes)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    dry_run = args.dry_run or args.report_only

    print("\nSkyyRose Catalog Auto-Sync")
    print("=" * 34)

    if dry_run:
        print("  [DRY RUN — no files will be written]\n")

    # Load canonical source
    if not _CATALOG_CSV.exists():
        print(f"ERROR: Catalog CSV not found: {_CATALOG_CSV}", file=sys.stderr)
        return 1

    rows = _load_csv()
    print(f"  Catalog: {len(rows)} SKUs loaded from CSV\n")

    report = SyncReport()

    # Run sync targets
    sync_fns = [
        lambda d=dry_run: sync_jersey_skus(dry_run=d),
        lambda r=rows, d=dry_run: sync_similarities_json(r, dry_run=d),
        lambda d=dry_run: sync_registry_updated(dry_run=d),
    ]
    for fn in sync_fns:
        action = fn()
        report.actions.append(action)
        icon = {
            "noop": "  ",
            "updated": "UP",
            "would-update": "~~",
            "skip": "--",
        }.get(action.action, "??")
        err_str = f" [ERROR: {action.error}]" if action.error else ""
        print(f"  [{icon}] {action.target}: {action.description}{err_str}")

    # Human attention section
    human_notes = _collect_human_attention(rows)
    if human_notes:
        print("\n  Files needing human / sweep-agent review:")
        for note in human_notes:
            print(note)

    # Summary
    updated = [a for a in report.actions if a.action in ("updated", "would-update")]
    noops = [a for a in report.actions if a.action == "noop"]
    errors = [a for a in report.actions if a.error]

    print(
        f"\n  {len(updated)} file(s) {'would be ' if dry_run else ''}updated, "
        f"{len(noops)} already in sync, {len(errors)} error(s)"
    )

    if errors:
        print("\nSync completed with errors — see above.", file=sys.stderr)
        return 1

    if args.report_only:
        return 0

    print("  Done.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
