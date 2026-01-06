#!/bin/bash
#
# DevSkyy Bash Command Validation Hook (PreToolUse)
# Security: Prevent dangerous bash commands from executing
#
# Validates bash commands for:
# - Command injection risks
# - Destructive operations (rm -rf, dd, mkfs)
# - Secret exposure (cat .env, echo $SECRET)
# - Privilege escalation (sudo, su)
# - Network exfiltration (curl, wget to external hosts)
#

set -euo pipefail

# Read hook input
input=$(cat)

# Extract bash command
bash_command=$(echo "$input" | jq -r '.tool_input.command // ""')

# If no command, allow (shouldn't happen)
if [ -z "$bash_command" ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  },
  "systemMessage": ""
}
EOF
  exit 0
fi

# ============================================================================
# SECURITY CHECKS
# ============================================================================

decision="allow"
reason=""

# 1. Check for destructive commands
if echo "$bash_command" | grep -qE '(rm\s+(-rf|--recursive|--force)|dd\s+if=|mkfs|fdisk|parted|format)'; then
  # Allow specific safe patterns
  if echo "$bash_command" | grep -qE '(rm.*node_modules|rm.*\.pyc|rm.*__pycache__|rm.*dist/|rm.*build/)'; then
    decision="allow"
  else
    decision="deny"
    reason="Potentially destructive command detected. Use specific file paths, avoid wildcards with rm -rf."
  fi
fi

# 2. Check for privilege escalation
if echo "$bash_command" | grep -qE '^(sudo|su\s)'; then
  decision="ask"
  reason="Command requires elevated privileges. Confirm this is necessary for the task."
fi

# 3. Check for secret exposure
if echo "$bash_command" | grep -qiE '(cat|echo|printf).*\.(env|secret|key|credential)'; then
  decision="deny"
  reason="Attempting to read sensitive files. Use environment variables instead, never expose secrets in terminal output."
fi

# 4. Check for credential exposure in echo/printf
if echo "$bash_command" | grep -qiE '(echo|printf).*\$\{?(API_KEY|SECRET|PASSWORD|TOKEN|CREDENTIALS)'; then
  decision="deny"
  reason="Attempting to echo sensitive environment variables. This would expose secrets in logs."
fi

# 5. Check for dangerous network operations
if echo "$bash_command" | grep -qE '(curl|wget|nc\s|netcat).*\|.*bash'; then
  decision="deny"
  reason="Piping network content to bash is a security risk (potential RCE). Download and inspect first."
fi

# 6. Check for git credential exposure
if echo "$bash_command" | grep -qE 'git\s+(clone|remote\s+add).*https://.*:.*@'; then
  decision="deny"
  reason="Git URL contains embedded credentials. Use git credential helpers or SSH keys instead."
fi

# 7. Check for eval with user input (command injection risk)
if echo "$bash_command" | grep -qE 'eval\s+'; then
  decision="ask"
  reason="Use of 'eval' detected. This can be dangerous with untrusted input. Confirm this is safe."
fi

# 8. Check for commands that modify .git directory
if echo "$bash_command" | grep -qE '(rm|mv|cp).*\.git/'; then
  decision="ask"
  reason="Attempting to modify .git directory. This can corrupt repository. Confirm intention."
fi

# 9. Check for package manager operations that skip verification
if echo "$bash_command" | grep -qE '(pip|npm|yarn)\s+install.*--no-verify'; then
  decision="ask"
  reason="Package installation skipping verification. This bypasses security checks. Confirm this is intended."
fi

# 10. Check for dangerous Docker operations
if echo "$bash_command" | grep -qE 'docker\s+(rm|rmi|system\s+prune).*-f'; then
  decision="ask"
  reason="Forced Docker cleanup detected. This may remove containers/images in use. Confirm this is safe."
fi

# ============================================================================
# ALLOWLIST: Common safe operations
# ============================================================================

# Always allow read-only operations
if echo "$bash_command" | grep -qE '^(ls|pwd|whoami|date|cat\s+[^\.])'; then
  decision="allow"
  reason=""
fi

# Allow git read operations
if echo "$bash_command" | grep -qE '^git\s+(status|log|diff|branch|show|remote\s+-v)'; then
  decision="allow"
  reason=""
fi

# Allow package list/audit operations
if echo "$bash_command" | grep -qE '^(pip|npm|yarn)\s+(list|audit|outdated|show)'; then
  decision="allow"
  reason=""
fi

# Allow test commands
if echo "$bash_command" | grep -qE '^(pytest|npm\s+test|npm\s+run\s+test|python\s+-m\s+pytest)'; then
  decision="allow"
  reason=""
fi

# Allow formatting commands
if echo "$bash_command" | grep -qE '^(isort|ruff|black|mypy)'; then
  decision="allow"
  reason=""
fi

# ============================================================================
# OUTPUT DECISION
# ============================================================================

if [ "$decision" = "deny" ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "deny"
  },
  "systemMessage": "🚫 **Bash Command Blocked**: $reason\n\nCommand: \`$bash_command\`"
}
EOF
  exit 0
elif [ "$decision" = "ask" ]; then
  cat <<EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "ask"
  },
  "systemMessage": "⚠️  **Bash Command Requires Confirmation**: $reason\n\nCommand: \`$bash_command\`"
}
EOF
  exit 0
else
  # Allow
  cat <<EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "allow"
  },
  "systemMessage": ""
}
EOF
  exit 0
fi
