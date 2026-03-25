#!/usr/bin/env bash
# scripts/theme-build.sh -- Full build pipeline for SkyyRose Flagship WordPress theme
#
# Orchestrates: CSS minification, JS webpack build, PHP lint, source map
# generation, build verification, and asset manifest generation.
#
# Usage:
#   bash scripts/theme-build.sh                 # Full build
#   bash scripts/theme-build.sh --css           # CSS only (clean-css)
#   bash scripts/theme-build.sh --js            # JS only (webpack)
#   bash scripts/theme-build.sh --lint          # PHP + JS lint only
#   bash scripts/theme-build.sh --verify        # Verify build output only
#   bash scripts/theme-build.sh --manifest      # Generate asset manifest only
#   bash scripts/theme-build.sh --clean         # Remove all .min.* and .map files
#   bash scripts/theme-build.sh --watch         # Build then watch for changes
#   bash scripts/theme-build.sh --production    # Full build + strip source maps
#   bash scripts/theme-build.sh --help          # Show help
#
# Requirements:
#   - Node.js + npm (webpack, clean-css-cli, terser)
#   - PHP 8.0+ for syntax checks
#   - Theme at wordpress-theme/skyyrose-flagship/

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
BUILD_LOG="$THEME_DIR/test-results/build.log"

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[BUILD]${NC} $1"; }
log_success() { echo -e "${GREEN}[  OK ]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[ WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ FAIL]${NC} $1" >&2; }
log_step()    { echo -e "${CYAN}${BOLD}══════ $1 ══════${NC}"; }

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------
MODE="full"
PRODUCTION=false

usage() {
    cat <<EOF
${BOLD}SkyyRose Flagship Theme Builder${NC}

Usage: theme-build.sh [OPTIONS]

Options:
  --css          Build CSS only (clean-css minification + source maps)
  --js           Build JS only (webpack production bundle)
  --lint         PHP + JS linting only (no build)
  --verify       Verify build output (count matching, size checks)
  --manifest     Generate asset-manifest.json only
  --clean        Remove all .min.*, .map, and build artifacts
  --watch        Full build then watch for file changes
  --production   Full build + strip source maps for production deploy
  --help         Show this help

Pipeline:
  1. Clean stale artifacts
  2. Build CSS (clean-css with source maps)
  3. Build JS (webpack production mode)
  4. PHP syntax check on all theme PHP
  5. JS lint (eslint)
  6. Verify build (count matching, size checks)
  7. Generate asset manifest

Theme: $THEME_DIR
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --css)        MODE="css"; shift ;;
            --js)         MODE="js"; shift ;;
            --lint)       MODE="lint"; shift ;;
            --verify)     MODE="verify"; shift ;;
            --manifest)   MODE="manifest"; shift ;;
            --clean)      MODE="clean"; shift ;;
            --watch)      MODE="watch"; shift ;;
            --production) PRODUCTION=true; shift ;;
            --help|-h)    usage; exit 0 ;;
            *)            log_error "Unknown option: $1"; usage; exit 1 ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# Pre-flight
# ---------------------------------------------------------------------------
preflight() {
    log_step "Pre-Flight Checks"

    if [[ ! -d "$THEME_DIR" ]]; then
        log_error "Theme directory not found: $THEME_DIR"
        exit 1
    fi

    if ! command -v node &>/dev/null; then
        log_error "Node.js not found — required for CSS/JS build"
        exit 1
    fi

    if ! command -v php &>/dev/null; then
        log_warn "PHP not found — skipping PHP lint"
    fi

    # Ensure node_modules exist
    if [[ ! -d "$THEME_DIR/node_modules" ]]; then
        log_info "Installing npm dependencies..."
        (cd "$THEME_DIR" && npm install --silent)
        log_success "npm install complete"
    fi

    # Ensure build output directory
    mkdir -p "$THEME_DIR/test-results"

    log_success "Pre-flight passed (Node $(node -v), npm $(npm -v))"
}

