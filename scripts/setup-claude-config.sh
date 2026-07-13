#!/usr/bin/env bash
#
# setup-claude-config.sh — per-clone bootstrap for DevSkyy Claude Code config.
#
# WHY: .claude/settings.json is gitignored (it carries keys/preferences), and its
# SessionStart hooks reference ABSOLUTE .wolf/hooks/ paths. A fresh clone therefore
# has no settings.json, and a renamed/moved clone (DevSkyy-slim, DevSkyy-embeddings-
# reframe, a worktree) inherits stale absolute paths. This script wires the canonical
# OpenWolf SessionStart hooks into THIS clone's own root, makes the hook scripts
# executable, and seeds .env files from their templates — idempotently and
# non-destructively.
#
# SAFE TO RE-RUN. It:
#   - backs up .claude/settings.json before any change (timestamped),
#   - matches hooks by basename so re-runs correct paths instead of duplicating,
#   - never overwrites an existing .env (only creates missing ones from *.example),
#   - never prints secret values.
#
# Usage:  ./setup-claude-config.sh [--dry-run]
#
set -euo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

# --- pretty logging ----------------------------------------------------------
if [[ -t 1 ]]; then
  BOLD=$'\033[1m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RED=$'\033[31m'; DIM=$'\033[2m'; RESET=$'\033[0m'
else
  BOLD=''; GREEN=''; YELLOW=''; RED=''; DIM=''; RESET=''
fi
log()  { printf '%s\n' "${DIM}·${RESET} $*"; }
ok()   { printf '%s\n' "${GREEN}✓${RESET} $*"; }
warn() { printf '%s\n' "${YELLOW}!${RESET} $*" >&2; }
die()  { printf '%s\n' "${RED}✗ $*${RESET}" >&2; exit 1; }
step() { printf '\n%s\n' "${BOLD}$*${RESET}"; }

# --- resolve clone root ------------------------------------------------------
# Prefer git toplevel; fall back to the directory this script lives in.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd -P)"
if REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null)"; then
  :
else
  REPO_ROOT="$SCRIPT_DIR"
fi
cd "$REPO_ROOT"

# --- validate this is a DevSkyy clone ----------------------------------------
step "Validating clone at ${BOLD}${REPO_ROOT}${RESET}"
[[ -f CLAUDE.md ]]   || die "no CLAUDE.md here — not a DevSkyy repo root."
[[ -d .wolf ]]       || die "no .wolf/ here — not a DevSkyy (OpenWolf) clone."
command -v python3 >/dev/null 2>&1 || die "python3 is required."
ok "DevSkyy clone confirmed (python3 $(python3 -c 'import sys;print(".".join(map(str,sys.version_info[:3])))'))"
[[ $DRY_RUN -eq 1 ]] && warn "DRY-RUN: no files will be written."

# --- 1. make .wolf hook scripts executable -----------------------------------
step "1. Hook scripts executable"
HOOK_DIR="$REPO_ROOT/.wolf/hooks"
made_exec=0
if [[ -d "$HOOK_DIR" ]]; then
  while IFS= read -r -d '' f; do
    if [[ ! -x "$f" ]]; then
      if [[ $DRY_RUN -eq 0 ]]; then chmod +x "$f"; fi
      log "chmod +x $(basename "$f")"
      made_exec=$((made_exec+1))
    fi
  done < <(find "$HOOK_DIR" -maxdepth 1 -type f \( -name '*.sh' -o -name '*.py' \) -print0)
  ok "hook scripts ready (${made_exec} newly marked executable)"
else
  warn "no .wolf/hooks/ directory — skipping."
fi

# --- 2. wire SessionStart hooks into .claude/settings.json -------------------
step "2. Wire OpenWolf SessionStart hooks into .claude/settings.json"
mkdir -p "$REPO_ROOT/.claude"
SETTINGS="$REPO_ROOT/.claude/settings.json"

# canonical SessionStart hook scripts (run on every session start, matcher '*')
CANON_HOOKS=("memory-audit.sh" "claude-mem-sync.sh")

# back up existing settings before mutation (single rolling backup — no litter)
if [[ -f "$SETTINGS" && $DRY_RUN -eq 0 ]]; then
  cp "$SETTINGS" "${SETTINGS}.bak"
  log "backed up settings.json → settings.json.bak"
fi

REPO_ROOT="$REPO_ROOT" \
SETTINGS="$SETTINGS" \
DRY_RUN="$DRY_RUN" \
CANON_HOOKS="${CANON_HOOKS[*]}" \
python3 <<'PY'
import json, os, sys

repo     = os.environ["REPO_ROOT"]
path     = os.environ["SETTINGS"]
dry      = os.environ["DRY_RUN"] == "1"
canon    = os.environ["CANON_HOOKS"].split()

# load existing settings (tolerate missing / empty / comment-free JSON)
data = {}
if os.path.exists(path) and os.path.getsize(path) > 0:
    try:
        with open(path) as fh:
            data = json.load(fh)
    except json.JSONDecodeError as e:
        print(f"  settings.json is not valid JSON ({e}); refusing to overwrite.", file=sys.stderr)
        sys.exit(3)
if not isinstance(data, dict):
    print("  settings.json root is not an object; refusing to overwrite.", file=sys.stderr)
    sys.exit(3)

hooks = data.setdefault("hooks", {})
ss = hooks.setdefault("SessionStart", [])

# find (or create) the wildcard matcher block
block = None
for b in ss:
    if isinstance(b, dict) and b.get("matcher", "*") in ("*", ""):
        block = b
        break
if block is None:
    block = {"matcher": "*", "hooks": []}
    ss.append(block)
block.setdefault("hooks", [])

def desired_command(name: str) -> str:
    return f"bash {repo}/.wolf/hooks/{name}"

def hook_basename(cmd: str) -> str:
    # match '.wolf/hooks/<name>' regardless of absolute prefix
    marker = "/.wolf/hooks/"
    return cmd.split(marker, 1)[1].split()[0] if marker in cmd else ""

changed = False
existing = block["hooks"]
for name in canon:
    want = desired_command(name)
    match = next((h for h in existing
                  if isinstance(h, dict) and hook_basename(h.get("command", "")) == name), None)
    if match is None:
        existing.append({"type": "command", "command": want, "timeout": 5})
        print(f"  + added SessionStart hook: {name}")
        changed = True
    elif match.get("command") != want:
        old = match.get("command")
        match["command"] = want                       # correct stale absolute path
        match.setdefault("type", "command")
        match.setdefault("timeout", 5)
        print(f"  ~ repointed {name}: {old}  ->  {want}")
        changed = True

if not changed:
    print("  settings.json already correct — no change.")
elif dry:
    print("  (dry-run) would write the above changes.")
else:
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print(f"  wrote {path}")
PY
ok "SessionStart hooks reconciled"

# --- 3. seed .env files from templates (never overwrite) ---------------------
step "3. Seed .env files from *.example (missing only)"
seeded=0
while IFS= read -r -d '' tmpl; do
  target="${tmpl%.example}"
  base_t="$(basename "$target")"
  if [[ -f "$target" ]]; then
    log "$base_t exists — left untouched"
  else
    if [[ $DRY_RUN -eq 0 ]]; then cp "$tmpl" "$target"; fi
    ok "created $base_t from $(basename "$tmpl") ${YELLOW}(fill in secrets)${RESET}"
    seeded=$((seeded+1))
  fi
done < <(find "$REPO_ROOT" -maxdepth 1 -type f -name '.env*.example' -print0)
[[ $seeded -eq 0 ]] && log "no new .env files needed"

# --- 4. sanity checks --------------------------------------------------------
step "4. Sanity checks"
[[ -f "$REPO_ROOT/.mcp.json" ]] && ok ".mcp.json present" || warn ".mcp.json missing — MCP servers won't load."
if python3 -c "import json,sys; json.load(open('$SETTINGS'))" 2>/dev/null; then
  ok "settings.json is valid JSON"
else
  warn "settings.json did not parse — review it."
fi

# --- done --------------------------------------------------------------------
step "${GREEN}Done.${RESET}"
cat <<EOF
${DIM}Next:${RESET}
  1. Fill any newly created .env / .env.wordpress with real values.
  2. Restart Claude Code so SessionStart hooks + MCP servers reload.
  3. Verify hook wiring:  bash .wolf/hooks/claude-mem-sync.sh && ls -la .wolf/claude-mem-digest.md
EOF
