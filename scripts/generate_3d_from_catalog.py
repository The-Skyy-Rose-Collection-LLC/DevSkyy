"""
SKU-to-3D-model batch orchestrator (Tripo3D image_to_model).
==============================================================

End-to-end pipeline: catalog SKU -> SOT packshot image -> Tripo3D
`image_to_model` generation -> asset validation -> SKU-organized archive ->
`Model3DGeneration` DB row.

Provider call path deliberately bypasses `TripoProvider` / `provider_factory`:
a single bare `TripoAssetAgent()` is constructed directly (per
`agents/tripo_agent.py`) and shared across the batch loop, so multi-account
credential resolution (`_ensure_credentials_resolved()`) happens once and is
cached for every subsequent call.

Two passes:
  1. Zero-cost validation (always runs first, no confirmation): resolves and
     checks every catalog SKU's packshot on disk, and probes the Tripo
     account balance (read-only `get_balance()`). Safe with `--dry-run`.
  2. Single-SKU paid dispatch (`--sku`): STOP-AND-SHOW gated per
     `skyyrose/elite_studio/pipeline3d/cli.py`'s `_confirm()` — the gate
     fails closed on a non-interactive context, opts in only via
     `SKYYROSE_AUTO_CONFIRM=1` or an explicit interactive `y`/`yes`.

Full-batch dispatch (`--all`, all 33 SKUs in one run) is explicitly OUT OF
SCOPE for this version — see `run()`.

Usage:
    python scripts/generate_3d_from_catalog.py --dry-run
    python scripts/generate_3d_from_catalog.py --sku br-001 --budget 50
"""

from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.storage.r2_client import AssetCategory, R2Client, R2Error

from agents.errors import ConfigurationError
from agents.models import Model3DGeneration
from agents.tripo_agent import TripoAssetAgent, TripoConfig
from agents.tripo_credentials import TripoCredentials, resolve_tripo_credentials
from database import db_manager
from skyyrose.core import sot_images
from skyyrose.core.catalog_loader import read_catalog_rows
from skyyrose.core.paths import REPO_ROOT, THEME_ROOT

# Per-generation Tripo3D credit cost for the `image_to_model` endpoint.
# CONFIRMED — a real 2026-07-22 dispatch (br-001, this session) measured
# ~20cr via the account balance delta (pre-balance minus post-balance).
# Distinct from the other pinned Tripo cost in this codebase (10cr/SKU, see
# `scripts/tripo_dispatch.py`), which is for `generate_multiview_image` +
# `flux.1_kontext_pro` — a DIFFERENT template.
TRIPO_IMAGE_TO_MODEL_CREDITS_ESTIMATE = float(
    os.getenv("TRIPO_IMAGE_TO_MODEL_CREDITS_ESTIMATE", "20")
)

# Gitignored (see .gitignore: "assets/3d-models-generated/") — generated,
# regenerable paid output, never committed.
OUTPUT_ROOT: Path = REPO_ROOT / "assets" / "3d-models-generated"


@dataclass(frozen=True)
class SkuReadiness:
    """Zero-cost validation pass result for one catalog SKU."""

    sku: str
    name: str
    ready: bool
    reason: str
    resolved_path: Path | None


@dataclass(frozen=True)
class DispatchManifest:
    """STOP-AND-SHOW cost manifest for a set of target SKUs."""

    skus: tuple[str, ...]
    cost_per_generation: float
    total_cost: float
    balance: float | None
    balance_after: float | None
    insufficient_balance: bool


# =============================================================================
# Zero-cost validation pass
# =============================================================================


def _resolve_sku_source_image(sku: str) -> tuple[Path | None, str]:
    """Resolve one SKU's packshot source image to an absolute, on-disk path.

    Calls `sot_images.resolve_image(sku, role="packshot")` — the SOT only
    DECLARES a theme-relative path; this also verifies the file actually
    exists on disk, joining the declared path onto `THEME_ROOT` first (the
    SOT contract is theme-relative, never absolute).

    Returns:
        `(absolute_path, "")` on success, or `(None, reason)` when the SOT
        has no packshot for the SKU or the declared file is missing on disk.
    """
    theme_relative = sot_images.resolve_image(sku, role="packshot")
    if not theme_relative:
        return None, "no packshot image declared in SOT"

    absolute = THEME_ROOT / theme_relative
    if not absolute.exists():
        return None, f"declared packshot missing on disk: {absolute}"

    return absolute, ""


