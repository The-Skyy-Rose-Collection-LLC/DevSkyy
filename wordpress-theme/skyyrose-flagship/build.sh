#!/usr/bin/env bash
# ============================================================================
# SkyyRose Flagship Theme — Production Asset Build
#
# Minifies all CSS and JS files in assets/ using proper tools:
#   CSS: clean-css-cli (via npx) or esbuild fallback
#   JS:  terser (via npx) or esbuild fallback
#
# Usage:
#   bash build.sh             # Build all CSS + JS
#   bash build.sh --css-only  # Build CSS only
#   bash build.sh --js-only   # Build JS only
#   bash build.sh --clean     # Remove all .min files
#   bash build.sh --watch     # Watch mode (rebuild on change)
#   bash build.sh --dry-run   # Show what would be built (no writes)
#
# Idempotent: safe to run multiple times. Overwrites existing .min files.
#
# @package SkyyRose_Flagship
# @since   4.1.0
# ============================================================================

set -euo pipefail

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSS_DIR="${THEME_DIR}/assets/css"
JS_DIR="${THEME_DIR}/assets/js"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Counters
css_count=0
js_count=0
css_saved=0
js_saved=0
total_original=0
total_minified=0
errors=0

# Flags
DO_CSS=true
DO_JS=true
DRY_RUN=false

# ============================================================================
# Parse arguments
# ============================================================================

for arg in "$@"; do
    case "$arg" in
        --css-only)
            DO_JS=false
            ;;
        --js-only)
            DO_CSS=false
            ;;
        --clean)
            echo -e "${YELLOW}Cleaning all minified files...${NC}"
            find "${CSS_DIR}" -name '*.min.css' -type f -delete 2>/dev/null || true
            find "${JS_DIR}" -name '*.min.js' -type f -delete 2>/dev/null || true
            echo -e "${GREEN}Done. All .min.css and .min.js files removed.${NC}"
            exit 0
            ;;
        --watch)
            echo -e "${CYAN}Watch mode: rebuilding on file changes...${NC}"
            echo -e "${DIM}Press Ctrl+C to stop.${NC}"
            # Use fswatch if available, otherwise poll
            if command -v fswatch &>/dev/null; then
                fswatch -o "${CSS_DIR}" "${JS_DIR}" --include='\.css$' --include='\.js$' --exclude='\.min\.' | while read -r; do
                    echo -e "\n${YELLOW}Change detected, rebuilding...${NC}"
                    bash "${BASH_SOURCE[0]}"
                done
            else
                echo -e "${YELLOW}fswatch not found. Install with: brew install fswatch${NC}"
                echo -e "${DIM}Falling back to 3-second poll...${NC}"
                while true; do
                    bash "${BASH_SOURCE[0]}"
                    sleep 3
                done
            fi
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --help|-h)
            echo "Usage: bash build.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --css-only   Build CSS only"
            echo "  --js-only    Build JS only"
            echo "  --clean      Remove all .min files"
            echo "  --watch      Watch mode (rebuild on change)"
            echo "  --dry-run    Show what would be built"
            echo "  --help       Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Run with --help for usage."
            exit 1
            ;;
    esac
done

# ============================================================================
# Detect available minification tools
# ============================================================================

CSS_TOOL=""
JS_TOOL=""

detect_tools() {
    # CSS tool detection
    if npx --yes clean-css-cli --version &>/dev/null 2>&1; then
        CSS_TOOL="cleancss"
    elif npx --yes csso-cli --version &>/dev/null 2>&1; then
        CSS_TOOL="csso"
    elif command -v npx &>/dev/null && npx --yes esbuild --version &>/dev/null 2>&1; then
        CSS_TOOL="esbuild"
    else
        echo -e "${RED}ERROR: No CSS minification tool found.${NC}"
        echo "Install Node.js and npm, then run: npm install"
        exit 1
    fi

    # JS tool detection
    if npx --yes terser --version &>/dev/null 2>&1; then
        JS_TOOL="terser"
    elif command -v npx &>/dev/null && npx --yes esbuild --version &>/dev/null 2>&1; then
        JS_TOOL="esbuild"
    else
        echo -e "${RED}ERROR: No JS minification tool found.${NC}"
        echo "Install Node.js and npm, then run: npm install"
        exit 1
    fi

    echo -e "${DIM}CSS tool: ${CSS_TOOL}  |  JS tool: ${JS_TOOL}${NC}"
}

# ============================================================================
# Minification functions
# ============================================================================

minify_css() {
    local src="$1"
    local dest="$2"

    case "$CSS_TOOL" in
        cleancss)
            npx --yes clean-css-cli -o "$dest" "$src" 2>/dev/null
            ;;
        csso)
            npx --yes csso-cli --input "$src" --output "$dest" 2>/dev/null
            ;;
        esbuild)
            npx --yes esbuild "$src" --minify --outfile="$dest" 2>/dev/null
            ;;
    esac
}

minify_js() {
    local src="$1"
    local dest="$2"

    case "$JS_TOOL" in
        terser)
            npx --yes terser "$src" \
                --compress "ecma=2015,passes=2,drop_console=false" \
                --mangle "toplevel=false" \
                --output "$dest" 2>/dev/null
            ;;
        esbuild)
            npx --yes esbuild "$src" --minify --target=es2015 --outfile="$dest" 2>/dev/null
            ;;
    esac
}

# ============================================================================
# File size helpers
# ============================================================================

file_size() {
    wc -c < "$1" 2>/dev/null | tr -d ' '
}

