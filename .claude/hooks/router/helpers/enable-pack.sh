#!/usr/bin/env bash
# Flip a Claude Code plugin's enabled state in ~/.claude/settings.json.
# Usage:
#   enable-pack.sh <plugin-name>          # enable
#   enable-pack.sh -d <plugin-name>       # disable
#   enable-pack.sh --list                 # list current enabled set
#   enable-pack.sh --restore-backup       # restore most-recent backup
#
# Notes:
#   - Modifies ~/.claude/settings.json in place via jq.
#   - Always writes a timestamped backup before changing.
#   - Plugin name must match the full key (e.g., 'caveman@caveman').

set -euo pipefail

SETTINGS="$HOME/.claude/settings.json"

usage() {
    sed -n '2,9p' "$0" | sed 's/^# //; s/^#//'
    exit 1
}

require_jq() {
    command -v jq >/dev/null 2>&1 || {
        echo "ERROR: jq required. brew install jq" >&2
        exit 2
    }
}

backup() {
    local ts
    ts=$(date +%Y%m%d-%H%M%S)
    cp "$SETTINGS" "$SETTINGS.backup-$ts"
    echo "Backup → $SETTINGS.backup-$ts"
}

list_enabled() {
    require_jq
    jq -r '.enabledPlugins | to_entries[] | select(.value == true) | .key' "$SETTINGS"
}

restore_backup() {
    local latest
    latest=$(ls -t "$SETTINGS".backup-* 2>/dev/null | head -1 || true)
    if [[ -z "$latest" ]]; then
        echo "ERROR: no backup found" >&2
        exit 3
    fi
    cp "$latest" "$SETTINGS"
    echo "Restored from $latest"
}

flip() {
    local plugin="$1"
    local value="$2"
    require_jq
    if ! jq -e --arg p "$plugin" '.enabledPlugins | has($p)' "$SETTINGS" >/dev/null; then
        echo "ERROR: plugin '$plugin' not found in enabledPlugins map" >&2
        echo "Run: $0 --list  to see current state" >&2
        exit 4
    fi
    backup
    local tmp
    tmp=$(mktemp)
    jq --arg p "$plugin" --argjson v "$value" '.enabledPlugins[$p] = $v' "$SETTINGS" >"$tmp"
    mv "$tmp" "$SETTINGS"
    echo "Set enabledPlugins[\"$plugin\"] = $value"
    echo "Restart Claude Code to apply."
}

case "${1:-}" in
    --list) list_enabled ;;
    --restore-backup) restore_backup ;;
    -d) [[ -n "${2:-}" ]] || usage; flip "$2" false ;;
    -h | --help | "") usage ;;
    *) flip "$1" true ;;
esac
