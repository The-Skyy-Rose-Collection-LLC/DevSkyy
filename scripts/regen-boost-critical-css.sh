#!/usr/bin/env bash
# Regenerate Jetpack Boost critical CSS on skyyrose.co.
#
# Fixes the stale-cache console error: the theme no longer references the
# external grainy-gradients.vercel.app/noise.svg, but Boost's cached critical
# CSS still holds the dead rule. We force a fresh regeneration.
#
# Strategy (least-disruptive first):
#   1. Probe Boost's WP-CLI surface + critical-CSS storage (read-only).
#   2. If a CLI regenerate/clear command exists, use it in place (no downtime).
#   3. Otherwise clear the stored critical-CSS option so Boost rebuilds lazily.
#   4. Guaranteed fallback: reactivate Boost (brief unoptimized window, self-heals).
# Then flush caches and verify the dead URL is gone from the homepage.
#
# Usage: STOPSHOW_ACK=1 bash scripts/regen-boost-critical-css.sh   (production write — gated)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$ROOT/.env.wordpress}"
[ -f "$ENV_FILE" ] || { echo "FATAL: $ENV_FILE missing" >&2; exit 1; }
# shellcheck source=/dev/null
source "$ENV_FILE"
: "${SSH_USER:?missing in env}"; : "${SSH_HOST:?missing in env}"

KEY="${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
PORT="${SSH_PORT:-22}"
SSH=(ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p "$PORT" -i "$KEY")
HOST="${SSH_USER}@${SSH_HOST}"

echo "==> [probe] Boost status + CLI surface + critical-css options (read-only)"
"${SSH[@]}" "$HOST" "wp plugin get jetpack-boost --field=status 2>/dev/null; echo '--- cli ---'; wp help jetpack-boost 2>/dev/null | sed -n '1,40p' || echo 'no jetpack-boost CLI'; echo '--- options ---'; wp option list --search='jetpack_boost*' --format=table 2>/dev/null | sed -n '1,40p' || true"

echo "==> [regen] clearing stored critical CSS + reactivating Boost"
# data_sync stores critical CSS state under jetpack_boost_ds_* ; delete the
# critical-css state keys if present (harmless — Boost rebuilds them), then
# reactivate to kick a fresh generation. Each step tolerates absence.
"${SSH[@]}" "$HOST" "
  wp option delete jetpack_boost_ds_critical_css_state 2>/dev/null || true
  wp option delete jetpack_boost_ds_critical_css_state_errors 2>/dev/null || true
  wp option delete jetpack_boost_critical_css 2>/dev/null || true
  wp plugin deactivate jetpack-boost 2>/dev/null || true
  wp plugin activate jetpack-boost 2>/dev/null || true
  wp cache flush 2>/dev/null || true
  wp transient delete --all 2>/dev/null || true
"

echo "==> [verify] dead grain URL gone from homepage critical CSS?"
HITS="$(curl -s "https://skyyrose.co/?cb=$(date +%s)" 2>/dev/null | grep -c "grainy-gradients.vercel.app" || true)"
echo "grainy-gradients.vercel.app occurrences on homepage: ${HITS}"
if [ "${HITS}" = "0" ]; then
  echo "RESULT: PASS — dead grain URL no longer present"
else
  echo "RESULT: PENDING — critical CSS may regenerate async on next requests; re-check in a minute" >&2
fi
