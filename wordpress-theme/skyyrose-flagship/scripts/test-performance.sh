#!/bin/bash

###############################################################################
# Performance Testing Script
#
# Runs PageSpeed Insights and Lighthouse tests
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SITE_URL="${1:-http://localhost:8080}"
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/tests/coverage/performance"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Performance Testing${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${BLUE}Testing URL: ${NC}$SITE_URL\n"

# Create output directory
mkdir -p "$OUTPUT_DIR"

###############################################################################
# Helper Functions
###############################################################################

info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

success() {
    echo -e "${GREEN}✓ SUCCESS:${NC} $1"
}

error() {
    echo -e "${RED}✗ ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

###############################################################################
# Check Dependencies
###############################################################################

echo -e "${BLUE}[1/5] Checking dependencies...${NC}\n"

# Check for Lighthouse CLI
if command -v lighthouse &> /dev/null; then
    success "Lighthouse CLI found"
    LIGHTHOUSE_AVAILABLE=true
else
    warn "Lighthouse CLI not found. Install with: npm install -g lighthouse"
    LIGHTHOUSE_AVAILABLE=false
fi

# Check for curl
if command -v curl &> /dev/null; then
    success "curl found"
else
    error "curl not found. Please install curl."
    exit 1
fi

# Check for jq (for JSON parsing)
if command -v jq &> /dev/null; then
    success "jq found"
    JQ_AVAILABLE=true
else
    warn "jq not found. Install for better JSON parsing: brew install jq"
    JQ_AVAILABLE=false
fi

echo ""

###############################################################################
# Test Site Availability
###############################################################################

echo -e "${BLUE}[2/5] Testing site availability...${NC}\n"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")

if [ "$HTTP_CODE" -eq 200 ]; then
    success "Site is accessible (HTTP $HTTP_CODE)"
else
    error "Site returned HTTP $HTTP_CODE"
    exit 1
fi

echo ""

###############################################################################
# Lighthouse Performance Test
###############################################################################

if [ "$LIGHTHOUSE_AVAILABLE" = true ]; then
    echo -e "${BLUE}[3/5] Running Lighthouse tests...${NC}\n"

    # Test pages
    PAGES=(
        "$SITE_URL"
        "$SITE_URL/shop/"
        "$SITE_URL/product/sample-product/"
    )

    for page in "${PAGES[@]}"; do
        page_name=$(echo "$page" | sed 's/[^a-zA-Z0-9]/-/g')
        output_file="$OUTPUT_DIR/lighthouse-$page_name.json"
        html_file="$OUTPUT_DIR/lighthouse-$page_name.html"

        info "Testing: $page"

        # Run Lighthouse
        lighthouse "$page" \
            --output=json \
            --output=html \
            --output-path="$OUTPUT_DIR/lighthouse-$page_name" \
            --chrome-flags="--headless" \
            --quiet 2>/dev/null || true

        if [ -f "$output_file" ]; then
            success "Lighthouse report generated: $html_file"

            # Parse scores if jq is available
            if [ "$JQ_AVAILABLE" = true ]; then
                perf_score=$(jq -r '.categories.performance.score * 100' "$output_file" 2>/dev/null || echo "N/A")
                seo_score=$(jq -r '.categories.seo.score * 100' "$output_file" 2>/dev/null || echo "N/A")
                accessibility_score=$(jq -r '.categories.accessibility.score * 100' "$output_file" 2>/dev/null || echo "N/A")
                best_practices_score=$(jq -r '.categories["best-practices"].score * 100' "$output_file" 2>/dev/null || echo "N/A")

                echo -e "  Performance: $perf_score/100"
                echo -e "  SEO: $seo_score/100"
                echo -e "  Accessibility: $accessibility_score/100"
                echo -e "  Best Practices: $best_practices_score/100"
            fi
        fi

        echo ""
    done
else
    info "Skipping Lighthouse tests (not installed)"
fi

###############################################################################
# Page Load Time Test
###############################################################################

echo -e "${BLUE}[4/5] Testing page load times...${NC}\n"

PAGES=(
    "$SITE_URL"
    "$SITE_URL/shop/"
    "$SITE_URL/cart/"
    "$SITE_URL/checkout/"
)

for page in "${PAGES[@]}"; do
    info "Testing: $page"

    # Get timing information
    timing=$(curl -o /dev/null -s -w "Time Total: %{time_total}s\nTime Connect: %{time_connect}s\nTime Start Transfer: %{time_starttransfer}s\n" "$page")

    echo "$timing"
    echo ""
done

###############################################################################
# Asset Size Check
###############################################################################

echo -e "${BLUE}[5/5] Checking asset sizes...${NC}\n"

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check CSS files
css_total=0
if [ -d "$THEME_DIR/assets/css" ]; then
    while IFS= read -r file; do
        size=$(wc -c < "$file")
        css_total=$((css_total + size))
        size_kb=$((size / 1024))
        echo "  CSS: $(basename "$file") - ${size_kb}KB"
    done < <(find "$THEME_DIR/assets/css" -name "*.css" -not -name "*.min.css")

    css_total_kb=$((css_total / 1024))
    info "Total CSS size: ${css_total_kb}KB"
fi

echo ""

# Check JS files
js_total=0
if [ -d "$THEME_DIR/assets/js" ]; then
    while IFS= read -r file; do
        size=$(wc -c < "$file")
        js_total=$((js_total + size))
        size_kb=$((size / 1024))
        echo "  JS: $(basename "$file") - ${size_kb}KB"
    done < <(find "$THEME_DIR/assets/js" -name "*.js" -not -name "*.min.js")

    js_total_kb=$((js_total / 1024))
    info "Total JS size: ${js_total_kb}KB"
fi

echo ""

# Check image files
image_total=0
if [ -d "$THEME_DIR/assets/images" ]; then
    while IFS= read -r file; do
        size=$(wc -c < "$file")
        image_total=$((image_total + size))
        size_kb=$((size / 1024))

        # Warn about large images
        if [ $size_kb -gt 500 ]; then
            warn "Large image: $(basename "$file") - ${size_kb}KB"
        else
            echo "  Image: $(basename "$file") - ${size_kb}KB"
        fi
    done < <(find "$THEME_DIR/assets/images" -name "*.jpg" -o -name "*.png" -o -name "*.gif" -o -name "*.webp" 2>/dev/null)

    if [ $image_total -gt 0 ]; then
        image_total_mb=$((image_total / 1024 / 1024))
        info "Total image size: ${image_total_mb}MB"
    fi
fi

echo ""

# Check 3D model files
model_total=0
if [ -d "$THEME_DIR/assets/models" ]; then
    while IFS= read -r file; do
        size=$(wc -c < "$file")
        model_total=$((model_total + size))
        size_kb=$((size / 1024))

        # Warn about large models
        if [ $size_kb -gt 5000 ]; then
            warn "Large 3D model: $(basename "$file") - ${size_kb}KB"
        else
            echo "  3D Model: $(basename "$file") - ${size_kb}KB"
        fi
    done < <(find "$THEME_DIR/assets/models" -name "*.glb" -o -name "*.gltf" 2>/dev/null)

    if [ $model_total -gt 0 ]; then
        model_total_mb=$((model_total / 1024 / 1024))
        info "Total 3D model size: ${model_total_mb}MB"
    fi
fi

###############################################################################
# Summary
###############################################################################

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Performance Test Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

success "Performance tests completed"
info "Reports saved to: $OUTPUT_DIR"

if [ "$LIGHTHOUSE_AVAILABLE" = true ]; then
    info "Open HTML reports in your browser:"
    find "$OUTPUT_DIR" -name "*.html" | while read -r file; do
        echo "  file://$file"
    done
fi

echo ""

# Recommendations
echo -e "${BLUE}Recommendations:${NC}\n"
echo "1. Keep CSS under 100KB total"
echo "2. Keep JavaScript under 200KB total"
echo "3. Optimize images to under 500KB each"
echo "4. Keep 3D models under 5MB each"
echo "5. Aim for Lighthouse Performance score > 90"
echo "6. Enable browser caching for static assets"
echo "7. Use lazy loading for images and 3D models"
echo "8. Minify CSS and JavaScript files"
echo "9. Use CDN for static assets"
echo "10. Implement HTTP/2 server push for critical assets"

echo ""
