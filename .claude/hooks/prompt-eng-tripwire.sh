#!/usr/bin/env bash
# PreToolUse tripwire — fires when Claude is about to Edit/Write/MultiEdit
# a file that contains a registered prompt OR introduces prompt-engineering
# content. Pre-emits a pointer to INDEX.yaml so the registry workflow is
# followed (bump version, update last_updated, etc.).
#
# Unlike paid-api-stopgate, this is NON-BLOCKING — it emits a stderr
# advisory (which Claude sees in tool result) but always exits 0. Real
# enforcement is at code-review time when version drift becomes obvious.

set -euo pipefail

# shellcheck source=lib/common.sh
source "$(dirname "$0")/lib/common.sh"

if [[ "${PROMPT_ENG_TRIPWIRE_DISABLE:-0}" == "1" ]]; then
    exit 0
fi

payload=$(cat)
tool_name=$(read_field "$payload" '.tool_name')

case "$tool_name" in
    Write|Edit|MultiEdit) ;;
    *) exit 0 ;;
esac

file_path=$(read_field "$payload" '.tool_input.file_path')
[[ -z "$file_path" ]] && exit 0

# File-path patterns that signal prompt engineering surface
path_is_prompt=0
case "$file_path" in
    */prompts/*|*_prompt*.py|*system_prompt*|*/agents.py|*/orchestrator.py)
        path_is_prompt=1 ;;
esac

# Content patterns (only check on Edit/MultiEdit/Write where we have content)
content_is_prompt=0
new_str=$(read_field "$payload" '.tool_input.new_string')
[[ -z "$new_str" ]] && new_str=$(read_field "$payload" '.tool_input.content')
if printf '%s' "$new_str" | grep -qE '(system_prompt\s*=|SYSTEM_PROMPT\s*=|AgentDefinition\(|prompt\s*=\s*['\''"]|"""[[:space:]]*You are)'; then
    content_is_prompt=1
fi

if (( path_is_prompt == 0 && content_is_prompt == 0 )); then
    exit 0
fi

# Per-session sentinel: emit once per session, not every edit
sentinel=$(session_sentinel "prompt-eng-advised")
if [[ -f "$sentinel" ]]; then
    exit 0
fi
touch "$sentinel"

cat >&2 <<EOF
[prompt-eng-tripwire] ADVISORY: this edit touches a prompt-engineering
surface ($file_path).

DevSkyy prompt registry: \`knowledge-base/prompts/INDEX.yaml\`
(schema + workflow: \`knowledge-base/prompts/README.md\`)

Before completing the edit:
  - Find/create the INDEX entry for this prompt.
  - Bump \`version\` (X.Y.0 material / X.Y.Z tweak).
  - Update \`last_updated\` to today.
  - Commit prompt + INDEX.yaml together: \`prompt(<id>): <change>\`.

Reusable fragments: \`knowledge-base/prompts/templates/\` (compose, don't
re-invent output-format boilerplate).

This advisory fires once per session. (Tool call NOT blocked.)
EOF

exit 0
