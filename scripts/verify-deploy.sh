#!/usr/bin/env bash
# scripts/verify-deploy.sh -- Post-deploy deep content verification for skyyrose.co
#
# Checks the live WordPress site for HTTP 200 AND page content markers.
# Catches "white screen of death", stuck maintenance mode, and partial deploy
# failures that return HTTP 200 but serve broken content.
#
# Usage:
#   bash scripts/verify-deploy.sh              # Verify production (skyyrose.co)
#   bash scripts/verify-deploy.sh --list       # Print health check list (no HTTP)
#   bash scripts/verify-deploy.sh --url URL    # Override target URL
#   bash scripts/verify-deploy.sh --help       # Show this help message
#   WORDPRESS_URL=https://staging.skyyrose.co bash scripts/verify-deploy.sh
#
# Exit codes:
#   0 - All pages verified (HTTP 200 + content markers found)
#   1 - One or more pages failed verification
#
# Environment:
#   WORDPRESS_URL   Target site URL (default: https://skyyrose.co)

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SITE_URL="${WORDPRESS_URL:-https://skyyrose.co}"
TIMESTAMP="$(date +%s)"
FAILURES=0
CHECKS=0

# ---------------------------------------------------------------------------
# Color logging (matches deploy-theme.sh pattern)
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No color

log_info()    { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
# shellcheck disable=SC2329  # Part of standard logging interface (used by deploy-pipeline.sh)
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[FAIL]${NC} $1"; }

# ---------------------------------------------------------------------------
# Usage / help
# ---------------------------------------------------------------------------
usage() {
    echo "Usage: verify-deploy.sh [OPTIONS]"
    echo ""
    echo "Post-deploy deep content verification for the SkyyRose WordPress site."
    echo "Checks HTTP status AND response body content for each page."
    echo ""
    echo "Options:"
    echo "  --help       Show this help message"
    echo "  --list       Print health check list without making HTTP requests"
    echo "  --url URL    Override the target site URL"
    echo ""
    echo "Environment:"
    echo "  WORDPRESS_URL   Target site URL (default: https://skyyrose.co)"
    echo ""
    echo "Pages verified:"
    echo "  Homepage, REST API, Collection: Black Rose, Collection: Love Hurts,"
    echo "  Collection: Signature, About"
}

# ---------------------------------------------------------------------------
# Health check definitions: "name|path|content_marker"
# ---------------------------------------------------------------------------
HEALTH_CHECKS=(
    "Homepage|/|SKYY ROSE"
    "REST API|/index.php?rest_route=/|namespaces"
    "Collection: Black Rose|/collection-black-rose/|Black Rose"
    "Collection: Love Hurts|/collection-love-hurts/|Love Hurts"
    "Collection: Signature|/collection-signature/|Signature"
    "About|/about/|SkyyRose"
)

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --help|-h)
                usage
                exit 0
                ;;
            --list)
                list_checks
                exit 0
                ;;
            --url)
                if [[ -n "${2:-}" ]]; then
                    SITE_URL="$2"
                    shift 2
                else
                    log_error "--url requires a URL argument"
                    exit 1
                fi
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
# List health checks (no HTTP requests)
# ---------------------------------------------------------------------------
list_checks() {
    echo "=== Health Check Pages ==="
    echo ""
    for entry in "${HEALTH_CHECKS[@]}"; do
        IFS='|' read -r name path marker <<< "$entry"
        echo "  $name"
        echo "    URL:    ${SITE_URL}${path}"
        echo "    Marker: $marker"
        echo ""
    done
    echo "Total: ${#HEALTH_CHECKS[@]} checks"
}

# ---------------------------------------------------------------------------
# Deep content verification for a single page
# ---------------------------------------------------------------------------
verify_page() {
    local name="$1"
    local url="$2"
    local marker="$3"

    CHECKS=$((CHECKS + 1))

    # Build cache-busting URL: use & if URL already has ?, otherwise use ?
    local full_url
    if [[ "$url" == *"?"* ]]; then
        full_url="${url}&_verify=${TIMESTAMP}"
    else
        full_url="${url}?_verify=${TIMESTAMP}"
    fi

    # Fetch page with retry support
    local response http_code body
    response=$(curl -sSL -w "\n%{http_code}" \
        --connect-timeout 10 --max-time 30 \
        --retry 2 --retry-delay 3 \
        "$full_url" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    # Check HTTP status
    if [[ "$http_code" -ne 200 ]]; then
        log_error "$name: HTTP $http_code (expected 200) -- $full_url"
        FAILURES=$((FAILURES + 1))
        return 1
    fi

    # Check content marker (case-insensitive)
    if ! echo "$body" | grep -qi "$marker"; then
        log_error "$name: Content marker '$marker' not found -- $full_url"
        FAILURES=$((FAILURES + 1))
        return 1
    fi

    log_success "$name: HTTP 200 + content verified"
    return 0
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    parse_args "$@"

    echo ""
    log_info "=== SkyyRose Post-Deploy Verification ==="
    log_info "Target: $SITE_URL"
    log_info "Cache-bust: _verify=$TIMESTAMP"
    echo ""

    # Run all health checks -- collect failures, do not exit on first
    for entry in "${HEALTH_CHECKS[@]}"; do
        IFS='|' read -r name path marker <<< "$entry"
        verify_page "$name" "${SITE_URL}${path}" "$marker" || true
    done

    # Summary
    echo ""
    log_info "=== Verification Summary ==="
    log_info "Checks: $CHECKS  Passed: $((CHECKS - FAILURES))  Failed: $FAILURES"

    if [[ "$FAILURES" -eq 0 ]]; then
        echo ""
        log_success "All $CHECKS pages verified successfully"
        exit 0
    else
        echo ""
        log_error "$FAILURES of $CHECKS pages failed verification"
        exit 1
    fi
}

main "$@"
