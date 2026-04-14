#!/usr/bin/env bash
# claude-mem-settings.sh — Interactive settings manager for ~/.claude-mem/settings.json

set -euo pipefail

SETTINGS_FILE="${HOME}/.claude-mem/settings.json"

# ── Colors ────────────────────────────────────────────────────────────────────
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# ── Helpers ───────────────────────────────────────────────────────────────────
get() {
  python3 -c "import json,sys; d=json.load(open('${SETTINGS_FILE}')); print(d.get('$1',''))"
}

set_key() {
  local key="$1" val="$2"
  python3 - "$key" "$val" <<'PY'
import json, sys
key, val = sys.argv[1], sys.argv[2]
path = __import__('os').path.expanduser('~/.claude-mem/settings.json')
with open(path) as f:
    d = json.load(f)
d[key] = val
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
print(f"  ✓ {key} = {val!r}")
PY
}

header() {
  clear
  echo -e "${BOLD}${CYAN}"
  echo "  ╔══════════════════════════════════════════════╗"
  echo "  ║        claude-mem  settings manager          ║"
  echo "  ║   ~/.claude-mem/settings.json  •  v12.1.0    ║"
  echo "  ╚══════════════════════════════════════════════╝${RESET}"
  echo
}

prompt_value() {
  local key="$1" current
  current=$(get "$key")
  echo -e "  ${DIM}current:${RESET} ${YELLOW}${current}${RESET}"
  echo -en "  new value (enter to keep): "
  read -r new_val
  if [[ -n "$new_val" ]]; then
    set_key "$key" "$new_val"
  else
    echo -e "  ${DIM}unchanged${RESET}"
  fi
}

toggle() {
  local key="$1" current
  current=$(get "$key")
  local new_val
  if [[ "$current" == "true" ]]; then new_val="false"; else new_val="true"; fi
  set_key "$key" "$new_val"
}

pause() {
  echo
  echo -en "  ${DIM}press enter to continue...${RESET}"
  read -r
}

require_settings() {
  if [[ ! -f "$SETTINGS_FILE" ]]; then
    echo -e "${RED}  Error: ${SETTINGS_FILE} not found.${RESET}"
    exit 1
  fi
}

# ── Category menus ────────────────────────────────────────────────────────────

menu_core() {
  while true; do
    header
    echo -e "  ${BOLD}Core / Provider${RESET}\n"
    echo -e "  1) Model            $(get CLAUDE_MEM_MODEL)"
    echo -e "  2) Provider         $(get CLAUDE_MEM_PROVIDER)"
    echo -e "  3) Auth method      $(get CLAUDE_MEM_CLAUDE_AUTH_METHOD)"
    echo -e "  4) Mode             $(get CLAUDE_MEM_MODE)"
    echo -e "  5) Log level        $(get CLAUDE_MEM_LOG_LEVEL)"
    echo -e "  6) Max agents       $(get CLAUDE_MEM_MAX_CONCURRENT_AGENTS)"
    echo -e "  7) Skip tools       $(get CLAUDE_MEM_SKIP_TOOLS)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; prompt_value CLAUDE_MEM_MODEL; pause ;;
      2) echo; echo -e "  Options: claude | gemini | openrouter"; prompt_value CLAUDE_MEM_PROVIDER; pause ;;
      3) echo; echo -e "  Options: cli | api_key"; prompt_value CLAUDE_MEM_CLAUDE_AUTH_METHOD; pause ;;
      4) echo; echo -e "  Options: code | code--chill | code--nl | ..."; prompt_value CLAUDE_MEM_MODE; pause ;;
      5) echo; echo -e "  Options: DEBUG | INFO | WARN | ERROR"; prompt_value CLAUDE_MEM_LOG_LEVEL; pause ;;
      6) echo; prompt_value CLAUDE_MEM_MAX_CONCURRENT_AGENTS; pause ;;
      7) echo; prompt_value CLAUDE_MEM_SKIP_TOOLS; pause ;;
      b|B) break ;;
    esac
  done
}

menu_context() {
  while true; do
    header
    echo -e "  ${BOLD}Context Injection${RESET}\n"
    echo -e "  1) Observations count      $(get CLAUDE_MEM_CONTEXT_OBSERVATIONS)"
    echo -e "  2) Session count           $(get CLAUDE_MEM_CONTEXT_SESSION_COUNT)"
    echo -e "  3) Full count              $(get CLAUDE_MEM_CONTEXT_FULL_COUNT)"
    echo -e "  4) Full field              $(get CLAUDE_MEM_CONTEXT_FULL_FIELD)"
    echo -e "  5) Show last summary       $(get CLAUDE_MEM_CONTEXT_SHOW_LAST_SUMMARY)"
    echo -e "  6) Show last message       $(get CLAUDE_MEM_CONTEXT_SHOW_LAST_MESSAGE)"
    echo -e "  7) Show terminal output    $(get CLAUDE_MEM_CONTEXT_SHOW_TERMINAL_OUTPUT)"
    echo -e "  8) Show read tokens        $(get CLAUDE_MEM_CONTEXT_SHOW_READ_TOKENS)"
    echo -e "  9) Show work tokens        $(get CLAUDE_MEM_CONTEXT_SHOW_WORK_TOKENS)"
    echo -e "  a) Show savings amount     $(get CLAUDE_MEM_CONTEXT_SHOW_SAVINGS_AMOUNT)"
    echo -e "  s) Show savings percent    $(get CLAUDE_MEM_CONTEXT_SHOW_SAVINGS_PERCENT)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; prompt_value CLAUDE_MEM_CONTEXT_OBSERVATIONS; pause ;;
      2) echo; prompt_value CLAUDE_MEM_CONTEXT_SESSION_COUNT; pause ;;
      3) echo; prompt_value CLAUDE_MEM_CONTEXT_FULL_COUNT; pause ;;
      4) echo; echo -e "  Options: narrative | summary"; prompt_value CLAUDE_MEM_CONTEXT_FULL_FIELD; pause ;;
      5) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_LAST_SUMMARY; pause ;;
      6) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_LAST_MESSAGE; pause ;;
      7) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_TERMINAL_OUTPUT; pause ;;
      8) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_READ_TOKENS; pause ;;
      9) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_WORK_TOKENS; pause ;;
      a|A) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_SAVINGS_AMOUNT; pause ;;
      s|S) echo; toggle CLAUDE_MEM_CONTEXT_SHOW_SAVINGS_PERCENT; pause ;;
      b|B) break ;;
    esac
  done
}

menu_tier() {
  while true; do
    header
    echo -e "  ${BOLD}Tier Routing${RESET}\n"
    echo -e "  1) Enabled           $(get CLAUDE_MEM_TIER_ROUTING_ENABLED)"
    echo -e "  2) Simple model      $(get CLAUDE_MEM_TIER_SIMPLE_MODEL)"
    echo -e "  3) Summary model     $(get CLAUDE_MEM_TIER_SUMMARY_MODEL)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; toggle CLAUDE_MEM_TIER_ROUTING_ENABLED; pause ;;
      2) echo; echo -e "  Options: haiku | sonnet | opus"; prompt_value CLAUDE_MEM_TIER_SIMPLE_MODEL; pause ;;
      3) echo; echo -e "  Leave blank to use main model"; prompt_value CLAUDE_MEM_TIER_SUMMARY_MODEL; pause ;;
      b|B) break ;;
    esac
  done
}

