#!/bin/bash

##
# SkyyRose Flagship Theme Validation Script
#
# Runs comprehensive validation checks for WordPress theme.
#
# @package SkyyRose_Flagship
# @since 2.0.0
##

set -e

echo "================================================"
echo "SkyyRose Flagship Theme Validation"
echo "Version 2.0.0"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        ERRORS=$((ERRORS + 1))
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

echo "Phase 1: Core WordPress Files"
echo "------------------------------"

# Check core files exist
for file in functions.php index.php header.php footer.php style.css page.php single.php archive.php 404.php; do
    if [ -f "$file" ]; then
        print_status 0 "File exists: $file"
    else
        print_status 1 "File missing: $file"
    fi
done

echo ""
echo "Phase 2: Brand CSS System"
echo "-------------------------"

# Check CSS files
CSS_DIR="assets/css"
for file in brand-variables.css luxury-theme.css collection-colors.css custom.css; do
    if [ -f "$CSS_DIR/$file" ]; then
        print_status 0 "CSS file exists: $file"

        # Check for @import statements (excluding comments)
        if grep -v "^\s*/\*" "$CSS_DIR/$file" | grep -v "^\s*\*" | grep -q "@import"; then
            print_status 1 "@import found in $file (WordPress.com incompatible)"
        else
            print_status 0 "No @import in $file (WordPress.com compatible)"
        fi
    else
        print_status 1 "CSS file missing: $file"
    fi
done

# Check enqueue file
if [ -f "inc/enqueue-brand-styles.php" ]; then
    print_status 0 "Enqueue file exists: inc/enqueue-brand-styles.php"
else
    print_status 1 "Enqueue file missing: inc/enqueue-brand-styles.php"
fi

echo ""
echo "Phase 3: PHP Syntax Validation"
echo "-------------------------------"

# Check PHP syntax
SYNTAX_ERRORS=0
while IFS= read -r -d '' file; do
    if ! php -l "$file" > /dev/null 2>&1; then
        print_status 1 "Syntax error in: $file"
        SYNTAX_ERRORS=$((SYNTAX_ERRORS + 1))
    fi
done < <(find . -name "*.php" -type f ! -path "./node_modules/*" ! -path "./vendor/*" ! -path "./.serena/*" -print0)

if [ $SYNTAX_ERRORS -eq 0 ]; then
    print_status 0 "All PHP files pass syntax check"
else
    print_status 1 "Found $SYNTAX_ERRORS PHP syntax errors"
fi

echo ""
echo "Phase 4: WooCommerce Safety"
echo "---------------------------"

# Check WooCommerce guards
if grep -q "class_exists.*WooCommerce" functions.php; then
    print_status 0 "WooCommerce guards found in functions.php"
else
    print_warning "No WooCommerce guards found in functions.php"
fi

# Check for unguarded WC() calls in main files
UNGUARDED_WC=0
for file in functions.php header.php footer.php; do
    if [ -f "$file" ]; then
        if grep -q "WC()" "$file"; then
            # Check up to 20 lines before WC() calls for class_exists guard
            if ! grep -B20 "WC()" "$file" | grep -q "class_exists.*WooCommerce"; then
                print_warning "Potentially unguarded WC() call in $file"
                UNGUARDED_WC=$((UNGUARDED_WC + 1))
            fi
        fi
    fi
done

if [ $UNGUARDED_WC -eq 0 ]; then
    print_status 0 "No unguarded WC() calls in main theme files"
fi

echo ""
echo "Phase 5: WordPress.com Requirements"
echo "------------------------------------"

# Check screenshot
if [ -f "screenshot.png" ]; then
    SCREENSHOT_INFO=$(file screenshot.png)
    if echo "$SCREENSHOT_INFO" | grep -q "1200 x 900"; then
        print_status 0 "Screenshot is 1200x900 (WordPress.com compatible)"
    else
        print_warning "Screenshot dimensions may not be 1200x900"
        echo "   $SCREENSHOT_INFO"
    fi
else
    print_status 1 "screenshot.png missing"
fi

# Check readme.txt
if [ -f "readme.txt" ]; then
    print_status 0 "readme.txt exists"

    # Check version matches
    README_VERSION=$(grep "Stable tag:" readme.txt | awk '{print $3}')
    STYLE_VERSION=$(grep "Version:" style.css | head -1 | awk '{print $2}')

    if [ "$README_VERSION" = "$STYLE_VERSION" ]; then
        print_status 0 "Version matches in readme.txt and style.css ($README_VERSION)"
    else
        print_warning "Version mismatch: readme.txt ($README_VERSION) vs style.css ($STYLE_VERSION)"
    fi
else
    print_status 1 "readme.txt missing"
fi

# Check for backup files
BACKUP_COUNT=$(find . -name "*.backup" -o -name "*.tmp" 2>/dev/null | wc -l)
if [ $BACKUP_COUNT -eq 0 ]; then
    print_status 0 "No backup or temp files found"
else
    print_warning "Found $BACKUP_COUNT backup/temp files that should be cleaned up"
fi

echo ""
echo "Phase 6: Theme Information"
echo "--------------------------"

# Extract theme info
THEME_NAME=$(grep "Theme Name:" style.css | cut -d: -f2 | xargs)
THEME_VERSION=$(grep "Version:" style.css | head -1 | cut -d: -f2 | xargs)
TESTED_UP_TO=$(grep "Tested up to:" style.css | cut -d: -f2 | xargs)
REQUIRES_PHP=$(grep "Requires PHP:" style.css | cut -d: -f2 | xargs)

echo "Theme Name: $THEME_NAME"
echo "Version: $THEME_VERSION"
echo "Tested up to: WordPress $TESTED_UP_TO"
echo "Requires PHP: $REQUIRES_PHP"

echo ""
echo "================================================"
echo "Validation Summary"
echo "================================================"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo ""
    echo "Theme is ready for:"
    echo "  - WordPress Theme Checker plugin"
    echo "  - WordPress.com upload"
    echo "  - Production deployment"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ PASSED WITH $WARNINGS WARNINGS${NC}"
    echo ""
    echo "Theme is functional but has minor issues."
    echo "Review warnings above before deployment."
    exit 0
else
    echo -e "${RED}✗ VALIDATION FAILED${NC}"
    echo ""
    echo "Errors: $ERRORS"
    echo "Warnings: $WARNINGS"
    echo ""
    echo "Please fix errors above before deployment."
    exit 1
fi
