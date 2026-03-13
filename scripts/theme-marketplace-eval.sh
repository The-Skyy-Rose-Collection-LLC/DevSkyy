#!/usr/bin/env bash
# scripts/theme-marketplace-eval.sh -- Marketplace readiness evaluation for WordPress theme
#
# Evaluates the SkyyRose Flagship theme against WordPress.org and ThemeForest
# submission requirements. Produces a scored report with pass/fail on each criterion.
#
# Usage:
#   bash scripts/theme-marketplace-eval.sh                # Full evaluation
#   bash scripts/theme-marketplace-eval.sh --wporg        # WordPress.org standards only
#   bash scripts/theme-marketplace-eval.sh --themeforest  # ThemeForest standards only
#   bash scripts/theme-marketplace-eval.sh --security     # Security checks only
#   bash scripts/theme-marketplace-eval.sh --score        # Print score only
#   bash scripts/theme-marketplace-eval.sh --fix          # Auto-fix what's possible
#   bash scripts/theme-marketplace-eval.sh --report       # Save report to file
#   bash scripts/theme-marketplace-eval.sh --help         # Show help
#
# Standards checked:
#   WordPress.org Theme Review: https://make.wordpress.org/themes/handbook/review/
#   ThemeForest Quality Standards: Envato quality + WordPress coding standards
#
# Requirements:
#   - PHP 8.0+
#   - Theme at wordpress-theme/skyyrose-flagship/

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
REPORT_DIR="$THEME_DIR/test-results"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
TOTAL_CHECKS=0
PASSED=0
WARNED=0
FAILED=0
SCORE=0

check_pass() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    PASSED=$((PASSED + 1))
    echo -e "  ${GREEN}✓${NC} $1"
}

check_warn() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    WARNED=$((WARNED + 1))
    echo -e "  ${YELLOW}△${NC} $1"
}

check_fail() {
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    FAILED=$((FAILED + 1))
    echo -e "  ${RED}✗${NC} $1"
}

log_step() { echo -e "\n${CYAN}${BOLD}══════ $1 ══════${NC}"; }

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
MODE="full"
AUTO_FIX=false
SAVE_REPORT=false

usage() {
    cat <<EOF
${BOLD}SkyyRose Theme — Marketplace Evaluation${NC}

Evaluates theme against WordPress.org and ThemeForest submission standards.

Usage: theme-marketplace-eval.sh [OPTIONS]

Options:
  --wporg        WordPress.org Theme Review standards
  --themeforest  ThemeForest/Envato quality standards
  --security     Security-focused checks only
  --score        Print final score only (machine-readable)
  --fix          Auto-fix issues where possible
  --report       Save detailed report to test-results/
  --help         Show this help

Scoring:
  90-100%  READY for submission
  75-89%   ALMOST READY — minor fixes needed
  50-74%   NEEDS WORK — significant issues
  <50%     NOT READY — major overhaul needed
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --wporg)       MODE="wporg"; shift ;;
            --themeforest) MODE="themeforest"; shift ;;
            --security)    MODE="security"; shift ;;
            --score)       MODE="score"; shift ;;
            --fix)         AUTO_FIX=true; shift ;;
            --report)      SAVE_REPORT=true; shift ;;
            --help|-h)     usage; exit 0 ;;
            *)             echo "Unknown: $1"; usage; exit 1 ;;
        esac
    done
}

# ===========================================================================
# SECTION 1: Required Files (WordPress.org mandatory)
# ===========================================================================
check_required_files() {
    log_step "1. Required Files"

    # Absolutely required
    local required_files=(
        "style.css:Theme stylesheet with header"
        "functions.php:Theme functions"
        "index.php:Main template fallback"
        "screenshot.png:Theme screenshot (1200×900)"
    )

    for entry in "${required_files[@]}"; do
        IFS=':' read -r file desc <<< "$entry"
        if [[ -f "$THEME_DIR/$file" ]]; then
            check_pass "$file — $desc"
        else
            check_fail "$file — MISSING ($desc)"
        fi
    done

    # Recommended files
    local recommended_files=(
        "header.php:Site header template"
        "footer.php:Site footer template"
        "sidebar.php:Sidebar template"
        "404.php:404 error page"
        "search.php:Search results template"
        "page.php:Static page template"
        "single.php:Single post template"
        "archive.php:Archive template"
        "comments.php:Comments template"
        "readme.txt:Theme documentation"
    )

    for entry in "${recommended_files[@]}"; do
        IFS=':' read -r file desc <<< "$entry"
        if [[ -f "$THEME_DIR/$file" ]]; then
            check_pass "$file — $desc"
        else
            check_warn "$file — missing ($desc) [recommended]"
        fi
    done
}

