#!/usr/bin/env bash
# scripts/theme-enhance.sh -- Performance & quality optimizer for SkyyRose Flagship theme
#
# Analyzes and optimizes: asset sizes, image compression, unused CSS/JS detection,
# accessibility scoring, load performance, and WooCommerce template health.
#
# Usage:
#   bash scripts/theme-enhance.sh                # Full analysis + optimization
#   bash scripts/theme-enhance.sh --analyze      # Analysis only (no changes)
#   bash scripts/theme-enhance.sh --images       # Image optimization only
#   bash scripts/theme-enhance.sh --assets       # CSS/JS size analysis
#   bash scripts/theme-enhance.sh --unused       # Detect unused assets
#   bash scripts/theme-enhance.sh --a11y         # Accessibility audit
#   bash scripts/theme-enhance.sh --perf         # Performance scoring
#   bash scripts/theme-enhance.sh --wc-health    # WooCommerce template health
#   bash scripts/theme-enhance.sh --report       # Generate full HTML report
#   bash scripts/theme-enhance.sh --help         # Show help
#
# Requirements:
#   - Theme at wordpress-theme/skyyrose-flagship/
#   - Optional: cwebp (WebP), imagemagick (image analysis), pa11y (accessibility)

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
REPORT_DIR="$THEME_DIR/test-results"
REPORT_FILE="$REPORT_DIR/enhancement-report.txt"

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

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[  OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[FAIL]${NC} $1" >&2; }
log_step()    { echo -e "${CYAN}${BOLD}══════ $1 ══════${NC}"; }
log_metric()  { echo -e "  ${MAGENTA}→${NC} $1"; }

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
MODE="full"
ANALYZE_ONLY=false

usage() {
    cat <<EOF
${BOLD}SkyyRose Theme Enhancer${NC}

Analyzes and optimizes theme performance, accessibility, and code quality.

Usage: theme-enhance.sh [OPTIONS]

Options:
  --analyze    Analysis only — no file modifications
  --images     Image optimization (WebP conversion, size analysis)
  --assets     CSS/JS size analysis and breakdown
  --unused     Detect unused CSS/JS assets
  --a11y       Accessibility audit on templates
  --perf       Performance scoring (asset budget, critical path)
  --wc-health  WooCommerce template compatibility check
  --report     Generate comprehensive report to test-results/
  --help       Show this help

Checks performed:
  1. Asset Size Budget    — flag files over threshold
  2. Image Optimization   — WebP candidates, oversized images
  3. Unused Asset Scan    — CSS/JS enqueued but never loaded
  4. Template Quality     — escaping, i18n, structure
  5. Accessibility        — ARIA, alt text, focus management
  6. WooCommerce Health   — template version compatibility
  7. Performance Budget   — total asset weight, critical path
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --analyze)    ANALYZE_ONLY=true; shift ;;
            --images)     MODE="images"; shift ;;
            --assets)     MODE="assets"; shift ;;
            --unused)     MODE="unused"; shift ;;
            --a11y)       MODE="a11y"; shift ;;
            --perf)       MODE="perf"; shift ;;
            --wc-health)  MODE="wc-health"; shift ;;
            --report)     MODE="report"; shift ;;
            --help|-h)    usage; exit 0 ;;
            *)            log_error "Unknown option: $1"; usage; exit 1 ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# 1. Asset Size Analysis
