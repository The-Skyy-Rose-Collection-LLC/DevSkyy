#!/usr/bin/env python3
"""Generate AVIF siblings for every V7 product-card shot (webp/png/jpg → .avif).

The V7 lookbook card (``template-parts/product-card-v7-lookbook.php``) serves each
shot through a ``<picture>`` element with an ``image/avif`` ``<source>`` whenever the
``.avif`` sibling is present on disk, falling back to the webp/png ``<img>``. AVIF is
~25-35% smaller than webp at equal quality — a standard e-commerce LCP/bandwidth win.
This produces those siblings for the tracked V7 served tree.

Idempotent: a shot whose ``.avif`` exists and is newer-or-equal to its source is
skipped (pass ``--force`` to rebuild all). Stdlib + Pillow (AVIF) — the theme's
build-time image step, NOT a CI/runtime dependency (the PHP only checks file
existence, never imports this).

Run (project .venv has Pillow w/ AVIF):
    PYTHONPATH=. .venv/bin/python scripts/gen_v7_avif.py [--force]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

_V7_DIR = Path(__file__).resolve().parents[1] / (
    "wordpress-theme/skyyrose-flagship/assets/images/products/v7"
)
_SRC_EXTS = (".webp", ".png", ".jpg", ".jpeg")
_AVIF_QUALITY = 60
_FORCE = "--force" in sys.argv[1:]


def _current(avif: Path, src: Path) -> bool:
    """True when ``avif`` exists and is at least as new as ``src`` (skip rebuild)."""
    return avif.exists() and avif.stat().st_mtime >= src.stat().st_mtime


def main() -> int:
    if not _V7_DIR.is_dir():
        print(f"no V7 tree at {_V7_DIR}", file=sys.stderr)
        return 1
    made, skipped = [], 0
    for src in sorted(_V7_DIR.rglob("*")):
        if src.suffix.lower() not in _SRC_EXTS or not src.is_file():
            continue
        avif = src.with_suffix(".avif")
        if not _FORCE and _current(avif, src):
            skipped += 1
            continue
        im = Image.open(src)
        if im.mode in ("P", "LA"):
            im = im.convert("RGBA")
        elif im.mode == "CMYK":
            im = im.convert("RGB")
        im.save(avif, "AVIF", quality=_AVIF_QUALITY)
        rel = src.relative_to(_V7_DIR.parent)
        made.append(f"{rel} → {avif.name} ({avif.stat().st_size // 1024}KB)")

    for m in made:
        print(f"  {m}")
    print(f"\navif: {len(made)} written | {skipped} up-to-date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