# ---------------------------------------------------------------------------
# 1. Clean
# ---------------------------------------------------------------------------
clean_artifacts() {
    log_step "Cleaning Build Artifacts"

    local css_min js_min maps
    css_min=$(find "$THEME_DIR/assets/css" -name "*.min.css" 2>/dev/null | wc -l | tr -d ' ')
    js_min=$(find "$THEME_DIR/assets/js" -name "*.min.js" 2>/dev/null | wc -l | tr -d ' ')
    maps=$(find "$THEME_DIR/assets" -name "*.map" 2>/dev/null | wc -l | tr -d ' ')

    find "$THEME_DIR/assets/css" -name "*.min.css" -delete 2>/dev/null || true
    find "$THEME_DIR/assets/css" -name "*.min.css.map" -delete 2>/dev/null || true
    find "$THEME_DIR/assets/js" -name "*.min.js" -delete 2>/dev/null || true
    find "$THEME_DIR/assets/js" -name "*.min.js.map" -delete 2>/dev/null || true
    rm -f "$THEME_DIR/style.min.css" "$THEME_DIR/style.min.css.map"
    rm -f "$THEME_DIR/asset-manifest.json"

    log_success "Cleaned: ${css_min} .min.css, ${js_min} .min.js, ${maps} .map files"
}

