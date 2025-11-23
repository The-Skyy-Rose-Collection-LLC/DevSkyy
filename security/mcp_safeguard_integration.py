"""
MCP Tool Calling Integration with Safeguards
Integrates Model Context Protocol tools with enterprise safeguards

Per Truth Protocol:
- Rule #1: Never guess - Verify all MCP tool calls
- Rule #5: No secrets in tool parameters
- Rule #7: Validate all tool inputs/outputs
- Rule #8: Test coverage ≥90%
- Rule #13: Security baseline enforcement

Features:
- MCP tool calling with safeguards
- Support for both Anthropic and OpenAI
- Rate limiting and authorization
- Audit logging
- Circuit breaker protection
"""

import logging
from typing import Any

from config.unified_config import get_config
from security.tool_calling_safeguards import (
    ToolCallConfig,
    ToolCallRequest,
    ToolPermissionLevel,
    ToolProvider,
    ToolRiskLevel,
    get_tool_safeguard_manager,
)
from services.mcp_client import MCPToolClient


logger = logging.getLogger(__name__)


# ============================================================================
# MCP SAFEGUARD WRAPPER
# ============================================================================


class SafeguardedMCPClient:
    """
    MCP client with integrated safeguards

    Wraps MCPToolClient to add:
    - Rate limiting per tool
    - Authorization checks
    - Parameter validation
    - Audit logging
    - Circuit breaker protection
    """

    def __init__(
        self,
        schema_path: str = "config/mcp/mcp_tool_calling_schema.json",
        anthropic_api_key: str | None = None,
        enable_safeguards: bool = True,
    ):
        """
        Initialize safeguarded MCP client

        Args:
            schema_path: Path to MCP schema
            anthropic_api_key: Anthropic API key
            enable_safeguards: Enable safeguard protection
        """
        self.mcp_client = MCPToolClient(schema_path=schema_path, anthropic_api_key=anthropic_api_key)
        self.enable_safeguards = enable_safeguards

        if enable_safeguards:
            self.safeguard_manager = get_tool_safeguard_manager()
            self._register_mcp_tools()
        else:
            self.safeguard_manager = None

        logger.info(
            f"✅ Safeguarded MCP Client initialized " f"(safeguards={'enabled' if enable_safeguards else 'disabled'})"
        )

    def _register_mcp_tools(self):
        """Register MCP tools with safeguard manager"""
        # Get all available tools from MCP schema
        available_tools = self.mcp_client.get_available_tools()

        # Register each tool with default configuration
        # In production, these would be loaded from a configuration file
        for tool_key in available_tools:
            parts = tool_key.split(".")
            if len(parts) == 2:
                category, tool_name = parts

                # Determine risk level based on category
                risk_mapping = {
                    "code_execution": ToolRiskLevel.HIGH,
                    "file_operations": ToolRiskLevel.MEDIUM,
                    "api_interactions": ToolRiskLevel.MEDIUM,
                    "data_processing": ToolRiskLevel.LOW,
                    "media_generation": ToolRiskLevel.LOW,
                    "voice_synthesis": ToolRiskLevel.LOW,
                    "video_processing": ToolRiskLevel.MEDIUM,
                }

                risk_level = risk_mapping.get(category, ToolRiskLevel.MEDIUM)

                # Create tool configuration
                tool_config = ToolCallConfig(
                    tool_name=tool_name,
                    description=f"MCP tool: {tool_name}",
                    permission_level=ToolPermissionLevel.AUTHENTICATED,
                    risk_level=risk_level,
                    provider=ToolProvider.ANTHROPIC,
                    max_calls_per_minute=10,
                    max_calls_per_hour=100,
                    is_consequential=True,
                )

                # Register with safeguard manager
                self.safeguard_manager.register_tool(tool_config)

        logger.info(f"✅ Registered {len(available_tools)} MCP tools with safeguards")

    async def invoke_tool(
        self,
        tool_name: str,
        category: str,
        inputs: dict[str, Any],
        user_id: str | None = None,
        permission_level: ToolPermissionLevel = ToolPermissionLevel.AUTHENTICATED,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 2000,
    ) -> dict[str, Any]:
        """
        Invoke MCP tool with safeguards

        Args:
            tool_name: Name of tool
            category: Tool category
            inputs: Tool inputs
            user_id: User ID for authorization
            permission_level: User's permission level
            model: AI model to use
            max_tokens: Maximum tokens

        Returns:
            Tool execution result

        Raises:
            ValueError: If safeguards block the call
            Exception: If execution fails
        """
        # Create tool call request
        request = ToolCallRequest(
            tool_name=tool_name,
            provider=ToolProvider.ANTHROPIC,
            user_id=user_id,
            permission_level=permission_level,
            parameters=inputs,
        )

        # Execute with safeguards
        if self.enable_safeguards:
            # Wrap MCP client call
            async def execute_mcp_tool():
                return await self.mcp_client.invoke_tool(
                    tool_name=tool_name, category=category, inputs=inputs, model=model, max_tokens=max_tokens
                )

            response = await self.safeguard_manager.execute_tool_call(request=request, func=execute_mcp_tool)

            return response.result

        else:
            # Execute without safeguards
            return await self.mcp_client.invoke_tool(
                tool_name=tool_name, category=category, inputs=inputs, model=model, max_tokens=max_tokens
            )

    def load_tool(self, tool_name: str, category: str) -> dict[str, Any]:
        """Load tool definition (passes through to MCP client)"""
        return self.mcp_client.load_tool(tool_name, category)

    def get_loaded_tools(self) -> list[str]:
        """Get list of loaded tools"""
        return self.mcp_client.get_loaded_tools()

    def get_available_tools(self, category: str | None = None) -> list[str]:
        """Get list of available tools"""
        return self.mcp_client.get_available_tools(category)

    def get_safeguard_statistics(self) -> dict[str, Any]:
        """Get safeguard statistics"""
        if self.safeguard_manager:
            return self.safeguard_manager.get_statistics()
        return {"enabled": False}


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_safeguarded_mcp_client(enable_safeguards: bool | None = None) -> SafeguardedMCPClient:
    """
    Create safeguarded MCP client with application configuration

    Args:
        enable_safeguards: Override safeguard setting (uses config if None)

    Returns:
        Configured SafeguardedMCPClient
    """
    config = get_config()

    if enable_safeguards is None:
        enable_safeguards = config.ai.enable_safeguards

    return SafeguardedMCPClient(enable_safeguards=enable_safeguards)


# Singleton instance
_global_safeguarded_client: SafeguardedMCPClient | None = None


def get_safeguarded_mcp_client() -> SafeguardedMCPClient:
    """
    Get global safeguarded MCP client instance

    Returns:
        Shared SafeguardedMCPClient instance
    """
    global _global_safeguarded_client

    if _global_safeguarded_client is None:
        _global_safeguarded_client = create_safeguarded_mcp_client()

    return _global_safeguarded_client


__all__ = [
    "SafeguardedMCPClient",
    "create_safeguarded_mcp_client",
    "get_safeguarded_mcp_client",
]
