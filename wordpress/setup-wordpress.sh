#!/bin/bash
###############################################################################
# SkyyRose WordPress Automated Setup Script
#
# This script automates the complete WordPress installation for the luxury
# ecommerce site with Three.js collections. Requires WP-CLI and WordPress admin.
#
# Usage: bash setup-wordpress.sh
#
# Author: Claude (Principal Engineer)
# Created: 2026-01-12
# Status: Production-Ready
###############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CHILD_THEME_PATH="./shoptimizer-child-theme"
COLLECTION_SLUGS=("signature" "love-hurts" "black-rose")
COLLECTION_NAMES=("SIGNATURE Collection" "LOVE HURTS Collection" "BLACK ROSE Collection")

###############################################################################
# Helper Functions
###############################################################################

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

check_wp_cli() {
    if ! command -v wp &> /dev/null; then
        log_error "WP-CLI not found. Install from https://wp-cli.org/"
        exit 1
    fi
    log_success "WP-CLI found: $(wp --version)"
}

check_wordpress() {
    if ! wp core is-installed 2>/dev/null; then
        log_error "WordPress not installed or not accessible from this directory"
        log_info "Navigate to your WordPress root directory and try again"
        exit 1
    fi
    log_success "WordPress installation detected"
}

check_parent_theme() {
    if ! wp theme is-installed shoptimizer 2>/dev/null; then
        log_warning "Parent theme 'Shoptimizer' not found"
        read -p "Install Shoptimizer theme now? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Please purchase Shoptimizer from: https://www.commercegurus.com/product/shoptimizer/"
            log_info "Then upload via WordPress Admin → Appearance → Themes → Add New → Upload Theme"
            log_error "Cannot proceed without parent theme"
            exit 1
        else
            log_error "Parent theme required. Exiting."
            exit 1
        fi
    fi
    log_success "Parent theme 'Shoptimizer' found"
}

###############################################################################
# Theme Installation
###############################################################################

install_child_theme() {
    log_info "Installing SkyyRose child theme..."

    # Check if child theme directory exists
    if [ ! -d "$CHILD_THEME_PATH" ]; then
        log_error "Child theme not found at $CHILD_THEME_PATH"
        exit 1
    fi

    # Get WordPress themes directory
    WP_THEMES_DIR=$(wp theme path)
    THEME_DEST="$WP_THEMES_DIR/shoptimizer-child-theme"

    # Copy theme files
    log_info "Copying theme files to $THEME_DEST..."
    cp -r "$CHILD_THEME_PATH" "$THEME_DEST"

    # Set proper permissions
    chmod -R 755 "$THEME_DEST"

    # Activate child theme
    wp theme activate shoptimizer-child-theme

    log_success "Child theme installed and activated"
}

###############################################################################
# Plugin Installation
###############################################################################

install_required_plugins() {
    log_info "Installing required plugins..."

    # Essential plugins
    PLUGINS=(
        "elementor"
        "woocommerce"
        "contact-form-7"
        "wordfence"
        "rank-math"
    )

    for plugin in "${PLUGINS[@]}"; do
        if wp plugin is-installed "$plugin" 2>/dev/null; then
            log_warning "Plugin '$plugin' already installed"
            wp plugin activate "$plugin" 2>/dev/null || true
        else
            log_info "Installing $plugin..."
            wp plugin install "$plugin" --activate
        fi
    done

    log_success "All required plugins installed"
}

###############################################################################
# WooCommerce Configuration
###############################################################################

configure_woocommerce() {
    log_info "Configuring WooCommerce..."

    # Set currency to USD
    wp option update woocommerce_currency 'USD'

    # Image sizes (optimized for luxury products)
    wp option update woocommerce_thumbnail_image_width 300
    wp option update woocommerce_thumbnail_cropping 'custom'
    wp option update woocommerce_thumbnail_cropping_custom_width 1
    wp option update woocommerce_thumbnail_cropping_custom_height 1

    wp option update woocommerce_single_image_width 1200
    wp option update woocommerce_gallery_thumbnail_image_width 150

    # Enable gallery features
    wp option update woocommerce_enable_lightbox 'yes'
    wp option update woocommerce_enable_product_gallery_zoom 'yes'
    wp option update woocommerce_enable_product_gallery_slider 'yes'

    # Catalog settings
    wp option update woocommerce_shop_page_display 'both'
    wp option update woocommerce_category_archive_display 'both'
    wp option update woocommerce_default_catalog_orderby 'menu_order'

    # Product reviews
    wp option update woocommerce_enable_reviews 'yes'
    wp option update woocommerce_review_rating_verification_required 'no'

    log_success "WooCommerce configured"
}

###############################################################################
# Create WooCommerce Categories
###############################################################################

