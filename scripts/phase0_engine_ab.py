"""Phase 0.3 — cross-engine fidelity A/B for threshold calibration.

Dispatches br-001 + lh-004 to {TRELLIS, Tripo, Meshy} via the ThreeDRoundTable,
scores each mesh through the fidelity gate in report-only mode against the
golden references, and recommends the per-tenant visible-face threshold from
real garments.

STOP-AND-SHOW: the default run is a DRY RUN — it prints the cost manifest and
spends nothing. Real dispatch requires `--execute` AND a per-run RunBudget;
every paid hop is budget-gated before dispatch. Per-SKU rates
(tasks/phase-e-manifest.md): Meshy $0.20, Tripo $0.25, TRELLIS $0.00 local /
hosted GPU-time billed separately. The dispatch + scoring adapters are
gated-integration (need engine keys/host); the orchestration is unit-tested
with injected fakes.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Bootstrap: allow `python3 scripts/phase0_engine_ab.py` (not only `-m`) by
# putting the repo root on sys.path before importing the skyyrose package.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skyyrose.elite_studio.budget import (  # noqa: E402
    DEFAULT_BUDGET_USD,
    BudgetExceededError,
    RunBudget,
)

# Verified per-SKU costs (USD). TRELLIS local = 0; hosted GPU-time billed apart.
ENGINE_COST_USD: dict[str, float] = {"trellis": 0.0, "tripo": 0.25, "meshy": 0.20}
DEFAULT_SKUS: tuple[str, ...] = ("br-001", "lh-004")
DEFAULT_ENGINES: tuple[str, ...] = ("trellis", "tripo", "meshy")

# (sku, engine, source_image) -> mesh_path. PAID. Injectable for testing.
DispatchFn = Callable[[str, str, str], str]
# (sku, mesh_path) -> visible composite score (report-only gate). Injectable.
ScoreFn = Callable[[str, str], float]
# sku -> source image path. Injectable.
SourceFn = Callable[[str], str]


@dataclass(frozen=True)
class ABRow:
    sku: str
    engine: str
    visible_score: float


@dataclass(frozen=True)
class ManifestLine:
    sku: str
    engine: str
    cost_usd: float
    source_image: str


def recommend_threshold(rows: list[ABRow], *, engine: str, margin: float = 0.03) -> float | None:
    """Lowest passing score for `engine` minus a safety margin, or None."""
    scores = [r.visible_score for r in rows if r.engine == engine]
    if not scores:
        return None
    return round(min(scores) - margin, 4)


def build_manifest(
    skus: tuple[str, ...], engines: tuple[str, ...], source_for: SourceFn
) -> list[ManifestLine]:
    """Assemble the (sku, engine) dispatch plan with per-line costs."""
    out: list[ManifestLine] = []
    for sku in skus:
        src = source_for(sku)
        for engine in engines:
            out.append(
                ManifestLine(
                    sku=sku,
                    engine=engine,
                    cost_usd=ENGINE_COST_USD.get(engine, 0.0),
                    source_image=src,
                )
            )
    return out


def manifest_total(manifest: list[ManifestLine]) -> float:
    return round(sum(m.cost_usd for m in manifest), 4)


def render_manifest(manifest: list[ManifestLine]) -> str:
    lines = [
        "STOP — Confirm before proceeding (paid Phase 0 A/B):",
        "",
        f"{'SKU':<10} {'ENGINE':<8} {'COST':>7}  SOURCE",
    ]
    for m in manifest:
        lines.append(f"{m.sku:<10} {m.engine:<8} ${m.cost_usd:>6.2f}  {m.source_image}")
    lines += [
        "",
        f"Total (excl. TRELLIS hosted GPU-time): ${manifest_total(manifest):.2f}",
        "Re-run with --execute to dispatch. Nothing has been spent.",
    ]
    return "\n".join(lines)


def run_ab(
    *,
    skus: tuple[str, ...],
    engines: tuple[str, ...],
    source_for: SourceFn,
    dispatch_fn: DispatchFn,
    score_fn: ScoreFn,
    budget: RunBudget,
) -> list[ABRow]:
    """Execute the paid A/B. Each (sku, engine) is budget-gated BEFORE dispatch.

    Raises BudgetExceededError (from RunBudget.ensure_within_budget) if the next
    hop would breach the ceiling — the caller halts with partial rows intact.
    """
    rows: list[ABRow] = []
    for sku in skus:
        src = source_for(sku)
        for engine in engines:
            cost = ENGINE_COST_USD.get(engine, 0.0)
            budget.ensure_within_budget(cost, stage=f"phase0:{engine}")
            mesh_path = dispatch_fn(sku, engine, src)
            budget.spend(cost, stage=f"phase0:{engine}")
            rows.append(ABRow(sku=sku, engine=engine, visible_score=score_fn(sku, mesh_path)))
    return rows


# ---------------------------------------------------------------------------
# Default gated-integration adapters (need engine keys/host; not unit-tested).
# ---------------------------------------------------------------------------


def _default_source_for(sku: str) -> str:
    """Resolve the SKU's golden front image as the dispatch source."""
    from skyyrose.elite_studio.platform.catalog_source import SkyyRoseCatalogSource

    refs = SkyyRoseCatalogSource().references(sku)
    front = refs.get("front")
    if front is None:
        raise RuntimeError(f"no front golden reference for {sku} — cannot dispatch")
    return str(front)


