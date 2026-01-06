#!/bin/bash
#
# Auto-Format Hook (PostToolUse: Write|Edit)
# ==========================================
#
# Automatically formats Python files after Write/Edit operations.
# Runs isort (imports) → ruff (linting) → black (formatting).
#
# Exit Codes:
#   0 - Success (formatted or skipped)
#   Other - Non-blocking error
#
# Output:
#   - suppressOutput: true (if no changes)
#   - systemMessage: "Formatted {file}: X changes" (if changes made)
#   - continue: true (always non-blocking)

set -euo pipefail

# Read hook input from stdin
input=$(cat)

# Extract tool name and file path
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Skip if not Write or Edit
if [[ ! "$tool_name" =~ ^(Write|Edit)$ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if no file path
if [ -z "$file_path" ] || [ "$file_path" = "null" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if not a Python file
if [[ ! "$file_path" =~ \.py$ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if file doesn't exist (e.g., deleted)
if [ ! -f "$file_path" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip non-production files (tests, scripts, imagery)
if [[ "$file_path" =~ ^(tests/|scripts/|imagery/) ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Perform formatting
changes_made=0
format_summary=""

# 1. Import sorting (isort)
if command -v isort >/dev/null 2>&1; then
  isort_output=$(isort "$file_path" --diff 2>&1 || true)
  if [ -n "$isort_output" ] && echo "$isort_output" | grep -q "Fixing"; then
    isort "$file_path" 2>&1 >/dev/null || true
    changes_made=1
    format_summary="${format_summary}isort "
  fi
fi

# 2. Linting fixes (ruff)
if command -v ruff >/dev/null 2>&1; then
  ruff_output=$(ruff check --fix "$file_path" 2>&1 || true)
  if echo "$ruff_output" | grep -q "Fixed"; then
    changes_made=1
    format_summary="${format_summary}ruff "
  fi
fi

# 3. Code formatting (black)
if command -v black >/dev/null 2>&1; then
  black_output=$(black "$file_path" 2>&1 || true)
  if echo "$black_output" | grep -q "reformatted"; then
    changes_made=1
    format_summary="${format_summary}black "
  fi
fi

# Generate output
if [ "$changes_made" -eq 1 ]; then
  # Changes were made - notify Claude
  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"✨ Auto-formatted: $file_path ($format_summary)\"
  }"
else
  # No changes needed - silent success
  echo '{"continue": true, "suppressOutput": true}'
fi

exit 0
