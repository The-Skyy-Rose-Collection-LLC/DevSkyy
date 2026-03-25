#!/usr/bin/env bash
#
# SkyyRose Flagship Theme -- Deployment Script
#
# Usage:
#   ./deploy.sh [target]
#
# Targets:
#   local      -- Copy theme to local WordPress installation
#   staging    -- Deploy to staging server via rsync
#   production -- Deploy to skyyrose.co (requires confirmation)
#
# Prerequisites:
#   - WP-CLI installed and configured
#   - SSH access to staging/production servers
#   - rsync available
#
# Environment Variables:
#   WP_PATH         -- Local WordPress installation path (default: /var/www/html)
#   STAGING_HOST    -- Staging server SSH host (e.g., staging.skyyrose.co)
#   STAGING_PATH    -- Remote theme directory on staging (default: /var/www/html/wp-content/themes)
#   PRODUCTION_HOST -- Production server SSH host (e.g., skyyrose.co)
#   PRODUCTION_PATH -- Remote theme directory on production (default: /var/www/html/wp-content/themes)
#
# @package SkyyRose_Flagship
# @since   3.12.0
#

set -euo pipefail

# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

readonly THEME_SLUG="skyyrose-flagship"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
readonly ARCHIVE_DIR="${SCRIPT_DIR}/.deploy-archives"
readonly ARCHIVE_NAME="${THEME_SLUG}-${TIMESTAMP}.zip"

# Colours (disabled if not a terminal).
if [[ -t 1 ]]; then
    readonly RED='\033[0;31m'
    readonly GREEN='\033[0;32m'
    readonly YELLOW='\033[1;33m'
    readonly CYAN='\033[0;36m'
    readonly ROSE='\033[38;5;174m'
    readonly BOLD='\033[1m'
    readonly RESET='\033[0m'
else
    readonly RED='' GREEN='' YELLOW='' CYAN='' ROSE='' BOLD='' RESET=''
fi

# --------------------------------------------------------------------------
# Defaults for Environment Variables
# --------------------------------------------------------------------------

WP_PATH="${WP_PATH:-/var/www/html}"
STAGING_HOST="${STAGING_HOST:-}"
STAGING_PATH="${STAGING_PATH:-/var/www/html/wp-content/themes}"
PRODUCTION_HOST="${PRODUCTION_HOST:-}"
PRODUCTION_PATH="${PRODUCTION_PATH:-/var/www/html/wp-content/themes}"

# --------------------------------------------------------------------------
# Utility Functions
# --------------------------------------------------------------------------

info()  { printf "${CYAN}[INFO]${RESET}  %s\n" "$*"; }
ok()    { printf "${GREEN}[  OK]${RESET}  %s\n" "$*"; }
warn()  { printf "${YELLOW}[WARN]${RESET}  %s\n" "$*"; }
fail()  { printf "${RED}[FAIL]${RESET}  %s\n" "$*"; }
header() {
    printf "\n${ROSE}${BOLD}--------------------------------------------------------------${RESET}\n"
    printf "${ROSE}${BOLD}  %s${RESET}\n" "$*"
    printf "${ROSE}${BOLD}--------------------------------------------------------------${RESET}\n\n"
}

die() {
    fail "$@"
    exit 1
}

# --------------------------------------------------------------------------
# Pre-Deployment Checks
# --------------------------------------------------------------------------

