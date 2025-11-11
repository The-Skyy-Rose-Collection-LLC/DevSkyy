#!/bin/bash

# Skyy Rose Collection Theme Deployment Script
# This script packages the complete theme and prepares it for deployment

set -e  # Exit on any error

echo "🌹 SKYY ROSE COLLECTION THEME DEPLOYMENT"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
THEME_NAME="skyy-rose-collection"
THEME_DIR="wordpress-mastery/templates/woocommerce-luxury"
PACKAGE_DIR="skyy-rose-collection-theme-package"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${BLUE}📦 Starting theme packaging process...${NC}"

# Create package directory
if [ -d "$PACKAGE_DIR" ]; then
    echo -e "${YELLOW}⚠️  Removing existing package directory...${NC}"
    rm -rf "$PACKAGE_DIR"
fi

mkdir -p "$PACKAGE_DIR"

echo -e "${GREEN}✅ Created package directory: $PACKAGE_DIR${NC}"

# Copy theme files
echo -e "${BLUE}📁 Copying theme files...${NC}"

# Core theme files
cp "$THEME_DIR/style.css" "$PACKAGE_DIR/"
cp "$THEME_DIR/functions.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/index.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/header.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/footer.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/front-page.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/sidebar.php" "$PACKAGE_DIR/"
cp "$THEME_DIR/searchform.php" "$PACKAGE_DIR/"

# Check if other template files exist and copy them
if [ -f "$THEME_DIR/single.php" ]; then
    cp "$THEME_DIR/single.php" "$PACKAGE_DIR/"
fi

if [ -f "$THEME_DIR/page.php" ]; then
    cp "$THEME_DIR/page.php" "$PACKAGE_DIR/"
fi

if [ -f "$THEME_DIR/archive.php" ]; then
    cp "$THEME_DIR/archive.php" "$PACKAGE_DIR/"
fi

if [ -f "$THEME_DIR/404.php" ]; then
    cp "$THEME_DIR/404.php" "$PACKAGE_DIR/"
fi

if [ -f "$THEME_DIR/comments.php" ]; then
    cp "$THEME_DIR/comments.php" "$PACKAGE_DIR/"
fi

# Copy assets directory
if [ -d "$THEME_DIR/assets" ]; then
    cp -r "$THEME_DIR/assets" "$PACKAGE_DIR/"
    echo -e "${GREEN}✅ Copied assets directory${NC}"
fi

# Copy WooCommerce templates
if [ -d "$THEME_DIR/woocommerce" ]; then
    cp -r "$THEME_DIR/woocommerce" "$PACKAGE_DIR/"
    echo -e "${GREEN}✅ Copied WooCommerce templates${NC}"
fi

# Create README.txt for the theme
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
=== Skyy Rose Collection ===
Contributors: DevSkyy
Tags: luxury, fashion, ecommerce, woocommerce, responsive, elegant, premium
Requires at least: 5.0
Tested up to: 6.4
Requires PHP: 8.1
Stable tag: 1.0.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

A luxury fashion WordPress theme designed for the Skyy Rose Collection brand.

== Description ==

Skyy Rose Collection is a premium WordPress theme designed specifically for luxury fashion brands and high-end eCommerce stores. With its elegant design, advanced WooCommerce integration, and sophisticated user experience, this theme provides everything needed to create a stunning online fashion boutique.

== Features ==

* Fully responsive design optimized for all devices
* WooCommerce integration with custom product templates
* Advanced product gallery with zoom and 360° view
* Luxury color palette and typography
* Custom widgets and sidebar areas
* SEO optimized with structured data
* Performance optimized for fast loading
* Accessibility compliant (WCAG 2.1 AA)
* Translation ready
* Custom post types and fields
* Advanced search functionality
* Newsletter integration
* Social media integration
* Customer review system

== Installation ==

1. Upload the theme files to the `/wp-content/themes/skyy-rose-collection` directory
2. Activate the theme through the 'Appearance > Themes' menu in WordPress
3. Go to Appearance > Customize to configure theme options
4. Install and activate WooCommerce plugin for eCommerce functionality

