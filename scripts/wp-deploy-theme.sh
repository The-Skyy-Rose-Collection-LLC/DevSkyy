#!/bin/bash
# =============================================================================
# Deploy SkyyRose Flagship Theme to WordPress.com Atomic via SFTP
# =============================================================================
#
# Syncs the entire theme directory to the live WordPress.com Atomic site.
# Uses lftp for reliable SFTP mirroring.
#
# Usage:
#   ./scripts/wp-deploy-theme.sh              # Full theme sync
#   ./scripts/wp-deploy-theme.sh --dry-run    # Preview without deploying
#   ./scripts/wp-deploy-theme.sh --file path  # Deploy single file
#
# Requires:
#   - lftp (brew install lftp)
#   - .env.wordpress with SFTP credentials
#
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
THEME_DIR="$PROJECT_ROOT/wordpress-theme/skyyrose-flagship"
ENV_FILE="$PROJECT_ROOT/.env.wordpress"

DRY_RUN=false
SINGLE_FILE=""

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_deploy()  { echo -e "${CYAN}[DEPLOY]${NC} $1"; }

# Load env
if [[ ! -f "$ENV_FILE" ]]; then
    log_error ".env.wordpress not found at $ENV_FILE"
    log_info "Create it with: SFTP_HOST, SFTP_PORT, SFTP_USER, SFTP_PASS, WP_THEME_PATH"
    exit 1
fi

source "$ENV_FILE"

# Validate required vars
for var in SFTP_HOST SFTP_PORT SFTP_USER SFTP_PASS WP_THEME_PATH; do
    if [[ -z "${!var:-}" || "${!var}" == "FILL_THIS_IN" ]]; then
        log_error "$var is not set or still has placeholder value in .env.wordpress"
        exit 1
    fi
done

# Check lftp
if ! command -v lftp &>/dev/null; then
    log_error "lftp is not installed. Install with: brew install lftp"
    exit 1
fi

# Check theme dir
if [[ ! -d "$THEME_DIR" ]]; then
    log_error "Theme directory not found: $THEME_DIR"
    exit 1
fi

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --file)
            SINGLE_FILE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Preview files without deploying"
            echo "  --file PATH     Deploy a single file (relative to theme dir)"
            echo "  --help          Show this help"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# Deploy
# =============================================================================

echo ""
echo "=========================================="
echo "  SKYYROSE THEME DEPLOYMENT"
echo "=========================================="
echo ""
log_info "Host: $SFTP_HOST:$SFTP_PORT"
log_info "User: $SFTP_USER"
log_info "Remote: $WP_THEME_PATH"
log_info "Local:  $THEME_DIR"
echo ""

if [[ -n "$SINGLE_FILE" ]]; then
    # Single file deploy
    local_path="$THEME_DIR/$SINGLE_FILE"
    if [[ ! -f "$local_path" ]]; then
        log_error "File not found: $local_path"
        exit 1
    fi

    remote_dir=$(dirname "$WP_THEME_PATH/$SINGLE_FILE")

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy: $SINGLE_FILE"
    else
        log_deploy "Uploading $SINGLE_FILE..."
        lftp -c "
set sftp:auto-confirm yes
set net:max-retries 3
set net:reconnect-interval-base 5
open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:$SFTP_PORT
mkdir -p $remote_dir
put $local_path -o $WP_THEME_PATH/$SINGLE_FILE
bye
"
        log_success "Deployed: $SINGLE_FILE"
    fi
else
    # Full theme mirror
    EXCLUDE_ARGS=""
    # Exclude files that shouldn't be deployed
    EXCLUDE_ARGS+=" --exclude .DS_Store"
    EXCLUDE_ARGS+=" --exclude .git/"
    EXCLUDE_ARGS+=" --exclude .gitignore"
    EXCLUDE_ARGS+=" --exclude node_modules/"
    EXCLUDE_ARGS+=" --exclude package.json"
    EXCLUDE_ARGS+=" --exclude package-lock.json"
    EXCLUDE_ARGS+=" --exclude *.map"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Previewing changes..."
        lftp -c "
set sftp:auto-confirm yes
set net:max-retries 3
open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:$SFTP_PORT
mirror --reverse --dry-run --verbose $EXCLUDE_ARGS \
  $THEME_DIR/ \
  $WP_THEME_PATH/
bye
"
    else
        log_deploy "Syncing full theme..."
        lftp -c "
set sftp:auto-confirm yes
set net:max-retries 3
set net:reconnect-interval-base 5
open -u $SFTP_USER,$SFTP_PASS sftp://$SFTP_HOST:$SFTP_PORT
mirror --reverse --verbose --only-newer $EXCLUDE_ARGS \
  $THEME_DIR/ \
  $WP_THEME_PATH/
bye
"
        log_success "Full theme sync complete"
    fi
fi

echo ""
echo "=========================================="
if [[ "$DRY_RUN" == "true" ]]; then
    log_info "DRY RUN complete — no files were changed"
else
    log_success "DEPLOYMENT COMPLETE"
    log_info "Site: https://skyyrose.co"
    log_info "Clear cache: wp-admin > Hosting > Clear Cache"
fi
echo "=========================================="
echo ""
