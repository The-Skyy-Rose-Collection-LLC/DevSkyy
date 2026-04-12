#!/usr/bin/env bash
# scripts/deploy-theme.sh -- Production deploy script for SkyyRose WordPress theme
# Transfers built theme files to skyyrose.co with maintenance mode safety and cache flushing.
#
# Usage:
#   bash scripts/deploy-theme.sh              # Live deploy to production
#   bash scripts/deploy-theme.sh --dry-run    # Preview what would happen (no server contact)
#   bash scripts/deploy-theme.sh --help       # Show this help message
#
# Requirements:
#   - .env.wordpress with SSH/SFTP credentials (or set ENV_FILE to override path)
#   - sshpass installed (brew install hudochenkov/sshpass/sshpass)
#   - Theme directory at wordpress-theme/skyyrose-flagship/
#
# Safety:
#   - Maintenance mode is activated before file transfer and deactivated after
#   - trap cleanup EXIT INT TERM guarantees maintenance mode is disabled on failure
#   - WordPress auto-deactivates maintenance mode after 10 minutes as a fallback

set -euo pipefail

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="${THEME_DIR_OVERRIDE:-$PROJECT_ROOT/wordpress-theme/skyyrose-flagship}"
ENV_FILE="${ENV_FILE:-$PROJECT_ROOT/.env.wordpress}"

# ---------------------------------------------------------------------------
# State tracking
# ---------------------------------------------------------------------------
DRY_RUN=false
WITH_MAINTENANCE=false
MAINTENANCE_ACTIVE=false

# ---------------------------------------------------------------------------
# Color logging
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
    echo "Usage: deploy-theme.sh [OPTIONS]"
    echo ""
    echo "Deploy the SkyyRose WordPress theme to production."
    echo ""
    echo "Options:"
    echo "  --dry-run            Preview what would happen without touching production"
    echo "  --with-maintenance   Enable wp maintenance-mode during deploy (legacy)."
    echo "                       Default is hot-swap, which avoids the Jetpack Uptime"
    echo "                       false-positive 503 window. Use --with-maintenance for"
    echo "                       deploys that include DB migrations or plugin changes."
    echo "  --help               Show this help message"
    echo ""
    echo "Environment:"
    echo "  ENV_FILE             Path to .env.wordpress (default: \$PROJECT_ROOT/.env.wordpress)"
    echo "  THEME_DIR_OVERRIDE   Override theme source directory"
    echo "  PUBLIC_URL           Verified URL for post-deploy check (default: https://skyyrose.co/)"
    echo ""
    echo "The script will:"
    echo "  1. Run preflight checks (credentials, tools, PHP syntax)"
    echo "  2. Transfer theme files via tar+scp with atomic hot-swap on remote"
    echo "     (or, with --with-maintenance, enable maintenance mode first)"
    echo "  3. Flush object/transient/rewrite caches"
    echo "  4. Verify the live site returns HTTP 200 with no PHP error markers"
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --with-maintenance)
                WITH_MAINTENANCE=true
                shift
                ;;
            --help|-h)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# ---------------------------------------------------------------------------
# Source credentials
# ---------------------------------------------------------------------------
load_credentials() {
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Credential file not found: $ENV_FILE"
        log_error "Create .env.wordpress with SSH_HOST, SSH_USER, SSH_PASS, WP_THEME_PATH, SFTP_HOST, SFTP_USER, SFTP_PASS"
        exit 1
    fi
    # shellcheck source=/dev/null
    source "$ENV_FILE"
}

# ---------------------------------------------------------------------------
# Cleanup handler -- ALWAYS disables maintenance mode on exit (DEPLOY-07)
# ---------------------------------------------------------------------------
cleanup() {
    if [[ "$MAINTENANCE_ACTIVE" == "true" ]]; then
        log_warn "Cleanup: disabling maintenance mode after unexpected exit..."
        wp_remote "maintenance-mode deactivate" || log_error "CRITICAL: Failed to deactivate maintenance mode -- check site manually"
        MAINTENANCE_ACTIVE=false
    fi
}

trap cleanup EXIT INT TERM