== Changelog ==

= 1.0.0 =
* Initial release
* Complete luxury fashion theme
* WooCommerce integration
* Advanced product features
* Custom widgets and templates

== Credits ==

* Google Fonts: Playfair Display, Inter, Dancing Script
* Icons: Custom SVG icons
* Images: Placeholder images included for demo purposes
EOF

echo -e "${GREEN}✅ Created README.txt${NC}"

# Create screenshot.png (placeholder)
echo -e "${BLUE}🖼️  Creating theme screenshot...${NC}"
# Note: In a real deployment, you'd want to include an actual 1200x900 screenshot
touch "$PACKAGE_DIR/screenshot.png"

# Create the zip package
echo -e "${BLUE}📦 Creating zip package...${NC}"
cd "$PACKAGE_DIR"
zip -r "../${THEME_NAME}-${TIMESTAMP}.zip" .
cd ..

echo -e "${GREEN}✅ Created zip package: ${THEME_NAME}-${TIMESTAMP}.zip${NC}"

# Create latest version without timestamp
cp "${THEME_NAME}-${TIMESTAMP}.zip" "${THEME_NAME}-latest.zip"
echo -e "${GREEN}✅ Created latest version: ${THEME_NAME}-latest.zip${NC}"

# Update the existing zip in wordpress-mastery/templates
if [ -f "wordpress-mastery/templates/wp-mastery-woocommerce-luxury-phase2a3-complete.zip" ]; then
    cp "${THEME_NAME}-latest.zip" "wordpress-mastery/templates/wp-mastery-woocommerce-luxury-phase2a3-complete.zip"
    echo -e "${GREEN}✅ Updated existing theme package${NC}"
fi

# Git operations
echo -e "${BLUE}🔄 Preparing Git commit...${NC}"

# Add all changes
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
else
    # Commit changes
    git commit -m "🌹 Complete Skyy Rose Collection luxury fashion theme

Features:
- ✨ Luxury brand styling with Skyy Rose Collection colors
- 🛍️ Advanced WooCommerce integration
- 📱 Fully responsive design
- 🎨 Custom product templates and galleries
- 🔍 Enhanced search functionality
- 💌 Newsletter integration
- 🎯 SEO optimized with structured data
- ⚡ Performance optimized
- ♿ Accessibility compliant
- 🌐 Translation ready

Package: ${THEME_NAME}-${TIMESTAMP}.zip
Ready for immediate deployment!"

    echo -e "${GREEN}✅ Committed changes to Git${NC}"

    # Push to remote
    echo -e "${BLUE}🚀 Pushing to remote repository...${NC}"
    git push origin main
    echo -e "${GREEN}✅ Pushed to remote repository${NC}"
fi

# Display deployment summary
echo ""
echo -e "${PURPLE}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${PURPLE}=====================${NC}"
echo ""
echo -e "${GREEN}📦 Theme Package:${NC} ${THEME_NAME}-${TIMESTAMP}.zip"
echo -e "${GREEN}📦 Latest Version:${NC} ${THEME_NAME}-latest.zip"
echo -e "${GREEN}📁 Package Directory:${NC} $PACKAGE_DIR"
echo ""
echo -e "${BLUE}🚀 NEXT STEPS:${NC}"
echo -e "1. Upload ${THEME_NAME}-latest.zip to WordPress admin"
echo -e "2. Go to Appearance > Themes > Add New > Upload Theme"
echo -e "3. Select the zip file and click 'Install Now'"
echo -e "4. Activate the theme"
echo -e "5. Go to Appearance > Customize to configure"
echo ""
echo -e "${GREEN}✨ Your Skyy Rose Collection theme is ready to go live!${NC}"

# Optional: Open the package directory
if command -v open &> /dev/null; then
    echo -e "${BLUE}📂 Opening package directory...${NC}"
    open "$PACKAGE_DIR"
fi

echo ""
echo -e "${PURPLE}🌹 Skyy Rose Collection - Luxury Fashion Theme${NC}"
echo -e "${PURPLE}   Ready for deployment and live use!${NC}"
echo ""
