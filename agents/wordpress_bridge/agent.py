"""WordPress Bridge Agent — Claude Agent SDK entry point.

Orchestrates 15 MCP tools to bridge dashboard pipelines to WordPress.
Uses ClaudeSDKClient with adaptive thinking for intelligent operation routing.
"""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
)

from agents.wordpress_bridge.mcp_server import create_wordpress_tools
from agents.wordpress_bridge.prompts import SYSTEM_PROMPT


class WordPressBridgeAgent:
    """Agent that bridges DevSkyy dashboard to WordPress/WooCommerce.

    Uses Claude Agent SDK with 15 custom MCP tools and adaptive thinking.
    """

    def __init__(
        self,
        *,
        model: str = "claude-opus-4-6",
        correlation_id: str | None = None,
    ):
        self.model = model
        self.correlation_id = correlation_id
        self.mcp_server = create_wordpress_tools()

    def get_options(self, permission_mode: str = "acceptEdits") -> ClaudeAgentOptions:
        """Build ClaudeAgentOptions with all 15 MCP tools."""
        return ClaudeAgentOptions(
            system_prompt=SYSTEM_PROMPT,
            mcp_servers={"wordpress_bridge": self.mcp_server},
            thinking={"type": "adaptive"},
            model=self.model,
            permission_mode=permission_mode,
            max_turns=20,
        )

    async def execute(
        self,
        prompt: str,
        *,
        permission_mode: str = "acceptEdits",
    ) -> dict[str, Any]:
        """Execute agent and return final result dict."""
        options = self.get_options(permission_mode=permission_mode)
        result_data: dict[str, Any] = {
            "result": "",
            "session_id": None,
            "cost_usd": None,
        }

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)
            async for message in client.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            result_data["result"] += block.text
                elif isinstance(message, ResultMessage):
                    result_data["result"] = message.result or ""
                    result_data["session_id"] = message.session_id
                    result_data["cost_usd"] = message.total_cost_usd

        return result_data


async def run_agent(
    prompt: str,
    *,
    model: str = "claude-opus-4-6",
    correlation_id: str | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """Run agent with SSE-compatible streaming output.

    Yields dicts suitable for JSON serialization as SSE events:
      {"type": "thinking", "content": "..."}
      {"type": "text", "content": "..."}
      {"type": "tool_use", "tool": "wp_health_check", "input": {...}}
      {"type": "tool_result", "tool": "wp_health_check", "content": "..."}
      {"type": "result", "content": "...", "session_id": "...", "cost_usd": 0.05}
    """
    agent = WordPressBridgeAgent(model=model, correlation_id=correlation_id)
    options = agent.get_options(permission_mode="acceptEdits")

    async with ClaudeSDKClient(options=options) as client:
        await client.query(prompt)
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield {"type": "text", "content": block.text}
                    elif hasattr(block, "thinking"):
                        yield {"type": "thinking", "content": block.thinking}
                    elif hasattr(block, "name") and hasattr(block, "input"):
                        # Tool use block
                        yield {
                            "type": "tool_use",
                            "tool": block.name,
                            "input": block.input if isinstance(block.input, dict) else {},
                        }
            elif isinstance(message, ResultMessage):
                yield {
                    "type": "result",
                    "content": message.result or "",
                    "session_id": message.session_id,
                    "cost_usd": message.total_cost_usd,
                }