# ---------------------------------------------------------------------------
# WP-CLI over SSH (proven pattern from wp-deploy-theme.sh)
# ---------------------------------------------------------------------------
wp_remote() {
    local cmd="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] wp $cmd"
        return 0
    fi
    local ssh_opts=(-o StrictHostKeyChecking=yes -p "${SSH_PORT:-22}")
    if [[ -f "${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}" ]]; then
        ssh_opts+=(-i "${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}")
    fi
    ssh "${ssh_opts[@]}" "${SSH_USER}@${SSH_HOST}" "wp $cmd" 2>/dev/null
}

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
preflight() {
    log_info "Running preflight checks..."

    # Verify required env vars
    local required_vars=(SSH_HOST SSH_USER SSH_PASS WP_THEME_PATH SFTP_HOST SFTP_USER SFTP_PASS)
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Missing required credential: $var"
            exit 1
        fi
    done
    log_success "All credentials present"

    # Verify SSH auth method (key preferred, sshpass fallback)
    if [[ -f "${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}" ]]; then
        log_success "SSH key found: ${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
    elif command -v sshpass &>/dev/null; then
        log_success "sshpass available (password auth)"
    else
        log_error "No SSH key at ~/.ssh/skyyrose-deploy and sshpass not installed"
        exit 1
    fi

    # Verify theme directory
    if [[ ! -d "$THEME_DIR" ]]; then
        log_error "Theme directory not found: $THEME_DIR"
        exit 1
    fi
    log_success "Theme directory exists: $THEME_DIR"

    # PHP syntax check
    local php_errors=0
    while IFS= read -r -d '' phpfile; do
        if ! /opt/homebrew/bin/php -l "$phpfile" &>/dev/null; then
            log_error "PHP syntax error: $phpfile"
            php_errors=$((php_errors + 1))
        fi
    done < <(find "$THEME_DIR" -name '*.php' -print0 2>/dev/null)

    if [[ "$php_errors" -gt 0 ]]; then
        log_error "$php_errors PHP file(s) have syntax errors -- fix before deploying"
        exit 1
    fi
    log_success "PHP syntax check passed"

    # Test SSH connectivity (skip in dry-run)
    if [[ "$DRY_RUN" == "false" ]]; then
        local ssh_test_opts=(-o StrictHostKeyChecking=yes -o ConnectTimeout=15 -p "${SSH_PORT:-22}")
        if [[ -f "${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}" ]]; then
            ssh_test_opts+=(-i "${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}")
        fi
        if ! ssh "${ssh_test_opts[@]}" "${SSH_USER}@${SSH_HOST}" "echo ok" 2>/dev/null; then
            log_error "SSH connectivity test failed -- check credentials and network"
            exit 1
        fi
        log_success "SSH connectivity verified"
    else
        log_info "[DRY RUN] Skipping SSH connectivity test"
    fi

    log_success "All preflight checks passed"
}

# ---------------------------------------------------------------------------
# Rsync exclude list (comprehensive -- prevents dev files from reaching production)
# ---------------------------------------------------------------------------
RSYNC_EXCLUDES=(
    --exclude='.git'
    --exclude='.git/'
    --exclude='node_modules/'
    --exclude='vendor/'
    --exclude='tests/'
    --exclude='test-results/'
    --exclude='.env*'
    --exclude='*.map'
    --exclude='*.log'
    --exclude='.DS_Store'
    --exclude='package.json'
    --exclude='package-lock.json'
    --exclude='composer.json'
    --exclude='composer.lock'
    --exclude='webpack.config.js'
    --exclude='deploy.sh'
    --exclude='CLAUDE.md'
    --exclude='IMMERSIVE-WORLDS-PLAN.md'
    --exclude='scripts/'
    --exclude='.deploy-archives/'
    --exclude='.gitignore'
    --exclude='generate_models.js'
    --exclude='.phpcs.xml'
    --exclude='.eslintrc*'
    --exclude='.prettierrc*'
    --exclude='.editorconfig'
    --exclude='phpunit.xml'
    --exclude='playwright-report/'
    --exclude='screenshots/'
)

# ---------------------------------------------------------------------------
# File transfer: rsync with lftp SFTP fallback (DEPLOY-01)
# ---------------------------------------------------------------------------
transfer_files() {
    log_info "Starting file transfer from $THEME_DIR to $WP_THEME_PATH..."

    if try_rsync; then
        log_success "File transfer completed via rsync"
        return 0
    fi

    log_warn "rsync failed or unavailable -- falling back to lftp SFTP mirror"

    if try_lftp; then
        log_success "File transfer completed via lftp SFTP"
        return 0
    fi

    log_error "Both rsync and lftp transfer failed"
    return 1
}

