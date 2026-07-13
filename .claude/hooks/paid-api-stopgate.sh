#!/usr/bin/env bash
# PreToolUse hook — BLOCKING gate for paid / irreversible operations.
#
# Unlike the structural prefetch hooks, this gate is genuinely punitive
# because the action is non-reversible: money spent, production site
# touched, or data destroyed. CLAUDE.md STOP-AND-SHOW protocol explicitly
# mandates explicit confirmation BEFORE such operations.
#
# Fires on Bash tool calls whose command matches known cost / production
# patterns. Emits a manifest (file path, cost estimate, action) on stderr
# and exits 2, forcing Claude to show the manifest to the user and obtain
# explicit "y" / "yes" before retrying.
#
# Bypass: prepend "STOPSHOW_ACK=1 " to the Bash command (which is what
# Claude does after user confirms).

set -euo pipefail

# Fail-closed on missing dependencies: a paid-API gate that silently no-ops
# when jq is absent is worse than no gate at all (user assumes protection
# but operations slip through). See review HIGH finding 2026-05-22.
if ! command -v jq >/dev/null 2>&1; then
    echo "[paid-api-stopgate] FATAL: jq missing from PATH — blocking all Bash calls to fail closed." >&2
    echo "[paid-api-stopgate] Install jq: brew install jq" >&2
    exit 2
fi

# shellcheck source=lib/common.sh
if [[ ! -f "$(dirname "$0")/lib/common.sh" ]]; then
    echo "[paid-api-stopgate] FATAL: lib/common.sh missing — blocking to fail closed." >&2
    exit 2
fi
source "$(dirname "$0")/lib/common.sh"

