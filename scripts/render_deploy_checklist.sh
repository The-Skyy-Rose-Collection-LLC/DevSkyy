#!/usr/bin/env bash
#
# Render Deployment Pre-Flight Checklist
# =======================================
#
# Validates that all prerequisites are met before deploying to Render.
# Run this script before initiating deployment to catch issues early.
#
# Usage:
#   ./scripts/render_deploy_checklist.sh
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  DevSkyy Render Deployment Pre-Flight Checklist       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    echo -e "  ${YELLOW}→${NC} $2"
    ((FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    echo -e "  ${YELLOW}→${NC} $2"
    ((WARNINGS++))
}

# 1. Check Git Repository
echo -e "${BLUE}[1/10] Git Repository${NC}"
if [ -d .git ]; then
    check_pass "Git repository initialized"

    # Check if on main branch
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if [ "$BRANCH" = "main" ]; then
        check_pass "On main branch"
    else
        check_warn "Not on main branch (current: $BRANCH)" "Switch to main: git checkout main"
    fi

    # Check for uncommitted changes
    if [ -z "$(git status --porcelain)" ]; then
        check_pass "No uncommitted changes"
    else
        check_warn "Uncommitted changes detected" "Commit changes: git add . && git commit -m 'message'"
    fi

    # Check remote
    if git remote -v | grep -q "github.com"; then
        check_pass "GitHub remote configured"
    else
        check_fail "GitHub remote not found" "Add remote: git remote add origin https://github.com/..."
    fi
else
    check_fail "Not a git repository" "Initialize: git init"
fi
echo ""

# 2. Check Required Files
echo -e "${BLUE}[2/10] Required Configuration Files${NC}"
FILES=(
    "render.yaml:Render deployment blueprint"
    "requirements.txt:Python dependencies"
    "main_enterprise.py:FastAPI application entry point"
    ".env.production:Production environment template"
)

for item in "${FILES[@]}"; do
    FILE="${item%%:*}"
    DESC="${item##*:}"
    if [ -f "$FILE" ]; then
        check_pass "$DESC ($FILE)"
    else
        check_fail "$DESC missing" "File not found: $FILE"
    fi
done
echo ""

# 3. Validate render.yaml
echo -e "${BLUE}[3/10] Render Blueprint Validation${NC}"
if [ -f render.yaml ]; then
    # Check for required fields
    if grep -q "type: web" render.yaml; then
        check_pass "Web service type defined"
    else
        check_fail "Web service type missing" "Add 'type: web' to render.yaml"
    fi

    if grep -q "buildCommand:" render.yaml; then
        check_pass "Build command specified"
    else
        check_fail "Build command missing" "Add buildCommand to render.yaml"
    fi

    if grep -q "startCommand:" render.yaml; then
        check_pass "Start command specified"
    else
        check_fail "Start command missing" "Add startCommand to render.yaml"
    fi

    if grep -q "healthCheckPath:" render.yaml; then
        check_pass "Health check path configured"
    else
        check_warn "Health check path not configured" "Recommended: healthCheckPath: /health"
    fi
else
    check_fail "render.yaml not found" "Create render.yaml configuration"
fi
echo ""

# 4. Check Python Requirements
echo -e "${BLUE}[4/10] Python Dependencies${NC}"
if [ -f requirements.txt ]; then
    # Check for critical packages
    REQUIRED_PACKAGES=(
        "fastapi"
        "uvicorn"
        "pydantic"
        "sqlalchemy"
        "asyncpg"
        "redis"
    )

    for pkg in "${REQUIRED_PACKAGES[@]}"; do
        if grep -qi "^${pkg}" requirements.txt; then
            check_pass "Required package: $pkg"
        else
            check_fail "Missing package: $pkg" "Add to requirements.txt: $pkg>=version"
        fi
    done

    # Check for version pins
    if grep -q "==" requirements.txt; then
        check_pass "Versions pinned (recommended for production)"
    else
        check_warn "Versions not pinned" "Recommended: Use == for exact versions"
    fi
else
    check_fail "requirements.txt not found" "Create requirements.txt"
fi
echo ""

# 5. Check Application Entry Point
echo -e "${BLUE}[5/10] Application Entry Point${NC}"
if [ -f main_enterprise.py ]; then
    if grep -q "app = FastAPI" main_enterprise.py; then
        check_pass "FastAPI app instance found"
    else
        check_fail "FastAPI app not found in main_enterprise.py" "Ensure 'app = FastAPI()' exists"
    fi

    if grep -q "@app.get.*health" main_enterprise.py; then
        check_pass "Health check endpoint defined"
    else
        check_warn "Health check endpoint not found" "Recommended: Add @app.get('/health') endpoint"
    fi
else
    check_fail "main_enterprise.py not found" "Create FastAPI application"
fi
echo ""

# 6. Environment Variables Check
echo -e "${BLUE}[6/10] Environment Variables${NC}"
if [ -f .env.production ]; then
    # Check for placeholder values that need replacement
    PLACEHOLDERS=$(grep -E "(REPLACE|CHANGE|GENERATE)" .env.production | wc -l)

    if [ "$PLACEHOLDERS" -gt 0 ]; then
        check_warn "$PLACEHOLDERS placeholder values found in .env.production" "These need to be set in Render dashboard"
    else
        check_pass "No placeholder values in .env.production"
    fi

    # Check for critical variables
    CRITICAL_VARS=(
        "DATABASE_URL"
        "REDIS_URL"
        "JWT_SECRET_KEY"
        "ENCRYPTION_MASTER_KEY"
    )

    for var in "${CRITICAL_VARS[@]}"; do
        if grep -q "^${var}=" .env.production; then
            check_pass "Variable defined: $var"
        else
            check_fail "Missing variable: $var" "Add to .env.production and Render dashboard"
        fi
    done

    # Check for at least one LLM provider
    if grep -qE "^(OPENAI_API_KEY|ANTHROPIC_API_KEY|GOOGLE_AI_API_KEY)=" .env.production; then
        check_pass "LLM provider API key configured"
    else
        check_warn "No LLM provider API key found" "Required: Add at least one LLM API key"
    fi
else
    check_fail ".env.production not found" "Create from template or run ./scripts/generate_secrets.sh"
fi
echo ""

# 7. Check for Sensitive Data
echo -e "${BLUE}[7/10] Security Scan${NC}"
# Check if any actual API keys are committed
if git ls-files | xargs grep -l "sk-[a-zA-Z0-9]\{32,\}" 2>/dev/null; then
    check_fail "Potential API keys found in committed files" "Remove API keys from git history"
else
    check_pass "No exposed API keys in git"
fi

# Check .gitignore
if [ -f .gitignore ]; then
    if grep -q ".env.production" .gitignore; then
        check_pass ".env.production in .gitignore"
    else
        check_warn ".env.production not in .gitignore" "Add to .gitignore to prevent commits"
    fi
else
    check_warn ".gitignore not found" "Create .gitignore and add sensitive files"
fi
echo ""

# 8. Database Configuration
echo -e "${BLUE}[8/10] Database Requirements${NC}"
# Check for migration files or database setup
if [ -d "migrations" ] || [ -d "alembic" ]; then
    check_pass "Database migrations directory found"
else
    check_warn "No migration directory found" "Consider using Alembic for database migrations"
fi

# Check for database models
if find . -name "models.py" -o -name "database.py" | grep -q .; then
    check_pass "Database models found"
else
    check_warn "No database models found" "Verify database setup is correct"
fi
echo ""

# 9. Check Documentation
echo -e "${BLUE}[9/10] Documentation${NC}"
if [ -f "README.md" ]; then
    check_pass "README.md exists"
else
    check_warn "README.md not found" "Create README with setup instructions"
fi

if [ -f "docs/deployment/RENDER_DEPLOYMENT_GUIDE.md" ]; then
    check_pass "Render deployment guide exists"
else
    check_warn "Deployment guide not found" "Create deployment documentation"
fi

if [ -f "CHANGELOG.md" ]; then
    check_pass "CHANGELOG.md exists"
else
    check_warn "CHANGELOG.md not found" "Consider maintaining a changelog"
fi
echo ""

# 10. Pre-deployment Commands
echo -e "${BLUE}[10/10] Pre-deployment Commands${NC}"

# Check if tests exist
if [ -d "tests" ]; then
    check_pass "Tests directory exists"

    # Try to run tests if pytest is available
    if command -v pytest &> /dev/null; then
        echo -e "  ${YELLOW}→${NC} Running tests..."
        if pytest tests/ -v --tb=short 2>&1 | tail -5; then
            check_pass "Tests passed"
        else
            check_warn "Some tests failed" "Fix failing tests before deploying"
        fi
    else
        check_warn "pytest not installed" "Install: pip install pytest"
    fi
else
    check_warn "No tests directory found" "Consider adding tests"
fi

# Check code formatting
if command -v black &> /dev/null; then
    if black --check . 2>&1 | grep -q "reformatted"; then
        check_warn "Code needs formatting" "Run: black ."
    else
        check_pass "Code is formatted"
    fi
else
    check_warn "black not installed" "Install: pip install black"
fi

# Check linting
if command -v ruff &> /dev/null; then
    if ruff check . 2>&1 | grep -q "error"; then
        check_warn "Linting errors found" "Run: ruff check . --fix"
    else
        check_pass "No linting errors"
    fi
else
    check_warn "ruff not installed" "Install: pip install ruff"
fi

echo ""

# Summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Summary                                               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo -e ""
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo -e ""

# Deployment readiness
if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ Ready for deployment!${NC}"
        echo -e "  Next steps:"
        echo -e "  1. Push to GitHub: ${BLUE}git push origin main${NC}"
        echo -e "  2. Deploy to Render: ${BLUE}https://dashboard.render.com${NC}"
        echo -e "  3. Follow: ${BLUE}docs/deployment/RENDER_DEPLOYMENT_GUIDE.md${NC}"
    else
        echo -e "${YELLOW}⚠ Ready with warnings${NC}"
        echo -e "  Address warnings for best results, then deploy."
    fi
    exit 0
else
    echo -e "${RED}✗ Not ready for deployment${NC}"
    echo -e "  Fix all failed checks before deploying."
    exit 1
fi
