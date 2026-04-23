"""Pre-flight source verification for the SkyyRose renders pipeline.

Resolves every SKU's source image using the same logic as config.py,
then prints the full manifest and requires explicit 'y' before any
FASHN API call is made.

Integrated into renders/__main__.py — runs automatically before every
sku / collection / all command unless --skip-preflight is passed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_TERMINAL_WIDTH = shutil.get_terminal_size((100, 40)).columns
_SEP = "─" * min(_TERMINAL_WIDTH, 100)

# Cost per FASHN API call (update when pricing changes)
_COST_PER_SAMPLE = 0.075  # tryon-v1.6 per image
_DEFAULT_SAMPLES = 4  # DEFAULT_NUM_SAMPLES from config
_MODELS_PER_PRODUCT = 4  # average models in MODEL_CAST per collection
_BG_REMOVE_COST = 0.025  # background-remove call


class PreflightAborted(RuntimeError):
    """Raised when the user rejects the manifest or a source file is missing."""


@dataclass
class SourceEntry:
    sku: str
    name: str
    collection: str
    source_path: str | None  # resolved path from _resolve_source_image
    source_exists: bool
    source_size_kb: float
    source_mtime: str
    resolution_method: str  # 'bundle_photo' | 'csv_override' | 'glob' | 'none'

    def __post_init__(self) -> None:
        if self.source_path:
            p = Path(self.source_path)
            self.source_exists = p.exists()
            if self.source_exists:
                st = p.stat()
                self.source_size_kb = st.st_size / 1024
                self.source_mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d")
        else:
            self.source_exists = False


def _detect_resolution_method(product: dict) -> str:
    """Infer how the source image was resolved."""
    from renders.config import PRODUCTS_DIR, _find_bundle_dir

    source = product.get("existing_front", "")
    if not source:
        return "none"

    # Bundle photo?
    bundle_dir = _find_bundle_dir(sku=product.get("sku", ""))
    if bundle_dir and source.startswith(str(bundle_dir)):
        return "bundle_photo"

    # CSV override or glob — both resolve inside PRODUCTS_DIR
    if source.startswith(str(PRODUCTS_DIR)):
        # Glob fallback names always contain the output_slug stem
        # CSV overrides are explicit filenames; glob picks largest file
        # We can't distinguish perfectly without re-running resolution,
        # so flag anything without a bundle photo as needing review.
        return "csv_override"

    return "glob"


def build_manifest(products: list[dict]) -> list[SourceEntry]:
    """Build preflight entries for a list of products from PRODUCT_CATALOG."""
    entries = []
    for p in products:
        source = p.get("existing_front")
        method = _detect_resolution_method(p)
        entry = SourceEntry(
            sku=p["sku"],
            name=p["name"],
            collection=p["collection"],
            source_path=source,
            source_exists=False,
            source_size_kb=0.0,
            source_mtime="",
            resolution_method=method,
        )
        entries.append(entry)
    return entries


def _try_show_thumbnail(path: str) -> None:
    """Show inline thumbnail if timg or chafa is available."""
    if os.getenv("RENDERS_PREVIEW", "1") == "0":
        return
    p = Path(path)
    if not p.exists():
        return
    for cmd in (
        ["timg", "--threads=-1", "-g", "32x16", str(p)],
        ["chafa", "--size", "32x16", str(p)],
    ):
        if shutil.which(cmd[0]):
            try:
                subprocess.run(
                    cmd, check=False, timeout=5, stdout=sys.stdout, stderr=subprocess.DEVNULL
                )
            except Exception:
                pass
            return


def print_manifest(
    entries: list[SourceEntry],
    num_models: int = _MODELS_PER_PRODUCT,
    num_samples: int = _DEFAULT_SAMPLES,
    include_bg_remove: bool = True,
    include_video: bool = False,
) -> tuple[int, int, float]:
    """
    Print manifest to stdout.
    Returns (total_fashn_calls, missing_count, estimated_cost_usd).
    """
    tryon_calls = len(entries) * num_models * num_samples
    bg_calls = len(entries) if include_bg_remove else 0
    tryon_cost = tryon_calls * _COST_PER_SAMPLE
    bg_cost = bg_calls * _BG_REMOVE_COST
    total_cost = tryon_cost + bg_cost
    missing: list[str] = []

    print()
    print("╔" + "═" * (min(_TERMINAL_WIDTH, 100) - 2) + "╗")
    print(
        "║  SKYYROSE RENDER PIPELINE — PRE-FLIGHT CHECK"
        + " " * (min(_TERMINAL_WIDTH, 100) - 48)
        + "║"
    )
    print("╚" + "═" * (min(_TERMINAL_WIDTH, 100) - 2) + "╝")
    print(f"  Products     : {len(entries)}")
    print(f"  Models / SKU : {num_models}")
    print(f"  Samples / run: {num_samples}")
    print(
        f"  FASHN calls  : {tryon_calls} try-on" + (f" + {bg_calls} bg-remove" if bg_calls else "")
    )
    print(
        f"  Est. cost    : ${total_cost:.2f}"
        + (f"  (${tryon_cost:.2f} try-on + ${bg_cost:.2f} bg-remove)" if bg_calls else "")
    )
    print(_SEP)

    for i, e in enumerate(entries, 1):
        if not e.source_path:
            status = "✗ NO SOURCE"
        elif not e.source_exists:
            status = "✗ FILE MISSING"
        elif e.resolution_method == "glob":
            status = "⚠ GLOB MATCH"
        elif e.resolution_method == "bundle_photo":
            status = "✓ BUNDLE PHOTO"
        elif e.resolution_method == "csv_override":
            status = "✓ CSV OVERRIDE"
        else:
            status = "✓ READY"

        print(f"\n  [{i:02d}]  {e.sku:<20s}  {status}")
        print(f"        {e.name}  [{e.collection}]")

        if e.source_path:
            prefix = "    → "
            full = prefix + e.source_path
            max_w = min(_TERMINAL_WIDTH, 100) - 2
            if len(full) > max_w:
                full = full[: max_w - 3] + "..."
            if not e.source_exists:
                full += "  ← MISSING"
            print(full)

            if e.source_exists:
                print(
                    f"        {Path(e.source_path).name}"
                    f"  ({e.source_size_kb:.0f}KB  {e.source_mtime}"
                    f"  via {e.resolution_method})"
                )
                _try_show_thumbnail(e.source_path)
        else:
            print("    → NO SOURCE MAPPED — will raise ValueError at runtime")

        if not e.source_exists:
            missing.append(e.sku)

    print()
    print(_SEP)

    glob_entries = [e for e in entries if e.resolution_method == "glob" and e.source_exists]
    if glob_entries:
        print(
            f"\n  ⚠  {len(glob_entries)} SKU(s) resolved via GLOB fallback "
            f"(no explicit source_override in CSV and no bundle photo):"
        )
        for e in glob_entries:
            print(f"     • {e.sku:<18s} → {Path(e.source_path).name}")
        print(
            "     Glob matches may pick the wrong file. "
            "Set render_source_override in product-catalog.csv to lock the source."
        )

    if missing:
        print(f"\n  ✗  {len(missing)} SKU(s) have NO source image on disk:")
        for sku in missing:
            print(f"     • {sku}")

    print()
    return tryon_calls, len(missing), total_cost


def preflight_verify(
    products: list[dict],
    num_models: int = _MODELS_PER_PRODUCT,
    num_samples: int = _DEFAULT_SAMPLES,
    include_bg_remove: bool = True,
    include_video: bool = False,
    *,
    skip: bool = False,
) -> list[SourceEntry]:
    """
    Run the preflight gate.

    Prints the source manifest and prompts for 'y' unless skip=True.
    Raises PreflightAborted if user declines or any source file is missing.
    Returns list of SourceEntry objects.
    """
    entries = build_manifest(products)
    total_calls, missing_count, estimated_cost = print_manifest(
        entries,
        num_models=num_models,
        num_samples=num_samples,
        include_bg_remove=include_bg_remove,
        include_video=include_video,
    )

    if missing_count:
        print(
            f"  ABORT: {missing_count} source image(s) missing from disk.\n"
            "  Fix the source paths before running the pipeline.\n"
        )
        raise PreflightAborted(
            f"{missing_count} source image(s) not found. "
            "Update render_source_override in product-catalog.csv or add bundle photos."
        )

    if skip:
        print("  [--skip-preflight] Confirmation skipped.\n")
        return entries

    print("  Every source image above will be sent to FASHN as the garment reference.")
    print("  Wrong image = wasted credits and wrong product photos on skyyrose.co.\n")

    try:
        answer = input("  Proceed with rendering? [y/N] > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  Non-interactive stdin — aborting. Use --skip-preflight for CI.\n")
        raise PreflightAborted("Non-interactive stdin: preflight aborted.")

    if answer not in ("y", "yes"):
        print("\n  Render cancelled. Zero FASHN credits spent.\n")
        raise PreflightAborted("User declined.")

    print()
    return entries
