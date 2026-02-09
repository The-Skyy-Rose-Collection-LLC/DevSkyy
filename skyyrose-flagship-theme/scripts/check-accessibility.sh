#!/bin/bash

###############################################################################
# Accessibility Testing Script
#
# Runs axe-core and other accessibility tests
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
OUTPUT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/tests/coverage/accessibility"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Accessibility Testing${NC}"
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

echo -e "${BLUE}[1/6] Checking dependencies...${NC}\n"

# Check for axe-core CLI
if command -v axe &> /dev/null; then
    success "axe-core CLI found"
    AXE_AVAILABLE=true
else
    warn "axe-core CLI not found. Install with: npm install -g @axe-core/cli"
    AXE_AVAILABLE=false
fi

# Check for pa11y
if command -v pa11y &> /dev/null; then
    success "pa11y found"
    PA11Y_AVAILABLE=true
else
    warn "pa11y not found. Install with: npm install -g pa11y"
    PA11Y_AVAILABLE=false
fi

# Check for curl
if command -v curl &> /dev/null; then
    success "curl found"
else
    error "curl not found. Please install curl."
    exit 1
fi

echo ""

###############################################################################
# Test Site Availability
###############################################################################

echo -e "${BLUE}[2/6] Testing site availability...${NC}\n"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")

if [ "$HTTP_CODE" -eq 200 ]; then
    success "Site is accessible (HTTP $HTTP_CODE)"
else
    error "Site returned HTTP $HTTP_CODE"
    exit 1
fi

echo ""

###############################################################################
# Axe-core Accessibility Tests
###############################################################################

if [ "$AXE_AVAILABLE" = true ]; then
    echo -e "${BLUE}[3/6] Running axe-core tests...${NC}\n"

    # Test pages
    PAGES=(
        "$SITE_URL|homepage"
        "$SITE_URL/shop/|shop"
        "$SITE_URL/cart/|cart"
        "$SITE_URL/checkout/|checkout"
    )

    for page_data in "${PAGES[@]}"; do
        IFS='|' read -r page page_name <<< "$page_data"
        output_file="$OUTPUT_DIR/axe-$page_name.json"

        info "Testing: $page"

        # Run axe
        axe "$page" --save "$output_file" --timeout 30000 2>/dev/null || true

        if [ -f "$output_file" ]; then
            # Count violations
            violations=$(grep -c '"impact":' "$output_file" 2>/dev/null || echo "0")

            if [ "$violations" -eq 0 ]; then
                success "No violations found"
            else
                warn "Found $violations accessibility issues"
            fi

            success "Report saved: $output_file"
        fi

        echo ""
    done
else
    info "Skipping axe-core tests (not installed)"
fi

###############################################################################
# Pa11y Accessibility Tests
###############################################################################

if [ "$PA11Y_AVAILABLE" = true ]; then
    echo -e "${BLUE}[4/6] Running pa11y tests...${NC}\n"

    # Test pages
    PAGES=(
        "$SITE_URL|homepage"
        "$SITE_URL/shop/|shop"
        "$SITE_URL/cart/|cart"
        "$SITE_URL/checkout/|checkout"
    )

    for page_data in "${PAGES[@]}"; do
        IFS='|' read -r page page_name <<< "$page_data"
        output_file="$OUTPUT_DIR/pa11y-$page_name.json"

        info "Testing: $page"

        # Run pa11y with WCAG 2.1 AA standard
        pa11y "$page" \
            --reporter json \
            --standard WCAG2AA \
            --timeout 30000 > "$output_file" 2>/dev/null || true

        if [ -f "$output_file" ]; then
            # Count issues
            issues=$(grep -c '"code":' "$output_file" 2>/dev/null || echo "0")

            if [ "$issues" -eq 0 ]; then
                success "No issues found"
            else
                warn "Found $issues accessibility issues"
            fi

            success "Report saved: $output_file"
        fi

        echo ""
    done
else
    info "Skipping pa11y tests (not installed)"
fi

###############################################################################
# Manual Accessibility Checks
###############################################################################

echo -e "${BLUE}[5/6] Manual accessibility checks...${NC}\n"

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check for skip links
info "Checking for skip links..."
if grep -r "skip-link\|skip-to-content" "$THEME_DIR" --include="*.php" > /dev/null; then
    success "Skip links found"
else
    warn "No skip links found - add for keyboard navigation"
fi

# Check for ARIA landmarks
info "Checking for ARIA landmarks..."
landmarks=("main" "nav" "header" "footer" "aside")
for landmark in "${landmarks[@]}"; do
    if grep -r "<$landmark\|role=\"$landmark\"" "$THEME_DIR" --include="*.php" > /dev/null; then
        success "Found <$landmark> landmark"
    else
        warn "Missing <$landmark> landmark"
    fi
done

echo ""

