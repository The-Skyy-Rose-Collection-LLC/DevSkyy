#!/usr/bin/env bash
# OpenWolf ↔ claude-mem sync (SessionStart)
# Queries ~/.claude-mem/claude-mem.db for the most recent observations on this project
# and writes a digest to .wolf/claude-mem-digest.md so OpenWolf's cerebrum/memory/anatomy
# can cross-reference observation IDs. Non-fatal on any failure.
set -u

DB="${HOME}/.claude-mem/claude-mem.db"
PROJECT="${CLAUDE_MEM_PROJECT_NAME:-DevSkyy}"
WOLF_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}/.wolf"
OUT="${WOLF_DIR}/claude-mem-digest.md"
LIMIT="${CLAUDE_MEM_DIGEST_LIMIT:-25}"

[[ -r "$DB" ]] || exit 0
command -v sqlite3 >/dev/null 2>&1 || exit 0
[[ -d "$WOLF_DIR" ]] || exit 0

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
sql="${tmpdir}/q.sql"
rows="${tmpdir}/rows.tsv"

cat > "$sql" <<SQL
.mode tabs
.headers off
SELECT
  id,
  COALESCE(type, ''),
  strftime('%Y-%m-%d %H:%M', datetime(created_at_epoch/1000, 'unixepoch', 'localtime')),
  REPLACE(REPLACE(COALESCE(title, ''),    char(10), ' '), char(9), ' '),
  REPLACE(REPLACE(COALESCE(subtitle, ''), char(10), ' '), char(9), ' ')
FROM observations
WHERE project = '${PROJECT}'
ORDER BY created_at_epoch DESC
LIMIT ${LIMIT};
SQL

sqlite3 "$DB" < "$sql" > "$rows" 2>/dev/null || exit 0

generated="$(date '+%Y-%m-%d %H:%M:%S %Z')"
total="$(sqlite3 "$DB" "SELECT COUNT(*) FROM observations WHERE project = '${PROJECT}';" 2>/dev/null || echo '?')"

{
  echo "# claude-mem Digest — ${PROJECT}"
  echo ""
  echo "> Auto-synced at SessionStart from \`~/.claude-mem/claude-mem.db\`."
  echo "> Refresh manually: \`bash .wolf/hooks/claude-mem-sync.sh\`"
  echo ""
  echo "- **Generated**: ${generated}"
  echo "- **Project total observations**: ${total}"
  echo "- **Showing**: last ${LIMIT}"
  echo ""
  echo "| ID | Type | When | Title |"
  echo "|----|------|------|-------|"
  awk -F'\t' '{
    gsub(/\|/, "/", $4)
    gsub(/\|/, "/", $5)
    printf "| %s | %s | %s | %s |\n", $1, $2, $3, $4
  }' "$rows"
  echo ""
  echo "---"
  echo ""
  echo "## Cross-reference convention"
  echo ""
  echo "When writing to \`.wolf/cerebrum.md\` or \`.wolf/memory.md\`, cite relevant observation IDs from above using the \`[cmem #NNN]\` suffix. Example:"
  echo ""
  echo "\`\`\`"
  echo "| 13:19 | enqueue homepage-v7.css on front-page slug | inc/enqueue.php | php -l clean | ~90 | [cmem #503] |"
  echo "\`\`\`"
  echo ""
  echo "Fetch full observation details via \`get_observations([NNN])\` MCP tool, or search via \`mem-search\` skill."
} > "${OUT}.tmp" && mv "${OUT}.tmp" "${OUT}"

exit 0