create_product_categories() {
    log_info "Creating product categories..."

    # Create parent "Collections" category
    COLLECTIONS_CAT_ID=$(wp term create product_cat "Collections" --porcelain 2>/dev/null || wp term list product_cat --field=term_id --name="Collections" --format=ids)

    # Create collection categories
    for i in "${!COLLECTION_SLUGS[@]}"; do
        slug="${COLLECTION_SLUGS[$i]}"
        name="${COLLECTION_NAMES[$i]}"

        CAT_ID=$(wp term create product_cat "$name" \
            --slug="$slug" \
            --parent="$COLLECTIONS_CAT_ID" \
            --porcelain 2>/dev/null || wp term list product_cat --field=term_id --slug="$slug" --format=ids)

        log_success "Category '$name' created (ID: $CAT_ID)"
    done

    log_success "All product categories created"
}

###############################################################################
# Create Collection Pages
###############################################################################

create_collection_pages() {
    log_info "Creating collection pages..."

    # Create parent "Collections" page
    COLLECTIONS_PAGE_ID=$(wp post create \
        --post_type=page \
        --post_title="Collections" \
        --post_name="collections" \
        --post_status=publish \
        --post_content="<p>Explore our luxury collections featuring interactive 3D experiences.</p>" \
        --porcelain 2>/dev/null || wp post list --post_type=page --name="collections" --field=ID --format=ids)

    log_success "Parent 'Collections' page created (ID: $COLLECTIONS_PAGE_ID)"

    # Create collection child pages
    for i in "${!COLLECTION_SLUGS[@]}"; do
        slug="${COLLECTION_SLUGS[$i]}"
        name="${COLLECTION_NAMES[$i]}"

        # Check if page already exists
        PAGE_ID=$(wp post list --post_type=page --name="$slug" --field=ID --format=ids 2>/dev/null || echo "")

        if [ -n "$PAGE_ID" ]; then
            log_warning "Page '$name' already exists (ID: $PAGE_ID)"
        else
            # Create page content with Three.js placeholder
            CONTENT=$(cat <<EOF
<!-- Hero Section -->
<div class="collection-hero" style="height: 100vh; background: linear-gradient(135deg, rgba(183,110,121,0.1) 0%, rgba(42,26,46,0.1) 100%); display: flex; align-items: center; justify-content: center; text-align: center;">
    <div>
        <h1 style="font-size: 4rem; font-weight: 300; letter-spacing: 0.1em; margin-bottom: 1rem;">$name</h1>
        <p style="font-size: 1.5rem; font-weight: 300; opacity: 0.8;">Experience luxury in 3D</p>
    </div>
</div>

<!-- Three.js Container (to be configured in Elementor) -->
<div id="threejs-placeholder" style="background: #f5f5f0; padding: 4rem 2rem; text-align: center;">
    <h2 style="font-size: 2rem; margin-bottom: 2rem;">3D Interactive Experience</h2>
    <p style="font-size: 1.2rem; color: #666; max-width: 600px; margin: 0 auto;">
        This section will be replaced with the Three.js 3D scene using Elementor HTML widget.
        See ELEMENTOR_PAGE_TEMPLATES.md for implementation instructions.
    </p>
</div>

<!-- Product Grid (WooCommerce Shortcode) -->
<div style="padding: 4rem 2rem; max-width: 1400px; margin: 0 auto;">
    <h2 style="text-align: center; font-size: 2.5rem; margin-bottom: 3rem;">Shop the Collection</h2>
    [products limit="12" columns="4" category="$slug" orderby="menu_order"]
</div>
EOF
)

            PAGE_ID=$(wp post create \
                --post_type=page \
                --post_title="$name" \
                --post_name="$slug" \
                --post_parent="$COLLECTIONS_PAGE_ID" \
                --post_status=publish \
                --post_content="$CONTENT" \
                --porcelain)

            # Enable Elementor on this page
            wp post meta update "$PAGE_ID" "_elementor_edit_mode" "builder"

            log_success "Page '$name' created (ID: $PAGE_ID)"
        fi
    done

    log_success "All collection pages created"
}

###############################################################################
# Configure Shoptimizer Theme Settings
###############################################################################

configure_shoptimizer() {
    log_info "Configuring Shoptimizer theme settings..."

    # Get current theme mods
    THEME_MODS=$(wp option get theme_mods_shoptimizer --format=json 2>/dev/null || echo "{}")

    # Enable Shoptimizer features
    wp option patch update theme_mods_shoptimizer shoptimizer_sticky_add_to_cart true --format=json
    wp option patch update theme_mods_shoptimizer shoptimizer_product_trust_badges true --format=json
    wp option patch update theme_mods_shoptimizer shoptimizer_distraction_free_checkout true --format=json
    wp option patch update theme_mods_shoptimizer shoptimizer_cart_slider true --format=json

    # Set brand colors
    wp option patch update theme_mods_shoptimizer primary_color '#B76E79' --format=json
    wp option patch update theme_mods_shoptimizer secondary_color '#2a1a2e' --format=json

    log_success "Shoptimizer configured with SkyyRose brand colors"
}

###############################################################################
# Create Sample Products
###############################################################################