human_size() {
    local bytes=$1
    if [ "$bytes" -ge 1048576 ]; then
        echo "$(echo "scale=1; $bytes / 1048576" | bc)MB"
    elif [ "$bytes" -ge 1024 ]; then
        echo "$(echo "scale=1; $bytes / 1024" | bc)KB"
    else
        echo "${bytes}B"
    fi
}

savings_pct() {
    local orig=$1
    local mini=$2
    if [ "$orig" -eq 0 ]; then
        echo "0"
        return
    fi
    echo "scale=1; (($orig - $mini) * 100) / $orig" | bc
}

# ============================================================================
# Main build
# ============================================================================

echo ""
echo -e "${BOLD}${CYAN}  SkyyRose Flagship — Production Build${NC}"
echo -e "${DIM}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${DIM}  ────────────────────────────────────${NC}"
echo ""

detect_tools

echo ""

# Summary table header
printf "${BOLD}%-45s %8s %8s %7s${NC}\n" "File" "Source" "Min" "Saved"
printf "%-45s %8s %8s %7s\n" "─────────────────────────────────────────────" "────────" "────────" "───────"

# ---- CSS Build ----
if [ "$DO_CSS" = true ]; then
    while IFS= read -r -d '' cssfile; do
        # Skip .min.css files
        [[ "$cssfile" == *.min.css ]] && continue

        rel_path="${cssfile#"${THEME_DIR}/"}"
        min_file="${cssfile%.css}.min.css"
        min_rel="${min_file#"${THEME_DIR}/"}"

        orig_size=$(file_size "$cssfile")

        if [ "$DRY_RUN" = true ]; then
            printf "${DIM}%-45s %8s %8s %7s${NC}\n" "$rel_path" "$(human_size "$orig_size")" "(dry)" "---"
            css_count=$((css_count + 1))
            continue
        fi

        if minify_css "$cssfile" "$min_file"; then
            mini_size=$(file_size "$min_file")
            pct=$(savings_pct "$orig_size" "$mini_size")
            saved=$((orig_size - mini_size))

            total_original=$((total_original + orig_size))
            total_minified=$((total_minified + mini_size))
            css_saved=$((css_saved + saved))
            css_count=$((css_count + 1))

            printf "${GREEN}%-45s${NC} %8s %8s ${GREEN}%6s%%${NC}\n" \
                "$rel_path" "$(human_size "$orig_size")" "$(human_size "$mini_size")" "$pct"
        else
            errors=$((errors + 1))
            printf "${RED}%-45s %8s %8s %7s${NC}\n" "$rel_path" "$(human_size "$orig_size")" "FAIL" "---"
        fi
    done < <(find "${CSS_DIR}" -name '*.css' -type f -print0 | sort -z)
fi

# ---- JS Build ----
if [ "$DO_JS" = true ]; then
    while IFS= read -r -d '' jsfile; do
        # Skip .min.js files
        [[ "$jsfile" == *.min.js ]] && continue

        rel_path="${jsfile#"${THEME_DIR}/"}"
        min_file="${jsfile%.js}.min.js"

        orig_size=$(file_size "$jsfile")

        if [ "$DRY_RUN" = true ]; then
            printf "${DIM}%-45s %8s %8s %7s${NC}\n" "$rel_path" "$(human_size "$orig_size")" "(dry)" "---"
            js_count=$((js_count + 1))
            continue
        fi

        if minify_js "$jsfile" "$min_file"; then
            mini_size=$(file_size "$min_file")
            pct=$(savings_pct "$orig_size" "$mini_size")
            saved=$((orig_size - mini_size))

            total_original=$((total_original + orig_size))
            total_minified=$((total_minified + mini_size))
            js_saved=$((js_saved + saved))
            js_count=$((js_count + 1))

            printf "${GREEN}%-45s${NC} %8s %8s ${GREEN}%6s%%${NC}\n" \
                "$rel_path" "$(human_size "$orig_size")" "$(human_size "$mini_size")" "$pct"
        else
            errors=$((errors + 1))
            printf "${RED}%-45s %8s %8s %7s${NC}\n" "$rel_path" "$(human_size "$orig_size")" "FAIL" "---"
        fi
    done < <(find "${JS_DIR}" -name '*.js' -type f -print0 | sort -z)
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
printf "%-45s %8s %8s %7s\n" "─────────────────────────────────────────────" "────────" "────────" "───────"

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}DRY RUN: ${css_count} CSS + ${js_count} JS files would be minified.${NC}"
else
    total_saved=$((total_original - total_minified))
    if [ "$total_original" -gt 0 ]; then
        total_pct=$(savings_pct "$total_original" "$total_minified")
    else
        total_pct="0"
    fi

    printf "${BOLD}%-45s %8s %8s ${GREEN}%6s%%${NC}\n" \
        "TOTAL" "$(human_size "$total_original")" "$(human_size "$total_minified")" "$total_pct"
    echo ""
    echo -e "  ${GREEN}CSS:${NC} ${css_count} files minified (${GREEN}$(human_size "$css_saved") saved${NC})"
    echo -e "  ${GREEN}JS: ${NC} ${js_count} files minified (${GREEN}$(human_size "$js_saved") saved${NC})"

    if [ "$errors" -gt 0 ]; then
        echo -e "  ${RED}Errors: ${errors} files failed${NC}"
    fi

    echo ""
    echo -e "  ${DIM}Total savings: $(human_size "$total_saved") (${total_pct}% reduction)${NC}"
fi

echo ""

if [ "$errors" -gt 0 ]; then
    exit 1
fi
