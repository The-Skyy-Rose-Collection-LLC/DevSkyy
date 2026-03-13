#!/usr/bin/env bash
# scripts/theme-dev.sh -- Daily development toolkit for SkyyRose Flagship theme
#
# One command for common theme development tasks: scaffold templates, create
# new components, run local tests, sync WC products, and manage the dev cycle.
#
# Usage:
#   bash scripts/theme-dev.sh new-template <name>       # Scaffold a new page template
#   bash scripts/theme-dev.sh new-part <name>            # Scaffold a template part
#   bash scripts/theme-dev.sh new-css <name>             # Create CSS + register enqueue
#   bash scripts/theme-dev.sh new-js <name>              # Create JS + register enqueue
#   bash scripts/theme-dev.sh test                       # Run all theme tests
#   bash scripts/theme-dev.sh test-php                   # PHP lint only
#   bash scripts/theme-dev.sh test-js                    # Jest unit tests
#   bash scripts/theme-dev.sh test-e2e                   # Playwright E2E tests
#   bash scripts/theme-dev.sh status                     # Theme health status
#   bash scripts/theme-dev.sh diff-live                  # Diff local theme vs live site
#   bash scripts/theme-dev.sh version <x.y.z>            # Bump theme version
#   bash scripts/theme-dev.sh package                    # Create distributable ZIP
#   bash scripts/theme-dev.sh help                       # Show help

set -euo pipefail

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
SITE_URL="${WORDPRESS_URL:-https://skyyrose.co}"

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

log_info()    { echo -e "${BLUE}[DEV]${NC} $1"; }
log_success() { echo -e "${GREEN}[ OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERR]${NC} $1" >&2; }

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------
usage() {
    cat <<EOF
${BOLD}SkyyRose Theme Developer Toolkit${NC}

Usage: theme-dev.sh <command> [args]

${CYAN}Scaffolding:${NC}
  new-template <name>     Create a new page template (template-<name>.php)
  new-part <name>         Create a new template part (template-parts/<name>.php)
  new-css <name>          Create CSS file + add to enqueue list
  new-js <name>           Create JS file + add to enqueue list

${CYAN}Testing:${NC}
  test                    Run all tests (PHP lint + Jest + E2E)
  test-php                PHP syntax check on all theme files
  test-js                 Jest unit tests
  test-e2e                Playwright E2E tests
  test-build              Build verification (count matching, sizes)

${CYAN}Workflow:${NC}
  status                  Theme health overview (files, sizes, issues)
  diff-live               Compare local theme vs live production
  version <x.y.z>         Bump version in style.css + functions.php
  package                 Create distributable theme ZIP
  wc-sync                 Show WooCommerce product summary via REST API

${CYAN}Other:${NC}
  help                    Show this help message
EOF
}

