#!/usr/bin/env bash
# UserPromptSubmit hook — nudge to the prompt-engineering dataset when
# Claude detects prompt-engineering work in progress.
#
# Triggers (case-insensitive): prompt, system_prompt, agent definition,
# few-shot, instruction template, system message, prompt template, etc.

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"

if [[ "${PROMPT_ENG_NUDGE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

payload=$(cat)
prompt=$(read_field "$payload" '.prompt')
[[ -z "$prompt" ]] && exit 0

cache_dir=$(ensure_cache_topic "prompt-eng-cache")
ttl=$((24 * 3600))

matches=$(scan_patterns "$prompt" <<'PATTERNS'
prompt-engineering|prompt[._ -]?engineer|prompt-tuning|prompt-craft
system-prompt|system[._ -]?prompt|system message|system_prompt
agent-definition|agent[._ -]?definition|agent prompt|agentdefinition
few-shot|few[._ -]?shot|in-context example
instruction-template|instruction template|prompt template|prompt-template
llm-prompt|llm prompt|model prompt
eval-prompt|prompt eval|prompt evaluation|prompt benchmark
brand-voice|brand voice prompt|brand-voice prompt
PATTERNS
)

[[ -z "$matches" ]] && exit 0

stale=()
while IFS= read -r topic; do
    [[ -z "$topic" ]] && continue
    if ! is_fresh "$cache_dir/$topic" "$ttl"; then
        stale+=("$topic")
    fi
done <<< "$matches"

(( ${#stale[@]} == 0 )) && exit 0

csv=$(IFS=,; echo "${stale[*]}")

# Build directive with literal text — no heredoc command-substitution traps.
directive="[prompt-eng-nudge] Prompt-engineering work detected (matched: ${csv}).

DevSkyy has a canonical prompt registry at  knowledge-base/prompts/INDEX.yaml
(schema + workflow at  knowledge-base/prompts/README.md ). Before editing or
creating prompts, follow the registry workflow:

EDITING an existing prompt:
  1. Find the INDEX.yaml entry matching the file/symbol you'll edit.
     If none exists — the prompt is unregistered; create the entry first.
  2. Bump version (X.Y.0 for material rewrites, X.Y.Z for tweaks).
  3. Update last_updated to today.
  4. Make the edit.
  5. If eval/<id>.jsonl exists, run it and update the performance block.
  6. Commit prompt + INDEX.yaml together with message  prompt(<id>): <change>

ADDING a new prompt:
  1. Write the prompt in its natural source-of-truth file.
  2. Add an INDEX.yaml entry with version 0.1.0 and evaluated: null.
  3. Write 3–5 representative eval cases in eval/<id>.jsonl.
  4. Tag appropriately so future searches find it.

Reusable fragments live in  knowledge-base/prompts/templates/  (e.g.,
structured-output-schema.md). Compose from those instead of re-inventing
output-format boilerplate per prompt.

This directive fires once per 24h per topic. Silence early after reading:
  touch '${cache_dir}/<topic>'

If this prompt is conversational only (no prompt edits planned), reply
without consulting the registry."

emit_user_prompt_context "$directive"
exit 0