def resolve_sku_readiness(catalog_rows: Sequence[dict[str, str]]) -> list[SkuReadiness]:
    """Zero-cost readiness check for every catalog row (spends nothing)."""
    readiness: list[SkuReadiness] = []
    for row in catalog_rows:
        sku = row["sku"]
        name = row.get("name", sku)
        path, reason = _resolve_sku_source_image(sku)
        readiness.append(
            SkuReadiness(
                sku=sku, name=name, ready=path is not None, reason=reason, resolved_path=path
            )
        )
    return readiness


def print_readiness_table(readiness: Sequence[SkuReadiness]) -> None:
    """Per-SKU ready/blocked table plus a final ready/blocked count."""
    print("\nSKU readiness (zero-cost validation pass):")
    for r in readiness:
        status = "READY" if r.ready else "BLOCKED"
        print(f"  {r.sku:<14} {status:<8} {r.name}")
        if not r.ready:
            print(f"      -> {r.reason}")
    ready_count = sum(1 for r in readiness if r.ready)
    print(
        f"\nReady: {ready_count}/{len(readiness)}   Blocked: {len(readiness) - ready_count}/{len(readiness)}"
    )


# =============================================================================
# Manifest math + budget gate
# =============================================================================


def build_manifest(
    skus: Sequence[str], *, cost_per_generation: float, balance: float | None
) -> DispatchManifest:
    """Compute the STOP-AND-SHOW cost manifest for `skus`.

    `balance_after` / `insufficient_balance` are `None` / `False` when
    `balance` is unknown (e.g. the free credential probe failed) — an
    unknown balance is not treated as insufficient.
    """
    total = len(skus) * cost_per_generation
    balance_after = None if balance is None else balance - total
    insufficient = balance_after is not None and balance_after < 0
    return DispatchManifest(
        skus=tuple(skus),
        cost_per_generation=cost_per_generation,
        total_cost=total,
        balance=balance,
        balance_after=balance_after,
        insufficient_balance=insufficient,
    )


def exceeds_budget(manifest: DispatchManifest, budget_ceiling: float | None) -> bool:
    """True when `manifest.total_cost` exceeds an explicit `--budget` ceiling.

    `budget_ceiling=None` means no ceiling was configured -> never exceeds.
    Checked BEFORE any dispatch begins (see `run()`), not per-item after
    the fact.
    """
    return budget_ceiling is not None and manifest.total_cost > budget_ceiling


def print_manifest(manifest: DispatchManifest, sources: dict[str, Path]) -> None:
    """Print the exact STOP-AND-SHOW manifest before any dispatch."""
    lines = ["", "=" * 70, "STOP — Confirm before proceeding:", "=" * 70]
    lines.append("  Action : Tripo3D image_to_model (paid)")
    for sku in manifest.skus:
        lines.append(f"    {sku:<14} source={sources[sku]}")
    lines.append(
        f"  Cost   : {len(manifest.skus)} SKU(s) x "
        f"{manifest.cost_per_generation:.2f} cr (TRIPO_IMAGE_TO_MODEL_CREDITS_ESTIMATE "
        "— confirmed via 2026-07-22 dispatch balance delta)"
    )
    lines.append(f"  Total  : ~{manifest.total_cost:.2f} credits")
    if manifest.balance is not None:
        status = "INSUFFICIENT" if manifest.insufficient_balance else "OK"
        lines.append(
            f"  Balance: {manifest.balance:.2f} cr  ->  after: "
            f"{manifest.balance_after:.2f} cr  [{status}]"
        )
        if manifest.insufficient_balance:
            print("  WARNING: insufficient balance — top up before dispatching.")
    lines.append("=" * 70)
    print("\n".join(lines))


