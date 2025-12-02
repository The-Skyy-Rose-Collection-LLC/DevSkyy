"""
DevSkyy MCP Module

Provides MCP server implementations for DevSkyy platform integration.

FastMCP Discovery:
    fastmcp run devskyy_mcp                    # Uses 'mcp' object
    fastmcp run devskyy_mcp:server             # Uses 'server' alias
    fastmcp run devskyy_mcp:app                # Uses 'app' alias
    fastmcp run devskyy_mcp:create_server      # Uses factory function
"""

from devskyy_mcp.optimization_server import mcp, run_server

# FastMCP auto-discovery aliases
# FastMCP looks for objects named: mcp, server, or app
server = mcp
app = mcp


def create_server():
    """
    Factory function for FastMCP server creation.

    Usage:
        fastmcp run devskyy_mcp:create_server
    """
    return mcp


__all__ = ["mcp", "server", "app", "run_server", "create_server"]
