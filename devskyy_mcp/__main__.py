"""
DevSkyy MCP Module Entry Point

Allows running the MCP server as a module:
    python -m devskyy_mcp

Or via FastMCP:
    fastmcp run devskyy_mcp
    fastmcp run devskyy_mcp:mcp
    fastmcp run devskyy_mcp:server
    fastmcp run devskyy_mcp:app
"""

from devskyy_mcp import run_server

if __name__ == "__main__":
    run_server()