run_prechecks() {
    header "Pre-Deployment Checks"

    local errors=0

    # 1. Verify theme directory exists.
    if [[ ! -d "${SCRIPT_DIR}" ]]; then
        fail "Theme directory does not exist: ${SCRIPT_DIR}"
        (( errors++ ))
    else
        ok "Theme directory exists"
    fi

    # 2. Verify style.css has correct theme header.
    local style_css="${SCRIPT_DIR}/style.css"
    if [[ ! -f "${style_css}" ]]; then
        fail "style.css not found"
        (( errors++ ))
    else
        if grep -q "Theme Name: SkyyRose Flagship" "${style_css}"; then
            ok "style.css has correct theme header"
        else
            fail "style.css missing 'Theme Name: SkyyRose Flagship' header"
            (( errors++ ))
        fi

        # Extract and display version.
        local theme_version
        theme_version="$(grep -oP 'Version:\s*\K[0-9.]+' "${style_css}" 2>/dev/null || echo "unknown")"
        info "Theme version: ${theme_version}"
    fi

    # 3. Check for PHP syntax errors.
    info "Checking PHP syntax..."
    local php_errors=0
    while IFS= read -r -d '' php_file; do
        if ! php -l "${php_file}" > /dev/null 2>&1; then
            fail "Syntax error in: ${php_file}"
            php -l "${php_file}" 2>&1 | tail -1
            (( php_errors++ ))
        fi
    done < <(find "${SCRIPT_DIR}" -name '*.php' -not -path '*/vendor/*' -not -path '*/node_modules/*' -print0)

    if [[ "${php_errors}" -eq 0 ]]; then
        ok "All PHP files pass syntax check"
    else
        fail "${php_errors} PHP file(s) have syntax errors"
        (( errors += php_errors ))
    fi

    # 4. Check for debug/console.log statements in JS.
    info "Scanning JavaScript for debug statements..."
    local js_warnings=0
    while IFS= read -r -d '' js_file; do
        if grep -qE '(console\.(log|debug|warn|error)|debugger)' "${js_file}" 2>/dev/null; then
            warn "Debug statement found: ${js_file}"
            (( js_warnings++ ))
        fi
    done < <(find "${SCRIPT_DIR}/assets/js" -name '*.js' -not -name '*.min.js' -not -path '*/node_modules/*' -print0 2>/dev/null)

    if [[ "${js_warnings}" -eq 0 ]]; then
        ok "No debug statements found in JS"
    else
        warn "${js_warnings} JS file(s) contain debug statements"
    fi

    # 5. Verify no .env or credentials files are included.
    info "Scanning for sensitive files..."
    local sensitive_patterns=('.env' '.env.local' '.env.production' 'credentials.json' 'auth.json' '*.pem' '*.key')
    local sensitive_found=0
    for pattern in "${sensitive_patterns[@]}"; do
        while IFS= read -r -d '' sensitive_file; do
            fail "Sensitive file found: ${sensitive_file}"
            (( sensitive_found++ ))
        done < <(find "${SCRIPT_DIR}" -name "${pattern}" -not -path '*/node_modules/*' -not -path '*/.deploy-archives/*' -print0 2>/dev/null)
    done

    if [[ "${sensitive_found}" -eq 0 ]]; then
        ok "No sensitive files found"
    else
        fail "${sensitive_found} sensitive file(s) found -- remove before deploying"
        (( errors += sensitive_found ))
    fi

    # 6. Check functions.php exists.
    if [[ ! -f "${SCRIPT_DIR}/functions.php" ]]; then
        fail "functions.php not found"
        (( errors++ ))
    else
        ok "functions.php exists"
    fi

    echo ""
    if [[ "${errors}" -gt 0 ]]; then
        die "Pre-deployment checks failed with ${errors} error(s). Fix issues and retry."
    fi

    ok "All pre-deployment checks passed"
}

# --------------------------------------------------------------------------
# Build Assets
# --------------------------------------------------------------------------

build_assets() {
    header "Building Assets"

    if [[ -f "${SCRIPT_DIR}/package.json" ]]; then
        if command -v npm > /dev/null 2>&1; then
            info "package.json found -- running npm install and build..."
            (
                cd "${SCRIPT_DIR}"
                npm install --omit=dev --silent 2>/dev/null || warn "npm install had warnings"
                if npm run build --if-present > /dev/null 2>&1; then
                    ok "npm build completed"
                else
                    warn "npm build script not found or failed -- continuing without build"
                fi
            )
        else
            warn "npm not found -- skipping asset build"
        fi
    elif [[ -f "${SCRIPT_DIR}/webpack.config.js" ]]; then
        if command -v npx > /dev/null 2>&1; then
            info "webpack.config.js found -- running webpack..."
            (
                cd "${SCRIPT_DIR}"
                npx webpack --mode production > /dev/null 2>&1 && ok "Webpack build completed" || warn "Webpack build failed -- continuing"
            )
        else
            warn "npx not found -- skipping webpack build"
        fi
    else
        info "No build system detected -- skipping asset build"
    fi
}

