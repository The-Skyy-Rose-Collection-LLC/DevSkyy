#!/bin/bash
#
# SkyyRose 2025 Theme Deployment Script
# Automated WordPress theme deployment using WP-CLI
#
# Based on Context7 WP-CLI documentation:
# - https://github.com/wp-cli/handbook/blob/main/commands/theme/activate.md
# - https://github.com/wp-cli/handbook/blob/main/commands/post/create.md
# - https://github.com/wp-cli/handbook/blob/main/commands/menu.md
# - https://github.com/wp-cli/handbook/blob/main/commands/option/update.md
#
# Version: 2.0.0
# Author: SkyyRose LLC
# Date: 2026-01-31

set -e  # Exit on error

# Configuration
WP_PATH="/Users/coreyfoster/Studio/the-skyy-rose-collection"
WP_CLI="/Users/coreyfoster/DevSkyy/wordpress-theme/wp-cli.phar"
THEME_NAME="skyyrose-2025"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to run WP-CLI
wp() {
    php "$WP_CLI" --path="$WP_PATH" "$@" 2>&1 | grep -v "Deprecated:" || true
}

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  SkyyRose 2025 Theme Deployment${NC}"
echo -e "${BLUE}  Where Love Meets Luxury${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Step 1: Activate Theme
echo -e "${YELLOW}[1/9]${NC} Activating SkyyRose 2025 theme..."
wp theme activate $THEME_NAME
echo -e "${GREEN}✓ Theme activated${NC}"
echo ""

# Step 2: Install and Activate WooCommerce
echo -e "${YELLOW}[2/9]${NC} Installing WooCommerce plugin..."
if wp plugin is-installed woocommerce 2>/dev/null; then
    echo "  WooCommerce already installed"
    wp plugin activate woocommerce
else
    wp plugin install woocommerce --activate
fi
echo -e "${GREEN}✓ WooCommerce activated${NC}"
echo ""

# Step 3: Install and Activate Elementor
echo -e "${YELLOW}[3/9]${NC} Installing Elementor plugin..."
if wp plugin is-installed elementor 2>/dev/null; then
    echo "  Elementor already installed"
    wp plugin activate elementor
else
    wp plugin install elementor --activate
fi
echo -e "${GREEN}✓ Elementor activated${NC}"
echo ""

# Step 4: Create Pages with Templates
echo -e "${YELLOW}[4/9]${NC} Creating pages with custom templates..."

# Home Page
HOME_ID=$(wp post create --post_type=page --post_title="Home" \
    --post_content="Welcome to SkyyRose - Where Love Meets Luxury" \
    --post_status=publish --porcelain)
wp post meta add $HOME_ID _wp_page_template template-home.php
echo -e "  ${GREEN}✓${NC} Created Home page (ID: $HOME_ID)"

# Black Rose Page
BLACK_ROSE_ID=$(wp post create --post_type=page --post_title="Black Rose" \
    --post_content="Enter the futuristic rose garden" \
    --post_status=publish --porcelain)
wp post meta add $BLACK_ROSE_ID _wp_page_template template-immersive.php
wp post meta add $BLACK_ROSE_ID _collection_type black-rose
echo -e "  ${GREEN}✓${NC} Created Black Rose page (ID: $BLACK_ROSE_ID)"

# Love Hurts Page
LOVE_HURTS_ID=$(wp post create --post_type=page --post_title="Love Hurts" \
    --post_content="Experience the enchanted castle" \
    --post_status=publish --porcelain)
wp post meta add $LOVE_HURTS_ID _wp_page_template template-immersive.php
wp post meta add $LOVE_HURTS_ID _collection_type love-hurts
echo -e "  ${GREEN}✓${NC} Created Love Hurts page (ID: $LOVE_HURTS_ID)"

# Signature Page
SIGNATURE_ID=$(wp post create --post_type=page --post_title="Signature" \
    --post_content="Walk the golden runway" \
    --post_status=publish --porcelain)
wp post meta add $SIGNATURE_ID _wp_page_template template-immersive.php
wp post meta add $SIGNATURE_ID _collection_type signature
echo -e "  ${GREEN}✓${NC} Created Signature page (ID: $SIGNATURE_ID)"

# Collections Page
COLLECTIONS_ID=$(wp post create --post_type=page --post_title="Collections" \
    --post_content="Browse our luxury collections" \
    --post_status=publish --porcelain)
