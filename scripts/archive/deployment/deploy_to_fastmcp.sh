#!/bin/bash

#
# Deploy DevSkyy MCP to FastMCP (critical-fuchsia-ape)
#
# This script deploys devskyy_mcp.py to the critical-fuchsia-ape FastMCP endpoint
# replacing the current echo_tool with all 17 DevSkyy tools.
#
# Usage:
#   ./scripts/deploy_to_fastmcp.sh [--install-cli] [--test-only]
#
# Options:
#   --install-cli    Install FastMCP CLI before deploying
#   --test-only      Run tests without deploying
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_FILE="$PROJECT_ROOT/devskyy_mcp.py"
CONFIG_FILE="$PROJECT_ROOT/fastmcp.config.json"
APP_NAME="critical-fuchsia-ape"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}DevSkyy MCP → FastMCP Deployment${NC}"
echo -e "${BLUE}Target: critical-fuchsia-ape.fastmcp.app${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Parse arguments
INSTALL_CLI=false
TEST_ONLY=false

for arg in "$@"; do
    case $arg in
        --install-cli)
            INSTALL_CLI=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
    esac
done

# Step 1: Install FastMCP CLI if requested
if [ "$INSTALL_CLI" = true ]; then
    echo -e "${BLUE}Step 1: Installing FastMCP CLI...${NC}"

    if command -v pip3 &> /dev/null; then
        pip3 install --upgrade fastmcp
        echo -e "${GREEN}✓ FastMCP CLI installed${NC}\n"
    else
        echo -e "${RED}✗ pip3 not found. Please install Python 3.11+${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}Step 1: Checking FastMCP CLI...${NC}"

    if ! command -v fastmcp &> /dev/null; then
        echo -e "${YELLOW}⚠ FastMCP CLI not found${NC}"
        echo -e "${YELLOW}Run with --install-cli flag to install:${NC}"
        echo -e "${BLUE}  ./scripts/deploy_to_fastmcp.sh --install-cli${NC}\n"
        exit 1
    fi

    echo -e "${GREEN}✓ FastMCP CLI found: $(which fastmcp)${NC}\n"
fi

# Step 2: Validate devskyy_mcp.py
echo -e "${BLUE}Step 2: Validating devskyy_mcp.py...${NC}"

if [ ! -f "$MCP_FILE" ]; then
    echo -e "${RED}✗ devskyy_mcp.py not found at $MCP_FILE${NC}"
    exit 1
fi

# Check Python syntax
if python3 -m py_compile "$MCP_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓ Python syntax valid${NC}"
else
    echo -e "${RED}✗ Python syntax errors in devskyy_mcp.py${NC}"
    exit 1
fi

# Count tools in the file
TOOL_COUNT=$(grep -c "@mcp.tool(" "$MCP_FILE" || echo "0")
echo -e "${GREEN}✓ Found $TOOL_COUNT tools defined${NC}\n"

# Step 3: Check dependencies
echo -e "${BLUE}Step 3: Checking dependencies...${NC}"

REQUIRED_PACKAGES=("fastmcp" "httpx" "pydantic")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if pip3 show "$package" &> /dev/null; then
        echo -e "${GREEN}✓ $package installed${NC}"
    else
        echo -e "${YELLOW}⚠ $package not installed${NC}"
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "\n${YELLOW}Installing missing packages...${NC}"
    pip3 install "${MISSING_PACKAGES[@]}"
fi

echo ""

# Step 4: Test locally (optional)
if [ "$TEST_ONLY" = true ]; then
    echo -e "${BLUE}Step 4: Testing devskyy_mcp.py locally...${NC}"

    # Set test environment variables
    export MCP_BACKEND="devskyy"
    export DEVSKYY_API_URL="http://localhost:8000"
    export DEVSKYY_API_KEY="test-key"

    # Try to import and validate the server
    python3 << EOF
import sys
sys.path.insert(0, '$PROJECT_ROOT')

try:
    # Import to check for syntax errors
    import devskyy_mcp
    print("✓ devskyy_mcp.py imports successfully")

    # Check that mcp server is defined
    if hasattr(devskyy_mcp, 'mcp'):
        print("✓ FastMCP server instance found")
    else:
        print("✗ FastMCP server instance not found")
        sys.exit(1)

except Exception as e:
    print(f"✗ Error importing devskyy_mcp: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Local test passed${NC}\n"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}Test completed successfully!${NC}"
        echo -e "${GREEN}Run without --test-only to deploy to FastMCP${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
    else
        echo -e "${RED}✗ Local test failed${NC}"
        exit 1
    fi

    exit 0
fi

