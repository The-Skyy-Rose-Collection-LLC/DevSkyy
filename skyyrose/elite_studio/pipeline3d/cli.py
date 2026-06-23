"""CLI for the 3D pipeline orchestrator (Phase 1 driver).

Usage:
    python -m skyyrose.elite_studio.pipeline3d \
        --sku br-001 --stages image-to-3d,texture,remesh,export --format glb [--go]

Default is dry-run: resolve source + compute the ONE whole-job estimate + print
the STOP-AND-SHOW banner, but do NOT dispatch. Pass --go to dispatch paid stages
(still gated by the confirmation banner unless SKYYROSE_AUTO_CONFIRM=1 or no TTY).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from skyyrose.elite_studio.budget import RunBudget

from .adapters.local_export import LocalExportAdapter
from .adapters.tripo import TripoAdapter
from .estimator import estimate
from .executor import run_job
from .models import JobSpec, Stage
from .preflight import PreflightError, resolve_source
from .router import Router
from .store import StageStore

_STAGE_ALIASES = {
    "image-to-3d": Stage.IMAGE_TO_3D,
    "image_to_3d": Stage.IMAGE_TO_3D,
    "texture": Stage.TEXTURE,
    "remesh": Stage.REMESH,
    "export": Stage.EXPORT,
}
_DEFAULT_PRIORITY = ["tripo", "local"]


def parse_stages(value: str) -> tuple[Stage, ...]:
    """Parse a comma-separated stage list into ordered Stage values."""
    out: list[Stage] = []
    for raw in value.split(","):
        token = raw.strip().lower()
        if not token:
            continue
        if token not in _STAGE_ALIASES:
            raise SystemExit(f"unknown stage: {token!r} (valid: {', '.join(_STAGE_ALIASES)})")
        out.append(_STAGE_ALIASES[token])
    if not out:
        raise SystemExit("no stages requested")
    return tuple(out)


def build_router(*, api_key: str | None, output_dir: Path) -> Router:
    """Build the Phase 1 router: Tripo + local export."""
    adapters = [
        TripoAdapter(api_key=api_key, output_dir=output_dir / "_tripo"),
        LocalExportAdapter(),
    ]
    return Router(adapters, priority=_DEFAULT_PRIORITY)


def _confirm(*, sku: str, source: Path, est: dict) -> bool:
    """STOP-AND-SHOW gate. Always prints the banner; returns True iff confirmed.

    A paid dispatch is NEVER silent. The banner prints first, unconditionally,
    so any run that is about to spend money shows what and how much. Approval is
    then resolved fail-closed:

      * ``SKYYROSE_AUTO_CONFIRM=1``  -> explicit batch opt-in, proceeds.
      * no TTY (CI, cron, subprocess, pytest) -> ABORTS. Auto-approving a paid
        call on a missing TTY would violate the STOP-AND-SHOW money rule.
      * interactive TTY -> prompts for an explicit ``y``.
    """
    banner = (
        "\nSTOP — Confirm before proceeding:\n\n"
        f"  Action : 3D pipeline (paid)\n"
        f"  SKU    : {sku}\n"
        f"  Source : {source}\n"
        f"  Stages : {', '.join(f'{k}=${v:.2f}' for k, v in est['by_stage'].items())}\n"
        f"  Total  : ~${est['total_usd']:.2f}\n\n"
        "Proceed? [y/N] "
    )
    sys.stdout.write(banner)
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


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gen3d", description="Unified 3D pipeline (Phase 1: Tripo).")
    p.add_argument("--sku", required=True)
    p.add_argument(
        "--image", default=None, help="Explicit source image path (overrides SKU lookup)"
    )
    p.add_argument("--stages", default="image-to-3d,texture,remesh,export")
    p.add_argument("--format", default="glb", choices=["glb"])
    p.add_argument("--output-dir", default="renders/3d")
    p.add_argument("--source-root", default=None, help="Override canonical source root")
    p.add_argument("--budget", type=float, default=5.0, help="Per-job USD ceiling")
    p.add_argument("--api-key", default=None, help="Tripo API key (else env TRIPO_API_KEY)")
    p.add_argument("--go", action="store_true", help="Dispatch paid stages (default: dry-run)")
    return p


async def run(argv: list[str]) -> int:
    """Programmatic entry point. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    stages = parse_stages(args.stages)
    output_dir = Path(args.output_dir)

    if args.api_key:
        sys.stderr.write(
            "warning: --api-key is visible in process listings and shell history; "
            "prefer the TRIPO_API_KEY env var\n"
        )

    try:
        source = resolve_source(sku=args.sku, image=args.image, source_root=args.source_root)
    except PreflightError as exc:
        sys.stderr.write(f"preflight failed: {exc}\n")
        return 2

    router = build_router(api_key=args.api_key, output_dir=output_dir)
    job = JobSpec(
        sku=args.sku,
        source_image=source,
        stages=stages,
        formats=(args.format,),
        budget_ceiling_usd=args.budget,
        output_dir=output_dir,
    )
    est = estimate(job, router)

    if not args.go:
        sys.stdout.write(
            f"\nDRY RUN — no dispatch.\n  SKU: {args.sku}\n  Source: {source}\n"
            f"  Stages: {', '.join(f'{k}=${v:.2f}' for k, v in est['by_stage'].items())}\n"
            f"  Estimated total: ~${est['total_usd']:.2f}\n"
            f"  (pass --go to dispatch)\n"
        )
        return 0

    # Affordability gate: refuse the whole job up front if the ONE estimate already
    # exceeds the ceiling, so we never bill stages 1..n-1 before a later stage trips
    # the per-stage budget check inside run_job.
    if est["total_usd"] > args.budget:
        sys.stderr.write(
            f"estimated cost ${est['total_usd']:.2f} exceeds budget ceiling "
            f"${args.budget:.2f} — aborting (raise --budget or drop stages)\n"
        )
        return 1

    if not _confirm(sku=args.sku, source=source, est=est):
        sys.stdout.write("aborted by user\n")
        return 1

    budget = RunBudget(ceiling_usd=args.budget)
    store = StageStore(output_dir / "_store")
    result = await run_job(job, router=router, store=store, budget=budget)
    sys.stdout.write(
        f"\nstatus: {result.status.value}\n"
        f"final: {result.final_artifact.path if result.final_artifact else None}\n"
        f"spent: ${result.total_cost_usd:.2f}\n"
    )
    if result.error:
        sys.stderr.write(f"error: {result.error}\n")
    return 0 if result.status.value == "succeeded" else 1


def main() -> int:
    """Synchronous CLI entry point. In an async context call ``run()`` directly."""
    return asyncio.run(run(sys.argv[1:]))


__all__ = ["run", "main", "parse_stages", "build_router"]
