"""3D fidelity scoring CLI — two-phase (free analytic → paid branding).
======================================================================

Ties together the fidelity scorer (``imagery/model_review_scorer.py``) and the
QA-review registry (``agents.models.Model3DReview``). Two explicitly-separated
passes, matching the plan's D4 two-phase-write decision:

  1. **Analytic pass** (``--sku SKU`` or ``--all-pending``) — free, no gate.
     Scores geometry/materials/colors/proportions + the texture-detail floor
     (all $0), creates a ``Model3DReview`` row with an overall partial score
     and ``fidelity_breakdown = NULL``. ``QAReviewSchema``'s breakdown object
     requires all 6 keys, so a partial dict would fail frontend validation —
     it stays NULL until branding is scored (phase 2).

  2. **Branding pass** (``--sku SKU --with-branding``) — the one paid VLM call,
     behind a STOP-AND-SHOW confirmation gate (mirrors
     ``scripts/generate_3d_from_catalog.py::_confirm``). Re-runs the free
     analytic dims, adds the branding score, and only then writes the full
     6-key ``fidelity_breakdown`` + a full overall score.

Design notes:
  * ``score_analytic`` calls ``asyncio.run()`` internally, so it must NOT be
    invoked from inside a running event loop — every scorer call goes through
    ``asyncio.to_thread`` (the worker thread has no running loop).
  * Read → score → write are three separate ``db_manager.session()`` blocks,
    so neither the human confirmation prompt nor the (up to 180s) VLM call
    holds a DB transaction open.
  * The free pass reads the GLB + reference packshot from LOCAL disk and
    fails closed if either is missing (no silent fallback, bug-230). Only the
    paid pass reaches the network — it downloads Tripo's rendered preview from
    R2 (the local ``_rendered.webp`` is gone by then), keeping the free pass
    network-free per the plan.

Usage:
    python scripts/score_3d_fidelity.py --sku br-001
    python scripts/score_3d_fidelity.py --all-pending
    python scripts/score_3d_fidelity.py --sku br-001 --with-branding
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from services.storage.r2_client import R2Client, R2Error
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.models import Model3DGeneration, Model3DReview
from database import db_manager
from imagery.model_review_scorer import (
    AnalyticScoreResult,
    BrandingScoreResult,
    score_analytic,
    score_branding_vlm,
)

# Estimated cost of one branding VLM judge call. Mirrors
# imagery/model_review_scorer._EST_BRANDING_JUDGE_COST_USD; each script keeps
# its own cost constant (same convention as
# scripts/generate_3d_from_catalog.py's TRIPO_IMAGE_TO_MODEL_CREDITS_ESTIMATE)
# so the STOP-AND-SHOW manifest never imports a private symbol.
_EST_BRANDING_COST_USD = 0.05


class ScoringSkip(Exception):
    """A single target can't be scored (missing file, already scored, aborted).

    Reported and skipped rather than fatal — one bad SKU never aborts a
    ``--all-pending`` batch.
    """


@dataclass(frozen=True)
class _GenerationSnapshot:
    """Plain, session-detached copy of the fields scoring needs.

    Built while a session is open so scoring (and the human confirmation
    prompt / slow VLM call) can run with no DB transaction held.
    """

    id: uuid.UUID
    sku: str
    model_path: str | None
    source_image_path: str | None
    rendered_preview_r2_key: str | None
    has_review: bool


# =============================================================================
# Score assembly
# =============================================================================


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _partial_score(analytic: AnalyticScoreResult) -> float:
    """Phase-1 headline score: mean of the 5 free dims (branding not yet scored)."""
    return _mean(
        [
            analytic.geometry,
            analytic.materials,
            analytic.colors,
            analytic.proportions,
            analytic.texture_detail_floor,
        ]
    )


def _full_breakdown(analytic: AnalyticScoreResult, branding: BrandingScoreResult) -> dict:
    """The 6-key breakdown the frontend's QAReviewSchema requires.

    ``texture_detail`` uses the free analytic floor — the optional VLM
    refinement (D2) ships disabled by default.
    """
    return {
        "geometry": analytic.geometry,
        "materials": analytic.materials,
        "colors": analytic.colors,
        "proportions": analytic.proportions,
        "branding": branding.branding,
        "texture_detail": analytic.texture_detail_floor,
    }


def _full_score(breakdown: dict) -> float:
    return _mean(list(breakdown.values()))


# =============================================================================
# Local-file + R2 resolution
# =============================================================================


def _require_local(path_str: str | None, sku: str, label: str) -> Path:
    """Resolve a recorded path to an on-disk file, or fail closed (bug-230)."""
    if not path_str:
        raise ScoringSkip(f"{sku}: generation has no {label} path recorded")
    path = Path(path_str)
    if not path.exists():
        raise ScoringSkip(
            f"{sku}: {label} not on disk at {path} — analytic scoring reads local files "
            "(run on the box that generated the model)"
        )
    return path


def _download_preview(r2_key: str, destination: Path) -> None:
    """Download Tripo's rendered preview from R2 to a local temp path."""
    try:
        R2Client().download_file(r2_key, destination)
    except R2Error as exc:
        raise ScoringSkip(f"R2 download of rendered preview failed ({r2_key}): {exc}") from exc


