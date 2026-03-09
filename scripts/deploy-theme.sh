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
    echo "  --dry-run    Preview what would happen without touching production"
    echo "  --help       Show this help message"
    echo ""
    echo "Environment:"
    echo "  ENV_FILE             Path to .env.wordpress (default: \$PROJECT_ROOT/.env.wordpress)"
    echo "  THEME_DIR_OVERRIDE   Override theme source directory"
    echo ""
    echo "The script will:"
    echo "  1. Run preflight checks (credentials, tools, PHP syntax)"
    echo "  2. Enable maintenance mode via WP-CLI over SSH"
    echo "  3. Transfer theme files via rsync (with lftp SFTP fallback)"
    echo "  4. Disable maintenance mode and flush all caches"
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
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new \
        -p "${SSH_PORT:-22}" "${SSH_USER}@${SSH_HOST}" "wp $cmd" 2>/dev/null
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

    # Verify sshpass
    if ! command -v sshpass &>/dev/null; then
        log_error "sshpass not installed. Run: brew install hudochenkov/sshpass/sshpass"
        exit 1
    fi
    log_success "sshpass available"

    # Verify theme directory
    if [[ ! -d "$THEME_DIR" ]]; then
        log_error "Theme directory not found: $THEME_DIR"
        exit 1
    fi
    log_success "Theme directory exists: $THEME_DIR"

    # PHP syntax check
    local php_errors=0
    while IFS= read -r -d '' phpfile; do
        if ! php -l "$phpfile" &>/dev/null; then
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
        if ! sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=accept-new \
            -p "${SSH_PORT:-22}" "${SSH_USER}@${SSH_HOST}" "echo ok" 2>/dev/null; then
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
        log_info "[DRY RUN] rsync -avz --delete --timeout=300 ${RSYNC_EXCLUDES[*]} $THEME_DIR/ -> ${SSH_USER}@${SSH_HOST}:${WP_THEME_PATH}/"
        return 0
    fi

    rsync -avz --delete --timeout=300 \
        "${RSYNC_EXCLUDES[@]}" \
        -e "sshpass -p '$SSH_PASS' ssh -o StrictHostKeyChecking=accept-new -p ${SSH_PORT:-22}" \
        "$THEME_DIR/" \
        "${SSH_USER}@${SSH_HOST}:${WP_THEME_PATH}/"
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

    # shellcheck disable=SC2086
    lftp -c "
set sftp:auto-confirm yes
set net:max-retries 3
set net:reconnect-interval-base 5
open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:${SFTP_PORT:-22}
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

    # 2. Enable maintenance mode (DEPLOY-02)
    log_info "Activating maintenance mode..."
    wp_remote "maintenance-mode activate"
    MAINTENANCE_ACTIVE=true
    log_success "Maintenance mode active"

    # 3. Transfer files (DEPLOY-01)
    transfer_files

    # 4. Disable maintenance mode (DEPLOY-03)
    log_info "Deactivating maintenance mode..."
    wp_remote "maintenance-mode deactivate"
    MAINTENANCE_ACTIVE=false
    log_success "Maintenance mode deactivated"

    # 5. Flush caches (DEPLOY-03)
    flush_caches

    log_success "=== Deploy complete ==="
}

main "$@"
