#!/bin/bash

###############################################################################
# Local WordPress Setup Script for SkyyRose Theme
#
# This script automates the complete WordPress setup for testing:
# - Installs WooCommerce
# - Creates product categories
# - Creates 3D immersive pages
# - Creates sample products with 3D positions
# - Configures permalinks
#
# Usage: bash scripts/setup-local-wordpress.sh
#
# Prerequisites:
# - WordPress installed at http://skyyrose.local
# - SkyyRose theme activated
# - WP-CLI available
#
# @package SkyyRose_Flagship
# @since 1.0.0
###############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║     SkyyRose Theme - Local WordPress Setup Script           ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if WP-CLI is available
if ! command -v wp &> /dev/null; then
    echo -e "${RED}✗ WP-CLI not found${NC}"
    echo ""
    echo "Please install WP-CLI or run this script from Local's site shell:"
    echo "  1. Right-click site in Local"
    echo "  2. Click 'Open site shell'"
    echo "  3. Run: bash scripts/setup-local-wordpress.sh"
    exit 1
fi

echo -e "${GREEN}✓ WP-CLI found${NC}"
echo ""

###############################################################################
# Step 1: Install and Activate WooCommerce
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 1: Installing WooCommerce${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if WooCommerce is already installed
if wp plugin is-installed woocommerce; then
    echo -e "${YELLOW}⚠ WooCommerce already installed${NC}"
    if wp plugin is-active woocommerce; then
        echo -e "${GREEN}✓ WooCommerce is active${NC}"
    else
        wp plugin activate woocommerce
        echo -e "${GREEN}✓ WooCommerce activated${NC}"
    fi
else
    wp plugin install woocommerce --activate
    echo -e "${GREEN}✓ WooCommerce installed and activated${NC}"
fi

echo ""

###############################################################################
# Step 2: Create Product Categories
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 2: Creating Product Categories${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Define categories
declare -A categories=(
    ["signature-collection"]="Signature Collection|Luxury rose arrangements in glass pavilion"
    ["love-hurts"]="Love Hurts|Gothic romance collection in enchanted castle"
    ["black-rose"]="Black Rose|Dark elegance collection in cathedral garden"
    ["preorder"]="Preorder|Upcoming exclusive releases"
)

for slug in "${!categories[@]}"; do
    IFS='|' read -r name description <<< "${categories[$slug]}"

    # Check if category exists
    if wp term list product_cat --slug="$slug" --format=count | grep -q "1"; then
        echo -e "${YELLOW}⚠ Category '$name' already exists${NC}"
    else
        wp term create product_cat "$name" --slug="$slug" --description="$description"
        echo -e "${GREEN}✓ Created category: $name${NC}"
    fi
done

echo ""

###############################################################################
# Step 3: Create 3D Immersive Pages
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 3: Creating 3D Immersive Pages${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Define pages with their templates
declare -A pages=(
    ["signature-collection-3d"]="Signature Collection 3D|template-signature-collection.php"
    ["love-hurts-3d"]="Love Hurts 3D|template-love-hurts.php"
    ["black-rose-3d"]="Black Rose 3D|template-black-rose.php"
    ["preorder-gateway-3d"]="Preorder Gateway 3D|template-preorder-gateway.php"
)

for slug in "${!pages[@]}"; do
    IFS='|' read -r title template <<< "${pages[$slug]}"

    # Check if page exists
    if wp post list --post_type=page --name="$slug" --format=count | grep -q "1"; then
        echo -e "${YELLOW}⚠ Page '$title' already exists${NC}"
        # Update template
        page_id=$(wp post list --post_type=page --name="$slug" --format=ids)
        wp post meta update "$page_id" _wp_page_template "$template"
        echo -e "${GREEN}  ✓ Template updated${NC}"
    else
        wp post create \
            --post_type=page \
            --post_title="$title" \
            --post_name="$slug" \
            --post_status=publish \
            --meta_input='{"_wp_page_template":"'"$template"'"}'
        echo -e "${GREEN}✓ Created page: $title${NC}"
    fi
done

echo ""

###############################################################################
# Step 4: Configure Permalinks
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 4: Configuring Permalinks${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

wp rewrite structure '/%postname%/' --hard
wp rewrite flush --hard
echo -e "${GREEN}✓ Permalinks set to post name${NC}"

echo ""

###############################################################################
# Step 5: Create Sample Products
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 5: Creating Sample Products${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Sample products data
# Format: category|product_name|price|x|y|z
declare -a products=(
    "signature-collection|Luxury Rose Bouquet|299|5.0|2.0|-3.0"
    "signature-collection|Premium Garden Arrangement|399|3.0|1.5|2.0"
    "signature-collection|Signature Rose Collection|499|-4.0|2.5|0.0"

    "love-hurts|Gothic Romance Bouquet|349|6.0|3.0|-2.0"
    "love-hurts|Enchanted Castle Rose|449|-3.0|2.0|4.0"
    "love-hurts|Love's Thorn Collection|549|0.0|4.0|-5.0"

    "black-rose|Dark Elegance Bouquet|379|4.5|1.8|-4.0"
    "black-rose|Midnight Rose Arrangement|479|-5.0|2.2|3.0"
    "black-rose|Cathedral Garden Collection|579|2.0|3.5|-1.0"

    "preorder|Exclusive Preview Collection|599|0.0|2.0|0.0"
    "preorder|Limited Edition Rose Set|699|-2.0|3.0|3.0"
)

for product_data in "${products[@]}"; do
    IFS='|' read -r category name price x y z <<< "$product_data"

    # Check if product exists
    if wp post list --post_type=product --title="$name" --format=count | grep -q "1"; then
        echo -e "${YELLOW}⚠ Product '$name' already exists${NC}"
    else
        # Create product
        product_id=$(wp wc product create \
            --name="$name" \
            --type=simple \
            --regular_price="$price" \
            --status=publish \
            --user=1 \
            --porcelain)

        # Add to category
        category_id=$(wp term list product_cat --slug="$category" --field=term_id)
        wp wc product update "$product_id" --categories="[{\"id\":$category_id}]" --user=1

        # Add 3D position metadata
        wp post meta update "$product_id" _3d_position_x "$x"
        wp post meta update "$product_id" _3d_position_y "$y"
        wp post meta update "$product_id" _3d_position_z "$z"

        echo -e "${GREEN}✓ Created: $name (${category})${NC}"
        echo -e "  Position: X=$x, Y=$y, Z=$z"
    fi
done

echo ""

###############################################################################
# Step 6: Configure WooCommerce Settings
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 6: Configuring WooCommerce Settings${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Disable WooCommerce onboarding wizard
wp option update woocommerce_task_list_hidden yes
wp option update woocommerce_onboarding_opt_in no

# Set currency
wp option update woocommerce_currency USD

# Enable guest checkout
wp option update woocommerce_enable_guest_checkout yes

# Disable reviews (optional)
wp option update woocommerce_enable_reviews no

echo -e "${GREEN}✓ WooCommerce settings configured${NC}"

echo ""

###############################################################################
# Step 7: Verify REST API
###############################################################################
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Step 7: Verifying REST API${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test REST API endpoint
site_url=$(wp option get siteurl)
api_url="$site_url/wp-json/skyyrose/v1/products/3d/signature-collection"

echo -e "Testing: ${BLUE}$api_url${NC}"

if curl -s "$api_url" | grep -q "id"; then
    echo -e "${GREEN}✓ REST API responding correctly${NC}"
else
    echo -e "${YELLOW}⚠ REST API may not be configured${NC}"
    echo -e "  Verify /inc/woocommerce.php contains REST API registration"
fi

echo ""

###############################################################################
# Final Summary
###############################################################################
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║                   Setup Complete!                            ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

echo -e "${GREEN}✅ WordPress setup complete!${NC}"
echo ""
echo "Test URLs:"
echo -e "  ${BLUE}$site_url${NC}"
echo -e "  ${BLUE}$site_url/signature-collection-3d/${NC}"
echo -e "  ${BLUE}$site_url/love-hurts-3d/${NC}"
echo -e "  ${BLUE}$site_url/black-rose-3d/${NC}"
echo -e "  ${BLUE}$site_url/preorder-gateway-3d/${NC}"
echo ""
echo "Archive Pages:"
echo -e "  ${BLUE}$site_url/product-category/signature-collection/${NC}"
echo -e "  ${BLUE}$site_url/product-category/love-hurts/${NC}"
echo -e "  ${BLUE}$site_url/product-category/black-rose/${NC}"
echo -e "  ${BLUE}$site_url/product-category/preorder/${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open site in browser to verify 3D scenes load"
echo "2. Run validation tests: bash scripts/validate-theme-complete.sh"
echo "3. Check console for any JavaScript errors"
echo ""
