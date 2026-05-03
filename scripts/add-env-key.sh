#!/usr/bin/env bash
# scripts/add-env-key.sh
# Add a key to every active .env file in one shot.
#
# Usage:
#   scripts/add-env-key.sh KEY [VALUE]
#   scripts/add-env-key.sh KEY                    # value prompted (hidden input)
#   scripts/add-env-key.sh KEY VALUE              # value inline
#   scripts/add-env-key.sh KEY VALUE --templates  # also write placeholder to .env.example
#
# Behavior:
#   - The real value is written ONLY to .env (gitignored).
#   - Tracked env files (.env.production, .env.staging, .env.skyyrose-experiences,
#     .env.wordpress) get the key with a placeholder value, so the schema stays in sync
#     across environments without leaking secrets to git.
#   - If KEY already exists in a file, the file is left alone (no overwrite).
#     Pass --force to overwrite.
#
# Why this exists:
#   detect-secrets + 8 active env files made adding a single key a multi-step,
#   easy-to-typo chore. This collapses it to one command.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

# --- Parse args ----------------------------------------------------------------
FORCE=0
WRITE_TEMPLATE=0
KEY=""
VALUE=""
VALUE_PROVIDED=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force)     FORCE=1; shift ;;
    --templates) WRITE_TEMPLATE=1; shift ;;
    -h|--help)
      sed -n '2,22p' "$0"
      exit 0
      ;;
    *)
      if [[ -z "$KEY" ]]; then
        KEY="$1"
      elif [[ $VALUE_PROVIDED -eq 0 ]]; then
        VALUE="$1"
        VALUE_PROVIDED=1
      else
        echo "Unexpected argument: $1" >&2
        exit 2
      fi
      shift
      ;;
  esac
done

if [[ -z "$KEY" ]]; then
  echo "Usage: scripts/add-env-key.sh KEY [VALUE] [--force] [--templates]" >&2
  exit 2
fi

# Validate KEY shape: uppercase, digits, underscore; must start with letter/underscore.
if ! [[ "$KEY" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
  echo "ERROR: KEY '$KEY' must match ^[A-Z_][A-Z0-9_]*$ (uppercase, digits, underscore)." >&2
  exit 2
fi

if [[ $VALUE_PROVIDED -eq 0 ]]; then
  # Read hidden — value never lands in shell history.
  read -r -s -p "Value for $KEY (input hidden): " VALUE
  echo
fi

# --- Targets -------------------------------------------------------------------
# The real, gitignored secret store. Receives the actual value.
REAL_FILE=".env"

# Tracked env scaffolds. Receive a placeholder so deploys know the key exists.
# Edit this list if your topology changes.
TEMPLATE_FILES=(
  ".env.production"
  ".env.staging"
  ".env.skyyrose-experiences"
  ".env.wordpress"
)
[[ $WRITE_TEMPLATE -eq 1 ]] && TEMPLATE_FILES+=(".env.example")

PLACEHOLDER="REPLACE_ME__set_in_real_env"

# --- Helpers -------------------------------------------------------------------
key_exists_in() {
  local file="$1"
  [[ -f "$file" ]] || return 1
  grep -qE "^[[:space:]]*${KEY}=" "$file"
}

# Append `KEY=VAL` to file. Ensures file ends with newline first.
append_kv() {
  local file="$1" val="$2"
  if [[ -f "$file" ]] && [[ -n "$(tail -c 1 "$file")" ]]; then
    printf '\n' >> "$file"
  fi
  printf '%s=%s\n' "$KEY" "$val" >> "$file"
}

# Replace existing KEY= line in file (BSD/macOS sed-safe via awk).
replace_kv() {
  local file="$1" val="$2" tmp
  tmp="$(mktemp)"
  awk -v k="$KEY" -v v="$val" '
    BEGIN { done=0 }
    {
      if (!done && $0 ~ "^[[:space:]]*"k"=") {
        print k"="v
        done=1
      } else {
        print
      }
    }
  ' "$file" > "$tmp"
  mv "$tmp" "$file"
}

apply_to() {
  local file="$1" val="$2" label="$3"
  if [[ ! -f "$file" ]]; then
    echo "  skip   $label  ($file does not exist)"
    return 0
  fi
  if key_exists_in "$file"; then
    if [[ $FORCE -eq 1 ]]; then
      replace_kv "$file" "$val"
      echo "  update $label  ($file)"
    else
      echo "  keep   $label  ($file already has $KEY; pass --force to overwrite)"
    fi
  else
    append_kv "$file" "$val"
    echo "  add    $label  ($file)"
  fi
}

# --- Apply ---------------------------------------------------------------------
echo "Adding $KEY across env files:"

# Real secret -> .env only
apply_to "$REAL_FILE" "$VALUE" "real value"

# Placeholders -> tracked templates
for f in "${TEMPLATE_FILES[@]}"; do
  apply_to "$f" "$PLACEHOLDER" "placeholder"
done

echo
echo "Done. Real value written to .env (gitignored)."
echo "Templates updated with placeholder '$PLACEHOLDER' so the key is visible to deploys."
echo "Replace placeholders in deployed environments via your secret manager."
