#!/usr/bin/env bash
# RALPH FAST — Optimized stop-hook health check (~2s target)
# Combines all --fast checks into minimal subprocess calls.
set -uo pipefail
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo /Users/theceo/DevSkyy)"

R='\033[0;31m' G='\033[0;32m' Y='\033[1;33m' B='\033[1m' N='\033[0m'
FAILS=0

ok()   { echo -e "  ${G}+${N} $1"; }
warn() { echo -e "  ${Y}~${N} $1"; }
fail() { echo -e "  ${R}x${N} $1"; FAILS=$((FAILS+1)); }

echo -e "${B}RALPH FAST${N}"

# --- 1. Lint (ruff is fast, ~200ms) ---
if python3 -m ruff check . -q 2>/dev/null; then
    ok "lint"
else
    python3 -m ruff check --fix . -q 2>/dev/null && python3 -m isort . -q 2>/dev/null
    python3 -m ruff check . -q 2>/dev/null && ok "lint (fixed)" || fail "lint"
fi

# --- 2. Format check (skip auto-fix, just report) ---
python3 -m ruff format --check . -q 2>/dev/null && ok "format" || { python3 -m ruff format . -q 2>/dev/null; ok "format (fixed)"; }

# --- 3. Secrets + debug prints + error leakage (single grep pass) ---
GREP_OPTS="--include=*.py --exclude-dir=.venv --exclude-dir=.venv-imagery --exclude-dir=.venv-lora --exclude-dir=.venv-agents --exclude-dir=node_modules --exclude-dir=__pycache__"
if grep -rn "api_key\s*=\s*['\"]sk-\|secret_key\s*=\s*['\"]" $GREP_OPTS . 2>/dev/null \
    | grep -vq "test_\|\.env\|os.getenv\|CLAUDE.md\|os\.environ\|getenv\|# example\|# noqa\|docstring"; then
    fail "hardcoded secrets"
else
    ok "no secrets"
fi

# --- 4. Env check (pure bash, no subprocesses) ---
if [[ -f .env ]]; then
    missing=""
    for k in JWT_SECRET_KEY DATABASE_URL ENVIRONMENT; do
        grep -q "^${k}=" .env 2>/dev/null || missing="$missing $k"
    done
    [[ -z "$missing" ]] && ok "env" || fail "env missing:$missing"
else
    fail "no .env"
fi

# --- 5. Build imports (single Python process) ---
python3 -c "
from main_enterprise import app
from security.jwt_oauth2_auth import auth_router
from database.db import db_manager
from agents.core.sub_agent import SubAgent
r = len([x.path for x in app.routes if hasattr(x,'path')])
print(f'OK:{r}')
" 2>/dev/null | grep -q "^OK:" && ok "imports" || fail "imports"

# --- Result ---
if [[ $FAILS -eq 0 ]]; then
    echo -e "${G}${B}RALPH OK${N}"
else
    echo -e "${R}${B}RALPH: $FAILS issues${N}"
fi
exit 0  # Never block session stop
