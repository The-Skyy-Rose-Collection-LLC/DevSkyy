#!/bin/bash
set -euo pipefail

# Tripo3D generation runner.
# Secrets are NEVER hardcoded — TRIPO_API_KEY must come from the environment or .env.
# The previously hardcoded key was exposed in git history and MUST be rotated in the
# Tripo dashboard before this script is used again.
set -a
[ -f .env ] && . ./.env
set +a
: "${TRIPO_API_KEY:?TRIPO_API_KEY not set — add the rotated key to .env}"

# Use certifi's bundle from the active interpreter (do NOT disable TLS verification).
SSL_CERT_FILE="$(python3 -c 'import certifi; print(certifi.where())')"
export SSL_CERT_FILE

python3 scripts/generate_3d_models_official_sdk.py
