#!/bin/bash
# WordPress Copilot Plugin Validation Script

set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== WordPress Copilot Plugin Validation ==="
echo "Plugin Directory: $PLUGIN_DIR"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check if required files exist
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        ((ERRORS++))
    fi
}

# Check if required directory exists
check_dir() {
    if [ -d "$1" ]; then
        local count=$(find "$1" -name "*.md" | wc -l | tr -d ' ')
        echo -e "${GREEN}✓${NC} $1 ($count files)"
    else
        echo -e "${RED}✗${NC} $1 (MISSING)"
        ((ERRORS++))
    fi
}

echo "--- Core Files ---"
check_file "$PLUGIN_DIR/.claude-plugin/plugin.json"
check_file "$PLUGIN_DIR/README.md"
check_file "$PLUGIN_DIR/TESTING.md"
check_file "$PLUGIN_DIR/hooks/hooks.json"
echo

echo "--- Commands ---"
check_file "$PLUGIN_DIR/commands/deploy.md"
check_file "$PLUGIN_DIR/commands/scaffold.md"
check_file "$PLUGIN_DIR/commands/optimize.md"
check_file "$PLUGIN_DIR/commands/verify.md"
check_file "$PLUGIN_DIR/commands/rollback.md"
check_file "$PLUGIN_DIR/commands/search.md"
check_file "$PLUGIN_DIR/commands/learn.md"
echo

echo "--- Agents ---"
check_file "$PLUGIN_DIR/agents/context7-enforcer.md"
check_file "$PLUGIN_DIR/agents/deployment-manager.md"
check_file "$PLUGIN_DIR/agents/wordpress-architect.md"
echo

echo "--- Skills ---"
check_dir "$PLUGIN_DIR/skills/immersive-3d-web-development"
check_dir "$PLUGIN_DIR/skills/interactive-web-development"
check_dir "$PLUGIN_DIR/skills/static-web-development"
check_dir "$PLUGIN_DIR/skills/frontend-architecture"
check_dir "$PLUGIN_DIR/skills/web-performance"
check_dir "$PLUGIN_DIR/skills/web-accessibility"
check_dir "$PLUGIN_DIR/skills/luxury-fashion-ecommerce"
check_dir "$PLUGIN_DIR/skills/theme-development"
check_dir "$PLUGIN_DIR/skills/elementor-widgets"
check_dir "$PLUGIN_DIR/skills/woocommerce-integration"
check_dir "$PLUGIN_DIR/skills/performance-optimization"
check_dir "$PLUGIN_DIR/skills/security-hardening"
check_dir "$PLUGIN_DIR/skills/deployment-workflow"
check_dir "$PLUGIN_DIR/skills/infrastructure"
check_dir "$PLUGIN_DIR/skills/continuous-learning"
check_dir "$PLUGIN_DIR/skills/open-source-intelligence"
echo

echo "--- SKILL.md Files ---"
for skill_dir in "$PLUGIN_DIR/skills"/*; do
    if [ -d "$skill_dir" ]; then
        skill_name=$(basename "$skill_dir")
        if [ -f "$skill_dir/SKILL.md" ]; then
            echo -e "${GREEN}✓${NC} $skill_name/SKILL.md"
        else
            echo -e "${RED}✗${NC} $skill_name/SKILL.md (MISSING)"
            ((ERRORS++))
        fi
    fi
done
echo

echo "--- Plugin Manifest Validation ---"
if [ -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ]; then
    # Check JSON validity
    if jq empty "$PLUGIN_DIR/.claude-plugin/plugin.json" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} plugin.json is valid JSON"

        # Check required fields
        name=$(jq -r '.name' "$PLUGIN_DIR/.claude-plugin/plugin.json")
        version=$(jq -r '.version' "$PLUGIN_DIR/.claude-plugin/plugin.json")
        description=$(jq -r '.description' "$PLUGIN_DIR/.claude-plugin/plugin.json")

        if [ "$name" != "null" ] && [ -n "$name" ]; then
            echo -e "${GREEN}✓${NC} Plugin name: $name"
        else
            echo -e "${RED}✗${NC} Plugin name missing"
            ((ERRORS++))
        fi

        if [ "$version" != "null" ] && [ -n "$version" ]; then
            echo -e "${GREEN}✓${NC} Plugin version: $version"
        else
            echo -e "${YELLOW}⚠${NC} Plugin version missing"
            ((WARNINGS++))
        fi

        if [ "$description" != "null" ] && [ -n "$description" ]; then
            echo -e "${GREEN}✓${NC} Plugin description exists"
        else
            echo -e "${YELLOW}⚠${NC} Plugin description missing"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}✗${NC} plugin.json is invalid JSON"
        ((ERRORS++))
    fi
fi
echo

echo "--- Hooks Configuration Validation ---"
if [ -f "$PLUGIN_DIR/hooks/hooks.json" ]; then
    if jq empty "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} hooks.json is valid JSON"

        # Check for Context7 enforcement hook
        has_pretooluse=$(jq 'has("PreToolUse")' "$PLUGIN_DIR/hooks/hooks.json")
        if [ "$has_pretooluse" = "true" ]; then
            echo -e "${GREEN}✓${NC} PreToolUse hook configured (Context7 enforcement)"
        else
            echo -e "${YELLOW}⚠${NC} PreToolUse hook not configured"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}✗${NC} hooks.json is invalid JSON"
        ((ERRORS++))
    fi
fi
echo

echo "--- Summary ---"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation passed with $WARNINGS warnings${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS errors and $WARNINGS warnings${NC}"
    exit 1
fi
