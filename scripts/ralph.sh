#!/usr/bin/env bash
# ═══════════════════════════════════════
#  RALPH — Recursive Auto-Loop Platform Health
#  Self-healing verification loop for DevSkyy
#
#  Usage:
#    ./scripts/ralph.sh           # Run full loop (max 3 iterations)
#    ./scripts/ralph.sh --max 5   # Custom max iterations
#    ./scripts/ralph.sh --phase 2 # Run single phase
#    ./scripts/ralph.sh --fast    # Quick check (lint + build + security only)
#    ./scripts/ralph.sh --watch   # Continuous mode (re-runs on file changes)
# ═══════════════════════════════════════

set -euo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo /Users/theceo/DevSkyy)"

MAX_LOOPS=${MAX_LOOPS:-3}
SINGLE_PHASE=""
WATCH_MODE=false
FAST_MODE=false
LOOP_COUNT=0
FAILED_PHASES=()
WARN_COUNT=0
RALPH_LOG="./logs/ralph-$(date +%Y%m%d-%H%M%S).log"

mkdir -p logs

# Parse args
while [[ $# -gt 0 ]]; do
    case $1 in
        --max) MAX_LOOPS="$2"; shift 2;;
        --phase) SINGLE_PHASE="$2"; shift 2;;
        --watch) WATCH_MODE=true; shift;;
        --fast) FAST_MODE=true; shift;;
        *) shift;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

log() { echo -e "$1" | tee -a "$RALPH_LOG"; }
pass() { log "  ${GREEN}✅ PASS${NC} — $1"; }
warn() { log "  ${YELLOW}⚠️  WARN${NC} — $1"; WARN_COUNT=$((WARN_COUNT + 1)); }
fail() { log "  ${RED}❌ FAIL${NC} — $1"; FAILED_PHASES+=("$2"); }
phase() { log "\n${CYAN}━━━ Phase $1: $2 ━━━${NC}"; }

# ═══════════════════════════════════════
# PHASES
# ═══════════════════════════════════════

phase_1_code_quality() {
    phase 1 "Code Quality"
    local errors=0

    # Lint
    if python3 -m ruff check . --quiet 2>/dev/null; then
        pass "ruff lint clean"
    else
        log "  ${YELLOW}⚡ AUTO-FIX${NC} — running ruff --fix + isort"
        python3 -m ruff check --fix . 2>/dev/null || true
        python3 -m isort . --quiet 2>/dev/null || true
        if python3 -m ruff check . --quiet 2>/dev/null; then
            pass "ruff lint clean (auto-fixed)"
        else
            local remaining
            remaining=$(python3 -m ruff check . --statistics 2>&1 | tail -1 | grep -oE "[0-9]+ errors" || echo "unknown")
            fail "ruff lint: $remaining remain" "1"
            errors=1
        fi
    fi

    # Format check
    if python3 -m ruff format --check . --quiet 2>/dev/null; then
        pass "ruff format clean"
    else
        log "  ${YELLOW}⚡ AUTO-FIX${NC} — running ruff format"
        python3 -m ruff format . 2>/dev/null || true
        pass "ruff format (auto-fixed)"
    fi

    # Secrets check — exclude .venv, node_modules, __pycache__
    if grep -rn "api_key\s*=\s*['\"]sk-\|secret_key\s*=\s*['\"]" \
        --include="*.py" --include="*.js" \
        --exclude-dir=.venv --exclude-dir=.venv-imagery --exclude-dir=.venv-lora \
        --exclude-dir=.venv-agents --exclude-dir=node_modules --exclude-dir=__pycache__ \
        . 2>/dev/null \
        | grep -v "test_\|\.env\|os.getenv\|CLAUDE.md\|os\.environ\|getenv\|# example\|# noqa\|docstring" > /dev/null 2>&1; then
        fail "Hardcoded secrets detected in source" "1"
        errors=1
    else
        pass "No hardcoded secrets"
    fi

    return $errors
}

phase_2_tests() {
    phase 2 "Tests"
    local output
    output=$(python3 -m pytest tests/ --tb=no -q 2>&1 | tail -3)

    if echo "$output" | grep -q "failed"; then
        local summary
        summary=$(echo "$output" | grep -E "passed|failed" | tail -1)
        fail "Tests: $summary" "2"
        return 1
    else
        local summary
        summary=$(echo "$output" | grep -E "passed|skipped" | tail -1)
        pass "Tests: ${summary:-all passing}"
        return 0
    fi
}

phase_env_check() {
    phase "1b" "Environment & Gitignore"
    local errors=0

    # .env existence
    if [[ -f ".env" ]]; then
        pass ".env file exists"
    else
        fail ".env file missing — copy from .env.example" "env"
        errors=1
        return $errors
    fi

    # Required keys in .env
    local required_keys=("JWT_SECRET_KEY" "DATABASE_URL" "ENVIRONMENT")
    local missing=()
    for key in "${required_keys[@]}"; do
        if ! grep -q "^${key}=" .env 2>/dev/null; then
            missing+=("$key")
        fi
    done
    if [[ ${#missing[@]} -gt 0 ]]; then
        fail "Missing required .env keys: ${missing[*]}" "env"
        errors=1
    else
        pass "All required .env keys present"
    fi

    # Check for placeholder values
    if grep -qE "^JWT_SECRET_KEY=your-jwt-secret|^ENCRYPTION_MASTER_KEY=your-base64" .env 2>/dev/null; then
        warn "Default placeholder keys in .env — generate real keys for production"
    fi

    # .gitignore checks
    if [[ -f ".gitignore" ]]; then
        local git_required=(".env" "*.db" "*.sqlite" ".venv/" "secrets/" "*.pem" "*.key" ".claude/")
        local git_missing=()
        for pattern in "${git_required[@]}"; do
            if ! grep -qF "$pattern" .gitignore 2>/dev/null; then
                git_missing+=("$pattern")
            fi
        done
        if [[ ${#git_missing[@]} -gt 0 ]]; then
            fail ".gitignore missing patterns: ${git_missing[*]}" "env"
            errors=1
        else
            pass ".gitignore covers all sensitive patterns"
        fi
    else
        fail ".gitignore file missing" "env"
        errors=1
    fi

    # Verify .env is not tracked by git
    if git ls-files --error-unmatch .env 2>/dev/null; then
        fail ".env is tracked by git — remove with: git rm --cached .env" "env"
        errors=1
    else
        pass ".env is not tracked by git"
    fi

    return $errors
}

phase_3_security() {
    phase 3 "Security"
    local errors=0

    # Check error leakage — count occurrences, warn if <110 (known tech debt), fail if growing
    local leakage_count
    leakage_count=$(grep -rn "str(exc)\|str(e)" --include="*.py" api/ \
        --exclude-dir=__pycache__ 2>/dev/null \
        | grep -v "logger\.\|log\.\|logging\.\|test_\|#\|_log\.\|structlog" \
        | wc -l | tr -d ' ')

    if [[ "$leakage_count" -eq 0 ]]; then
        pass "No error leakage in API layer"
    elif [[ "$leakage_count" -le 110 ]]; then
        warn "Error leakage: $leakage_count instances (known tech debt, target: 0)"
    else
        fail "Error leakage growing: $leakage_count instances (baseline: ~105)" "3"
        errors=1
    fi

    # Check auth on endpoints
    if grep -rn "async def.*request\|async def.*Request" api/ --include="*.py" \
        | grep -v "Depends\|health\|root\|docs\|ready\|live\|webhook\|graphql\|test_\|__pycache__" \
        | head -5 | grep -q .; then
        warn "Some endpoints may lack auth (review manually)"
    else
        pass "Auth coverage looks good"
    fi

    # Check for debug prints
    if grep -rn "print(" --include="*.py" api/ \
        --exclude-dir=__pycache__ 2>/dev/null \
        | grep -v "test_\|#\|__main__" | head -3 | grep -q .; then
        warn "Debug print() calls found in API layer"
    else
        pass "No debug prints in API layer"
    fi

    return $errors
}

phase_4_api_health() {
    phase 4 "API Health"

    local route_count
    route_count=$(python3 -c "
from main_enterprise import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
critical = ['/health', '/api/v1/auth/token', '/api/v1/auth/register', '/api/v1/auth/me']
missing = [c for c in critical if c not in routes]
if missing:
    print(f'MISSING:{len(routes)}:{\",\".join(missing)}')
else:
    print(f'OK:{len(routes)}')
" 2>&1 | grep -E "^OK:|^MISSING:" || echo "ERROR:0")

    if echo "$route_count" | grep -q "^OK:"; then
        local count=$(echo "$route_count" | cut -d: -f2)
        pass "API healthy — $count routes, all critical present"
        return 0
    else
        fail "API issues — $route_count" "4"
        return 1
    fi
}

phase_5_database() {
    phase 5 "Database Integrity"

    local db_check
    db_check=$(python3 -c "
import asyncio
from database.db import db_manager, ProductRepository, UserRepository

async def check():
    await db_manager.initialize()
    async with db_manager.session() as db:
        from sqlalchemy import select, func
        from database.db import Product
        result = await db.execute(select(func.count()).select_from(Product))
        pcount = result.scalar()
        admin = await UserRepository(db).get_by_username('admin')
        print(f'OK:{pcount}:{\"yes\" if admin else \"no\"}')
    await db_manager.close()

asyncio.run(check())
" 2>&1 | grep "^OK:" || echo "ERROR:0:no")

    if echo "$db_check" | grep -q "^OK:"; then
        local pcount=$(echo "$db_check" | cut -d: -f2)
        local admin=$(echo "$db_check" | cut -d: -f3)
        if [[ "$admin" == "yes" ]]; then
            pass "Database OK — $pcount products, admin exists"
            return 0
        else
            fail "Admin user missing — run: python3 -m database.seed_admin" "5"
            # Auto-fix
            log "  ${YELLOW}⚡ AUTO-FIX${NC} — seeding admin user"
            python3 -m database.seed_admin 2>/dev/null && pass "Admin seeded" && return 0
            return 1
        fi
    else
        fail "Database error" "5"
        return 1
    fi
}

phase_6_wordpress() {
    phase 6 "WordPress Sync"

    local wp_check
    wp_check=$(python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('WORDPRESS_SITE_URL', os.getenv('WORDPRESS_URL', ''))
auth = os.getenv('WP_AUTH_USER', '')
print(f'{\"OK\" if url else \"MISSING_URL\"}:{\"OK\" if auth else \"NO_AUTH\"}')
" 2>&1 | tail -1)

    if echo "$wp_check" | grep -q "^OK:OK"; then
        pass "WordPress env configured"
        return 0
    elif echo "$wp_check" | grep -q "^OK:"; then
        warn "WordPress URL set but auth credentials missing"
        return 0
    else
        fail "WORDPRESS_SITE_URL not set in .env" "6"
        return 1
    fi
}

phase_7_agents() {
    phase 7 "Agent System"

    local agent_check
    agent_check=$(python3 -c "
import importlib
agents = [
    ('agents.core.commerce.sub_agents.product_ops', 'ProductOpsSubAgent'),
    ('agents.core.commerce.sub_agents.wordpress_assets', 'WordPressAssetsSubAgent'),
    ('agents.core.commerce.sub_agents.wordpress_bridge', 'WordPressBridgeSubAgent'),
    ('agents.core.content.sub_agents.seo_copywriter', 'SeoCopywriterSubAgent'),
    ('agents.core.content.sub_agents.collection_content', 'CollectionContentSubAgent'),
    ('agents.core.creative.sub_agents.brand_creative', 'BrandCreativeSubAgent'),
    ('agents.core.marketing.sub_agents.social_media', 'SocialMediaSubAgent'),
    ('agents.core.marketing.sub_agents.campaign_ops', 'CampaignOpsSubAgent'),
    ('agents.core.operations.sub_agents.security_monitor', 'SecurityMonitorSubAgent'),
    ('agents.core.operations.sub_agents.coding_doctor', 'CodingDoctorSubAgent'),
    ('agents.core.operations.sub_agents.deploy_health', 'DeployHealthSubAgent'),
    ('agents.core.analytics.sub_agents.analytics_ops', 'AnalyticsOpsSubAgent'),
    ('agents.core.imagery.sub_agents.gemini_image', 'GeminiImageSubAgent'),
    ('agents.core.imagery.sub_agents.fashn_vton', 'FashnVtonSubAgent'),
    ('agents.core.imagery.sub_agents.tripo_3d', 'Tripo3dSubAgent'),
    ('agents.core.imagery.sub_agents.meshy_3d', 'Meshy3dSubAgent'),
    ('agents.core.imagery.sub_agents.hf_spaces', 'HfSpacesSubAgent'),
    ('agents.core.web_builder.sub_agents.web_dev', 'WebDevSubAgent'),
]
ok = 0
for mod_path, cls_name in agents:
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)
    if hasattr(cls, 'system_prompt') and len(cls.system_prompt) > 20:
        ok += 1
print(f'{ok}/{len(agents)}')
" 2>&1 | tail -1)

    if [[ "$agent_check" == "18/18" ]]; then
        pass "All 18 sub-agents verified"
        return 0
    else
        fail "Agents: $agent_check healthy" "7"
        return 1
    fi
}

phase_8_build() {
    phase 8 "Build & Imports"

    if python3 -c "from main_enterprise import app" 2>/dev/null; then
        pass "Main app imports clean"
    else
        fail "main_enterprise.py has import errors" "8"
        return 1
    fi

    if python3 -c "
from security.jwt_oauth2_auth import auth_router, jwt_manager, password_manager
from database.db import db_manager, ProductRepository, UserRepository
from agents.core.sub_agent import SubAgent
" 2>/dev/null; then
        pass "All critical modules import clean"
        return 0
    else
        fail "Critical module import failure" "8"
        return 1
    fi
}

phase_9_docs() {
    phase 9 "Documentation"
    # Lightweight check
    if [[ -f "CLAUDE.md" ]] && [[ -f "docs/ARCHITECTURE.md" ]]; then
        pass "Core docs present"
    else
        warn "Missing core documentation files"
    fi
    return 0
}

phase_10_final() {
    phase 10 "Final Audit"

    if [[ ${#FAILED_PHASES[@]} -eq 0 ]]; then
        if [[ $WARN_COUNT -gt 0 ]]; then
            pass "All phases green ($WARN_COUNT warnings)"
        else
            pass "All phases green — perfect score"
        fi
        return 0
    else
        fail "Failed phases: ${FAILED_PHASES[*]}" "10"
        return 1
    fi
}

# ═══════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════

run_loop() {
    LOOP_COUNT=$((LOOP_COUNT + 1))
    FAILED_PHASES=()
    WARN_COUNT=0

    log "\n${BOLD}═══════════════════════════════════════${NC}"
    log "${BOLD}  RALPH — Loop #$LOOP_COUNT / $MAX_LOOPS${NC}"
    if $FAST_MODE; then
        log "${BOLD}  MODE: FAST (lint + build + security)${NC}"
    fi
    log "${BOLD}═══════════════════════════════════════${NC}"

    if [[ -n "$SINGLE_PHASE" ]]; then
        case "$SINGLE_PHASE" in
            1) phase_1_code_quality || true ;;
            2) phase_2_tests || true ;;
            3) phase_3_security || true ;;
            4) phase_4_api_health || true ;;
            5) phase_5_database || true ;;
            6) phase_6_wordpress || true ;;
            7) phase_7_agents || true ;;
            8) phase_8_build || true ;;
            9) phase_9_docs || true ;;
            10) phase_10_final || true ;;
            *) log "  ${RED}Unknown phase: $SINGLE_PHASE${NC}" ;;
        esac
    elif $FAST_MODE; then
        # Fast mode: lint + env + security + build only (~5 seconds)
        phase_1_code_quality || true
        phase_env_check || true
        phase_3_security || true
        phase_8_build || true
        phase_10_final || true
    else
        phase_1_code_quality || true
        phase_env_check || true
        phase_2_tests || true
        phase_3_security || true
        phase_4_api_health || true
        phase_5_database || true
        phase_6_wordpress || true
        phase_7_agents || true
        phase_8_build || true
        phase_9_docs || true
        phase_10_final || true
    fi

    # Report
    log "\n${BOLD}═══════════════════════════════════════${NC}"
    if [[ ${#FAILED_PHASES[@]} -eq 0 ]]; then
        log "${GREEN}${BOLD}  RALPH VERIFIED ✅  (Loop #$LOOP_COUNT)${NC}"
        log "${BOLD}═══════════════════════════════════════${NC}"
        log "Log: $RALPH_LOG"
        return 0
    else
        log "${RED}${BOLD}  RALPH FAILED ❌  (Loop #$LOOP_COUNT)${NC}"
        log "${RED}  Failed phases: ${FAILED_PHASES[*]}${NC}"
        log "${BOLD}═══════════════════════════════════════${NC}"

        if [[ $LOOP_COUNT -ge $MAX_LOOPS ]]; then
            log "\n${RED}${BOLD}  MAX LOOPS REACHED ($MAX_LOOPS). Escalating to user.${NC}"
            log "  Log: $RALPH_LOG"
            return 1
        else
            log "\n${YELLOW}${BOLD}  Restarting loop...${NC}"
            sleep 2
            run_loop
        fi
    fi
}

# Watch mode — re-run on file changes
if $WATCH_MODE; then
    log "${CYAN}RALPH WATCH MODE — monitoring for changes...${NC}"
    while true; do
        run_loop || true
        log "\n${CYAN}Waiting for file changes... (Ctrl+C to stop)${NC}"
        fswatch -1 -r --include='\.py$' --include='\.php$' --include='\.js$' \
            --exclude='\.git' --exclude='__pycache__' --exclude='node_modules' \
            . 2>/dev/null || inotifywait -r -e modify --include='.*\.(py|php|js)$' . 2>/dev/null || sleep 30
        log "\n${YELLOW}Change detected — restarting RALPH...${NC}"
        LOOP_COUNT=0
    done
else
    run_loop
fi
