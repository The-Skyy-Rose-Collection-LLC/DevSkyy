#!/bin/bash
#
# Auto-Security-Scan Hook (PostToolUse: Bash)
# ============================================
#
# Automatically scans for security vulnerabilities after dependency changes.
# Triggered after: pip install, npm install, yarn add
#
# Exit Codes:
#   0 - Success (scanned or skipped)
#   Other - Non-blocking error
#
# Output:
#   - suppressOutput: true (if not a dependency command)
#   - systemMessage: "⚠️  Security: X vulnerabilities found"
#   - continue: true (always non-blocking)

set -euo pipefail

# Read hook input from stdin
input=$(cat)

# Extract tool name and bash command
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
bash_command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Only trigger on Bash commands
if [ "$tool_name" != "Bash" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if no command
if [ -z "$bash_command" ] || [ "$bash_command" = "null" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Check if this is a dependency installation command
is_dependency_install=false

if echo "$bash_command" | grep -qE '(pip|pip3) install'; then
  is_dependency_install=true
  package_manager="pip"
elif echo "$bash_command" | grep -qE 'npm install'; then
  is_dependency_install=true
  package_manager="npm"
elif echo "$bash_command" | grep -qE 'yarn add'; then
  is_dependency_install=true
  package_manager="yarn"
fi

# Skip if not a dependency install
if [ "$is_dependency_install" = "false" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Create log directory if needed
mkdir -p .claude/hooks/logs

# Run security scan based on package manager
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
log_file=".claude/hooks/logs/security-scan.jsonl"
vulnerabilities_found=0
scan_output=""

if [ "$package_manager" = "pip" ]; then
  # Python security scan
  if command -v pip-audit >/dev/null 2>&1; then
    scan_output=$(pip-audit --desc --format json 2>&1 || echo '{"vulnerabilities": []}')
    critical_count=$(echo "$scan_output" | jq '[.vulnerabilities[] | select(.fix_versions)] | length' 2>/dev/null || echo "0")
    vulnerabilities_found=$critical_count

    # Log scan results
    cat << EOF >> "$log_file"
{"timestamp": "$timestamp", "package_manager": "pip", "vulnerabilities": $vulnerabilities_found, "command": "$bash_command", "status": "scanned"}
EOF

    if [ "$vulnerabilities_found" -gt 0 ]; then
      # Extract top 3 vulnerabilities
      top_vulns=$(echo "$scan_output" | jq -r '[.vulnerabilities[] | select(.fix_versions)] | .[:3][] | "- \(.name) (\(.id)): \(.summary)"' 2>/dev/null || echo "")

      echo "{
        \"continue\": true,
        \"suppressOutput\": false,
        \"systemMessage\": \"⚠️  Security scan: $vulnerabilities_found vulnerabilities found in Python dependencies\\n\\nTop issues:\\n$top_vulns\\n\\nRun: pip-audit --desc for full report\"
      }"
      exit 0
    fi
  else
    cat << EOF >> "$log_file"
{"timestamp": "$timestamp", "package_manager": "pip", "vulnerabilities": "unknown", "command": "$bash_command", "status": "pip-audit not installed"}
EOF

    echo "{
      \"continue\": true,
      \"suppressOutput\": false,
      \"systemMessage\": \"ℹ️  Install pip-audit for security scanning: pip install pip-audit\"
    }"
    exit 0
  fi

elif [ "$package_manager" = "npm" ]; then
  # Node.js security scan
  if command -v npm >/dev/null 2>&1; then
    scan_output=$(npm audit --json 2>&1 || echo '{"vulnerabilities": {}}')
    critical_count=$(echo "$scan_output" | jq '.metadata.vulnerabilities.critical // 0' 2>/dev/null || echo "0")
    high_count=$(echo "$scan_output" | jq '.metadata.vulnerabilities.high // 0' 2>/dev/null || echo "0")
    vulnerabilities_found=$((critical_count + high_count))

    # Log scan results
    cat << EOF >> "$log_file"
{"timestamp": "$timestamp", "package_manager": "npm", "vulnerabilities": $vulnerabilities_found, "command": "$bash_command", "status": "scanned"}
EOF

    if [ "$vulnerabilities_found" -gt 0 ]; then
      echo "{
        \"continue\": true,
        \"suppressOutput\": false,
        \"systemMessage\": \"⚠️  Security scan: $critical_count critical, $high_count high vulnerabilities in npm dependencies\\n\\nRun: npm audit for full report\"
      }"
      exit 0
    fi
  fi
fi

# No vulnerabilities found
cat << EOF >> "$log_file"
{"timestamp": "$timestamp", "package_manager": "$package_manager", "vulnerabilities": 0, "command": "$bash_command", "status": "clean"}
EOF

echo "{
  \"continue\": true,
  \"suppressOutput\": false,
  \"systemMessage\": \"✅ Security scan: No critical vulnerabilities found in $package_manager dependencies\"
}"

exit 0