menu_semantic() {
  while true; do
    header
    echo -e "  ${BOLD}Semantic Injection (Chroma)${RESET}\n"
    echo -e "  1) Inject enabled      $(get CLAUDE_MEM_SEMANTIC_INJECT)"
    echo -e "  2) Inject limit        $(get CLAUDE_MEM_SEMANTIC_INJECT_LIMIT)"
    echo -e "  3) Chroma enabled      $(get CLAUDE_MEM_CHROMA_ENABLED)"
    echo -e "  4) Chroma mode         $(get CLAUDE_MEM_CHROMA_MODE)"
    echo -e "  5) Chroma host         $(get CLAUDE_MEM_CHROMA_HOST)"
    echo -e "  6) Chroma port         $(get CLAUDE_MEM_CHROMA_PORT)"
    echo -e "  7) Chroma SSL          $(get CLAUDE_MEM_CHROMA_SSL)"
    echo -e "  8) Chroma API key      $(get CLAUDE_MEM_CHROMA_API_KEY)"
    echo -e "  9) Chroma tenant       $(get CLAUDE_MEM_CHROMA_TENANT)"
    echo -e "  a) Chroma database     $(get CLAUDE_MEM_CHROMA_DATABASE)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; toggle CLAUDE_MEM_SEMANTIC_INJECT; pause ;;
      2) echo; prompt_value CLAUDE_MEM_SEMANTIC_INJECT_LIMIT; pause ;;
      3) echo; toggle CLAUDE_MEM_CHROMA_ENABLED; pause ;;
      4) echo; echo -e "  Options: local | remote"; prompt_value CLAUDE_MEM_CHROMA_MODE; pause ;;
      5) echo; prompt_value CLAUDE_MEM_CHROMA_HOST; pause ;;
      6) echo; prompt_value CLAUDE_MEM_CHROMA_PORT; pause ;;
      7) echo; toggle CLAUDE_MEM_CHROMA_SSL; pause ;;
      8) echo; prompt_value CLAUDE_MEM_CHROMA_API_KEY; pause ;;
      9) echo; prompt_value CLAUDE_MEM_CHROMA_TENANT; pause ;;
      a|A) echo; prompt_value CLAUDE_MEM_CHROMA_DATABASE; pause ;;
      b|B) break ;;
    esac
  done
}

menu_gemini() {
  while true; do
    header
    echo -e "  ${BOLD}Gemini Provider${RESET}\n"
    local key_preview
    key_preview=$(get CLAUDE_MEM_GEMINI_API_KEY)
    [[ -n "$key_preview" ]] && key_preview="${key_preview:0:8}..." || key_preview="(not set)"
    echo -e "  1) API key             ${key_preview}"
    echo -e "  2) Model               $(get CLAUDE_MEM_GEMINI_MODEL)"
    echo -e "  3) Rate limiting       $(get CLAUDE_MEM_GEMINI_RATE_LIMITING_ENABLED)"
    echo -e "  4) Max context msgs    $(get CLAUDE_MEM_GEMINI_MAX_CONTEXT_MESSAGES)"
    echo -e "  5) Max tokens          $(get CLAUDE_MEM_GEMINI_MAX_TOKENS)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; prompt_value CLAUDE_MEM_GEMINI_API_KEY; pause ;;
      2) echo; prompt_value CLAUDE_MEM_GEMINI_MODEL; pause ;;
      3) echo; toggle CLAUDE_MEM_GEMINI_RATE_LIMITING_ENABLED; pause ;;
      4) echo; prompt_value CLAUDE_MEM_GEMINI_MAX_CONTEXT_MESSAGES; pause ;;
      5) echo; prompt_value CLAUDE_MEM_GEMINI_MAX_TOKENS; pause ;;
      b|B) break ;;
    esac
  done
}

menu_openrouter() {
  while true; do
    header
    echo -e "  ${BOLD}OpenRouter Provider${RESET}\n"
    local key_preview
    key_preview=$(get CLAUDE_MEM_OPENROUTER_API_KEY)
    [[ -n "$key_preview" ]] && key_preview="${key_preview:0:8}..." || key_preview="(not set)"
    echo -e "  1) API key             ${key_preview}"
    echo -e "  2) Model               $(get CLAUDE_MEM_OPENROUTER_MODEL)"
    echo -e "  3) Site URL            $(get CLAUDE_MEM_OPENROUTER_SITE_URL)"
    echo -e "  4) App name            $(get CLAUDE_MEM_OPENROUTER_APP_NAME)"
    echo -e "  5) Max context msgs    $(get CLAUDE_MEM_OPENROUTER_MAX_CONTEXT_MESSAGES)"
    echo -e "  6) Max tokens          $(get CLAUDE_MEM_OPENROUTER_MAX_TOKENS)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; prompt_value CLAUDE_MEM_OPENROUTER_API_KEY; pause ;;
      2) echo; prompt_value CLAUDE_MEM_OPENROUTER_MODEL; pause ;;
      3) echo; prompt_value CLAUDE_MEM_OPENROUTER_SITE_URL; pause ;;
      4) echo; prompt_value CLAUDE_MEM_OPENROUTER_APP_NAME; pause ;;
      5) echo; prompt_value CLAUDE_MEM_OPENROUTER_MAX_CONTEXT_MESSAGES; pause ;;
      6) echo; prompt_value CLAUDE_MEM_OPENROUTER_MAX_TOKENS; pause ;;
      b|B) break ;;
    esac
  done
}

