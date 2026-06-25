"""Test ClaudeSDKClient (async context manager) with MCP server.

Docs use ClaudeSDKClient for SDK MCP servers; orchestrator uses query().
Theory: query() doesn't fully support SDK MCP servers in 0.1.41.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Any

for var in list(os.environ):
    if var.startswith(("CLAUDE_CODE_", "CLAUDE_AUTOCOMPACT_")) or var in (
        "CLAUDECODE",
        "CLAUDE_TMPDIR",
        "CLAUDE_EFFORT",
        "AI_AGENT",
    ):
        os.environ.pop(var, None)


def stderr_callback(line: str) -> None:
    print(f"[CLI STDERR] {line.rstrip()}", file=sys.stderr, flush=True)


async def main() -> None:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ClaudeSDKClient,
        ResultMessage,
        TextBlock,
        create_sdk_mcp_server,
        tool,
    )

    @tool("ping", "Reply with pong", {})
    async def ping_tool(args: dict[str, Any]) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": "pong"}]}

    server = create_sdk_mcp_server(name="diag", version="1.0.0", tools=[ping_tool])

    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt="Reply with one word.",
        permission_mode="bypassPermissions",
        max_turns=1,
        max_budget_usd=0.05,
        mcp_servers={"diag": server},
        allowed_tools=["mcp__diag__ping"],
        stderr=stderr_callback,
    )

    print("[diagnose] starting ClaudeSDKClient...", file=sys.stderr, flush=True)

    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query("reply READY")
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            print(f"[ASSISTANT] {block.text}")
                elif isinstance(msg, ResultMessage):
                    print(f"[RESULT] cost=${msg.total_cost_usd:.4f} duration={msg.duration_ms}ms")
    except Exception as e:
        print(
            f"[diagnose] EXCEPTION {type(e).__name__}: {e}",
            file=sys.stderr,
            flush=True,
        )
        raise


if __name__ == "__main__":
    asyncio.run(main())
