#!/usr/bin/env bash
# scripts/wp-cli-nextgen-backfill-loop.sh
#
# Self-pacing batch loop for wp skyyrose nextgen-backfill.
# Each iteration = fresh SSH session + bounded WP-CLI run, avoids
# WordPress.com session timeouts on long single-shot backfills.
#
# Stops when:
# - dry-run reports "Would convert 0 files" (nothing left to do)
# - any batch errors (non-zero exit)
# - max iterations reached
#
# Usage:
#   bash scripts/wp-cli-nextgen-backfill-loop.sh
#   BATCH_SIZE=50 MAX_ITERS=40 bash scripts/wp-cli-nextgen-backfill-loop.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BATCH_SIZE="${BATCH_SIZE:-25}"
MAX_ITERS="${MAX_ITERS:-30}"
SLEEP_BETWEEN="${SLEEP_BETWEEN:-2}"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m'

log_info()    { echo -e "${BLUE}[LOOP]${NC} $1"; }
log_done()    { echo -e "${GREEN}[DONE]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Quick dry-run sanity check first — surfaces remaining work + verifies SSH works.
log_info "Initial dry-run audit..."
if ! dry_output=$("$SCRIPT_DIR/wp-cli-nextgen-backfill.sh" --dry-run 2>&1); then
    log_error "Dry-run failed:"
    echo "$dry_output"
    exit 1
fi
echo "$dry_output"

# Extract "Would convert N files" from the dry-run output.
remaining=$(echo "$dry_output" | grep -oE 'Would convert [0-9]+' | grep -oE '[0-9]+' | head -1)
if [[ -z "$remaining" ]] || [[ "$remaining" == "0" ]]; then
    log_done "Nothing to convert — backfill already complete."
    exit 0
fi
log_info "$remaining files remaining. Batches of $BATCH_SIZE, max $MAX_ITERS iterations."

consecutive_fails=0
MAX_CONSECUTIVE_FAILS="${MAX_CONSECUTIVE_FAILS:-5}"
total_fails=0

for ((i = 1; i <= MAX_ITERS; i++)); do
    log_info "Iteration $i/$MAX_ITERS (--limit=$BATCH_SIZE) ..."
    # set +e so a failing batch doesn't kill the loop (script has set -e at top).
    set +e
    "$SCRIPT_DIR/wp-cli-nextgen-backfill.sh" "--limit=$BATCH_SIZE"
    batch_exit=$?
    set -e

    if [[ $batch_exit -ne 0 ]]; then
        ((consecutive_fails++))
        ((total_fails++))
        log_warn "Batch $i failed (exit $batch_exit). Consecutive: $consecutive_fails/$MAX_CONSECUTIVE_FAILS. Total: $total_fails."
        if (( consecutive_fails >= MAX_CONSECUTIVE_FAILS )); then
            log_error "Hit $MAX_CONSECUTIVE_FAILS consecutive failures — stopping. Idempotent re-run safe."
            exit 2
        fi
        sleep $(( SLEEP_BETWEEN * 3 ))  # back off after failure
        continue
    fi
    consecutive_fails=0

    # Re-check remaining via fresh dry-run every 4 iterations.
    if (( i % 4 == 0 )); then
        if dry_output=$("$SCRIPT_DIR/wp-cli-nextgen-backfill.sh" --dry-run 2>&1); then
            remaining=$(echo "$dry_output" | grep -oE 'Would convert [0-9]+' | grep -oE '[0-9]+' | head -1)
            log_info "Remaining after $i iterations: ${remaining:-unknown} (total_fails=$total_fails)"
            if [[ -n "$remaining" ]] && [[ "$remaining" == "0" ]]; then
                log_done "All files converted after $i iterations."
                exit 0
            fi
        fi
    fi

    sleep "$SLEEP_BETWEEN"
done

log_warn "Hit MAX_ITERS=$MAX_ITERS. Re-run to continue (idempotent)."
exit 0
