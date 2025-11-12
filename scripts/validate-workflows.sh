#!/bin/bash
# CI/CD Workflow Validation Script
# Tests workflow files for syntax errors and common issues

set -e

echo "============================================"
echo "DevSkyy CI/CD Workflow Validation"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Function to print test result
print_result() {
    local test_name=$1
    local result=$2
    local message=$3
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $test_name"
        ((PASSED++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $test_name"
        echo -e "  ${RED}Error: $message${NC}"
        ((FAILED++))
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $test_name"
        echo -e "  ${YELLOW}Warning: $message${NC}"
        ((WARNINGS++))
    fi
}

echo "1. Checking workflow files exist..."
echo "-----------------------------------"

workflows=(
    ".github/workflows/ci-cd.yml"
    ".github/workflows/test.yml"
    ".github/workflows/security-scan.yml"
    ".github/workflows/performance.yml"
    ".github/workflows/codeql.yml"
    ".github/workflows/neon_workflow.yml"
)

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        print_result "$(basename $workflow)" "PASS"
    else
        print_result "$(basename $workflow)" "FAIL" "File not found"
    fi
done

echo ""
echo "2. Validating YAML syntax..."
echo "-----------------------------------"

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        if python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>/dev/null; then
            print_result "$(basename $workflow) syntax" "PASS"
        else
            error=$(python3 -c "import yaml; yaml.safe_load(open('$workflow'))" 2>&1 || true)
            print_result "$(basename $workflow) syntax" "FAIL" "$error"
        fi
    fi
done

echo ""
echo "3. Checking for removed redundant files..."
echo "-----------------------------------"

if [ ! -f ".github/workflows/python-package.yml" ]; then
    print_result "python-package.yml removed" "PASS"
else
    print_result "python-package.yml removed" "FAIL" "File should be deleted"
fi

if [ ! -f ".github/workflows/main.yml" ]; then
    print_result "main.yml removed" "PASS"
else
    print_result "main.yml removed" "FAIL" "File should be deleted"
fi

echo ""
echo "4. Checking for concurrency controls..."
echo "-----------------------------------"

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        if grep -q "concurrency:" "$workflow"; then
            print_result "$(basename $workflow) has concurrency" "PASS"
        else
            print_result "$(basename $workflow) has concurrency" "WARN" "No concurrency control found"
        fi
    fi
done

echo ""
echo "5. Checking test requirements..."
echo "-----------------------------------"

if [ -f "requirements-test.txt" ]; then
    print_result "requirements-test.txt exists" "PASS"
    
    # Check for pytest-rerunfailures
    if grep -q "pytest-rerunfailures" requirements-test.txt; then
        print_result "pytest-rerunfailures included" "PASS"
    else
        print_result "pytest-rerunfailures included" "FAIL" "Missing retry plugin"
    fi
    
    # Check for coverage tools
    if grep -q "pytest-cov" requirements-test.txt; then
        print_result "pytest-cov included" "PASS"
    else
        print_result "pytest-cov included" "FAIL" "Missing coverage tool"
    fi
else
    print_result "requirements-test.txt exists" "FAIL" "File not found"
fi

echo ""
echo "6. Checking test directory structure..."
echo "-----------------------------------"

test_dirs=(
    "tests/agents"
    "tests/api"
    "tests/security"
    "tests/ml"
    "tests/infrastructure"
    "tests/integration"
    "tests/e2e"
)

for dir in "${test_dirs[@]}"; do
    if [ -d "$dir" ]; then
        print_result "$dir exists" "PASS"
    else
        print_result "$dir exists" "WARN" "Directory not found"
    fi
done

echo ""
echo "7. Checking pytest configuration..."
echo "-----------------------------------"

if [ -f "pytest.ini" ]; then
    print_result "pytest.ini exists" "PASS"
    
    # Check for coverage threshold
    if grep -q "cov-fail-under=90" pytest.ini; then
        print_result "Coverage threshold 90% set" "PASS"
    else
        print_result "Coverage threshold 90% set" "WARN" "Threshold may not be 90%"
    fi
    
    # Check for asyncio mode
    if grep -q "asyncio_mode = auto" pytest.ini; then
        print_result "Asyncio mode configured" "PASS"
    else
        print_result "Asyncio mode configured" "WARN" "May cause async test issues"
    fi
else
    print_result "pytest.ini exists" "WARN" "Using default pytest config"
fi

echo ""
echo "8. Checking composite actions..."
echo "-----------------------------------"

if [ -f ".github/actions/setup-python-deps/action.yml" ]; then
    print_result "setup-python-deps action exists" "PASS"
else
    print_result "setup-python-deps action exists" "FAIL" "Composite action not found"
fi

echo ""
echo "9. Checking for workflow dispatch inputs..."
echo "-----------------------------------"

if grep -q "workflow_dispatch:" .github/workflows/ci-cd.yml; then
    print_result "ci-cd.yml has workflow_dispatch" "PASS"
    
    if grep -q "skip-tests:" .github/workflows/ci-cd.yml; then
        print_result "ci-cd.yml has skip-tests input" "PASS"
    else
        print_result "ci-cd.yml has skip-tests input" "WARN" "Input not found"
    fi
else
    print_result "ci-cd.yml has workflow_dispatch" "FAIL" "No manual trigger"
fi

echo ""
echo "10. Checking documentation..."
echo "-----------------------------------"

if [ -f ".github/workflows/README.md" ]; then
    print_result "Workflow README exists" "PASS"
else
    print_result "Workflow README exists" "WARN" "Missing documentation"
fi

if [ -f ".github/workflows/WORKFLOW_STATUS.md" ]; then
    print_result "Workflow status doc exists" "PASS"
else
    print_result "Workflow status doc exists" "WARN" "Missing status documentation"
fi

if [ -f "CI_CD_REFACTORING_SUMMARY.md" ]; then
    print_result "Refactoring summary exists" "PASS"
else
    print_result "Refactoring summary exists" "WARN" "Missing refactoring documentation"
fi

echo ""
echo "============================================"
echo "Validation Summary"
echo "============================================"
echo -e "${GREEN}Passed:${NC} $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC} $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Commit your changes"
    echo "2. Push to feature branch"
    echo "3. Create pull request"
    echo "4. Monitor CI/CD runs"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi
