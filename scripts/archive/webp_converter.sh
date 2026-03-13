#!/bin/bash
###############################################################################
# SkyyRose WebP Converter with Safari Fallback
#
# Converts JPG/PNG to WebP format for 90% size reduction while maintaining
# quality. Automatically generates fallback JPG for Safari <14 and older browsers.
#
# Features:
# - Batch conversion of all JPG/PNG in directory
# - Maintains directory structure
# - Generates both .webp and .jpg fallback
# - Preserves original files (non-destructive)
# - Quality control (default 85 for optimal size/quality)
#
# Usage:
#   ./webp_converter.sh <input_dir> <output_dir> [quality]
#
# Example:
#   ./webp_converter.sh ./product_images ./optimized_images
#   ./webp_converter.sh ./product_images ./optimized_images 90
#
# WordPress Integration:
#   Use with <picture> tag for automatic fallback:
#   <picture>
#     <source srcset="image.webp" type="image/webp">
#     <img src="image.jpg" alt="Product">
#   </picture>
#
# @package SkyyRose_Imagery
# @version 1.0.0
###############################################################################

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Default configuration
DEFAULT_QUALITY=85
FALLBACK_QUALITY=90  # Higher quality for fallback JPG

# Check ImageMagick installation
if ! command -v magick &> /dev/null; then
    echo -e "${RED}ERROR: ImageMagick not found. Install with:${NC}"
    echo "  macOS: brew install imagemagick"
    echo "  Ubuntu: sudo apt-get install imagemagick"
    exit 1
fi

# Check WebP support
if ! magick -list format | grep -q WebP; then
    echo -e "${RED}ERROR: ImageMagick WebP delegate not found${NC}"
    echo "Reinstall ImageMagick with WebP support:"
    echo "  macOS: brew reinstall imagemagick --with-webp"
    exit 1
fi

# Parse arguments
if [ $# -lt 2 ]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <input_dir> <output_dir> [quality]"
    echo ""
    echo "Arguments:"
    echo "  input_dir   - Directory containing JPG/PNG images"
    echo "  output_dir  - Directory for WebP + fallback outputs"
    echo "  quality     - WebP quality 1-100 (default: $DEFAULT_QUALITY)"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
QUALITY="${3:-$DEFAULT_QUALITY}"

# Validate input
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}ERROR: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

if ! [[ "$QUALITY" =~ ^[0-9]+$ ]] || [ "$QUALITY" -lt 1 ] || [ "$QUALITY" -gt 100 ]; then
    echo -e "${RED}ERROR: Quality must be 1-100${NC}"
    exit 1
fi

# Create output directories
mkdir -p "$OUTPUT_DIR/webp"
mkdir -p "$OUTPUT_DIR/fallback"

# Statistics
TOTAL=0
WEBP_CREATED=0
FALLBACK_CREATED=0
SKIPPED=0
FAILED=0
TOTAL_ORIGINAL_SIZE=0
TOTAL_WEBP_SIZE=0
TOTAL_FALLBACK_SIZE=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         SkyyRose WebP Converter with Fallback v1.0.0        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Input:          $INPUT_DIR"
echo "  Output (WebP):  $OUTPUT_DIR/webp"
echo "  Output (JPG):   $OUTPUT_DIR/fallback"
echo "  WebP Quality:   $QUALITY%"
echo "  JPG Quality:    $FALLBACK_QUALITY%"
echo ""

