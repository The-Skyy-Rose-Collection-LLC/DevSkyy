#!/bin/bash
#
# Batch Product Image Processor (ORIGINAL COLORS PRESERVED)
#
# Standardizes product photography WITHOUT altering product colors:
# - White background (#FFFFFF)
# - 1200×1600px (WooCommerce standard)
# - Quality enhancement (90%)
# - NO color tinting (preserves original product colors)
#
# Usage:
#   ./scripts/batch_product_processor_original_colors.sh INPUT_DIR OUTPUT_DIR
#
# Example:
#   ./scripts/batch_product_processor_original_colors.sh ~/products ./processed_products
#
# Formats Supported: JPG, PNG, HEIC
# Processing: Non-destructive (originals untouched)

set -e

# Configuration
TARGET_WIDTH=1200
TARGET_HEIGHT=1600
BG_COLOR="white"          # White background
QUALITY=90                # High quality JPG output

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Validate arguments
if [ "$#" -ne 2 ]; then
    echo -e "${RED}Error: Invalid arguments${NC}"
    echo "Usage: $0 INPUT_DIR OUTPUT_DIR"
    echo ""
    echo "Example:"
    echo "  $0 ~/products ./processed_products"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"

# Validate input directory
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}Error: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Verify ImageMagick installation
if ! command -v magick &> /dev/null && ! command -v convert &> /dev/null; then
    echo -e "${RED}Error: ImageMagick not found${NC}"
    echo "Install: brew install imagemagick"
    exit 1
fi

# Use 'magick' or 'convert' depending on version
MAGICK_CMD="magick"
if ! command -v magick &> /dev/null; then
    MAGICK_CMD="convert"
fi

echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Batch Product Image Processor (Original Colors)${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""
echo -e "Input directory:  ${INPUT_DIR}"
echo -e "Output directory: ${OUTPUT_DIR}"
echo -e "Target size:      ${TARGET_WIDTH}×${TARGET_HEIGHT}px"
echo -e "Background:       ${BG_COLOR}"
echo -e "Quality:          ${QUALITY}%"
echo -e "${YELLOW}Color tinting:    DISABLED (original colors preserved)${NC}"
echo ""
echo -e "${BLUE}============================================================${NC}"
echo ""

# Find all image files
shopt -s nullglob
image_files=()
for format in "*.jpg" "*.JPG" "*.jpeg" "*.JPEG" "*.png" "*.PNG" "*.heic" "*.HEIC"; do
    for file in "$INPUT_DIR"/$format; do
        [ -e "$file" ] || continue
        image_files+=("$file")
    done
done

total_files=${#image_files[@]}

if [ "$total_files" -eq 0 ]; then
    echo -e "${RED}Error: No image files found in $INPUT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}Found $total_files images to process${NC}"
echo ""

# Process images
processed=0
failed=0
start_time=$(date +%s)

for input_file in "${image_files[@]}"; do
    filename=$(basename "$input_file")
    name="${filename%.*}"
    output_file="$OUTPUT_DIR/${name}.jpg"

    echo -ne "${BLUE}[$((processed + failed + 1))/$total_files]${NC} Processing: $filename... "

    # ImageMagick processing (NO COLOR TINTING)
    if $MAGICK_CMD "$input_file" \
        -resize "${TARGET_WIDTH}x${TARGET_HEIGHT}^" \
        -gravity center \
        -extent "${TARGET_WIDTH}x${TARGET_HEIGHT}" \
        -background "$BG_COLOR" \
        -flatten \
        -quality $QUALITY \
        "$output_file" 2>/dev/null; then

        echo -e "${GREEN}✓${NC}"
        ((processed++))
    else
        echo -e "${RED}✗${NC}"
        ((failed++))
    fi
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}Processing Complete${NC}"
echo -e "${BLUE}============================================================${NC}"
echo -e "Processed:  ${GREEN}$processed${NC}"
echo -e "Failed:     ${RED}$failed${NC}"
echo -e "Duration:   ${duration}s"
echo ""
echo -e "${GREEN}✓ Output directory: $OUTPUT_DIR${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

if [ "$failed" -gt 0 ]; then
    echo -e "${YELLOW}⚠  Some images failed to process${NC}"
    echo "Check ImageMagick installation and input file formats"
    exit 1
fi

echo -e "${GREEN}✓ All images processed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review processed images in $OUTPUT_DIR"
echo "  2. Convert to WebP: ./scripts/webp_converter.sh $OUTPUT_DIR ./webp_output"
echo "  3. Upload to WordPress: python scripts/integrate_webp_wordpress.py"
echo ""
