#!/bin/bash
# Simple WordPress OAuth Deployment
# Generates authorization URL and deployment instructions

set -e

# Load credentials
source .env.wordpress 2>/dev/null || {
    echo "❌ Error: .env.wordpress not found"
    exit 1
}

echo "🚀 SkyyRose WordPress Deployment"
echo "================================="
echo ""

# Generate OAuth URL
# URL encode the redirect URI
REDIRECT_URI="urn%3Aietf%3Awg%3Aoauth%3A2.0%3Aoob"
AUTH_URL="https://public-api.wordpress.com/oauth2/authorize?client_id=${WORDPRESS_CLIENT_ID}&redirect_uri=${REDIRECT_URI}&response_type=code"

echo "📋 STEP 1: Authorize Application"
echo ""
echo "Click this link to authorize:"
echo ""
echo "$AUTH_URL"
echo ""
echo "After clicking 'Approve', you'll get an authorization code."
echo ""
read -p "Enter authorization code: " AUTH_CODE

if [ -z "$AUTH_CODE" ]; then
    echo "❌ Error: No authorization code provided"
    exit 1
fi

echo ""
echo "🔐 Getting access token..."

# Get access token
TOKEN_RESPONSE=$(curl -s -X POST https://public-api.wordpress.com/oauth2/token \
    -d "client_id=${WORDPRESS_CLIENT_ID}" \
    -d "client_secret=${WORDPRESS_CLIENT_SECRET}" \
    -d "grant_type=authorization_code" \
    -d "code=${AUTH_CODE}" \
    -d "redirect_uri=urn:ietf:wg:oauth:2.0:oob")

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Error getting access token:"
    echo "$TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Authenticated!"
echo ""

# Get site URL
read -p "Enter your WordPress.com site URL (e.g., mysite.wordpress.com): " SITE_URL

if [ -z "$SITE_URL" ]; then
    echo "❌ Error: Site URL required"
    exit 1
fi

# Remove protocol if present
SITE_URL=$(echo "$SITE_URL" | sed 's|https\?://||' | sed 's|/$||')

echo ""
echo "🌐 Connecting to $SITE_URL..."

# Get site info
SITE_INFO=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    "https://public-api.wordpress.com/rest/v1.2/sites/$SITE_URL")

SITE_NAME=$(echo "$SITE_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin).get('name', '$SITE_URL'))" 2>/dev/null)

echo "✅ Connected to: $SITE_NAME"
echo ""

# Create pages
echo "📄 Creating WordPress pages..."
echo ""

create_page() {
    local TITLE="$1"
    local SLUG="$2"

    RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        "https://public-api.wordpress.com/rest/v1.2/sites/$SITE_URL/posts/new" \
        -d "{\"title\":\"$TITLE\",\"type\":\"page\",\"status\":\"publish\",\"slug\":\"$SLUG\"}")

    if echo "$RESPONSE" | grep -q '"ID"'; then
        echo "   ✅ $TITLE"
    else
        ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('message', 'Unknown error'))" 2>/dev/null)
        echo "   ⚠️  $TITLE: $ERROR"
    fi
}

# Create all pages
create_page "Home" "home"
create_page "The Vault" "vault"
create_page "Black Rose" "black-rose"
create_page "Black Rose Experience" "black-rose-experience"
create_page "Love Hurts" "love-hurts"
create_page "Love Hurts Experience" "love-hurts-experience"
create_page "Signature" "signature"
create_page "Signature Experience" "signature-experience"
create_page "About" "about"
create_page "Contact" "contact"

echo ""
echo "✅ Pages created!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📦 NEXT STEPS:"
echo ""
echo "1️⃣  Upload Theme:"
echo "    → Go to: https://$SITE_URL/wp-admin/theme-install.php"
echo "    → Click 'Upload Theme'"
echo "    → Choose: $(pwd)/skyyrose-2025-theme.zip"
echo "    → Click 'Install Now' then 'Activate'"
echo ""
echo "2️⃣  Set Homepage:"
echo "    → Go to: https://$SITE_URL/wp-admin/options-reading.php"
echo "    → Select 'A static page'"
echo "    → Homepage: Select 'Home'"
echo "    → Save Changes"
echo ""
echo "3️⃣  Assign Templates to Pages:"
echo "    → Edit each page (Pages → All Pages)"
echo "    → In 'Page Attributes', select template:"
echo "       • Home → 'Home'"
echo "       • The Vault → 'Vault'"
echo "       • Black Rose → 'Collection' (set Custom Field: _collection_type = black-rose)"
echo "       • Black Rose Experience → 'Immersive Experience' (set Custom Field: _collection_type = black-rose)"
echo "       • Love Hurts → 'Collection' (set Custom Field: _collection_type = love-hurts)"
echo "       • Love Hurts Experience → 'Immersive Experience' (set Custom Field: _collection_type = love-hurts)"
echo "       • Signature → 'Collection' (set Custom Field: _collection_type = signature)"
echo "       • Signature Experience → 'Immersive Experience' (set Custom Field: _collection_type = signature)"
echo "       • About → 'About SkyyRose'"
echo "       • Contact → 'Contact'"
echo ""
echo "4️⃣  Import Products:"
echo "    → Go to: https://$SITE_URL/wp-admin/edit.php?post_type=product&page=product_importer"
echo "    → Upload: $(pwd)/skyyrose-2025/PRODUCT_DATA.csv"
echo "    → Run Import (30 products)"
echo ""
echo "5️⃣  Create Navigation Menu:"
echo "    → Go to: https://$SITE_URL/wp-admin/nav-menus.php"
echo "    → Create 'Primary Navigation' with collection dropdowns"
echo "    → (See WORDPRESS_DEPLOYMENT.md for menu structure)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎉 Pages created! Continue with steps above to complete deployment."
echo ""
echo "📖 Full guide: $(pwd)/WORDPRESS_DEPLOYMENT.md"
echo ""