wp post meta add $COLLECTIONS_ID _wp_page_template template-collection.php
echo -e "  ${GREEN}✓${NC} Created Collections page (ID: $COLLECTIONS_ID)"

# The Vault Page
VAULT_ID=$(wp post create --post_type=page --post_title="The Vault" \
    --post_content="Pre-order exclusive pieces" \
    --post_status=publish --porcelain)
wp post meta add $VAULT_ID _wp_page_template template-vault.php
echo -e "  ${GREEN}✓${NC} Created The Vault page (ID: $VAULT_ID)"

echo ""

# Step 5: Set Homepage
echo -e "${YELLOW}[5/9]${NC} Setting static front page..."
wp option update show_on_front page
wp option update page_on_front $HOME_ID
echo -e "${GREEN}✓ Homepage configured${NC}"
echo ""

# Step 6: Create Navigation Menu
echo -e "${YELLOW}[6/9]${NC} Creating primary navigation menu..."

# Create menu
MENU_ID=$(wp menu create "Primary Menu" --porcelain)
echo "  Created menu (ID: $MENU_ID)"

# Add menu items
wp menu item add-post $MENU_ID $HOME_ID --title="Home"
wp menu item add-post $MENU_ID $BLACK_ROSE_ID --title="Black Rose"
wp menu item add-post $MENU_ID $LOVE_HURTS_ID --title="Love Hurts"
wp menu item add-post $MENU_ID $SIGNATURE_ID --title="Signature"
wp menu item add-post $MENU_ID $COLLECTIONS_ID --title="Collections"
wp menu item add-post $MENU_ID $VAULT_ID --title="The Vault"

# Assign to primary location
wp menu location assign $MENU_ID primary

echo -e "${GREEN}✓ Navigation menu created and assigned${NC}"
echo ""

# Step 7: Configure Theme Customizer
echo -e "${YELLOW}[7/9]${NC} Configuring theme customizer settings..."
wp option update theme_mods_$THEME_NAME --format=json <<'JSON'
{
  "skyyrose_brand_name": "SkyyRose",
  "skyyrose_tagline": "Where Love Meets Luxury",
  "skyyrose_collection_black_rose_color": "#8B0000",
  "skyyrose_collection_love_hurts_color": "#B76E79",
  "skyyrose_collection_signature_color": "#D4AF37"
}
JSON
echo -e "${GREEN}✓ Theme customizer configured${NC}"
echo ""

# Step 8: Configure WooCommerce
echo -e "${YELLOW}[8/9]${NC} Configuring WooCommerce settings..."
wp option update woocommerce_store_address "Oakland"
wp option update woocommerce_store_city "Oakland"
wp option update woocommerce_default_country "US:CA"
wp option update woocommerce_currency "USD"
wp option update woocommerce_enable_reviews "yes"
echo -e "${GREEN}✓ WooCommerce configured${NC}"
echo ""

# Step 9: Create Product Categories
echo -e "${YELLOW}[9/9]${NC} Creating WooCommerce product categories..."

# Create categories
wp term create product_cat "Black Rose" \
    --slug=black-rose \
    --description="Futuristic gothic streetwear with metallic accents"

wp term create product_cat "Love Hurts" \
    --slug=love-hurts \
    --description="Romantic rebellion - where beauty meets pain"

wp term create product_cat "Signature" \
    --slug=signature \
    --description="Timeless luxury with golden details"

echo -e "${GREEN}✓ Product categories created${NC}"
echo ""

# Final Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Theme:${NC} SkyyRose 2025 activated"
echo -e "${GREEN}Plugins:${NC} WooCommerce, Elementor activated"
echo -e "${GREEN}Pages Created:${NC} 6 pages with custom templates"
echo -e "${GREEN}Homepage:${NC} Set to Home page"
echo -e "${GREEN}Menu:${NC} Primary navigation configured"
echo -e "${GREEN}Categories:${NC} 3 product categories created"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Visit homepage: http://localhost:8881"
echo "2. Edit pages with Elementor"
echo "3. Add products to WooCommerce"
echo "4. Customize theme in Appearance > Customize"
echo ""
echo -e "${YELLOW}SkyyRose 2025 v2.0.0${NC}"
echo -e "${YELLOW}Where Love Meets Luxury${NC}"
echo ""