if [[ "${PAID_API_STOPGATE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

payload=$(cat)
tool_name=$(read_field "$payload" '.tool_name')
[[ "$tool_name" == "Bash" ]] || exit 0

command=$(read_field "$payload" '.tool_input.command')
[[ -z "$command" ]] && exit 0

# Acknowledgement bypass — user already confirmed in this Bash call.
# CRITICAL: must match as a LEADING-PREFIX env assignment, not a substring
# anywhere in the command. Substring match was trivially bypassed by
# embedding the token in a string literal or flag value
# (e.g., --label="STOPSHOW_ACK=1"). See review CRITICAL 2026-05-22.
# 2026-07-07: also accept the token after OTHER leading env assignments
# (e.g. `ENV_FILE=/x STOPSHOW_ACK=1 bash ...`). Only assignment-shaped
# tokens ([A-Za-z_]NAME=value) are consumed from the very start of the
# command, so a token buried in a flag or string literal still never
# reaches command position and cannot bypass.
if [[ "$command" == "STOPSHOW_ACK=1 "* ]] || [[ "$command" == "env STOPSHOW_ACK=1 "* ]]; then
    exit 0
fi
stripped="${command#env }"
while [[ "$stripped" =~ ^([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*)[[:space:]]+ ]]; do
    if [[ "${BASH_REMATCH[1]}" == "STOPSHOW_ACK=1" ]]; then
        exit 0
    fi
    stripped="${stripped:${#BASH_REMATCH[0]}}"
done

# Each rule: <regex>:::<category>:::<estimate>
# (`:::` separator chosen so regex `|` chars stay intact inside <regex>.)
RULES=(
    # ---- Python-module entry points (existing coverage) ----
    'python.*-m\s+renders\.fashn:::FASHN tryon (paid):::~$1.60 per SKU (4 models × 4 samples × $0.075 + 16 bg-remove × $0.025)'
    'python.*-m\s+renders\.generate:::FLUX / Gemini image generation:::~$0.04 per image, $0.50–$2.00 per SKU bundle'
    'python.*tripo:::Tripo3D multiview / mesh generation:::~$0.10–$0.50 per dispatch'
    'python.*meshy:::Meshy 3D mesh / texture generation:::~$0.20–$1.00 per mesh'
    'seedream_ghost_mannequin\.py.*--go:::Seedream-4 ghost-mannequin generation (paid):::~$0.06 per image, ~$2 for all 33 SKUs'
    'python.*seedream.*--go:::Seedream-4 / fal image generation (paid):::~$0.06 per image (model-dependent)'
    # ---- OpenAI gpt-image-2 render pipeline (closes coverage gap 2026-06-18) ----
    '(oai-render-run\.py\s+generate|oai_render/cli\.py.*generate):::OpenAI gpt-image-2 render generate (paid):::~$0.40 per image (EST_COST_PER_IMAGE_USD), $50 hard run cap'
    # ---- Direct-HTTP coverage (closes review HIGH finding 2026-05-22) ----
    '(curl|wget|httpx|http\s+|python.*requests).*api\.fashn\.ai:::FASHN direct HTTP (paid):::~$0.075/sample + $0.025/bg-remove'
    '(curl|wget|httpx).*api\.openai\.com/v1/images:::OpenAI DALL-E direct HTTP (paid):::~$0.04 per image (DALL-E 3 standard)'
    '(curl|wget|httpx).*generativelanguage\.googleapis\.com.*(imagen|generateImage):::Gemini Imagen direct HTTP (paid):::~$0.04 per image'
    '(curl|wget|httpx).*fal\.(run|ai):::fal.ai direct HTTP (paid):::~$0.05 per call (model-dependent)'
    '(curl|wget|httpx).*api\.together\.xyz.*images:::Together.ai image direct HTTP (paid):::~$0.005–$0.05 per image'
    '(curl|wget|httpx).*api\.replicate\.com:::Replicate direct HTTP (paid):::variable per model, $0.001–$0.50 per prediction'
    '(curl|wget|httpx).*(platform\.tripo3d|api\.tripo3d):::Tripo3D direct HTTP (paid):::~$0.10–$0.50 per dispatch'
    '(curl|wget|httpx).*api\.meshy\.ai:::Meshy direct HTTP (paid):::~$0.20–$1.00 per mesh'
    # ---- Production deploys (closes review HIGH finding 2026-05-22) ----
    # 2026-07-07: deploy scripts gate on EXECUTION context only — an interpreter
    # invocation or command-position path — so read-only mentions (head/grep/cat
    # of the script) no longer false-positive. See bug-177.
    '((bash|sh|zsh|source)[[:space:]]+[^|;&]*deploy-(theme|mu-plugin)\.sh|(^|[;&|][[:space:]]*)[^[:space:]|;&]*/deploy-(theme|mu-plugin)\.sh([[:space:]]|$)):::WordPress deploy to skyyrose.co (production):::none direct, but production site touched'
    'run_managed_agent\.sh.*--budget:::Managed agent run with budget (paid):::budgeted LLM spend'
    'npm\s+run\s+deploy(:?\s|$):::npm run deploy → WordPress or Vercel production:::production site touched (skyyrose.co or devskyy.app)'
    '(vercel\s+deploy|vercel\s+--prod):::Vercel production deployment (devskyy.app):::none direct, but production site touched'
    'wp\s+(media\s+import|post\s+(create|update|delete)):::WordPress.com REST write (production):::production data mutation'
    # ---- Destructive shell ops ----
    '(rm\s+-rf\s+/\s*$|rm\s+-rf\s+/\s+|rm\s+-rf\s+~|rm\s+-rf\s+\$\{?HOME\}?|rm\s+(-[a-z]*r[a-z]*f[a-z]*|-[a-z]*f[a-z]*r[a-z]*|--recursive.*--force|--force.*--recursive)\s+/):::Recursive delete of system / home directory:::IRREVERSIBLE data loss'
    'git\s+push\s+(--force|-f|--force-with-lease):::Force push:::destructive: rewrites remote history'
    'git\s+reset\s+--hard\s+(origin|HEAD~):::Hard reset:::destructive: discards local commits'
    '(npx\s+claude-mem.*delete|claude-mem\s+delete):::claude-mem deletion:::memory loss (semi-irreversible)'
)

for rule in "${RULES[@]}"; do
    pattern="${rule%%:::*}"
    rest="${rule#*:::}"
    category="${rest%%:::*}"
    estimate="${rest#*:::}"
    if printf '%s' "$command" | grep -qE -- "$pattern"; then
        cat >&2 <<EOF
[paid-api-stopgate] BLOCKED — STOP-AND-SHOW required per DevSkyy CLAUDE.md.

  Category:  $category
  Estimate:  $estimate
  Command:   $command

This operation costs money, touches production, or is irreversible. Per the
STOP-AND-SHOW protocol you MUST:

  1. Print the exact manifest above to the user.
  2. Wait for explicit "y" / "yes" confirmation.
  3. Re-issue the Bash call with STOPSHOW_ACK=1 prepended:
       STOPSHOW_ACK=1 $command

Do NOT run the command without confirmation. Apologizing after spending
money or breaking the site is not acceptable. The bypass token signals
that the user has explicitly approved THIS specific invocation.
EOF
        exit 2
    fi
done

exit 0
