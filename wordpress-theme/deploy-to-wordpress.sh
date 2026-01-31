#!/bin/bash
# SkyyRose WordPress Theme Deployment Script
# Usage: ./deploy-to-wordpress.sh [method]
# Methods: wpcli, ftp, manual

set -e

THEME_DIR="/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025"
THEME_ZIP="/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025-theme.zip"
PRODUCT_CSV="/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025/PRODUCT_DATA.csv"

echo "🚀 SkyyRose WordPress Theme Deployment"
echo "======================================="
echo ""

# Detect deployment method
METHOD="${1:-detect}"

if [ "$METHOD" = "detect" ]; then
    if command -v wp &> /dev/null; then
        METHOD="wpcli"
        echo "✅ WP-CLI detected - using automated deployment"
    else
        METHOD="manual"
        echo "ℹ️  WP-CLI not found - using manual deployment"
    fi
fi

case $METHOD in
    wpcli)
        echo "📦 Deploying via WP-CLI..."
        echo ""

        # Check if WordPress is accessible
        if ! wp --version &> /dev/null; then
            echo "❌ Error: WP-CLI not installed or not in PATH"
            echo "Install: https://wp-cli.org/#installing"
            exit 1
        fi

        # Install theme
        echo "1️⃣  Installing theme..."
        wp theme install "$THEME_ZIP" --activate

        # Create pages
        echo "2️⃣  Creating pages..."

        # Home page
        wp post create --post_type=page --post_title='Home' --post_status=publish --post_name='home' --meta_input='{"_wp_page_template":"template-home.php"}' || echo "Page may already exist"

        # Vault page
        wp post create --post_type=page --post_title='The Vault' --post_status=publish --post_name='vault' --meta_input='{"_wp_page_template":"template-vault.php"}' || echo "Page may already exist"

        # Collection pages
        for collection in "black-rose" "love-hurts" "signature"; do
            # Shop page
            wp post create --post_type=page --post_title="${collection^} Collection" --post_status=publish --post_name="$collection" --meta_input='{"_wp_page_template":"template-collection.php","_collection_type":"'$collection'"}' || echo "Page may already exist"

            # Experience page
            wp post create --post_type=page --post_title="${collection^} Experience" --post_status=publish --post_name="${collection}-experience" --meta_input='{"_wp_page_template":"template-immersive.php","_collection_type":"'$collection'"}' || echo "Page may already exist"
        done

        # Info pages
        wp post create --post_type=page --post_title='About' --post_status=publish --post_name='about' --meta_input='{"_wp_page_template":"page-about.php"}' || echo "Page may already exist"
        wp post create --post_type=page --post_title='Contact' --post_status=publish --post_name='contact' --meta_input='{"_wp_page_template":"page-contact.php"}' || echo "Page may already exist"

        # Set homepage
        echo "3️⃣  Setting homepage..."
        HOME_ID=$(wp post list --post_type=page --name=home --field=ID --format=csv)
        wp option update show_on_front page
        wp option update page_on_front "$HOME_ID"

        # Import products (requires WooCommerce)
        if wp plugin is-installed woocommerce; then
            echo "4️⃣  Importing products..."
            wp wc product import "$PRODUCT_CSV" --user=1 || echo "⚠️  Product import may require manual completion"
        else
            echo "⚠️  WooCommerce not installed - skipping product import"
            echo "   Install WooCommerce and import $PRODUCT_CSV manually"
        fi

        echo ""
        echo "✅ Deployment complete!"
        echo ""
        echo "📋 Next steps:"
        echo "   1. Visit your site to verify"
        echo "   2. Configure WooCommerce (if not done)"
        echo "   3. Set up navigation menu"
        echo "   4. Upload product images"
        ;;

    ftp)
        echo "📦 Deploying via FTP..."
        echo ""

        read -p "FTP Host: " FTP_HOST
        read -p "FTP User: " FTP_USER
        read -sp "FTP Pass: " FTP_PASS
        echo ""
        read -p "Remote theme path (e.g., /wp-content/themes/): " REMOTE_PATH

        echo "Uploading theme..."
        lftp -u "$FTP_USER","$FTP_PASS" "$FTP_HOST" <<EOF