def _confirm() -> bool:
    """STOP-AND-SHOW gate. Fail-closed, modeled on
    `skyyrose/elite_studio/pipeline3d/cli.py`'s `_confirm()`.

    Resolution order:
      * `SKYYROSE_AUTO_CONFIRM=1`  -> explicit batch opt-in, proceeds.
      * no TTY (CI, cron, subprocess, pytest) -> ABORTS. Never auto-approves
        a paid call on a missing TTY.
      * interactive TTY -> prompts for an explicit `y`/`yes`.
    """
    sys.stdout.write("\nProceed? [y/N] ")
    sys.stdout.flush()
    if os.getenv("SKYYROSE_AUTO_CONFIRM") == "1":
        sys.stdout.write("\nauto-confirmed via SKYYROSE_AUTO_CONFIRM=1\n")
        return True
    if not sys.stdin.isatty():
        sys.stdout.write(
            "\nnon-interactive context — aborting paid dispatch "
            "(set SKYYROSE_AUTO_CONFIRM=1 to allow)\n"
        )
        return False
    try:
        return input().strip().lower() in {"y", "yes"}
    except EOFError:
        return False


# =============================================================================
# Dispatch (single-SKU only — see run()'s --all guard)
# =============================================================================


def _validation_status(validation: dict[str, Any]) -> str:
    """Map an `AssetValidation` dict onto a short DB status string."""
    if not validation.get("is_valid", True):
        return "invalid"
    if validation.get("warnings"):
        return "warnings"
    return "valid"


async def dispatch_sku(
    agent: TripoAssetAgent, *, sku: str, name: str, source_image: Path
) -> dict[str, Any]:
    """Generate -> validate -> archive -> upload -> DB-record for one SKU.

    Moves the GLB from the agent's own output dir into
    `assets/3d-models-generated/<sku>/<sku>.glb`, uploads it (and, when
    present, Tripo's own rendered-preview image) to R2, and writes a
    `Model3DGeneration` row via the project's async `db_manager` singleton
    (`database/CLAUDE.md`'s hard rule: all DB access goes through
    `async with db_manager.session() as session`).

    The GLB upload is the point of this pipeline (a servable model) -- an
    `R2Error` there propagates and no DB row is written. The rendered-preview
    upload is best-effort: on failure only branding VLM scoring loses
    Tripo's own preview image, so it's reported and dispatch continues.
    """
    result = await agent._tool_generate_from_image(
        image_path=str(source_image),
        product_name=name,
        output_format="glb",
    )
    generated_path = Path(result["model_path"])

    validation = await agent._tool_validate_asset(model_path=str(generated_path))

    final_dir = OUTPUT_ROOT / sku
    final_dir.mkdir(parents=True, exist_ok=True)
    final_path = final_dir / f"{sku}.glb"
    shutil.move(str(generated_path), str(final_path))

    status = _validation_status(validation)

    r2 = R2Client()
    model_upload = r2.upload_file(final_path, category=AssetCategory.MODEL_3D, product_id=sku)

    rendered_preview_r2_key: str | None = None
    thumbnail_path = result.get("thumbnail_path")
    if thumbnail_path and Path(thumbnail_path).exists():
        try:
            preview_upload = r2.upload_file(
                thumbnail_path, category=AssetCategory.THUMBNAIL, product_id=sku
            )
            rendered_preview_r2_key = preview_upload.key
        except R2Error as exc:
            print(
                f"  WARNING: R2 upload of rendered-preview image failed for {sku} "
                f"({thumbnail_path}) -- continuing without it; branding VLM scoring "
                f"won't have Tripo's preview available: {exc}"
            )

    await db_manager.initialize()
    async with db_manager.session() as session:
        session.add(
            Model3DGeneration(
                id=uuid.uuid4(),
                sku=sku,
                task_id=result["task_id"],
                provider="tripo3d",
                format="glb",
                model_path=str(final_path),
                source_image_path=str(source_image),
                validation_status=status,
                validation_details=validation,
                model_r2_key=model_upload.key,
                rendered_preview_r2_key=rendered_preview_r2_key,
            )
        )
        await session.commit()

    return {
        "sku": sku,
        "task_id": result["task_id"],
        "model_path": str(final_path),
        "validation_status": status,
        "model_r2_key": model_upload.key,
        "rendered_preview_r2_key": rendered_preview_r2_key,
    }


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="generate_3d_from_catalog",
        description="SKU-to-3D-model batch orchestrator (Tripo3D image_to_model).",
    )
    p.add_argument(
        "--sku", default=None, help="Single SKU to dispatch (required unless --dry-run)."
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run only the zero-cost validation pass; never reach the confirmation gate.",
    )
    p.add_argument(
        "--budget",
        type=float,
        default=None,
        help="Credit ceiling. Checked BEFORE any dispatch begins; aborts if the manifest total exceeds it.",
    )
    p.add_argument(
        "--all",
        action="store_true",
        help="NOT IMPLEMENTED in this version.",
    )
    return p