def _roundtable_dispatch(sku: str, engine: str, source_image: str) -> str:
    """GATED-INTEGRATION: dispatch ONE engine via ThreeDRoundTable, return mesh path.

    Raw fidelity (enhance_quality=False) so the A/B measures the engine, not the
    enhancer. Requires the engine's keys/host; raises on failure.
    """
    import asyncio

    from orchestration.threed_round_table import ThreeDProvider, ThreeDRoundTable

    provider = {
        "trellis": ThreeDProvider.TRELLIS_2,
        "tripo": ThreeDProvider.TRIPO3D,
        "meshy": ThreeDProvider.MESHY,
    }[engine]
    rt = ThreeDRoundTable(
        enable_tripo3d=(engine == "tripo"),
        enable_meshy=(engine == "meshy"),
        enable_trellis=(engine == "trellis"),
        enable_anigen=False,
    )

    async def _go() -> str:
        result = await rt.compete_image_to_3d(
            image_path=source_image, providers=[provider], enhance_quality=False
        )
        for entry in result.entries:
            if entry.provider == provider and entry.response.success and entry.response.output_path:
                return entry.response.output_path
        raise RuntimeError(f"{engine}: no successful mesh for {sku}")

    return asyncio.run(_go())


def _default_score(sku: str, mesh_path: str) -> float:
    """Mean visible-face composite from the report-only fidelity gate."""
    from skyyrose.elite_studio.platform.fidelity import gate
    from skyyrose.elite_studio.platform.tenancy import TenantRegistry

    tenant = TenantRegistry.default().get("skyyrose")
    report = gate.evaluate(tenant, sku, mesh_path)  # threshold 0.0 = report-only
    scores = report.composite_by_angle
    if not scores:
        return 0.0
    return round(sum(scores.values()) / len(scores), 6)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="phase0_engine_ab", description="Phase 0 cross-engine fidelity A/B"
    )
    parser.add_argument("--skus", nargs="+", default=list(DEFAULT_SKUS))
    parser.add_argument("--engines", nargs="+", default=list(DEFAULT_ENGINES))
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually dispatch (PAID + GPU). Default is a dry-run manifest only.",
    )
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET_USD)
    parser.add_argument(
        "--env-file",
        default=None,
        help="Load env vars from this file via python-dotenv before dispatch "
        "(robust parsing; keeps secrets out of the shell and logs).",
    )
    args = parser.parse_args(argv)
    skus = tuple(args.skus)
    engines = tuple(args.engines)

    if args.env_file:
        try:
            from dotenv import load_dotenv
        except ImportError:
            print("python-dotenv not installed; cannot load --env-file", file=sys.stderr)
            return 3
        load_dotenv(args.env_file, override=True)

    manifest = build_manifest(skus, engines, _default_source_for)
    print(render_manifest(manifest))
    if not args.execute:
        return 0  # STOP-AND-SHOW: dry run, nothing spent

    budget = RunBudget(ceiling_usd=args.budget)
    try:
        rows = run_ab(
            skus=skus,
            engines=engines,
            source_for=_default_source_for,
            dispatch_fn=_roundtable_dispatch,
            score_fn=_default_score,
            budget=budget,
        )
    except BudgetExceededError as exc:
        print(f"\nHALTED on budget: {exc}")
        return 2

    print("\n=== A/B fidelity scores ===")
    for r in rows:
        print(f"{r.sku:<10} {r.engine:<8} {r.visible_score:.4f}")
    for engine in engines:
        rec = recommend_threshold(rows, engine=engine)
        if rec is not None:
            print(f"recommended threshold ({engine}): {rec}")
    print(f"\nbudget: {budget.snapshot()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
