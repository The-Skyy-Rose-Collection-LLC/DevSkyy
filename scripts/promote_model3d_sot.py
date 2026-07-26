#!/usr/bin/env python3
"""Promote APPROVED Model3DReview rows into their SKU's sot.json entry.

The 3D-model analogue of the asset hub -> sot.json seam that
``wordpress-theme/skyyrose-flagship/data/build-collection-sot.py`` already
applies to 2D imagery: an approved verdict is baked into the per-collection
``sot.json`` upstream so every consumer (``skyyrose.core.sot_images``, the PHP
theme reader, the dashboard manifest) honors it uniformly, with no parallel
override anywhere else. This script writes the ``model_3d`` key; the reader
is ``skyyrose.core.sot_images.resolve_model_3d``.

Sibling script, not a change to build-collection-sot.py -- deliberately:
build-collection-sot.py's ``build_documents()`` is pure and DB-free (only
tracked masters + filesystem reads), which is exactly what lets its freshness
guard byte-compare a regeneration against the committed sot.json in a clean
CI checkout. This step instead needs a live ``AsyncSession`` against
``agents.models.Model3DGeneration`` / ``Model3DReview`` (populated today only
via real Postgres + alembic migration 004, never by
``database.db_manager``'s own dev-fallback ``create_all``) -- folding that in
would force an async event loop and a live DB dependency into a script whose
own test suite currently drives it with a bare ``subprocess.run`` and zero DB
fixture. Keeping promotion a separate overlay pass also matches its narrower
job: it only ADDS ``model_3d`` to an ALREADY-BUILT sot.json (run
build-collection-sot.py first); it never touches anything else in the
document.

KNOWN FOLLOW-UP: writing ``model_3d`` into sot.json makes
build-collection-sot.py's freshness-guard byte-compare (a masters-only
regeneration will never reproduce a DB-sourced key) fail the first time this
script runs for real. The guard needs to learn to preserve/tolerate
``model_3d`` before this promotes anything against a live database -- out of
scope here since no ``Model3DReview`` row is approved yet (nothing to
promote against real data).

USAGE: python3 scripts/promote_model3d_sot.py [--sot-dir DIR]
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.models import Model3DGeneration, Model3DReview
from database import db_manager
from skyyrose.core.paths import REPO_ROOT

SOT_DIR: Path = REPO_ROOT / "wordpress-theme" / "skyyrose-flagship" / "data" / "collections"


@dataclass(frozen=True)
class ApprovedModel3D:
    """One promoted (approved review, its generation) pair -- DB-row-shaped,
    but DB-free so :func:`promote_model3d` is testable without a session."""

    sku: str
    model_path: str
    format: str
    task_id: str
    approved_at: str


def _to_repo_relative_path(model_path: str) -> str:
    """Normalize a ``Model3DGeneration.model_path`` to a REPO_ROOT-relative string.

    ``dispatch_sku`` in ``scripts/generate_3d_from_catalog.py`` always writes
    an ABSOLUTE path under ``REPO_ROOT / "assets" / "3d-models-generated"``
    (its ``OUTPUT_ROOT`` derives from ``REPO_ROOT``). ``sot.json``'s
    ``model_3d.path`` must never be absolute -- matching
    ``resolve_image``'s never-absolute contract, just rooted at
    ``REPO_ROOT`` instead of ``THEME_ROOT`` since generated 3D models live
    outside the WordPress theme tree -- so this strips the ``REPO_ROOT``
    prefix. Raises rather than writing an unrooted path into the tracked
    sot.json (fail closed, not a silent fallback): today every real
    ``model_path`` is under ``REPO_ROOT`` by construction, so hitting this
    branch means the DB row is corrupt, not that a rooted path is unusual.
    """
    path = Path(model_path)
    if not path.is_absolute():
        return model_path
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError as exc:
        raise ValueError(
            f"model3d path is not under REPO_ROOT, refusing to promote: {model_path!r}"
        ) from exc


async def fetch_approved_model3d(session: AsyncSession) -> list[ApprovedModel3D]:
    """Query every APPROVED ``Model3DReview`` joined to its ``Model3DGeneration``.

    Ordered oldest-approved-first so :func:`promote_model3d`'s per-SKU
    last-write-wins dedup keeps the MOST RECENT approval when a SKU has more
    than one. ``approved_at`` maps to the review's ``updated_at`` column --
    there is no dedicated ``approved_at`` column on ``Model3DReview``, and
    that column has no ``onupdate=``, so a future approval workflow must set
    it explicitly when flipping ``status`` to ``"approved"``.
    """
    stmt = (
        select(Model3DReview, Model3DGeneration)
        .join(Model3DGeneration, Model3DReview.generation_id == Model3DGeneration.id)
        .where(Model3DReview.status == "approved")
        .order_by(Model3DReview.updated_at.asc())
    )
    result = await session.execute(stmt)
    return [
        ApprovedModel3D(
            sku=generation.sku,
            model_path=_to_repo_relative_path(generation.model_path),
            format=generation.format or "",
            task_id=generation.task_id or "",
            approved_at=review.updated_at.isoformat() if review.updated_at else "",
        )
        for review, generation in result.all()
    ]


def _sku_index(sot_by_slug: dict[str, dict]) -> dict[str, tuple[str, int]]:
    """``sku -> (slug, product-index)`` across every collection's sot.json."""
    index: dict[str, tuple[str, int]] = {}
    for slug, sot in sot_by_slug.items():
        for i, prod in enumerate(sot.get("products", [])):
            sku = prod.get("sku")
            if sku:
                index[sku] = (slug, i)
    return index


