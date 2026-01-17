#!/bin/bash
###############################################################################
# SkyyRose Responsive Image Generator
#
# Generates responsive image variants for hero sections, banners, and featured
# content. Creates optimized versions for desktop, tablet, mobile, and retina
# displays following modern web performance best practices.
#
# Standard Breakpoints (SkyyRose Design System):
#   - Desktop:     1920×1080 (Full HD hero)
#   - Desktop 2x:  3840×2160 (Retina/4K)
#   - Tablet:      1024×576  (iPad landscape)
#   - Mobile:      768×432   (iPad portrait)
#   - Mobile 2x:   1536×864  (Retina mobile)
#   - Small:       375×211   (iPhone SE/modern phones)
#
# Usage:
#   ./responsive_image_generator.sh <input_dir> <output_dir> [--aspect RATIO]
#
# Example:
#   ./responsive_image_generator.sh ./hero_images ./responsive_heroes
#   ./responsive_image_generator.sh ./banners ./responsive_banners --aspect 21:9
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
CYAN='\033[0;36m'
NC='\033[0m'

# Default configuration
DEFAULT_ASPECT="16:9"
QUALITY=85

# Check arguments BEFORE strict mode activates array
if [ $# -lt 2 ]; then
    echo -e "${RED}ERROR: Missing required arguments${NC}"
    echo "Usage: $0 <input_dir> <output_dir> [--aspect RATIO]"
    echo ""
    echo "Arguments:"
    echo "  input_dir   - Directory with source hero/banner images"
    echo "  output_dir  - Directory for responsive variants"
    echo "  --aspect    - Aspect ratio (default: $DEFAULT_ASPECT)"
    echo "                Options: 16:9, 21:9, 4:3, 1:1"
    echo ""
    echo "Breakpoints:"
    echo "  desktop-2x: 3840x2160"
    echo "  desktop:    1920x1080"
    echo "  tablet:     1024x576"
    echo "  mobile-2x:  1536x864"
    echo "  mobile:     768x432"
    echo "  small:      375x211"
    exit 1
fi

# Breakpoint definitions (width×height)
# Format: "name:widthxheight"
BREAKPOINTS="desktop:1920x1080 desktop-2x:3840x2160 tablet:1024x576 mobile:768x432 mobile-2x:1536x864 small:375x211"

# Check ImageMagick
if ! command -v magick &> /dev/null; then
    echo -e "${RED}ERROR: ImageMagick not found${NC}"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
ASPECT="$DEFAULT_ASPECT"

# Parse optional aspect ratio
shift 2
while [ $# -gt 0 ]; do
    case "$1" in
        --aspect)
            ASPECT="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}ERROR: Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Validate input
if [ ! -d "$INPUT_DIR" ]; then
    echo -e "${RED}ERROR: Input directory does not exist: $INPUT_DIR${NC}"
    exit 1
fi

# Adjust breakpoints for aspect ratio
case "$ASPECT" in
    21:9)
        BREAKPOINTS["desktop"]="2560x1080"
        BREAKPOINTS["desktop-2x"]="5120x2160"
        BREAKPOINTS["tablet"]="1366x576"
        BREAKPOINTS["mobile"]="1024x432"
        ;;
    4:3)
        BREAKPOINTS["desktop"]="1440x1080"
        BREAKPOINTS["desktop-2x"]="2880x2160"
        BREAKPOINTS["tablet"]="768x576"
        BREAKPOINTS["mobile"]="576x432"
        ;;
    1:1)
        BREAKPOINTS["desktop"]="1080x1080"
        BREAKPOINTS["desktop-2x"]="2160x2160"
        BREAKPOINTS["tablet"]="768x768"
        BREAKPOINTS["mobile"]="600x600"
        BREAKPOINTS["small"]="375x375"
        ;;
esac

# Create output directories
for bp in "${!BREAKPOINTS[@]}"; do
    mkdir -p "$OUTPUT_DIR/$bp"
done

# Statistics
TOTAL=0
PROCESSED=0
SKIPPED=0
FAILED=0

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      SkyyRose Responsive Image Generator v1.0.0             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  Input:       $INPUT_DIR"
echo "  Output:      $OUTPUT_DIR"
echo "  Aspect:      $ASPECT"
echo "  Quality:     $QUALITY%"
echo ""
echo -e "${CYAN}Breakpoints:${NC}"
for bp in desktop desktop-2x tablet mobile mobile-2x small; do
    if [ -n "${BREAKPOINTS[$bp]:-}" ]; then
        echo "  $bp: ${BREAKPOINTS[$bp]}"
    fi
done
echo ""

# Process images
FORMATS="*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG"

