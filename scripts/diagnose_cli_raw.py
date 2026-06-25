"""Build the exact CLI command the SDK would use and run it via subprocess
with stderr captured directly. Bypasses the SDK's silent stderr handler.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# Strip Claude Code env markers
for var in list(os.environ):
    if var.startswith(("CLAUDE_CODE_", "CLAUDE_AUTOCOMPACT_")) or var in (
        "CLAUDECODE",
        "CLAUDE_TMPDIR",
        "CLAUDE_EFFORT",
        "AI_AGENT",
    ):
        os.environ.pop(var, None)

# Re-add the SDK's expected marker (SDK does this for the subprocess)
os.environ["CLAUDE_CODE_ENTRYPOINT"] = "sdk-py"

mcp_config = {
    "mcpServers": {
        "diag": {
            "type": "sdk",
            "name": "diag",
        }
    }
}

cmd = [
    "claude",
    "--output-format",
    "stream-json",
    "--verbose",
    "--system-prompt",
    "Reply with one word.",
    "--max-turns",
    "1",
    "--max-budget-usd",
    "0.05",
    "--model",
    "sonnet",
    "--permission-mode",
    "default",
    "--mcp-config",
    json.dumps(mcp_config),
    "--setting-sources",
    "",
]

print("[CMD]", " ".join(repr(c) for c in cmd), file=sys.stderr)
print("[ENV] CLAUDE_*:", {k: v for k, v in os.environ.items() if "CLAUDE" in k}, file=sys.stderr)

# Send a minimal stream-json init request to stdin to trigger handshake
init_input = (
    json.dumps(
        {
            "type": "user",
            "message": {"role": "user", "content": [{"type": "text", "text": "ping"}]},
        }
    )
    + "\n"
)

result = subprocess.run(
    cmd,
    input=init_input,
    capture_output=True,
    text=True,
    timeout=30,
)

print(f"[exit_code] {result.returncode}")
print(f"[stdout]\n{result.stdout}")
print(f"[stderr]\n{result.stderr}", file=sys.stderr)
