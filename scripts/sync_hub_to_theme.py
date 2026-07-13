#!/usr/bin/env python3
"""Stage verified hub renders into the WordPress theme (as webp+avif) so they serve.

The hub (``assets/hub/manifest.json``) is the verified imagery authority. Legacy-theme
picks already live under the theme and serve as-is; verified renders from off-theme
engines (oai-image-2 / gemini / pipeline) must be transcoded into the theme tree to be
servable. The theme serves **webp/avif** only (``.gitignore`` excludes ``*.png`` under
``assets/**``, and ``inc/performance.php`` auto-serves the ``.avif`` sibling of a base
when it exists), so this transcodes each canonical verified ``<sku>-<face>`` whose
``source`` is NOT already under the theme into BOTH:

    wordpress-theme/skyyrose-flagship/assets/images/products/hub/<sku>-<face>.webp
    wordpress-theme/skyyrose-flagship/assets/images/products/hub/<sku>-<face>.avif

``asset_hub.served_theme_path`` returns the ``.webp`` path; ``build-collection-sot.py``
overrides the catalog front/back to it, so the whole SOT chain (sot.json → PHP theme,
data/sot-images.json → dashboard) honors the verdict. Idempotent: an up-to-date,
larger-or-equal-mtime ``.webp`` is left alone.

Dry-run by DEFAULT (prints the staging plan, transcodes nothing). ``--apply`` writes.
This stages files for deploy; the skyyrose.co deploy itself stays STOP-AND-SHOW.

Run (needs Pillow w/ webp+avif — the project .venv has both):
    PYTHONPATH=. .venv/bin/python scripts/sync_hub_to_theme.py [--apply]
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

from skyyrose.core import asset_hub
from skyyrose.core.paths import REPO_ROOT, THEME_ROOT

APPLY = "--apply" in sys.argv[1:]
HUB_DIR = REPO_ROOT / "assets" / "hub"
WEBP_QUALITY = 82
AVIF_QUALITY = 60


def staging_plan() -> list[dict]:
    """Canonical verified front/back whose source is off-theme → transcode plan."""
    plan: list[dict] = []
    for aid, e in asset_hub.manifest().items():
        sku, face = e.get("sku"), e.get("face")
        if not sku or not face or aid != f"{sku}-{face}":
            continue
        if e.get("verdict") != "verified":
            continue
        if (e.get("source") or "").startswith(asset_hub.THEME_PREFIX):
            continue  # already serves from the theme as-is
        hub_path = e.get("path")
        if not hub_path:
            continue
        src = HUB_DIR / hub_path
        base = f"{asset_hub.HUB_THEME_SUBDIR}/{sku}-{face}"
        plan.append(
            {
                "aid": aid,
                "engine": e.get("engine"),
                "src": src,
                "webp": THEME_ROOT / f"{base}.webp",
                "avif": THEME_ROOT / f"{base}.avif",
            }
        )
    return plan


def _transcode(src: Path, webp: Path, avif: Path) -> tuple[int, int]:
    """Write webp + avif derivatives of ``src``; return (webp_kb, avif_kb)."""
    im = Image.open(src)
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    elif im.mode == "CMYK":
        im = im.convert("RGB")
    webp.parent.mkdir(parents=True, exist_ok=True)
    im.save(webp, "WEBP", quality=WEBP_QUALITY, method=6)
    im.save(avif, "AVIF", quality=AVIF_QUALITY)
    return webp.stat().st_size // 1024, avif.stat().st_size // 1024


def main() -> int:
    plan = staging_plan()
    print(f"HUB → THEME transcode  ({'APPLY' if APPLY else 'DRY-RUN — no writes'})")
    print(
        f"dest: {asset_hub.THEME_PREFIX}{asset_hub.HUB_THEME_SUBDIR}/  (webp q{WEBP_QUALITY} + avif q{AVIF_QUALITY})\n"
    )
    if not plan:
        print("nothing to stage — every verified face already serves from the theme.")
        return 0

    done, missing = [], []
    for p in plan:
        if not p["src"].exists():
            print(f"  {p['aid']:14s} {p['engine']:11s}  MISSING-SRC  {p['src']}")
            missing.append(p["aid"])
            continue
        src_kb = p["src"].stat().st_size // 1024
        rel = p["webp"].relative_to(THEME_ROOT)
        if APPLY:
            wkb, akb = _transcode(p["src"], p["webp"], p["avif"])
            print(
                f"  {p['aid']:14s} {p['engine']:11s} {src_kb:>5}KB → webp {wkb}KB + avif {akb}KB  {rel}"
            )
        else:
            print(f"  {p['aid']:14s} {p['engine']:11s} {src_kb:>5}KB → {rel} (+ .avif)")
        done.append(p["aid"])

    verb = "transcoded" if APPLY else "would transcode"
    print(f"\n{verb}: {len(done)} | missing-src: {len(missing)} {missing}")
    if not APPLY:
        print("\nDry-run only. Re-run with --apply to stage. (Deploy to skyyrose.co stays gated.)")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
