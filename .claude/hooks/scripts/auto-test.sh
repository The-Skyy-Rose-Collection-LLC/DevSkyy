#!/bin/bash
#
# Auto-Test Hook (PostToolUse: Write|Edit)
# =========================================
#
# Automatically runs tests after code changes to production modules.
# Finds corresponding test file and executes pytest.
#
# Exit Codes:
#   0 - Success (tests passed or skipped)
#   Other - Non-blocking error
#
# Output:
#   - suppressOutput: true (if no tests or not applicable)
#   - systemMessage: "✅ X tests passed" or "❌ X tests failed"
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

# Skip if file is already a test file
if [[ "$file_path" =~ ^tests/ ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip non-production files (scripts, imagery, examples)
if [[ "$file_path" =~ ^(scripts/|imagery/|examples/) ]]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Extract module name from file path
# e.g., "agents/commerce_agent.py" → "commerce_agent"
# e.g., "llm/router.py" → "router"
module_name=$(basename "$file_path" .py)

# Construct test file path
# Pattern: tests/test_{module_name}.py
test_file="tests/test_${module_name}.py"

# Check if test file exists
if [ ! -f "$test_file" ]; then
  # No test file found - warn user
  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"⚠️  No tests found for $file_path (expected: $test_file)\"
  }"
  exit 0
fi

# Run pytest on the specific test file
if ! command -v pytest >/dev/null 2>&1; then
  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"⚠️  pytest not installed - cannot run tests\"
  }"
  exit 0
fi

# Execute pytest with minimal output
test_output=$(pytest "$test_file" -v --tb=short --maxfail=5 2>&1 || true)

# Parse results
passed=$(echo "$test_output" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' || echo "0")
failed=$(echo "$test_output" | grep -oE '[0-9]+ failed' | grep -oE '[0-9]+' || echo "0")
errors=$(echo "$test_output" | grep -oE '[0-9]+ error' | grep -oE '[0-9]+' || echo "0")

# Calculate total issues
total_issues=$((failed + errors))

# Generate output based on results
if [ "$total_issues" -eq 0 ] && [ "$passed" -gt 0 ]; then
  # All tests passed
  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"✅ Tests passed: $passed tests for $file_path\"
  }"
elif [ "$total_issues" -gt 0 ]; then
  # Some tests failed
  # Extract failure details (first 3 failures)
  failure_summary=$(echo "$test_output" | grep -A 2 "FAILED" | head -9 || echo "")

  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"❌ Tests failed: $passed passed, $failed failed, $errors errors for $file_path\\n\\nFailure preview:\\n$failure_summary\\n\\nRun: pytest $test_file -v for details\"
  }"
else
  # No tests ran (possibly all skipped)
  echo "{
    \"continue\": true,
    \"suppressOutput\": false,
    \"systemMessage\": \"⚠️  No tests executed for $file_path (check test file: $test_file)\"
  }"
fi

exit 0