# =============================================================================
# STOP-AND-SHOW gate (paid branding pass only)
# =============================================================================


def _print_branding_manifest(snap: _GenerationSnapshot, model_path: Path, reference: Path) -> None:
    lines = [
        "",
        "=" * 70,
        "STOP — Confirm before proceeding:",
        "=" * 70,
        "  Action    : Branding VLM judge (paid Anthropic vision call)",
        f"  SKU       : {snap.sku}",
        f"  Model     : {model_path}",
        f"  Reference : {reference}",
        f"  Preview   : R2:{snap.rendered_preview_r2_key}",
        f"  Cost      : ~${_EST_BRANDING_COST_USD:.2f}  (1 VLM judge call)",
        "=" * 70,
    ]
    print("\n".join(lines))


def _confirm() -> bool:
    """STOP-AND-SHOW gate. Fail-closed, mirrors
    ``scripts/generate_3d_from_catalog.py::_confirm``.

      * ``SKYYROSE_AUTO_CONFIRM=1``     -> explicit opt-in, proceeds.
      * no TTY (CI, cron, pytest)       -> ABORTS (never auto-approves a paid call).
      * interactive TTY                 -> prompts for an explicit ``y``/``yes``.
    """
    sys.stdout.write("\nProceed? [y/N] ")
    sys.stdout.flush()
    if os.getenv("SKYYROSE_AUTO_CONFIRM") == "1":
        sys.stdout.write("\nauto-confirmed via SKYYROSE_AUTO_CONFIRM=1\n")
        return True
    if not sys.stdin.isatty():
        sys.stdout.write(
            "\nnon-interactive context — aborting paid branding call "
            "(set SKYYROSE_AUTO_CONFIRM=1 to allow)\n"
        )
        return False
    try:
        return input().strip().lower() in {"y", "yes"}
    except EOFError:
        return False


# =============================================================================
# Scoring passes (no DB session held — score_* run off the event loop)
# =============================================================================


async def _score_analytic_only(snap: _GenerationSnapshot) -> tuple[float, dict | None]:
    """Free pass: 4 analytic dims + texture floor, no gate, no network."""
    if snap.has_review:
        raise ScoringSkip(
            f"{snap.sku}: a review already exists — skipping "
            "(use --with-branding to add the branding score)"
        )
    model_path = _require_local(snap.model_path, snap.sku, "GLB")
    reference = _require_local(snap.source_image_path, snap.sku, "reference packshot")
    analytic = await asyncio.to_thread(score_analytic, model_path, snap.sku, reference)
    return _partial_score(analytic), None


async def _score_full(snap: _GenerationSnapshot) -> tuple[float, dict]:
    """Paid pass: analytic dims + branding VLM (STOP-AND-SHOW gated)."""
    model_path = _require_local(snap.model_path, snap.sku, "GLB")
    reference = _require_local(snap.source_image_path, snap.sku, "reference packshot")
    if not snap.rendered_preview_r2_key:
        raise ScoringSkip(
            f"{snap.sku}: no rendered_preview_r2_key on the generation — "
            "branding scoring needs Tripo's rendered preview image"
        )

    _print_branding_manifest(snap, model_path, reference)
    if not _confirm():
        raise ScoringSkip(f"{snap.sku}: branding scoring aborted at confirmation gate")

    with tempfile.TemporaryDirectory() as tmp:
        preview = Path(tmp) / f"{snap.sku}_rendered_preview"
        _download_preview(snap.rendered_preview_r2_key, preview)
        # Both free; only score_branding_vlm below is the paid call.
        analytic = await asyncio.to_thread(score_analytic, model_path, snap.sku, reference)
        branding = await asyncio.to_thread(score_branding_vlm, preview, reference, snap.sku)

    breakdown = _full_breakdown(analytic, branding)
    return _full_score(breakdown), breakdown


# =============================================================================
# DB read / write
# =============================================================================