# ---------------------------------------------------------------------------
# 2. Build CSS
# ---------------------------------------------------------------------------
build_css() {
    log_step "Building CSS"

    local start_time
    start_time=$(date +%s)

    (cd "$THEME_DIR" && node scripts/build-css.js) 2>&1 | tee -a "$BUILD_LOG"

    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    local css_count total_src total_min
    css_count=$(find "$THEME_DIR/assets/css" -name "*.min.css" 2>/dev/null | wc -l | tr -d ' ')
    total_src=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" 2>/dev/null | wc -l | tr -d ' ')

    # Calculate total size reduction
    local src_size min_size
    src_size=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    min_size=$(find "$THEME_DIR/assets/css" -name "*.min.css" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')

    if [[ "$src_size" -gt 0 ]]; then
        local savings=$(( (src_size - min_size) * 100 / src_size ))
        log_success "CSS: ${total_src} source → ${css_count} minified (${savings}% avg reduction) [${elapsed}s]"
    else
        log_success "CSS: ${css_count} files built [${elapsed}s]"
    fi
}

# ---------------------------------------------------------------------------
# 3. Build JS
# ---------------------------------------------------------------------------
build_js() {
    log_step "Building JS"

    local start_time
    start_time=$(date +%s)

    # Check if webpack config exists
    if [[ -f "$THEME_DIR/webpack.config.js" ]]; then
        (cd "$THEME_DIR" && npx webpack --mode production 2>&1) | tee -a "$BUILD_LOG"
    else
        # Fallback: use terser to minify each JS file individually
        log_info "No webpack.config.js — using terser for individual minification"

        local js_count=0
        local js_errors=0

        while IFS= read -r src_file; do
            local min_file="${src_file%.js}.min.js"
            local map_file="${min_file}.map"

            if npx terser "$src_file" \
                --compress passes=2 \
                --mangle \
                --source-map "filename='$(basename "$map_file")',url='$(basename "$map_file")'" \
                -o "$min_file" 2>/dev/null; then
                js_count=$((js_count + 1))
            else
                log_error "Failed to minify: $(basename "$src_file")"
                js_errors=$((js_errors + 1))
            fi
        done < <(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" -type f)

        if [[ "$js_errors" -gt 0 ]]; then
            log_error "$js_errors JS file(s) failed minification"
        fi
    fi

    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    local js_min_count
    js_min_count=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" 2>/dev/null | wc -l | tr -d ' ')

    # Calculate total JS reduction
    local src_size min_size
    src_size=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
    min_size=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')

    if [[ "$src_size" -gt 0 ]]; then
        local savings=$(( (src_size - min_size) * 100 / src_size ))
        log_success "JS: ${js_min_count} files minified (${savings}% avg reduction) [${elapsed}s]"
    else
        log_success "JS: ${js_min_count} files built [${elapsed}s]"
    fi
}

# ---------------------------------------------------------------------------
# 4. PHP Lint
# ---------------------------------------------------------------------------
lint_php() {
    log_step "PHP Syntax Check"

    if ! command -v php &>/dev/null; then
        log_warn "PHP not available — skipping"
        return 0
    fi

    local errors=0
    local checked=0

    # Lint all theme PHP files (exclude vendor/ and node_modules/)
    while IFS= read -r php_file; do
        checked=$((checked + 1))
        if ! php -l "$php_file" &>/dev/null; then
            log_error "Syntax error: $php_file"
            php -l "$php_file" 2>&1 | tail -1
            errors=$((errors + 1))
        fi
    done < <(find "$THEME_DIR" \
        -name "*.php" \
        -not -path "*/vendor/*" \
        -not -path "*/node_modules/*" \
        -type f)

    if [[ "$errors" -gt 0 ]]; then
        log_error "$errors of $checked PHP files have syntax errors"
        return 1
    fi

    log_success "PHP: $checked files — all clean"
}

# ---------------------------------------------------------------------------
# 5. JS Lint
# ---------------------------------------------------------------------------
lint_js() {
    log_step "JS Lint (ESLint)"

    if [[ ! -f "$THEME_DIR/node_modules/.bin/eslint" ]]; then
        log_warn "ESLint not installed — skipping"
        return 0
    fi

    local eslint_errors
    if eslint_errors=$(cd "$THEME_DIR" && npx eslint "assets/js/**/*.js" \
        --ignore-pattern "*.min.js" \
        --ignore-pattern "vendor/**" \
        --format compact 2>&1); then
        local warnings
        warnings=$(echo "$eslint_errors" | grep -c "warning" || true)
        log_success "JS lint passed ($warnings warnings)"
    else
        local error_count
        error_count=$(echo "$eslint_errors" | grep -c "error" || true)
        log_warn "JS lint: $error_count issues (non-blocking)"
        echo "$eslint_errors" | head -10
    fi
}

# ---------------------------------------------------------------------------
# 6. Verify Build
# ---------------------------------------------------------------------------
verify_build() {
    log_step "Build Verification"

    local verify_script="$THEME_DIR/scripts/verify-build.sh"
    if [[ -f "$verify_script" ]]; then
        bash "$verify_script" 2>&1 | tee -a "$BUILD_LOG"
    else
        log_warn "verify-build.sh not found — running inline checks"

        local js_src js_min css_src css_min
        js_src=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" | wc -l | tr -d ' ')
        js_min=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" | wc -l | tr -d ' ')
        css_src=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" | wc -l | tr -d ' ')
        css_min=$(find "$THEME_DIR/assets/css" -name "*.min.css" | wc -l | tr -d ' ')

        if [[ "$js_src" -eq "$js_min" ]]; then
            log_success "JS: $js_src source = $js_min minified"
        else
            log_error "JS mismatch: $js_src source ≠ $js_min minified"
        fi

        if [[ "$css_src" -eq "$css_min" ]]; then
            log_success "CSS: $css_src source = $css_min minified"
        else
            log_error "CSS mismatch: $css_src source ≠ $css_min minified"
        fi
    fi
}

# ---------------------------------------------------------------------------
# 7. Asset Manifest
# ---------------------------------------------------------------------------
generate_manifest() {
    log_step "Generating Asset Manifest"

    local manifest="$THEME_DIR/asset-manifest.json"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

    # Build JSON manifest of all production assets
    {
        echo "{"
        echo "  \"generated\": \"$timestamp\","
        echo "  \"theme_version\": \"$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')\","
        echo "  \"css\": {"

        local first=true
        while IFS= read -r min_file; do
            local basename rel_path size
            basename=$(basename "$min_file")
            rel_path=${min_file#"$THEME_DIR/"}
            size=$(wc -c < "$min_file" | tr -d ' ')

            local src_file="${min_file%.min.css}.css"
            local src_size=0
            [[ -f "$src_file" ]] && src_size=$(wc -c < "$src_file" | tr -d ' ')

            local hash
            hash=$(md5 -q "$min_file" 2>/dev/null || md5sum "$min_file" | cut -d' ' -f1)

            if [[ "$first" == "true" ]]; then
                first=false
            else
                echo ","
            fi
            printf '    "%s": {"path": "%s", "size": %d, "source_size": %d, "hash": "%s"}' \
                "${basename%.min.css}" "$rel_path" "$size" "$src_size" "${hash:0:8}"
        done < <(find "$THEME_DIR/assets/css" -name "*.min.css" -type f | sort)

        echo ""
        echo "  },"
        echo "  \"js\": {"

        first=true
        while IFS= read -r min_file; do
            local basename rel_path size
            basename=$(basename "$min_file")
            rel_path=${min_file#"$THEME_DIR/"}
            size=$(wc -c < "$min_file" | tr -d ' ')

            local src_file="${min_file%.min.js}.js"
            local src_size=0
            [[ -f "$src_file" ]] && src_size=$(wc -c < "$src_file" | tr -d ' ')

            local hash
            hash=$(md5 -q "$min_file" 2>/dev/null || md5sum "$min_file" | cut -d' ' -f1)

            if [[ "$first" == "true" ]]; then
                first=false
            else
                echo ","
            fi
            printf '    "%s": {"path": "%s", "size": %d, "source_size": %d, "hash": "%s"}' \
                "${basename%.min.js}" "$rel_path" "$size" "$src_size" "${hash:0:8}"
        done < <(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" -type f | sort)

        echo ""
        echo "  },"

        # Totals
        local total_css_src total_css_min total_js_src total_js_min
        total_css_src=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
        total_css_min=$(find "$THEME_DIR/assets/css" -name "*.min.css" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
        total_js_src=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')
        total_js_min=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" -exec cat {} + 2>/dev/null | wc -c | tr -d ' ')

        echo "  \"totals\": {"
        echo "    \"css_source_bytes\": $total_css_src,"
        echo "    \"css_minified_bytes\": $total_css_min,"
        echo "    \"js_source_bytes\": $total_js_src,"
        echo "    \"js_minified_bytes\": $total_js_min,"
        echo "    \"total_source_bytes\": $((total_css_src + total_js_src)),"
        echo "    \"total_minified_bytes\": $((total_css_min + total_js_min))"
        echo "  }"
        echo "}"
    } > "$manifest"

    log_success "Manifest: $manifest"
}

# ---------------------------------------------------------------------------
# Strip source maps (production mode)
# ---------------------------------------------------------------------------
strip_source_maps() {
    log_step "Stripping Source Maps (Production)"

    local maps
    maps=$(find "$THEME_DIR/assets" -name "*.map" 2>/dev/null | wc -l | tr -d ' ')
    find "$THEME_DIR/assets" -name "*.map" -delete 2>/dev/null || true
    rm -f "$THEME_DIR/style.min.css.map"

    # Remove sourceMappingURL references from minified files
    find "$THEME_DIR/assets" -name "*.min.css" -exec sed -i '' '/sourceMappingURL/d' {} + 2>/dev/null || true
    find "$THEME_DIR/assets" -name "*.min.js" -exec sed -i '' '/sourceMappingURL/d' {} + 2>/dev/null || true

    log_success "Stripped $maps source maps"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"

    local start_time
    start_time=$(date +%s)

    echo ""
    echo -e "${BOLD}  SkyyRose Flagship — Theme Build${NC}"
    echo -e "  Theme:   ${THEME_DIR}"
    echo -e "  Mode:    ${CYAN}${MODE}${NC}"
    if [[ "$PRODUCTION" == "true" ]]; then
        echo -e "  Target:  ${RED}PRODUCTION${NC} (source maps stripped)"
    fi
    echo ""

    case "$MODE" in
        css)
            preflight
            build_css
            ;;
        js)
            preflight
            build_js
            ;;
        lint)
            preflight
            lint_php
            lint_js
            ;;
        verify)
            verify_build
            ;;
        manifest)
            generate_manifest
            ;;
        clean)
            clean_artifacts
            ;;
        watch)
            preflight
            clean_artifacts
            build_css
            build_js
            lint_php
            verify_build
            generate_manifest
            log_info "Watching for changes... (Ctrl+C to stop)"
            (cd "$THEME_DIR" && npx nodemon \
                --watch assets/css --ext css \
                --watch assets/js --ext js \
                --ignore "*.min.*" --ignore "*.map" \
                --exec "bash $0 --css && bash $0 --js" \
                2>/dev/null) || \
            log_warn "nodemon not available — install with: npm i -g nodemon"
            ;;
        full)
            preflight
            clean_artifacts
            build_css
            build_js
            lint_php
            lint_js
            verify_build
            generate_manifest

            if [[ "$PRODUCTION" == "true" ]]; then
                strip_source_maps
            fi
            ;;
    esac

    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))

    echo ""
    log_success "Build complete [${elapsed}s]"
}

main "$@"
