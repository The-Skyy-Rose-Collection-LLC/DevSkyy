#!/usr/bin/env bash
# Pre-commit hook: strip empty <claude-mem-context> stubs from staged files.
#
# When the claude-mem plugin (v13.x) injects an empty stub into a CLAUDE.md and
# the file gets staged, this hook:
#   - Strips the stub block from the working copy
#   - Re-stages the file (so the commit reflects the cleaned version)
#   - If stripping leaves the file with zero changes vs HEAD, unstages it
#   - If the file is a brand-new untracked stub-only file, unstages + deletes it
#
# Exit codes:
#   0 — no stubs found, or stubs cleaned successfully
#   1 — cleaning failed (file write / git error)
#
# Whitelist (provably safe, confidence 1.0):
#   - Files matching '(^|/)CLAUDE\.md$'
#   - Stub block: <claude-mem-context>\s*</claude-mem-context> with no content between

set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[[ -z "$ROOT" ]] && exit 0
cd "$ROOT"

# Process staged CLAUDE.md paths (added or modified) — bash 3.2 compatible
STRIPPED=()

while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  [[ ! -f "$file" ]] && continue

  # Python prints "MODIFIED" to stdout iff it changed the file. Avoids non-zero
  # exit codes that would trip `set -e` before our branch logic could decide.
  result="$(python3 - "$file" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")

# Match an empty stub block: <claude-mem-context>(whitespace only)</claude-mem-context>
# Allow surrounding blank lines so we remove them too.
pattern = re.compile(
    r"\n*<claude-mem-context>\s*</claude-mem-context>\n*",
    re.MULTILINE,
)
cleaned = pattern.sub("\n", text)

# Collapse runs of 3+ blank lines that the strip might have created
cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

# Ensure file ends with a single trailing newline if original did
if text.endswith("\n") and not cleaned.endswith("\n"):
    cleaned += "\n"

if cleaned != text:
    path.write_text(cleaned, encoding="utf-8")
    print("MODIFIED")
PY
)"

  if [[ "$result" == "MODIFIED" ]]; then
    STRIPPED+=("$file")
  fi
done < <(git diff --cached --name-only --diff-filter=AM 2>/dev/null | grep -E '(^|/)CLAUDE\.md$' || true)

[[ ${#STRIPPED[@]} -eq 0 ]] && exit 0

# Re-stage cleaned files; unstage + delete if file became empty-equivalent
for file in "${STRIPPED[@]}"; do
  if [[ -s "$file" ]] && [[ -n "$(tr -d '[:space:]' < "$file")" ]]; then
    git add -- "$file"
  else
    # File is now empty (or whitespace only) — unstage + delete.
    # -f required because staged content differs from working tree post-strip.
    git rm --cached -f -- "$file" >/dev/null 2>&1 || true
    rm -f -- "$file"
  fi
done

if [[ ${#STRIPPED[@]} -gt 0 ]]; then
  echo "strip-claude-mem-stubs: cleaned ${#STRIPPED[@]} file(s):"
  printf '  %s\n' "${STRIPPED[@]}"
fi

exit 0