# ===========================================================================
# SECTION 2: style.css Theme Header
# ===========================================================================
check_theme_header() {
    log_step "2. Theme Header (style.css)"

    local style="$THEME_DIR/style.css"
    if [[ ! -f "$style" ]]; then
        check_fail "style.css not found"
        return
    fi

    local required_headers=(
        "Theme Name"
        "Author"
        "Description"
        "Version"
        "License"
        "License URI"
        "Text Domain"
    )

    for header in "${required_headers[@]}"; do
        if grep -qi "^[[:space:]]*${header}:" "$style" 2>/dev/null; then
            local value
            value=$(grep -i "^[[:space:]]*${header}:" "$style" | head -1 | sed "s/.*${header}:[[:space:]]*//" | tr -d '\r')
            check_pass "${header}: ${value}"
        else
            check_fail "${header} — MISSING from style.css header"
        fi
    done

    # Recommended headers
    local optional_headers=(
        "Theme URI"
        "Author URI"
        "Tags"
        "Requires at least"
        "Tested up to"
        "Requires PHP"
    )

    for header in "${optional_headers[@]}"; do
        if grep -qi "^[[:space:]]*${header}:" "$style" 2>/dev/null; then
            check_pass "${header} — present"
        else
            check_warn "${header} — missing [recommended]"
        fi
    done

    # Text domain should match directory name
    local text_domain
    text_domain=$(grep -i "Text Domain:" "$style" | sed 's/.*Text Domain:[[:space:]]*//' | tr -d '\r' | tr -d ' ')
    local dir_name
    dir_name=$(basename "$THEME_DIR")
    if [[ "$text_domain" == "$dir_name" ]]; then
        check_pass "Text domain matches directory name: $text_domain"
    else
        check_warn "Text domain ($text_domain) ≠ directory name ($dir_name)"
    fi
}

# ===========================================================================
# SECTION 3: Screenshot
# ===========================================================================
check_screenshot() {
    log_step "3. Screenshot"

    local screenshot=""
    for ext in png jpg jpeg; do
        if [[ -f "$THEME_DIR/screenshot.$ext" ]]; then
            screenshot="$THEME_DIR/screenshot.$ext"
            break
        fi
    done

    if [[ -z "$screenshot" ]]; then
        check_fail "screenshot.png — MISSING (required for marketplace)"
        return
    fi

    check_pass "Screenshot found: $(basename "$screenshot")"

    # Check size (should be 1200x900 for wp.org, 880x660 minimum for ThemeForest)
    local file_size
    file_size=$(wc -c < "$screenshot" | tr -d ' ')
    local file_kb=$((file_size / 1024))

    if [[ "$file_kb" -lt 2048 ]]; then
        check_pass "Screenshot size: ${file_kb}KB (under 2MB limit)"
    else
        check_fail "Screenshot size: ${file_kb}KB (exceeds 2MB limit)"
    fi

    # Check dimensions if sips available (macOS)
    if command -v sips &>/dev/null; then
        local width height
        width=$(sips -g pixelWidth "$screenshot" 2>/dev/null | tail -1 | awk '{print $2}')
        height=$(sips -g pixelHeight "$screenshot" 2>/dev/null | tail -1 | awk '{print $2}')

        if [[ -n "$width" && -n "$height" ]]; then
            if [[ "$width" -eq 1200 && "$height" -eq 900 ]]; then
                check_pass "Screenshot dimensions: ${width}×${height} (WordPress.org optimal)"
            elif [[ "$width" -ge 880 && "$height" -ge 660 ]]; then
                check_warn "Screenshot dimensions: ${width}×${height} (acceptable, optimal is 1200×900)"
            else
                check_fail "Screenshot dimensions: ${width}×${height} (minimum 880×660 required)"
            fi
        fi
    fi
}

