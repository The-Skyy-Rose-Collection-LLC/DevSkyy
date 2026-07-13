#!/usr/bin/env bash
# Key a white-background emblem render to a transparent cut-out, trim, resize,
# and emit webp + png matching the Black Rose / Love Hurts emblem convention
# (webp ~512 tall, png full-res). ImageMagick 4-corner floodfill preserves
# internal highlights (unlike a global -transparent white). rembg is broken on
# this env (numpy 2.x), so this is the keying path.
#
#   scripts/process_emblem.sh <input.png> <slug>
#   → assets/images/emblems/<slug>-emblem.{webp,png}  (into a target theme dir
#     via THEME_DIR override, default the repo theme)
set -euo pipefail

IN="${1:?usage: process_emblem.sh <input.png> <slug>}"
SLUG="${2:?usage: process_emblem.sh <input.png> <slug>}"
THEME="${THEME_DIR:-wordpress-theme/skyyrose-flagship}"
OUT_DIR="$THEME/assets/images/emblems"
FUZZ="${FUZZ:-10}"   # % tolerance for white-ish edges; tune per render

mkdir -p "$OUT_DIR"
W=$(identify -format '%w' "$IN"); H=$(identify -format '%h' "$IN")

# 4-corner floodfill to alpha, then trim to bbox. -fuzz absorbs JPEG-ish white
# noise; corners only, so interior gold/glass highlights survive.
magick "$IN" -alpha set -bordercolor white -border 1 \
  -fuzz "${FUZZ}%" -fill none \
  -draw "alpha 0,0 floodfill" \
  -draw "alpha $((W+1)),0 floodfill" \
  -draw "alpha 0,$((H+1)) floodfill" \
  -draw "alpha $((W+1)),$((H+1)) floodfill" \
  -shave 1x1 -trim +repage \
  "$OUT_DIR/${SLUG}-emblem.png"

# webp: cap height at 512 to match BR/LH webp scale, keep aspect + alpha.
magick "$OUT_DIR/${SLUG}-emblem.png" -resize 'x512>' \
  -define webp:lossless=false -quality 90 \
  "$OUT_DIR/${SLUG}-emblem.webp"

echo "wrote:"
identify -format '  %f  %wx%h  %b\n' "$OUT_DIR/${SLUG}-emblem.png" "$OUT_DIR/${SLUG}-emblem.webp"
echo "alpha corners (should be 0/transparent):"
magick "$OUT_DIR/${SLUG}-emblem.png" -format '  TL=%[pixel:p{0,0}]\n' info:
