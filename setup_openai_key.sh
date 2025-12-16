#!/bin/bash
# Setup OpenAI API Key for DevSkyy
# Usage: ./setup_openai_key.sh

set -e

echo "=================================================="
echo "  DevSkyy - OpenAI API Key Setup"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if key is already set
if [ -n "$OPENAI_API_KEY" ]; then
    MASKED_KEY="${OPENAI_API_KEY:0:10}...${OPENAI_API_KEY: -4}"
    echo -e "${GREEN}✓${NC} OPENAI_API_KEY is already set: ${MASKED_KEY}"
    echo ""
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing key."
        exit 0
    fi
fi

# Prompt for API key
echo -e "${BLUE}Please enter your OpenAI API key:${NC}"
echo "(It should start with 'sk-' or 'sk-proj-')"
echo ""
read -s -p "API Key: " API_KEY
echo ""

# Validate key format
if [[ ! $API_KEY =~ ^sk- ]]; then
    echo -e "${RED}✗ Invalid API key format. Key should start with 'sk-'${NC}"
    exit 1
fi

# Determine shell config file
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_CONFIG="$HOME/.bash_profile"
    SHELL_NAME="bash"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
    SHELL_NAME="bash"
else
    echo -e "${YELLOW}⚠ Could not find shell config file${NC}"
    echo "Creating ~/.zshrc..."
    SHELL_CONFIG="$HOME/.zshrc"
    SHELL_NAME="zsh"
    touch "$SHELL_CONFIG"
fi

echo ""
echo -e "${BLUE}Shell config file: ${SHELL_CONFIG}${NC}"

# Check if key already exists in config
if grep -q "export OPENAI_API_KEY=" "$SHELL_CONFIG"; then
    echo -e "${YELLOW}⚠ OPENAI_API_KEY already exists in ${SHELL_CONFIG}${NC}"
    echo "Updating existing entry..."
    
    # Backup config file
    cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✓${NC} Backup created: ${SHELL_CONFIG}.backup.*"
    
    # Remove old entry
    sed -i.tmp '/export OPENAI_API_KEY=/d' "$SHELL_CONFIG"
    rm -f "${SHELL_CONFIG}.tmp"
fi

# Add new key to config
echo "" >> "$SHELL_CONFIG"
echo "# OpenAI API Key - Added by DevSkyy setup $(date +%Y-%m-%d)" >> "$SHELL_CONFIG"
echo "export OPENAI_API_KEY=\"${API_KEY}\"" >> "$SHELL_CONFIG"

echo -e "${GREEN}✓${NC} API key added to ${SHELL_CONFIG}"

# Also create .env file
echo ""
echo "Creating .env file..."

# Ensure .env is in .gitignore
if [ -f .gitignore ]; then
    if ! grep -q "^\.env$" .gitignore; then
        echo ".env" >> .gitignore
        echo -e "${GREEN}✓${NC} Added .env to .gitignore"
    fi
else
    echo ".env" > .gitignore
    echo -e "${GREEN}✓${NC} Created .gitignore with .env"
fi

# Create .env file
cat > .env << EOF
# DevSkyy Environment Variables
# Generated: $(date)
# DO NOT COMMIT THIS FILE TO GIT

# OpenAI API Key
OPENAI_API_KEY=${API_KEY}

# Add other API keys as needed:
# ANTHROPIC_API_KEY=your-key-here
# GOOGLE_API_KEY=your-key-here
# MISTRAL_API_KEY=your-key-here
# COHERE_API_KEY=your-key-here
# GROQ_API_KEY=your-key-here
EOF

chmod 600 .env
echo -e "${GREEN}✓${NC} Created .env file with restricted permissions (600)"

# Test the key
echo ""
echo "Testing API key..."
export OPENAI_API_KEY="${API_KEY}"

if python3 test_openai_connection.py; then
    echo ""
    echo -e "${GREEN}=================================================="
    echo "  ✓ Setup Complete!"
    echo -e "==================================================${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Reload your shell:"
    echo "     source ${SHELL_CONFIG}"
    echo ""
    echo "  2. Or start a new terminal session"
    echo ""
    echo "  3. Verify the setup:"
    echo "     python3 scripts/verify_llm_clients.py"
    echo ""
else
    echo ""
    echo -e "${RED}=================================================="
    echo "  ✗ API Key Test Failed"
    echo -e "==================================================${NC}"
    echo ""
    echo "Please check:"
    echo "  1. Your API key is valid"
    echo "  2. Your OpenAI account has credits"
    echo "  3. Your internet connection is working"
    echo ""
    echo "Visit: https://platform.openai.com/api-keys"
fi

