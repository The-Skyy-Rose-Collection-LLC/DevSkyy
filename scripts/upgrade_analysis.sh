#!/bin/bash
###############################################################################
# SkyyRose WordPress Upgrade Analysis
#
# Checks for outdated WordPress, WooCommerce, Elementor, and PHP versions.
# Provides recommendations for safe upgrade paths.
#
# Usage:
#   ./scripts/upgrade_analysis.sh
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-2025"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  SkyyRose WordPress Upgrade Analysis${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

###############################################################################
# 1. THEME VERSION CHECK
###############################################################################

echo -e "${YELLOW}📦 Checking Theme Version...${NC}"

if [ -f "$THEME_DIR/style.css" ]; then
    THEME_VERSION=$(grep "^Version:" "$THEME_DIR/style.css" | awk '{print $2}')
    THEME_NAME=$(grep "^Theme Name:" "$THEME_DIR/style.css" | sed 's/^Theme Name: //')
    REQUIRES_WP=$(grep "^Requires at least:" "$THEME_DIR/style.css" | awk '{print $4}')
    REQUIRES_PHP=$(grep "^Requires PHP:" "$THEME_DIR/style.css" | awk '{print $3}')

    echo -e "  ${GREEN}✓${NC} Theme: $THEME_NAME"
    echo -e "  ${GREEN}✓${NC} Version: $THEME_VERSION"
    echo -e "  ${GREEN}✓${NC} Requires WordPress: $REQUIRES_WP+"
    echo -e "  ${GREEN}✓${NC} Requires PHP: $REQUIRES_PHP+"
else
    echo -e "  ${RED}✗${NC} Theme style.css not found!"
    exit 1
fi

echo ""

###############################################################################
# 2. WORDPRESS VERSION CHECK
###############################################################################

echo -e "${YELLOW}📦 WordPress Version Check...${NC}"

# WordPress latest versions (as of 2026-02)
WP_LATEST_STABLE="6.7.1"
WP_SECURITY_VERSION="6.7.0"

echo -e "  ${BLUE}ℹ${NC} Current Requirement: $REQUIRES_WP+"
echo -e "  ${BLUE}ℹ${NC} Latest Stable: $WP_LATEST_STABLE"
echo -e "  ${BLUE}ℹ${NC} Minimum Security: $WP_SECURITY_VERSION"
echo ""
echo -e "  ${YELLOW}⚠${NC}  Action: Update to WordPress $WP_LATEST_STABLE"
echo -e "      Reason: Security patches, performance improvements"
echo -e "      Risk: Low (minor version update)"

echo ""

###############################################################################
# 3. WOOCOMMERCE VERSION CHECK
###############################################################################

echo -e "${YELLOW}📦 WooCommerce Version Check...${NC}"

# WooCommerce latest versions (as of 2026-02)
WOO_LATEST_STABLE="9.5.2"
WOO_MIN_REQUIRED="8.5.0"

echo -e "  ${BLUE}ℹ${NC} Theme Requires: $WOO_MIN_REQUIRED+"
echo -e "  ${BLUE}ℹ${NC} Latest Stable: $WOO_LATEST_STABLE"
echo ""
echo -e "  ${YELLOW}⚠${NC}  Action: Update to WooCommerce $WOO_LATEST_STABLE"
echo -e "      Reason: PCI compliance, new payment methods, bug fixes"
echo -e "      Risk: Medium (major version update)"
echo -e "      ${RED}CRITICAL:${NC} Test checkout flow on staging first!"

echo ""

###############################################################################
# 4. ELEMENTOR VERSION CHECK
###############################################################################

echo -e "${YELLOW}📦 Elementor Version Check...${NC}"

# Elementor latest versions (as of 2026-02)
ELEMENTOR_LATEST_STABLE="3.25.4"
ELEMENTOR_MIN_REQUIRED="3.18.0"

echo -e "  ${BLUE}ℹ${NC} Theme Requires: $ELEMENTOR_MIN_REQUIRED+"
echo -e "  ${BLUE}ℹ${NC} Latest Stable: $ELEMENTOR_LATEST_STABLE"
echo ""
echo -e "  ${YELLOW}⚠${NC}  Action: Update to Elementor $ELEMENTOR_LATEST_STABLE"
echo -e "      Reason: Widget compatibility, performance, new features"
echo -e "      Risk: Low (minor version update)"
echo -e "      ${YELLOW}NOTE:${NC} Test custom SkyyRose widgets after update"

echo ""

###############################################################################
# 5. PHP VERSION CHECK
###############################################################################

echo -e "${YELLOW}📦 PHP Version Check...${NC}"

PHP_CURRENT=$(php -v 2>/dev/null | head -n 1 | awk '{print $2}' | cut -d'-' -f1 || echo "Not installed")
PHP_LATEST_STABLE="8.3.14"
PHP_MIN_REQUIRED="8.1.0"

echo -e "  ${BLUE}ℹ${NC} Current (Local): $PHP_CURRENT"
echo -e "  ${BLUE}ℹ${NC} Theme Requires: $PHP_MIN_REQUIRED+"
echo -e "  ${BLUE}ℹ${NC} Latest Stable: $PHP_LATEST_STABLE"
echo ""

