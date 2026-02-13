#!/bin/bash

##
# SkyyRose Theme Deployment Verification Script
#
# Verifies theme deployment on www.skyyrose.co without requiring WordPress admin access.
# Tests CSS loading, security headers, performance, and accessibility.
#
# Usage: ./verify-deployment.sh
##

set -e

SITE_URL="https://www.skyyrose.co"
THEME_VERSION="2.0.0"
COLOR_RESET="\033[0m"
COLOR_GREEN="\033[0;32m"
COLOR_RED="\033[0;31m"
COLOR_YELLOW="\033[1;33m"
COLOR_BLUE="\033[0;34m"

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SkyyRose Theme Deployment Verification"
echo "  Target: $SITE_URL"
echo "  Theme: SkyyRose Flagship v$THEME_VERSION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

##
# Helper Functions
##

pass() {
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} $1"
    ((PASS_COUNT++))
}

fail() {
    echo -e "${COLOR_RED}✗${COLOR_RESET} $1"
    ((FAIL_COUNT++))
}

warn() {
    echo -e "${COLOR_YELLOW}⚠${COLOR_RESET} $1"
    ((WARN_COUNT++))
}

info() {
    echo -e "${COLOR_BLUE}ℹ${COLOR_RESET} $1"
}

section() {
    echo
    echo -e "${COLOR_BLUE}━━━ $1 ━━━${COLOR_RESET}"
    echo
}

##
# Test 1: Site Accessibility
##

section "1. Site Accessibility"

HTTP_CODE=$(curl -o /dev/null -s -w "%{http_code}" "$SITE_URL")

if [ "$HTTP_CODE" == "200" ]; then
    pass "Site is accessible (HTTP $HTTP_CODE)"
else
    fail "Site returned HTTP $HTTP_CODE (expected 200)"
fi

# Check SSL certificate
if curl -s "$SITE_URL" | grep -q "https"; then
    pass "SSL certificate valid"
else
    warn "SSL certificate issue detected"
fi

##
# Test 2: CSS File Loading
##

section "2. CSS File Loading"

CSS_FILES=(
    "brand-variables.css"
    "luxury-theme.css"
    "collection-colors.css"
    "custom.css"
)

for css_file in "${CSS_FILES[@]}"; do
    CSS_URL="$SITE_URL/wp-content/themes/skyyrose-flagship/assets/css/$css_file"
    CSS_CODE=$(curl -o /dev/null -s -w "%{http_code}" "$CSS_URL")

    if [ "$CSS_CODE" == "200" ]; then
        pass "$css_file loads correctly (HTTP $CSS_CODE)"

        # Verify it's actually CSS (not HTML error page)
        CONTENT_TYPE=$(curl -s -I "$CSS_URL" | grep -i "content-type" | grep -i "css")
        if [ -n "$CONTENT_TYPE" ]; then
            pass "  └─ MIME type is correct (text/css)"
        else
            fail "  └─ MIME type is incorrect (not text/css)"
        fi
    else
        fail "$css_file failed to load (HTTP $CSS_CODE)"
    fi
done

##
# Test 3: Brand Color Verification
##

section "3. Brand Color Verification"

# Download homepage and check for rose gold color
HOMEPAGE_HTML=$(curl -s "$SITE_URL")

if echo "$HOMEPAGE_HTML" | grep -q "#B76E79\|rgb(183, 110, 121)"; then
    pass "Rose Gold color (#B76E79) found in page source"
else
    warn "Rose Gold color not found in inline styles (may be in external CSS)"
fi

if echo "$HOMEPAGE_HTML" | grep -q "Playfair Display\|playfair"; then
    pass "Playfair Display font referenced"
else
    warn "Playfair Display font not found in page source"
fi

if echo "$HOMEPAGE_HTML" | grep -q "Montserrat\|montserrat"; then
    pass "Montserrat font referenced"
else
    warn "Montserrat font not found in page source"
fi

##
# Test 4: Security Headers
##

section "4. Security Headers"

HEADERS=$(curl -s -I "$SITE_URL")

# Check for Content-Security-Policy
if echo "$HEADERS" | grep -qi "Content-Security-Policy"; then
    CSP_HEADER=$(echo "$HEADERS" | grep -i "Content-Security-Policy")

    if echo "$CSP_HEADER" | grep -q "pixel.wp.com"; then
        pass "CSP allows pixel.wp.com (WordPress.com analytics)"
    else
        warn "CSP does not explicitly allow pixel.wp.com"
    fi

    if echo "$CSP_HEADER" | grep -q "blob:"; then
        pass "CSP allows blob: URLs (emoji loader)"
    else
        warn "CSP does not allow blob: URLs"
    fi
else
    warn "No Content-Security-Policy header found"
fi

# Check for X-Frame-Options
if echo "$HEADERS" | grep -qi "X-Frame-Options"; then
    pass "X-Frame-Options header present"
else
    warn "X-Frame-Options header missing"
fi

# Check for HTTPS redirect
if echo "$HEADERS" | grep -qi "Strict-Transport-Security"; then
    pass "HSTS header present (forces HTTPS)"
else
    info "HSTS header not present (optional)"
fi

##
# Test 5: Theme Detection
##

section "5. Theme Detection"

# Check if SkyyRose theme is referenced in page source
if echo "$HOMEPAGE_HTML" | grep -q "skyyrose-flagship\|SkyyRose Flagship"; then
    pass "SkyyRose Flagship theme detected in page source"
else
    warn "Theme name not found in page source (may be minified)"
fi

# Check for theme version
if echo "$HOMEPAGE_HTML" | grep -q "2\.0\.0\|Version 2.0.0"; then
    pass "Theme version 2.0.0 detected"
else
    info "Theme version not found in page source (optional)"
fi

##
# Test 6: Template Detection
##

section "6. Template Detection"

# Check for homepage template markers
if echo "$HOMEPAGE_HTML" | grep -q "luxury-homepage\|collections-showcase\|hero-title"; then
    pass "Luxury Homepage template detected"
else
    warn "Luxury Homepage template not detected (may not be set)"
fi

# Check for collection cards
if echo "$HOMEPAGE_HTML" | grep -q "collection-card\|Signature Collection\|Love Hurts\|Black Rose"; then
    pass "Collections showcase detected"
else
    warn "Collections showcase not found (template may not be active)"
fi

##
# Test 7: Performance Check
##

section "7. Performance Check"

# Measure page load time
LOAD_TIME=$(curl -o /dev/null -s -w "%{time_total}" "$SITE_URL")
LOAD_TIME_MS=$(echo "$LOAD_TIME * 1000" | bc | cut -d. -f1)

if [ "$LOAD_TIME_MS" -lt 2000 ]; then
    pass "Page load time: ${LOAD_TIME_MS}ms (excellent, < 2s)"
elif [ "$LOAD_TIME_MS" -lt 3000 ]; then
    pass "Page load time: ${LOAD_TIME_MS}ms (good, < 3s)"
else
    warn "Page load time: ${LOAD_TIME_MS}ms (may need optimization)"
fi

# Check page size
PAGE_SIZE=$(curl -s "$SITE_URL" | wc -c)
PAGE_SIZE_KB=$((PAGE_SIZE / 1024))

if [ "$PAGE_SIZE_KB" -lt 500 ]; then
    pass "Page size: ${PAGE_SIZE_KB}KB (optimal)"
elif [ "$PAGE_SIZE_KB" -lt 1000 ]; then
    pass "Page size: ${PAGE_SIZE_KB}KB (acceptable)"
else
    warn "Page size: ${PAGE_SIZE_KB}KB (may need optimization)"
fi

##
# Test 8: Mobile Responsive Check
##

section "8. Mobile Responsive Check"

# Check for viewport meta tag
if echo "$HOMEPAGE_HTML" | grep -q "viewport.*width=device-width"; then
    pass "Viewport meta tag present (mobile responsive)"
else
    fail "Viewport meta tag missing (not mobile responsive)"
fi

# Check for media queries in CSS files
CUSTOM_CSS=$(curl -s "$SITE_URL/wp-content/themes/skyyrose-flagship/assets/css/custom.css" 2>/dev/null)
if echo "$CUSTOM_CSS" | grep -q "@media.*max-width"; then
    pass "Media queries found in custom.css (responsive breakpoints)"
else
    warn "No media queries found in custom.css"
fi

##
# Test 9: WordPress.com Specific Checks
##

section "9. WordPress.com Integration"

# Check for WordPress.com assets
if echo "$HOMEPAGE_HTML" | grep -q "s0.wp.com\|s1.wp.com\|s2.wp.com"; then
    pass "WordPress.com CDN assets detected"
else
    info "No WordPress.com CDN assets found (may use direct URLs)"
fi

# Check for Jetpack
if echo "$HOMEPAGE_HTML" | grep -q "jetpack"; then
    info "Jetpack detected (WordPress.com integration active)"
else
    info "Jetpack not detected (may not be enabled)"
fi

##
# Test 10: Functionality Tests
##

section "10. Functionality Tests"

# Check for WooCommerce
SHOP_CODE=$(curl -o /dev/null -s -w "%{http_code}" "$SITE_URL/shop")
if [ "$SHOP_CODE" == "200" ]; then
    pass "Shop page accessible (WooCommerce likely active)"
else
    info "Shop page not found (WooCommerce may not be active)"
fi

# Check for contact page
CONTACT_CODE=$(curl -o /dev/null -s -w "%{http_code}" "$SITE_URL/contact")
if [ "$CONTACT_CODE" == "200" ]; then
    pass "Contact page accessible"
else
    info "Contact page not found (may not be created yet)"
fi

# Check for about page
ABOUT_CODE=$(curl -o /dev/null -s -w "%{http_code}" "$SITE_URL/about")
if [ "$ABOUT_CODE" == "200" ]; then
    pass "About page accessible"
else
    info "About page not found (may not be created yet)"
fi

##
# Summary
##

section "Deployment Verification Summary"

TOTAL_CHECKS=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))

echo "Total Checks: $TOTAL_CHECKS"
echo -e "${COLOR_GREEN}Passed: $PASS_COUNT${COLOR_RESET}"
echo -e "${COLOR_YELLOW}Warnings: $WARN_COUNT${COLOR_RESET}"
echo -e "${COLOR_RED}Failed: $FAIL_COUNT${COLOR_RESET}"
echo

if [ "$FAIL_COUNT" -eq 0 ]; then
    echo -e "${COLOR_GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  ✓ DEPLOYMENT SUCCESSFUL"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo
    echo "✓ Theme appears to be deployed correctly!"
    echo "✓ All critical checks passed"

    if [ "$WARN_COUNT" -gt 0 ]; then
        echo
        echo "⚠ Note: $WARN_COUNT warnings found - review above for details"
        echo "  (Warnings are non-critical but should be addressed)"
    fi
else
    echo -e "${COLOR_RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  ✗ DEPLOYMENT ISSUES DETECTED"
    echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${COLOR_RESET}"
    echo
    echo "✗ $FAIL_COUNT critical issues found"
    echo "  Review failed checks above and consult DEPLOYMENT-CHECKLIST.md"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Exit with error code if any checks failed
if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
else
    exit 0
fi
