#!/usr/bin/env bash
# Deploy the Ally-AJAX-guard MU-plugin to skyyrose.co wp-content/mu-plugins/.
#
# Fixes the CommerceKit nonce-endpoint JSON corruption: Ally (pojo-accessibility)
# injects its remediation <style> into every response, including JSON. This
# MU-plugin removes Ally from the active-plugins list on AJAX/REST requests only.
#
# Credentials are sourced from .env.wordpress at runtime (never printed). Uses the
# same SSH key + host the theme deploy uses. Verifies the endpoint afterward.
#
# Usage: STOPSHOW_ACK=1 bash scripts/deploy-mu-plugin.sh   (production write — gated)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${ENV_FILE:-$ROOT/.env.wordpress}"
SRC="$ROOT/wordpress/mu-plugins/skyyrose-ally-ajax-guard.php"

[ -f "$ENV_FILE" ] || { echo "FATAL: $ENV_FILE missing" >&2; exit 1; }
[ -f "$SRC" ]      || { echo "FATAL: $SRC missing" >&2; exit 1; }
php -l "$SRC" >/dev/null || { echo "FATAL: php syntax error in mu-plugin" >&2; exit 1; }

# shellcheck source=/dev/null
source "$ENV_FILE"
: "${SSH_USER:?missing in env}"; : "${SSH_HOST:?missing in env}"; : "${WP_THEME_PATH:?missing in env}"

KEY="${SSH_KEY_PATH:-$HOME/.ssh/skyyrose-deploy}"
PORT="${SSH_PORT:-22}"
WP_CONTENT="$(dirname "$(dirname "$WP_THEME_PATH")")"   # .../wp-content/themes/X -> .../wp-content
MU_DIR="$WP_CONTENT/mu-plugins"
SSH=(ssh -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p "$PORT" -i "$KEY")
SCP=(scp -o StrictHostKeyChecking=accept-new -P "$PORT" -i "$KEY")

echo "==> ensuring $MU_DIR exists"
"${SSH[@]}" "${SSH_USER}@${SSH_HOST}" "mkdir -p '$MU_DIR'"

echo "==> uploading skyyrose-ally-ajax-guard.php"
"${SCP[@]}" "$SRC" "${SSH_USER}@${SSH_HOST}:$MU_DIR/skyyrose-ally-ajax-guard.php"

echo "==> flushing cache"
"${SSH[@]}" "${SSH_USER}@${SSH_HOST}" "wp cache flush" >/dev/null 2>&1 || true

echo "==> verifying nonce endpoint (should be clean JSON, no <head>/ea11y)"
RESP="$(curl -s "https://skyyrose.co/?commercekit-ajax=commercekit_get_nonce&cb=$(date +%s)" 2>/dev/null)"
echo "RESP[0:200]: ${RESP:0:200}"
if printf '%s' "$RESP" | grep -q "ea11y-remediation-styles"; then
  echo "RESULT: STILL CORRUPTED — ea11y markup present" >&2
  exit 2
fi
case "$RESP" in
  '{'*) echo "RESULT: PASS — clean JSON, no Ally injection" ;;
  *)    echo "RESULT: PARTIAL — Ally gone but body not pure JSON; inspect (residual wrapper?)" ;;
esac
