#!/bin/bash
# DevSkyy Requirements Validation Script
# Validates all requirements files for syntax, conflicts, and pinning standards
# Exit code 0 = all validations passed
# Exit code 1 = validation failures found

# Strict mode with explicit error handling via VALIDATION_FAILED flag
set -eEuo pipefail

# Trap for cleanup on unexpected errors
trap 'echo "Error on line $LINENO. Validation aborted."; exit 1' ERR

echo "=================================================="
echo "DevSkyy Requirements Validation"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VALIDATION_FAILED=0

# Requirements files to validate
REQUIREMENTS_FILES=(
    "requirements.txt"
    "requirements-dev.txt"
    "requirements-test.txt"
    "requirements-production.txt"
    "requirements.minimal.txt"
    "requirements.vercel.txt"
    "requirements_mcp.txt"
    "requirements-luxury-automation.txt"
    "wordpress-mastery/docker/ai-services/requirements.txt"
)

echo "Step 1: Checking files exist..."
echo "-----------------------------------"
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$req_file" ]; then
        echo -e "${GREEN}✓${NC} Found: $req_file"
    else
        echo -e "${RED}✗${NC} Missing: $req_file"
        VALIDATION_FAILED=1
    fi
done
echo ""

echo "Step 2: Syntax validation (pip install --dry-run)..."
echo "-----------------------------------"
for req_file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$req_file" ]; then
        echo "Testing: $req_file"
        if pip install --dry-run --no-deps -r "$req_file" > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} $req_file - syntax valid"
        else
            echo -e "${RED}✗${NC} $req_file - syntax errors detected"
            pip install --dry-run --no-deps -r "$req_file" 2>&1 | head -20
            VALIDATION_FAILED=1
        fi
    fi
done
echo ""

echo "Step 3: Checking version pinning standards..."
echo "-----------------------------------"
# Check main requirements.txt for unpinned versions (except build tools)
if [ -f "requirements.txt" ]; then
    set +e  # Allow grep to return no matches without failing
    UNPINNED=$(grep -v "^#" requirements.txt | grep -v "^$" | grep -E ">=|~=" | grep -v "setuptools")
    set -e  # Re-enable strict error checking
    if [ -z "$UNPINNED" ]; then
        echo -e "${GREEN}✓${NC} requirements.txt - all packages properly pinned"
    else
        echo -e "${YELLOW}⚠${NC} requirements.txt - found unpinned packages:"
        echo "$UNPINNED"
        # This is a warning, not a failure
    fi
fi

# Check dev/test files use -r inheritance
if [ -f "requirements-dev.txt" ]; then
    if grep -q "^-r requirements.txt" requirements-dev.txt; then
        echo -e "${GREEN}✓${NC} requirements-dev.txt - uses -r inheritance"
    else
        echo -e "${RED}✗${NC} requirements-dev.txt - missing -r requirements.txt"
        VALIDATION_FAILED=1
    fi
fi

if [ -f "requirements-test.txt" ]; then
    if grep -q "^-r requirements.txt" requirements-test.txt; then
        echo -e "${GREEN}✓${NC} requirements-test.txt - uses -r inheritance"
    else
        echo -e "${RED}✗${NC} requirements-test.txt - missing -r requirements.txt"
        VALIDATION_FAILED=1
    fi
fi
echo ""

echo "Step 4: Checking for duplicate packages in requirements.txt..."
echo "-----------------------------------"
if [ -f "requirements.txt" ]; then
    DUPLICATES=$(grep -v "^#" requirements.txt | grep -v "^$" | sed 's/\[.*\]//g' | sed 's/[=<>].*//g' | sort | uniq -d)
    if [ -z "$DUPLICATES" ]; then
        echo -e "${GREEN}✓${NC} No duplicate packages found"
    else
        echo -e "${RED}✗${NC} Duplicate packages found:"
        echo "$DUPLICATES"
        VALIDATION_FAILED=1
    fi
fi
echo ""

echo "Step 5: Checking for security vulnerabilities (if safety installed)..."
echo "-----------------------------------"
if command -v safety &> /dev/null; then
    for req_file in "requirements.txt" "requirements-production.txt"; do
        if [ -f "$req_file" ]; then
            echo "Scanning: $req_file"
            if safety check -r "$req_file" --output text 2>&1 | grep -q "No known security vulnerabilities found"; then
                echo -e "${GREEN}✓${NC} $req_file - no known vulnerabilities"
            else
                echo -e "${YELLOW}⚠${NC} $req_file - vulnerabilities detected (see safety output)"
                # Don't fail on vulnerabilities, just warn
            fi
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} safety not installed, skipping vulnerability scan"
fi
echo ""

echo "=================================================="
if [ $VALIDATION_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed!${NC}"
    exit 1
fi