for format in $FORMATS; do
    for input_file in "$INPUT_DIR"/$format; do
        [ -e "$input_file" ] || continue

        TOTAL=$((TOTAL + 1))
        filename=$(basename "$input_file")
        name="${filename%.*}"

        echo -e "${BLUE}▶ Processing: $filename${NC}"

        image_failed=false
        variants_created=0

        # Generate all breakpoint variants
        for bp in "${!BREAKPOINTS[@]}"; do
            dimensions="${BREAKPOINTS[$bp]}"
            output_file="$OUTPUT_DIR/$bp/${name}.jpg"

            # Skip if exists
            if [ -f "$output_file" ]; then
                continue
            fi

            # Extract width and height
            width="${dimensions%x*}"
            height="${dimensions#*x}"

            # Generate variant with smart crop
            if magick "$input_file" \
                -resize "${width}x${height}^" \
                -gravity center \
                -extent "${width}x${height}" \
                -quality $QUALITY \
                "$output_file" 2>&1; then

                variants_created=$((variants_created + 1))
            else
                echo -e "${RED}  ✗ Failed: $bp${NC}"
                image_failed=true
            fi
        done

        if [ "$image_failed" == "true" ]; then
            FAILED=$((FAILED + 1))
            echo -e "${RED}  ✗ Some variants failed${NC}"
        elif [ $variants_created -eq 0 ]; then
            SKIPPED=$((SKIPPED + 1))
            echo -e "${YELLOW}  ⊘ All variants exist${NC}"
        else
            PROCESSED=$((PROCESSED + 1))
            echo -e "${GREEN}  ✓ Created $variants_created variants${NC}"
        fi
    done
done

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                        Summary                               ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo "  Total images:     $TOTAL"
echo -e "  ${GREEN}Processed:        $PROCESSED${NC}"
echo -e "  ${YELLOW}Skipped (exists): $SKIPPED${NC}"
echo -e "  ${RED}Failed:           $FAILED${NC}"
echo ""

# WordPress/HTML integration guide
if [ $PROCESSED -gt 0 ]; then
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  HTML Integration Guide                      ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Use <picture> with srcset for responsive delivery:"
    echo ""
    echo -e "${YELLOW}<picture>${NC}"
    echo -e "${YELLOW}  <!-- Desktop (1920w and up) -->${NC}"
    echo -e "${YELLOW}  <source media=\"(min-width: 1920px)\"${NC}"
    echo -e "${YELLOW}          srcset=\"/desktop-2x/hero.jpg 2x, /desktop/hero.jpg 1x\">${NC}"
    echo ""
    echo -e "${YELLOW}  <!-- Tablet (768w - 1919w) -->${NC}"
    echo -e "${YELLOW}  <source media=\"(min-width: 768px)\"${NC}"
    echo -e "${YELLOW}          srcset=\"/tablet/hero.jpg\">${NC}"
    echo ""
    echo -e "${YELLOW}  <!-- Mobile (375w - 767w) -->${NC}"
    echo -e "${YELLOW}  <source media=\"(min-width: 375px)\"${NC}"
    echo -e "${YELLOW}          srcset=\"/mobile-2x/hero.jpg 2x, /mobile/hero.jpg 1x\">${NC}"
    echo ""
    echo -e "${YELLOW}  <!-- Small screens (<375w) -->${NC}"
    echo -e "${YELLOW}  <img src=\"/small/hero.jpg\" alt=\"Hero\" loading=\"lazy\">${NC}"
    echo -e "${YELLOW}</picture>${NC}"
    echo ""
    echo "Or use WordPress srcset attribute:"
    echo ""
    echo -e "${YELLOW}wp_get_attachment_image(${NC}"
    echo -e "${YELLOW}  \$attachment_id,${NC}"
    echo -e "${YELLOW}  'full',${NC}"
    echo -e "${YELLOW}  false,${NC}"
    echo -e "${YELLOW}  ['srcset' => 'desktop.jpg 1920w, tablet.jpg 1024w, mobile.jpg 768w']${NC}"
    echo -e "${YELLOW});${NC}"
    echo ""
fi

# Elementor integration note
if [ $PROCESSED -gt 0 ]; then
    echo -e "${CYAN}Elementor Integration:${NC}"
    echo "1. Upload all variants to Media Library"
    echo "2. Use 'Background' widget with custom media queries"
    echo "3. Or use 'Image' widget with srcset attribute"
    echo ""
fi

if [ $PROCESSED -gt 0 ]; then
    echo -e "${GREEN}✓ Generation complete!${NC}"
    echo "  Output: $OUTPUT_DIR"
    echo ""
    echo "Directory structure:"
    for bp in "${!BREAKPOINTS[@]}"; do
        count=$(find "$OUTPUT_DIR/$bp" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "  $OUTPUT_DIR/$bp/ ($count files)"
    done
    exit 0
elif [ $TOTAL -eq 0 ]; then
    echo -e "${YELLOW}⚠ No images found in: $INPUT_DIR${NC}"
    exit 1
else
    echo -e "${RED}✗ No new images processed${NC}"
    exit 1
fi