create_sample_products() {
    log_info "Creating sample products..."

    # Sample products for each collection
    declare -A PRODUCTS=(
        ["signature"]="Signature Rose Hoodie,Signature Rose Tee,Signature Rose Joggers"
        ["love-hurts"]="Love Hurts Windbreaker,Love Hurts Hoodie,Love Hurts Joggers"
        ["black-rose"]="Black Rose Sherpa,Black Rose Hooded Dress,Black Rose Joggers"
    )

    for collection in "${!PRODUCTS[@]}"; do
        IFS=',' read -ra PRODUCT_NAMES <<< "${PRODUCTS[$collection]}"

        for product_name in "${PRODUCT_NAMES[@]}"; do
            # Check if product exists
            EXISTING=$(wp post list --post_type=product --title="$product_name" --field=ID --format=ids 2>/dev/null || echo "")

            if [ -n "$EXISTING" ]; then
                log_warning "Product '$product_name' already exists"
                continue
            fi

            # Create product
            PRODUCT_ID=$(wp post create \
                --post_type=product \
                --post_title="$product_name" \
                --post_status=publish \
                --post_content="<p>Premium quality $product_name from the SkyyRose $collection collection.</p>" \
                --porcelain)

            # Set product meta
            wp post meta update "$PRODUCT_ID" _regular_price "89.99"
            wp post meta update "$PRODUCT_ID" _price "89.99"
            wp post meta update "$PRODUCT_ID" _stock_status "instock"
            wp post meta update "$PRODUCT_ID" _manage_stock "yes"
            wp post meta update "$PRODUCT_ID" _stock "50"

            # Assign to category
            CAT_ID=$(wp term list product_cat --slug="$collection" --field=term_id --format=ids)
            wp post term set "$PRODUCT_ID" product_cat "$CAT_ID"

            log_success "Product '$product_name' created (ID: $PRODUCT_ID)"
        done
    done

    log_success "Sample products created"
}

###############################################################################
# Setup Permalinks
###############################################################################

configure_permalinks() {
    log_info "Configuring permalinks..."

    # Set to post name structure
    wp rewrite structure '/%postname%/'
    wp rewrite flush

    # WooCommerce permalinks
    wp option update woocommerce_permalinks '{"product_base":"product","category_base":"product-category","tag_base":"product-tag","attribute_base":"","use_verbose_page_rules":true}' --format=json

    log_success "Permalinks configured"
}

###############################################################################
# Create Essential Pages
###############################################################################

create_essential_pages() {
    log_info "Creating essential pages..."

    # Homepage
    HOME_ID=$(wp post create \
        --post_type=page \
        --post_title="Home" \
        --post_name="home" \
        --post_status=publish \
        --post_content="<p>Welcome to SkyyRose - Luxury fashion with immersive 3D experiences.</p>" \
        --porcelain 2>/dev/null || wp post list --post_type=page --name="home" --field=ID --format=ids)

    # Set as front page
    wp option update show_on_front 'page'
    wp option update page_on_front "$HOME_ID"

    # Blog page
    BLOG_ID=$(wp post create \
        --post_type=page \
        --post_title="Blog" \
        --post_name="blog" \
        --post_status=publish \
        --porcelain 2>/dev/null || wp post list --post_type=page --name="blog" --field=ID --format=ids)

    wp option update page_for_posts "$BLOG_ID"

    # About page
    wp post create \
        --post_type=page \
        --post_title="About Us" \
        --post_name="about" \
        --post_status=publish \
        --post_content="<p>Learn about SkyyRose - Where luxury meets innovation.</p>" \
        2>/dev/null || log_warning "About page may already exist"

    log_success "Essential pages created"
}

###############################################################################
# Main Execution
###############################################################################

main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     SkyyRose WordPress Automated Setup Script             ║"
    echo "║     Enterprise-Grade Luxury Ecommerce Installation        ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    # Pre-flight checks
    log_info "Running pre-flight checks..."
    check_wp_cli
    check_wordpress
    check_parent_theme

    echo ""
    log_warning "This script will modify your WordPress installation."
    log_warning "Make sure you have a backup before proceeding."
    echo ""
    read -p "Continue with installation? (y/n): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled by user"
        exit 0
    fi

    echo ""
    log_info "Starting installation..."
    echo ""

    # Execute setup steps
    install_child_theme
    install_required_plugins
    configure_woocommerce
    create_product_categories
    create_collection_pages
    configure_shoptimizer
    create_sample_products
    configure_permalinks
    create_essential_pages

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                 🎉 Setup Complete! 🎉                      ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_success "WordPress site configured successfully"
    echo ""
    log_info "Next Steps:"
    echo "  1. Log into WordPress Admin"
    echo "  2. Configure Elementor on collection pages (see ELEMENTOR_PAGE_TEMPLATES.md)"
    echo "  3. Upload product images (see PRODUCT_IMAGERY_GUIDE.md)"
    echo "  4. Test Three.js scenes on each collection page"
    echo "  5. Run testing checklist (see TESTING_PLAN.md)"
    echo ""
    log_info "Documentation: /Users/coreyfoster/DevSkyy/wordpress/"
    echo ""
}

# Execute main function
main "$@"