# --------------------------------------------------------------------------
# Create Archive
# --------------------------------------------------------------------------

create_archive() {
    header "Creating Archive"

    mkdir -p "${ARCHIVE_DIR}"

    info "Creating ${ARCHIVE_NAME}..."

    # Build the exclude list.
    local -a excludes=(
        '.git'
        '.git/*'
        'node_modules'
        'node_modules/*'
        '.deploy-archives'
        '.deploy-archives/*'
        'tests'
        'tests/*'
        '.env*'
        '*.log'
        '.DS_Store'
        'Thumbs.db'
        'deploy.sh'
        'composer.lock'
        'package-lock.json'
        'phpunit.xml'
        '.phpcs.xml'
        '.eslintrc*'
        '.prettierrc*'
        '.editorconfig'
        'CLAUDE.md'
    )

    local exclude_args=()
    for pattern in "${excludes[@]}"; do
        exclude_args+=(-x "${THEME_SLUG}/${pattern}")
    done

    # Create the zip from the parent directory so the archive root is the theme slug.
    (
        cd "${SCRIPT_DIR}/.."
        zip -r "${ARCHIVE_DIR}/${ARCHIVE_NAME}" "${THEME_SLUG}" \
            "${exclude_args[@]}" \
            -q
    )

    local archive_path="${ARCHIVE_DIR}/${ARCHIVE_NAME}"
    local archive_size
    archive_size="$(du -h "${archive_path}" | cut -f1)"

    ok "Archive created: ${archive_path} (${archive_size})"
    echo "${archive_path}"
}

# --------------------------------------------------------------------------
# Deploy: Local
# --------------------------------------------------------------------------

deploy_local() {
    header "Deploying to Local WordPress"

    local target_dir="${WP_PATH}/wp-content/themes/${THEME_SLUG}"

    if [[ ! -d "${WP_PATH}" ]]; then
        die "WordPress installation not found at: ${WP_PATH}\n  Set WP_PATH environment variable to the correct path."
    fi

    if [[ ! -d "${WP_PATH}/wp-content/themes" ]]; then
        die "Themes directory not found: ${WP_PATH}/wp-content/themes"
    fi

    info "Target: ${target_dir}"

    # Sync theme files (exclude dev files).
    rsync -av --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.deploy-archives' \
        --exclude='tests' \
        --exclude='.env*' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        --exclude='deploy.sh' \
        --exclude='CLAUDE.md' \
        "${SCRIPT_DIR}/" "${target_dir}/"

    ok "Theme files synced to ${target_dir}"

    # Activate theme via WP-CLI if available.
    if command -v wp > /dev/null 2>&1; then
        info "Activating theme via WP-CLI..."
        if wp theme activate "${THEME_SLUG}" --path="${WP_PATH}" 2>/dev/null; then
            ok "Theme activated: ${THEME_SLUG}"
        else
            warn "WP-CLI theme activation failed -- activate manually in wp-admin"
        fi

        run_local_health_check "${WP_PATH}"
    else
        warn "WP-CLI not found -- activate theme manually in wp-admin"
    fi
}

# --------------------------------------------------------------------------
# Deploy: Staging
# --------------------------------------------------------------------------

deploy_staging() {
    header "Deploying to Staging"

    if [[ -z "${STAGING_HOST}" ]]; then
        die "STAGING_HOST not set. Export it before running:\n  export STAGING_HOST=staging.skyyrose.co"
    fi

    info "Host: ${STAGING_HOST}"
    info "Path: ${STAGING_PATH}/${THEME_SLUG}"

    # Test SSH connectivity.
    info "Testing SSH connection..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "${STAGING_HOST}" "echo ok" > /dev/null 2>&1; then
        die "Cannot connect to ${STAGING_HOST} via SSH. Check your SSH config."
    fi
    ok "SSH connection verified"

    # rsync theme to staging.
    info "Syncing theme files..."
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.deploy-archives' \
        --exclude='tests' \
        --exclude='.env*' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        --exclude='deploy.sh' \
        --exclude='CLAUDE.md' \
        "${SCRIPT_DIR}/" "${STAGING_HOST}:${STAGING_PATH}/${THEME_SLUG}/"

    ok "Theme files synced to staging"

    # Activate theme on staging.
    info "Activating theme on staging..."
    if ssh "${STAGING_HOST}" "cd ${STAGING_PATH}/.. && wp theme activate ${THEME_SLUG} --path=\$(dirname '${STAGING_PATH}')" 2>/dev/null; then
        ok "Theme activated on staging"
    else
        warn "Remote WP-CLI activation failed -- activate manually"
    fi

    # Remote health check.
    run_remote_health_check "${STAGING_HOST}" "${STAGING_PATH}"
}