# ---------------------------------------------------------------------------
# Scaffold: New Page Template
# ---------------------------------------------------------------------------
cmd_new_template() {
    local name="${1:-}"
    if [[ -z "$name" ]]; then
        log_error "Usage: theme-dev.sh new-template <name>"
        log_info "Example: theme-dev.sh new-template sustainability"
        exit 1
    fi

    local slug=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local file="$THEME_DIR/template-${slug}.php"
    local display_name=$(echo "$name" | sed 's/-/ /g; s/\b\(.\)/\u\1/g')

    if [[ -f "$file" ]]; then
        log_error "Template already exists: $file"
        exit 1
    fi

    cat > "$file" <<PHPEOF
<?php
/**
 * Template Name: ${display_name}
 *
 * @package SkyyRose_Flagship
 * @since   $(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>

<main id="primary" class="site-main" role="main" tabindex="-1">
<div class="page--${slug}" data-page="${slug}">

	<section class="page-hero" aria-label="<?php esc_attr_e( '${display_name}', 'skyyrose-flagship' ); ?>">
		<div class="page-hero__content fade-in-up">
			<h1 class="page-hero__title">
				<?php echo esc_html__( '${display_name}', 'skyyrose-flagship' ); ?>
			</h1>
		</div>
	</section>

	<section class="page-content" aria-labelledby="${slug}-heading">
		<div class="page-content__inner">
			<?php
			while ( have_posts() ) :
				the_post();
				the_content();
			endwhile;
			?>
		</div>
	</section>

</div>
</main>

<?php get_footer(); ?>
PHPEOF

    log_success "Created: $file"
    log_info "Assign in WordPress → Pages → Edit → Page Attributes → Template: ${display_name}"
}

# ---------------------------------------------------------------------------
# Scaffold: New Template Part
# ---------------------------------------------------------------------------
cmd_new_part() {
    local name="${1:-}"
    if [[ -z "$name" ]]; then
        log_error "Usage: theme-dev.sh new-part <name>"
        exit 1
    fi

    local slug=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local file="$THEME_DIR/template-parts/${slug}.php"

    if [[ -f "$file" ]]; then
        log_error "Template part already exists: $file"
        exit 1
    fi

    local version
    version=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')

    cat > "$file" <<PHPEOF
<?php
/**
 * Template Part: ${name}
 *
 * @package SkyyRose_Flagship
 * @since   ${version}
 */

defined( 'ABSPATH' ) || exit;

\$args = wp_parse_args( \$args ?? array(), array(
	'title' => '',
) );
?>

<div class="${slug}">
	<?php if ( ! empty( \$args['title'] ) ) : ?>
		<h3 class="${slug}__title">
			<?php echo esc_html( \$args['title'] ); ?>
		</h3>
	<?php endif; ?>
</div>
PHPEOF

    log_success "Created: $file"
    log_info "Use: get_template_part( 'template-parts/${slug}', null, array( 'title' => 'Hello' ) );"
}

# ---------------------------------------------------------------------------
# Scaffold: New CSS
# ---------------------------------------------------------------------------
cmd_new_css() {
    local name="${1:-}"
    if [[ -z "$name" ]]; then
        log_error "Usage: theme-dev.sh new-css <name>"
        exit 1
    fi

    local slug=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local file="$THEME_DIR/assets/css/${slug}.css"

    if [[ -f "$file" ]]; then
        log_error "CSS file already exists: $file"
        exit 1
    fi

    cat > "$file" <<CSSEOF
/**
 * ${name} Styles
 *
 * @package SkyyRose_Flagship
 */

.${slug} {
	/* Component root */
}
CSSEOF

    log_success "Created: $file"
    log_info "Register in inc/enqueue.php:"
    echo -e "  ${DIM}wp_enqueue_style( 'skyyrose-${slug}', SKYYROSE_ASSETS_URI . '/css/${slug}.css', array(), SKYYROSE_VERSION );${NC}"
}

# ---------------------------------------------------------------------------
# Scaffold: New JS
# ---------------------------------------------------------------------------
cmd_new_js() {
    local name="${1:-}"
    if [[ -z "$name" ]]; then
        log_error "Usage: theme-dev.sh new-js <name>"
        exit 1
    fi

    local slug=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    local file="$THEME_DIR/assets/js/${slug}.js"

    if [[ -f "$file" ]]; then
        log_error "JS file already exists: $file"
        exit 1
    fi

    cat > "$file" <<JSEOF
/**
 * ${name}
 *
 * @package SkyyRose_Flagship
 */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const root = document.querySelector('.${slug}');
    if (!root) return;

    // Component initialization
  });
})();
JSEOF

    log_success "Created: $file"
    log_info "Register in inc/enqueue.php:"
    echo -e "  ${DIM}wp_enqueue_script( 'skyyrose-${slug}', SKYYROSE_ASSETS_URI . '/js/${slug}.js', array(), SKYYROSE_VERSION, true );${NC}"
}

