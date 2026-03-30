#!/bin/bash
# Batch optimize all images in the WordPress theme
# Usage: bash scripts/optimize-images.sh [directory]
#
# Default: wordpress-theme/skyyrose-flagship/assets/images/
# Tools: ImageMagick, cwebp, optipng, pngquant, jpegoptim, svgo

set -euo pipefail

BREW="/opt/homebrew/bin"
TARGET_DIR="${1:-wordpress-theme/skyyrose-flagship/assets/images}"
MAX_WIDTH=2048
JPEG_QUALITY=90
WEBP_QUALITY=85
PNG_QUALITY="80-95"

# Counters
optimized=0
webp_created=0
resized=0
total_saved=0

echo "━━━ SkyyRose Image Optimizer ━━━"
echo "Directory: $TARGET_DIR"
echo ""

# ─── JPEG optimization ───
echo "▸ Optimizing JPEGs..."
find "$TARGET_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" \) | while read -r f; do
	orig_size=$(stat -f%z "$f")

	# Resize if too wide
	width=$("$BREW/magick" identify -format "%w" "$f" 2>/dev/null || echo "0")
	if [ "$width" -gt "$MAX_WIDTH" ] 2>/dev/null; then
		"$BREW/magick" "$f" -resize "${MAX_WIDTH}x>" -quality 92 "$f"
		echo "  ↕ Resized: $(basename "$f") (${width}px → ${MAX_WIDTH}px)"
		resized=$((resized + 1))
	fi

	# Optimize
	"$BREW/jpegoptim" --max=$JPEG_QUALITY --strip-all --quiet "$f" 2>/dev/null || true

	new_size=$(stat -f%z "$f")
	saved=$((orig_size - new_size))
	if [ "$saved" -gt 0 ]; then
		echo "  ✓ $(basename "$f") — saved $(( saved / 1024 ))KB"
		total_saved=$((total_saved + saved))
		optimized=$((optimized + 1))
	fi
done

# ─── PNG optimization ───
echo ""
echo "▸ Optimizing PNGs..."
find "$TARGET_DIR" -type f -name "*.png" | while read -r f; do
	orig_size=$(stat -f%z "$f")

	"$BREW/pngquant" --quality=$PNG_QUALITY --speed 3 --force --output "$f" "$f" 2>/dev/null || true
	"$BREW/optipng" -o2 -quiet "$f" 2>/dev/null || true

	new_size=$(stat -f%z "$f")
	saved=$((orig_size - new_size))
	if [ "$saved" -gt 0 ]; then
		echo "  ✓ $(basename "$f") — saved $(( saved / 1024 ))KB"
		total_saved=$((total_saved + saved))
		optimized=$((optimized + 1))
	fi
done

# ─── SVG optimization ───
echo ""
echo "▸ Optimizing SVGs..."
find "$TARGET_DIR" -type f -name "*.svg" | while read -r f; do
	"$BREW/svgo" --quiet "$f" 2>/dev/null || true
	echo "  ✓ $(basename "$f")"
done

# ─── WebP generation ───
echo ""
echo "▸ Generating WebP variants..."
find "$TARGET_DIR" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \) | while read -r f; do
	dir=$(dirname "$f")
	name=$(basename "${f%.*}")
	webp="${dir}/${name}.webp"

	if [ ! -f "$webp" ] || [ "$f" -nt "$webp" ]; then
		"$BREW/cwebp" -q $WEBP_QUALITY -m 6 -quiet "$f" -o "$webp" 2>/dev/null || true
		if [ -f "$webp" ]; then
			orig=$(stat -f%z "$f")
			new=$(stat -f%z "$webp")
			pct=0
			[ "$orig" -gt 0 ] && pct=$(( (orig - new) * 100 / orig ))
			echo "  ✓ ${name}.webp (${pct}% smaller)"
			webp_created=$((webp_created + 1))
		fi
	fi
done

echo ""
echo "━━━ Done ━━━"
echo "Optimized: $optimized files"
echo "WebP created: $webp_created files"
echo "Resized: $resized files"
echo "Total saved: $(( total_saved / 1024 ))KB"