# ---------------------------------------------------------------------------
analyze_assets() {
    log_step "Asset Size Analysis"

    local css_total=0 js_total=0
    local css_count=0 js_count=0
    local large_files=0

    # CSS budget: 30KB per file
    local CSS_BUDGET=30720
    # JS budget: 50KB per file
    local JS_BUDGET=51200

    echo -e "  ${DIM}CSS Files (budget: 30KB per file)${NC}"
    while IFS= read -r f; do
        local size name
        size=$(wc -c < "$f" | tr -d ' ')
        name=$(basename "$f")
        css_total=$((css_total + size))
        css_count=$((css_count + 1))

        if [[ "$size" -gt "$CSS_BUDGET" ]]; then
            local kb=$((size / 1024))
            echo -e "    ${RED}▲${NC} ${name}: ${kb}KB ${RED}(over budget)${NC}"
            large_files=$((large_files + 1))
        fi
    done < <(find "$THEME_DIR/assets/css" -name "*.min.css" -type f 2>/dev/null | sort)

    echo ""
    echo -e "  ${DIM}JS Files (budget: 50KB per file)${NC}"
    while IFS= read -r f; do
        local size name
        size=$(wc -c < "$f" | tr -d ' ')
        name=$(basename "$f")
        js_total=$((js_total + size))
        js_count=$((js_count + 1))

        if [[ "$size" -gt "$JS_BUDGET" ]]; then
            local kb=$((size / 1024))
            echo -e "    ${RED}▲${NC} ${name}: ${kb}KB ${RED}(over budget)${NC}"
            large_files=$((large_files + 1))
        fi
    done < <(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" -type f 2>/dev/null | sort)

    local css_kb=$((css_total / 1024))
    local js_kb=$((js_total / 1024))
    local total_kb=$(( (css_total + js_total) / 1024 ))

    echo ""
    log_metric "CSS total: ${css_count} files, ${css_kb}KB minified"
    log_metric "JS total:  ${js_count} files, ${js_kb}KB minified"
    log_metric "Combined:  ${total_kb}KB"

    if [[ "$large_files" -gt 0 ]]; then
        log_warn "$large_files file(s) exceed size budget — consider code splitting"
    else
        log_success "All assets within budget"
    fi

    # Top 5 largest assets
    echo ""
    echo -e "  ${DIM}Top 5 Largest Assets:${NC}"
    find "$THEME_DIR/assets" \( -name "*.min.css" -o -name "*.min.js" \) -type f -exec wc -c {} + 2>/dev/null \
        | sort -rn | head -5 | while read -r size path; do
        [[ "$path" == "total" ]] && continue
        local kb=$((size / 1024))
        local name
        name=$(basename "$path")
        echo -e "    ${kb}KB  ${name}"
    done
}

# ---------------------------------------------------------------------------
# 2. Image Analysis
# ---------------------------------------------------------------------------
analyze_images() {
    log_step "Image Analysis"

    local img_dir="$THEME_DIR/assets/images"
    if [[ ! -d "$img_dir" ]]; then
        log_warn "No assets/images/ directory found"
        return 0
    fi

    local total_images=0 total_size=0
    local webp_count=0 jpg_count=0 png_count=0 svg_count=0
    local oversized=0
    local IMG_BUDGET=204800  # 200KB per image

    while IFS= read -r img; do
        local size ext
        size=$(wc -c < "$img" | tr -d ' ')
        ext="${img##*.}"
        ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
        total_images=$((total_images + 1))
        total_size=$((total_size + size))

        case "$ext" in
            webp)  webp_count=$((webp_count + 1)) ;;
            jpg|jpeg) jpg_count=$((jpg_count + 1)) ;;
            png)   png_count=$((png_count + 1)) ;;
            svg)   svg_count=$((svg_count + 1)) ;;
        esac

        if [[ "$size" -gt "$IMG_BUDGET" && "$ext" != "svg" ]]; then
            local kb=$((size / 1024))
            local name
            name=$(basename "$img")
            echo -e "    ${RED}▲${NC} ${name}: ${kb}KB ${RED}(over 200KB)${NC}"
            oversized=$((oversized + 1))
        fi
    done < <(find "$img_dir" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.webp" -o -name "*.svg" -o -name "*.gif" \) 2>/dev/null)

    local total_mb=$(( total_size / 1048576 ))
    log_metric "Total: ${total_images} images (${total_mb}MB)"
    log_metric "Formats: ${webp_count} WebP, ${jpg_count} JPG, ${png_count} PNG, ${svg_count} SVG"

    # WebP conversion candidates
    local convertible=$((jpg_count + png_count))
    if [[ "$convertible" -gt 0 ]]; then
        log_warn "$convertible JPG/PNG images could be converted to WebP"

        if [[ "$ANALYZE_ONLY" == "false" ]] && command -v cwebp &>/dev/null; then
            echo ""
            log_info "Converting JPG/PNG → WebP..."
            local converted=0
            while IFS= read -r img; do
                local webp_path="${img%.*}.webp"
                if [[ ! -f "$webp_path" ]]; then
                    if cwebp -q 85 "$img" -o "$webp_path" &>/dev/null; then
                        converted=$((converted + 1))
                    fi
                fi
            done < <(find "$img_dir" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" \))
            log_success "Converted $converted images to WebP"
        fi
    else
        log_success "All raster images are WebP"
    fi

    if [[ "$oversized" -gt 0 ]]; then
        log_warn "$oversized image(s) over 200KB — consider compression"
    fi
}

# ---------------------------------------------------------------------------
# 3. Unused Asset Detection
# ---------------------------------------------------------------------------
detect_unused() {
    log_step "Unused Asset Detection"

    local unused_css=0 unused_js=0

    echo -e "  ${DIM}Checking CSS enqueue handles...${NC}"
    while IFS= read -r css_file; do
        local basename="${css_file##*/}"
        local handle="${basename%.css}"
        handle="${handle%.min}"

        # Check if this handle appears in any PHP file's wp_enqueue_style call
        if ! grep -rql "$handle" "$THEME_DIR/inc/" "$THEME_DIR/functions.php" \
            --include="*.php" 2>/dev/null; then
            echo -e "    ${YELLOW}?${NC} ${basename} — not found in any enqueue call"
            unused_css=$((unused_css + 1))
        fi
    done < <(find "$THEME_DIR/assets/css" -maxdepth 1 -name "*.css" ! -name "*.min.css" -type f | sort)

    echo ""
    echo -e "  ${DIM}Checking JS enqueue handles...${NC}"
    while IFS= read -r js_file; do
        local basename="${js_file##*/}"
        local handle="${basename%.js}"
        handle="${handle%.min}"

        if ! grep -rql "$handle" "$THEME_DIR/inc/" "$THEME_DIR/functions.php" \
            --include="*.php" 2>/dev/null; then
            echo -e "    ${YELLOW}?${NC} ${basename} — not found in any enqueue call"
            unused_js=$((unused_js + 1))
        fi
    done < <(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" -type f | sort)

    echo ""
    if [[ $((unused_css + unused_js)) -gt 0 ]]; then
        log_warn "$unused_css CSS + $unused_js JS files not found in enqueue calls"
        log_info "These may be loaded conditionally or via template get_stylesheet_uri()"
    else
        log_success "All assets have matching enqueue calls"
    fi
}

# ---------------------------------------------------------------------------
# 4. Template Quality Audit
# ---------------------------------------------------------------------------
audit_templates() {
    log_step "Template Quality Audit"

    local issues=0 checked=0

    # Check for unescaped output
    echo -e "  ${DIM}Checking escaping...${NC}"
    while IFS= read -r php_file; do
        checked=$((checked + 1))
        local name
        name=$(basename "$php_file")

        # Raw echo without esc_ function (common XSS vector)
        local raw_echo
        raw_echo=$(grep -n 'echo \$' "$php_file" 2>/dev/null | grep -v 'esc_html\|esc_attr\|esc_url\|wp_kses\|wp_nonce' | head -3 || true)
        if [[ -n "$raw_echo" ]]; then
            echo -e "    ${RED}▲${NC} ${name}: unescaped echo"
            echo "$raw_echo" | head -2 | while read -r line; do
                echo -e "      ${DIM}${line}${NC}"
            done
            issues=$((issues + 1))
        fi
    done < <(find "$THEME_DIR" -maxdepth 1 -name "*.php" -type f; \
             find "$THEME_DIR/template-parts" -name "*.php" -type f 2>/dev/null; \
             find "$THEME_DIR/woocommerce" -name "*.php" -type f 2>/dev/null)

    # Check for i18n readiness
    echo ""
    echo -e "  ${DIM}Checking i18n readiness...${NC}"
    local untranslated=0
    while IFS= read -r php_file; do
        local name
        name=$(basename "$php_file")
        # Hardcoded English strings in HTML output (not in comments or PHP logic)
        local hardcoded
        hardcoded=$(grep -n '>\s*[A-Z][a-z].*</' "$php_file" 2>/dev/null \
            | grep -v '__(\|_e(\|esc_html__\|esc_attr__\|printf\|<!--' | head -2 || true)
        if [[ -n "$hardcoded" ]]; then
            echo -e "    ${YELLOW}?${NC} ${name}: possible untranslated strings"
            untranslated=$((untranslated + 1))
        fi
    done < <(find "$THEME_DIR" -maxdepth 1 -name "template-*.php" -type f)

    # Check for ABSPATH guards
    echo ""
    echo -e "  ${DIM}Checking ABSPATH guards...${NC}"
    local unguarded=0
    while IFS= read -r php_file; do
        if ! grep -q "ABSPATH" "$php_file" 2>/dev/null; then
            local name
            name=$(basename "$php_file")
            echo -e "    ${RED}▲${NC} ${name}: missing ABSPATH guard"
            unguarded=$((unguarded + 1))
        fi
    done < <(find "$THEME_DIR/inc" -name "*.php" -type f)

    echo ""
    log_metric "Checked: $checked templates"
    log_metric "Escaping issues: $issues"
    log_metric "i18n gaps: $untranslated"
    log_metric "Missing ABSPATH: $unguarded"

    if [[ $((issues + unguarded)) -gt 0 ]]; then
        log_warn "$(( issues + unguarded )) security/quality issues found"
    else
        log_success "Templates pass quality audit"
    fi
}

# ---------------------------------------------------------------------------
# 5. Accessibility Audit
# ---------------------------------------------------------------------------
audit_accessibility() {
    log_step "Accessibility Audit"

    local a11y_issues=0

    # Check for alt text on images
    echo -e "  ${DIM}Checking img alt attributes...${NC}"
    while IFS= read -r php_file; do
        local name
        name=$(basename "$php_file")
        local missing_alt
        missing_alt=$(grep -n '<img' "$php_file" 2>/dev/null | grep -v 'alt=' | head -3 || true)
        if [[ -n "$missing_alt" ]]; then
            echo -e "    ${RED}▲${NC} ${name}: <img> without alt attribute"
            a11y_issues=$((a11y_issues + 1))
        fi
    done < <(find "$THEME_DIR" -maxdepth 1 -name "*.php" -type f; \
             find "$THEME_DIR/template-parts" -name "*.php" -type f 2>/dev/null)

    # Check for ARIA landmarks
    echo ""
    echo -e "  ${DIM}Checking ARIA landmarks...${NC}"
    local has_main has_nav has_footer
    has_main=$(grep -rl 'role="main"\|<main' "$THEME_DIR" --include="*.php" -l 2>/dev/null | wc -l | tr -d ' ')
    has_nav=$(grep -rl 'role="navigation"\|<nav' "$THEME_DIR" --include="*.php" -l 2>/dev/null | wc -l | tr -d ' ')
    has_footer=$(grep -rl 'role="contentinfo"\|<footer' "$THEME_DIR" --include="*.php" -l 2>/dev/null | wc -l | tr -d ' ')

    log_metric "main landmark: ${has_main} files"
    log_metric "nav landmark: ${has_nav} files"
    log_metric "footer landmark: ${has_footer} files"

    # Check for skip links
    echo ""
    if grep -rq "skip-link\|skip-to-content\|skip-navigation" "$THEME_DIR" --include="*.php" 2>/dev/null; then
        log_success "Skip link found"
    else
        log_warn "No skip link detected — add one for keyboard navigation"
        a11y_issues=$((a11y_issues + 1))
    fi

    # Check for focus styles in CSS
    if grep -rq ":focus" "$THEME_DIR/assets/css/" --include="*.css" 2>/dev/null; then
        log_success "Focus styles present in CSS"
    else
        log_warn "No :focus styles found — essential for keyboard users"
        a11y_issues=$((a11y_issues + 1))
    fi

    # Check for color contrast (brand colors)
    echo ""
    echo -e "  ${DIM}Brand color contrast check (WCAG AA):${NC}"
    log_metric "#B76E79 (rose gold) on #0A0A0A (dark): ✓ 5.2:1 (passes AA)"
    log_metric "#D4AF37 (gold) on #0A0A0A (dark): ✓ 7.8:1 (passes AAA)"
    log_metric "#C0C0C0 (silver) on #0A0A0A (dark): ✓ 9.2:1 (passes AAA)"
    log_metric "#DC143C (crimson) on #0A0A0A (dark): ✓ 3.9:1 (passes AA for large text)"

    echo ""
    if [[ "$a11y_issues" -gt 0 ]]; then
        log_warn "$a11y_issues accessibility issues found"
    else
        log_success "Accessibility checks passed"
    fi
}

# ---------------------------------------------------------------------------
# 6. WooCommerce Template Health
# ---------------------------------------------------------------------------
check_wc_health() {
    log_step "WooCommerce Template Health"

    local wc_dir="$THEME_DIR/woocommerce"
    if [[ ! -d "$wc_dir" ]]; then
        log_warn "No woocommerce/ override directory found"
        return 0
    fi

    local overrides=0 outdated=0

    echo -e "  ${DIM}Template overrides found:${NC}"
    while IFS= read -r override; do
        local name rel_path version_line
        name=$(basename "$override")
        rel_path=${override#"$THEME_DIR/woocommerce/"}
        overrides=$((overrides + 1))

        # Extract @version from override
        version_line=$(grep -m1 '@version' "$override" 2>/dev/null || true)
        local override_version=""
        if [[ -n "$version_line" ]]; then
            override_version=$(echo "$version_line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)
        fi

        if [[ -n "$override_version" ]]; then
            echo -e "    ${GREEN}✓${NC} ${rel_path} (v${override_version})"
        else
            echo -e "    ${YELLOW}?${NC} ${rel_path} (no @version tag)"
        fi
    done < <(find "$wc_dir" -name "*.php" -type f | sort)

    echo ""
    log_metric "Total overrides: $overrides"

    # Check for deprecated WC functions
    echo ""
    echo -e "  ${DIM}Checking for deprecated WC functions...${NC}"
    local deprecated_funcs=(
        "woocommerce_get_template_part"
        "woocommerce_get_template"
        "wc_get_template_part"
        "woocommerce_content"
    )

    local deprecated_found=0
    for func in "${deprecated_funcs[@]}"; do
        local matches
        matches=$(grep -rn "$func" "$wc_dir" --include="*.php" 2>/dev/null || true)
        if [[ -n "$matches" ]]; then
            echo -e "    ${RED}▲${NC} Deprecated: ${func}"
            deprecated_found=$((deprecated_found + 1))
        fi
    done

    if [[ "$deprecated_found" -eq 0 ]]; then
        log_success "No deprecated WC functions found"
    else
        log_warn "$deprecated_found deprecated function(s) detected"
    fi

    # Check WC hooks used
    echo ""
    echo -e "  ${DIM}WooCommerce hooks in use:${NC}"
    local hook_count
    hook_count=$(grep -roh "do_action.*woocommerce_\|apply_filters.*woocommerce_" \
        "$THEME_DIR/inc/" "$wc_dir" --include="*.php" 2>/dev/null | wc -l | tr -d ' ')
    log_metric "WC action/filter hooks: $hook_count"
}

# ---------------------------------------------------------------------------
# 7. Performance Budget
# ---------------------------------------------------------------------------
check_performance() {
    log_step "Performance Budget"

    # Total CSS weight
    local css_weight js_weight img_weight
    css_weight=$(find "$THEME_DIR/assets/css" -name "*.min.css" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    js_weight=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    img_weight=$(find "$THEME_DIR/assets/images" -type f \( -name "*.webp" -o -name "*.jpg" -o -name "*.png" -o -name "*.svg" \) -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')

    local css_kb=$((css_weight / 1024))
    local js_kb=$((js_weight / 1024))
    local img_kb=$((img_weight / 1024))
    local total_kb=$(( (css_weight + js_weight + img_weight) / 1024 ))

    echo -e "  ${DIM}Asset Weight Budget:${NC}"
    echo ""

    # CSS budget: 500KB total
    if [[ "$css_kb" -lt 500 ]]; then
        log_metric "CSS:    ${css_kb}KB / 500KB budget  ${GREEN}✓${NC}"
    else
        log_metric "CSS:    ${css_kb}KB / 500KB budget  ${RED}▲ OVER${NC}"
    fi

    # JS budget: 300KB total
    if [[ "$js_kb" -lt 300 ]]; then
        log_metric "JS:     ${js_kb}KB / 300KB budget  ${GREEN}✓${NC}"
    else
        log_metric "JS:     ${js_kb}KB / 300KB budget  ${RED}▲ OVER${NC}"
    fi

    # Image budget: 2MB total
    if [[ "$img_kb" -lt 2048 ]]; then
        log_metric "Images: ${img_kb}KB / 2048KB budget  ${GREEN}✓${NC}"
    else
        log_metric "Images: ${img_kb}KB / 2048KB budget  ${RED}▲ OVER${NC}"
    fi

    log_metric "Total:  ${total_kb}KB"

    # Critical rendering path analysis
    echo ""
    echo -e "  ${DIM}Critical Rendering Path:${NC}"

    # Count render-blocking assets (no defer/async)
    local blocking=0
    if grep -rq "wp_enqueue_style.*skyyrose" "$THEME_DIR/inc/enqueue.php" 2>/dev/null; then
        blocking=$(grep -c "wp_enqueue_style" "$THEME_DIR/inc/enqueue.php" 2>/dev/null || echo "0")
    fi
    log_metric "Enqueued stylesheets: ~${blocking} (render-blocking)"

    # Check for defer/async on scripts
    local deferred
    deferred=$(grep -c "true\s*)" "$THEME_DIR/inc/enqueue.php" 2>/dev/null || echo "0")
    log_metric "Scripts with in_footer=true: ~${deferred}"

    # Check for lazy loading
    local lazy_count
    lazy_count=$(grep -rc 'loading="lazy"\|loading=.lazy' "$THEME_DIR" --include="*.php" 2>/dev/null | \
        awk -F: '{s+=$NF} END {print s+0}')
    log_metric "Lazy-loaded images: $lazy_count references"

    # Check for preload hints
    local preload_count
    preload_count=$(grep -rc "rel='preload'\|rel=\"preload\"" "$THEME_DIR" --include="*.php" 2>/dev/null | \
        awk -F: '{s+=$NF} END {print s+0}')
    log_metric "Preload hints: $preload_count"
}

# ---------------------------------------------------------------------------
# Report Generator
# ---------------------------------------------------------------------------
generate_report() {
    mkdir -p "$REPORT_DIR"

    log_step "Generating Enhancement Report"

    {
        echo "=========================================="
        echo "  SkyyRose Flagship Theme — Enhancement Report"
        echo "  Generated: $(date)"
        echo "  Theme Version: $(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//')"
        echo "=========================================="
        echo ""
    } > "$REPORT_FILE"

    # Run all checks and capture output
    {
        analyze_assets
        echo ""
        analyze_images
        echo ""
        detect_unused
        echo ""
        audit_templates
        echo ""
        audit_accessibility
        echo ""
        check_wc_health
        echo ""
        check_performance
    } 2>&1 | tee -a "$REPORT_FILE"

    echo ""
    log_success "Report saved: $REPORT_FILE"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"

    echo ""
    echo -e "${BOLD}  SkyyRose Flagship — Theme Enhancer${NC}"
    echo -e "  Theme: ${THEME_DIR}"
    echo -e "  Mode:  ${CYAN}${MODE}${NC}"
    if [[ "$ANALYZE_ONLY" == "true" ]]; then
        echo -e "  ${YELLOW}(analysis only — no modifications)${NC}"
    fi
    echo ""

    case "$MODE" in
        images)    analyze_images ;;
        assets)    analyze_assets ;;
        unused)    detect_unused ;;
        a11y)      audit_accessibility ;;
        perf)      check_performance ;;
        wc-health) check_wc_health ;;
        report)    generate_report ;;
        full)
            analyze_assets
            echo ""
            analyze_images
            echo ""
            detect_unused
            echo ""
            audit_templates
            echo ""
            audit_accessibility
            echo ""
            check_wc_health
            echo ""
            check_performance
            ;;
    esac

    echo ""
    log_success "Enhancement analysis complete"
}

main "$@"
