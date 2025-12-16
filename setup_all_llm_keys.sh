#!/bin/bash
# Setup All LLM Provider API Keys for DevSkyy
# Usage: ./setup_all_llm_keys.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=================================================="
echo "  DevSkyy - Multi-LLM Provider Setup"
echo "=================================================="
echo ""

# Determine shell config file
if [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.bash_profile" ]; then
    SHELL_CONFIG="$HOME/.bash_profile"
elif [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    SHELL_CONFIG="$HOME/.zshrc"
    touch "$SHELL_CONFIG"
fi

echo -e "${BLUE}Shell config: ${SHELL_CONFIG}${NC}"
echo ""

# Backup config
cp "$SHELL_CONFIG" "${SHELL_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
echo -e "${GREEN}✓${NC} Backup created"
echo ""

# Function to add or update API key
add_api_key() {
    local KEY_NAME=$1
    local KEY_VALUE=$2
    
    # Remove old entry if exists
    sed -i.tmp "/export ${KEY_NAME}=/d" "$SHELL_CONFIG"
    rm -f "${SHELL_CONFIG}.tmp"
    
    # Add new entry
    echo "export ${KEY_NAME}=\"${KEY_VALUE}\"" >> "$SHELL_CONFIG"
}

# Check existing keys
echo -e "${CYAN}Checking existing API keys...${NC}"
echo ""

source "$SHELL_CONFIG" 2>/dev/null || true

# OpenAI
if [ -n "$OPENAI_API_KEY" ]; then
    echo -e "${GREEN}✓ OPENAI_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ OPENAI_API_KEY${NC} not set"
fi

# Anthropic
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ ANTHROPIC_API_KEY${NC} not set"
fi

# Google
if [ -n "$GOOGLE_API_KEY" ]; then
    echo -e "${GREEN}✓ GOOGLE_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ GOOGLE_API_KEY${NC} not set"
fi

# Mistral
if [ -n "$MISTRAL_API_KEY" ]; then
    echo -e "${GREEN}✓ MISTRAL_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ MISTRAL_API_KEY${NC} not set"
fi

# Cohere
if [ -n "$COHERE_API_KEY" ]; then
    echo -e "${GREEN}✓ COHERE_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ COHERE_API_KEY${NC} not set"
fi

# Groq
if [ -n "$GROQ_API_KEY" ]; then
    echo -e "${GREEN}✓ GROQ_API_KEY${NC} already set"
else
    echo -e "${YELLOW}⚠ GROQ_API_KEY${NC} not set"
fi

echo ""
echo "=================================================="
echo "  Setup Instructions"
echo "=================================================="
echo ""
echo "I'll guide you through setting up each provider."
echo "You can skip any provider by pressing Enter without typing anything."
echo ""
echo -e "${YELLOW}IMPORTANT: Get your API keys from these URLs first:${NC}"
echo ""
echo "1. Anthropic (Claude):  https://console.anthropic.com/settings/keys"
echo "2. Google (Gemini):     https://aistudio.google.com/app/apikey"
echo "3. Groq (Fast):         https://console.groq.com/keys"
echo "4. Mistral:             https://console.mistral.ai/api-keys/"
echo "5. Cohere:              https://dashboard.cohere.com/api-keys"
echo ""
read -p "Press Enter when you're ready to continue..."
echo ""

# Anthropic
echo "=================================================="
echo "  1. Anthropic (Claude 3.5 Sonnet)"
echo "=================================================="
echo "Get your key: https://console.anthropic.com/settings/keys"
echo ""
read -s -p "Anthropic API Key (or Enter to skip): " ANTHROPIC_KEY
echo ""
if [ -n "$ANTHROPIC_KEY" ]; then
    add_api_key "ANTHROPIC_API_KEY" "$ANTHROPIC_KEY"
    echo -e "${GREEN}✓${NC} Anthropic key added"
else
    echo -e "${YELLOW}⊘${NC} Skipped"
fi
echo ""

# Google
echo "=================================================="
echo "  2. Google (Gemini 1.5/2.0)"
echo "=================================================="
echo "Get your key: https://aistudio.google.com/app/apikey"
echo ""
read -s -p "Google API Key (or Enter to skip): " GOOGLE_KEY
echo ""
if [ -n "$GOOGLE_KEY" ]; then
    add_api_key "GOOGLE_API_KEY" "$GOOGLE_KEY"
    echo -e "${GREEN}✓${NC} Google key added"
else
    echo -e "${YELLOW}⊘${NC} Skipped"
fi
echo ""

# Groq
echo "=================================================="
echo "  3. Groq (Ultra-Fast Llama/Mixtral)"
echo "=================================================="
echo "Get your key: https://console.groq.com/keys"
echo ""
read -s -p "Groq API Key (or Enter to skip): " GROQ_KEY
echo ""
if [ -n "$GROQ_KEY" ]; then
    add_api_key "GROQ_API_KEY" "$GROQ_KEY"
    echo -e "${GREEN}✓${NC} Groq key added"
else
    echo -e "${YELLOW}⊘${NC} Skipped"
fi
echo ""

# Done
echo "=================================================="
echo "  Setup Complete!"
echo "=================================================="
echo ""
echo "Reload your shell to use the new keys:"
echo -e "${CYAN}source ${SHELL_CONFIG}${NC}"
echo ""
echo "Or start a new terminal session."
echo ""
echo "Verify setup:"
echo -e "${CYAN}python3 scripts/verify_llm_clients.py${NC}"
echo ""

