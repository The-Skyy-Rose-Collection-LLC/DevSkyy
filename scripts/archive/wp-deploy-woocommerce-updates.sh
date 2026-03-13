#!/bin/bash
# =============================================================================
# Deploy WooCommerce Template Updates & Minified CSS
# =============================================================================
#
# Syncs updated WooCommerce template overrides and minified CSS files
# from the local repo to the WordPress installation via SSH/SFTP or locally.
#
# Updated templates:
#   - archive-product.php       (v8.6.0 - new woocommerce_shop_loop_header hook)
#   - cart/cart.php              (v10.1.0 - new hooks, a11y, sold_individually)
#   - checkout/form-checkout.php (v9.4.0 - aria-label, registration check)
#   - content-product.php        (v9.4.0 - type-safe is_a() check)
#   - single-product.php         (v1.6.4 - version tag update)
#
# Also deploys:
#   - 4 minified CSS files (woocommerce*.min.css)
#   - Updated enqueue.php (auto-loads .min.css in production)
#
# Usage:
#   ./scripts/wp-deploy-woocommerce-updates.sh --ssh user@host:/path/to/wp
#   ./scripts/wp-deploy-woocommerce-updates.sh --local /path/to/wp
#   ./scripts/wp-deploy-woocommerce-updates.sh --dry-run --ssh user@host:/path
#
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
THEME_NAME="skyyrose-flagship"

DRY_RUN=false
WP_PATH=""
SSH_TARGET=""
SKIP_CACHE_FLUSH=false

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Run WP-CLI on target
wp_cmd() {
    if [[ -n "$SSH_TARGET" ]]; then
        ssh "$SSH_TARGET" "cd $WP_PATH && wp $*"
    else
        cd "$WP_PATH" && wp "$@"
    fi
}

# Copy file to target
deploy_file() {
    local src="$1"
    local dest_relative="$2"

    if [[ ! -f "$src" ]]; then
        log_error "Source not found: $src"
        return 1
    fi

    local dest
    if [[ -n "$SSH_TARGET" ]]; then
        dest="$SSH_TARGET:$WP_PATH/wp-content/themes/$THEME_NAME/$dest_relative"
    else
        dest="$WP_PATH/wp-content/themes/$THEME_NAME/$dest_relative"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] $dest_relative"
        return 0
    fi

    if [[ -n "$SSH_TARGET" ]]; then
        # Ensure remote directory exists
        local remote_dir
        remote_dir=$(dirname "$WP_PATH/wp-content/themes/$THEME_NAME/$dest_relative")
        ssh "$SSH_TARGET" "mkdir -p $remote_dir"
        scp -q "$src" "$dest"
    else
        local local_dir
        local_dir=$(dirname "$dest")
        mkdir -p "$local_dir"
        cp "$src" "$dest"
    fi

    log_success "$dest_relative"
}

# =============================================================================
# Main
# =============================================================================

deploy_woocommerce_updates() {
    echo ""
    echo "=========================================="
    echo "  SKYYROSE WOOCOMMERCE UPDATE DEPLOYMENT"
    echo "=========================================="
    echo ""

    # ---- WooCommerce Template Overrides ----
    log_info "Deploying WooCommerce template overrides..."

    local wc_templates=(
        "woocommerce/archive-product.php"
        "woocommerce/cart/cart.php"
        "woocommerce/checkout/form-checkout.php"
        "woocommerce/content-product.php"
        "woocommerce/single-product.php"
    )

    for tpl in "${wc_templates[@]}"; do
        deploy_file "$THEME_DIR/$tpl" "$tpl"
    done

    echo ""

    # ---- Minified CSS ----
    log_info "Deploying minified CSS..."

    local css_files=(
        "assets/css/woocommerce.min.css"
        "assets/css/woocommerce-cart.min.css"
        "assets/css/woocommerce-checkout.min.css"
        "assets/css/woocommerce-single.min.css"
    )

    for css in "${css_files[@]}"; do
        deploy_file "$THEME_DIR/$css" "$css"
    done

    echo ""

    # ---- Enqueue (minified CSS loader) ----
    log_info "Deploying updated enqueue.php..."
    deploy_file "$THEME_DIR/inc/enqueue.php" "inc/enqueue.php"

    echo ""

    # ---- Flush caches ----
    if [[ "$DRY_RUN" == "false" && "$SKIP_CACHE_FLUSH" == "false" ]]; then
        log_info "Flushing WordPress caches..."
        wp_cmd cache flush 2>/dev/null && log_success "Object cache flushed" || log_warn "Cache flush skipped (WP-CLI not available)"
        wp_cmd transient delete --all 2>/dev/null && log_success "Transients cleared" || true
    fi

    echo ""
    echo "=========================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN complete — no files were changed"
    else
        log_success "DEPLOYMENT COMPLETE (10 files)"
        echo ""
        echo "  Templates:  5 WooCommerce overrides (v8.6.0 - v10.1.0)"
        echo "  CSS:        4 minified stylesheets"
        echo "  PHP:        1 enqueue.php (auto .min.css loading)"
    fi
    echo "=========================================="
    echo ""
}

# =============================================================================
# CLI
# =============================================================================

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --local PATH        Path to local WordPress installation"
    echo "  --ssh TARGET        SSH target (user@host:/path/to/wordpress)"
    echo "  --dry-run           Preview files without deploying"
    echo "  --skip-cache-flush  Skip WP cache flush after deploy"
    echo "  --help              Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run --local /var/www/html/wordpress"
    echo "  $0 --ssh root@skyyrose.co:/var/www/html"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --local)
            WP_PATH="$2"
            shift 2
            ;;
        --ssh)
            SSH_TARGET="${2%%:*}"
            WP_PATH="${2#*:}"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-cache-flush)
            SKIP_CACHE_FLUSH=true
            shift
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

if [[ -z "$WP_PATH" ]]; then
    log_error "WordPress path required. Use --local or --ssh."
    echo ""
    print_usage
    exit 1
fi

deploy_woocommerce_updates
