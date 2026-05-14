"""Diagnostic: capture exact claude CLI stderr when SDK fails.

Run via wrapper to ensure env strip:
    ./scripts/run_managed_agent.sh -- python3 scripts/diagnose_sdk.py
or directly with manual env strip.
"""

from __future__ import annotations

import asyncio
import os
import sys

# Make sure parent's CLAUDE_* don't leak (defensive — wrapper should handle this)
for var in list(os.environ):
    if var.startswith(("CLAUDE_CODE_", "CLAUDE_AUTOCOMPACT_")) or var in (
        "CLAUDECODE",
        "CLAUDE_TMPDIR",
        "CLAUDE_EFFORT",
        "AI_AGENT",
    ):
        os.environ.pop(var, None)


def stderr_callback(line: str) -> None:
    """Print every line the claude CLI writes to stderr — verbatim."""
    print(f"[CLI STDERR] {line.rstrip()}", file=sys.stderr, flush=True)


async def main() -> None:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    options = ClaudeAgentOptions(
        model="haiku",
        system_prompt="Reply with one word.",
        permission_mode="bypassPermissions",
        max_turns=1,
        max_budget_usd=0.05,
        stderr=stderr_callback,  # KEY: capture CLI stderr
        allowed_tools=[],
    )

    print("[diagnose] starting SDK query...", file=sys.stderr, flush=True)

    try:
        async for msg in query(prompt="ping", options=options):
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(f"[ASSISTANT] {block.text}")
            elif isinstance(msg, ResultMessage):
                print(f"[RESULT] cost=${msg.total_cost_usd:.4f} duration={msg.duration_ms}ms")
    except Exception as e:
        print(f"[diagnose] caught {type(e).__name__}: {e}", file=sys.stderr, flush=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
