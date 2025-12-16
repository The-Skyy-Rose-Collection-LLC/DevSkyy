#!/bin/bash

###############################################################################
# DevSkyy MCP Server Setup Script
# 
# This script configures Model Context Protocol (MCP) servers for Claude Desktop
# and other MCP-compatible clients.
#
# Usage:
#   ./scripts/setup_mcp.sh
#
# Requirements:
#   - Python 3.11+
#   - Node.js 18+
#   - Claude Desktop (optional)
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║   DevSkyy MCP Server Setup                                   ║${NC}"
echo -e "${BLUE}║   Configure Model Context Protocol Servers                   ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo -e "${GREEN}✓ Python ${PYTHON_VERSION}${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi
NODE_VERSION=$(node --version)
echo -e "${GREEN}✓ Node.js ${NODE_VERSION}${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found. Please install npm${NC}"
    exit 1
fi
NPM_VERSION=$(npm --version)
echo -e "${GREEN}✓ npm ${NPM_VERSION}${NC}"

echo ""

# Install Python dependencies
echo -e "${YELLOW}Installing Python MCP dependencies...${NC}"
cd "$PROJECT_ROOT"

if [ -f "mcp/requirements.txt" ]; then
    pip3 install -r mcp/requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ mcp/requirements.txt not found, skipping Python dependencies${NC}"
fi

echo ""

# Test MCP servers
echo -e "${YELLOW}Testing MCP servers...${NC}"

# Test DevSkyy OpenAI server
if [ -f "mcp/openai_server.py" ]; then
    timeout 5 python3 mcp/openai_server.py --help &> /dev/null || true
    echo -e "${GREEN}✓ DevSkyy OpenAI MCP server found${NC}"
else
    echo -e "${RED}✗ mcp/openai_server.py not found${NC}"
fi

# Test DevSkyy main server
if [ -f "devskyy_mcp.py" ]; then
    timeout 5 python3 devskyy_mcp.py --help &> /dev/null || true
    echo -e "${GREEN}✓ DevSkyy Main MCP server found${NC}"
else
    echo -e "${RED}✗ devskyy_mcp.py not found${NC}"
fi

echo ""

# Configure Claude Desktop
echo -e "${YELLOW}Configuring Claude Desktop...${NC}"

CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

if [ ! -d "$CLAUDE_CONFIG_DIR" ]; then
    echo -e "${YELLOW}⚠ Claude Desktop not found. Skipping Claude configuration.${NC}"
    echo -e "${YELLOW}  Install Claude Desktop from: https://claude.ai/download${NC}"
else
    # Backup existing config
    if [ -f "$CLAUDE_CONFIG_FILE" ]; then
        BACKUP_FILE="$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        cp "$CLAUDE_CONFIG_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓ Backed up existing config to: $BACKUP_FILE${NC}"
    fi
    
    # Copy example config
    if [ -f "config/claude/desktop.example.json" ]; then
        # Update paths in config
        sed "s|/Users/coreyfoster/DevSkyy|$PROJECT_ROOT|g" \
            config/claude/desktop.example.json > "$CLAUDE_CONFIG_FILE"
        echo -e "${GREEN}✓ Claude Desktop config updated${NC}"
        echo -e "${BLUE}  Config location: $CLAUDE_CONFIG_FILE${NC}"
    else
        echo -e "${RED}✗ config/claude/desktop.example.json not found${NC}"
    fi
fi

echo ""

# Environment variables setup
echo -e "${YELLOW}Setting up environment variables...${NC}"

ENV_FILE="$PROJECT_ROOT/.env.mcp"

if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << 'EOF'
# DevSkyy MCP Environment Variables
# Copy these to your ~/.zshrc or ~/.bash_profile

# OpenAI API Key (required for devskyy-openai server)
export OPENAI_API_KEY="sk-your-openai-key-here"

# Anthropic API Key (optional, for Claude API access)
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key-here"

# DevSkyy API Key (required for devskyy-main server)
export DEVSKYY_API_KEY="your-devskyy-api-key-here"

# GitHub Personal Access Token (required for github server)
export GITHUB_TOKEN="ghp_your-github-token-here"

# Brave Search API Key (optional, for web search)
export BRAVE_API_KEY="your-brave-api-key-here"
EOF
    echo -e "${GREEN}✓ Created .env.mcp file${NC}"
    echo -e "${YELLOW}  Please edit $ENV_FILE and add your API keys${NC}"
else
    echo -e "${BLUE}  .env.mcp already exists${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║   Setup Complete!                                            ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo ""
echo -e "1. ${YELLOW}Configure API keys:${NC}"
echo -e "   Edit: $ENV_FILE"
echo -e "   Then add to your shell profile (~/.zshrc or ~/.bash_profile)"
echo ""
echo -e "2. ${YELLOW}Restart Claude Desktop:${NC}"
echo -e "   Quit and reopen Claude Desktop to load MCP servers"
echo ""
echo -e "3. ${YELLOW}Test MCP servers:${NC}"
echo -e "   python3 mcp/openai_server.py"
echo -e "   python3 devskyy_mcp.py"
echo ""
echo -e "4. ${YELLOW}Read documentation:${NC}"
echo -e "   docs/MCP_CONFIGURATION_GUIDE.md"
echo ""
echo -e "${BLUE}Configured MCP Servers:${NC}"
echo -e "  • devskyy-openai    - OpenAI models (GPT-4o, vision, code gen)"
echo -e "  • devskyy-main      - 54-agent ecosystem"
echo -e "  • filesystem        - File operations"
echo -e "  • git               - Version control"
echo -e "  • github            - GitHub API"
echo -e "  • postgres          - Database operations"
echo -e "  • sequential-thinking - Complex reasoning"
echo -e "  • brave-search      - Web search"
echo -e "  • fetch             - Web content"
echo -e "  • memory            - Persistent context"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"