def _snapshot(generation: Model3DGeneration, *, has_review: bool) -> _GenerationSnapshot:
    return _GenerationSnapshot(
        id=generation.id,
        sku=generation.sku,
        model_path=generation.model_path,
        source_image_path=generation.source_image_path,
        rendered_preview_r2_key=generation.rendered_preview_r2_key,
        has_review=has_review,
    )


async def _latest_generation_for_sku(session: AsyncSession, sku: str) -> Model3DGeneration | None:
    stmt = (
        select(Model3DGeneration)
        .where(Model3DGeneration.sku == sku)
        .order_by(Model3DGeneration.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def _generations_without_review(session: AsyncSession) -> list[Model3DGeneration]:
    stmt = (
        select(Model3DGeneration)
        .where(~exists().where(Model3DReview.generation_id == Model3DGeneration.id))
        .order_by(Model3DGeneration.created_at.asc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def _existing_review(session: AsyncSession, generation_id: uuid.UUID) -> Model3DReview | None:
    stmt = (
        select(Model3DReview)
        .where(Model3DReview.generation_id == generation_id)
        .order_by(Model3DReview.created_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalars().first()


async def _load_snapshots(sku: str | None, *, all_pending: bool) -> list[_GenerationSnapshot]:
    async with db_manager.session() as session:
        if all_pending:
            gens = await _generations_without_review(session)
            return [_snapshot(g, has_review=False) for g in gens]

        assert sku is not None  # guarded by run()'s arg validation
        generation = await _latest_generation_for_sku(session, sku)
        if generation is None:
            return []
        existing = await _existing_review(session, generation.id)
        return [_snapshot(generation, has_review=existing is not None)]


async def _upsert_review(
    session: AsyncSession, snap: _GenerationSnapshot, score: float, breakdown: dict | None
) -> None:
    review = await _existing_review(session, snap.id)
    if review is None:
        review = Model3DReview(id=uuid.uuid4(), generation_id=snap.id, status="pending")
        session.add(review)
    review.fidelity_score = score
    if breakdown is not None:
        review.fidelity_breakdown = breakdown


# =============================================================================
# CLI
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="score_3d_fidelity",
        description="Two-phase 3D fidelity scorer (free analytic -> paid branding).",
    )
    p.add_argument("--sku", default=None, help="Single SKU to score (its most recent generation).")
    p.add_argument(
        "--all-pending",
        action="store_true",
        dest="all_pending",
        help="Analytic-score every generation that has no review yet (free, no gate).",
    )
    p.add_argument(
        "--with-branding",
        action="store_true",
        dest="with_branding",
        help="Add the paid branding VLM score (STOP-AND-SHOW gated). Requires --sku.",
    )
    return p


def _validate_args(args: argparse.Namespace) -> str | None:
    """Return an error message for an invalid flag combination, else None."""
    if args.with_branding and args.all_pending:
        return (
            "--with-branding cannot be combined with --all-pending (paid call, one SKU at a time)"
        )
    if args.with_branding and not args.sku:
        return "--with-branding requires --sku"
    if not args.all_pending and not args.sku:
        return "pass --sku SKU or --all-pending"
    return None


async def run(argv: list[str]) -> int:
    """Programmatic entry point. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    err = _validate_args(args)
    if err is not None:
        sys.stderr.write(f"error: {err}\n")
        return 2

    await db_manager.initialize()

    snapshots = await _load_snapshots(args.sku, all_pending=args.all_pending)
    if not snapshots:
        if args.all_pending:
            print("no generations pending analytic scoring")
            return 0
        sys.stderr.write(f"error: no Model3DGeneration found for sku {args.sku!r}\n")
        return 1

    scored: list[tuple[_GenerationSnapshot, float, dict | None]] = []
    for snap in snapshots:
        try:
            if args.with_branding:
                score, breakdown = await _score_full(snap)
            else:
                score, breakdown = await _score_analytic_only(snap)
        except ScoringSkip as skip:
            print(f"SKIP {skip}")
            continue
        scored.append((snap, score, breakdown))

    if not scored:
        return 1

    async with db_manager.session() as session:
        for snap, score, breakdown in scored:
            await _upsert_review(session, snap, score, breakdown)
        await session.commit()

    for snap, score, breakdown in scored:
        kind = "6-dim" if breakdown is not None else "analytic"
        print(f"OK — {snap.sku}: {kind} scored, fidelity={score:.1f}")
    return 0


def main() -> int:
    """Synchronous CLI entry point. In an async context call ``run()`` directly."""
    return asyncio.run(run(sys.argv[1:]))


if __name__ == "__main__":
    raise SystemExit(main())
