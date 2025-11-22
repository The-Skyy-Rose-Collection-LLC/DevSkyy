#!/bin/bash
# Quick WordPress Build Script
# Uses brand configuration to automatically build WordPress sites

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════╗
║        WordPress Auto-Builder from Brand Config          ║
╚══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Function to list available brand configs
list_configs() {
    echo "Available brand configurations:"
    echo ""

    if [ -d "config/brands" ]; then
        for file in config/brands/*.json; do
            if [ -f "$file" ]; then
                name=$(basename "$file" .json)
                echo "  - $name"
            fi
        done
    fi

    if [ -f "config/brand-config.json" ]; then
        echo "  - brand-config (custom)"
    fi

    echo ""
}

# Function to create new brand config
create_config() {
    echo "Creating new brand configuration..."
    echo ""

    read -p "Brand name: " BRAND_NAME
    read -p "Brand tagline: " BRAND_TAGLINE
    read -p "Primary color (hex): " PRIMARY_COLOR
    read -p "Secondary color (hex): " SECONDARY_COLOR

    echo ""
    echo "Theme type:"
    echo "  1) luxury_fashion"
    echo "  2) streetwear"
    echo "  3) minimalist"
    echo "  4) vintage"
    echo "  5) sustainable"
    read -p "Select (1-5): " THEME_CHOICE

    case $THEME_CHOICE in
        1) THEME_TYPE="luxury_fashion" ;;
        2) THEME_TYPE="streetwear" ;;
        3) THEME_TYPE="minimalist" ;;
        4) THEME_TYPE="vintage" ;;
        5) THEME_TYPE="sustainable" ;;
        *) THEME_TYPE="luxury_fashion" ;;
    esac

    # Generate config file
    CONFIG_FILE="config/brands/${BRAND_NAME,,}.json"
    CONFIG_FILE="${CONFIG_FILE// /-}"

    cat > "$CONFIG_FILE" << EOF
{
  "brand": {
    "name": "${BRAND_NAME}",
    "tagline": "${BRAND_TAGLINE}",
    "industry": "${THEME_TYPE}"
  },
  "colors": {
    "primary": "${PRIMARY_COLOR}",
    "secondary": "${SECONDARY_COLOR}",
    "accent": "#ffffff"
  },
  "typography": {
    "heading_font": "Playfair Display",
    "body_font": "Montserrat"
  },
  "assets": {
    "logo": "assets/brand/logo.png",
    "hero_images": ["assets/brand/hero.jpg"]
  },
  "theme": {
    "type": "${THEME_TYPE}",
    "layout_style": "full-width"
  },
  "pages": ["home", "shop", "about", "contact"],
  "features": {
    "woocommerce": true,
    "blog": true
  }
}
EOF

    echo ""
    echo -e "${GREEN}✓ Configuration created: ${CONFIG_FILE}${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Edit ${CONFIG_FILE} to customize"
    echo "  2. Add your logo and images to assets/brand/"
    echo "  3. Run: ./scripts/wordpress/quick_build.sh --config ${CONFIG_FILE}"
    echo ""
}

# Function to build from config
build_from_config() {
    CONFIG_FILE=$1
    DEPLOY=${2:-false}

    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}✗ Config file not found: ${CONFIG_FILE}${NC}"
        exit 1
    fi

    echo -e "${BLUE}Building WordPress site from: ${CONFIG_FILE}${NC}"
    echo ""

    # Check API key
    if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
        echo -e "${YELLOW}⚠ Warning: ANTHROPIC_API_KEY not set${NC}"
        echo "  AI features will be limited"
        echo ""
    fi

    # Build
    if [ "$DEPLOY" = true ]; then
        python3 scripts/auto_build_wp.py --config "$CONFIG_FILE" --deploy
    else
        python3 scripts/auto_build_wp.py --config "$CONFIG_FILE"
    fi
}

# Function to setup assets directory
setup_assets() {
    echo "Setting up assets directory structure..."

    mkdir -p assets/brand
    mkdir -p staging/themes/deployed

    echo ""
    echo "Directory structure:"
    echo "  assets/brand/          - Put your brand assets here"
    echo "    ├── logo.png         - Main logo"
    echo "    ├── logo-white.png   - White version of logo"
    echo "    ├── favicon.ico      - Site favicon"
    echo "    ├── hero-1.jpg       - Hero/banner images"
    echo "    └── about.jpg        - About page image"
    echo ""
    echo -e "${GREEN}✓ Asset directories created${NC}"
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [command] [options]

Commands:
  list                  - List available brand configurations
  create                - Create new brand configuration interactively
  build [config]        - Build WordPress site from config
  build-deploy [config] - Build and deploy to WordPress
  setup-assets          - Setup asset directory structure
  help                  - Show this help

Examples:
  # List available configs
  $0 list

  # Create new brand config
  $0 create

  # Build from example config
  $0 build config/brand-config.example.json

  # Build from custom config
  $0 build config/brands/my-brand.json

  # Build and deploy
  $0 build-deploy config/brands/my-brand.json

  # Setup asset directories
  $0 setup-assets

Environment Variables:
  ANTHROPIC_API_KEY     - Required for AI features
  WP_SITE_URL           - WordPress site URL (for deployment)
  WP_APP_PASSWORD       - WordPress application password

Brand Configuration:
  Create a JSON file with your brand details (colors, logo, etc.)
  See: config/brand-config.example.json for template
  Or use: $0 create

Asset Management:
  Place your brand assets in: assets/brand/
  - logo.png, hero images, product photos, etc.
  Configure paths in your brand config JSON

EOF
}

# Main command handler
case "${1:-help}" in
    list)
        list_configs
        ;;
    create)
        create_config
        ;;
    build)
        if [ -z "${2:-}" ]; then
            echo "Error: Config file required"
            echo "Usage: $0 build <config-file>"
            exit 1
        fi
        build_from_config "$2" false
        ;;
    build-deploy)
        if [ -z "${2:-}" ]; then
            echo "Error: Config file required"
            echo "Usage: $0 build-deploy <config-file>"
            exit 1
        fi
        build_from_config "$2" true
        ;;
    setup-assets)
        setup_assets
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