menu_transcripts() {
  while true; do
    header
    echo -e "  ${BOLD}Transcripts${RESET}\n"
    echo -e "  1) Enabled        $(get CLAUDE_MEM_TRANSCRIPTS_ENABLED)"
    echo -e "  2) Config path    $(get CLAUDE_MEM_TRANSCRIPTS_CONFIG_PATH)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; toggle CLAUDE_MEM_TRANSCRIPTS_ENABLED; pause ;;
      2) echo; prompt_value CLAUDE_MEM_TRANSCRIPTS_CONFIG_PATH; pause ;;
      b|B) break ;;
    esac
  done
}

menu_folder() {
  while true; do
    header
    echo -e "  ${BOLD}Folder CLAUDE.md${RESET}\n"
    echo -e "  1) Enabled             $(get CLAUDE_MEM_FOLDER_CLAUDEMD_ENABLED)"
    echo -e "  2) Use local md        $(get CLAUDE_MEM_FOLDER_USE_LOCAL_MD)"
    echo -e "  3) MD exclude list     $(get CLAUDE_MEM_FOLDER_MD_EXCLUDE)"
    echo -e "  4) Excluded projects   $(get CLAUDE_MEM_EXCLUDED_PROJECTS)"
    echo -e "\n  b) Back"
    echo -en "\n  Choice: "
    read -r c
    case "$c" in
      1) echo; toggle CLAUDE_MEM_FOLDER_CLAUDEMD_ENABLED; pause ;;
      2) echo; toggle CLAUDE_MEM_FOLDER_USE_LOCAL_MD; pause ;;
      3) echo; prompt_value CLAUDE_MEM_FOLDER_MD_EXCLUDE; pause ;;
      4) echo; prompt_value CLAUDE_MEM_EXCLUDED_PROJECTS; pause ;;
      b|B) break ;;
    esac
  done
}

daemon_controls() {
  header
  echo -e "  ${BOLD}Daemon Controls${RESET}\n"
  echo -e "  Restarting worker to apply settings changes...\n"
  claude-mem restart 2>&1 | sed 's/^/  /'
  pause
}

show_all() {
  header
  echo -e "  ${BOLD}All Settings${RESET}\n"
  python3 - <<PY
import json
with open('${SETTINGS_FILE}') as f:
    d = json.load(f)
for k, v in sorted(d.items()):
    masked = v
    if 'API_KEY' in k and v:
        masked = v[:8] + '...'
    print(f"  {k:<48} {masked}")
PY
  pause
}

# ── Main menu ─────────────────────────────────────────────────────────────────
main() {
  require_settings
  while true; do
    header
    echo -e "  ${BOLD}Settings Categories${RESET}\n"
    echo -e "  1) Core / Provider"
    echo -e "  2) Context Injection"
    echo -e "  3) Tier Routing"
    echo -e "  4) Semantic / Chroma"
    echo -e "  5) Gemini"
    echo -e "  6) OpenRouter"
    echo -e "  7) Transcripts"
    echo -e "  8) Folder CLAUDE.md"
    echo -e "  9) Show all settings"
    echo -e "  r) Restart daemon"
    echo -e "  q) Quit"
    echo -en "\n  Choice: "
    read -r choice
    case "$choice" in
      1) menu_core ;;
      2) menu_context ;;
      3) menu_tier ;;
      4) menu_semantic ;;
      5) menu_gemini ;;
      6) menu_openrouter ;;
      7) menu_transcripts ;;
      8) menu_folder ;;
      9) show_all ;;
      r|R) daemon_controls ;;
      q|Q) echo -e "\n  ${GREEN}Done.${RESET}\n"; exit 0 ;;
    esac
  done
}

main