# --------------------------------------------------------------------------
# Deploy: Production
# --------------------------------------------------------------------------

deploy_production() {
    header "Deploying to Production (skyyrose.co)"

    if [[ -z "${PRODUCTION_HOST}" ]]; then
        die "PRODUCTION_HOST not set. Export it before running:\n  export PRODUCTION_HOST=skyyrose.co"
    fi

    # Require explicit confirmation.
    printf "\n"
    printf "${RED}${BOLD}  WARNING: You are about to deploy to PRODUCTION.${RESET}\n"
    printf "${RED}  Host: ${PRODUCTION_HOST}${RESET}\n"
    printf "${RED}  Path: ${PRODUCTION_PATH}/${THEME_SLUG}${RESET}\n"
    printf "\n"
    printf "  Type ${BOLD}YES${RESET} to confirm: "
    read -r confirmation

    if [[ "${confirmation}" != "YES" ]]; then
        die "Production deployment aborted. You must type exactly 'YES' to confirm."
    fi

    info "Proceeding with production deployment..."

    # Test SSH connectivity.
    info "Testing SSH connection..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "${PRODUCTION_HOST}" "echo ok" > /dev/null 2>&1; then
        die "Cannot connect to ${PRODUCTION_HOST} via SSH. Check your SSH config."
    fi
    ok "SSH connection verified"

    # Create a backup on the remote server first.
    info "Creating backup of current theme on production..."
    local backup_name="${THEME_SLUG}-backup-${TIMESTAMP}.tar.gz"
    if ssh "${PRODUCTION_HOST}" "cd ${PRODUCTION_PATH} && tar -czf /tmp/${backup_name} ${THEME_SLUG}/ 2>/dev/null"; then
        ok "Backup created: /tmp/${backup_name}"
    else
        warn "Could not create backup (theme may not exist yet on remote)"
    fi

    # rsync theme to production.
    info "Syncing theme files..."
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.deploy-archives' \
        --exclude='tests' \
        --exclude='.env*' \
        --exclude='*.log' \
        --exclude='.DS_Store' \
        --exclude='deploy.sh' \
        --exclude='CLAUDE.md' \
        "${SCRIPT_DIR}/" "${PRODUCTION_HOST}:${PRODUCTION_PATH}/${THEME_SLUG}/"

    ok "Theme files synced to production"

    # Activate theme on production.
    info "Activating theme on production..."
    if ssh "${PRODUCTION_HOST}" "cd ${PRODUCTION_PATH}/.. && wp theme activate ${THEME_SLUG} --path=\$(dirname '${PRODUCTION_PATH}')" 2>/dev/null; then
        ok "Theme activated on production"
    else
        warn "Remote WP-CLI activation failed -- activate manually in wp-admin"
    fi

    # Remote health check.
    run_remote_health_check "${PRODUCTION_HOST}" "${PRODUCTION_PATH}"

    printf "\n${GREEN}${BOLD}  Production deployment complete.${RESET}\n"
    printf "  Backup: /tmp/${backup_name} (on ${PRODUCTION_HOST})\n\n"
}

# --------------------------------------------------------------------------
# Post-Deployment Health Checks
# --------------------------------------------------------------------------

run_local_health_check() {
    local wp_path="$1"

    header "Post-Deployment Health Check (Local)"

    if ! command -v wp > /dev/null 2>&1; then
        warn "WP-CLI not available -- skipping health checks"
        return 0
    fi

    # Verify theme is active.
    local active_theme
    active_theme="$(wp theme list --status=active --field=name --path="${wp_path}" 2>/dev/null || echo "")"
    if [[ "${active_theme}" == "${THEME_SLUG}" ]]; then
        ok "Active theme: ${THEME_SLUG}"
    else
        fail "Expected active theme '${THEME_SLUG}' but found '${active_theme}'"
    fi

    # Check for PHP fatal errors in theme.
    if wp eval "echo 'Theme loaded successfully';" --path="${wp_path}" 2>/dev/null; then
        ok "Theme loads without fatal errors"
    else
        fail "Theme may have fatal errors"
    fi

    # Check WooCommerce status.
    if wp plugin is-active woocommerce --path="${wp_path}" 2>/dev/null; then
        ok "WooCommerce is active"
    else
        warn "WooCommerce is not active"
    fi
}