# Check for image alt attributes
info "Checking image alt attributes..."
php_files=$(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*")

# Look for <img without alt
missing_alt=$(echo "$php_files" | xargs grep -n "<img" | grep -v "alt=" | wc -l)
if [ "$missing_alt" -gt 0 ]; then
    warn "Found $missing_alt <img> tags without alt attributes"
else
    success "All <img> tags have alt attributes"
fi

# Check for form labels
info "Checking form labels..."
inputs_without_labels=$(echo "$php_files" | xargs grep -n "<input" | grep -v "type=\"hidden\"" | grep -v -E "id=|aria-label" | wc -l)
if [ "$inputs_without_labels" -gt 0 ]; then
    warn "Found $inputs_without_labels input fields that may be missing labels"
else
    success "All input fields appear to have labels"
fi

# Check for heading hierarchy
info "Checking heading hierarchy..."
if echo "$php_files" | xargs grep -E "<h[1-6]" > /dev/null; then
    success "Heading tags found"

    # Check if H1 exists
    if echo "$php_files" | xargs grep "<h1" > /dev/null; then
        success "H1 heading found"
    else
        warn "No H1 heading found"
    fi
else
    warn "No heading tags found"
fi

echo ""

# Check for color contrast in CSS
info "Checking CSS for color values..."
if [ -d "$THEME_DIR/assets/css" ]; then
    css_files=$(find "$THEME_DIR/assets/css" -name "*.css")
    if [ -n "$css_files" ]; then
        warn "Manual check required: Verify color contrast ratios meet WCAG 2.1 AA (4.5:1)"
        echo "  Use tools like:"
        echo "  - WebAIM Contrast Checker: https://webaim.org/resources/contrastchecker/"
        echo "  - Chrome DevTools: Inspect > Accessibility panel"
    fi
fi

echo ""

# Check for focus indicators
info "Checking for focus indicators..."
if [ -d "$THEME_DIR/assets/css" ]; then
    if grep -r ":focus" "$THEME_DIR/assets/css" --include="*.css" > /dev/null; then
        success "Focus styles found in CSS"
    else
        warn "No focus styles found - add :focus styles for keyboard navigation"
    fi
fi

# Check for keyboard event handlers
info "Checking JavaScript event handlers..."
if [ -d "$THEME_DIR/assets/js" ]; then
    if grep -r "addEventListener.*'click'" "$THEME_DIR/assets/js" --include="*.js" > /dev/null; then
        if grep -r "addEventListener.*'keypress'\|addEventListener.*'keydown'" "$THEME_DIR/assets/js" --include="*.js" > /dev/null; then
            success "Keyboard event handlers found alongside click handlers"
        else
            warn "Click handlers found but no keyboard equivalents - ensure keyboard accessibility"
        fi
    fi
fi

echo ""

###############################################################################
# WCAG 2.1 Checklist
###############################################################################

echo -e "${BLUE}[6/6] WCAG 2.1 AA Compliance Checklist${NC}\n"

info "Manual verification required for:"
echo ""
echo "Perceivable:"
echo "  ☐ All images have descriptive alt text"
echo "  ☐ Videos have captions and transcripts"
echo "  ☐ Color is not the only means of conveying information"
echo "  ☐ Text can be resized up to 200% without loss of content"
echo "  ☐ Color contrast ratio is at least 4.5:1 (text) or 3:1 (large text)"
echo ""
echo "Operable:"
echo "  ☐ All functionality is keyboard accessible"
echo "  ☐ No keyboard traps exist"
echo "  ☐ Skip navigation links are provided"
echo "  ☐ Page titles are descriptive and unique"
echo "  ☐ Focus order is logical"
echo "  ☐ Link purpose is clear from link text or context"
echo "  ☐ Multiple ways to navigate (menu, search, sitemap)"
echo "  ☐ Focus indicator is visible"
echo ""
echo "Understandable:"
echo "  ☐ Page language is identified"
echo "  ☐ Navigation is consistent across pages"
echo "  ☐ Form labels and instructions are provided"
echo "  ☐ Error messages are clear and helpful"
echo "  ☐ Error prevention for important actions"
echo ""
echo "Robust:"
echo "  ☐ HTML is valid"
echo "  ☐ Name, Role, Value can be programmatically determined"
echo "  ☐ Status messages can be programmatically determined"
echo ""

###############################################################################
# Summary
###############################################################################

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Accessibility Test Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

success "Accessibility tests completed"
info "Reports saved to: $OUTPUT_DIR"

echo ""
echo -e "${BLUE}Next Steps:${NC}\n"
echo "1. Review automated test reports in: $OUTPUT_DIR"
echo "2. Complete manual WCAG 2.1 AA checklist above"
echo "3. Test with screen readers (NVDA, JAWS, VoiceOver)"
echo "4. Test keyboard navigation throughout site"
echo "5. Verify color contrast with tools"
echo "6. Test with browser zoom at 200%"
echo "7. Test with assistive technologies"

echo ""
echo -e "${BLUE}Recommended Tools:${NC}\n"
echo "- WAVE Browser Extension: https://wave.webaim.org/extension/"
echo "- axe DevTools: https://www.deque.com/axe/devtools/"
echo "- Accessibility Insights: https://accessibilityinsights.io/"
echo "- Color Contrast Analyzer: https://www.tpgi.com/color-contrast-checker/"

echo ""