# Function to get file size in bytes
get_file_size() {
    if [ -f "$1" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            stat -f%z "$1"
        else
            stat -c%s "$1"
        fi
    else
        echo 0
    fi
}

# Function to format bytes
format_bytes() {
    local bytes=$1
    if [ $bytes -lt 1024 ]; then
        echo "${bytes}B"
    elif [ $bytes -lt 1048576 ]; then
        echo "$(( bytes / 1024 ))KB"
    else
        echo "$(( bytes / 1048576 ))MB"
    fi
}

# Process images
FORMATS="*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG"

for format in $FORMATS; do
    for input_file in "$INPUT_DIR"/$format; do
        [ -e "$input_file" ] || continue

        TOTAL=$((TOTAL + 1))
        filename=$(basename "$input_file")
        name="${filename%.*}"

        webp_output="$OUTPUT_DIR/webp/${name}.webp"
        fallback_output="$OUTPUT_DIR/fallback/${name}.jpg"

        # Check if both already exist
        if [ -f "$webp_output" ] && [ -f "$fallback_output" ]; then
            echo -e "${YELLOW}⊘ Skipping (exists): $filename${NC}"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        echo -e "${BLUE}▶ Processing: $filename${NC}"

        original_size=$(get_file_size "$input_file")
        TOTAL_ORIGINAL_SIZE=$((TOTAL_ORIGINAL_SIZE + original_size))

        # Create WebP version
        if [ ! -f "$webp_output" ]; then
            if magick "$input_file" -quality $QUALITY "$webp_output" 2>&1; then
                webp_size=$(get_file_size "$webp_output")
                TOTAL_WEBP_SIZE=$((TOTAL_WEBP_SIZE + webp_size))
                WEBP_CREATED=$((WEBP_CREATED + 1))

                savings=$(( 100 - (webp_size * 100 / original_size) ))
                echo -e "${GREEN}  ✓ WebP:     $(format_bytes $webp_size) (${savings}% smaller)${NC}"
            else
                FAILED=$((FAILED + 1))
                echo -e "${RED}  ✗ WebP conversion failed${NC}"
                continue
            fi
        fi

        # Create JPG fallback (for Safari <14, IE, older browsers)
        if [ ! -f "$fallback_output" ]; then
            if magick "$input_file" -quality $FALLBACK_QUALITY "$fallback_output" 2>&1; then
                fallback_size=$(get_file_size "$fallback_output")
                TOTAL_FALLBACK_SIZE=$((TOTAL_FALLBACK_SIZE + fallback_size))
                FALLBACK_CREATED=$((FALLBACK_CREATED + 1))

                echo -e "${MAGENTA}  ✓ Fallback: $(format_bytes $fallback_size)${NC}"
            else
                echo -e "${YELLOW}  ⚠ Fallback creation failed (WebP still available)${NC}"
            fi
        fi
    done
done

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        Summary                               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo "  Total images:      $TOTAL"
echo -e "  ${GREEN}WebP created:      $WEBP_CREATED${NC}"
echo -e "  ${MAGENTA}Fallbacks created: $FALLBACK_CREATED${NC}"
echo -e "  ${YELLOW}Skipped (exists):  $SKIPPED${NC}"
echo -e "  ${RED}Failed:            $FAILED${NC}"
echo ""

if [ $WEBP_CREATED -gt 0 ]; then
    # Calculate savings
    avg_savings=$(( 100 - (TOTAL_WEBP_SIZE * 100 / TOTAL_ORIGINAL_SIZE) ))

    echo -e "${YELLOW}Size Analysis:${NC}"
    echo "  Original total:  $(format_bytes $TOTAL_ORIGINAL_SIZE)"
    echo "  WebP total:      $(format_bytes $TOTAL_WEBP_SIZE)"
    echo "  Fallback total:  $(format_bytes $TOTAL_FALLBACK_SIZE)"
    echo ""
    echo -e "${GREEN}  Average savings: ${avg_savings}%${NC}"
    echo ""
fi

# WordPress integration guide
if [ $WEBP_CREATED -gt 0 ]; then
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               WordPress Integration Guide                    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Use <picture> tag for automatic browser fallback:"
    echo ""
    echo -e "${YELLOW}<picture>${NC}"
    echo -e "${YELLOW}  <source srcset=\"/webp/product.webp\" type=\"image/webp\">${NC}"
    echo -e "${YELLOW}  <img src=\"/fallback/product.jpg\" alt=\"Product\">${NC}"
    echo -e "${YELLOW}</picture>${NC}"
    echo ""
    echo "Or use WebP Express plugin: https://wordpress.org/plugins/webp-express/"
    echo ""
fi

if [ $WEBP_CREATED -gt 0 ]; then
    echo -e "${GREEN}✓ Conversion complete!${NC}"
    echo "  WebP:     $OUTPUT_DIR/webp/"
    echo "  Fallback: $OUTPUT_DIR/fallback/"
    exit 0
elif [ $TOTAL -eq 0 ]; then
    echo -e "${YELLOW}⚠ No images found in: $INPUT_DIR${NC}"
    exit 1
else
    echo -e "${RED}✗ No new images processed${NC}"
    exit 1
fi
