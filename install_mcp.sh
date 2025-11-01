#!/bin/bash

# DevSkyy Enhanced MCP Server v1.1.0 - Installation Script
# Automatically sets up Claude Desktop integration

set -e

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   DevSkyy Enhanced MCP Server v1.1.0 - Installation             ║"
echo "║   Industry-First Multi-Agent AI Platform Integration            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if we're in the DevSkyy directory
if [ ! -f "devskyy_mcp.py" ]; then
    print_error "Please run this script from the DevSkyy directory"
    exit 1
fi

print_info "Starting DevSkyy MCP Server installation..."
echo

# Step 1: Install Python dependencies
print_info "Step 1: Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements_mcp.txt
    print_status "Python dependencies installed"
elif command -v pip &> /dev/null; then
    pip install -r requirements_mcp.txt
    print_status "Python dependencies installed"
else
    print_error "pip not found. Please install Python and pip first."
    exit 1
fi
echo

# Step 2: Check Python version
print_info "Step 2: Checking Python version..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$python_version >= 3.11" | bc -l) -eq 1 ]]; then
    print_status "Python $python_version is compatible"
else
    print_warning "Python $python_version detected. Python 3.11+ recommended for best performance."
fi
echo

# Step 3: Test MCP server
print_info "Step 3: Testing MCP server..."
if python3 -c "import devskyy_mcp; print('Import successful')" &> /dev/null; then
    print_status "MCP server imports successfully"
else
    print_error "MCP server import failed. Check dependencies."
    exit 1
fi
echo

# Step 4: Set up Claude Desktop configuration
print_info "Step 4: Setting up Claude Desktop configuration..."

# Get current directory
CURRENT_DIR=$(pwd)
PYTHON_PATH=$(which python3)

# Claude Desktop config directory
CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_CONFIG_FILE="$CLAUDE_CONFIG_DIR/claude_desktop_config.json"

# Create config directory if it doesn't exist
mkdir -p "$CLAUDE_CONFIG_DIR"

# Check if config file exists
if [ -f "$CLAUDE_CONFIG_FILE" ]; then
    print_warning "Claude Desktop config already exists. Creating backup..."
    cp "$CLAUDE_CONFIG_FILE" "$CLAUDE_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create or update config file
cat > "$CLAUDE_CONFIG_FILE" << EOF
{
  "mcpServers": {
    "devskyy": {
      "command": "$PYTHON_PATH",
      "args": ["$CURRENT_DIR/devskyy_mcp.py"],
      "env": {
        "DEVSKYY_API_KEY": "",
        "DEVSKYY_API_URL": "http://localhost:8000"
      }
    }
  }
}
EOF

print_status "Claude Desktop configuration created"
echo

# Step 5: Environment setup
print_info "Step 5: Environment setup..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    cat > ".env" << EOF
# DevSkyy MCP Server Environment Variables
DEVSKYY_API_KEY=your-api-key-here
DEVSKYY_API_URL=http://localhost:8000
EOF
    print_status "Environment file created (.env)"
else
    print_warning "Environment file already exists"
fi

echo
print_info "🎉 Installation Complete!"
echo

# Final instructions
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        NEXT STEPS                               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo
print_info "1. Set your API key:"
echo "   export DEVSKYY_API_KEY='your-actual-api-key'"
echo "   # Or edit the .env file"
echo
print_info "2. Start the DevSkyy API server (in another terminal):"
echo "   cd $CURRENT_DIR"
echo "   python3 main.py"
echo
print_info "3. Test the MCP server:"
echo "   python3 devskyy_mcp.py"
echo
print_info "4. Restart Claude Desktop to load the new configuration"
echo
print_info "5. In Claude Desktop, you should now see 14 DevSkyy tools available:"
echo "   📋 11 Core Tools"
echo "   🔒 2 Security Tools"
echo "   📊 1 Analytics Tool"
echo

print_status "DevSkyy Enhanced MCP Server v1.1.0 is ready!"
echo
print_info "For detailed usage instructions, see: MCP_ENHANCED_GUIDE.md"
print_info "For troubleshooting, see: README_MCP.md"
echo

# Test command
print_info "Quick test command:"
echo "   Try in Claude: 'Use devskyy_list_agents to show me all available AI agents'"
echo