if [[ "$PHP_CURRENT" == "Not installed" ]]; then
    echo -e "  ${RED}✗${NC} PHP not detected (or not in PATH)"
elif [[ "$PHP_CURRENT" < "8.1" ]]; then
    echo -e "  ${RED}✗${NC} PHP version too old! Minimum: 8.1"
    echo -e "      ${RED}CRITICAL:${NC} Upgrade PHP immediately!"
elif [[ "$PHP_CURRENT" < "8.3" ]]; then
    echo -e "  ${YELLOW}⚠${NC}  Action: Upgrade to PHP $PHP_LATEST_STABLE"
    echo -e "      Reason: Performance (25% faster), security patches"
    echo -e "      Risk: Low (PHP 8.1 → 8.3 is compatible)"
else
    echo -e "  ${GREEN}✓${NC} PHP version is current"
fi

echo ""

###############################################################################
# 6. CDN ASSET CHECK
###############################################################################

echo -e "${YELLOW}🔗 Checking CDN Assets...${NC}"

CDN_URLS=(
    "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"
    "https://cdn.babylonjs.com/babylon.js"
    "https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"
    "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap"
)

CDN_FAILED=0

for url in "${CDN_URLS[@]}"; do
    if curl -s -I "$url" | grep -q "HTTP/[0-9.]\+ 200"; then
        echo -e "  ${GREEN}✓${NC} $url"
    else
        echo -e "  ${RED}✗${NC} $url (FAILED)"
        CDN_FAILED=$((CDN_FAILED + 1))
    fi
done

if [ $CDN_FAILED -gt 0 ]; then
    echo ""
    echo -e "  ${RED}✗${NC} $CDN_FAILED CDN assets unreachable!"
    echo -e "      ${RED}CRITICAL:${NC} 3D scenes will not load!"
else
    echo -e "  ${GREEN}✓${NC} All CDN assets accessible"
fi

echo ""

###############################################################################
# 7. THEME FILE INTEGRITY
###############################################################################

echo -e "${YELLOW}🔧 Checking Theme File Integrity...${NC}"

REQUIRED_FILES=(
    "functions.php"
    "style.css"
    "template-collection.php"
    "page-collection-black-rose.php"
    "page-collection-love-hurts.php"
    "page-collection-signature.php"
    "template-immersive.php"
    "template-vault.php"
    "inc/security-hardening.php"
    "inc/woocommerce-config.php"
    "inc/elementor-widgets.php"
)

MISSING_FILES=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$THEME_DIR/$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo -e "  ${RED}✗${NC} $MISSING_FILES required files missing!"
    echo -e "      ${RED}CRITICAL:${NC} Theme is incomplete!"
else
    echo ""
    echo -e "  ${GREEN}✓${NC} All required files present"
fi

echo ""

###############################################################################
# 8. UPGRADE RECOMMENDATION SUMMARY
###############################################################################

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Upgrade Recommendations${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}Priority: HIGH${NC}"
echo ""
echo -e "1. ${GREEN}WordPress Core${NC}"
echo -e "   Current Requirement: $REQUIRES_WP+"
echo -e "   Latest Stable: $WP_LATEST_STABLE"
echo -e "   Action: Update to $WP_LATEST_STABLE"
echo ""

echo -e "2. ${GREEN}WooCommerce${NC}"
echo -e "   Current Requirement: 8.5+"
echo -e "   Latest Stable: $WOO_LATEST_STABLE"
echo -e "   Action: Update to $WOO_LATEST_STABLE"
echo -e "   ${RED}⚠ CRITICAL: Test checkout on staging first!${NC}"
echo ""

echo -e "3. ${GREEN}Elementor${NC}"
echo -e "   Current Requirement: 3.18+"
echo -e "   Latest Stable: $ELEMENTOR_LATEST_STABLE"
echo -e "   Action: Update to $ELEMENTOR_LATEST_STABLE"
echo -e "   ${YELLOW}⚠ NOTE: Test custom widgets after update${NC}"
echo ""

echo -e "${YELLOW}Priority: MEDIUM${NC}"
echo ""
echo -e "4. ${GREEN}PHP Version${NC}"
echo -e "   Current: $PHP_CURRENT"
echo -e "   Latest Stable: $PHP_LATEST_STABLE"
echo -e "   Action: Upgrade to PHP $PHP_LATEST_STABLE for 25% performance boost"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Safe Update Sequence${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "1. ${GREEN}Backup${NC} database and files"
echo -e "2. ${GREEN}Test on staging${NC} environment first"
echo -e "3. ${GREEN}Update WordPress Core${NC} (lowest risk)"
echo -e "4. ${GREEN}Update WooCommerce${NC} (test checkout flow)"
echo -e "5. ${GREEN}Update Elementor${NC} (test custom widgets)"
echo -e "6. ${GREEN}Update other plugins${NC} one at a time"
echo -e "7. ${GREEN}Verify all pages${NC} load correctly"
echo -e "8. ${GREEN}Monitor error logs${NC} for 48 hours"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Upgrade Analysis Complete${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Exit with error if critical issues found
if [ $MISSING_FILES -gt 0 ] || [ $CDN_FAILED -gt 0 ]; then
    exit 1
fi

exit 0
