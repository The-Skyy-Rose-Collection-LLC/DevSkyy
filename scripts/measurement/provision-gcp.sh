#!/usr/bin/env bash
# scripts/measurement/provision-gcp.sh
# Phase 0.5 helper — automates Step 1 of eval/measurement-access-requests.md.
#
# What it does (idempotent — safe to re-run):
#   1. Verifies gcloud is installed and authenticated.
#   2. Creates GCP project (default: skyyrose-measurement; override via $SKYYROSE_GCP_PROJECT or --project-id).
#   3. Creates service account "skyyrose-readonly" inside the project.
#   4. Generates a JSON key for the service account into ~/Downloads/skyyrose-readonly-key.json.
#   5. Enables the three required APIs: Analytics Data, Search Console, Tag Manager.
#   6. Prints the service account email — copy this into Steps 2–4 of the access packet.
#
# What it does NOT do (cannot — no API exists for self-grant):
#   - Add the service account to GA4 Property Access Management
#   - Add the service account to Search Console Users and permissions
#   - Add the service account to Tag Manager User Management
# Those four steps remain human work in admin UIs (per the access packet).
#
# Pre-flight: run `gcloud auth login` once before this script. The script asserts an
# active account exists and exits non-zero with instructions if not.

set -euo pipefail

PROJECT_ID="${SKYYROSE_GCP_PROJECT:-skyyrose-measurement}"
SA_NAME="skyyrose-readonly"
SA_DESCRIPTION="Read-only access for Skyyrose measurement pipelines"
KEY_OUTPUT_PATH="${HOME}/Downloads/skyyrose-readonly-key.json"
APIS=(
  analyticsdata.googleapis.com
  searchconsole.googleapis.com
  tagmanager.googleapis.com
)

# --- Argument parsing -------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-id)
      PROJECT_ID="$2"
      shift 2
      ;;
    --key-out)
      KEY_OUTPUT_PATH="$2"
      shift 2
      ;;
    -h | --help)
      grep -E "^# " "$0" | sed 's/^# //'
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 64
      ;;
  esac
done

color() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
info()  { color "36" "→ $*"; }
ok()    { color "32" "✓ $*"; }
fail()  { color "31" "✗ $*" >&2; }

# --- Pre-flight: gcloud installed + authenticated ---------------------------
if ! command -v gcloud >/dev/null 2>&1; then
  fail "gcloud not installed. Install with: brew install --cask google-cloud-sdk"
  exit 127
fi

ACTIVE_ACCOUNT="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
if [[ -z "$ACTIVE_ACCOUNT" ]]; then
  fail "No active gcloud account. Run: gcloud auth login"
  exit 1
fi
ok "Authenticated as: $ACTIVE_ACCOUNT"

# --- Step 1.1: Project ------------------------------------------------------
info "Ensuring project '$PROJECT_ID' exists..."
if gcloud projects describe "$PROJECT_ID" >/dev/null 2>&1; then
  ok "Project already exists — reusing"
else
  if ! gcloud projects create "$PROJECT_ID" --name="Skyyrose Measurement" 2>&1 | tee /tmp/gcp-create.log; then
    if grep -q "already in use" /tmp/gcp-create.log; then
      fail "Project ID '$PROJECT_ID' is taken globally. Pick a unique one. Suggestions:"
      fail "  --project-id ${PROJECT_ID}-${USER}"
      fail "  --project-id ${PROJECT_ID}-$(date +%s | tail -c 6)"
      fail "  --project-id ${PROJECT_ID}-skyy"
    fi
    exit 1
  fi
  ok "Project created"
fi

gcloud config set project "$PROJECT_ID" >/dev/null 2>&1
ok "Active project set to $PROJECT_ID"

# --- Step 1.2: Service account ---------------------------------------------
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
info "Ensuring service account '$SA_NAME' exists..."
if gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" >/dev/null 2>&1; then
  ok "Service account already exists — reusing"
else
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Skyyrose Read-only Measurement" \
    --description="$SA_DESCRIPTION" \
    --project="$PROJECT_ID" >/dev/null
  ok "Service account created: $SA_EMAIL"
fi

# --- Step 1.3: JSON key -----------------------------------------------------
if [[ -f "$KEY_OUTPUT_PATH" ]]; then
  fail "Key file already exists at $KEY_OUTPUT_PATH"
  fail "Refusing to overwrite — delete it first or pass --key-out <other-path>"
  fail "(Existing keys remain valid in GCP IAM until you explicitly delete them there.)"
  # Don't exit non-zero here — the rest of provisioning is still useful.
  ok "Skipping key generation; using existing file"
else
  info "Generating JSON key → $KEY_OUTPUT_PATH"
  gcloud iam service-accounts keys create "$KEY_OUTPUT_PATH" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID" >/dev/null
  chmod 600 "$KEY_OUTPUT_PATH"
  ok "Key file written (mode 600)"
fi

# --- Step 1.4: Enable APIs --------------------------------------------------
for api in "${APIS[@]}"; do
  info "Enabling $api..."
  gcloud services enable "$api" --project="$PROJECT_ID" >/dev/null
  ok "$api enabled"
done

# --- Output: ready-to-use values for next steps -----------------------------
cat <<EOF

============================================================
  Step 1 complete. Use these values for the next steps:
============================================================

Service account email (paste into Steps 2-4 admin UIs):
  ${SA_EMAIL}

Key file (for Step 7 Vercel env):
  ${KEY_OUTPUT_PATH}

Step 7 command for the JSON env var:
  vercel env add GOOGLE_SERVICE_ACCOUNT_JSON production < ${KEY_OUTPUT_PATH}

Next: action Steps 2-5 of eval/measurement-access-requests.md (admin UI grants).
============================================================
EOF
