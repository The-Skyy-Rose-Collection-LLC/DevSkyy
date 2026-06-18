#!/usr/bin/env python3
"""Build a garment-preserving mask for a gpt-image-2 masked edit (FREE, local).

Pipeline (no API, no spend):
  1. Crop the source lookbook to the edit aspect (default 3:2) and resize to the
     edit size, so source + mask + output all share one geometry.
  2. Segment the foreground garment/display cluster with rembg (u2net, cached).
  3. Clean the alpha: fill interior holes, dilate a protective margin so garment
     edges are never clipped, feather the boundary for a clean regen seam.
  4. Emit the OpenAI mask (alpha=255 over garments => FROZEN; alpha=0 over the
     scene => REGENERATED — per OpenAI's "transparent areas are edited" rule).
  5. Emit a human overlay: garments full-colour, the regen zone dimmed — so the
     founder can see exactly what is locked before any paid edit.

Outputs -> renders/oai/_lookbook/:
  _prep-<stem>.png      prepped source (edit geometry)
  _mask-<stem>.png      OpenAI mask (RGBA)
  _overlay-<stem>.png   reviewable protected-region overlay
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove
from scipy import ndimage

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "renders" / "oai" / "_lookbook"

# Per-garment protect boxes in the prepped 1536x1024 frame. Salient-object
# models miss scattered garments, so we segment each garment inside its own box
# (where it IS the salient object) and union the cuts. Boxes are generous;
# rembg tightens to the actual garment edge inside each.
PRESETS: dict[str, list[tuple[int, int, int, int]]] = {
    # Love Hurts lookbook: jacket / rose-shorts / track-pants / bag / black-shorts.
    # The rose-under-glass is intentionally EXCLUDED so the scene can relight it.
    "love-hurts": [
        (430, 120, 810, 620),  # bomber jacket on the bust (hood + body)
        (945, 135, 1220, 470),  # rose-print shorts, hanging upper-right
        (1085, 520, 1350, 865),  # white track pants on the right throne
        (1290, 365, 1490, 685),  # FANATIC bag, far right
        (70, 585, 350, 790),  # black shorts draped on the left pew
    ],
}


def crop_to_aspect(img: Image.Image, aspect_w: int, aspect_h: int) -> Image.Image:
    """Centre-crop to the target aspect (keeps the mid-frame garments)."""
    w, h = img.size
    target = aspect_w / aspect_h
    if w / h > target:  # too wide -> crop width
        new_w = int(round(h * target))
        x0 = (w - new_w) // 2
        return img.crop((x0, 0, x0 + new_w, h))
    new_h = int(round(w / target))  # too tall -> crop height
    y0 = (h - new_h) // 2
    return img.crop((0, y0, w, y0 + new_h))


def clean_alpha(alpha: np.ndarray, *, dilate_px: int, feather_px: int) -> np.ndarray:
    """Binarise -> fill holes -> dilate margin -> feather. Returns uint8 0..255."""
    binary = alpha > 96
    binary = ndimage.binary_fill_holes(binary)
    # Drop tiny specks (keep components >= 0.05% of frame).
    labels, n = ndimage.label(binary)
    if n:
        min_area = int(0.0005 * binary.size)
        keep = np.zeros_like(binary)
        for i in range(1, n + 1):
            comp = labels == i
            if comp.sum() >= min_area:
                keep |= comp
        binary = keep
    mask = (binary * 255).astype(np.uint8)
    if dilate_px > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_px * 2 + 1, dilate_px * 2 + 1))
        mask = cv2.dilate(mask, k)
    if feather_px > 0:
        ksize = feather_px * 2 + 1
        mask = cv2.GaussianBlur(mask, (ksize, ksize), 0)
    return mask


def segment_by_boxes(
    img: Image.Image, boxes: list[tuple[int, int, int, int]], model: str
) -> np.ndarray:
    """Segment each garment inside its own box and union the alphas (full-frame)."""
    w, h = img.size
    full = np.zeros((h, w), dtype=np.uint8)
    session = new_session(model)
    for x0, y0, x1, y1 in boxes:
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(w, x1), min(h, y1)
        if x0 >= x1 or y0 >= y1:
            print(f"WARN: box {(x0, y0, x1, y1)} clipped to zero — skipping", file=sys.stderr)
            continue
        crop = img.crop((x0, y0, x1, y1))
        cut = remove(crop, session=session)
        a = np.array(cut.split()[-1])
        full[y0:y1, x0:x1] = np.maximum(full[y0:y1, x0:x1], a)
    return full


def main() -> int:
    ap = argparse.ArgumentParser(description="Build garment-preserving edit mask")
    ap.add_argument("--source", type=Path, default=Path("/tmp/lh-lookbook-ref-hires.png"))
    ap.add_argument("--width", type=int, default=1536)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--dilate", type=int, default=10, help="protective margin px")
    ap.add_argument("--feather", type=int, default=6, help="edge feather px")
    ap.add_argument("--model", default="u2net", help="rembg model (u2net | isnet-general-use)")
    ap.add_argument(
        "--preset",
        choices=sorted(PRESETS),
        help="per-garment box preset (segments each garment separately, then unions)",
    )
    args = ap.parse_args()

    if not args.source.is_file():
        print(f"ABORT: source not a readable file: {args.source}")
        return 2
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stem = args.source.stem

    src = Image.open(args.source).convert("RGB")
    prepped = crop_to_aspect(src, args.width, args.height).resize(
        (args.width, args.height), Image.LANCZOS
    )
    prep_path = OUTPUT_DIR / f"_prep-{stem}.png"
    prepped.save(prep_path)

    if args.preset:
        alpha = segment_by_boxes(prepped, PRESETS[args.preset], args.model)
    else:
        cut = remove(prepped, session=new_session(args.model))  # RGBA, bg transparent
        alpha = np.array(cut.split()[-1])
    fg = clean_alpha(alpha, dilate_px=args.dilate, feather_px=args.feather)

    # OpenAI mask: alpha=255 over garments (FROZEN), 0 over scene (REGEN).
    mask_rgba = np.zeros((args.height, args.width, 4), dtype=np.uint8)
    mask_rgba[..., 3] = fg
    mask_path = OUTPUT_DIR / f"_mask-{stem}.png"
    Image.fromarray(mask_rgba, "RGBA").save(mask_path)

    # Human overlay: garments full-colour; regen zone dimmed + green-tinted.
    base = np.array(prepped).astype(np.float32)
    fg_f = (fg.astype(np.float32) / 255.0)[..., None]
    dimmed = base * 0.30
    dimmed[..., 1] = np.clip(dimmed[..., 1] + 40, 0, 255)  # green cast on regen zone
    overlay = (base * fg_f + dimmed * (1 - fg_f)).astype(np.uint8)
    overlay_path = OUTPUT_DIR / f"_overlay-{stem}.png"
    Image.fromarray(overlay).save(overlay_path)

    pct = 100.0 * (fg > 127).sum() / fg.size
    print(f"prepped : {prep_path}  ({args.width}x{args.height})")
    print(f"mask    : {mask_path}  (frozen={pct:.1f}% of frame)")
    print(f"overlay : {overlay_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
