#!/bin/bash
# Test WordPress Copilot Deployment Workflow

set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
THEME_DIR="${THEME_DIR:-/Users/coreyfoster/DevSkyy/wordpress-theme/skyyrose-2025}"

echo "=== WordPress Copilot Deployment Test ==="
echo "Plugin Directory: $PLUGIN_DIR"
echo "Theme Directory: $THEME_DIR"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "--- Pre-Deployment Checks ---"

# Check theme directory exists
if [ -d "$THEME_DIR" ]; then
    echo -e "${GREEN}✓${NC} Theme directory exists"
else
    echo -e "${RED}✗${NC} Theme directory not found: $THEME_DIR"
    echo "Set THEME_DIR environment variable to test with different theme"
    exit 1
fi

# Check for required theme files
check_theme_file() {
    if [ -f "$THEME_DIR/$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
    else
        echo -e "${RED}✗${NC} $1 missing"
        ((ERRORS++))
    fi
}

check_theme_file "style.css"
check_theme_file "functions.php"
check_theme_file "index.php"
echo

# Check for development files that shouldn't be deployed
echo "--- Development Files Check (should be excluded) ---"
check_excluded() {
    if [ -e "$THEME_DIR/$1" ]; then
        echo -e "${YELLOW}⚠${NC} $1 exists (should be excluded from deployment)"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} $1 not present (good)"
    fi
}

check_excluded "node_modules"
check_excluded ".env"
check_excluded ".env.local"
check_excluded "*.log"
check_excluded ".git"
echo

# Test ZIP creation
echo "--- ZIP Package Creation Test ---"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TEST_ZIP="/tmp/skyyrose-deployment-test-$TIMESTAMP.zip"

echo "Creating test deployment package..."
cd "$THEME_DIR"
zip -r "$TEST_ZIP" . \
    -x "*.git*" \
    -x "node_modules/*" \
    -x ".env*" \
    -x "*.log" \
    -x "*.map" \
    -x "*.DS_Store" \
    >/dev/null 2>&1

