#!/bin/bash

# DevSkyy API Key Setup Script
# Loads environment variables and starts the API server

set -e

echo "🔑 DevSkyy API Key Setup"
echo "========================"

# Check if we're in the DevSkyy directory
if [ ! -f "devskyy_mcp.py" ]; then
    echo "❌ Please run this script from the DevSkyy directory"
    exit 1
fi

# Load environment variables from .env file
if [ -f ".env" ]; then
    echo "📋 Loading environment variables from .env..."
    source .env
    echo "✅ Environment variables loaded"
else
    echo "❌ .env file not found. Please run ./install_mcp.sh first"
    exit 1
fi

# Verify API key is set
if [ -z "$DEVSKYY_API_KEY" ]; then
    echo "❌ DEVSKYY_API_KEY not found in .env file"
    exit 1
fi

# Display configuration
echo
echo "🔧 Current Configuration:"
echo "   API Key: ${DEVSKYY_API_KEY:0:15}...${DEVSKYY_API_KEY: -10}"
echo "   API URL: $DEVSKYY_API_URL"
echo "   Key Length: ${#DEVSKYY_API_KEY} characters"

# Export for current session
export DEVSKYY_API_KEY
export DEVSKYY_API_URL

echo
echo "✅ API key setup complete!"
echo
echo "🚀 Ready to start DevSkyy API server"
echo "   Run: python3 main.py"
echo
echo "📋 Or test MCP server:"
echo "   Run: python3 devskyy_mcp.py"
echo
echo "🔌 Claude Desktop Integration:"
echo "   1. Restart Claude Desktop"
echo "   2. Look for 14 DevSkyy tools"
echo "   3. Test with: 'Use devskyy_list_agents'"
