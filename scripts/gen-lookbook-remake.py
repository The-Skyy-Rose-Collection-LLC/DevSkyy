#!/usr/bin/env python3
"""Lookbook remake via gpt-image-2 EDIT (garment-preserving).

Takes the founder's existing Love Hurts lookbook (real garments already
composited in) as the SOURCE image and re-renders it "better" — same garments,
same layout, elevated scene. Because the garments come from the input image,
they are preserved, never invented (the "actual clothing" guarantee).

Two variants:
  v1 elevated  — faithful: same garments/layout, better light, detail, depth.
  v2 beauty    — push the Beauty-and-the-Beast enchanted-cathedral mood harder.

Keys read at runtime from .env.hf by python-dotenv — never printed.

Usage
-----
  python scripts/gen-lookbook-remake.py plan
  python scripts/gen-lookbook-remake.py go                 # both variants
  python scripts/gen-lookbook-remake.py go --variant v1    # one variant
  python scripts/gen-lookbook-remake.py go --source /path/to/ref.png
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path("/tmp/lh-lookbook-ref-hires.png")
OUTPUT_DIR = PROJECT_ROOT / "renders" / "oai" / "_lookbook"
# Masked mode (pixel-exact garments): prepped frame + garment mask from
# build-lookbook-mask.py must share geometry (1536x1024).
PREP_SOURCE = OUTPUT_DIR / "_prep-lh-lookbook-ref-hires.png"
MASK_PATH = OUTPUT_DIR / "_mask-lh-lookbook-ref-hires.png"

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env.hf", override=False)
except Exception as exc:  # pragma: no cover
    print(f"FATAL: could not load .env.hf ({exc})", file=sys.stderr)
    sys.exit(2)

MODEL = "gpt-image-2"
SIZE = "1536x1024"  # landscape, closest to the ~4:3 reference
QUALITY = "high"
EST_COST_PER_IMAGE = 0.40  # edit with 1 input image ≈ $0.35–0.40 (repo-verified floor)
HARD_CAP_USD = 5.0

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

# The non-negotiable garment-preservation clause, prepended to every variant.
PRESERVE = (
    "This is a fashion lookbook of REAL garments. Keep every garment EXACTLY as "
    "shown in the source image — identical designs, embroidery, printed text, "
    "logos, colors, proportions, and on-scene placement. Do NOT redesign, "
    "recolor, restyle, add, remove, or move any garment, bag, or the rose-under-"
    "glass. Only improve the surrounding scene, lighting, materials, and detail. "
)

VARIANTS = {
    "v1": (
        PRESERVE + "Re-render this Love Hurts lookbook at higher production value: cleaner "
        "studio-grade lighting, deeper shadow detail, richer stone and velvet "
        "textures, crisp focus on each garment, subtle volumetric haze, refined "
        "color grade in crimson and warm candlelight. Luxury streetwear editorial, "
        "photographic, ultra-detailed, 8k. Keep the gothic-cathedral setting and "
        "the same camera framing."
    ),
    "v2": (
        PRESERVE + "Intensify the Beauty-and-the-Beast enchantment: the single crimson rose "
        "under the glass cloche glowing softly as the heart of the room, dramatic "
        "god-rays pouring through the stained-glass windows, taller candle "
        "candelabra with warm flickering flame, heavier draped crimson and plum "
        "velvet, slow-falling rose petals suspended in the light, weathered marble "
        "and gold detailing, fairytale grandeur and romance-meets-darkness mood. "
        "Cinematic, painterly luxury, ultra-detailed, 8k. Same gothic cathedral, "
        "same garment placement."
    ),
}


def _as_upload(path: Path) -> tuple[str, bytes, str]:
    mime = _MIME.get(path.suffix.lower())
    if mime is None:
        raise ValueError(f"Unsupported source image type: {path}")
    size = path.stat().st_size
    if size > 20 * 1024 * 1024:  # OpenAI image-edit hard cap is 20 MB
        raise ValueError(f"{path.name} is {size // 1024 // 1024} MB (OpenAI edit cap 20 MB)")
    return (path.name, path.read_bytes(), mime)


def gen_edit(source: Path, prompt: str, mask: Path | None = None) -> bytes:
    from openai import OpenAI

    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY absent from .env.hf")
    client = OpenAI(api_key=key, timeout=240.0)
    kwargs: dict = {
        "model": MODEL,
        "image": [_as_upload(source)],
        "prompt": prompt,
        "size": SIZE,
        "quality": QUALITY,
        "n": 1,
    }
    if mask is not None:
        # Masked edit: alpha=0 regions regenerate, alpha=255 (garments) frozen.
        kwargs["mask"] = _as_upload(mask)
    resp = client.images.edit(**kwargs)
    b64 = resp.data[0].b64_json
    if not b64:
        raise RuntimeError("openai returned no image data")
    return base64.b64decode(b64)


def build_manifest(source: Path, variants: list[str], mask: Path | None) -> str:
    n = len(variants)
    total = n * EST_COST_PER_IMAGE
    src_ok = source.exists()
    mode = (
        "MASKED (pixel-exact garments — frozen by mask)"
        if mask
        else "generative (garments redrawn)"
    )
    mask_line = (
        f"  Mask        : {mask}  {'✓ exists' if mask and mask.exists() else '✗ MISSING'}"
        if mask
        else "  Mask        : (none — generative edit)"
    )
    lines = [
        "STOP — Confirm before proceeding (PAID gpt-image-2 EDIT — lookbook remake):",
        "",
        f"  Model       : {MODEL} (edit, quality={QUALITY}, size={SIZE})",
        f"  Mode        : {mode}",
        f"  Source      : {source}  {'✓ exists' if src_ok else '✗ MISSING'}",
        mask_line,
        f"  Variants    : {', '.join(variants)}",
        f"  Images      : {n}",
        f"  Est. cost   : ~${total:.2f}  (FLOOR @ ${EST_COST_PER_IMAGE:.2f}/img; OpenAI bills actual)",
        f"  Hard cap    : ${HARD_CAP_USD:.2f}" + ("  ⚠ EXCEEDED" if total > HARD_CAP_USD else ""),
        f"  Key present : {'✓' if os.environ.get('OPENAI_API_KEY') else '✗ MISSING'}",
        f"  Output      : {OUTPUT_DIR.relative_to(PROJECT_ROOT)}/love-hurts-remake-<variant>.png",
        "",
        "Proceed? [y/N]",
    ]
    return "\n".join(lines)


def run(source: Path, variants: list[str], mask: Path | None) -> int:
    if not source.exists():
        print(f"ABORT: source image not found: {source}", file=sys.stderr)
        return 2
    if mask is not None and not mask.exists():
        print(f"ABORT: mask not found: {mask}", file=sys.stderr)
        return 2
    total = len(variants) * EST_COST_PER_IMAGE
    if total > HARD_CAP_USD:
        print(f"ABORT: estimate ${total:.2f} exceeds hard cap ${HARD_CAP_USD:.2f}")
        return 2
    import openai

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "-masked" if mask else ""
    failures = 0
    for v in variants:
        dest = OUTPUT_DIR / f"love-hurts-remake-{v}{suffix}.png"
        try:
            print(f"[{v}] editing …", flush=True)
            data = gen_edit(source, VARIANTS[v], mask=mask)
            dest.write_bytes(data)
            print(f"[{v}] ✓ {dest}  ({len(data) // 1024} KB)", flush=True)
        except openai.AuthenticationError:
            # Never print str(exc) — the OpenAI SDK echoes a partial key in it.
            print(f"[{v}] ✗ AuthenticationError: check OPENAI_API_KEY", file=sys.stderr)
            return 1
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[{v}] ✗ {type(exc).__name__}: {exc}", file=sys.stderr)
    print(f"\nDone. {len(variants) - failures} ok, {failures} failed -> {OUTPUT_DIR}")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="gpt-image-2 lookbook remake")
    ap.add_argument("mode", choices=["plan", "go"])
    ap.add_argument(
        "--source",
        type=Path,
        default=None,
        help="default: prepped frame in masked mode, else raw ref",
    )
    ap.add_argument("--variant", action="append", choices=["v1", "v2"], help="default = both")
    ap.add_argument(
        "--masked",
        action="store_true",
        help="pixel-exact: use the prepped frame + garment mask (frozen garments)",
    )
    ap.add_argument("--mask", type=Path, default=None, help="override mask path (implies --masked)")
    args = ap.parse_args()
    variants = args.variant or ["v1", "v2"]

    mask = None
    if args.mask is not None:
        mask = args.mask
    elif args.masked:
        mask = MASK_PATH
    # In masked mode the source MUST match the mask geometry → the prepped frame.
    source = args.source or (PREP_SOURCE if mask else DEFAULT_SOURCE)

    if args.mode == "plan":
        print(build_manifest(source, variants, mask))
        return 0
    return run(source, variants, mask)


if __name__ == "__main__":
    raise SystemExit(main())
