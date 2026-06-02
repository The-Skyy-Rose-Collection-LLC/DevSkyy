#!/usr/bin/env python3
"""stage-review {sku} | --all — bridge a finished render into the approval queue.

The keystone hand-off in the ghost-mannequin pipeline. The render engine
(scripts/seedream_ghost_mannequin.py) writes to

    assets/product-source/{sku}__{slug}/renders/seedream-probe*.png

but the approval CLI (scripts/approve_ghost.py -> skyyrose.core.review.approve)
reads from

    renders/ghost-mannequin/{sku}-ghost-front.webp

Nothing previously bridged the two, so approval errored with "no review file ...
place file before approving" and the whole render -> approve -> WooCommerce chain
could not start. This script is that bridge: it selects the chosen render,
converts PNG -> WEBP, and writes it to the path review.approve() expects.

It does NOT touch approved/ or the catalog CSV — that is approve_ghost.py's job
(it moves the staged file into approved/ and rewrites front_model_image).

Path constants, the SKU allowlist (a path-traversal defense — the SKU is
interpolated into a filesystem path), and root detection are imported from
skyyrose.core.review so there is a single source of truth shared with the
consumer of these files.

Exit codes:
    0 — all requested SKUs staged / skipped / not-yet-rendered cleanly (or dry-run)
    1 — at least one SKU hit a genuine error (ambiguous folder, bad --render, IO)
    2 — argparse usage error

A SKU that simply has no render yet is reported as "no-render" and does NOT fail
the batch — render it first, then re-run.
"""

from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyyrose.core.review import (  # noqa: E402
    APPROVED_SUBDIR,
    GHOST_FILENAME_FMT,
    GHOST_REL,
    ReviewError,
    _resolve_root,
    _validate_sku,
)

# assets/product-source/{sku}__{slug}/renders/seedream-probe*.png
PRODUCT_SOURCE_REL = "assets/product-source"
RENDERS_SUBDIR = "renders"
RENDER_GLOB = "seedream-probe*.png"
SKIPPED_JSON = "SKIPPED.json"
WEBP_QUALITY = 92
# Match the version suffix in seedream-probe-v4-clean.png; bare seedream-probe.png == v1.
_VERSION_RE = re.compile(r"-v(\d+)")

_log = logging.getLogger("stage_review")


@dataclass(frozen=True)
class StageResult:
    """Outcome for one SKU. ``ok`` is False only for genuine failures."""

    sku: str
    status: str  # staged | would-stage | exists | already-approved | skipped | error
    src: Path | None
    dst: Path | None
    detail: str

    @property
    def ok(self) -> bool:
        return self.status != "error"


# --------------------------------------------------------------------------- paths


def _approved_path(root: Path, sku: str) -> Path:
    return root / GHOST_REL / APPROVED_SUBDIR / GHOST_FILENAME_FMT.format(sku=sku)


def _review_path(root: Path, sku: str) -> Path:
    return root / GHOST_REL / GHOST_FILENAME_FMT.format(sku=sku)


def resolve_source_folder(root: Path, sku: str) -> Path:
    """Resolve assets/product-source/{sku}__<slug>/ for a SKU (exactly one match)."""
    base = root / PRODUCT_SOURCE_REL
    matches = sorted(p for p in base.glob(f"{sku}__*") if p.is_dir())
    if not matches:
        raise ReviewError(
            f"no product-source folder for {sku}: expected {base}/{sku}__<slug>/ "
            f"— render the SKU first or check the slug"
        )
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise ReviewError(f"ambiguous source folder for {sku}: {len(matches)} matches ({names})")
    return matches[0]


def _render_version(path: Path) -> int:
    match = _VERSION_RE.search(path.name)
    return int(match.group(1)) if match else 1


def select_render(render_dir: Path, *, override: str | None = None) -> Path:
    """Pick the render to stage.

    Precedence: explicit ``override`` filename > highest -vN variant > sole file.
    The version heuristic means a re-rendered ``-v4-clean.png`` supersedes the
    base ``seedream-probe.png`` (== v1) automatically; pass ``override`` to force
    a specific file when the heuristic is wrong.
    """
    if not render_dir.is_dir():
        raise ReviewError(f"no renders/ dir: expected {render_dir}")
    if override:
        chosen = render_dir / override
        if not chosen.is_file():
            raise ReviewError(f"override render not found: {chosen}")
        return chosen
    candidates = sorted(p for p in render_dir.glob(RENDER_GLOB) if p.is_file())
    if not candidates:
        raise ReviewError(f"no render in {render_dir} matching {RENDER_GLOB!r}")
    if len(candidates) == 1:
        return candidates[0]
    best = max(candidates, key=_render_version)
    others = ", ".join(p.name for p in candidates if p != best)
    _log.warning(
        "%s: %d render variants; auto-selected highest version %s (others: %s) "
        "— pass --render to override",
        render_dir.parent.name,
        len(candidates),
        best.name,
        others,
    )
    return best


def load_skipped(root: Path) -> set[str]:
    """SKUs in renders/ghost-mannequin/SKIPPED.json — out-of-scope accessories."""
    import json

    path = root / GHOST_REL / SKIPPED_JSON
    if not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {entry["sku"] for entry in data.get("skipped", []) if "sku" in entry}
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        _log.warning("could not parse %s (%s) — treating skip list as empty", path, exc)
        return set()


def discover_skus(root: Path) -> list[str]:
    """All SKUs that have a product-source folder, derived from folder names."""
    base = root / PRODUCT_SOURCE_REL
    if not base.is_dir():
        return []
    skus: set[str] = set()
    for folder in base.glob("*__*"):
        if not folder.is_dir():
            continue
        sku = folder.name.split("__", 1)[0]
        try:
            _validate_sku(sku)
        except ReviewError:
            continue
        skus.add(sku)
    return sorted(skus)


