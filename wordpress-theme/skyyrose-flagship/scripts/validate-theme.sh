#!/bin/bash

###############################################################################
# Theme Validation Script
#
# Validates WordPress theme requirements and best practices
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Theme directory
THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}WordPress Theme Validation${NC}"
echo -e "${BLUE}========================================${NC}\n"

###############################################################################
# Helper Functions
###############################################################################

pass() {
    echo -e "${GREEN}✓ PASS:${NC} $1"
    ((PASS++))
}

fail() {
    echo -e "${RED}✗ FAIL:${NC} $1"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN:${NC} $1"
    ((WARN++))
}

info() {
    echo -e "${BLUE}ℹ INFO:${NC} $1"
}

###############################################################################
# Required Files Check
###############################################################################

echo -e "\n${BLUE}[1/8] Checking Required Files...${NC}\n"

# Check for required files
required_files=(
    "style.css"
    "index.php"
    "functions.php"
    "screenshot.png"
)

for file in "${required_files[@]}"; do
    if [ -f "$THEME_DIR/$file" ]; then
        pass "Required file exists: $file"
    else
        fail "Missing required file: $file"
    fi
done

# Check for recommended files
recommended_files=(
    "header.php"
    "footer.php"
    "sidebar.php"
    "single.php"
    "page.php"
    "archive.php"
    "search.php"
    "404.php"
)

for file in "${recommended_files[@]}"; do
    if [ -f "$THEME_DIR/$file" ]; then
        pass "Recommended file exists: $file"
    else
        warn "Missing recommended file: $file"
    fi
done

###############################################################################
# Style.css Header Check
###############################################################################

echo -e "\n${BLUE}[2/8] Validating style.css Header...${NC}\n"

if [ -f "$THEME_DIR/style.css" ]; then
    # Check for required header fields
    required_headers=(
        "Theme Name"
        "Description"
        "Author"
        "Version"
        "License"
        "Text Domain"
    )

    for header in "${required_headers[@]}"; do
        if grep -q "$header:" "$THEME_DIR/style.css"; then
            pass "style.css contains: $header"
        else
            fail "style.css missing: $header"
        fi
    done
else
    fail "style.css not found"
fi

###############################################################################
# Template Files Check
###############################################################################

echo -e "\n${BLUE}[3/8] Checking Template Files...${NC}\n"

# Check for WooCommerce templates
if [ -d "$THEME_DIR/woocommerce" ]; then
    pass "WooCommerce template directory exists"

    wc_templates=$(find "$THEME_DIR/woocommerce" -name "*.php" | wc -l)
    info "Found $wc_templates WooCommerce template files"
else
    warn "WooCommerce template directory not found"
fi

# Check for template-parts
if [ -d "$THEME_DIR/template-parts" ]; then
    pass "Template parts directory exists"

    template_parts=$(find "$THEME_DIR/template-parts" -name "*.php" | wc -l)
    info "Found $template_parts template part files"
else
    warn "Template parts directory not found"
fi

###############################################################################
# Functions.php Check
###############################################################################

echo -e "\n${BLUE}[4/8] Validating functions.php...${NC}\n"

if [ -f "$THEME_DIR/functions.php" ]; then
    # Check for theme setup function
    if grep -q "function.*_setup" "$THEME_DIR/functions.php"; then
        pass "Theme setup function found"
    else
        fail "Theme setup function not found"
    fi

    # Check for after_setup_theme hook
    if grep -q "add_action.*'after_setup_theme'" "$THEME_DIR/functions.php"; then
        pass "after_setup_theme hook found"
    else
        fail "after_setup_theme hook not found"
    fi

    # Check for wp_enqueue_scripts
    if grep -q "add_action.*'wp_enqueue_scripts'" "$THEME_DIR/functions.php"; then
        pass "wp_enqueue_scripts hook found"
    else
        fail "wp_enqueue_scripts hook not found"
    fi

    # Check for security - no direct file access
    if grep -q "ABSPATH" "$THEME_DIR/functions.php"; then
        pass "Direct file access protection found"
    else
        warn "No direct file access protection"
    fi
else
    fail "functions.php not found"
fi

###############################################################################
# Security Check
###############################################################################

echo -e "\n${BLUE}[5/8] Checking Security...${NC}\n"

# Check for SQL injection vulnerabilities
if grep -r "\$_GET\|\$_POST\|\$_REQUEST" "$THEME_DIR" --include="*.php" | grep -v "// phpcs:ignore" | grep -qv "wp_unslash\|sanitize_"; then
    warn "Potential unsanitized user input found - verify all inputs are sanitized"
else
    pass "No obvious unsanitized user input"
fi

