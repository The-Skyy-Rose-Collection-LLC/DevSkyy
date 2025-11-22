#!/bin/bash
# WordPress Site Builder - Quick CLI Tool
# Build WordPress themes from the command line

set -euo pipefail

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=================================================="
echo "WordPress Site Builder CLI"
echo "==================================================${NC}"
echo ""

# Check requirements
check_requirements() {
    echo "Checking requirements..."

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 not found${NC}"
        exit 1
    fi

    if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
        echo -e "${YELLOW}⚠ Warning: ANTHROPIC_API_KEY not set${NC}"
        echo "  AI features will be limited"
    fi

    echo -e "${GREEN}✓ Requirements OK${NC}"
    echo ""
}

# Interactive theme builder
build_interactive() {
    echo "Theme Type Selection:"
    echo "  1) Luxury Fashion"
    echo "  2) Streetwear"
    echo "  3) Minimalist"
    echo "  4) Vintage"
    echo "  5) Sustainable"
    echo ""
    read -p "Select theme type (1-5): " theme_choice

    case $theme_choice in
        1) THEME_TYPE="luxury_fashion" ;;
        2) THEME_TYPE="streetwear" ;;
        3) THEME_TYPE="minimalist" ;;
        4) THEME_TYPE="vintage" ;;
        5) THEME_TYPE="sustainable" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac

    echo ""
    read -p "Brand name: " BRAND_NAME
    read -p "Primary color (hex, e.g., #1a1a1a): " PRIMARY_COLOR
    read -p "Include WooCommerce? (y/n): " WOOCOMMERCE

    echo ""
    echo "Building theme..."
    python3 -c "
import asyncio
from agent.wordpress.theme_builder import ElementorThemeBuilder
import os

async def build():
    builder = ElementorThemeBuilder(api_key=os.getenv('ANTHROPIC_API_KEY'))

    brand_info = {
        'name': '${BRAND_NAME}',
        'primary_color': '${PRIMARY_COLOR}',
    }

    theme = await builder.generate_theme(
        brand_info=brand_info,
        theme_type='${THEME_TYPE}',
        pages=['home', 'shop', 'about', 'contact'],
        include_woocommerce=${WOOCOMMERCE,,} == 'y'
    )

    export_result = await builder.export_theme(
        theme=theme,
        format='elementor_json',
        output_dir='staging/themes/deployed'
    )

    print(f'\n✓ Theme created: {export_result[\"path\"]}')

asyncio.run(build())
"
}

# Quick build with defaults
build_quick() {
    THEME_TYPE=${1:-luxury_fashion}
    BRAND_NAME=${2:-"My Fashion Brand"}

    echo "Building ${THEME_TYPE} theme for ${BRAND_NAME}..."
    python3 examples/build_wordpress_site.py
}

# Deploy theme
deploy_theme() {
    THEME_PATH=$1

    if [ -z "${WP_SITE_URL:-}" ]; then
        echo -e "${RED}✗ WP_SITE_URL not set${NC}"
        echo "Set: export WP_SITE_URL=https://your-site.com"
        exit 1
    fi

    if [ -z "${WP_APP_PASSWORD:-}" ]; then
        echo -e "${RED}✗ WP_APP_PASSWORD not set${NC}"
        echo "Generate one in WordPress: Users > Profile > Application Passwords"
        exit 1
    fi

    echo "Deploying theme to ${WP_SITE_URL}..."
    python3 -c "
import asyncio
from agent.wordpress.automated_theme_uploader import (
    AutomatedThemeUploader,
    WordPressCredentials,
    UploadMethod
)
import os

async def deploy():
    credentials = WordPressCredentials(
        site_url=os.getenv('WP_SITE_URL'),
        username=os.getenv('WP_USERNAME', 'admin'),
        password='',
        application_password=os.getenv('WP_APP_PASSWORD')
    )

    uploader = AutomatedThemeUploader()
    result = await uploader.deploy_theme(
        theme_path='${THEME_PATH}',
        credentials=credentials,
        upload_method=UploadMethod.WORDPRESS_REST_API,
        activate_after_upload=False,
        backup_existing=True
    )

    if result.success:
        print(f'\n✓ Deployed: {result.deployment_id}')
    else:
        print(f'\n✗ Failed: {result.error_message}')

asyncio.run(deploy())
"
}

# Show help
show_help() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  interactive     - Interactive theme builder"
    echo "  quick [type]    - Quick build with defaults"
    echo "  deploy [path]   - Deploy theme to WordPress"
    echo "  help            - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 interactive"
    echo "  $0 quick luxury_fashion"
    echo "  $0 deploy staging/themes/deployed/my-theme"
    echo ""
    echo "Environment variables:"
    echo "  ANTHROPIC_API_KEY  - Required for AI features"
    echo "  WP_SITE_URL        - WordPress site URL"
    echo "  WP_APP_PASSWORD    - WordPress application password"
    echo ""
}

# Main
check_requirements

case "${1:-interactive}" in
    interactive)
        build_interactive
        ;;
    quick)
        build_quick "${2:-}" "${3:-}"
        ;;
    deploy)
        if [ -z "${2:-}" ]; then
            echo "Error: Theme path required"
            show_help
            exit 1
        fi
        deploy_theme "$2"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