# ===========================================================================
# SECTION 4: PHP Coding Standards
# ===========================================================================
check_php_standards() {
    log_step "4. PHP Coding Standards"

    if ! command -v php &>/dev/null; then
        check_warn "PHP not available — skipping syntax checks"
        return
    fi

    # PHP syntax
    local errors=0 checked=0
    while IFS= read -r f; do
        checked=$((checked + 1))
        if ! php -l "$f" &>/dev/null; then
            errors=$((errors + 1))
        fi
    done < <(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*" -type f)

    if [[ "$errors" -eq 0 ]]; then
        check_pass "PHP syntax: $checked files — all clean"
    else
        check_fail "PHP syntax: $errors of $checked files have errors"
    fi

    # ABSPATH guards
    local unguarded=0
    while IFS= read -r f; do
        if ! grep -q "ABSPATH\|defined.*ABSPATH" "$f" 2>/dev/null; then
            local name
            name=$(basename "$f")
            # Skip functions.php (it's the entry point in WP)
            if [[ "$name" != "functions.php" ]]; then
                unguarded=$((unguarded + 1))
            fi
        fi
    done < <(find "$THEME_DIR" -maxdepth 1 -name "*.php" -type f; \
             find "$THEME_DIR/inc" -name "*.php" -type f 2>/dev/null; \
             find "$THEME_DIR/template-parts" -name "*.php" -type f 2>/dev/null)

    if [[ "$unguarded" -eq 0 ]]; then
        check_pass "ABSPATH guards: all PHP files protected"
    else
        check_warn "ABSPATH guards: $unguarded file(s) missing direct access prevention"
    fi

    # Escaping audit (critical for wp.org)
    local esc_issues=0
    while IFS= read -r f; do
        # echo $var without escaping
        local raw
        raw=$(grep -n 'echo \$\|<?= \$' "$f" 2>/dev/null \
            | grep -v 'esc_html\|esc_attr\|esc_url\|esc_textarea\|wp_kses\|wp_nonce\|absint\|intval' || true)
        if [[ -n "$raw" ]]; then
            esc_issues=$((esc_issues + 1))
        fi
    done < <(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*" -type f)

    if [[ "$esc_issues" -eq 0 ]]; then
        check_pass "Output escaping: all outputs properly escaped"
    else
        check_warn "Output escaping: $esc_issues file(s) may have unescaped output"
    fi

    # Nonce verification on form handlers
    local form_handlers
    form_handlers=$(grep -rl '\$_POST\|\$_GET\|\$_REQUEST' "$THEME_DIR" --include="*.php" \
        -l --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
    local nonce_verified
    nonce_verified=$(grep -rl 'wp_verify_nonce\|check_admin_referer\|check_ajax_referer' "$THEME_DIR" --include="*.php" \
        -l --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$form_handlers" -gt 0 ]]; then
        if [[ "$nonce_verified" -ge "$form_handlers" ]]; then
            check_pass "Nonce verification: $nonce_verified/$form_handlers form handlers verified"
        else
            check_warn "Nonce verification: $nonce_verified of $form_handlers form handlers have nonce checks"
        fi
    fi

    # Prefix check (all functions should use theme prefix)
    local unprefixed=0
    while IFS= read -r f; do
        # Find function declarations without skyyrose_ prefix (exclude vendor)
        local bad_funcs
        bad_funcs=$(grep -n '^function [a-z]' "$f" 2>/dev/null \
            | grep -v 'function skyyrose_\|function __' || true)
        if [[ -n "$bad_funcs" ]]; then
            unprefixed=$((unprefixed + 1))
        fi
    done < <(find "$THEME_DIR/inc" -name "*.php" -type f 2>/dev/null)

    if [[ "$unprefixed" -eq 0 ]]; then
        check_pass "Function prefixing: all functions use skyyrose_ prefix"
    else
        check_warn "Function prefixing: $unprefixed file(s) have unprefixed functions"
    fi
}

# ===========================================================================
# SECTION 5: Translation Ready (i18n)
# ===========================================================================
check_i18n() {
    log_step "5. Translation Readiness (i18n)"

    # Check for text domain usage
    local text_domain="skyyrose-flagship"
    local i18n_calls
    i18n_calls=$(grep -rc "__(\|_e(\|_x(\|_n(\|esc_html__(\|esc_attr__(\|esc_html_e(" "$THEME_DIR" \
        --include="*.php" --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null \
        | awk -F: '{s+=$NF} END {print s+0}')

    if [[ "$i18n_calls" -gt 0 ]]; then
        check_pass "i18n function calls: $i18n_calls found"
    else
        check_fail "No i18n function calls found — theme is not translatable"
    fi

    # Check text domain consistency
    local wrong_domain
    wrong_domain=$(grep -rn "__(\|_e(\|esc_html__(\|esc_attr__(" "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null \
        | grep -v "'$text_domain'" | grep -v "\"$text_domain\"" | grep -c "'" || echo "0")

    if [[ "$wrong_domain" -eq 0 ]]; then
        check_pass "Text domain: consistently using '$text_domain'"
    else
        check_warn "Text domain: $wrong_domain call(s) may use wrong domain"
    fi

    # Check for .pot file
    if [[ -f "$THEME_DIR/languages/${text_domain}.pot" ]]; then
        check_pass "POT file exists: languages/${text_domain}.pot"
    elif [[ -d "$THEME_DIR/languages" ]]; then
        check_warn "languages/ dir exists but no .pot file (generate with wp i18n make-pot)"
    else
        check_warn "No languages/ directory — create one with .pot file for translations"
    fi

    # Hardcoded strings (not wrapped in i18n functions)
    local hardcoded=0
    while IFS= read -r f; do
        local name
        name=$(basename "$f")
        local matches
        matches=$(grep -n '>\s*[A-Z][a-z].*</' "$f" 2>/dev/null \
            | grep -v '__(\|_e(\|esc_html__\|esc_attr__\|printf\|<!--\|aria-label' | wc -l | tr -d ' ')
        if [[ "$matches" -gt 3 ]]; then
            hardcoded=$((hardcoded + 1))
        fi
    done < <(find "$THEME_DIR" -maxdepth 1 -name "template-*.php" -type f)

    if [[ "$hardcoded" -eq 0 ]]; then
        check_pass "No significant hardcoded strings detected"
    else
        check_warn "$hardcoded template(s) may have hardcoded English strings"
    fi
}

# ===========================================================================
# SECTION 6: Security
# ===========================================================================
check_security() {
    log_step "6. Security Audit"

    # eval() usage
    local eval_count
    eval_count=$(grep -rn 'eval(' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$eval_count" -eq 0 ]]; then
        check_pass "No eval() calls found"
    else
        check_fail "eval() used $eval_count time(s) — REJECTED by WordPress.org"
    fi

    # base64_decode (often flagged)
    local base64_count
    base64_count=$(grep -rn 'base64_decode\|base64_encode' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$base64_count" -eq 0 ]]; then
        check_pass "No base64_encode/decode calls"
    else
        check_warn "base64 usage: $base64_count call(s) — will be flagged in review"
    fi

    # file_get_contents for remote URLs
    local remote_fetch
    remote_fetch=$(grep -rn 'file_get_contents.*http' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$remote_fetch" -eq 0 ]]; then
        check_pass "No file_get_contents() for remote URLs (use wp_remote_get)"
    else
        check_fail "file_get_contents() used for remote URLs ($remote_fetch) — use wp_remote_get()"
    fi

    # Direct database queries without prepare
    local unsafe_db
    unsafe_db=$(grep -rn '\$wpdb->query\|\$wpdb->get_' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null \
        | grep -v 'prepare' | wc -l | tr -d ' ')
    if [[ "$unsafe_db" -eq 0 ]]; then
        check_pass "All \$wpdb queries use prepare()"
    else
        check_warn "$unsafe_db database query(ies) may lack prepare() — check for SQL injection"
    fi

    # Capability checks on admin functions
    local admin_funcs
    admin_funcs=$(grep -rn 'add_menu_page\|add_submenu_page\|add_options_page' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')
    local cap_checks
    cap_checks=$(grep -rn 'current_user_can\|manage_options' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$admin_funcs" -gt 0 && "$cap_checks" -gt 0 ]]; then
        check_pass "Capability checks present for admin pages"
    elif [[ "$admin_funcs" -gt 0 ]]; then
        check_warn "Admin pages found but capability checks may be insufficient"
    else
        check_pass "No custom admin pages requiring capability checks"
    fi

    # Sanitization on input
    local sanitize_count
    sanitize_count=$(grep -rc 'sanitize_text_field\|sanitize_email\|absint\|intval\|wp_kses' "$THEME_DIR" \
        --include="*.php" --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null \
        | awk -F: '{s+=$NF} END {print s+0}')

    if [[ "$sanitize_count" -gt 0 ]]; then
        check_pass "Input sanitization: $sanitize_count sanitize/validate calls found"
    else
        check_warn "No sanitization functions detected — ensure all user input is sanitized"
    fi

    # Check for hardcoded secrets
    local secrets
    secrets=$(grep -rn 'api_key\|api_secret\|password\s*=' "$THEME_DIR" --include="*.php" \
        --exclude-dir=vendor --exclude-dir=node_modules 2>/dev/null \
        | grep -v 'sanitize\|nonce\|get_option\|define\|//\|/\*\|@param' | wc -l | tr -d ' ')
    if [[ "$secrets" -eq 0 ]]; then
        check_pass "No hardcoded secrets detected"
    else
        check_warn "$secrets possible hardcoded credential(s) — check manually"
    fi
}

# ===========================================================================
# SECTION 7: Theme Features (wp.org + ThemeForest)
# ===========================================================================
check_features() {
    log_step "7. Theme Features"

    # Custom logo support
    if grep -rq 'custom-logo\|add_theme_support.*custom-logo' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Custom logo support"
    else
        check_warn "Custom logo support not detected"
    fi

    # Custom menus
    if grep -rq 'register_nav_menus\|register_nav_menu' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Custom menus registered"
    else
        check_warn "No register_nav_menus() call found"
    fi

    # Widget areas
    if grep -rq 'register_sidebar' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Widget areas registered"
    else
        check_warn "No register_sidebar() call found"
    fi

    # Post thumbnails
    if grep -rq 'post-thumbnails\|add_theme_support.*thumbnails' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Post thumbnails support"
    else
        check_warn "Post thumbnails not enabled"
    fi

    # Title tag
    if grep -rq 'title-tag\|add_theme_support.*title-tag' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Title tag support (wp_title handled by WordPress)"
    else
        check_fail "title-tag support missing — required for WordPress.org"
    fi

    # HTML5 support
    if grep -rq "add_theme_support.*html5" "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "HTML5 support enabled"
    else
        check_warn "HTML5 theme support not detected"
    fi

    # Customizer
    if [[ -f "$THEME_DIR/inc/customizer.php" ]]; then
        check_pass "Customizer integration (inc/customizer.php)"
    else
        check_warn "No customizer.php found"
    fi

    # WooCommerce support
    if grep -rq "add_theme_support.*woocommerce" "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "WooCommerce support declared"
    else
        check_warn "WooCommerce add_theme_support not found"
    fi

    # Responsive
    if grep -rq 'viewport\|@media' "$THEME_DIR/style.css" 2>/dev/null; then
        check_pass "Responsive design (viewport meta + media queries)"
    else
        check_warn "No responsive indicators found in style.css"
    fi

    # wp_body_open()
    if grep -rq 'wp_body_open' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "wp_body_open() hook present"
    else
        check_warn "wp_body_open() missing — required since WP 5.2"
    fi
}

# ===========================================================================
# SECTION 8: ThemeForest-Specific
# ===========================================================================
check_themeforest() {
    log_step "8. ThemeForest-Specific Quality"

    # Documentation
    if [[ -d "$THEME_DIR/documentation" ]] || [[ -f "$THEME_DIR/readme.txt" ]]; then
        check_pass "Documentation included"
    else
        check_warn "No documentation/ directory or readme.txt — required for ThemeForest"
    fi

    # Demo content
    if find "$THEME_DIR" -name "*.xml" -path "*/data/*" -type f 2>/dev/null | head -1 | grep -q .; then
        check_pass "Demo content XML found"
    else
        check_warn "No demo content import file — recommended for ThemeForest"
    fi

    # License file
    if [[ -f "$THEME_DIR/license.txt" ]] || [[ -f "$THEME_DIR/LICENSE" ]]; then
        check_pass "License file present"
    elif grep -q "License:" "$THEME_DIR/style.css" 2>/dev/null; then
        check_pass "License declared in style.css header"
    else
        check_warn "No license file found"
    fi

    # Code quality — no debug output
    local debug_count
    debug_count=$(grep -rn 'var_dump\|print_r\|error_log\|console\.log' "$THEME_DIR" \
        --include="*.php" --include="*.js" \
        --exclude-dir=vendor --exclude-dir=node_modules \
        -l 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$debug_count" -eq 0 ]]; then
        check_pass "No debug output (var_dump, console.log, etc.)"
    else
        check_warn "$debug_count file(s) contain debug output — remove before submission"
    fi

    # Child theme ready
    if grep -rq 'get_template_directory\|get_stylesheet_directory' "$THEME_DIR/functions.php" 2>/dev/null; then
        check_pass "Child theme compatible (uses get_template_directory)"
    else
        check_warn "May not be child-theme friendly — use get_template_directory()"
    fi

    # Theme options (customizer-based, not separate options page)
    if grep -rq 'customize_register\|WP_Customize' "$THEME_DIR" --include="*.php" 2>/dev/null; then
        check_pass "Customizer-based theme options (WordPress best practice)"
    else
        check_warn "No Customizer integration found"
    fi

    # Cross-browser CSS
    local vendor_prefixes
    vendor_prefixes=$(grep -rc '\-webkit-\|\-moz-\|\-ms-' "$THEME_DIR/style.css" 2>/dev/null || echo "0")
    if [[ "$vendor_prefixes" -gt 5 ]]; then
        check_pass "Vendor prefixes present ($vendor_prefixes instances)"
    else
        check_warn "Few vendor prefixes — ensure cross-browser compatibility"
    fi
}

# ===========================================================================
# SECTION 9: File Structure & Hygiene
# ===========================================================================
check_hygiene() {
    log_step "9. File Structure & Hygiene"

    # No .git directory in theme
    if [[ -d "$THEME_DIR/.git" ]]; then
        check_fail ".git directory present — must be excluded from submission"
    else
        check_pass "No .git directory"
    fi

    # No .DS_Store files
    local ds_store
    ds_store=$(find "$THEME_DIR" -name ".DS_Store" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$ds_store" -eq 0 ]]; then
        check_pass "No .DS_Store files"
    else
        check_warn "$ds_store .DS_Store file(s) — remove before submission"
        if [[ "$AUTO_FIX" == "true" ]]; then
            find "$THEME_DIR" -name ".DS_Store" -delete 2>/dev/null
            echo -e "    ${GREEN}→ Auto-fixed: removed .DS_Store files${NC}"
        fi
    fi

    # No Thumbs.db
    local thumbs
    thumbs=$(find "$THEME_DIR" -name "Thumbs.db" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$thumbs" -eq 0 ]]; then
        check_pass "No Thumbs.db files"
    else
        check_warn "$thumbs Thumbs.db file(s) — remove before submission"
    fi

    # No empty files
    local empty_files
    empty_files=$(find "$THEME_DIR" -name "*.php" -empty -not -path "*/vendor/*" -not -path "*/node_modules/*" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$empty_files" -eq 0 ]]; then
        check_pass "No empty PHP files"
    else
        check_warn "$empty_files empty PHP file(s) found"
    fi

    # node_modules should not be submitted
    if [[ -d "$THEME_DIR/node_modules" ]]; then
        check_warn "node_modules/ present — exclude from submission ZIP"
    else
        check_pass "No node_modules/ directory"
    fi

    # vendor/ managed properly
    if [[ -d "$THEME_DIR/vendor" ]]; then
        if [[ -f "$THEME_DIR/composer.json" ]]; then
            check_pass "vendor/ with composer.json — include in submission"
        else
            check_warn "vendor/ without composer.json — verify it's needed"
        fi
    fi

    # File count and theme size
    local file_count
    file_count=$(find "$THEME_DIR" -type f \
        -not -path "*/node_modules/*" \
        -not -path "*/vendor/*" \
        -not -path "*/.git/*" 2>/dev/null | wc -l | tr -d ' ')

    echo ""
    echo -e "  ${DIM}Theme files (excluding vendor/node_modules): ${file_count}${NC}"
}

# ===========================================================================
# Score Calculation & Summary
# ===========================================================================
calculate_score() {
    if [[ "$TOTAL_CHECKS" -gt 0 ]]; then
        # Passes = full points, warns = half points, fails = zero
        local points=$(( (PASSED * 100) + (WARNED * 50) ))
        local max_points=$((TOTAL_CHECKS * 100))
        SCORE=$(( points * 100 / max_points ))
    fi
}

print_summary() {
    calculate_score

    echo ""
    echo -e "${BOLD}══════════════════════════════════════════${NC}"
    echo -e "${BOLD}  MARKETPLACE EVALUATION SUMMARY${NC}"
    echo -e "${BOLD}══════════════════════════════════════════${NC}"
    echo ""
    echo -e "  Checks:  ${TOTAL_CHECKS}"
    echo -e "  Passed:  ${GREEN}${PASSED}${NC}"
    echo -e "  Warned:  ${YELLOW}${WARNED}${NC}"
    echo -e "  Failed:  ${RED}${FAILED}${NC}"
    echo ""

    if [[ "$SCORE" -ge 90 ]]; then
        echo -e "  Score:   ${GREEN}${BOLD}${SCORE}%${NC} — ${GREEN}READY for submission${NC}"
    elif [[ "$SCORE" -ge 75 ]]; then
        echo -e "  Score:   ${YELLOW}${BOLD}${SCORE}%${NC} — ${YELLOW}ALMOST READY (minor fixes)${NC}"
    elif [[ "$SCORE" -ge 50 ]]; then
        echo -e "  Score:   ${YELLOW}${BOLD}${SCORE}%${NC} — ${YELLOW}NEEDS WORK${NC}"
    else
        echo -e "  Score:   ${RED}${BOLD}${SCORE}%${NC} — ${RED}NOT READY${NC}"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"

    if [[ "$MODE" == "score" ]]; then
        # Quiet mode — run all checks silently, print score
        exec 3>&1 1>/dev/null 2>/dev/null
        check_required_files
        check_theme_header
        check_screenshot
        check_php_standards
        check_i18n
        check_security
        check_features
        check_themeforest
        check_hygiene
        calculate_score
        exec 1>&3 3>&-
        echo "$SCORE"
        exit 0
    fi

    echo ""
    echo -e "${BOLD}  SkyyRose Flagship — Marketplace Evaluation${NC}"
    echo -e "  Theme:    ${THEME_DIR}"
    echo -e "  Version:  $(grep 'Version:' "$THEME_DIR/style.css" 2>/dev/null | head -1 | sed 's/.*Version: *//' || echo 'unknown')"
    echo -e "  Mode:     ${CYAN}${MODE}${NC}"
    echo ""

    if [[ "$SAVE_REPORT" == "true" ]]; then
        mkdir -p "$REPORT_DIR"
        local report_file="$REPORT_DIR/marketplace-eval-$(date +%Y%m%d-%H%M%S).txt"
        echo "Saving report to: $report_file"

        {
            case "$MODE" in
                wporg)
                    check_required_files; check_theme_header; check_screenshot
                    check_php_standards; check_i18n; check_security; check_features
                    check_hygiene
                    ;;
                themeforest)
                    check_required_files; check_theme_header; check_screenshot
                    check_php_standards; check_i18n; check_security; check_features
                    check_themeforest; check_hygiene
                    ;;
                security)
                    check_security
                    ;;
                full)
                    check_required_files; check_theme_header; check_screenshot
                    check_php_standards; check_i18n; check_security; check_features
                    check_themeforest; check_hygiene
                    ;;
            esac
            print_summary
        } 2>&1 | tee "$report_file"
    else
        case "$MODE" in
            wporg)
                check_required_files; check_theme_header; check_screenshot
                check_php_standards; check_i18n; check_security; check_features
                check_hygiene
                ;;
            themeforest)
                check_required_files; check_theme_header; check_screenshot
                check_php_standards; check_i18n; check_security; check_features
                check_themeforest; check_hygiene
                ;;
            security)
                check_security
                ;;
            full)
                check_required_files; check_theme_header; check_screenshot
                check_php_standards; check_i18n; check_security; check_features
                check_themeforest; check_hygiene
                ;;
        esac
        print_summary
    fi
}

main "$@"
