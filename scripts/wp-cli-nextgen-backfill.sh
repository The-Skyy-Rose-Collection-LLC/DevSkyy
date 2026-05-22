#!/usr/bin/env bash
# scripts/wp-cli-nextgen-backfill.sh
#
# Runs `wp skyyrose nextgen-backfill` on the production WordPress.com host
# via the same SSH transport that deploy-theme.sh uses. Generates AVIF + WebP
# siblings for every existing Media Library image attachment so the picture
# helper in inc/performance.php has next-gen sources to negotiate against.
#
# Usage:
#   bash scripts/wp-cli-nextgen-backfill.sh --dry-run         # safe preview
#   bash scripts/wp-cli-nextgen-backfill.sh --limit=50        # batch test
#   bash scripts/wp-cli-nextgen-backfill.sh                   # full backfill
#
# Idempotent — skips any file where the AVIF/WebP sibling already exists.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.wordpress}"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

if [[ ! -f "$ENV_FILE" ]]; then
    log_error "Credential file not found: $ENV_FILE"
    exit 1
fi
# shellcheck source=/dev/null
source "$ENV_FILE"

# Build SSH command — key preferred, sshpass fallback.
SSH_STRICT="${SSH_STRICT_HOST:-accept-new}"
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
SSH_PORT="${SSH_PORT:-22}"

SSH_CMD=( ssh -o "StrictHostKeyChecking=$SSH_STRICT" -o ConnectTimeout=15 -p "$SSH_PORT" )
if [[ -f "$SSH_KEY_PATH" ]]; then
    SSH_CMD+=( -i "$SSH_KEY_PATH" )
elif [[ -n "${SSH_PASS:-}" ]] && command -v sshpass &>/dev/null; then
    export SSHPASS="$SSH_PASS"
    SSH_CMD=( sshpass -e "${SSH_CMD[@]}" )
else
    log_error "No SSH credentials available (no key at $SSH_KEY_PATH and no SSH_PASS+sshpass)"
    exit 1
fi

# Forward all script args to wp-cli verbatim.
WP_ARGS="$*"

log_info "Running on ${SSH_USER}@${SSH_HOST}: wp skyyrose nextgen-backfill ${WP_ARGS}"
"${SSH_CMD[@]}" "${SSH_USER}@${SSH_HOST}" "wp skyyrose nextgen-backfill ${WP_ARGS}"
exit_code=$?

unset SSHPASS

if [[ $exit_code -eq 0 ]]; then
    log_success "Backfill completed (exit 0)"
else
    log_error "Backfill exited with code $exit_code"
fi
exit $exit_code
