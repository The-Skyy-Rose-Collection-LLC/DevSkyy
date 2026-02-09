#!/bin/bash

###############################################################################
# Master Test Runner Script
#
# Runs all tests and validation checks for the theme
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SITE_URL="${1:-http://localhost:8080}"
THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORTS_DIR="$THEME_DIR/tests/coverage"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TOTAL_TESTS=0

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║        SkyyRose Flagship Theme - Test Suite Runner           ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}Theme Directory:${NC} $THEME_DIR"
echo -e "${CYAN}Site URL:${NC} $SITE_URL"
echo -e "${CYAN}Reports Directory:${NC} $REPORTS_DIR"
echo -e "${CYAN}Timestamp:${NC} $TIMESTAMP\n"

# Create reports directory
mkdir -p "$REPORTS_DIR"

###############################################################################
# Helper Functions
###############################################################################

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

error() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

section() {
    echo ""
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${MAGENTA} $1${NC}"
    echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

subsection() {
    echo ""
    echo -e "${CYAN}─── $1 ───${NC}"
    echo ""
}

run_test() {
    local test_name="$1"
    local test_command="$2"

    ((TOTAL_TESTS++))

    info "Running: $test_name"

    if eval "$test_command" > /dev/null 2>&1; then
        success "$test_name passed"
        return 0
    else
        error "$test_name failed"
        return 1
    fi
}

###############################################################################
# Pre-flight Checks
###############################################################################

section "PRE-FLIGHT CHECKS"

# Check if we're in the theme directory
if [ ! -f "$THEME_DIR/style.css" ]; then
    error "Not in theme directory or style.css not found"
    exit 1
fi
success "Theme directory verified"

# Check for required tools
command -v php >/dev/null 2>&1 && success "PHP found" || warn "PHP not found"
command -v node >/dev/null 2>&1 && success "Node.js found" || warn "Node.js not found"
command -v npm >/dev/null 2>&1 && success "npm found" || warn "npm not found"
command -v composer >/dev/null 2>&1 && success "Composer found" || warn "Composer not found"

# Check if site is accessible
if curl -f -s "$SITE_URL" > /dev/null 2>&1; then
    success "Site is accessible at $SITE_URL"
else
    warn "Site not accessible at $SITE_URL (some tests will be skipped)"
fi

###############################################################################
# 1. Theme Validation
###############################################################################

section "1. THEME VALIDATION"

if [ -x "$THEME_DIR/scripts/validate-theme.sh" ]; then
    if "$THEME_DIR/scripts/validate-theme.sh"; then
        success "Theme validation passed"
    else
        error "Theme validation failed"
    fi
else
    warn "validate-theme.sh not found or not executable"
fi

###############################################################################
# 2. PHP Tests
###############################################################################

section "2. PHP UNIT TESTS"

if [ -f "$THEME_DIR/vendor/bin/phpunit" ]; then
    subsection "Running PHPUnit Tests"

    cd "$THEME_DIR"

    if ./vendor/bin/phpunit --testdox 2>&1 | tee "$REPORTS_DIR/phpunit-output-$TIMESTAMP.txt"; then
        success "PHPUnit tests passed"
    else
        error "PHPUnit tests failed"
    fi

    # Generate coverage report
    if ./vendor/bin/phpunit --coverage-html "$REPORTS_DIR/php" > /dev/null 2>&1; then
        success "PHP coverage report generated"
        info "View at: file://$REPORTS_DIR/php/index.html"
    fi
else
    warn "PHPUnit not installed (run: composer install)"
fi

###############################################################################
# 3. JavaScript Tests
###############################################################################

section "3. JAVASCRIPT TESTS"

if [ -f "$THEME_DIR/node_modules/.bin/jest" ]; then
    subsection "Running Jest Tests"

    cd "$THEME_DIR"

    if npm run test:js -- --coverage 2>&1 | tee "$REPORTS_DIR/jest-output-$TIMESTAMP.txt"; then
        success "Jest tests passed"
    else
        error "Jest tests failed"
    fi

    if [ -d "$REPORTS_DIR/js" ]; then
        success "JavaScript coverage report generated"
        info "View at: file://$REPORTS_DIR/js/index.html"
    fi
else
    warn "Jest not installed (run: npm install)"
fi

###############################################################################
# 4. End-to-End Tests
###############################################################################

section "4. END-TO-END TESTS"

if [ -f "$THEME_DIR/node_modules/.bin/playwright" ]; then
    subsection "Running Playwright Tests"

    cd "$THEME_DIR"

    if npm run test:e2e 2>&1 | tee "$REPORTS_DIR/e2e-output-$TIMESTAMP.txt"; then
        success "E2E tests passed"
    else
        error "E2E tests failed"
    fi

    if [ -d "$REPORTS_DIR/e2e-report" ]; then
        success "E2E report generated"
        info "View with: npx playwright show-report $REPORTS_DIR/e2e-report"
    fi
else
    warn "Playwright not installed (run: npm install)"
fi

###############################################################################
# 5. Performance Testing
###############################################################################

section "5. PERFORMANCE TESTING"

if [ -x "$THEME_DIR/scripts/test-performance.sh" ]; then
    subsection "Running Performance Tests"

    if "$THEME_DIR/scripts/test-performance.sh" "$SITE_URL" 2>&1 | tee "$REPORTS_DIR/performance-$TIMESTAMP.txt"; then
        success "Performance tests completed"
    else
        warn "Performance tests had issues"
    fi
else
    warn "test-performance.sh not found or not executable"
fi

###############################################################################
# 6. Accessibility Testing
###############################################################################

section "6. ACCESSIBILITY TESTING"

if [ -x "$THEME_DIR/scripts/check-accessibility.sh" ]; then
    subsection "Running Accessibility Tests"

    if "$THEME_DIR/scripts/check-accessibility.sh" "$SITE_URL" 2>&1 | tee "$REPORTS_DIR/accessibility-$TIMESTAMP.txt"; then
        success "Accessibility tests completed"
    else
        warn "Accessibility tests had issues"
    fi
else
    warn "check-accessibility.sh not found or not executable"
fi

###############################################################################
# 7. Browser Compatibility Testing
###############################################################################

section "7. BROWSER COMPATIBILITY"

if [ -x "$THEME_DIR/scripts/test-browsers.sh" ]; then
    subsection "Running Browser Tests"

    if "$THEME_DIR/scripts/test-browsers.sh" "$SITE_URL" 2>&1 | tee "$REPORTS_DIR/browsers-$TIMESTAMP.txt"; then
        success "Browser tests completed"
    else
        warn "Browser tests had issues"
    fi
else
    warn "test-browsers.sh not found or not executable"
fi

###############################################################################
# 8. 3D Asset Validation
###############################################################################

section "8. 3D ASSET VALIDATION"

if [ -x "$THEME_DIR/scripts/validate-3d.sh" ]; then
    subsection "Validating 3D Assets"

    if "$THEME_DIR/scripts/validate-3d.sh" 2>&1 | tee "$REPORTS_DIR/3d-validation-$TIMESTAMP.txt"; then
        success "3D validation completed"
    else
        warn "3D validation had issues"
    fi
else
    warn "validate-3d.sh not found or not executable"
fi

###############################################################################
# 9. Code Quality
###############################################################################

section "9. CODE QUALITY"

subsection "PHP Code Standards"

if command -v phpcs >/dev/null 2>&1; then
    if phpcs --standard=WordPress --extensions=php --ignore=vendor,node_modules "$THEME_DIR" > "$REPORTS_DIR/phpcs-$TIMESTAMP.txt" 2>&1; then
        success "PHP code standards check passed"
    else
        warn "PHP code standards issues found"
        info "View report: $REPORTS_DIR/phpcs-$TIMESTAMP.txt"
    fi
else
    warn "PHPCS not installed"
fi

subsection "JavaScript Linting"

if [ -f "$THEME_DIR/node_modules/.bin/eslint" ]; then
    if npm run lint:js > "$REPORTS_DIR/eslint-$TIMESTAMP.txt" 2>&1; then
        success "JavaScript linting passed"
    else
        warn "JavaScript linting issues found"
        info "View report: $REPORTS_DIR/eslint-$TIMESTAMP.txt"
    fi
else
    warn "ESLint not installed"
fi

###############################################################################
# 10. Security Scan
###############################################################################

section "10. SECURITY SCAN"

subsection "Basic Security Checks"

# Check for common security issues
security_issues=0

# Check for debug mode
if grep -r "define.*WP_DEBUG.*true" "$THEME_DIR" --include="*.php" > /dev/null 2>&1; then
    warn "WP_DEBUG found set to true"
    ((security_issues++))
fi

# Check for exposed credentials
if grep -r "password\|api_key\|secret" "$THEME_DIR" --include="*.php" --include="*.js" | grep -v "password_hash\|check_admin_referer" | grep -v "^\s*\*" | grep -v "^\s*//" > /dev/null 2>&1; then
    warn "Potential exposed credentials found"
    ((security_issues++))
fi

# Check file permissions
if find "$THEME_DIR" -name "*.php" -perm 0777 2>/dev/null | grep -q .; then
    warn "Files with 777 permissions found"
    ((security_issues++))
fi

if [ $security_issues -eq 0 ]; then
    success "Basic security checks passed"
else
    warn "Found $security_issues security concerns"
fi

###############################################################################
# Summary Report
###############################################################################

section "TEST SUMMARY"

echo -e "${CYAN}┌────────────────────────────────────────┐${NC}"
echo -e "${CYAN}│${NC}  Test Suite Execution Summary         ${CYAN}│${NC}"
echo -e "${CYAN}├────────────────────────────────────────┤${NC}"
printf "${CYAN}│${NC}  %-20s %15s ${CYAN}│${NC}\n" "Total Tests:" "$TOTAL_TESTS"
printf "${CYAN}│${NC}  ${GREEN}%-20s %15s${NC} ${CYAN}│${NC}\n" "Passed:" "$TESTS_PASSED"
printf "${CYAN}│${NC}  ${RED}%-20s %15s${NC} ${CYAN}│${NC}\n" "Failed:" "$TESTS_FAILED"
echo -e "${CYAN}└────────────────────────────────────────┘${NC}"

echo ""

# Calculate pass rate
if [ $TOTAL_TESTS -gt 0 ]; then
    pass_rate=$((TESTS_PASSED * 100 / TOTAL_TESTS))
    echo -e "Pass Rate: ${CYAN}$pass_rate%${NC}"
fi

echo ""
echo -e "${CYAN}Reports saved to:${NC} $REPORTS_DIR"
echo ""

# List generated reports
if ls "$REPORTS_DIR"/*-$TIMESTAMP.txt >/dev/null 2>&1; then
    echo -e "${CYAN}Generated Reports:${NC}"
    for report in "$REPORTS_DIR"/*-$TIMESTAMP.txt; do
        echo "  - $(basename "$report")"
    done
    echo ""
fi

# Coverage reports
echo -e "${CYAN}Coverage Reports:${NC}"
[ -d "$REPORTS_DIR/php" ] && echo "  - PHP: file://$REPORTS_DIR/php/index.html"
[ -d "$REPORTS_DIR/js" ] && echo "  - JavaScript: file://$REPORTS_DIR/js/index.html"
[ -d "$REPORTS_DIR/e2e-report" ] && echo "  - E2E: npx playwright show-report $REPORTS_DIR/e2e-report"
echo ""

###############################################################################
# Exit Status
###############################################################################

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}                  ALL TESTS PASSED! ✓                          ${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}              SOME TESTS FAILED - SEE ABOVE ✗                   ${NC}"
    echo -e "${RED}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    exit 1
fi
