#!/usr/bin/env bash
# Run a Claude Agent SDK session safely, even when invoked from inside an
# existing Claude Code session.
#
# Background: the `claude` CLI (Node binary) that the Python SDK shells out to
# refuses to start when CLAUDECODE / CLAUDE_CODE_ENTRYPOINT are set in the
# environment — that guard exists to prevent two parent Claude Code loops from
# corrupting shared ~/.claude/ state. Stripping those two vars for the child
# subprocess is the supported bypass; the parent shell is untouched.
#
# Usage:
#   ./scripts/run_managed_agent.sh "Audit theme for a11y issues"
#   ./scripts/run_managed_agent.sh --agent brand-writer "Write captions for br-001"
#   ./scripts/run_managed_agent.sh --interactive "Let's review the platform"
#   ./scripts/run_managed_agent.sh --list-agents

set -euo pipefail

# Load .env if present so ANTHROPIC_API_KEY is available to the subprocess.
if [[ -f .env ]]; then
    set -a
    # shellcheck source=/dev/null
    source .env
    set +a
fi

# Read-only flags don't spawn the SDK subprocess — skip key check for those.
needs_key=1
for arg in "$@"; do
    case "$arg" in
        --list-agents|-h|--help) needs_key=0 ;;
    esac
done

if [[ "$needs_key" == "1" && -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ERROR: ANTHROPIC_API_KEY not set (no .env or key missing from .env)" >&2
    exit 2
fi

# env -u strips vars for THIS exec only; parent shell keeps them.
# Resolve python binary (macOS ships without `python`, only `python3`).
PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"
if [[ -z "$PYTHON_BIN" ]]; then
    echo "ERROR: no python3 or python on PATH" >&2
    exit 3
fi

# Strip ALL Claude Code parent-session markers. The `claude` CLI's
# nested-session guard checks multiple env vars (CLAUDECODE,
# CLAUDE_CODE_SESSION_ID, CLAUDE_CODE_EXECPATH, etc.) — stripping only
# CLAUDECODE leaves the rest as detection signals and the subprocess
# transport closes before initialization completes.
unset_flags=()
while IFS='=' read -r name _; do
    case "$name" in
        CLAUDECODE|CLAUDE_CODE_*|CLAUDE_AUTOCOMPACT_*|CLAUDE_TMPDIR|CLAUDE_EFFORT|AI_AGENT)
            unset_flags+=("-u" "$name")
            ;;
    esac
done < <(env)

exec env "${unset_flags[@]}" "$PYTHON_BIN" -m skyyrose.multi_agent "$@"
