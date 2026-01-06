#!/bin/bash
#
# DevSkyy Audit Logging Hook (PostToolUse)
# GDPR Compliance: Log all tool executions for audit trail
#
# Retention: 30 days (configurable via AUDIT_RETENTION_DAYS)
# Log Format: JSON Lines (JSONL) for easy parsing
# PII Protection: Never log credentials, user data, or sensitive inputs
#

set -euo pipefail

# Configuration
AUDIT_LOG_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.claude/hooks/logs"
AUDIT_LOG_FILE="${AUDIT_LOG_DIR}/tool-audit.jsonl"
AUDIT_RETENTION_DAYS="${AUDIT_RETENTION_DAYS:-30}"

# Ensure log directory exists
mkdir -p "$AUDIT_LOG_DIR"

# Read hook input
input=$(cat)

# Extract fields from input (with fallbacks)
session_id=$(echo "$input" | jq -r '.session_id // "unknown"')
tool_name=$(echo "$input" | jq -r '.tool_name // "unknown"')
cwd=$(echo "$input" | jq -r '.cwd // "unknown"')
permission_mode=$(echo "$input" | jq -r '.permission_mode // "unknown"')

# Generate correlation ID (unique per tool execution)
correlation_id="${session_id}_$(date +%s)_$$"

# Get timestamp in ISO 8601 format
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Extract sanitized tool input (remove sensitive data)
tool_input_raw=$(echo "$input" | jq -c '.tool_input // {}')

# Sanitize tool input - remove potential credentials
tool_input_sanitized=$(echo "$tool_input_raw" | jq 'walk(
  if type == "string" then
    if test("(?i)(password|secret|token|key|credential)"; "") then
      "[REDACTED]"
    else
      .
    end
  else
    .
  end
)')

# Check if tool succeeded (exit code in tool_result)
tool_result=$(echo "$input" | jq -r '.tool_result // "{}"')
success="true"
error_message="null"

# Try to determine if tool failed
if echo "$tool_result" | jq -e '.error' > /dev/null 2>&1; then
  success="false"
  error_message=$(echo "$tool_result" | jq -r '.error // "unknown error"')
fi

# Build audit log entry
audit_entry=$(cat <<EOF
{
  "timestamp": "$timestamp",
  "correlation_id": "$correlation_id",
  "session_id": "$session_id",
  "tool_name": "$tool_name",
  "tool_input": $tool_input_sanitized,
  "working_directory": "$cwd",
  "permission_mode": "$permission_mode",
  "success": $success,
  "error_message": $error_message,
  "audit_version": "1.0"
}
EOF
)

# Validate JSON before writing
if echo "$audit_entry" | jq . > /dev/null 2>&1; then
  # Append to audit log
  echo "$audit_entry" >> "$AUDIT_LOG_FILE"
else
  # JSON validation failed, log error
  echo "{\"error\": \"Failed to create valid audit entry\", \"timestamp\": \"$timestamp\"}" >> "$AUDIT_LOG_FILE"
fi

# ============================================================================
# LOG ROTATION: Delete entries older than retention period
# ============================================================================
if [ -f "$AUDIT_LOG_FILE" ]; then
  # Calculate cutoff timestamp (retention_days ago)
  cutoff_date=$(date -u -v-${AUDIT_RETENTION_DAYS}d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || \
                date -u -d "$AUDIT_RETENTION_DAYS days ago" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || \
                echo "1970-01-01T00:00:00Z")

  # Create temporary file for filtered logs
  temp_log="${AUDIT_LOG_FILE}.tmp"

  # Keep only entries newer than cutoff
  if command -v jq > /dev/null 2>&1; then
    jq -c "select(.timestamp > \"$cutoff_date\")" "$AUDIT_LOG_FILE" > "$temp_log" 2>/dev/null || touch "$temp_log"
    mv "$temp_log" "$AUDIT_LOG_FILE"
  fi
fi

# ============================================================================
# GDPR COMPLIANCE: Generate daily summary
# ============================================================================
# Check if it's a new day (create summary at midnight)
summary_file="${AUDIT_LOG_DIR}/daily-summary-$(date -u +%Y-%m-%d).json"
if [ ! -f "$summary_file" ]; then
  # Count tool executions by type
  if [ -f "$AUDIT_LOG_FILE" ]; then
    today=$(date -u +%Y-%m-%d)

    # Generate summary
    jq -s "
      map(select(.timestamp | startswith(\"$today\"))) |
      {
        date: \"$today\",
        total_executions: length,
        tools_used: map(.tool_name) | unique,
        success_rate: (map(select(.success == true)) | length) / (length | if . == 0 then 1 else . end),
        generated_at: \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"
      }
    " "$AUDIT_LOG_FILE" > "$summary_file" 2>/dev/null || true
  fi
fi

# ============================================================================
# OUTPUT: Silent success (don't clutter transcript)
# ============================================================================
cat <<EOF
{
  "continue": true,
  "suppressOutput": true,
  "systemMessage": ""
}
EOF

exit 0