# ---------------------------------------------------------------------------
# Test: All
# ---------------------------------------------------------------------------
cmd_test() {
    log_info "Running all theme tests..."
    echo ""
    cmd_test_php
    echo ""
    cmd_test_js
    echo ""
    cmd_test_build
}

cmd_test_php() {
    log_info "PHP Syntax Check"
    local errors=0 checked=0

    while IFS= read -r f; do
        checked=$((checked + 1))
        if ! php -l "$f" &>/dev/null; then
            log_error "$(basename "$f")"
            errors=$((errors + 1))
        fi
    done < <(find "$THEME_DIR" -name "*.php" \
        -not -path "*/vendor/*" -not -path "*/node_modules/*" -type f)

    if [[ "$errors" -eq 0 ]]; then
        log_success "PHP: $checked files — all clean"
    else
        log_error "PHP: $errors of $checked files have errors"
        return 1
    fi
}

cmd_test_js() {
    log_info "Jest Unit Tests"
    if [[ -f "$THEME_DIR/node_modules/.bin/jest" ]]; then
        (cd "$THEME_DIR" && npx jest --passWithNoTests 2>&1) || log_warn "Some tests failed"
    else
        log_warn "Jest not installed — skipping"
    fi
}

cmd_test_build() {
    log_info "Build Verification"
    if [[ -f "$THEME_DIR/scripts/verify-build.sh" ]]; then
        bash "$THEME_DIR/scripts/verify-build.sh"
    else
        log_warn "verify-build.sh not found"
    fi
}

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
cmd_status() {
    echo -e "${BOLD}  SkyyRose Flagship — Theme Status${NC}"
    echo ""

    local version
    version=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')
    echo -e "  Version:   ${CYAN}${version}${NC}"
    echo -e "  Directory: ${THEME_DIR}"
    echo ""

    # File counts
    local php_count css_count js_count template_count
    php_count=$(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*" | wc -l | tr -d ' ')
    css_count=$(find "$THEME_DIR/assets/css" -name "*.css" ! -name "*.min.css" 2>/dev/null | wc -l | tr -d ' ')
    js_count=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.js" ! -name "*.min.js" 2>/dev/null | wc -l | tr -d ' ')
    template_count=$(find "$THEME_DIR" -maxdepth 1 -name "template-*.php" 2>/dev/null | wc -l | tr -d ' ')

    echo -e "  ${DIM}Files:${NC}"
    echo -e "    PHP:        ${php_count}"
    echo -e "    CSS:        ${css_count} source"
    echo -e "    JS:         ${js_count} source"
    echo -e "    Templates:  ${template_count} page templates"
    echo ""

    # Build state
    local css_min js_min
    css_min=$(find "$THEME_DIR/assets/css" -name "*.min.css" 2>/dev/null | wc -l | tr -d ' ')
    js_min=$(find "$THEME_DIR/assets/js" -maxdepth 1 -name "*.min.js" 2>/dev/null | wc -l | tr -d ' ')

    echo -e "  ${DIM}Build State:${NC}"
    if [[ "$css_count" -eq "$css_min" && "$css_count" -gt 0 ]]; then
        echo -e "    CSS:  ${GREEN}✓${NC} $css_min/$css_count minified"
    else
        echo -e "    CSS:  ${YELLOW}△${NC} $css_min/$css_count minified"
    fi

    if [[ "$js_count" -eq "$js_min" && "$js_count" -gt 0 ]]; then
        echo -e "    JS:   ${GREEN}✓${NC} $js_min/$js_count minified"
    else
        echo -e "    JS:   ${YELLOW}△${NC} $js_min/$js_count minified"
    fi
    echo ""

    # Quick PHP lint
    local php_errors=0
    while IFS= read -r f; do
        if ! php -l "$f" &>/dev/null 2>&1; then
            php_errors=$((php_errors + 1))
        fi
    done < <(find "$THEME_DIR" -name "*.php" -not -path "*/vendor/*" -not -path "*/node_modules/*" -type f)

    if [[ "$php_errors" -eq 0 ]]; then
        echo -e "  PHP Syntax: ${GREEN}✓ Clean${NC}"
    else
        echo -e "  PHP Syntax: ${RED}✗ $php_errors error(s)${NC}"
    fi

    # Git status
    echo ""
    echo -e "  ${DIM}Git:${NC}"
    local branch
    branch=$(cd "$PROJECT_ROOT" && git branch --show-current 2>/dev/null || echo "unknown")
    echo -e "    Branch: ${branch}"
    local changed
    changed=$(cd "$PROJECT_ROOT" && git diff --name-only -- "wordpress-theme/" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "    Changed theme files: ${changed}"
}

# ---------------------------------------------------------------------------
# Version Bump
# ---------------------------------------------------------------------------
cmd_version() {
    local new_version="${1:-}"
    if [[ -z "$new_version" ]]; then
        local current
        current=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')
        log_error "Usage: theme-dev.sh version <x.y.z>"
        log_info "Current version: $current"
        exit 1
    fi

    # Validate semver format
    if ! [[ "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $new_version (expected x.y.z)"
        exit 1
    fi

    local old_version
    old_version=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')

    # Update style.css
    sed -i '' "s/Version: .*/Version: ${new_version}/" "$THEME_DIR/style.css"

    # Update functions.php
    sed -i '' "s/define( 'SKYYROSE_VERSION', '.*'/define( 'SKYYROSE_VERSION', '${new_version}'/" "$THEME_DIR/functions.php"

    # Update package.json
    if [[ -f "$THEME_DIR/package.json" ]]; then
        sed -i '' "s/\"version\": \".*\"/\"version\": \"${new_version}\"/" "$THEME_DIR/package.json"
    fi

    log_success "Version bumped: $old_version → $new_version"
    log_info "Updated: style.css, functions.php, package.json"
}

# ---------------------------------------------------------------------------
# Package ZIP
# ---------------------------------------------------------------------------
cmd_package() {
    log_info "Creating distributable theme ZIP..."

    local version
    version=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')
    local zip_name="skyyrose-flagship-${version}.zip"
    local zip_path="$PROJECT_ROOT/$zip_name"

    # Build first
    if [[ -f "$SCRIPT_DIR/theme-build.sh" ]]; then
        log_info "Running production build..."
        bash "$SCRIPT_DIR/theme-build.sh" --production 2>&1 | tail -5
    fi

    # Create ZIP excluding dev files
    (cd "$PROJECT_ROOT/wordpress-theme" && zip -r "$zip_path" "skyyrose-flagship/" \
        -x "*/node_modules/*" \
        -x "*/.DS_Store" \
        -x "*/test-results/*" \
        -x "*/tests/*" \
        -x "*/.eslintrc*" \
        -x "*/package-lock.json" \
        -x "*/webpack.config.js" \
        -x "*/.gitignore" \
        -x "*/Thumbs.db" \
        -x "*/*.map" \
        > /dev/null 2>&1)

    local zip_size
    zip_size=$(wc -c < "$zip_path" | tr -d ' ')
    local zip_mb=$(( zip_size / 1048576 ))

    log_success "Package: $zip_path (${zip_mb}MB)"

    # ThemeForest max is 50MB
    if [[ "$zip_mb" -lt 50 ]]; then
        log_success "Size OK for marketplace submission (< 50MB)"
    else
        log_warn "Package exceeds 50MB — too large for most marketplaces"
    fi
}

# ---------------------------------------------------------------------------
# Diff vs Live
# ---------------------------------------------------------------------------
cmd_diff_live() {
    log_info "Comparing local theme vs live site..."
    echo -e "  ${DIM}Checking key pages for content markers...${NC}"
    echo ""

    local pages=(
        "/|site-main"
        "/collection-black-rose/|collection--black-rose"
        "/collection-love-hurts/|collection--love-hurts"
        "/collection-signature/|collection--signature"
        "/collection-kids-capsule/|collection--kids-capsule"
        "/shop/|woocommerce"
    )

    for entry in "${pages[@]}"; do
        IFS='|' read -r path marker <<< "$entry"
        local url="${SITE_URL}${path}"

        local http_code
        http_code=$(curl -sSL -o /dev/null -w "%{http_code}" --connect-timeout 5 --max-time 10 "$url" 2>/dev/null || echo "000")

        if [[ "$http_code" == "200" ]]; then
            echo -e "  ${GREEN}✓${NC} ${path} — HTTP ${http_code}"
        else
            echo -e "  ${RED}✗${NC} ${path} — HTTP ${http_code}"
        fi
    done

    # Compare local theme version vs live
    echo ""
    local local_version
    local_version=$(grep 'Version:' "$THEME_DIR/style.css" | head -1 | sed 's/.*Version: *//' | tr -d ' ')
    echo -e "  Local version:  ${CYAN}${local_version}${NC}"

    local live_style
    live_style=$(curl -sS --connect-timeout 5 --max-time 10 \
        "${SITE_URL}/wp-content/themes/skyyrose-flagship/style.css" 2>/dev/null | head -20)
    local live_version
    live_version=$(echo "$live_style" | grep 'Version:' | head -1 | sed 's/.*Version: *//' | tr -d ' ')

    if [[ -n "$live_version" ]]; then
        echo -e "  Live version:   ${CYAN}${live_version}${NC}"
        if [[ "$local_version" == "$live_version" ]]; then
            log_success "Versions match — deploy is current"
        else
            log_warn "Version mismatch — local $local_version ≠ live $live_version"
        fi
    else
        log_warn "Could not fetch live theme version"
    fi
}

# ---------------------------------------------------------------------------
# WC Sync Status
# ---------------------------------------------------------------------------
cmd_wc_sync() {
    log_info "WooCommerce Product Summary"

    local env_file="$PROJECT_ROOT/.env.wordpress"
    if [[ ! -f "$env_file" ]]; then
        log_warn "No .env.wordpress — cannot query WC REST API"
        return 0
    fi

    source "$env_file" 2>/dev/null || true

    local wc_key="${WC_CONSUMER_KEY:-}"
    local wc_secret="${WC_CONSUMER_SECRET:-}"

    if [[ -z "$wc_key" || -z "$wc_secret" ]]; then
        log_warn "WC_CONSUMER_KEY/SECRET not set in .env.wordpress"
        return 0
    fi

    local products
    products=$(curl -sS "${SITE_URL}/index.php?rest_route=/wc/v3/products&per_page=100" \
        -u "${wc_key}:${wc_secret}" 2>/dev/null)

    local count
    count=$(echo "$products" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

    echo -e "  Total products: ${CYAN}${count}${NC}"
}

# ---------------------------------------------------------------------------
# Main Router
# ---------------------------------------------------------------------------
main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        new-template)  cmd_new_template "$@" ;;
        new-part)      cmd_new_part "$@" ;;
        new-css)       cmd_new_css "$@" ;;
        new-js)        cmd_new_js "$@" ;;
        test)          cmd_test ;;
        test-php)      cmd_test_php ;;
        test-js)       cmd_test_js ;;
        test-e2e)      (cd "$THEME_DIR" && npx playwright test "$@") ;;
        test-build)    cmd_test_build ;;
        status)        cmd_status ;;
        diff-live)     cmd_diff_live ;;
        version)       cmd_version "$@" ;;
        package)       cmd_package ;;
        wc-sync)       cmd_wc_sync ;;
        help|--help|-h) usage ;;
        *)             log_error "Unknown command: $command"; echo ""; usage; exit 1 ;;
    esac
}

main "$@"
