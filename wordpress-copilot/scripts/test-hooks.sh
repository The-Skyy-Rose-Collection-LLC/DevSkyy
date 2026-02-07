#!/bin/bash
# Test WordPress Copilot Hooks Configuration

set -e

PLUGIN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOKS_FILE="$PLUGIN_DIR/hooks/hooks.json"

echo "=== WordPress Copilot Hooks Testing ==="
echo "Hooks File: $HOOKS_FILE"
echo

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0

if [ ! -f "$HOOKS_FILE" ]; then
    echo -e "${RED}✗${NC} hooks.json not found"
    exit 1
fi

echo "--- JSON Syntax Validation ---"
if jq empty "$HOOKS_FILE" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} hooks.json is valid JSON"
else
    echo -e "${RED}✗${NC} hooks.json contains syntax errors"
    exit 1
fi
echo

echo "--- Hook Types Validation ---"
hook_types=$(jq -r 'keys[]' "$HOOKS_FILE")
valid_types=("PreToolUse" "PostToolUse" "Stop" "SubagentStop" "SessionStart" "SessionEnd" "UserPromptSubmit" "PreCompact" "Notification")

for hook in $hook_types; do
    if [[ " ${valid_types[@]} " =~ " ${hook} " ]]; then
        echo -e "${GREEN}✓${NC} $hook (valid hook type)"
    else
        echo -e "${RED}✗${NC} $hook (invalid hook type)"
        ((ERRORS++))
    fi
done
echo

echo "--- PreToolUse Hook (Context7 Enforcement) ---"
if jq -e '.PreToolUse' "$HOOKS_FILE" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} PreToolUse hook exists"

    # Check matcher
    matcher=$(jq -r '.PreToolUse[0].matcher' "$HOOKS_FILE")
    if [[ "$matcher" == *"Write"* ]] || [[ "$matcher" == *"Edit"* ]]; then
        echo -e "${GREEN}✓${NC} Matcher includes Write/Edit: $matcher"
    else
        echo -e "${YELLOW}⚠${NC} Matcher may not catch all code generation: $matcher"
    fi

    # Check hook type
    hook_type=$(jq -r '.PreToolUse[0].hooks[0].type' "$HOOKS_FILE")
    if [ "$hook_type" = "prompt" ]; then
        echo -e "${GREEN}✓${NC} Hook type: prompt (Context7 verification)"
    else
        echo -e "${YELLOW}⚠${NC} Hook type: $hook_type (expected 'prompt')"
    fi

    # Check blocking
    blocking=$(jq -r '.PreToolUse[0].hooks[0].blocking' "$HOOKS_FILE")
    if [ "$blocking" = "true" ]; then
        echo -e "${GREEN}✓${NC} Blocking: true (prevents code generation without Context7)"
    else
        echo -e "${RED}✗${NC} Blocking: $blocking (should be true)"
        ((ERRORS++))
    fi

    # Check prompt content
    prompt=$(jq -r '.PreToolUse[0].hooks[0].prompt' "$HOOKS_FILE")
    if [[ "$prompt" == *"Context7"* ]]; then
        echo -e "${GREEN}✓${NC} Prompt mentions Context7"
    else
        echo -e "${RED}✗${NC} Prompt doesn't mention Context7"
        ((ERRORS++))
    fi
else
    echo -e "${RED}✗${NC} PreToolUse hook not found (Context7 enforcement missing)"
    ((ERRORS++))
fi
echo

echo "--- Stop Hook (Continuous Learning) ---"
if jq -e '.Stop' "$HOOKS_FILE" >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Stop hook exists (pattern extraction enabled)"

    stop_prompt=$(jq -r '.Stop[0].hooks[0].prompt' "$HOOKS_FILE")
    if [[ "$stop_prompt" == *"pattern"* ]] || [[ "$stop_prompt" == *"learn"* ]]; then
        echo -e "${GREEN}✓${NC} Stop hook configured for pattern extraction"
    else
        echo -e "${YELLOW}⚠${NC} Stop hook may not extract patterns"
    fi
else
    echo -e "${YELLOW}⚠${NC} Stop hook not configured (continuous learning disabled)"
fi
echo

echo "--- Hook Structure Validation ---"
for hook in $hook_types; do
    hooks_array=$(jq -r ".${hook}" "$HOOKS_FILE")

    if [ "$hooks_array" = "null" ]; then
        continue
    fi

    # Check if it's an array
    if ! echo "$hooks_array" | jq -e 'type == "array"' >/dev/null 2>&1; then
        echo -e "${RED}✗${NC} $hook is not an array"
        ((ERRORS++))
        continue
    fi

    # Check each hook configuration
    hook_count=$(echo "$hooks_array" | jq 'length')
    echo "Validating $hook ($hook_count configurations):"

    for ((i=0; i<$hook_count; i++)); do
        # Check required fields
        has_matcher=$(echo "$hooks_array" | jq -e ".[$i] | has(\"matcher\")")
        has_hooks=$(echo "$hooks_array" | jq -e ".[$i] | has(\"hooks\")")

        if [ "$has_matcher" = "true" ] && [ "$has_hooks" = "true" ]; then
            echo -e "  ${GREEN}✓${NC} Configuration $i has required fields"
        else
            echo -e "  ${RED}✗${NC} Configuration $i missing required fields"
            ((ERRORS++))
        fi
    done
done
echo

echo "--- Summary ---"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All hook tests passed!${NC}"
    echo
    echo "Hooks configured:"
    echo "  - Context7 enforcement (PreToolUse, blocking)"
    echo "  - Continuous learning (Stop)"
    exit 0
else
    echo -e "${RED}✗ Hook tests failed with $ERRORS errors${NC}"
    exit 1
fi
