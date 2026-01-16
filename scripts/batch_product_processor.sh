#!/bin/bash
###############################################################################
# SkyyRose Batch Product Image Processor
#
# Standardizes product photography for luxury e-commerce:
# - Resize to 1200×1600 (WooCommerce optimal PDP size)
# - White background (#FFFFFF for clean luxury aesthetic)
# - Rose gold tint overlay (#C9A962 @ 15% opacity for brand consistency)
#
# Usage:
#   ./batch_product_processor.sh <input_dir> <output_dir> [--skip-tint]
#
# Example:
#   ./batch_product_processor.sh ./raw_photos ./processed_products
#   ./batch_product_processor.sh ./raw_photos ./processed_products --skip-tint
#
# @package SkyyRose_Imagery
# @version 1.0.0
###############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TARGET_WIDTH=1200
TARGET_HEIGHT=1600
BG_COLOR="#FFFFFF"
ROSE_GOLD="#C9A962"
TINT_OPACITY=15  # Percentage
QUALITY=90

# Check ImageMagick installation
if ! command -v magick &> /dev/null; then
    echo -e "${RED}ERROR: ImageMagick not found. Install with:${NC}"
    echo "  macOS: brew install imagemagick"
    echo "  Ubuntu: sudo apt-get install imagemagick"
    echo "  Windows: choco install imagemagick"
    exit 1
fi

# Parse arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <input_dir> <output_dir> [--skip-tint]"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
SKIP_TINT=false

if [ "${3:-}" == "--skip-tint" ]; then
    SKIP_TINT=true
fi

# Validate input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}ERROR: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Supported formats
FORMATS="*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG *.heic *.HEIC"

# Statistics
TOTAL=0
PROCESSED=0
SKIPPED=0
FAILED=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       SkyyRose Batch Product Image Processor v1.0.0        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Input:       $INPUT_DIR"
echo "  Output:      $OUTPUT_DIR"
echo "  Dimensions:  ${TARGET_WIDTH}×${TARGET_HEIGHT}px"
echo "  Background:  $BG_COLOR (white)"
echo "  Rose Tint:   $([ "$SKIP_TINT" == "true" ] && echo "Disabled" || echo "$ROSE_GOLD @ ${TINT_OPACITY}%")"
echo "  Quality:     $QUALITY%"
echo ""

# Process images
for format in $FORMATS; do
    for input_file in "$INPUT_DIR"/$format 2>/dev/null; do
        # Skip if glob didn't match
        [ -e "$input_file" ] || continue

        TOTAL=$((TOTAL + 1))
        filename=$(basename "$input_file")
        name="${filename%.*}"
        output_file="$OUTPUT_DIR/${name}.jpg"

        # Skip if already processed
        if [ -f "$output_file" ]; then
            echo -e "${YELLOW}⊘ Skipping (exists): $filename${NC}"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        echo -e "${BLUE}▶ Processing: $filename${NC}"

        # Process with ImageMagick
        if [ "$SKIP_TINT" == "true" ]; then
            # Standard processing without tint
            if magick "$input_file" \
                -resize "${TARGET_WIDTH}x${TARGET_HEIGHT}^" \
                -gravity center \
                -extent "${TARGET_WIDTH}x${TARGET_HEIGHT}" \
                -background "$BG_COLOR" \
                -flatten \
                -quality $QUALITY \
                "$output_file" 2>&1; then

                PROCESSED=$((PROCESSED + 1))
                echo -e "${GREEN}  ✓ Saved: $output_file${NC}"
            else
                FAILED=$((FAILED + 1))
                echo -e "${RED}  ✗ Failed: $filename${NC}"
            fi
        else
            # Processing with rose gold tint overlay
            if magick "$input_file" \
                -resize "${TARGET_WIDTH}x${TARGET_HEIGHT}^" \
                -gravity center \
                -extent "${TARGET_WIDTH}x${TARGET_HEIGHT}" \
                -background "$BG_COLOR" \
                -flatten \
                \( +clone -fill "$ROSE_GOLD" -colorize $TINT_OPACITY% \) \
                -composite \
                -quality $QUALITY \
                "$output_file" 2>&1; then

                PROCESSED=$((PROCESSED + 1))
                echo -e "${GREEN}  ✓ Saved: $output_file (rose gold tint applied)${NC}"
            else
                FAILED=$((FAILED + 1))
                echo -e "${RED}  ✗ Failed: $filename${NC}"
            fi
        fi
    done
done

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        Summary                               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo "  Total found:      $TOTAL"
echo -e "  ${GREEN}Processed:        $PROCESSED${NC}"
echo -e "  ${YELLOW}Skipped (exists): $SKIPPED${NC}"
echo -e "  ${RED}Failed:           $FAILED${NC}"
echo ""

if [ $PROCESSED -gt 0 ]; then
    echo -e "${GREEN}✓ Processing complete! Images saved to: $OUTPUT_DIR${NC}"
    exit 0
elif [ $TOTAL -eq 0 ]; then
    echo -e "${YELLOW}⚠ No images found in: $INPUT_DIR${NC}"
    echo "  Supported formats: JPG, JPEG, PNG, HEIC"
    exit 1
else
    echo -e "${RED}✗ No new images processed${NC}"
    exit 1
fi
