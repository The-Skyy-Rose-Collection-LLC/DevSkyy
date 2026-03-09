#!/usr/bin/env bash
# Lint PHP files passed as arguments.
# php -l only accepts one file at a time, so we loop.
set -euo pipefail

ERRORS=0
for file in "$@"; do
  # Skip flag-like arguments (CLAUDE.md learning: reject flag-like targets)
  case "$file" in -*) continue ;; esac

  # Skip if file doesn't exist (could be deleted in staging)
  [[ -f "$file" ]] || continue

  if ! php -l "$file" 2>&1 | grep -q "No syntax errors"; then
    echo "FAIL: $file"
    ERRORS=$((ERRORS + 1))
  fi
done

if [ "$ERRORS" -gt 0 ]; then
  echo "PHP syntax errors found in $ERRORS file(s)"
  exit 1
fi
