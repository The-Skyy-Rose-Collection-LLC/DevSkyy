#!/bin/bash
###############################################################################
# SkyyRose 2025 WordPress Theme - WP-CLI Deployment Script
#
# Usage:
#   ./deploy-wpcli.sh [environment] [wp-path]
#
# Examples:
#   ./deploy-wpcli.sh production /var/www/html
#   ./deploy-wpcli.sh staging ~/public_html
#
# Requirements:
#   - WP-CLI installed (https://wp-cli.org/)
#   - SSH access to WordPress server
#   - WordPress 6.4+, PHP 8.1+, WooCommerce 8.0+
#
# Author: SkyyRose Team
# Version: 3.0.0
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
THEME_NAME="skyyrose-2025"
THEME_VERSION="3.0.0"
ENV="${1:-production}"
WP_PATH="${2:-/var/www/html}"

echo -e "${BLUE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███████╗██╗  ██╗██╗   ██╗██╗   ██╗██████╗  ██████╗    ║
║   ██╔════╝██║ ██╔╝╚██╗ ██╔╝╚██╗ ██╔╝██╔══██╗██╔═══██╗   ║
║   ███████╗█████╔╝  ╚████╔╝  ╚████╔╝ ██████╔╝██║   ██║   ║
║   ╚════██║██╔═██╗   ╚██╔╝    ╚██╔╝  ██╔══██╗██║   ██║   ║
║   ███████║██║  ██╗   ██║      ██║   ██║  ██║╚██████╔╝   ║
║   ╚══════╝╚═╝  ╚═╝   ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ║
║                                                           ║
║              WP-CLI Deployment Script v3.0.0             ║
║              Oakland Soul. Luxury Heart.                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}Deployment Configuration:${NC}"
echo "  Environment: $ENV"
echo "  Theme: $THEME_NAME v$THEME_VERSION"
echo "  WordPress Path: $WP_PATH"
echo ""

# Check if WP-CLI is installed
if ! command -v wp &> /dev/null; then
    echo -e "${RED}✗ WP-CLI not found. Please install: https://wp-cli.org/${NC}"
    exit 1
fi

echo -e "${GREEN}✓ WP-CLI found: $(wp --version)${NC}"

# Change to WordPress directory
if [ ! -d "$WP_PATH" ]; then
    echo -e "${RED}✗ WordPress directory not found: $WP_PATH${NC}"
    exit 1
fi

cd "$WP_PATH"
echo -e "${GREEN}✓ Changed to WordPress directory${NC}"

# Verify WordPress installation
if ! wp core is-installed --path="$WP_PATH" 2>/dev/null; then
    echo -e "${RED}✗ WordPress not installed at: $WP_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}✓ WordPress installation verified${NC}"

# Get WordPress version
WP_VERSION=$(wp core version --path="$WP_PATH")
echo "  WordPress version: $WP_VERSION"

# Check WordPress version requirement (6.4+)
REQUIRED_WP_VERSION="6.4"
if [ "$(printf '%s\n' "$REQUIRED_WP_VERSION" "$WP_VERSION" | sort -V | head -n1)" != "$REQUIRED_WP_VERSION" ]; then
    echo -e "${RED}✗ WordPress $REQUIRED_WP_VERSION+ required (found $WP_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ WordPress version compatible${NC}"

# Check if WooCommerce is installed
if ! wp plugin is-installed woocommerce --path="$WP_PATH" 2>/dev/null; then
    echo -e "${YELLOW}⚠ WooCommerce not installed. Installing...${NC}"
    wp plugin install woocommerce --activate --path="$WP_PATH"
    echo -e "${GREEN}✓ WooCommerce installed${NC}"
else
    echo -e "${GREEN}✓ WooCommerce already installed${NC}"
fi

# Activate WooCommerce if not active
if ! wp plugin is-active woocommerce --path="$WP_PATH" 2>/dev/null; then
    echo -e "${YELLOW}⚠ WooCommerce inactive. Activating...${NC}"
    wp plugin activate woocommerce --path="$WP_PATH"
    echo -e "${GREEN}✓ WooCommerce activated${NC}"
fi

# Get WooCommerce version
WC_VERSION=$(wp plugin get woocommerce --field=version --path="$WP_PATH")
echo "  WooCommerce version: $WC_VERSION"

# Create backup before deployment
echo ""
echo -e "${BLUE}Creating backup...${NC}"
BACKUP_DIR="$HOME/skyyrose-backups"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/skyyrose-backup-$(date +%Y%m%d-%H%M%S).tar.gz"

