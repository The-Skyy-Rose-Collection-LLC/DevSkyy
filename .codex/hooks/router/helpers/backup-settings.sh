#!/usr/bin/env bash
# Timestamped backup of both global and project Claude Code settings.
# Run before any config-modifying script.

set -euo pipefail

TS=$(date +%Y%m%d-%H%M%S)
GLOBAL="$HOME/.claude/settings.json"
PROJECT="$HOME/DevSkyy/.claude/settings.json"

for src in "$GLOBAL" "$PROJECT"; do
    if [[ -f "$src" ]]; then
        dst="$src.backup-$TS"
        cp "$src" "$dst"
        echo "✓ $src → $dst"
    fi
done