def promote_model3d(
    sot_by_slug: dict[str, dict], approved: Sequence[ApprovedModel3D]
) -> dict[str, dict]:
    """Bake each approved 3D model into its SKU's product entry as ``model_3d``.

    Pure -- no disk I/O, no DB. Returns NEW sot documents (immutable
    copy-on-write, per project convention); ``sot_by_slug`` is never mutated.
    A SKU in ``approved`` that matches no product in any collection is
    skipped (never invents a product entry). When a SKU appears more than
    once in ``approved``, the LAST entry wins (pair with
    :func:`fetch_approved_model3d`'s oldest-first ordering for "most recent
    approval wins").
    """
    index = _sku_index(sot_by_slug)
    updated = {
        slug: {**sot, "products": [dict(p) for p in sot.get("products", [])]}
        for slug, sot in sot_by_slug.items()
    }
    for row in approved:
        loc = index.get(row.sku)
        if loc is None:
            continue
        slug, i = loc
        updated[slug]["products"][i] = {
            **updated[slug]["products"][i],
            "model_3d": {
                "path": row.model_path,
                "format": row.format,
                "task_id": row.task_id,
                "approved_at": row.approved_at,
            },
        }
    return updated


def _serialize(obj: object) -> str:
    """Byte format for sot.json -- must stay identical to
    ``build-collection-sot.py``'s ``serialize()`` (2-space indent,
    ASCII-escaped, trailing newline). Duplicated locally rather than
    imported: that module's filename is hyphenated, so it cannot be
    ``import``ed as a normal Python module.
    """
    return json.dumps(obj, indent=2, ensure_ascii=True) + "\n"


def _load_sot_documents(sot_dir: Path) -> dict[str, dict]:
    """``{slug: sot_dict}`` for every ``<sot_dir>/<slug>/sot.json`` on disk."""
    return {p.parent.name: json.loads(p.read_text()) for p in sorted(sot_dir.glob("*/sot.json"))}


async def run(sot_dir: Path | None = None) -> int:
    """Load sot.json from ``sot_dir``, promote every approved row, write back."""
    out = sot_dir or SOT_DIR
    sot_by_slug = _load_sot_documents(out)

    await db_manager.initialize()
    async with db_manager.session() as session:
        approved = await fetch_approved_model3d(session)

    updated = promote_model3d(sot_by_slug, approved)
    index = _sku_index(sot_by_slug)
    promoted = [row.sku for row in approved if row.sku in index]
    unmatched = [row.sku for row in approved if row.sku not in index]

    for slug, sot in updated.items():
        (out / slug / "sot.json").write_text(_serialize(sot))

    print(f"promoted {len(promoted)} SKU(s): {', '.join(promoted) or '(none)'}")
    if unmatched:
        print(f"WARNING: {len(unmatched)} approved SKU(s) matched no collection: {unmatched}")
    return 0


def main() -> int:
    """Synchronous CLI entry point. In an async context call `run()` directly."""
    parser = argparse.ArgumentParser(
        description="Promote APPROVED Model3DReview rows into their SKU's sot.json."
    )
    parser.add_argument(
        "--sot-dir",
        default=None,
        help="Directory containing per-slug sot.json folders. Defaults to "
        "data/collections/ (the tracked SOT view).",
    )
    args = parser.parse_args()
    sot_dir = Path(args.sot_dir) if args.sot_dir else None
    return asyncio.run(run(sot_dir))


if __name__ == "__main__":
    raise SystemExit(main())