cd $REMOTE_PATH
mirror -R $THEME_DIR skyyrose-2025
bye
EOF

        echo ""
        echo "✅ Theme uploaded via FTP!"
        echo ""
        echo "📋 Next steps:"
        echo "   1. Go to WordPress Admin → Appearance → Themes"
        echo "   2. Activate 'SkyyRose 2025'"
        echo "   3. Create pages manually (see DEPLOYMENT_READY.md)"
        echo "   4. Import products via WooCommerce → Products → Import"
        ;;

    manual)
        echo "📦 Manual Deployment Instructions"
        echo ""
        echo "Theme ZIP ready: $THEME_ZIP"
        echo ""
        echo "🔧 STEP 1: Upload Theme"
        echo "   1. Go to WordPress Admin → Appearance → Themes → Add New"
        echo "   2. Click 'Upload Theme'"
        echo "   3. Choose file: $THEME_ZIP"
        echo "   4. Click 'Install Now'"
        echo "   5. Click 'Activate'"
        echo ""
        echo "🔧 STEP 2: Create Pages"
        echo "   Create these pages in Pages → Add New:"
        echo ""
        echo "   Page Title          | Template                | Slug                | Meta"
        echo "   --------------------|-------------------------|---------------------|------------------"
        echo "   Home                | Home                    | home                | -"
        echo "   The Vault           | Vault                   | vault               | -"
        echo "   Black Rose          | Collection              | black-rose          | _collection_type=black-rose"
        echo "   Black Rose Exp      | Immersive Experience    | black-rose-exp      | _collection_type=black-rose"
        echo "   Love Hurts          | Collection              | love-hurts          | _collection_type=love-hurts"
        echo "   Love Hurts Exp      | Immersive Experience    | love-hurts-exp      | _collection_type=love-hurts"
        echo "   Signature           | Collection              | signature           | _collection_type=signature"
        echo "   Signature Exp       | Immersive Experience    | signature-exp       | _collection_type=signature"
        echo "   About               | About SkyyRose          | about               | -"
        echo "   Contact             | Contact                 | contact             | -"
        echo ""
        echo "🔧 STEP 3: Set Homepage"
        echo "   1. Go to Settings → Reading"
        echo "   2. Set 'A static page'"
        echo "   3. Homepage: Select 'Home'"
        echo "   4. Save Changes"
        echo ""
        echo "🔧 STEP 4: Import Products"
        echo "   1. Go to WooCommerce → Products → Import"
        echo "   2. Choose file: $PRODUCT_CSV"
        echo "   3. Map columns (auto-detected)"
        echo "   4. Run Import"
        echo "   5. Verify 30 products imported"
        echo ""
        echo "🔧 STEP 5: Set Up Menu"
        echo "   1. Go to Appearance → Menus"
        echo "   2. Create 'Primary Navigation'"
        echo "   3. Add pages with structure:"
        echo "      - Home"
        echo "      - Collections (dropdown)"
        echo "        - Black Rose (dropdown)"
        echo "          - Experience"
        echo "          - Shop"
        echo "        - Love Hurts (dropdown)"
        echo "          - Experience"
        echo "          - Shop"
        echo "        - Signature (dropdown)"
        echo "          - Experience"
        echo "          - Shop"
        echo "      - Pre-Order (The Vault)"
        echo "      - About"
        echo "      - Contact"
        echo "   4. Assign to 'Primary Menu'"
        echo ""
        echo "📖 Full guide: $THEME_DIR/DEPLOYMENT_READY.md"
        echo ""
        echo "✅ Ready to deploy!"
        ;;

    *)
        echo "❌ Unknown method: $METHOD"
        echo ""
        echo "Usage: $0 [wpcli|ftp|manual]"
        exit 1
        ;;
esac

echo ""
echo "🎉 WordPress deployment ready!"
echo ""
echo "📚 Documentation:"
echo "   - Deployment Guide: $THEME_DIR/DEPLOYMENT_READY.md"
echo "   - Security Info: /Users/coreyfoster/DevSkyy/wordpress-theme/SECURITY.md"
echo "   - API Guide: /Users/coreyfoster/DevSkyy/wordpress-theme/WORDPRESS_COM_API.md"
echo ""
