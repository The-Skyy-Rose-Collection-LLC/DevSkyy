#!/usr/bin/env bash
# DevSkyy one-command bootstrap.
#
# Idempotent. Safe to re-run. Gets a clone-to-running shell in a single command.
#
# What it does (in order):
#   1. Sanity-check Python (3.11+) and Node (>=22) are on PATH.
#   2. Create .env from .env.example if missing (never overwrites).
#   3. Install Python package in editable mode with dev extras.
#   4. Install frontend npm deps.
#   5. Print a green checklist of what was set up and a short "next steps" block.
#
# What it deliberately does NOT do:
#   - Touch production. Never deploys, never calls paid APIs.
#   - Install the ADK venv (.venv-agents/) — that requires numpy isolation and
#     is documented separately in CLAUDE.md.
#   - Install the WordPress/PHP toolchain — `cd wordpress-theme && composer install`
#     is its own concern and is gated behind PHPCS work.
#   - Run migrations. The default SQLite DB is created lazily by the API on first
#     request; Postgres is opt-in via DATABASE_URL.
#
# Usage:
#   bash scripts/bootstrap.sh
#   make bootstrap   # equivalent
#
# Exit codes:
#   0 — bootstrap completed (all steps successful, or skipped because already present)
#   1 — prerequisite missing (Python or Node not on PATH, wrong version)
#   2 — install failure (pip or npm exited non-zero)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# --- pretty printing ---------------------------------------------------------
if [[ -t 1 ]]; then
    BOLD=$'\033[1m'
    GREEN=$'\033[32m'
    YELLOW=$'\033[33m'
    RED=$'\033[31m'
    DIM=$'\033[2m'
    RESET=$'\033[0m'
else
    BOLD=""; GREEN=""; YELLOW=""; RED=""; DIM=""; RESET=""
fi

step()  { printf '%s==>%s %s\n' "$BOLD$GREEN" "$RESET" "$1"; }
warn()  { printf '%s!!%s  %s\n' "$BOLD$YELLOW" "$RESET" "$1"; }
fail()  { printf '%sxx%s  %s\n' "$BOLD$RED" "$RESET" "$1" >&2; }
note()  { printf '%s     %s%s\n' "$DIM" "$1" "$RESET"; }

# --- prerequisites -----------------------------------------------------------
step "Checking prerequisites"

if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 not found on PATH. Install Python 3.11+ from python.org or your package manager."
    exit 1
fi
PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
PYTHON_MAJOR="${PYTHON_VERSION%%.*}"
PYTHON_MINOR="${PYTHON_VERSION##*.}"
if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 11 ]]; }; then
    fail "Python 3.11+ required, found $PYTHON_VERSION. Upgrade Python."
    exit 1
fi
note "Python $PYTHON_VERSION OK"

if ! command -v node >/dev/null 2>&1; then
    fail "node not found on PATH. Install Node.js 22 from nodejs.org or via nvm."
    exit 1
fi
NODE_MAJOR="$(node -p 'process.versions.node.split(".")[0]')"
if [[ "$NODE_MAJOR" -lt 22 ]]; then
    fail "Node 22+ required, found $(node --version). Run \`nvm use\` (.nvmrc pins 22)."
    exit 1
fi
note "Node $(node --version) OK"

if ! command -v npm >/dev/null 2>&1; then
    fail "npm not found on PATH. Comes bundled with Node — reinstall Node if missing."
    exit 1
fi
note "npm $(npm --version) OK"

if ! command -v pip >/dev/null 2>&1 && ! command -v pip3 >/dev/null 2>&1; then
    fail "pip not found on PATH. \`python3 -m ensurepip --upgrade\` or your package manager."
    exit 1
fi
PIP="$(command -v pip || command -v pip3)"
note "pip at $PIP OK"

# --- .env file ---------------------------------------------------------------
step "Provisioning .env"

if [[ -f .env ]]; then
    note ".env already exists — leaving untouched"
else
    if [[ ! -f .env.example ]]; then
        warn ".env.example not found — skipping .env creation"
    else
        cp .env.example .env
        note "Created .env from .env.example"
        warn "Edit .env and fill in any keys you need before running paid APIs"
    fi
fi

# --- Python deps -------------------------------------------------------------
step "Installing Python package (editable, dev extras)"
note "Running: $PIP install -e \".[dev]\""

if ! "$PIP" install -e ".[dev]" --quiet 2>&1 | tail -20; then
    fail "Python install failed — see output above"
    exit 2
fi
note "Python install OK"

# --- Frontend deps -----------------------------------------------------------
step "Installing frontend npm deps"
if [[ ! -d frontend ]]; then
    warn "frontend/ directory not found — skipping (unexpected layout)"
else
    pushd frontend >/dev/null
    if [[ -d node_modules ]] && [[ -f package-lock.json ]] && [[ node_modules/.package-lock.json -nt package-lock.json ]]; then
        note "frontend/node_modules is up to date — skipping npm install"
    else
        note "Running: npm ci --no-audit --no-fund (in frontend/)"
        if ! npm ci --no-audit --no-fund 2>&1 | tail -20; then
            warn "npm ci failed — falling back to npm install"
            if ! npm install --no-audit --no-fund 2>&1 | tail -20; then
                fail "Frontend install failed — see output above"
                popd >/dev/null
                exit 2
            fi
        fi
    fi
    popd >/dev/null
fi
note "Frontend install OK"

# --- summary -----------------------------------------------------------------
echo
step "Bootstrap complete"
cat <<EOF

  ${BOLD}Next steps:${RESET}

  Run the API:        ${GREEN}uvicorn main_enterprise:app --reload --port 8000${RESET}
  Run the dashboard:  ${GREEN}cd frontend && npm run dev${RESET}
  Run tests:          ${GREEN}make test-fast${RESET}
  Full CI locally:    ${GREEN}make ci${RESET}

  ${BOLD}Workspaces this script did NOT touch (run separately if you need them):${RESET}

  ADK agents (.venv-agents/)  see CLAUDE.md  -  numpy conflict, isolated venv
  WordPress theme              cd wordpress-theme/skyyrose-flagship && composer install
  Imagery (Nano Banana)        see docs/NANO_BANANA.md

EOF
