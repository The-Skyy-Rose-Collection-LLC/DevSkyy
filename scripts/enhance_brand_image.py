"""Enhance a brand-asset or product-reference image to canonical quality.

Single entry point for any image that's about to be saved into
`wordpress-theme/skyyrose-flagship/data/brand-logos/` or
`wordpress-theme/skyyrose-flagship/data/product-references/`. Runs a
deterministic enhancement pipeline:

    1. JPEG-artifact denoise via OpenCV bilateral filter (preserves edges).
    2. 2x upscale via PIL LANCZOS (no AI hallucination — pure resampling).
    3. Subtle unsharp mask to recover edge clarity lost to upscaling.
    4. Light contrast / saturation lift (1.05×) so logos read crisply.
    5. Save as high-quality JPEG (95) or lossless PNG, preserving aspect ratio.

Usage:
    python scripts/enhance_brand_image.py SOURCE TARGET
    python scripts/enhance_brand_image.py "/Users/.../photo.jpeg" \\
        wordpress-theme/skyyrose-flagship/data/brand-logos/sr-monogram.jpeg
    python scripts/enhance_brand_image.py SOURCE TARGET --upscale 4

The pipeline is deterministic (no AI, no paid API) — output quality depends
purely on Pillow + OpenCV's mathematical filters. For SkyyRose's primarily
illustrated logos / techflats, this is the right tradeoff: predictable
output, zero cost, no hallucination.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def enhance(
    source: Path,
    *,
    upscale: int = 2,
    denoise: bool = True,
    sharpen: bool = True,
    contrast: float = 1.05,
    saturation: float = 1.02,
) -> Image.Image:
    """Run the deterministic enhancement pipeline. Returns a Pillow Image."""
    if not source.is_file():
        raise FileNotFoundError(f"source image not found: {source}")

    if denoise:
        # Bilateral filter — gentle edge-preserving denoise. Removes JPEG
        # blocking artifacts on photographed/scanned techflats without
        # blurring crisp logo edges.
        cv_img = cv2.imread(str(source), cv2.IMREAD_UNCHANGED)
        if cv_img is None:
            raise RuntimeError(f"OpenCV could not decode {source}")
        if cv_img.ndim == 3 and cv_img.shape[2] == 4:
            # Preserve alpha — denoise BGR, keep A.
            bgr = cv_img[..., :3]
            alpha = cv_img[..., 3:4]
            denoised = cv2.bilateralFilter(bgr, d=7, sigmaColor=35, sigmaSpace=35)
            cv_img = np.concatenate([denoised, alpha], axis=2)
            img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGRA2RGBA))
        else:
            denoised = cv2.bilateralFilter(cv_img, d=7, sigmaColor=35, sigmaSpace=35)
            img = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
    else:
        img = Image.open(source).convert("RGB" if source.suffix.lower() != ".png" else "RGBA")

    if upscale > 1:
        new_size = (img.width * upscale, img.height * upscale)
        img = img.resize(new_size, Image.LANCZOS)

    if sharpen:
        img = img.filter(ImageFilter.UnsharpMask(radius=1.4, percent=140, threshold=2))

    if contrast and contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    if saturation and saturation != 1.0 and img.mode != "L":
        img = ImageEnhance.Color(img).enhance(saturation)

    return img


def save(img: Image.Image, target: Path, *, quality: int = 95) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    suffix = target.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(target, "JPEG", quality=quality, optimize=True, progressive=True)
    elif suffix == ".png":
        img.save(target, "PNG", optimize=True)
    elif suffix == ".webp":
        img.save(target, "WEBP", quality=quality, method=6)
    else:
        raise ValueError(f"unsupported target format: {suffix}")
    return target


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("source", type=Path, help="source image path")
    parser.add_argument("target", type=Path, help="enhanced output path")
    parser.add_argument("--upscale", type=int, default=2, help="upscale factor (1=no upscale)")
    parser.add_argument("--no-denoise", dest="denoise", action="store_false")
    parser.add_argument("--no-sharpen", dest="sharpen", action="store_false")
    parser.add_argument("--contrast", type=float, default=1.05)
    parser.add_argument("--saturation", type=float, default=1.02)
    parser.add_argument("--quality", type=int, default=95)
    parser.add_argument(
        "--keep-source-copy",
        action="store_true",
        help="also save the unmodified source alongside the enhanced output (debug)",
    )
    args = parser.parse_args(argv)

    img = enhance(
        args.source,
        upscale=args.upscale,
        denoise=args.denoise,
        sharpen=args.sharpen,
        contrast=args.contrast,
        saturation=args.saturation,
    )
    out = save(img, args.target, quality=args.quality)

    src_size = args.source.stat().st_size
    out_size = out.stat().st_size
    print(
        f"enhanced: {args.source.name} ({src_size:,}B, {Image.open(args.source).size}) "
        f"→ {out.name} ({out_size:,}B, {img.size})  "
        f"[upscale={args.upscale}x denoise={args.denoise} sharpen={args.sharpen}]"
    )

    if args.keep_source_copy:
        debug_path = out.with_name(out.stem + ".source-original" + args.source.suffix)
        shutil.copy2(args.source, debug_path)
        print(f"  source copy: {debug_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