if [ -d "$WP_PATH/wp-content/themes/$THEME_NAME" ]; then
    tar -czf "$BACKUP_FILE" -C "$WP_PATH/wp-content/themes" "$THEME_NAME" 2>/dev/null || true
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ No existing theme to backup${NC}"
fi

# Deploy theme
echo ""
echo -e "${BLUE}Deploying theme...${NC}"

THEME_SRC="/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025"
THEME_DEST="$WP_PATH/wp-content/themes/$THEME_NAME"

# Remove old theme if exists
if [ -d "$THEME_DEST" ]; then
    echo -e "${YELLOW}⚠ Removing old theme version...${NC}"
    rm -rf "$THEME_DEST"
fi

# Copy theme files
echo "Copying theme files..."
mkdir -p "$THEME_DEST"
cp -r "$THEME_SRC"/* "$THEME_DEST/"
echo -e "${GREEN}✓ Theme files copied${NC}"

# Set correct permissions
echo "Setting file permissions..."
find "$THEME_DEST" -type d -exec chmod 755 {} \;
find "$THEME_DEST" -type f -exec chmod 644 {} \;
echo -e "${GREEN}✓ Permissions set (755 dirs, 644 files)${NC}"

# Activate theme
echo ""
echo -e "${BLUE}Activating theme...${NC}"

CURRENT_THEME=$(wp theme list --status=active --field=name --path="$WP_PATH")
if [ "$CURRENT_THEME" = "$THEME_NAME" ]; then
    echo -e "${YELLOW}⚠ Theme already active${NC}"
else
    wp theme activate "$THEME_NAME" --path="$WP_PATH"
    echo -e "${GREEN}✓ Theme activated${NC}"
fi

# Configure WordPress settings
echo ""
echo -e "${BLUE}Configuring WordPress settings...${NC}"

# Set permalinks to Post name
wp rewrite structure '/%postname%/' --path="$WP_PATH" 2>/dev/null
wp rewrite flush --path="$WP_PATH"
echo -e "${GREEN}✓ Permalinks configured${NC}"

# Enable WooCommerce features
wp option update woocommerce_store_address "Oakland, CA" --path="$WP_PATH" 2>/dev/null || true
wp option update woocommerce_currency "USD" --path="$WP_PATH" 2>/dev/null || true
wp option update woocommerce_enable_reviews "yes" --path="$WP_PATH" 2>/dev/null || true
echo -e "${GREEN}✓ WooCommerce settings configured${NC}"

# Import products (if CSV exists)
echo ""
if [ -f "$THEME_DEST/PRODUCT_DATA.csv" ]; then
    echo -e "${BLUE}Product import available at: $THEME_DEST/PRODUCT_DATA.csv${NC}"
    echo "  Import via: WooCommerce > Products > Import"
fi

# Create required pages
echo ""
echo -e "${BLUE}Creating required pages...${NC}"

# Check and create Homepage
if ! wp post list --post_type=page --name=home --field=ID --path="$WP_PATH" | grep -q .; then
    HOME_ID=$(wp post create --post_type=page --post_title="Home" --post_status=publish --post_name=home --page_template=template-home.php --path="$WP_PATH" --porcelain)
    wp option update page_on_front "$HOME_ID" --path="$WP_PATH"
    wp option update show_on_front "page" --path="$WP_PATH"
    echo -e "${GREEN}✓ Homepage created and set as front page${NC}"
else
    echo -e "${YELLOW}⚠ Homepage already exists${NC}"
fi

# Check and create About page
if ! wp post list --post_type=page --name=about --field=ID --path="$WP_PATH" | grep -q .; then
    wp post create --post_type=page --post_title="About" --post_status=publish --post_name=about --page_template=page-about.php --path="$WP_PATH" --porcelain > /dev/null
    echo -e "${GREEN}✓ About page created${NC}"
else
    echo -e "${YELLOW}⚠ About page already exists${NC}"
fi

# Check and create Contact page
if ! wp post list --post_type=page --name=contact --field=ID --path="$WP_PATH" | grep -q .; then
    wp post create --post_type=page --post_title="Contact" --post_status=publish --post_name=contact --page_template=page-contact.php --path="$WP_PATH" --porcelain > /dev/null
    echo -e "${GREEN}✓ Contact page created${NC}"
else
    echo -e "${YELLOW}⚠ Contact page already exists${NC}"
fi

# Check and create Collection pages
for collection in "black-rose" "love-hurts" "signature"; do
    PAGE_NAME=$(echo "$collection" | tr '-' ' ' | awk '{for(i=1;i<=NF;i++)sub(/./,toupper(substr($i,1,1)),$i)}1')
    if ! wp post list --post_type=page --name="$collection" --field=ID --path="$WP_PATH" | grep -q .; then
        wp post create --post_type=page --post_title="$PAGE_NAME Collection" --post_status=publish --post_name="$collection" --page_template=template-collection.php --meta_input='{"_collection_type":"'"$collection"'"}' --path="$WP_PATH" --porcelain > /dev/null
        echo -e "${GREEN}✓ $PAGE_NAME Collection page created${NC}"
    else
        echo -e "${YELLOW}⚠ $PAGE_NAME Collection page already exists${NC}"
    fi
done

# Check and create The Vault page
if ! wp post list --post_type=page --name=vault --field=ID --path="$WP_PATH" | grep -q .; then
    wp post create --post_type=page --post_title="The Vault" --post_status=publish --post_name=vault --page_template=template-vault.php --path="$WP_PATH" --porcelain > /dev/null
    echo -e "${GREEN}✓ The Vault page created${NC}"
else
    echo -e "${YELLOW}⚠ The Vault page already exists${NC}"
fi

# Flush caches
echo ""
echo -e "${BLUE}Flushing caches...${NC}"
wp cache flush --path="$WP_PATH" 2>/dev/null || true
wp transient delete --all --path="$WP_PATH" 2>/dev/null || true
wp rewrite flush --path="$WP_PATH"
echo -e "${GREEN}✓ Caches flushed${NC}"

# Security checks
echo ""
echo -e "${BLUE}Running security checks...${NC}"

# Disable debug mode in production
if [ "$ENV" = "production" ]; then
    if wp config get WP_DEBUG --path="$WP_PATH" 2>/dev/null | grep -q "true"; then
        wp config set WP_DEBUG false --raw --path="$WP_PATH" 2>/dev/null || true
        echo -e "${GREEN}✓ Debug mode disabled${NC}"
    else
        echo -e "${GREEN}✓ Debug mode already disabled${NC}"
    fi
fi

# Check file permissions
INSECURE_FILES=$(find "$THEME_DEST" -type f -perm -111 | wc -l)
if [ "$INSECURE_FILES" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Found $INSECURE_FILES executable files (fixing...)${NC}"
    find "$THEME_DEST" -type f -perm -111 -exec chmod 644 {} \;
    echo -e "${GREEN}✓ File permissions corrected${NC}"
else
    echo -e "${GREEN}✓ No insecure file permissions${NC}"
fi

# Deployment summary
echo ""
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              ✓ DEPLOYMENT SUCCESSFUL                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${BLUE}Deployment Summary:${NC}"
echo "  ✓ Theme: $THEME_NAME v$THEME_VERSION"
echo "  ✓ Environment: $ENV"
echo "  ✓ WordPress: $WP_VERSION"
echo "  ✓ WooCommerce: $WC_VERSION"
echo "  ✓ Pages created: Homepage, About, Contact, Collections, Vault"
echo "  ✓ Backup: $BACKUP_FILE"
echo ""

# Next steps
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Visit your site: $(wp option get siteurl --path="$WP_PATH")"
echo "  2. Import products: WooCommerce > Products > Import"
echo "  3. Upload PRODUCT_DATA.csv (30 products)"
echo "  4. Create menus: Appearance > Menus"
echo "  5. Configure payment gateways: WooCommerce > Settings > Payments"
echo "  6. Test checkout flow"
echo "  7. Run PageSpeed test (target: 85+ mobile)"
echo ""

# Monitoring
echo -e "${BLUE}Monitoring:${NC}"
echo "  - Error log: $WP_PATH/wp-content/debug.log"
echo "  - PHP error log: /var/log/php-error.log"
echo "  - Apache/Nginx logs: /var/log/apache2/ or /var/log/nginx/"
echo ""

# Rollback instructions
echo -e "${YELLOW}Rollback (if needed):${NC}"
echo "  tar -xzf $BACKUP_FILE -C $WP_PATH/wp-content/themes/"
echo "  wp theme activate <previous-theme> --path=$WP_PATH"
echo ""

echo -e "${GREEN}🌹 Oakland Soul. Luxury Heart. 🌹${NC}"
echo ""

exit 0