run_remote_health_check() {
    local host="$1"
    local theme_path="$2"
    local wp_root
    wp_root="$(dirname "${theme_path}")"

    header "Post-Deployment Health Check (Remote: ${host})"

    # Verify theme is active on remote.
    local active_theme
    active_theme="$(ssh "${host}" "wp theme list --status=active --field=name --path='${wp_root}'" 2>/dev/null || echo "")"
    if [[ "${active_theme}" == "${THEME_SLUG}" ]]; then
        ok "Active theme: ${THEME_SLUG}"
    else
        if [[ -n "${active_theme}" ]]; then
            fail "Expected active theme '${THEME_SLUG}' but found '${active_theme}'"
        else
            warn "Could not verify active theme via WP-CLI"
        fi
    fi

    # Check theme files exist on remote.
    if ssh "${host}" "test -f '${theme_path}/${THEME_SLUG}/style.css'" 2>/dev/null; then
        ok "style.css exists on remote"
    else
        fail "style.css not found on remote"
    fi

    if ssh "${host}" "test -f '${theme_path}/${THEME_SLUG}/functions.php'" 2>/dev/null; then
        ok "functions.php exists on remote"
    else
        fail "functions.php not found on remote"
    fi
}

# --------------------------------------------------------------------------
# Usage
# --------------------------------------------------------------------------

usage() {
    cat <<USAGE

${ROSE}${BOLD}SkyyRose Flagship Theme -- Deployment Script${RESET}

${BOLD}Usage:${RESET}
  ./deploy.sh <target>

${BOLD}Targets:${RESET}
  local        Copy theme to local WordPress installation
  staging      Deploy to staging server via rsync
  production   Deploy to skyyrose.co (requires YES confirmation)
  check        Run pre-deployment checks only
  archive      Create a distributable zip archive only

${BOLD}Environment Variables:${RESET}
  WP_PATH          Local WP install path     (default: /var/www/html)
  STAGING_HOST     Staging SSH host           (required for staging)
  STAGING_PATH     Staging themes path        (default: /var/www/html/wp-content/themes)
  PRODUCTION_HOST  Production SSH host        (required for production)
  PRODUCTION_PATH  Production themes path     (default: /var/www/html/wp-content/themes)

${BOLD}Examples:${RESET}
  WP_PATH=/opt/wordpress ./deploy.sh local
  STAGING_HOST=staging.skyyrose.co ./deploy.sh staging
  PRODUCTION_HOST=skyyrose.co ./deploy.sh production
  ./deploy.sh check
  ./deploy.sh archive

USAGE
}

# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

main() {
    local target="${1:-}"

    if [[ -z "${target}" ]]; then
        usage
        exit 1
    fi

    printf "\n${ROSE}${BOLD}  SkyyRose Flagship -- Theme Deployment${RESET}\n"
    printf "  ${CYAN}Target: ${BOLD}${target}${RESET}\n"
    printf "  ${CYAN}Time:   ${TIMESTAMP}${RESET}\n"

    case "${target}" in
        local)
            run_prechecks
            build_assets
            create_archive
            deploy_local
            ;;
        staging)
            run_prechecks
            build_assets
            create_archive
            deploy_staging
            ;;
        production)
            run_prechecks
            build_assets
            create_archive
            deploy_production
            ;;
        check)
            run_prechecks
            ok "Pre-deployment checks complete."
            ;;
        archive)
            run_prechecks
            build_assets
            create_archive
            ok "Archive creation complete."
            ;;
        *)
            fail "Unknown target: ${target}"
            usage
            exit 1
            ;;
    esac

    printf "\n${GREEN}${BOLD}  Deployment pipeline finished successfully.${RESET}\n\n"
}

main "$@"