# Step 5: Deploy to FastMCP
echo -e "${BLUE}Step 4: Deploying to FastMCP...${NC}\n"

echo -e "${YELLOW}Deployment Method:${NC}"
echo -e "FastMCP offers several deployment options:"
echo -e ""
echo -e "  ${BLUE}1. FastMCP CLI (Recommended)${NC}"
echo -e "     fastmcp deploy $MCP_FILE --name $APP_NAME"
echo -e ""
echo -e "  ${BLUE}2. FastMCP Dashboard${NC}"
echo -e "     https://fastmcp.com/dashboard → Upload $MCP_FILE"
echo -e ""
echo -e "  ${BLUE}3. GitHub Integration${NC}"
echo -e "     Connect your repo at https://fastmcp.com/github"
echo -e ""

# Check if user is logged in to FastMCP
if command -v fastmcp &> /dev/null; then
    echo -e "${YELLOW}Attempting deployment via FastMCP CLI...${NC}\n"

    # Try to deploy
    if fastmcp deploy "$MCP_FILE" --name "$APP_NAME" --config "$CONFIG_FILE" 2>&1; then
        echo -e "\n${GREEN}✓ Deployment successful!${NC}"
        echo -e "${GREEN}✓ Your server is now live at: https://$APP_NAME.fastmcp.app${NC}\n"

        # Test the deployed endpoint
        echo -e "${BLUE}Testing deployed endpoint...${NC}"
        sleep 5  # Wait for deployment to propagate

        HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "https://$APP_NAME.fastmcp.app/health" || echo "000")

        if [ "$HEALTH_CHECK" = "200" ]; then
            echo -e "${GREEN}✓ Health check passed${NC}"
        else
            echo -e "${YELLOW}⚠ Health check returned HTTP $HEALTH_CHECK${NC}"
            echo -e "${YELLOW}  The server may still be starting up${NC}"
        fi

    else
        EXIT_CODE=$?
        echo -e "\n${YELLOW}⚠ CLI deployment not available or failed${NC}"
        echo -e "${YELLOW}Exit code: $EXIT_CODE${NC}\n"

        echo -e "${BLUE}Please deploy manually:${NC}"
        echo -e ""
        echo -e "  ${BLUE}1. Visit:${NC} https://fastmcp.com/dashboard"
        echo -e "  ${BLUE}2. Click:${NC} 'New Deployment' or 'Update App'"
        echo -e "  ${BLUE}3. Upload:${NC} $MCP_FILE"
        echo -e "  ${BLUE}4. Set app name:${NC} $APP_NAME"
        echo -e "  ${BLUE}5. Configure environment variables from:${NC} $CONFIG_FILE"
        echo -e ""
        echo -e "${YELLOW}Required environment variables:${NC}"
        echo -e "  - CRITICAL_FUCHSIA_APE_KEY"
        echo -e "  - DEVSKYY_API_KEY"
        echo -e "  - OPENAI_API_KEY (optional)"
        echo -e "  - ANTHROPIC_API_KEY (optional)"
        echo -e "  - TRIPO_API_KEY (optional)"
        echo -e "  - FASHN_API_KEY (optional)"
        echo -e ""
    fi
else
    echo -e "${YELLOW}FastMCP CLI not available${NC}"
    echo -e "${YELLOW}Please deploy manually via the dashboard${NC}\n"
fi

# Step 6: Provide post-deployment instructions
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Post-Deployment Steps${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${YELLOW}1. Verify deployment:${NC}"
echo -e "   curl https://$APP_NAME.fastmcp.app/health"
echo -e ""

echo -e "${YELLOW}2. List available tools:${NC}"
echo -e "   curl https://$APP_NAME.fastmcp.app/tools"
echo -e ""

echo -e "${YELLOW}3. Update Claude Desktop config:${NC}"
echo -e '   Add to ~/.claude/claude_desktop_config.json:'
echo -e '   {'
echo -e '     "mcpServers": {'
echo -e '       "devskyy": {'
echo -e '         "command": "python",'
echo -e '         "args": ["'$MCP_FILE'"],'
echo -e '         "env": {'
echo -e '           "MCP_BACKEND": "critical-fuchsia-ape",'
echo -e '           "CRITICAL_FUCHSIA_APE_URL": "https://'$APP_NAME'.fastmcp.app",'
echo -e '           "CRITICAL_FUCHSIA_APE_KEY": "your-api-key"'
echo -e '         }'
echo -e '       }'
echo -e '     }'
echo -e '   }'
echo -e ""

echo -e "${YELLOW}4. Test with an MCP client:${NC}"
echo -e "   The server should now expose all 17 DevSkyy tools"
echo -e ""

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Deployment script completed!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"
