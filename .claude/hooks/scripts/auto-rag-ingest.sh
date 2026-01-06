#!/bin/bash
#
# Auto-RAG-Ingest Hook (PostToolUse: Write)
# ==========================================
#
# Automatically ingests documentation files into RAG knowledge base.
# Triggered after Write operations on .md, .txt files in docs/ or README.
#
# Exit Codes:
#   0 - Success (ingested or skipped)
#   Other - Non-blocking error
#
# Output:
#   - suppressOutput: true (if not a doc file)
#   - systemMessage: "📚 Ingested {file} into RAG"
#   - continue: true (always non-blocking)

set -euo pipefail

# Read hook input from stdin
input=$(cat)

# Extract tool name and file path
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
file_path=$(echo "$input" | jq -r '.tool_input.file_path // ""')

# Only trigger on Write (not Edit, to avoid re-ingesting on every change)
if [ "$tool_name" != "Write" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if no file path
if [ -z "$file_path" ] || [ "$file_path" = "null" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Check if this is a documentation file
is_doc_file=false

# Check file extension
if [[ "$file_path" =~ \.(md|txt)$ ]]; then
  # Check if in docs/ directory or is README/CLAUDE.md
  if [[ "$file_path" =~ ^docs/ ]] || [[ "$file_path" =~ README\.md$ ]] || [[ "$file_path" =~ CLAUDE\.md$ ]]; then
    is_doc_file=true
  fi
fi

# Skip if not a documentation file
if [ "$is_doc_file" = "false" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Skip if file doesn't exist
if [ ! -f "$file_path" ]; then
  echo '{"continue": true, "suppressOutput": true}'
  exit 0
fi

# Create log directory if needed
mkdir -p .claude/hooks/logs

# Log ingestion event
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
log_file=".claude/hooks/logs/rag-ingestion.jsonl"

# Get file metadata
file_size=$(wc -c < "$file_path" | tr -d ' ')
line_count=$(wc -l < "$file_path" | tr -d ' ')

# Log the ingestion attempt
cat << EOF >> "$log_file"
{"timestamp": "$timestamp", "action": "auto_ingest", "file": "$file_path", "size_bytes": $file_size, "lines": $line_count, "status": "queued", "trigger": "PostToolUse:Write"}
EOF

# Note: Actual RAG ingestion would happen here via MCP tool
# For now, we just log the event since the MCP server may not be running

# Output success message
echo "{
  \"continue\": true,
  \"suppressOutput\": false,
  \"systemMessage\": \"📚 Auto-ingest queued: $file_path ($line_count lines) → RAG knowledge base\\n\\nNote: Actual ingestion requires RAG MCP server. Run /rag-ingest to verify.\"
}"

exit 0