if [ -f "$TEST_ZIP" ]; then
    size=$(du -h "$TEST_ZIP" | cut -f1)
    echo -e "${GREEN}✓${NC} ZIP created successfully: $TEST_ZIP ($size)"

    # Check ZIP contents
    echo
    echo "ZIP contents summary:"
    unzip -l "$TEST_ZIP" | tail -1

    # Verify no excluded files made it in
    echo
    echo "Checking for excluded files in ZIP..."
    has_node_modules=$(unzip -l "$TEST_ZIP" | grep -c "node_modules" || true)
    has_env=$(unzip -l "$TEST_ZIP" | grep -c "\.env" || true)
    has_git=$(unzip -l "$TEST_ZIP" | grep -c "\.git" || true)

    if [ "$has_node_modules" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No node_modules in ZIP"
    else
        echo -e "${RED}✗${NC} node_modules found in ZIP ($has_node_modules files)"
        ((ERRORS++))
    fi

    if [ "$has_env" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No .env files in ZIP"
    else
        echo -e "${RED}✗${NC} .env files found in ZIP"
        ((ERRORS++))
    fi

    if [ "$has_git" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} No .git directory in ZIP"
    else
        echo -e "${RED}✗${NC} .git directory found in ZIP"
        ((ERRORS++))
    fi

    # Cleanup
    rm "$TEST_ZIP"
else
    echo -e "${RED}✗${NC} ZIP creation failed"
    ((ERRORS++))
fi
echo

# Test SFTP connectivity (if credentials provided)
echo "--- SFTP Connection Test (Optional) ---"
if [ -n "$SFTP_HOST" ] && [ -n "$SFTP_USER" ] && [ -n "$SFTP_PASS" ]; then
    echo "Testing SFTP connection to $SFTP_HOST..."

    if command -v lftp &> /dev/null; then
        echo -e "${GREEN}✓${NC} lftp installed"

        # Test connection (don't actually upload)
        if lftp -c "
            set sftp:auto-confirm yes
            open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:22
            ls /htdocs
            bye
        " 2>/dev/null; then
            echo -e "${GREEN}✓${NC} SFTP connection successful"
        else
            echo -e "${RED}✗${NC} SFTP connection failed"
            ((ERRORS++))
        fi
    else
        echo -e "${YELLOW}⚠${NC} lftp not installed (required for SFTP deployment)"
        echo "Install: brew install lftp"
        ((WARNINGS++))
    fi
else
    echo -e "${BLUE}ℹ${NC} SFTP credentials not provided (skipping connection test)"
    echo "Set SFTP_HOST, SFTP_USER, SFTP_PASS to test connectivity"
fi
echo

# Test post-deployment verification
echo "--- Post-Deployment Verification Test ---"
SITE_URL="${SITE_URL:-https://skyyrose.co}"
echo "Testing site accessibility: $SITE_URL"

if command -v curl &> /dev/null; then
    # Test site responds
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$SITE_URL")
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Site responds with HTTP 200"
    else
        echo -e "${YELLOW}⚠${NC} Site responds with HTTP $http_code"
        ((WARNINGS++))
    fi

    # Test CSP headers
    csp_header=$(curl -sI "$SITE_URL" | grep -i "content-security-policy" || true)
    if [ -n "$csp_header" ]; then
        echo -e "${GREEN}✓${NC} CSP header present"

        # Check for required directives
        if echo "$csp_header" | grep -q "unsafe-inline"; then
            echo -e "${GREEN}✓${NC} CSP allows unsafe-inline (WordPress.com requirement)"
        else
            echo -e "${YELLOW}⚠${NC} CSP missing unsafe-inline"
        fi

        if echo "$csp_header" | grep -q "cdn.babylonjs.com"; then
            echo -e "${GREEN}✓${NC} CSP allows cdn.babylonjs.com"
        else
            echo -e "${YELLOW}⚠${NC} CSP doesn't allow cdn.babylonjs.com"
        fi
    else
        echo -e "${YELLOW}⚠${NC} No CSP header detected"
    fi

    # Test theme CSS loads
    theme_css_url="$SITE_URL/wp-content/themes/skyyrose-2025/style.css"
    css_code=$(curl -s -o /dev/null -w "%{http_code}" "$theme_css_url")
    if [ "$css_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Theme CSS loads successfully"
    else
        echo -e "${YELLOW}⚠${NC} Theme CSS returns HTTP $css_code"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} curl not installed (skipping site tests)"
fi
echo

# Test deployment script exists
echo "--- Deployment Command Validation ---"
if [ -f "$PLUGIN_DIR/commands/deploy.md" ]; then
    echo -e "${GREEN}✓${NC} Deploy command exists"

    # Check for key deployment steps in command
    if grep -q "ZIP" "$PLUGIN_DIR/commands/deploy.md"; then
        echo -e "${GREEN}✓${NC} Deploy command includes ZIP creation"
    fi

    if grep -q "SFTP\|upload" "$PLUGIN_DIR/commands/deploy.md"; then
        echo -e "${GREEN}✓${NC} Deploy command includes upload instructions"
    fi

    if grep -q "verif\|check" "$PLUGIN_DIR/commands/deploy.md"; then
        echo -e "${GREEN}✓${NC} Deploy command includes verification"
    fi
else
    echo -e "${RED}✗${NC} Deploy command not found"
    ((ERRORS++))
fi
echo

echo "--- Summary ---"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All deployment tests passed!${NC}"
    echo
    echo "Ready for deployment:"
    echo "  1. Theme package can be created"
    echo "  2. No excluded files in package"
    echo "  3. Site is accessible"
    echo "  4. Deploy command is configured"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Deployment tests passed with $WARNINGS warnings${NC}"
    echo
    echo "Warnings can be addressed but don't block deployment"
    exit 0
else
    echo -e "${RED}✗ Deployment tests failed with $ERRORS errors and $WARNINGS warnings${NC}"
    echo
    echo "Fix errors before deploying"
    exit 1
fi
