#!/usr/bin/env python3
"""upload-approved — STOP AND SHOW gated WC batch upload of approved ghost-mannequin images.

Phase 18 (UPLOAD-01). Reads renders/ghost-mannequin/approved/ + catalog, builds
manifest, prints STOP AND SHOW preview to stderr, prompts for literal "y", then
runs the upload via skyyrose.elite_studio.upload.upload_batch().

Exit codes:
    0 — all targeted SKUs UPLOADED or ALREADY_SYNCED; verification passed
    1 — manifest empty, user declined, WC error, verification mismatch, IO error
    2 — argparse usage error

Usage:
    upload_approved.py --dry-run            # manifest only, no WC calls, exits 0
    upload_approved.py                      # interactive STOP AND SHOW gate
    upload_approved.py --yes                # CI: skip stdin prompt (still prints preview)
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from skyyrose.elite_studio.upload import (  # noqa: E402
    PreviewRow,
    UploadManifest,
    WooCommerceUploader,
    append_upload_log,
    build_manifest,
    format_manifest_table,
    format_results_table,
    preview_manifest,
    upload_batch,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upload-approved",
        description=(
            "Batch-upload approved ghost-mannequin images to WooCommerce. "
            "STOP AND SHOW gate before any write. --dry-run for manifest-only preview."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build manifest and print preview; make zero WC calls; exit 0.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip interactive y/N prompt (still prints STOP AND SHOW to stderr).",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root override (defaults to script's parent dir).",
    )
    return parser


def _print_skipped(manifest: UploadManifest) -> None:
    if not manifest.skipped:
        return
    print("", file=sys.stderr)
    print(f"  SKIPPED ({len(manifest.skipped)} SKUs):", file=sys.stderr)
    for s in manifest.skipped:
        print(f"    {s.sku:<10} {s.reason}", file=sys.stderr)


def _dry_run_preview(manifest: UploadManifest) -> list[PreviewRow]:
    """Render manifest with no product_id / current image info (no WC calls)."""
    return [
        PreviewRow(
            sku=e.sku,
            source_path=e.source_path,
            product_id=None,
            current_image_url=None,
            status="READY",
        )
        for e in manifest.entries
    ]


def _print_stop_and_show(rows: list[PreviewRow], dry_run: bool) -> None:
    print("", file=sys.stderr)
    print("STOP — Confirm before proceeding:", file=sys.stderr)
    print("", file=sys.stderr)
    print("Action  : WooCommerce batch image upload", file=sys.stderr)
    print("Target  : WC REST v3 (live site)", file=sys.stderr)
    ready = sum(1 for r in rows if r.status == "READY")
    already = sum(1 for r in rows if r.status == "ALREADY_SYNCED")
    not_found = sum(1 for r in rows if r.status == "PRODUCT_NOT_FOUND")
    print(
        f"Totals  : {ready} to upload, {already} already synced (skip), "
        f"{not_found} product-not-found (skip)",
        file=sys.stderr,
    )
    print("Cost    : $0.00 (WordPress.com hosting, no per-call API cost)", file=sys.stderr)
    print("Manifest:", file=sys.stderr)
    print(format_manifest_table(rows), file=sys.stderr)
    if dry_run:
        print("", file=sys.stderr)
        print("[--dry-run] no confirmation prompt; no upload calls. Exiting.", file=sys.stderr)


def _prompt_confirmation() -> bool:
    sys.stderr.write("\nProceed? [y/N]: ")
    sys.stderr.flush()
    line = sys.stdin.readline()
    return line.strip().lower() in ("y", "yes")


async def run(args: argparse.Namespace) -> int:
    manifest = build_manifest(root=args.root)
    if not manifest.entries:
        print(
            "error: manifest empty — no approved/{sku}-ghost-front.webp files match catalog rows",
            file=sys.stderr,
        )
        _print_skipped(manifest)
        return 1

    if args.dry_run:
        rows = _dry_run_preview(manifest)
        _print_stop_and_show(rows, dry_run=True)
        _print_skipped(manifest)
        return 0

    # Live mode — connect to WC, do read-only preview, then gate write.
    async with WooCommerceUploader() as client:
        try:
            await client.smoke_test()
        except Exception as exc:
            print(f"error: WC connectivity/auth failure: {exc}", file=sys.stderr)
            return 1
        rows = await preview_manifest(client, manifest)
        _print_stop_and_show(rows, dry_run=False)
        _print_skipped(manifest)

        if not args.yes:
            if not _prompt_confirmation():
                print("aborted by user", file=sys.stderr)
                return 1

        results = await upload_batch(client, manifest)
        print("", file=sys.stderr)
        print("Results:", file=sys.stderr)
        print(format_results_table(results), file=sys.stderr)
        log_path = append_upload_log(results, root=args.root)
        print(f"\nlog: {log_path}", file=sys.stderr)

        failed = [r for r in results if r.status not in ("UPLOADED", "ALREADY_SYNCED", "DRY_RUN")]
        return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    # Configure logging to stderr at WARNING by default so logging.exception()
    # in the catch-all below produces a visible traceback. Operator can crank
    # to DEBUG via PYTHONLOGLEVEL or by editing in-place.
    logging.basicConfig(
        level=logging.WARNING,
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )
    args = build_parser().parse_args(argv)
    try:
        return asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 1
    except Exception as exc:
        # Full traceback to stderr via logging; only the exception class name
        # to the user-facing message (avoid echoing raw exc.args which may
        # contain env-derived strings from config loading).
        logging.exception("upload_approved unhandled exception")
        print(
            f"unexpected error: {exc.__class__.__name__} (traceback above)",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