# ----------------------------------------------------------------------- convert


def _convert_to_webp(src_png: Path, dst_webp: Path, *, quality: int = WEBP_QUALITY) -> None:
    """Convert PNG -> WEBP atomically (tmp in target dir + os.replace)."""
    from PIL import Image

    dst_webp.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=dst_webp.parent, prefix=".tmp_stage_", suffix=".webp")
    os.close(fd)
    try:
        with Image.open(src_png) as im:
            im.save(tmp, "WEBP", quality=quality, method=6)
        os.replace(tmp, dst_webp)
    except BaseException:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
        raise


# -------------------------------------------------------------------------- core


def stage_one(
    sku: str,
    *,
    root: Path | str | None = None,
    render: str | None = None,
    force: bool = False,
    dry_run: bool = False,
    skipped: set[str] | None = None,
) -> StageResult:
    """Stage one SKU's render into the review queue. Never raises for expected
    states (skipped, already-approved, exists) — those are returned as results.
    Raises ReviewError only for an invalid SKU before any work begins.
    """
    _validate_sku(sku)
    base = _resolve_root(root)
    if skipped is None:
        skipped = load_skipped(base)

    if sku in skipped:
        return StageResult(sku, "skipped", None, None, "in SKIPPED.json (out-of-scope accessory)")

    approved = _approved_path(base, sku)
    if approved.is_file():
        return StageResult(
            sku, "already-approved", None, approved, "already approved; nothing to stage"
        )

    dst = _review_path(base, sku)
    try:
        folder = resolve_source_folder(base, sku)
    except ReviewError as exc:
        return StageResult(sku, "error", None, dst, str(exc))

    # "not rendered yet" is a precondition, not a failure: it must not fail a
    # --all batch where other SKUs are ready. Genuine problems (ambiguous folder,
    # missing override file) still surface as errors below.
    render_dir = folder / RENDERS_SUBDIR
    has_render = render_dir.is_dir() and any(render_dir.glob(RENDER_GLOB))
    if render is None and not has_render:
        return StageResult(
            sku, "no-render", None, dst, "no render yet — run the render pipeline first"
        )
    try:
        src = select_render(render_dir, override=render)
    except ReviewError as exc:
        return StageResult(sku, "error", None, dst, str(exc))

    if dst.is_file() and not force:
        return StageResult(
            sku, "exists", src, dst, "review file already staged (use --force to overwrite)"
        )

    rel = dst.relative_to(base)
    if dry_run:
        return StageResult(sku, "would-stage", src, dst, f"{src.name} -> {rel}")

    try:
        _convert_to_webp(src, dst)
    except OSError as exc:
        return StageResult(sku, "error", src, dst, f"webp conversion failed: {exc}")
    return StageResult(sku, "staged", src, dst, f"{src.name} -> {rel}")


def stage_all(
    *,
    root: Path | str | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> list[StageResult]:
    """Stage every SKU that has a product-source folder, honoring the skip list."""
    base = _resolve_root(root)
    skipped = load_skipped(base)
    results: list[StageResult] = []
    for sku in discover_skus(base):
        results.append(stage_one(sku, root=base, force=force, dry_run=dry_run, skipped=skipped))
    return results


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stage-review",
        description=(
            "Bridge a finished render into the approval queue: select the render, "
            "convert PNG->WEBP, write renders/ghost-mannequin/{sku}-ghost-front.webp. "
            "Run before approve_ghost.py."
        ),
    )
    parser.add_argument("sku", nargs="?", help="Catalog SKU (e.g. br-001). Omit with --all.")
    parser.add_argument("--all", action="store_true", help="Stage every SKU with a render.")
    parser.add_argument(
        "--render", default=None, help="Override render filename (single SKU only)."
    )
    parser.add_argument(
        "--force", action="store_true", help="Overwrite an already-staged review file."
    )
    parser.add_argument("--dry-run", action="store_true", help="Report actions without writing.")
    parser.add_argument(
        "--root", default=None, help="Repo root override (defaults to detected root)."
    )
    return parser


def _print_result(result: StageResult) -> None:
    glyph = {
        "staged": "OK  ",
        "would-stage": "DRY ",
        "exists": "skip",
        "already-approved": "skip",
        "skipped": "skip",
        "no-render": "wait",
        "error": "FAIL",
    }.get(result.status, "?   ")
    print(f"  [{glyph}] {result.sku:<9} {result.status:<16} {result.detail}")


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.all and args.sku:
        parser.error("pass a single SKU or --all, not both")
    if not args.all and not args.sku:
        parser.error("provide a SKU or --all")
    if args.render and args.all:
        parser.error("--render applies to a single SKU only, not --all")

    if args.all:
        results = stage_all(root=args.root, force=args.force, dry_run=args.dry_run)
    else:
        try:
            results = [
                stage_one(
                    args.sku,
                    root=args.root,
                    render=args.render,
                    force=args.force,
                    dry_run=args.dry_run,
                )
            ]
        except ReviewError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if not results:
        print("no SKUs to stage (no product-source folders found)")
        return 0

    print(f"stage-review ({'dry-run' if args.dry_run else 'live'}):")
    for result in results:
        _print_result(result)

    staged = sum(1 for r in results if r.status in ("staged", "would-stage"))
    failed = [r for r in results if r.status == "error"]
    print(f"\n{staged} staged, {len(results) - staged - len(failed)} skipped, {len(failed)} failed")
    if failed:
        for r in failed:
            print(f"  FAILED {r.sku}: {r.detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
