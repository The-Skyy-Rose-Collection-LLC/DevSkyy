#!/bin/bash
# =============================================================================
# WP-CLI Elementor Template Deployment Script
# =============================================================================
#
# This script deploys Elementor templates to WordPress using WP-CLI.
# WP-CLI provides direct database access, bypassing REST API meta field limits.
#
# Prerequisites:
#   - WP-CLI installed (https://wp-cli.org/)
#   - SSH access to WordPress server OR local WordPress installation
#   - Elementor Pro activated on WordPress site
#
# Usage:
#   # Local WordPress installation
#   ./scripts/wp-cli-deploy-templates.sh --local /path/to/wordpress
#
#   # Remote via SSH
#   ./scripts/wp-cli-deploy-templates.sh --ssh user@host:/path/to/wordpress
#
#   # Dry run (preview only)
#   ./scripts/wp-cli-deploy-templates.sh --dry-run --local /path/to/wordpress
#
# Author: DevSkyy Platform Team
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$PROJECT_ROOT/wordpress/elementor_templates"
CSS_DIR="$PROJECT_ROOT/wordpress/skyyrose-immersive/assets/css"

# Configuration
DRY_RUN=false
WP_PATH=""
SSH_TARGET=""

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Execute WP-CLI command (local or remote)
wp_cmd() {
    if [[ -n "$SSH_TARGET" ]]; then
        ssh "$SSH_TARGET" "cd $WP_PATH && wp $*"
    else
        cd "$WP_PATH" && wp "$@"
    fi
}

# Validate template file
validate_template() {
    local template_file="$1"

    if [[ ! -f "$template_file" ]]; then
        log_error "Template not found: $template_file"
        return 1
    fi

    # Check file size (max 5MB)
    local size=$(stat -f%z "$template_file" 2>/dev/null || stat -c%s "$template_file")
    if [[ $size -gt 5242880 ]]; then
        log_error "Template too large: $template_file ($size bytes)"
        return 1
    fi

    # Validate JSON
    if ! jq empty "$template_file" 2>/dev/null; then
        log_error "Invalid JSON: $template_file"
        return 1
    fi

    return 0
}

# =============================================================================
# Template Mapping
# =============================================================================

declare -A PAGE_TEMPLATES=(
    ["home"]="home.json"
    ["experiences"]="collections.json"
    ["signature"]="signature.json"
    ["black-rose"]="black_rose.json"
    ["love-hurts"]="love_hurts.json"
    ["about"]="about.json"
)

declare -A PAGE_TITLES=(
    ["home"]="Home"
    ["experiences"]="3D Experiences"
    ["signature"]="SIGNATURE Collection"
    ["black-rose"]="BLACK ROSE Collection"
    ["love-hurts"]="LOVE HURTS Collection"
    ["about"]="About SkyyRose"
)

# =============================================================================
# Deployment Functions
# =============================================================================

