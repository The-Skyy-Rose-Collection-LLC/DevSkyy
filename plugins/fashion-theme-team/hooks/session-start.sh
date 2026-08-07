#!/usr/bin/env bash
# shellcheck disable=SC2016
set -euo pipefail

project_root="${CLAUDE_PROJECT_DIR:-${PWD}}"

if [[ -d "${project_root}/wordpress-theme" ]] || [[ -f "${project_root}/style.css" ]]; then
  printf '%s\n' '[FashionThemeTeam] Motherbase and Fashion Theme Brain available. Resume the phase ledger, route work through brain/taxonomy.json, load only relevant packs and runnable charters, require preview.html + contract.json + evidence.json, keep builders separate from reviewers, and apply the minimal tool profile.'
fi