# Check for proper escaping
php_files=$(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*")

# Check for echo without escaping
if echo "$php_files" | xargs grep -l "echo \$" | grep -qv "esc_"; then
    warn "Found 'echo' statements that may need escaping functions"
else
    pass "Echo statements appear to use proper escaping"
fi

# Check for nonce verification in AJAX handlers
if grep -r "wp_ajax" "$THEME_DIR" --include="*.php" | grep -q "check_ajax_referer\|wp_verify_nonce"; then
    pass "AJAX handlers use nonce verification"
elif grep -r "wp_ajax" "$THEME_DIR" --include="*.php" > /dev/null; then
    warn "AJAX handlers found but nonce verification unclear"
fi

###############################################################################
# WooCommerce Integration Check
###############################################################################

echo -e "\n${BLUE}[6/8] Checking WooCommerce Integration...${NC}\n"

if grep -q "add_theme_support.*'woocommerce'" "$THEME_DIR/functions.php"; then
    pass "WooCommerce support declared"

    # Check for WooCommerce hooks
    if grep -q "woocommerce_" "$THEME_DIR/functions.php"; then
        pass "WooCommerce hooks found"
    fi

    # Check for product gallery features
    if grep -q "wc-product-gallery" "$THEME_DIR/functions.php"; then
        pass "WooCommerce product gallery features enabled"
    else
        warn "WooCommerce product gallery features not found"
    fi
else
    warn "WooCommerce support not declared"
fi

###############################################################################
# Asset Check
###############################################################################

echo -e "\n${BLUE}[7/8] Checking Assets...${NC}\n"

# Check for CSS files
css_files=$(find "$THEME_DIR/assets" -name "*.css" 2>/dev/null | wc -l)
if [ "$css_files" -gt 0 ]; then
    pass "Found $css_files CSS files"
else
    warn "No CSS files found in assets directory"
fi

# Check for JS files
js_files=$(find "$THEME_DIR/assets" -name "*.js" 2>/dev/null | wc -l)
if [ "$js_files" -gt 0 ]; then
    pass "Found $js_files JavaScript files"
else
    warn "No JavaScript files found in assets directory"
fi

# Check for Three.js
if [ -f "$THEME_DIR/assets/three/three.min.js" ] || [ -f "$THEME_DIR/assets/js/three.min.js" ]; then
    pass "Three.js library found"
else
    warn "Three.js library not found"
fi

# Check for 3D models directory
if [ -d "$THEME_DIR/assets/models" ]; then
    pass "3D models directory exists"

    model_files=$(find "$THEME_DIR/assets/models" -name "*.glb" -o -name "*.gltf" 2>/dev/null | wc -l)
    if [ "$model_files" -gt 0 ]; then
        info "Found $model_files 3D model files"
    fi
else
    warn "3D models directory not found"
fi

# Check for optimized images
if command -v identify &> /dev/null; then
    large_images=$(find "$THEME_DIR" -name "*.jpg" -o -name "*.png" 2>/dev/null | xargs identify 2>/dev/null | awk '{if ($3 > 2000 || $4 > 2000) print}' | wc -l)
    if [ "$large_images" -gt 0 ]; then
        warn "Found $large_images images larger than 2000px - consider optimizing"
    else
        pass "All images appear to be reasonably sized"
    fi
fi

###############################################################################
# Code Standards Check
###############################################################################

echo -e "\n${BLUE}[8/8] Checking Code Standards...${NC}\n"

# Check for PHP syntax errors
php_error=0
for file in $(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*"); do
    if ! php -l "$file" > /dev/null 2>&1; then
        fail "PHP syntax error in: $file"
        php_error=1
    fi
done

if [ $php_error -eq 0 ]; then
    pass "No PHP syntax errors found"
fi

# Check for WordPress coding standards (if PHPCS is available)
if command -v phpcs &> /dev/null; then
    if phpcs --standard=WordPress "$THEME_DIR" --extensions=php --ignore=vendor,node_modules > /dev/null 2>&1; then
        pass "WordPress coding standards check passed"
    else
        warn "WordPress coding standards violations found (run phpcs for details)"
    fi
else
    info "PHPCS not installed - skipping coding standards check"
fi

# Check for JavaScript syntax (if eslint is available)
if command -v eslint &> /dev/null; then
    if eslint "$THEME_DIR/assets/js" --quiet 2> /dev/null; then
        pass "JavaScript linting passed"
    else
        warn "JavaScript linting issues found (run eslint for details)"
    fi
else
    info "ESLint not installed - skipping JavaScript linting"
fi

###############################################################################
# Summary
###############################################################################

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${YELLOW}Warnings: $WARN${NC}"
echo -e "${RED}Failed: $FAIL${NC}\n"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Theme validation completed successfully!${NC}\n"
    exit 0
else
    echo -e "${RED}✗ Theme validation failed with $FAIL errors${NC}\n"
    exit 1
fi