# Get or create page by slug
get_or_create_page() {
    local slug="$1"
    local title="$2"
    local parent_id="${3:-0}"

    # Check if page exists
    local page_id=$(wp_cmd post list --post_type=page --name="$slug" --field=ID 2>/dev/null || echo "")

    if [[ -z "$page_id" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would create page: $slug"
            echo "NEW"
            return
        fi

        # Create new page
        page_id=$(wp_cmd post create \
            --post_type=page \
            --post_title="$title" \
            --post_name="$slug" \
            --post_status=publish \
            --post_parent="$parent_id" \
            --porcelain)

        log_success "Created page: $slug (ID: $page_id)"
    else
        log_info "Page exists: $slug (ID: $page_id)"
    fi

    echo "$page_id"
}

# Import Elementor template to page
import_template() {
    local page_id="$1"
    local template_file="$2"
    local slug="$3"

    if [[ "$page_id" == "NEW" ]]; then
        return 0
    fi

    # Validate template
    if ! validate_template "$template_file"; then
        return 1
    fi

    # Extract content array from template
    local elementor_data=$(jq -c '.content' "$template_file")

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would import template to page $page_id: $template_file"
        return 0
    fi

    # Update Elementor meta fields
    wp_cmd post meta update "$page_id" _elementor_data "$elementor_data"
    wp_cmd post meta update "$page_id" _elementor_edit_mode "builder"
    wp_cmd post meta update "$page_id" _elementor_template_type "wp-page"
    wp_cmd post meta update "$page_id" _elementor_version "3.32.0"

    log_success "Imported template to page $page_id: $slug"
}

# Import via Elementor CLI (if available)
import_via_elementor_cli() {
    local template_file="$1"

    # Check if Elementor CLI is available
    if ! wp_cmd elementor --version &>/dev/null; then
        log_warning "Elementor CLI not available, using direct meta update"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would import via Elementor CLI: $template_file"
        return 0
    fi

    wp_cmd elementor library import "$template_file" --returnType=ids
    return 0
}

# Inject custom CSS
inject_css() {
    local css_files=("$@")
    local combined_css=""

    for css_file in "${css_files[@]}"; do
        local css_path="$CSS_DIR/$css_file"
        if [[ -f "$css_path" ]]; then
            combined_css+="/* === $css_file === */\n"
            combined_css+=$(cat "$css_path")
            combined_css+="\n\n"
            log_info "Loaded CSS: $css_file"
        else
            log_warning "CSS file not found: $css_file"
        fi
    done

    if [[ -z "$combined_css" ]]; then
        log_warning "No CSS files to inject"
        return 0
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would inject ${#combined_css} chars of CSS"
        return 0
    fi

    # Get or create custom_css post
    local css_post_id=$(wp_cmd post list --post_type=custom_css --posts_per_page=1 --field=ID 2>/dev/null || echo "")

    if [[ -z "$css_post_id" ]]; then
        css_post_id=$(wp_cmd post create \
            --post_type=custom_css \
            --post_status=publish \
            --post_content="$combined_css" \
            --porcelain)
        log_success "Created custom CSS post: $css_post_id"
    else
        wp_cmd post update "$css_post_id" --post_content="$combined_css"
        log_success "Updated custom CSS post: $css_post_id"
    fi
}

# =============================================================================
# Main Deployment
# =============================================================================

deploy_all() {
    log_info "Starting deployment..."
    echo "=========================================="
    echo "  SKYYROSE TEMPLATE DEPLOYMENT"
    echo "=========================================="

    # Create parent pages first
    log_info "Creating/verifying parent pages..."

    local experiences_id=$(get_or_create_page "experiences" "3D Experiences")

    # Deploy each page
    for slug in "${!PAGE_TEMPLATES[@]}"; do
        local template="${PAGE_TEMPLATES[$slug]}"
        local title="${PAGE_TITLES[$slug]}"
        local template_path="$TEMPLATES_DIR/$template"
        local parent_id=0

        # Set parent for collection pages
        case "$slug" in
            signature|black-rose|love-hurts)
                parent_id="$experiences_id"
                ;;
        esac

        log_info "Processing: $slug"

        # Get or create page
        local page_id=$(get_or_create_page "$slug" "$title" "$parent_id")

        # Import template
        if [[ -f "$template_path" ]]; then
            import_template "$page_id" "$template_path" "$slug"
        else
            log_warning "Template not found for $slug: $template_path"
        fi

        echo ""
    done

    # Inject CSS
    log_info "Injecting custom CSS..."
    inject_css "luxury-design-system.css" "luxury-overrides.css" "immersive.css"

    echo ""
    echo "=========================================="
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "DRY RUN complete - no changes made"
    else
        log_success "DEPLOYMENT COMPLETE"
    fi
    echo "=========================================="
}

# =============================================================================
# CLI Argument Parsing
# =============================================================================

print_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --local PATH      Path to local WordPress installation"
    echo "  --ssh TARGET      SSH target (user@host:/path/to/wordpress)"
    echo "  --dry-run         Preview changes without deploying"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --dry-run --local /var/www/html/wordpress"
    echo "  $0 --ssh root@skyyrose.co:/var/www/html"
}

# Parse arguments
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

# Validate configuration
if [[ -z "$WP_PATH" ]]; then
    log_error "WordPress path not specified"
    print_usage
    exit 1
fi

# Run deployment
deploy_all