async def _resolve_readiness_and_credentials(
    catalog_rows: list[dict[str, str]],
) -> tuple[list[SkuReadiness], float | None, TripoCredentials | None]:
    """Zero-cost validation pass: SKU readiness table + a read-only balance probe."""
    readiness = resolve_sku_readiness(catalog_rows)
    print_readiness_table(readiness)

    try:
        creds = await resolve_tripo_credentials()
        print(
            f"\nTripo credentials resolved: "
            f"{'global (.ai)' if creds.is_global else 'china (.com)'} region, "
            f"balance={creds.balance:.2f} cr"
        )
        return readiness, creds.balance, creds
    except ConfigurationError as exc:
        print(f"\nTripo credential resolution FAILED: {exc}")
        return readiness, None, None


async def run(argv: list[str]) -> int:
    """Programmatic entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    if args.all:
        raise SystemExit(
            "full-batch dispatch is not available in this version -- run --sku one at a time."
        )

    catalog_rows = read_catalog_rows()
    readiness, balance, creds = await _resolve_readiness_and_credentials(catalog_rows)

    if args.dry_run:
        return 0

    if not args.sku:
        sys.stderr.write("error: --sku is required unless --dry-run is passed\n")
        return 2

    target = next((r for r in readiness if r.sku == args.sku), None)
    if target is None:
        sys.stderr.write(f"error: SKU {args.sku!r} not found in catalog\n")
        return 2

    if not target.ready:
        print(f"\nSKIP {target.sku} — {target.reason}")
        return 1

    assert target.resolved_path is not None, "ready implies resolved_path is set"

    manifest = build_manifest(
        [target.sku], cost_per_generation=TRIPO_IMAGE_TO_MODEL_CREDITS_ESTIMATE, balance=balance
    )
    print_manifest(manifest, {target.sku: target.resolved_path})

    if exceeds_budget(manifest, args.budget):
        sys.stderr.write(
            f"estimated cost {manifest.total_cost:.2f} cr exceeds budget ceiling "
            f"{args.budget:.2f} cr -- aborting (raise --budget)\n"
        )
        return 1

    if not _confirm():
        print("aborted by user")
        return 1

    row = next(r for r in catalog_rows if r["sku"] == target.sku)
    # Reuse the already-probed credentials so the account charged always matches
    # the account+balance shown in the manifest above -- letting TripoAssetAgent()
    # re-resolve here could pick a different account if balances shifted between
    # the two probes (bug found in code review, see cerebrum.md).
    agent = (
        TripoAssetAgent(
            config=TripoConfig(
                api_key=creds.api_key, base_url=creds.base_url, is_global=creds.is_global
            )
        )
        if creds is not None
        else TripoAssetAgent()
    )
    result = await dispatch_sku(
        agent, sku=target.sku, name=row["name"], source_image=target.resolved_path
    )
    print(
        f"\nOK — {result['sku']}: task={result['task_id']} "
        f"model={result['model_path']} validation={result['validation_status']}"
    )
    return 0


def main() -> int:
    """Synchronous CLI entry point. In an async context call `run()` directly."""
    return asyncio.run(run(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
