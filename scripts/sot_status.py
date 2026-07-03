#!/usr/bin/env python3
"""sot_status.py — unified SOT freshness dashboard.

Aggregates the EXISTING catalog/theme/imagery validators into one domain table:
    domain | artifact | check | status

It does not reimplement any validator — each domain row either (a) shells out to or
imports an existing checker and rolls its result up, or (b) is an explicit UNCHECKED
row naming the one-line reason no validator is wired yet. The only genuinely new check
introduced here is the live WooCommerce reconcile (scripts/wc_reconcile.py).

Status values:
    OK            — the underlying validator(s) passed
    DRIFT         — the underlying validator(s) found inconsistency
    BROKEN        — the validator itself could not run (missing file, bad JSON, etc.)
    UNCHECKED     — no validator is wired for this domain (reason given)
    LIVE-SKIPPED  — a live check was requested but credentials/network were unavailable

Exit code is non-zero only when a row is DRIFT or BROKEN. UNCHECKED and LIVE-SKIPPED
are informational and never fail the run (so the weekly CI job and a creds-absent
dev run both stay green).

Usage:
    python scripts/sot_status.py             # table, no live WC probe
    python scripts/sot_status.py --live      # + read-only WC reconcile
    python scripts/sot_status.py --json      # machine-readable
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THEME = REPO_ROOT / "wordpress-theme" / "skyyrose-flagship"
PYTHON = sys.executable

# Needed for `from skyyrose.core import asset_hub` (hub pixels domain) and
# `from scripts import wc_reconcile` (WC store domain) to resolve when this file is
# invoked directly (`python scripts/sot_status.py`), where sys.path[0] is scripts/,
# not the repo root. Set once at import time so domain functions don't depend on
# each other's execution order to get REPO_ROOT onto sys.path first.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OK = "OK"
DRIFT = "DRIFT"
BROKEN = "BROKEN"
UNCHECKED = "UNCHECKED"
LIVE_SKIPPED = "LIVE-SKIPPED"

_FAILING_STATUSES = frozenset({DRIFT, BROKEN})

# validate_catalog_consistency.py checks that get their own domain row instead of
# rolling up into the generic "catalog" row.
_DOSSIER_CHECK_NAMES = frozenset({"dossier_slugs"})
_IMAGERY_CHECK_NAMES = frozenset({"sot_images_current"})


@dataclass(frozen=True)
class DomainStatus:
    domain: str
    artifact: str
    check: str
    status: str
    detail: str = ""


# ---------------------------------------------------------------------------
# Pure helpers — no subprocess/network, fixture-testable
# ---------------------------------------------------------------------------


def status_from_checks(results: dict[str, tuple[bool, str]]) -> tuple[str, str]:
    """Roll a set of named (passed, message) results up into (status, detail).

    Empty input is BROKEN (the caller couldn't even collect any results) — a check
    with zero results run is never silently OK.
    """
    if not results:
        return BROKEN, "no check results collected"
    failed = {name: msg for name, (passed, msg) in results.items() if not passed}
    if failed:
        detail = "; ".join(f"{name}: {msg}" for name, msg in sorted(failed.items()))
        return DRIFT, detail
    return OK, f"{len(results)}/{len(results)} checks passed"


def unchecked(reason: str) -> tuple[str, str]:
    return UNCHECKED, reason


def broken(reason: str) -> tuple[str, str]:
    return BROKEN, reason


def build_row(
    domain: str, artifact: str, check: str, status_detail: tuple[str, str]
) -> DomainStatus:
    status, detail = status_detail
    return DomainStatus(domain=domain, artifact=artifact, check=check, status=status, detail=detail)


def overall_exit_code(rows: list[DomainStatus]) -> int:
    return 1 if any(r.status in _FAILING_STATUSES for r in rows) else 0


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _run(cmd: list[str], *, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout)


# ---------------------------------------------------------------------------
# scripts/validate_catalog_consistency.py — covers catalog, dossiers (partial),
# and product imagery (partial)
# ---------------------------------------------------------------------------


def _validate_catalog_checks() -> dict[str, tuple[bool, str]] | None:
    """Run validate_catalog_consistency.py --json once. None on hard failure to run."""
    try:
        proc = _run([PYTHON, "scripts/validate_catalog_consistency.py", "--json"])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"__error__": (False, f"failed to launch validator: {exc}")}
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None
    return {c["name"]: (bool(c["passed"]), c.get("message", "")) for c in data.get("checks", [])}


def _catalog_domain(catalog_checks: dict[str, tuple[bool, str]] | None) -> DomainStatus:
    if catalog_checks is None:
        return build_row(
            "catalog",
            "skyyrose-catalog.csv + logo-registry.json",
            "validate_catalog_consistency.py --json",
            broken("validator produced no parseable JSON output"),
        )
    subset = {
        name: result
        for name, result in catalog_checks.items()
        if name not in _DOSSIER_CHECK_NAMES and name not in _IMAGERY_CHECK_NAMES
    }
    return build_row(
        "catalog",
        "skyyrose-catalog.csv + logo-registry.json",
        "validate_catalog_consistency.py --json",
        status_from_checks(subset),
    )


# ---------------------------------------------------------------------------
# dossiers — validate_catalog_consistency.py's dossier_slugs + the two dedicated
# dossier scripts (dossier-check.yml CI job)
# ---------------------------------------------------------------------------


def _run_exit_only(cmd: list[str]) -> tuple[bool, str]:
    try:
        proc = _run(cmd)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"failed to launch {cmd[-1]}: {exc}"
    if proc.returncode == 0:
        return True, "exit 0"
    tail = (proc.stdout or proc.stderr or "").strip().splitlines()
    return False, tail[-1] if tail else f"exit {proc.returncode}"


def _dossiers_domain(catalog_checks: dict[str, tuple[bool, str]] | None) -> DomainStatus:
    results: dict[str, tuple[bool, str]] = {}
    if catalog_checks is not None:
        for name in _DOSSIER_CHECK_NAMES:
            if name in catalog_checks:
                results[name] = catalog_checks[name]
    results["check_dossier_coverage"] = _run_exit_only(
        [PYTHON, "scripts/check_dossier_coverage.py"]
    )
    results["validate_dossier"] = _run_exit_only([PYTHON, "scripts/validate_dossier.py"])
    return build_row(
        "dossiers",
        "wordpress-theme/skyyrose-flagship/data/dossiers/",
        "check_dossier_coverage.py + validate_dossier.py + dossier_slugs",
        status_from_checks(results),
    )


# ---------------------------------------------------------------------------
# product imagery — validate_catalog_consistency.py's sot_images_current
# ---------------------------------------------------------------------------


def _product_imagery_domain(catalog_checks: dict[str, tuple[bool, str]] | None) -> DomainStatus:
    if catalog_checks is None:
        return build_row(
            "product imagery (sot-images)",
            "data/sot-images.json",
            "sot_images_current (validate_catalog_consistency.py)",
            broken("validator produced no parseable JSON output"),
        )
    subset = {n: r for n, r in catalog_checks.items() if n in _IMAGERY_CHECK_NAMES}
    return build_row(
        "product imagery (sot-images)",
        "data/sot-images.json",
        "sot_images_current (validate_catalog_consistency.py)",
        status_from_checks(subset),
    )


# ---------------------------------------------------------------------------
# non-product imagery — no validator exists
# ---------------------------------------------------------------------------


def _non_product_imagery_domain() -> DomainStatus:
    return build_row(
        "non-product imagery (visual-manifest)",
        "wordpress-theme/skyyrose-flagship/data/visual-manifest.json",
        "none",
        unchecked(
            "no standalone consistency validator exists for visual-manifest.json vs "
            "the actual non-product image files on disk — verified manually per CLAUDE.md"
        ),
    )


# ---------------------------------------------------------------------------
# collection content (sot.json x4) — data/verify-collection-sot.py directly
# (the same script freshness-guard.sh's CHECK 1 shells out to)
# ---------------------------------------------------------------------------


def _collection_content_domain() -> DomainStatus:
    script = THEME / "data" / "verify-collection-sot.py"
    if not script.exists():
        return build_row(
            "collection content (sot.json x4)",
            "wordpress-theme/skyyrose-flagship/data/collections/*/sot.json",
            "data/verify-collection-sot.py",
            broken(f"verifier not found: {script}"),
        )
    passed, detail = _run_exit_only([PYTHON, str(script)])
    return build_row(
        "collection content (sot.json x4)",
        "wordpress-theme/skyyrose-flagship/data/collections/*/sot.json",
        "data/verify-collection-sot.py",
        (OK, detail) if passed else (DRIFT, detail),
    )


# ---------------------------------------------------------------------------
# brand canon — hand-authored source text, nothing generated to diff against
# ---------------------------------------------------------------------------


def _brand_canon_domain() -> DomainStatus:
    return build_row(
        "brand canon",
        "knowledge-base/seed/from-interview.md",
        "none",
        unchecked(
            "founder-authored source text — no generated downstream artifact exists "
            "to diff against for drift"
        ),
    )


# ---------------------------------------------------------------------------
# theme version triple — style.css / functions.php / readme.txt agreement
# (freshness-guard.sh CHECK 3, parsed from its --all output; not re-derived)
# ---------------------------------------------------------------------------


def _parse_freshness_guard_section(output: str, header_prefix: str) -> bool | None:
    """Find the freshness-guard.sh section whose header starts with `header_prefix`
    and return True if its body contains a checkmark line, False if a cross line,
    None if the section wasn't found at all (script didn't run / output shape changed).
    """
    clean = _strip_ansi(output)
    lines = clean.splitlines()
    in_section = False
    saw_result = None
    for line in lines:
        stripped = line.strip()
        if re.match(r"^\d+\.\s", stripped):
            if in_section:
                break  # next numbered section — stop
            in_section = stripped.startswith(header_prefix)
            continue
        if not in_section:
            continue
        if stripped.startswith("✓"):  # ✓
            saw_result = True
        elif stripped.startswith("✗"):  # ✗
            saw_result = False
    return saw_result


def _run_freshness_guard_all() -> tuple[bool, str]:
    """Run freshness-guard.sh --all once; return (ran_ok, raw_stdout)."""
    script = REPO_ROOT / "scripts" / "freshness-guard.sh"
    if not script.exists():
        return False, ""
    try:
        proc = _run(["bash", str(script), "--all"], timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return True, proc.stdout


def _theme_version_domain(freshness_output: str | None) -> DomainStatus:
    artifact = "style.css + functions.php + readme.txt"
    check = "freshness-guard.sh --all (section 3)"
    if freshness_output is None:
        return build_row(
            "theme version triple", artifact, check, broken("freshness-guard.sh --all did not run")
        )
    result = _parse_freshness_guard_section(freshness_output, "3. Theme version sync")
    if result is None:
        return build_row(
            "theme version triple",
            artifact,
            check,
            broken("could not locate 'Theme version sync' section in freshness-guard output"),
        )
    return build_row(
        "theme version triple",
        artifact,
        check,
        (
            (OK, "versions synced")
            if result
            else (DRIFT, "version mismatch — see freshness-guard output")
        ),
    )


# ---------------------------------------------------------------------------
# hub pixels — skyyrose.core.asset_hub.verify_integrity() (existing validator)
# ---------------------------------------------------------------------------


def _hub_pixels_domain() -> DomainStatus:
    artifact = "assets/hub/manifest.json"
    check = "skyyrose.core.asset_hub.verify_integrity()"
    # Every verified manifest entry's pixels live under the gitignored
    # assets/hub/collections/ tree (see .gitignore "/assets/*" rule) — the manifest
    # itself is tracked and always present, but a fresh checkout or CI runner never
    # has the pixels. Presence-gate the same way _presence_probe does for 3D/GLB
    # and scene backdrops: absent tree -> UNCHECKED, not a DRIFT false alarm.
    pixels_dir = REPO_ROOT / "assets" / "hub" / "collections"
    if not pixels_dir.exists():
        return build_row(
            "hub pixels",
            artifact,
            check,
            unchecked(f"gitignored disk asset dir not present in this checkout: {pixels_dir}"),
        )
    try:
        from skyyrose.core import asset_hub  # noqa: PLC0415
    except ImportError as exc:
        return build_row("hub pixels", artifact, check, broken(f"import failed: {exc}"))
    try:
        problems = asset_hub.verify_integrity()
    except (
        Exception
    ) as exc:  # noqa: BLE001 — surface any validator crash as BROKEN, not a hard stop
        return build_row("hub pixels", artifact, check, broken(f"verify_integrity() raised: {exc}"))
    if problems:
        return build_row("hub pixels", artifact, check, (DRIFT, "; ".join(problems[:5])))
    return build_row("hub pixels", artifact, check, (OK, "every verified entry resolves on disk"))


# ---------------------------------------------------------------------------
# 3D/GLB + scene backdrops — presence probes only (gitignored disk assets; no
# content-consistency validator exists, so this checks existence, not drift)
# ---------------------------------------------------------------------------


def _presence_probe(domain: str, dir_path: Path, artifact_label: str) -> DomainStatus:
    check = "presence probe (directory exists + non-empty)"
    if not dir_path.exists():
        return build_row(
            domain,
            artifact_label,
            check,
            unchecked(f"gitignored disk asset dir not present in this checkout: {dir_path}"),
        )
    has_content = any(dir_path.iterdir())
    return build_row(
        domain,
        artifact_label,
        check,
        (OK, "present, non-empty") if has_content else (DRIFT, "directory exists but is empty"),
    )


def _glb_domain() -> DomainStatus:
    return _presence_probe("3D/GLB", REPO_ROOT / "renders" / "3d", "renders/3d/ (GLBs + qc/*.json)")


def _scene_backdrops_domain() -> DomainStatus:
    return _presence_probe(
        "scene backdrops",
        THEME / "assets" / "scenes",
        "wordpress-theme/skyyrose-flagship/assets/scenes/",
    )


# ---------------------------------------------------------------------------
# fonts — no validator exists
# ---------------------------------------------------------------------------


def _fonts_domain() -> DomainStatus:
    return build_row(
        "fonts",
        "wordpress-theme/skyyrose-flagship/theme.json (Font Library)",
        "none",
        unchecked(
            "no automated check — self-hosted font declarations are hand-maintained "
            "(see docs/google-fonts-selfhost.md)"
        ),
    )


# ---------------------------------------------------------------------------
# WC store — the one NEW check (scripts/wc_reconcile.py)
# ---------------------------------------------------------------------------


def _wc_store_domain(*, live: bool) -> DomainStatus:
    artifact = "https://skyyrose.co (WooCommerce REST) vs skyyrose-catalog.csv"
    check = "scripts/wc_reconcile.py (read-only GET)"
    if not live:
        return build_row(
            "WC store", artifact, check, (LIVE_SKIPPED, "run with --live to reconcile")
        )
    from scripts import wc_reconcile  # noqa: PLC0415 — deferred: only needed when --live

    try:
        result = wc_reconcile.reconcile()
    except wc_reconcile.CredentialsMissing as exc:
        return build_row("WC store", artifact, check, (LIVE_SKIPPED, str(exc)))
    except Exception as exc:  # noqa: BLE001 — network/API errors surface as BROKEN, not a crash
        return build_row("WC store", artifact, check, broken(f"live fetch failed: {exc}"))
    if result.clean:
        detail = f"{result.csv_count} CSV / {result.live_count} live SKUs — no drift"
        return build_row("WC store", artifact, check, (OK, detail))
    parts = []
    if result.csv_only:
        parts.append(f"{len(result.csv_only)} CSV-only")
    if result.live_only:
        parts.append(f"{len(result.live_only)} live-only")
    if result.field_drift:
        parts.append(f"{len(result.field_drift)} field drift")
    return build_row("WC store", artifact, check, (DRIFT, ", ".join(parts)))


# ---------------------------------------------------------------------------
# WP menus / legal pages — live-only, no repo artifact, no probe implemented
# ---------------------------------------------------------------------------


def _wp_menus_domain() -> DomainStatus:
    return build_row(
        "WP menus",
        "live-only (WordPress nav menus)",
        "none",
        unchecked("live-only surface, not backed by a repo artifact — no probe implemented yet"),
    )


def _legal_pages_domain() -> DomainStatus:
    return build_row(
        "legal pages",
        "live-only (WP.com published pages)",
        "none",
        unchecked(
            "live-only surface published via WP.com MCP — no probe implemented yet "
            "(pages themselves are live per project memory)"
        ),
    )


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_domain_table(*, live: bool = False) -> list[DomainStatus]:
    catalog_checks = _validate_catalog_checks()
    ran_freshness, freshness_output = _run_freshness_guard_all()

    return [
        _catalog_domain(catalog_checks),
        _dossiers_domain(catalog_checks),
        _product_imagery_domain(catalog_checks),
        _non_product_imagery_domain(),
        _collection_content_domain(),
        _brand_canon_domain(),
        _theme_version_domain(freshness_output if ran_freshness else None),
        _hub_pixels_domain(),
        _glb_domain(),
        _scene_backdrops_domain(),
        _fonts_domain(),
        _wc_store_domain(live=live),
        _wp_menus_domain(),
        _legal_pages_domain(),
    ]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_table(rows: list[DomainStatus]) -> str:
    domain_w = max(len(r.domain) for r in rows) + 2
    status_w = max(len(r.status) for r in rows) + 2
    lines = [f"{'DOMAIN':<{domain_w}}{'STATUS':<{status_w}}CHECK / DETAIL"]
    lines.append("-" * (domain_w + status_w + 40))
    for r in rows:
        lines.append(f"{r.domain:<{domain_w}}{r.status:<{status_w}}{r.check}")
        if r.detail:
            lines.append(f"{'':<{domain_w}}{'':<{status_w}}  {r.detail}")
    return "\n".join(lines)


def render_json(rows: list[DomainStatus]) -> str:
    return json.dumps(
        {
            "passed": overall_exit_code(rows) == 0,
            "rows": [
                {
                    "domain": r.domain,
                    "artifact": r.artifact,
                    "check": r.check,
                    "status": r.status,
                    "detail": r.detail,
                }
                for r in rows
            ],
        },
        indent=2,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--live", action="store_true", help="run the live WC reconcile probe")
    parser.add_argument(
        "--json", dest="json_output", action="store_true", help="machine-readable output"
    )
    args = parser.parse_args(argv)

    rows = build_domain_table(live=args.live)

    if args.json_output:
        print(render_json(rows))
    else:
        print(render_table(rows))

    return overall_exit_code(rows)


if __name__ == "__main__":
    sys.exit(main())