try_rsync() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] sftp upload $THEME_DIR/ -> ${SSH_USER}@${SSH_HOST}:${WP_THEME_PATH}/"
        return 0
    fi

    local key_path="${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
    local ssh_opts="-o StrictHostKeyChecking=yes -p ${SSH_PORT:-22}"
    if [[ -f "$key_path" ]]; then
        ssh_opts="$ssh_opts -i $key_path"
    fi

    # WordPress.com doesn't support rsync protocol — use sftp batch upload
    log_info "Creating upload archive..."
    local tmpzip="/tmp/skyyrose-flagship-deploy.tar.gz"
    tar -czf "$tmpzip" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='vendor' \
        --exclude='tests' \
        --exclude='test-results' \
        --exclude='_archive' \
        --exclude='.env*' \
        --exclude='*.map' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        --exclude='deploy.sh' \
        --exclude='CLAUDE.md' \
        --exclude='IMMERSIVE-WORLDS-PLAN.md' \
        --exclude='.deploy-archives' \
        --exclude='.gitignore' \
        --exclude='.phpcs.xml' \
        --exclude='.eslintrc*' \
        --exclude='.prettierrc*' \
        --exclude='.editorconfig' \
        --exclude='phpunit.xml' \
        --exclude='playwright-report' \
        --exclude='screenshots' \
        --exclude='.serena' \
        -C "$(dirname "$THEME_DIR")" "$(basename "$THEME_DIR")"

    local archive_size
    archive_size="$(du -h "$tmpzip" | cut -f1)"
    log_info "Archive: $tmpzip ($archive_size)"

    # Upload via scp then extract remotely
    local key_flag=""
    if [[ -f "$key_path" ]]; then
        key_flag="-i $key_path"
    fi

    log_info "Uploading via scp..."
    scp -P "${SSH_PORT:-22}" $key_flag -o StrictHostKeyChecking=yes "$tmpzip" "${SSH_USER}@${SSH_HOST}:/tmp/skyyrose-deploy.tar.gz"

    log_info "Extracting on remote (atomic hot-swap)..."
    # Hot-swap deploy (DEPLOY-08): rename current theme aside, then rename new
    # theme into place. The live path is unreachable only between two consecutive
    # rename(2) syscalls — microseconds, not the ~60 seconds the old `rm -rf && mv`
    # pattern produced with maintenance mode. Jetpack Uptime stops firing
    # false-positive "site is down" alerts during routine code-only deploys.
    local swap_id
    swap_id="$(date +%s)-$$"
    ssh -p "${SSH_PORT:-22}" $key_flag -o StrictHostKeyChecking=yes "${SSH_USER}@${SSH_HOST}" "cd /tmp && tar -xzf skyyrose-deploy.tar.gz && (if [ -d '${WP_THEME_PATH}' ]; then mv '${WP_THEME_PATH}' '${WP_THEME_PATH}.old.${swap_id}'; fi) && mv skyyrose-flagship '${WP_THEME_PATH}' && (rm -rf '${WP_THEME_PATH}.old.${swap_id}' 2>/dev/null; rm -f skyyrose-deploy.tar.gz; true)"

    rm -f "$tmpzip"
    log_success "Theme uploaded and extracted"
}

try_lftp() {
    if ! command -v lftp &>/dev/null; then
        log_warn "lftp not installed -- cannot use SFTP fallback"
        return 1
    fi

    # Convert rsync excludes to lftp exclude format
    local lftp_excludes=""
    for exc in "${RSYNC_EXCLUDES[@]}"; do
        local pattern="${exc#--exclude=}"
        pattern="${pattern//\'/}"
        lftp_excludes="$lftp_excludes --exclude $pattern"
    done

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] lftp SFTP mirror $THEME_DIR/ -> $WP_THEME_PATH/"
        return 0
    fi

    local key_path="${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
    # shellcheck disable=SC2086
    lftp -c "
set sftp:auto-confirm yes
set sftp:connect-program 'ssh -i $key_path -o StrictHostKeyChecking=yes'
set net:max-retries 3
set net:reconnect-interval-base 5
open -u $SFTP_USER, sftp://$SFTP_HOST:${SFTP_PORT:-22}
mirror --reverse --verbose --only-newer --delete $lftp_excludes \
  $THEME_DIR/ \
  $WP_THEME_PATH/
bye
"
}

# ---------------------------------------------------------------------------
# Cache flush (DEPLOY-03)
# ---------------------------------------------------------------------------
flush_caches() {
    log_info "Flushing all caches..."
    wp_remote "cache flush"
    wp_remote "transient delete --all"
    wp_remote "rewrite flush"
    log_success "All caches flushed"
}

# ---------------------------------------------------------------------------
# Post-deploy verification (DEPLOY-08)
#
# Boris Cherny's #1 tip for Claude Code: "Give Claude a way to verify its
# work. If Claude has that feedback loop, it will 2-3x the quality of the
# final result."
#
# We curl the live homepage with a cache-buster query string (bypasses
# Jetpack Boost page cache) and assert: HTTP 200, response size >= 50 KB
# (an error page or half-rendered fatal is typically much smaller), and
# no PHP error markers leaking through to the HTML body. Exits non-zero
# on any failure so the caller knows the deploy didn't really land.
#
# Override the verified URL via the PUBLIC_URL env var.
# ---------------------------------------------------------------------------
verify_live() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Skipping live verification"
        return 0
    fi

    local public_url="${PUBLIC_URL:-https://skyyrose.co/}"
    local bust_url="${public_url}?deploy_verify=$(date +%s)"
    local tmpfile
    tmpfile="$(mktemp)"
    # shellcheck disable=SC2064
    trap "rm -f '$tmpfile'" RETURN

    log_info "Running post-deploy verification: $bust_url"

    local http_code
    http_code=$(curl -sS -o "$tmpfile" -w "%{http_code}" \
        -A "DevSkyy-deploy-verify/1.0" \
        --max-time 30 \
        "$bust_url" 2>/dev/null || echo "000")

    if [[ "$http_code" != "200" ]]; then
        log_error "Verification FAILED: homepage returned HTTP $http_code (expected 200)"
        return 1
    fi

    local size
    size=$(wc -c < "$tmpfile" | tr -d ' ')
    if [[ "${size:-0}" -lt 50000 ]]; then
        log_error "Verification FAILED: homepage response too small (${size:-0} bytes, expected >= 50 KB)"
        return 1
    fi

    if grep -qE "Fatal error|Parse error|Call to undefined|There has been a critical error" "$tmpfile"; then
        log_error "Verification FAILED: PHP error markers found in homepage response:"
        grep -oE "(Fatal error|Parse error|Call to undefined|There has been a critical error)[^<]{0,100}" "$tmpfile" | head -3 >&2
        return 1
    fi

    log_success "Post-deploy verification passed (HTTP $http_code, $size bytes)"
    return 0
}

# ---------------------------------------------------------------------------
# Main deploy pipeline
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "=== DRY RUN MODE -- no changes will be made ==="
    fi

    log_info "=== SkyyRose Theme Deploy ==="
    log_info "Theme: $THEME_DIR"
    log_info "Target: ${ENV_FILE##*/}"

    # Load credentials (validates file exists)
    load_credentials

    # 1. Preflight checks
    preflight

    # 2. Maintenance mode — OPT-IN via --with-maintenance (DEPLOY-02)
    # Hot-swap (the default transfer path) makes maintenance mode unnecessary
    # for code-only deploys and eliminates the Jetpack Uptime false-positive
    # alert window. Pass --with-maintenance when deploying DB migrations or
    # plugin changes that require the site to be locked.
    if [[ "$WITH_MAINTENANCE" == "true" ]]; then
        log_info "Activating maintenance mode (--with-maintenance)..."
        wp_remote "maintenance-mode activate"
        MAINTENANCE_ACTIVE=true
        log_success "Maintenance mode active"
    else
        log_info "Skipping maintenance mode (hot-swap default) — pass --with-maintenance to opt in"
    fi

    # 3. Transfer files (DEPLOY-01)
    transfer_files

    # 4. Disable maintenance mode if it was enabled (DEPLOY-03)
    if [[ "$MAINTENANCE_ACTIVE" == "true" ]]; then
        log_info "Deactivating maintenance mode..."
        wp_remote "maintenance-mode deactivate"
        MAINTENANCE_ACTIVE=false
        log_success "Maintenance mode deactivated"
    fi

    # 5. Flush caches (DEPLOY-03)
    flush_caches

    # 6. Post-deploy verification gate (DEPLOY-08 — Boris Cherny tip #14)
    if ! verify_live; then
        log_error "=== Deploy FAILED post-verification ==="
        log_error "Site may be in a broken state — investigate before re-deploying"
        exit 1
    fi

    log_success "=== Deploy complete (verified live) ==="
}

main "$@"
